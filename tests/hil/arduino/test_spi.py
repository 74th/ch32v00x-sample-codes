"""HIL: Arduino Core CH32 spi_master (book-code spi_master-arduino_core_ch32, ADT7310 reader), Pico SPI slave.

DESTRUCTIVE: rebuilds and flashes the DUT with the pinned minichlink.

Wiring: PC5 SCK -> GP6, PC6 MOSI -> GP7, PC7 MISO <- GP4, PC0 CS -> GP5 (sample change: the book sketch drives
no CS, so the sample holds PC0 low during each SPI transaction). SPISettings(1 MHz, MSB first, mode 0).

Expected behaviour from samples_ch32v003_arduino/spi_master/spi_master.ino:
- setup: delay 3000, reset_adt7310(): one CS frame FF FF FF FF, delay 500, 54; then delay 500.
- loop: one CS frame of two 00 bytes reading `raw` from MISO.
  raw not 0000/FFFF -> print, delay 1000 (next read ~1 s later);
  raw 0000/FFFF -> reset_adt7310() again: CS stays low ~500 ms, next read ~1 s later.
Pico SPI_SLAVE (mode 0 only) captures the first 2 bytes of a CS frame and returns a 2-byte reply; the reset
branch is seen as the long CS low on GP5 (GPIO_SAMPLE 10 ms). Serial output is not observed.
"""
import time

import pytest

from capture_helpers import captured, edge_record
from ch32hil import judge

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, fields_of, find_port, new_run, save,
                     sample_gpio)

pytestmark = [pytest.mark.hil, pytest.mark.arduino, pytest.mark.spi]

CS_GP = 5
VALID = "0c80"      # ADT7310 13-bit 25.0 degC
INVALID = "0000"    # triggers reset_adt7310()


SCK_GP = 6
SCK_HZ = 750_000    # SPISettings(1 MHz): the core picks the /64 prescaler of 48 MHz (expected value, checked by measurement)


def _spi(port, reply, edge_pin=None, log=False):
    def action(client):
        r = client.request("SPI_SLAVE", reply, "MODE0")
        return {"ok": r.ok, "fields": r.fields, "t": time.monotonic(), **fields_of(r)}
    if log:      # the DUT's Serial output (PD5 -> GP9) is printed right after the read: capture it across the frame
        result, cap, _ = captured(port, "UART", 9, 115200, action, settle_s=0.4)
        result["log_capture"] = cap
        return result
    if edge_pin is None:
        return _with_client(port, 6, action)
    result, cap, start = captured(port, "EDGE", edge_pin, None, action)
    result["sck_summary"] = edge_record(cap, start)
    return result


def _check_log(result, raw_hex):
    return judge.judge_log(result.pop("log_capture"), judge.arduino_spi_master_text(int(raw_hex, 16)), "spi_master_log")


def _check_sck(result):
    return judge.judge_period(result["sck_summary"], SCK_HZ, label="spi_sck")


def _expect(result, rx, reply):
    if not (result["ok"] and result.get("rx") == rx and result.get("tx") == reply and result.get("mode") == "0"):
        raise AssertionError(f"SPI frame mismatch, expected rx={rx} tx={reply}: {result}")
    return result


def _gap(a, b, lo, hi):
    gap = round(b["t"] - a["t"], 3)
    if not lo <= gap <= hi:
        raise AssertionError(f"read interval {gap} s outside {lo}..{hi} s")
    return gap


def _cs_low_runs(runs):
    lows = [n for v, n in runs if v == "0"]
    return max(lows) if lows else 0


def test_arduino_spi_master(request, hil_device, hil_config, hil_dut):
    dut = hil_dut("spi_master")
    run = new_run(hil_device, "spi_master", cs="PC0 (sample change)",
                  criteria="reset frame ffff; read frames 0000 ~1 s apart after a valid reply; "
                           "reply 0000 -> CS low >= 400 ms (reset_adt7310) then reads resume")
    print("HIL ARDUINO SPI: DUT master PC5/PC6/PC7, CS PC0 -> Pico SPI_SLAVE GP6/GP7/GP4/GP5")
    port = {}
    out = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.phase("dut_reset", dut.reset)
        p = port.get("p")
        run.phase("settle", time.sleep, 1.5)     # setup's delay(3000) exceeds SPI_SLAVE's 3 s wait
        a = run.phase("measure_reset_frame", _spi, p, INVALID)
        out["reset_frame"] = a and run.phase("check_reset_frame", _expect, a, "ffff", INVALID)
        # the reset frame keeps CS low ~500 ms and ends with 0x54; wait for CS high before the next capture
        boot_cs = run.phase("measure_cs_reset_frame", sample_gpio, p, CS_GP, 60, 10000)
        if boot_cs is not None:
            out["boot_cs_runs"] = boot_cs

            def frame_ends():
                if boot_cs[-1][0] != "1" or _cs_low_runs(boot_cs) < 20:
                    raise AssertionError(f"reset frame CS low then high not seen: {boot_cs}")
            run.phase("check_cs_reset_frame", frame_ends)
        b = run.phase("measure_read_valid", _spi, p, VALID, SCK_GP)
        out["read_valid"] = b and run.phase("check_read_valid", _expect, b, "0000", VALID)
        out["sck"] = b and run.phase("check_sck", _check_sck, b)
        if b:
            b.pop("sck_summary", None)
        c = run.phase("measure_read_after_valid", _spi, p, INVALID)
        out["read_after_valid"] = c and run.phase("check_read_after_valid", _expect, c, "0000", INVALID)
        if b and c:
            out["valid_interval_s"] = run.phase("check_valid_interval", _gap, b, c, 0.9, 1.3)
        runs = run.phase("measure_cs_after_invalid", sample_gpio, p, CS_GP, 80, 10000)
        if runs is not None:
            out["cs_runs"] = runs

            def reset_seen():
                longest = _cs_low_runs(runs)
                if longest < 40:
                    raise AssertionError(f"no ~500 ms CS low (reset_adt7310) after reply 0000: runs={runs}")
                return longest
            out["cs_longest_low_samples"] = run.phase("check_reset_after_invalid", reset_seen)
        d = run.phase("measure_read_after_reset", _spi, p, VALID, None, True)
        out["read_after_reset"] = d and run.phase("check_read_after_reset", _expect, d, "0000", VALID)
        out["log"] = d and run.phase("check_log", _check_log, d, VALID)
        if c and d:
            out["reset_interval_s"] = round(d["t"] - c["t"], 3)
    finally:
        run.meta["frames"] = out
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "arduino_spi_master")
    print(run.to_json())
    assert run.ok, run.to_json()

