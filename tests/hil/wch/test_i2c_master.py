"""HIL: official WCH SDK i2c_master (book-code i2c_master-wch_sdk): Pico emulates an SHT31 at 0x44 (GP10 SDA / GP11 SCL).

DESTRUCTIVE: rebuilds and flashes the DUT. Run: uv run pytest --hil --hil-framework wch tests/hil/wch/test_i2c_master.py

DUT (PC1 SDA / PC2 SCL, 400 kHz): write 30 A2, 300 ms, write 30 41, 300 ms; loop: write 24 00, 300 ms, read 6 bytes,
300 ms, print "Temperature: <t>, Humidity: <h>" on PD5, 4700 ms. The Pico bus runs at its own 100 kHz setting,
so the bus speed of the DUT is not judged. The fixed reply raw T=0x6666, H=0x8000 converts (book formulas) to 24 / 50;
the printed text proves the DUT parsed the bytes the Pico returned. Pico commands are sequential, hence the UART text
is captured after the I2C transaction (the sample prints it 300 ms after the read).
"""
import pytest

from ch32hil.pico import PicoError

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, fields_of, find_port, new_run, save,
                     uart_receive)
from arduino.test_i2c import SHT31, SHT31_REPLY, _expect_write, _slave

pytestmark = [pytest.mark.hil, pytest.mark.wch, pytest.mark.i2c]

SAMPLE = "i2c_master"
TEXT = b"Temperature: 24, Humidity: 50\r\n"


def _sequence(run, dut, port):
    out = {}
    # `minichlink -i` (wait_ready) restarts the DUT: capture the first write right after it (no extra reset).
    run.phase("dut_restart", dut.wait_ready, "reset")
    boot = run.phase("measure_soft_reset", _slave, port, SHT31, 2, "-", 3000)
    out["soft_reset"] = boot and run.phase("check_soft_reset", _expect_write, boot, "30a2")
    clear = run.phase("measure_clear_status", _slave, port, SHT31, 2, "-", 1500)
    out["clear_status"] = clear and run.phase("check_clear_status", _expect_write, clear, "3041")
    first = run.phase("measure_loop0", _slave, port, SHT31, 2, SHT31_REPLY, 2000)
    out["loop0"] = first and run.phase("check_loop0", _expect_write, first, "2400", "6")

    def text():
        rx, fields = uart_receive(port, len(TEXT), 2000)
        if rx != TEXT or fields.get("uart_errors") != "0x0":
            raise AssertionError(f"conversion text mismatch: {rx!r} want {TEXT!r} {fields}")
        return rx.decode()
    out["text"] = run.phase("check_conversion_text", text)
    wrong = run.phase("measure_wrong_address", _slave, port, SHT31 + 1, 2, "-", 3000)
    if wrong is not None:
        def untouched():
            if wrong["ok"] or wrong.get("received") != "0":
                raise AssertionError(f"0x{SHT31 + 1:02x} received a transfer: {wrong}")
        run.phase("check_wrong_address", untouched)
    second = run.phase("measure_loop1", _slave, port, SHT31, 2, SHT31_REPLY, 5000)
    if second is not None and first is not None:
        out["loop1"] = run.phase("check_loop1", _expect_write, second, "2400", "6")
        out["loop_period_s"] = round(second["t"] - first["t"], 3)

        def period():
            if not 4.8 <= out["loop_period_s"] <= 6.0:
                raise AssertionError(f"loop period {out['loop_period_s']} s, expected ~5.3 s")
        run.phase("check_loop_period", period)
    return out


def test_wch_i2c_master(request, hil_device, hil_config, hil_dut):
    dut = hil_dut(SAMPLE)
    run = new_run(hil_device, SAMPLE, sht31_reply=SHT31_REPLY,
                  criteria="0x44 writes 30a2, 3041, then 2400 + 6-byte read; text 'Temperature: 24, Humidity: 50'; "
                           "0x45 untouched; loop ~5.3 s")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        if not run.primary_failure:
            run.meta["transfers"] = _sequence(run, dut, port.get("p"))
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "wch_i2c_master")
    print(run.to_json())
    assert run.ok, run.to_json()
