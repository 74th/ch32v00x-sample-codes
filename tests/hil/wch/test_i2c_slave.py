"""HIL: official WCH SDK i2c_slave (book-code i2c_slave-wch_sdk): Pico master to the DUT at 0x10 (GP10 SDA / GP11 SCL).

DESTRUCTIVE: rebuilds and flashes the DUT. Run: uv run pytest --hil --hil-framework wch tests/hil/wch/test_i2c_slave.py

DUT: 0x30 registers; a write sets the pointer from its first byte and stores the following bytes (pointer advances);
a read returns bytes from the pointer (pointer advances); 0x20..0x23 = 00 10 20 30. The pointer moves in the I2C
event interrupt on every byte, so a write of the pointer followed by a read works both as two transactions (STOP) and
as a repeated START. The UART log lines of the sample are not judged (the Pico runs one command at a time, so they
are printed before a capture can start).
"""
import time

import pytest

from capture_helpers import captured
from ch32hil import judge

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, fields_of, find_port, new_run, save)

pytestmark = [pytest.mark.hil, pytest.mark.wch, pytest.mark.i2c]

DUT_SLAVE = 0x10
GAP_S = 0.3   # between I2C_MASTER transactions to the DUT slave


def _slave_sequence(port):
    def action(client):
        client.negotiate(["I2C_MASTER", "I2C_PROBE"])
        log = {}
        for addr, want in ((DUT_SLAVE, "1"), (DUT_SLAVE + 1, "0")):
            probe = fields_of(client.request("I2C_PROBE", addr, 500))
            log[f"probe_0x{addr:02x}"] = probe
            if probe.get("ack") != want:
                raise AssertionError(f"I2C_PROBE 0x{addr:02x}: ack={probe.get('ack')} expected {want}: {probe}")
        # Pointer write ending in STOP, then a read in a separate transaction.
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
        # Repeated START: write the pointer and read in one transaction (no STOP between).
        for name, tx, n, want in (("repeated_start_0x20", "20", 4, "00102030"), ("repeated_start_0x10", "10", 4, "aabbccdd"),
                                  ("repeated_start_0x22", "22", 2, "2030")):
            time.sleep(GAP_S)
            r = client.request("I2C_MASTER", DUT_SLAVE, tx, n, 500)
            f = fields_of(r)
            log[name] = {"ok": r.ok, **f}
            if not r.ok or f.get("rx") != want or f.get("read_rc") != str(n):
                raise AssertionError(f"I2C_MASTER {name}: expected rx={want} read_rc={n}: {r.fields}")
        return log
    # The DUT's printf log (PD5 -> GP9) is captured across the whole sequence: the Pico runs one command at a time, so the
    # capture is armed first and read afterwards. The sample prints from its main loop shortly after each transfer.
    log, cap, _ = captured(port, "UART", 9, 115200, action, settle_s=0.6, timeout=8)
    log["_capture"] = cap
    return log




def test_wch_i2c_slave(request, hil_device, hil_config, hil_dut):
    dut = hil_dut("i2c_slave")
    run = new_run(hil_device, "i2c_slave",
                  criteria="0x10 ACK, 0x11 NACK; reg 0x20 reads 00102030; write 0x10 aabbccdd reads back; partial read; repeated START reads")
    print("HIL WCH I2C slave: Pico master to DUT 0x10 on GP10/GP11")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.phase("dut_reset", dut.reset)
        run.phase("settle", time.sleep, 0.5)
        transfers = run.phase("measure", _slave_sequence, port.get("p"))
        cap = transfers and transfers.pop("_capture", None)
        run.meta["transfers"] = transfers
        if cap is not None:
            run.meta["log"] = run.phase("check_log", judge.judge_log, cap, list(judge.wch_i2c_slave_reg_lines()), "i2c_slave_log")
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "wch_i2c_slave")
    print(run.to_json())
    assert run.ok, run.to_json()
