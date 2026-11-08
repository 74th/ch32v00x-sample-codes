"""HIL: official WCH SDK watchdog (book-code watchdogtimer-wch_sdk): IWDG ~2 s, fed while PA1 is high.

DESTRUCTIVE: rebuilds and flashes the DUT. Run: uv run pytest --hil --hil-framework wch tests/hil/wch/test_watchdog.py

DUT: LED1 PC0 (-> GP5) blinks 250/250 ms while PA1 is high and the IWDG is fed every loop (500 ms); PA1 low (GP12 -> RC)
stops feeding. After every start LED2 (PC4) lights 500 ms. UART (PD5) prints "reset cause: IWDG|other" at start and
"loop N cause=..." (N counts loops since the last start; the loop takes 500 ms) in every loop.
Judged here:
  1. after a debugger reset: loop lines show cause=other (the start text itself is not captured: see the code)
  2. normal operation: PC0 250/250 ms (+-100 ms), loop counter keeps increasing, no restart (counter does not drop)
  3. PA1 low for 1000 ms: still alive (the last feed is <= 0.5 s before the hold, so < 1.6 s without feed: no reset)
  4. PA1 low for 2000 ms: the watchdog resets (>= 2.0 s without feed): cause=IWDG and a small loop counter after it
Together 3 and 4 bracket the timeout between ~1.6 s and ~2.5 s (nominal 2 s, LSI tolerance not measured).
"""
import re
import time

import pytest

from ch32hil.pico import PicoError

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, check_square, find_port, new_run, sample_gpio,
                     save, uart_receive)

pytestmark = [pytest.mark.hil, pytest.mark.wch, pytest.mark.watchdog]

SAMPLE = "watchdog"
# CH32V006 (measured, okf/log/2026-11-08-1656-ch32v006-wch-batch3-timer-dma-sleep-watchdog.md): the IWDG (reload 2000)
# does not reset after a 2.0 s or 2.3 s hold and has reset by 2.6 s (+0..0.5 s since the last feed), so a 2 s hold is not
# enough there. Pico's GPIO_DRIVE lasts at most 2000 ms, so longer holds are chained. The owner chose a longer hold for
# CH32V006 (3 s requested); 3.5 s is used for margin (4/4 resets in the bracket runs). The reset cause is judged as on
# the other devices: the reset-cause register reads IWDGRSTF after the watchdog reset on CH32V006 too.
HOLD_RESET_MS = {"default": 2000, "ch32v006": 3500}
BUTTON_GP, LED1_GP = 12, 5
LOOP = re.compile(rb"loop (\d+) cause=(\w+)\r\n")


def _hold_low(port, ms):
    """Hold PA1 low for `ms` (GPIO_DRIVE lasts at most 2000 ms, so longer holds are chained; each call's reply is checked
    and the gaps between calls are only the host round trip)."""
    def action(client):
        left = ms
        while left > 0:
            chunk = min(left, 2000) if left - min(left, 2000) >= 10 or left <= 2000 else left - 10
            reply = client.request("GPIO_DRIVE", BUTTON_GP, 0, chunk)
            if not reply.ok:
                raise PicoError(f"GPIO_DRIVE failed: {reply.fields}")
            left -= chunk
    _with_client(port, ms / 1000 + 3, action)


def _loop_line(port, attempts=3):
    seen = []
    for _ in range(attempts):
        rx, fields = uart_receive(port, 32, 1500)
        seen.append(rx)
        m = LOOP.search(rx)
        if m and fields.get("uart_errors") in ("0x0", None):
            return int(m.group(1)), m.group(2).decode(), rx.decode("ascii", "replace")
    raise AssertionError(f"no 'loop N cause=...' line: {seen}")


def test_wch_watchdog(request, hil_device, hil_config, hil_dut):   # noqa: C901
    dut = hil_dut(SAMPLE)
    run = new_run(hil_device, SAMPLE, criteria="cause=other at start; blink 250/250 and counter rises; PA1 low 1 s: alive; "
                                              "PA1 low 2 s: cause=IWDG and counter restarts; timeout ~1.6..2.5 s")
    port, out = {}, {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        p = port.get("p")
        # The DUT prints its start text at once and then a "loop" line every 500 ms, which a 32-byte Pico capture armed
        # ~0.3 s after a reset cannot reliably catch from the start. The cause is therefore judged from the loop lines.
        run.phase("dut_restart", dut.wait_ready, "reset")   # `minichlink -i` restarts the DUT
        run.phase("settle", time.sleep, 1.0)   # LED2's 500 ms pulse is over
        runs = run.phase("measure_blink", sample_gpio, p, LED1_GP, 300, 10000)
        if runs is not None:
            out["blink_runs"] = runs
            run.phase("check_blink", check_square, runs, 25, 25, 10)
        before = run.phase("loop_before", _loop_line, p)
        out["before"] = before

        def cause_other():
            if before is None or before[1] != "other":
                raise AssertionError(f"expected cause=other after a debugger reset: {before}")
        run.phase("check_cause_other", cause_other)
        # 1000 ms without feeding: not enough for a reset
        run.phase("hold_1s", _hold_low, p, 1000)
        short = run.phase("loop_after_1s", _loop_line, p)
        out["after_1s"] = short

        def alive():
            if before is None or short is None:
                raise AssertionError("missing loop lines")
            if short[1] != "other" or short[0] <= before[0]:
                raise AssertionError(f"DUT restarted or stalled after a 1 s hold: before={before} after={short}")
        run.phase("check_alive_after_1s", alive)
        # 2000 ms without feeding: the watchdog must reset the chip
        hold_ms = HOLD_RESET_MS.get(hil_device.name, HOLD_RESET_MS["default"])
        run.phase("hold_for_reset", _hold_low, p, hold_ms)
        reset = run.phase("loop_after_2s", _loop_line, p)
        out["after_2s"] = reset

        def reset_seen():
            if reset is None:
                raise AssertionError("missing loop line")
            if reset[1] != "IWDG" or reset[0] > 3:
                raise AssertionError(f"no watchdog reset after a {hold_ms} ms hold: {reset}")
        run.phase("check_iwdg_reset", reset_seen)
        run.phase("dut_restore", dut.reset)
    finally:
        run.meta["observed"] = out
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "wch_watchdog")
    print(run.to_json())
    assert run.ok, run.to_json()
