"""Helpers for HIL tests that need a Pico background capture around another Pico command.

The capture lives only while the USB serial session is open (the firmware stops it when the port closes), so the
arm, the action and the collect must run in one client session."""
import time

from test_blink_and_read import _with_client

CAPTURE_CMDS = ["CAPTURE_START", "CAPTURE_READ", "CAPTURE_STOP"]


def captured(port, kind, pin, baud, action, settle_s=0.0, timeout=12):
    """Arm a capture (kind "EDGE" or "UART"), run `action(client)`, wait `settle_s`, stop and collect.

    Returns (action_result, ch32hil.pico.Capture, start_fields). The capture is stopped even when `action` raises."""
    def operation(client):
        client.negotiate(CAPTURE_CMDS)
        start = client.capture_start(kind, pin, baud)
        try:
            result = action(client)
        except BaseException:
            client.capture_stop()
            raise
        if settle_s:
            time.sleep(settle_s)
        return result, client.capture_collect(), start
    return _with_client(port, timeout, operation)


def edge_record(capture, start):
    """Summarise an EDGE capture (see ch32hil.judge.edge_summary) with the cycle constants the Pico reported."""
    from ch32hil import judge
    return judge.edge_summary(capture.items, int(start["res_ps"]), int(start["k_period"]), int(start["k_high"]))


def fields(reply):
    return dict(f.split("=", 1) for f in reply.fields if "=" in f)


def i2c_slave_result(client, addr, expect, reply, timeout_ms):
    """One I2C_SLAVE command as the dict the I2C HIL tests use (ok, status, t, response fields)."""
    r = client.request("I2C_SLAVE", addr, expect, reply, timeout_ms)
    return {"ok": r.ok, "status": r.fields[0] if r.fields and "=" not in r.fields[0] else "OK",
            "t": time.monotonic(), **fields(r)}


def i2c_slave_captured(port, addr, expect, reply, timeout_ms, kind, pin, baud=None, settle_s=0.0):
    """I2C_SLAVE with a background capture armed around it. Returns (result_dict, Capture, start_fields)."""
    return captured(port, kind, pin, baud, lambda client: i2c_slave_result(client, addr, expect, reply, timeout_ms),
                    settle_s=settle_s, timeout=timeout_ms / 1000 + 8)


def _wait_write(client, addr, reply, timeout_ms=5000, attempts=2):
    """I2C_SLAVE until a DUT write arrives (the command's own limit is 5 s; the DUT loops every ~5.3 s)."""
    tries = []
    for _ in range(attempts):
        result = i2c_slave_result(client, addr, 2, reply, timeout_ms)
        tries.append(result)
        if result["ok"]:
            break
    return {**tries[-1], "attempts": len(tries)}


def observe_i2c_bus_error(port, addr, sync_reply, resume_reply, hold_ms=1000, uart_pin=9, uart_baud=115200):
    """Observation (not a pass/fail judgement of the DUT) of a DUT I2C master when the Pico holds a line Low.

    For SDA and SCL in turn: wait for a DUT write to `addr` (I2C_SLAVE; reply `sync_reply`, '-' = write only), then
    hold the line Low for `hold_ms` right away (the DUT's next transaction, or its retry, hits the held bus), release,
    and wait for the DUT's next write (reply `resume_reply`) to see whether communication resumes. The DUT's UART log
    (when `uart_pin` is given) is captured across the whole sequence. Only a fixture fault raises: an I2C_HOLD that
    fails, or GP10/GP11 not back to input without pulls afterwards."""
    def action(client):
        client.negotiate(["I2C_SLAVE", "I2C_HOLD", "GPIO_STATE"])
        steps = {}
        for line in ("SDA", "SCL"):
            step = {"sync": _wait_write(client, addr, sync_reply)}
            held = client.i2c_hold(line, hold_ms)
            step["hold"] = held
            step["resume"] = _wait_write(client, addr, resume_reply)
            for pin in (10, 11):
                state = fields(client.request("GPIO_STATE", pin))
                if state.get("output") != "0" or state.get("pull_up") != "0" or state.get("pull_down") != "0":
                    raise AssertionError(f"GP{pin} not released after I2C_HOLD {line}: {state}")
            steps[line] = step
        return steps
    if uart_pin is None:
        return {"steps": _with_client(port, 25, action), "log": None}
    steps, cap, _ = captured(port, "UART", uart_pin, uart_baud, action, timeout=25)
    return {"steps": steps, "log": {"received": cap.received, "overflow": cap.overflow, "frame_errors": cap.frame_errors,
                                    "text": bytes(cap.items).decode("ascii", "replace")}}


def pwm_edge_survey(port, pin, count=12, periods=6, timeout_ms=100, gap_s=0.07):
    """Repeated EDGE_MEASURE of a DUT PWM output (pin has no edges at 0 % / 100 % duty: counted as `timeouts`).

    Returns (rows, timeouts); judge with ch32hil.judge.judge_pwm_survey."""
    from ch32hil.pico import PicoEdgeTimeout

    def action(client):
        client.negotiate(["EDGE_MEASURE"])
        rows, timeouts = [], 0
        for _ in range(count):
            try:
                rows.append(client.edge_measure(pin, periods, timeout_ms))
            except PicoEdgeTimeout:
                timeouts += 1
            time.sleep(gap_s)
        return rows, timeouts
    return _with_client(port, count * (gap_s + timeout_ms / 1000 + 0.3) + 5, action)
