"""HIL: Arduino Core CH32 pwm (book-code pwm-arduino_core_ch32), measured by Pico GPIO_PULSE.

DESTRUCTIVE: rebuilds and flashes the DUT with the pinned minichlink.

Expected values derived from samples_ch32v003_arduino/pwm/pwm.ino and the official core 1.0.6
(PWM_FREQUENCY 1000 Hz, PWM_RESOLUTION 12 bit, so analogWrite(v) has duty ~ v / 4095):
- LED1 = analogWrite(128*i-1) and LED2 = analogWrite(128*(33-i)-1), i = 1..32 ramping every 31 ms (and back),
  so each duty is close to k/32 and LED1 + LED2 ~ 33/32 at the same step.
- PATTERN 2 (sample default): LED1 = PD2 (TIM1_CH1) -> GP14, LED2 = PC4 (TIM1_CH4) -> GP15.
- PATTERN 3 (book: "動作せず"): LED1 = PC6 (TIM1_CH1_1) -> GP7, LED2 = PC5 (TIM2_CH2_1) -> GP6; reference only.
- PATTERN 1 (book default) uses PD4, which is not wired to the Pico.
GPIO_PULSE is an uncalibrated software measurement; at k = 32 (100 %) there are no edges and it times out.
"""
import dataclasses
import time

import pytest

from ch32hil import judge
from ch32hil.pico import PicoError
from capture_helpers import pwm_edge_survey

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, find_port, new_run, save,
                     uart_receive)

pytestmark = [pytest.mark.hil, pytest.mark.arduino, pytest.mark.pwm]

SAMPLE = "pwm"
STEP_PPM = 1_000_000 / 32
PERIOD_US = (800, 1200)          # 1 kHz, same functional window as the ch32fun PWM test
STEP_TOLERANCE_PPM = 15_000      # each duty within this of the nearest k/32
SUM_PPM, SUM_TOLERANCE_PPM = 33 * STEP_PPM, 2 * STEP_PPM  # LED1 + LED2 at (almost) the same step
PAIRS, PAIR_GAP_S = 12, 0.09


def _pulse(client, pin):
    reply = client.request("GPIO_PULSE", pin, 50)
    fields = dict(f.split("=", 1) for f in reply.fields if "=" in f)
    if not reply.ok:
        return {"pin": pin, "error": " ".join(reply.fields)}
    return {"pin": pin, "period_us": int(fields["period_us"]), "duty_ppm": int(fields["duty_ppm"])}


def _pairs(port, led1, led2):
    def action(client):
        client.negotiate(["GPIO_PULSE"])
        out = []
        for _ in range(PAIRS):
            out.append((_pulse(client, led1), _pulse(client, led2)))
            time.sleep(PAIR_GAP_S)
        return out
    return _with_client(port, PAIRS * (PAIR_GAP_S + 0.5) + 3, action)


def _check(pairs):
    ok = [m for pair in pairs for m in pair if "duty_ppm" in m]
    if len(ok) < PAIRS:
        raise AssertionError(f"too few PWM measurements: {pairs}")
    for m in ok:
        nearest = round(m["duty_ppm"] / STEP_PPM) * STEP_PPM
        if not PERIOD_US[0] <= m["period_us"] <= PERIOD_US[1] or abs(m["duty_ppm"] - nearest) > STEP_TOLERANCE_PPM:
            raise AssertionError(f"PWM outside expectation (1 kHz, k/32 duty): {m}; all={pairs}")
    sums = [a["duty_ppm"] + b["duty_ppm"] for a, b in pairs if "duty_ppm" in a and "duty_ppm" in b]
    bad = [s for s in sums if abs(s - SUM_PPM) > SUM_TOLERANCE_PPM]
    if len(sums) < PAIRS // 2 or bad:
        raise AssertionError(f"LED1+LED2 duty not complementary (~{SUM_PPM:.0f} ppm): sums={sums}; all={pairs}")
    duties = [m["duty_ppm"] for m in ok]
    if max(duties) - min(duties) < 8 * STEP_PPM:
        raise AssertionError(f"duty does not ramp: {duties}")
    return {"sums_ppm": sums, "duty_range_ppm": [min(duties), max(duties)], "measurements": len(ok)}


def _edge_judge(port, pin):
    """EDGE_MEASURE of LED1: 1 kHz +-3 %; duty near a k/32 step (the ramp moves every 31 ms, so a few readings may mix two steps)."""
    rows, timeouts = pwm_edge_survey(port, pin, count=16, periods=6)
    return judge.judge_pwm_survey(rows, timeouts, 1000, duty_grid=32, duty_tol_ppm=15_000, label="arduino_pwm")


def _uart_reference(port):
    rx, fields = uart_receive(port, 12, 2500)
    return {"rx": rx.decode("ascii", "replace"), "uart_errors": fields.get("uart_errors")}


def _run(request, hil_device, hil_config, dut, led1, led2, name, **meta):
    run = new_run(hil_device, SAMPLE, **meta)
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.phase("dut_reset", dut.reset)
        pairs = run.phase("measure", _pairs, port.get("p"), led1, led2)
        run.meta["pairs"] = pairs
        if pairs is not None:
            run.meta["summary"] = run.phase("check", _check, pairs)
        run.meta["edge"] = run.phase("measure_edge", _edge_judge, port.get("p"), led1)
        # printf("up"/"down") via USART_Printf_Init on PD5: reference only (book notes it may not work)
        try:
            run.meta["uart_reference"] = _uart_reference(port.get("p"))
        except Exception as exc:  # noqa: BLE001 - recorded, not judged
            run.meta["uart_reference"] = f"{type(exc).__name__}: {exc}"
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, name)
    print(run.to_json())
    return run


# (LED1 GP, LED2 GP, sample PATTERN) per device. CH32V006: PC4 (TIM1_CH4) shows no signal on this DUT (cause not
# identified), so by the owner's decision the required pair is PD2 (TIM1_CH1) + PC0 (TIM2_CH3, Pico GP5); the PC4 pair
# stays as a reference test below.
REQUIRED_PAIR = {"default": (14, 15, 2, "PD2 -> GP14, PC4 -> GP15"), "ch32v006": (14, 5, 4, "PD2 -> GP14, PC0 -> GP5")}


def test_arduino_pwm(request, hil_device, hil_config, hil_dut):
    led1, led2, pattern, wiring = REQUIRED_PAIR.get(hil_device.name, REQUIRED_PAIR["default"])
    print(f"HIL ARDUINO PWM: PATTERN {pattern}, {wiring}")
    run = _run(request, hil_device, hil_config, hil_dut(SAMPLE), led1, led2, "arduino_pwm", pattern=pattern,
               criteria="1 kHz (800..1200 us); duty within 15000 ppm of k/32; LED1+LED2 ~ 33/32; ramps")
    assert run.ok, run.to_json()


@pytest.mark.xfail(reason="reference: book notes the PATTERN 3 remap (PC6/PC5) does not work", strict=False)
def test_arduino_pwm_remap_reference(request, hil_device, hil_config, hil_dut):
    print("HIL ARDUINO PWM (reference): PATTERN 3, PC6 -> GP7, PC5 -> GP6")
    dut = dataclasses.replace(hil_dut(SAMPLE),
                              make_args=("ARDUINO_FLAGS=--build-property compiler.cpp.extra_flags=-DPATTERN=3",))
    run = _run(request, hil_device, hil_config, dut, 7, 6, "arduino_pwm_remap", pattern=3, reference=True)
    # leave the default (PATTERN 2) build in place: a non-empty make_args makes Dut.build() clean first
    dataclasses.replace(dut, make_args=("ARDUINO_FLAGS=",)).build()
    assert run.ok, run.to_json()


@pytest.mark.xfail(reason="reference (CH32V006): PC4 (TIM1_CH4) shows no signal on this DUT; cause not identified",
                   strict=False)
def test_arduino_pwm_pc4_reference(request, hil_device, hil_config, hil_dut):
    """The PATTERN 2 pair (PD2 + PC4) on CH32V006, kept as a separate reference result (XFAIL or XPASS is saved)."""
    if hil_device.name != "ch32v006":
        pytest.skip("only CH32V006 uses PD2+PC0 as the required pair; the others run PATTERN 2 in test_arduino_pwm")
    print("HIL ARDUINO PWM (reference): PATTERN 2, PD2 -> GP14, PC4 -> GP15")
    dut = dataclasses.replace(hil_dut(SAMPLE),
                              make_args=("ARDUINO_FLAGS=--build-property compiler.cpp.extra_flags=-DPATTERN=2",))
    run = _run(request, hil_device, hil_config, dut, 14, 15, "arduino_pwm_pc4", pattern=2, reference=True,
               criteria="same criteria as the required pair, on PC4")
    dataclasses.replace(dut, make_args=("ARDUINO_FLAGS=",)).build()
    assert run.ok, run.to_json()
