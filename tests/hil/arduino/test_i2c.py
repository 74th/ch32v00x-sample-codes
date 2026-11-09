"""HIL: Arduino Core CH32 i2c_master / i2c_slave (book-code), Pico I2C on GP10 SDA / GP11 SCL (100 kHz).

DESTRUCTIVE: rebuilds and flashes the DUT with the pinned minichlink.

Pico commands run one at a time, so the Serial output (printed right after each transfer) is not observed;
the judgement uses the bus contents seen or produced by the Pico.

i2c_master (samples_ch32v003_arduino/i2c_master/i2c_master.ino), DUT master to an SHT31 at 0x44:
  setup: write 30 A2 (soft reset), delay 300, write 30 41 (clear status), delay 300;
  loop:  write 24 00, delay 300, read 6 bytes, delay 5000.
  The Pico acts as the SHT31 (I2C_SLAVE 0x44) and returns a fixed 6-byte measurement.
i2c_slave (samples_ch32v003_arduino/i2c_slave/i2c_slave.ino), DUT slave at 0x10 with 0x30 registers:
  a write sets position = first byte and stores the following bytes from there; a read returns
  4 bytes from position; registers 0x20..0x23 start as 00 10 20 30.
"""
import time

import pytest

from capture_helpers import edge_record, i2c_slave_captured, observe_i2c_bus_error
from ch32hil import judge

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, fields_of, find_port, new_run,
                     reset_during, save)

pytestmark = [pytest.mark.hil, pytest.mark.arduino, pytest.mark.i2c]

SHT31 = 0x44
DUT_SLAVE = 0x10
GAP_S = 0.3   # between I2C_MASTER transactions to the DUT slave


def _crc8(data):
    """Sensirion CRC-8 (poly 0x31, init 0xFF) so the reply looks like a real SHT31 frame."""
    crc = 0xFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x31) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


T_RAW, H_RAW = 0x6666, 0x8000
SHT31_REPLY = bytes([T_RAW >> 8, T_RAW & 0xFF, _crc8([T_RAW >> 8, T_RAW & 0xFF]),
                     H_RAW >> 8, H_RAW & 0xFF, _crc8([H_RAW >> 8, H_RAW & 0xFF])]).hex()


def _slave(port, addr, expect, reply, timeout_ms):
    def action(client):
        r = client.request("I2C_SLAVE", addr, expect, reply, timeout_ms)
        return {"ok": r.ok, "status": r.fields[0] if r.fields and "=" not in r.fields[0] else "OK",
                "t": time.monotonic(), **fields_of(r)}
    return _with_client(port, timeout_ms / 1000 + 3, action)


SCL_GP, UART_GP = 11, 9
SCL_HZ = 100_000    # Wire's default clock (core 1.0.6 Wire.cpp:92)


def _slave_scl(port, addr, expect, reply, timeout_ms, hz_pin=SCL_GP):
    """I2C_SLAVE with the SCL edge capture armed around it; the summary is judged by _check_scl."""
    result, cap, start = i2c_slave_captured(port, addr, expect, reply, timeout_ms, "EDGE", hz_pin)
    result["scl_summary"] = edge_record(cap, start)
    return result


def _check_scl(result, expected_hz=SCL_HZ):
    return judge.judge_period(result["scl_summary"], expected_hz, judge.I2C_SCL_TOL_PCT, label="i2c_scl")


def _slave_log(port, addr, expect, reply, timeout_ms):
    """I2C_SLAVE with the DUT's Serial output (PD5 -> GP9) captured across it and 0.4 s after it."""
    result, cap, _ = i2c_slave_captured(port, addr, expect, reply, timeout_ms, "UART", UART_GP, 115200, settle_s=0.4)
    result["log_capture"] = cap
    return result


def _check_log(result, expected, label="log"):
    cap = result.pop("log_capture")
    record = judge.judge_log(cap, expected, label)
    return record


def _expect_write(result, rx, sent="0"):
    if not (result["ok"] and result.get("rx") == rx and result.get("sent") == sent):
        raise AssertionError(f"expected DUT write {rx} (sent {sent}) to 0x{SHT31:02x}: {result}")
    return result


def _master_sequence(run, dut, port):
    # settle 1.0 s: the restart by the preceding minichlink -b already sent 30a2/3041 (300 ms apart)
    boot = run.phase("dut_reset", reset_during, dut, lambda: _slave(port, SHT31, 2, "-", 3000), 3, 0.3, 1.0)
    out = {"boot": boot}
    if boot is None:
        return out
    out["soft_reset"] = run.phase("check_soft_reset", _expect_write, boot, "30a2")
    clear = run.phase("measure_clear_status", _slave, port, SHT31, 2, "-", 1500)
    out["clear_status"] = clear and run.phase("check_clear_status", _expect_write, clear, "3041")
    first = run.phase("measure_loop0", _slave_scl, port, SHT31, 2, SHT31_REPLY, 2000)
    out["loop0"] = first and run.phase("check_loop0", _expect_write, first, "2400", "6")
    out["scl"] = first and run.phase("check_scl", _check_scl, first)
    if first:
        first.pop("scl_summary", None)
    wrong = run.phase("measure_wrong_address", _slave, port, SHT31 + 1, 2, "-", 3000)
    if wrong is not None:
        out["wrong_address"] = wrong

        def untouched():
            if wrong["ok"] or wrong.get("received") != "0":
                raise AssertionError(f"0x{SHT31 + 1:02x} received a transfer: {wrong}")
        run.phase("check_wrong_address", untouched)
    second = run.phase("measure_loop1", _slave_log, port, SHT31, 2, SHT31_REPLY, 5000)
    if second is not None:
        out["log"] = run.phase("check_log", _check_log, second, judge.arduino_i2c_master_text(T_RAW, H_RAW), "i2c_master_log")
    if second is not None and first is not None:
        out["loop1"] = run.phase("check_loop1", _expect_write, second, "2400", "6")
        out["loop_period_s"] = round(second["t"] - first["t"], 3)

        def period():
            if not 4.8 <= out["loop_period_s"] <= 6.0:
                raise AssertionError(f"loop period {out['loop_period_s']} s, expected ~5.3 s (300 + 5000 ms)")
        run.phase("check_loop_period", period)
    return out


def _slave_sequence(port):
    def action(client):
        client.negotiate(["I2C_MASTER", "I2C_PROBE"])
        log = {}
        for addr, want in ((DUT_SLAVE, "1"), (DUT_SLAVE + 1, "0")):
            probe = fields_of(client.request("I2C_PROBE", addr, 500))
            log[f"probe_0x{addr:02x}"] = probe
            if probe.get("ack") != want:
                raise AssertionError(f"I2C_PROBE 0x{addr:02x}: ack={probe.get('ack')} expected {want}: {probe}")
        # Like the book's own test master (i2c_slave-test_master): set the position with a write ending in STOP,
        # then read in a separate transaction. onReceive runs on STOP, so a repeated-START read would still use
        # the previous position (recorded below as a reference, not judged).
        steps = (("set_0x20", "20", 0, None), ("read_0x20", "-", 4, "00102030"),
                 ("write_0x10", "10aabbccdd", 0, None),
                 ("set_0x10", "10", 0, None), ("read_0x10", "-", 4, "aabbccdd"),
                 ("set_0x12", "12", 0, None), ("read_0x12", "-", 2, "ccdd"))
        for name, tx, n, want in steps:
            r = client.request("I2C_MASTER", DUT_SLAVE, tx, n, 500)
            f = fields_of(r)
            log[name] = {"ok": r.ok, **f}
            if not r.ok or (want is not None and f.get("rx") != want):
                raise AssertionError(f"I2C_MASTER {name}: expected rx={want}: {r.fields}")
            time.sleep(GAP_S)
        r = client.request("I2C_MASTER", DUT_SLAVE, "20", 4, 500)   # repeated START, reference only
        log["reference_repeated_start_0x20"] = {"ok": r.ok, **fields_of(r)}
        return log
    return _with_client(port, 8, action)


def test_arduino_i2c_master(request, hil_device, hil_config, hil_dut):
    dut = hil_dut("i2c_master")
    run = new_run(hil_device, "i2c_master", sht31_reply=SHT31_REPLY,
                  criteria="0x44 writes 30a2, 3041, then 2400 + 6-byte read; 0x45 untouched; loop ~5.3 s")
    print("HIL ARDUINO I2C master: Pico emulates SHT31 at 0x44 on GP10/GP11")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        if not run.primary_failure:
            run.meta["transfers"] = _master_sequence(run, dut, port.get("p"))
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "arduino_i2c_master")
    print(run.to_json())
    assert run.ok, run.to_json()


# Official core 1.0.6 (CH32V003 and CH32V002): the Wire slave sometimes holds SCL low after a transaction (a read followed by
# another transaction; the bus stays stuck until the DUT is reset). The CPU stays inside the EV interrupt handler:
# onRequest -> Wire.write -> i2c_slave_write() busy-waits for BYTE_TRANSMITTED, which never comes after the
# master's NACK on the last byte. Not strict: a run can pass.
# okf/log/2026-11-07-2310-arduino-neopixel-timing.md
# Also on CH32V002 (2026-11-07 23:35: write+read back to back hangs at the 3rd read; this test failed 5 of 6 runs).
SLAVE_KNOWN_INTERMITTENT = {
    "ch32v003": "official core 1.0.6: Wire slave intermittently holds SCL low (stuck in the EV handler)",
    "ch32v002": "official core 1.0.6: Wire slave intermittently holds SCL low (stuck in the EV handler)",
}


def test_arduino_i2c_slave(request, hil_device, hil_config, hil_dut):
    if hil_device.name in SLAVE_KNOWN_INTERMITTENT:
        request.node.add_marker(pytest.mark.xfail(reason=SLAVE_KNOWN_INTERMITTENT[hil_device.name], strict=False))
    dut = hil_dut("i2c_slave")
    run = new_run(hil_device, "i2c_slave",
                  criteria="0x10 ACK, 0x11 NACK; reg 0x20 reads 00102030; write 0x10 aabbccdd reads back; partial read")
    print("HIL ARDUINO I2C slave: Pico master to DUT 0x10 on GP10/GP11")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.phase("dut_reset", dut.reset)
        run.phase("settle", time.sleep, 0.5)
        run.meta["transfers"] = run.phase("measure", _slave_sequence, port.get("p"))
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "arduino_i2c_slave")
    print(run.to_json())
    assert run.ok, run.to_json()


# i2c_slave-test_master (samples_<device>_arduino/i2c_slave_test_master): the book's second DUT, master of the
# i2c_slave sketch. Every loop (count = 1, 2, ...): write 10 c c+1 c+2 c+3 to 0x10 (STOP), delay 100,
# write 20 (STOP), read 4 bytes, print, delay 1000. The Pico plays the 0x10 slave.
TEST_MASTER_REPLY = "a1b2c3d4"


def _write_tail(result):
    """c from a capture whose received bytes end with the 5-byte write 10 c c+1 c+2 c+3."""
    rx = bytes.fromhex(result["rx"]) if result.get("rx", "-") != "-" else b""
    tail = rx[-5:]
    if len(tail) == 5 and tail[0] == 0x10 and list(tail[1:]) == [(tail[1] + i) & 0xFF for i in range(4)]:
        return tail[1]
    return None


def _test_master_sequence(run, port):
    """The DUT loops on its own, so the first capture only synchronises: armed at an arbitrary point it may also
    take the preceding 20 + read (then the Pico reports ERR I2C for the extra bytes); its received bytes must
    still end with the write. The following captures are aligned and judged strictly."""
    out = {}
    # The sync capture stops after 5 received bytes. Armed right after the preceding "20" it can end one byte before the
    # write completes (seen on CH32V006 in 2 of ~13 runs: rx=20 10 02 03 04), which says nothing about the DUT: such an
    # attempt is inconclusive and repeated (at most 3 times). The judged captures below stay strict.
    count, attempts = None, []
    for attempt in range(3):
        sync = run.phase("measure_sync_write", _slave, port, DUT_SLAVE, 5, "-", 3000)
        attempts.append(sync)
        if sync is None:
            out["sync_write"], out["sync_attempts"] = None, attempts
            return out
        count = _write_tail(sync) if sync else None
        if count is not None:
            break                             # every attempt stays in the staged results and in out["sync_attempts"]
    out["sync_write"], out["sync_attempts"] = sync, attempts

    def check_sync(result):
        c = _write_tail(result)
        if c is None:
            raise AssertionError(f"received bytes do not end with 10 c c+1 c+2 c+3 after {len(attempts)} attempts: "
                                 f"{[a and a.get('rx') for a in attempts]}")
        return c
    count = run.phase("check_sync_write", check_sync, sync)
    read = run.phase("measure_read", _slave_log, port, DUT_SLAVE, 1, TEST_MASTER_REPLY, 1000)
    out["read"] = read and run.phase("check_read", _expect_slave_read, read)
    if read is not None:
        out["read_log"] = run.phase("check_read_log", _check_log, read, judge.arduino_test_master_read_text(TEST_MASTER_REPLY),
                                    "test_master_read_log")
    second = run.phase("measure_next_write", _slave, port, DUT_SLAVE, 5, "-", 3000)
    out["next_write"] = second
    if second is not None and count is not None:
        def check_next(result):
            c = _write_tail(result)
            if not (result["ok"] and result.get("received") == "5" and c is not None):
                raise AssertionError(f"expected exactly the write 10 c c+1 c+2 c+3: {result}")
            return c
        nxt = run.phase("check_next_write", check_next, second)
        out["count"] = [count, nxt]
        out["loop_period_s"] = round(second["t"] - sync["t"], 3)

        def increments():
            if nxt != (count + 1) & 0xFF:
                raise AssertionError(f"count did not increase by 1: {count} -> {nxt}")
            if not 0.9 <= out["loop_period_s"] <= 1.6:
                raise AssertionError(f"loop period {out['loop_period_s']} s, expected ~1.1 s (100 + 1000 ms)")
        run.phase("check_loop", increments)
    return out


def _expect_slave_read(result):
    if not (result["ok"] and result.get("rx") == "20" and result.get("sent") == "4"):
        raise AssertionError(f"expected write 20 then a 4-byte read from 0x{DUT_SLAVE:02x}: {result}")
    return result


def test_arduino_i2c_slave_test_master(request, hil_device, hil_config, hil_dut):
    dut = hil_dut("i2c_slave_test_master")
    run = new_run(hil_device, "i2c_slave_test_master", slave_reply=TEST_MASTER_REPLY,
                  criteria="0x10 receives 10 c..c+3, then 20 + 4-byte read; next loop c+1 after ~1.1 s")
    print("HIL ARDUINO I2C test master: Pico plays the 0x10 slave on GP10/GP11")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.phase("dut_reset", dut.reset)
        if not run.primary_failure:
            run.meta["transfers"] = _test_master_sequence(run, port.get("p"))
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "arduino_i2c_slave_test_master")
    print(run.to_json())
    assert run.ok, run.to_json()


def test_arduino_i2c_master_bus_error_observation(request, hil_device, hil_config, hil_dut):
    """Observation only: hold SDA, then SCL, Low while the DUT master is mid-sequence, and record the DUT's log and
    whether its transactions resume. Only a fixture fault (the Pico not releasing a line) fails this test."""
    dut = hil_dut("i2c_master")
    run = new_run(hil_device, "i2c_master", observation="i2c_bus_error")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.phase("dut_reset", dut.reset)
        run.meta["observation_result"] = run.phase("observe", observe_i2c_bus_error, port.get("p"), SHT31, "-", SHT31_REPLY)
        print("BUS ERROR observation:", run.meta["observation_result"])
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "arduino_i2c_master_bus_error")
    assert run.ok, run.to_json()
