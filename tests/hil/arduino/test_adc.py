"""HIL: Arduino Core CH32 adc (book-code adc-arduino_core_ch32), PA1/PA2 RC driven by Pico GP12/GP13.

DESTRUCTIVE: rebuilds and flashes the DUT with the pinned minichlink.

Expected values derived from samples_ch32v003_arduino/adc/adc.ino: every ~100 ms the sketch prints
"loop <n>\\r\\n" and "X: <analogRead(PA1)>, Y: <analogRead(PA2)>\\r\\n". The default read resolution is the variant's
ADC_RESOLUTION: 10 bit (0..1023) for CH32V003F4, 12 bit (0..4095) for the CH32V006K8 variant borrowed for CH32V002.

Stimulus: the Pico firmware's PWM stimulus (ADC_OBSERVE) only accepts the ch32fun sample's hex output, and the
firmware is not changed here. So each RC (10 kOhm, 1 uF, tau 10 ms) is charged or discharged by GPIO_DRIVE for
500 ms (50 tau); after the drive is released (Pico pin input, no pull) the capacitor holds the level while the
Serial text is received. Uncalibrated: only a coarse high/low change per channel is judged.
"""
import re

import pytest

from ch32hil.pico import PicoError

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, find_port, new_run, save,
                     uart_receive)

pytestmark = [pytest.mark.hil, pytest.mark.arduino, pytest.mark.adc]

SAMPLE = "adc"
X_GP, Y_GP = 12, 13              # PA1 (X), PA2 (Y)
# (full scale, driven-high minimum, driven-low maximum) per device; full scale from the variant ADC_RESOLUTION
# (official core 1.0.6). Coarse thresholds: 700/300 of 1023, the same ratio on 4095.
# CH32V006: variant_CH32V006K8.h ADC_RESOLUTION 12 (core 1.0.6), so the 4095-scale thresholds apply.
SCALE = {"ch32v003": (1023, 700, 300), "ch32v002": (4095, 2800, 1200), "ch32v006": (4095, 2800, 1200)}
LINE = re.compile(r"X: (\d+), Y: (\d+)\r\n")


def _drive(port, pin, level, ms=500):
    def action(client):
        reply = client.request("GPIO_DRIVE", pin, level, ms)
        if not reply.ok:
            raise PicoError(f"GPIO_DRIVE {pin} {level} failed: {reply.fields}")
    _with_client(port, ms / 1000 + 3, action)


def _read_xy(port, attempts=3):
    """First complete X/Y line within a few 32-byte captures."""
    seen = []
    for _ in range(attempts):
        rx, fields = uart_receive(port, 32, 1000)
        text = rx.decode("ascii", "replace")
        seen.append(text)
        if fields.get("uart_errors") not in ("0x0", None):
            continue
        m = LINE.search(text)
        if m:
            return int(m.group(1)), int(m.group(2)), text
    raise AssertionError(f"no complete X/Y line received: {seen}")


def _state(port, scale, x_level, y_level):
    full, high_min, low_max = scale
    _drive(port, X_GP, x_level)
    _drive(port, Y_GP, y_level)
    x, y, text = _read_xy(port)
    want = (high_min <= x if x_level else x <= low_max) and (high_min <= y if y_level else y <= low_max)
    result = {"x_level": x_level, "y_level": y_level, "x": x, "y": y, "full_scale": full, "rx": text}
    if not (0 <= x <= full and 0 <= y <= full and want):
        raise AssertionError(f"ADC reading does not follow the stimulus: {result}")
    return result


def test_arduino_adc(request, hil_device, hil_config, hil_dut):
    dut = hil_dut(SAMPLE)
    scale = SCALE[hil_device.name]
    run = new_run(hil_device, SAMPLE, uncalibrated=True, full_scale=scale[0],
                  criteria=f"driven-high channel >= {scale[1]}, driven-low channel <= {scale[2]} (0..{scale[0]})")
    print("HIL ARDUINO ADC: GP12 -> RC -> PA1 (X), GP13 -> RC -> PA2 (Y), PD5 -> GP9 Serial")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.phase("dut_reset", dut.reset)
        run.meta["x_high_y_low"] = run.phase("measure_x_high", _state, port.get("p"), scale, 1, 0)
        run.meta["x_low_y_high"] = run.phase("measure_y_high", _state, port.get("p"), scale, 0, 1)
        run.meta["both_low"] = run.phase("measure_both_low", _state, port.get("p"), scale, 0, 0)
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "arduino_adc")
    print(run.to_json())
    assert run.ok, run.to_json()
