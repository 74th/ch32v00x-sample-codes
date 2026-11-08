"""HIL: official WCH SDK adc (book-code adc-wch_sdk), PA1/PA2 RC driven by Pico GP12/GP13.

DESTRUCTIVE: rebuilds and flashes the DUT. Run: uv run pytest --hil --hil-framework wch tests/hil/wch/test_adc.py

The DUT prints "x: <PA1>, y: <PA2>" (10 bit, 0..1023) every 200 ms on PD5. Stimulus: each RC (10 kOhm, 1 uF,
tau 10 ms) is charged/discharged by GPIO_DRIVE; after the release (Pico pin input) the capacitor holds its level.
 - coarse: high-driven channel >= 700, low-driven channel <= 300; both channels are exercised independently
 - monotonic: after a full discharge, three cumulative 10 ms charge pulses (1 - e^-1 = 63 %, then ~86 %, ~95 %)
   must read strictly increasing by >= 20 counts
Uncalibrated against any external reference: the sample's own ADC calibration runs, but no voltage is measured.
"""
import re

import pytest

from ch32hil.pico import PicoError

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, find_port, new_run, save,
                     uart_receive)

pytestmark = [pytest.mark.hil, pytest.mark.wch, pytest.mark.adc]

SAMPLE = "adc"
X_GP, Y_GP = 12, 13              # PA1 (x), PA2 (y)
# (full scale, driven-high minimum, driven-low maximum, minimum step between charge pulses) per device:
# CH32V003 10 bit, CH32V002 12 bit (same ratios, values x4; the 002 numbers are unexercised, no CH32V002 attached yet)
SCALE = {"ch32v003": (1023, 700, 300, 20), "ch32v002": (4095, 2800, 1200, 80),
         "ch32v006": (4095, 2800, 1200, 80)}   # 006: same 12-bit ADC and SDK as 002 (same ratios, not tuned to results)
LINE = re.compile(r"x: (\d+), y: (\d+)\r\n")


def _drive(port, pin, level, ms):
    def action(client):
        reply = client.request("GPIO_DRIVE", pin, level, ms)
        if not reply.ok:
            raise PicoError(f"GPIO_DRIVE {pin} {level} failed: {reply.fields}")
    _with_client(port, ms / 1000 + 3, action)


def _read_xy(port, attempts=3):
    seen = []
    for _ in range(attempts):
        rx, fields = uart_receive(port, 32, 1000)
        text = rx.decode("ascii", "replace")
        seen.append(text)
        m = LINE.search(text)
        if m and fields.get("uart_errors") in ("0x0", None):
            return int(m.group(1)), int(m.group(2))
    raise AssertionError(f"no complete x/y line received: {seen}")


def _coarse(port, scale, x_level, y_level):
    FULL, HIGH_MIN, LOW_MAX, _ = scale
    _drive(port, X_GP, x_level, 500)
    _drive(port, Y_GP, y_level, 500)
    x, y = _read_xy(port)
    ok = (HIGH_MIN <= x if x_level else x <= LOW_MAX) and (HIGH_MIN <= y if y_level else y <= LOW_MAX)
    result = {"x_level": x_level, "y_level": y_level, "x": x, "y": y}
    if not (0 <= x <= FULL and 0 <= y <= FULL and ok):
        raise AssertionError(f"ADC reading does not follow the stimulus: {result}")
    return result


def _monotonic(port, scale, pin, index):
    _, _, LOW_MAX, MIN_STEP = scale
    _drive(port, X_GP if pin == X_GP else Y_GP, 0, 500)
    _drive(port, Y_GP if pin == X_GP else X_GP, 0, 500)
    values = []
    for _ in range(3):
        _drive(port, pin, 1, 10)
        values.append(_read_xy(port)[index])
    if not all(b - a >= MIN_STEP for a, b in zip(values, values[1:])) or values[0] <= LOW_MAX * 2 // 3:
        raise AssertionError(f"charge steps not strictly increasing: {values}")
    return values


def test_wch_adc(request, hil_device, hil_config, hil_dut):
    dut = hil_dut(SAMPLE)
    scale = SCALE[hil_device.name]
    FULL, HIGH_MIN, LOW_MAX, MIN_STEP = scale
    run = new_run(hil_device, SAMPLE, criteria=f"coarse high>={HIGH_MIN}/low<={LOW_MAX} of {FULL}; "
                                              f"3 charge steps increase by >={MIN_STEP}; no external reference")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.phase("dut_reset", dut.reset)
        run.meta["x_high_y_low"] = run.phase("x_high_y_low", _coarse, port.get("p"), scale, 1, 0)
        run.meta["x_low_y_high"] = run.phase("x_low_y_high", _coarse, port.get("p"), scale, 0, 1)
        run.meta["both_low"] = run.phase("both_low", _coarse, port.get("p"), scale, 0, 0)
        run.meta["x_steps"] = run.phase("x_monotonic", _monotonic, port.get("p"), scale, X_GP, 0)
        run.meta["y_steps"] = run.phase("y_monotonic", _monotonic, port.get("p"), scale, Y_GP, 1)
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "wch_adc")
    print(run.to_json())
    assert run.ok, run.to_json()
