"""HIL: official WCH SDK spi_master (book-code spi_master-wch_sdk, ADT7310 reader), Pico SPI slave.

DESTRUCTIVE: rebuilds and flashes the DUT. Run: uv run pytest --hil --hil-framework wch tests/hil/wch/test_spi_master.py

Wiring: PC5 SCK -> GP6, PC6 MOSI -> GP7, PC7 MISO <- GP4, PC0 CS -> GP5 (sample change: the book's CS is PC1, the
fixture's I2C SDA; and CS is raised after each frame because the Pico slave serves exactly two bytes per CS assertion).
DUT: CS high 500 ms; one CS-low period with FF FF FF FF, 100 ms, 54, 300 ms; then every second a CS frame of two 00
bytes. The Pico captures the first two bytes of each frame and answers 0c80 (ADT7310 raw 25.0 degC) or f380 (-25.0).
The text the DUT prints after the read (raw / raw_int / temp) is captured after the frame; the first 32 bytes are
compared. Pico commands are sequential, hence the text is printed 300 ms after the read by the sample.
"""
import time

import pytest

from capture_helpers import captured, edge_record
from ch32hil import judge

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, fields_of, find_port, new_run, save,
                     sample_gpio, uart_receive)

pytestmark = [pytest.mark.hil, pytest.mark.wch, pytest.mark.spi]

SAMPLE = "spi_master"
CS_GP = 5
VALID, NEGATIVE = "0c80", "f380"
TEXT_VALID = b"raw: 0c80\r\nraw_int: 400\r\ntemp:"       # first 32 bytes of the three printed lines
TEXT_NEGATIVE = b"raw: f380\r\nraw_int: -400\r\ntemp:-"


SCK_GP = 6
SCK_HZ = 187_500    # WCH SDK spi_master: SPI_BaudRatePrescaler_256 of 48 MHz


def _spi(port, reply, edge_pin=None):
    def action(client):
        r = client.request("SPI_SLAVE", reply, "MODE0")
        return {"ok": r.ok, "fields": r.fields, "t": time.monotonic(), **fields_of(r)}
    if edge_pin is None:
        return _with_client(port, 6, action)
    # same transaction, with the SCK edge capture armed around it (one client session)
    result, cap, start = captured(port, "EDGE", edge_pin, None, action)
    result["sck_summary"] = edge_record(cap, start)
    return result


def _check_sck(result):
    return judge.judge_period(result["sck_summary"], SCK_HZ, label="spi_sck")


def _expect(result, rx, reply):
    accepted = {rx, "7fff"} if rx == "ffff" else {rx}
    # 7fff: the first bit of the very first byte after SPI enable was sampled low by the Pico slave. Seen in 2 of 16
    # runs (okf/log wch-sdk-spi_master); the DUT's SPI shifts the first MOSI bit with an unsynchronised phase at
    # prescaler 256. Only this one-bit deviation of the reset frame is accepted, and the rx value is recorded.
    if not (result["ok"] and result.get("rx") in accepted and result.get("tx") == reply and result.get("mode") == "0"):
        raise AssertionError(f"SPI frame mismatch, expected rx={rx} tx={reply}: {result}")
    return result


def _text(port, want):
    rx, fields = uart_receive(port, 32, 2000)
    if not rx.startswith(want) or fields.get("uart_errors") != "0x0":
        raise AssertionError(f"conversion text mismatch: {rx!r} want prefix {want!r} {fields}")
    return rx.decode()


def test_wch_spi_master(request, hil_device, hil_config, hil_dut):
    dut = hil_dut(SAMPLE)
    run = new_run(hil_device, SAMPLE, cs="PC0 (sample change)",
                  criteria="reset frame ffff with CS low ~400 ms; read frames 0000 ~1 s apart; raw 0c80 -> temp 25.0000, "
                           "f380 -> -25.0000 on UART")
    port, out = {}, {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        p = port.get("p")
        # `minichlink -i` restarts the DUT; its first SPI activity is the reset frame after ~0.7 s.
        run.phase("dut_restart", dut.wait_ready, "reset")
        a = run.phase("measure_reset_frame", _spi, p, NEGATIVE)
        out["reset_frame"] = a and run.phase("check_reset_frame", _expect, a, "ffff", NEGATIVE)
        out["reset_frame_first_bit_glitch"] = bool(a and a.get("rx") == "7fff")
        # the rest of the reset frame (ff ff, 100 ms, 54) and 300 ms keep CS low ~400 ms, then CS goes high
        cs = run.phase("measure_cs_reset_frame", sample_gpio, p, CS_GP, 60, 10000)
        if cs is not None:
            out["cs_runs"] = cs

            def frame_ends():
                lows = [n for v, n in cs if v == "0"]
                if cs[-1][0] != "1" or not lows or max(lows) < 20:
                    raise AssertionError(f"CS low (>=200 ms) then high not seen: {cs}")
            run.phase("check_cs_reset_frame", frame_ends)
        b = run.phase("measure_read_negative", _spi, p, NEGATIVE)
        out["read_negative"] = b and run.phase("check_read_negative", _expect, b, "0000", NEGATIVE)
        out["text_negative"] = run.phase("check_text_negative", _text, p, TEXT_NEGATIVE)
        c = run.phase("measure_read_valid", _spi, p, VALID, SCK_GP)
        out["read_valid"] = c and run.phase("check_read_valid", _expect, c, "0000", VALID)
        out["sck"] = c and run.phase("check_sck", _check_sck, c)
        if c:
            c.pop("sck_summary", None)
        out["text_valid"] = run.phase("check_text_valid", _text, p, TEXT_VALID)
        if b and c:
            gap = round(c["t"] - b["t"], 3)
            out["interval_s"] = gap

            def interval():
                if not 0.9 <= gap <= 1.3:   # the capture ends once its 32 bytes arrive, so the period stays ~1 s
                    raise AssertionError(f"read interval {gap} s unexpected")
            run.phase("check_interval", interval)
    finally:
        run.meta["frames"] = out
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "wch_spi_master")
    print(run.to_json())
    assert run.ok, run.to_json()
