"""Shared HIL flow of the CH32V006-only samples (usart2, tim3, opa, tkey): the WCH SDK and the ch32fun versions behave alike
and are judged alike (ch32hil/v006_only.py).

DESTRUCTIVE: rebuilds and flashes the DUT. Used by tests/hil/wch/test_v006_only.py (prefix "wch_") and
tests/hil/test_v006_only_ch32fun.py (prefix "", via arduino.common.new_run). Skipped on every device other than CH32V006 (before anything is built or flashed).
- usart2: PD2 -> Pico GP14, PIO UART capture (115200 8N1): the fixed text must arrive repeatedly.
- opa: PGA (4x, 8x). The Pico drives PA2 through its 10 kOhm/1 uF RC with a 10 kHz PWM (ADC_OBSERVE; its own report parsing
  times out because the DUT's log is not the book's format, which is expected and ignored) while the DUT's log (PD5 ->
  GP9) is captured in the background. Judged by out/in (voltages are not calibrated), with the saturation recorded.
- tim3: PC0 -> Pico GP5, period/duty by EDGE_MEASURE (500 Hz, 50 %).
- tkey: PD4 (floating) and PA2 (10 kOhm + 1 uF) values are recorded (reference, no pass/fail on the values).
"""
import dataclasses
from time import sleep

import pytest

from arduino.common import _cleanup, _prepare, build_flash_readback, find_port, save, uart_receive  # noqa: F401
from capture_helpers import captured, pwm_edge_survey
from ch32hil import judge, v006_only as v

UART_GP, USART2_GP, PC0_GP = 9, 14, 5


def only_v006(hil_device):
    if hil_device.name != "ch32v006":
        pytest.skip("CH32V006-only peripheral (USART2/OPA/TIM3/TKEY are not on this device)")


def _setup(request, hil_config, run, dut):
    port = {}
    run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
    run.phase("fixture_setup", _prepare, port.get("p"), 6)
    build_flash_readback(run, dut)
    run.phase("dut_reset", dut.reset)
    return port


def _finish(request, run, port, name):
    run.phase("cleanup", _cleanup, port.get("p"), 6)
    save(request, run, name)
    print(run.to_json())
    assert run.ok, run.to_json()


def run_tim3(request, hil_device, hil_config, hil_dut, new_run, prefix):
    only_v006(hil_device)
    expected = v.tim3_expected_hz()
    run = new_run(hil_device, "tim3", criteria=f"PC0 {expected:.0f} Hz +-3 %, duty 50 % (TIM3 DMA toggle, ATRLR {v.TIM3_RELOAD})")
    port = _setup(request, hil_config, run, hil_dut("tim3"))
    try:
        run.phase("settle", sleep, 0.5)
        rows = run.phase("measure", pwm_edge_survey, port.get("p"), PC0_GP, 8, 6, 200, 0.05)
        if rows is not None:
            run.meta["edge"] = run.phase("check", lambda: judge.judge_pwm_survey(
                rows[0], rows[1], expected, duty_expected_ppm=500_000, duty_tol_ppm=20_000, label="tim3"))
    finally:
        _finish(request, run, port, f"{prefix}tim3")


def run_usart2(request, hil_device, hil_config, hil_dut, new_run, prefix):
    only_v006(hil_device)
    run = new_run(hil_device, "usart2", criteria="PD2 -> GP14: 'usart2 0123456789' repeated at 115200 8N1 (PIO capture, >= 2 times in 1.2 s)")
    port = _setup(request, hil_config, run, hil_dut("usart2"))
    try:
        run.phase("settle", sleep, 0.3)
        res = run.phase("capture", captured, port.get("p"), "UART", USART2_GP, 115200, lambda client: sleep(1.2))
        if res is not None:
            run.meta["usart2"] = run.phase("check", v.judge_usart2, res[1])
    finally:
        _finish(request, run, port, f"{prefix}usart2")


def _opa_capture(port, duty, settle_ms=500, timeout_ms=3000):
    """Background UART capture of the DUT log while ADC_OBSERVE holds a PWM on GP13 (PA2's RC). Returns (status, bytes)."""
    def action(client):
        client.negotiate(["ADC_OBSERVE"])
        reply = client.request("ADC_OBSERVE", duty, settle_ms, timeout_ms, timeout=(settle_ms + timeout_ms) / 1000 + 4)
        # expected: ERR TIMEOUT adc_report (the book's report format is not the DUT's); anything else is not a stimulus run
        return reply.fields[:2]
    status, cap, _ = captured(port, "UART", UART_GP, 115200, action, settle_s=0.4, timeout=(settle_ms + timeout_ms) / 1000 + 8)
    if cap.overflow or cap.frame_errors:
        raise AssertionError(f"log capture lost data: overflow={cap.overflow} frame_errors={cap.frame_errors}")
    # the DUT's log is not the book's report: ADC_OBSERVE ends with TIMEOUT adc_report or, when its own UART receiver
    # overruns on the continuous log, ERR UART uart_errors=0x8 (overrun). Both happen after the PWM ran the whole time.
    if status[:1] not in (["TIMEOUT"], ["UART"]):
        raise AssertionError(f"ADC_OBSERVE did not run as a pure stimulus (expected TIMEOUT or UART overrun): {status}")
    return status, bytes(cap.items)


# +-10 %: the first measurements (2026-11-09, CH32V006) gave out/in 3.94 (gain 4) and 7.84 (gain 8), within 2.0 % of the
# gain; no gain-error figure was found in the resources, so the window keeps a margin of 5x the observed deviation.
OPA_TOL_PCT = 10.0
# (gain, duty % list judged, duty % recorded only (output near the rail)); the RC filters the 10 kHz PWM to ~duty * 3.3 V
OPA_CASES = {4: ([10, 20], [60]), 8: ([10], [40])}


def run_opa(request, hil_device, hil_config, hil_dut, new_run, prefix, gain):
    only_v006(hil_device)
    judged, recorded = OPA_CASES[gain]
    dut = dataclasses.replace(hil_dut("opa"), make_args=(f"EXTRA_CFLAGS=-DOPA_GAIN={gain}",))
    run = new_run(hil_device, "opa", variant=f"OPA_GAIN={gain}",
                  criteria=f"out/in (ADC_IN7 over ADC_IN0) median within the gain {gain} window; saturation recorded")
    port = _setup(request, hil_config, run, dut)
    results = {}
    try:
        for duty in judged + recorded:
            res = run.phase(f"measure_duty{duty}", _opa_capture, port.get("p"), duty)
            if res is None:
                continue
            rows = v.parse_opa(res[1])
            results[duty] = {"rows": rows[:20], "log_tail": res[1][-120:].decode("ascii", "replace")}
            if duty in judged:
                results[duty]["judged"] = run.phase(f"check_duty{duty}", lambda: v.judge_opa(
                    rows, gain, tol_pct=OPA_TOL_PCT, label=f"opa_gain{gain}_duty{duty}"))
            else:
                results[duty]["saturation"] = v.saturation_record(rows, gain)
    finally:
        run.meta["opa"] = results
        _finish(request, run, port, f"{prefix}opa_gain{gain}")


def run_tkey(request, hil_device, hil_config, hil_dut, new_run, prefix):
    only_v006(hil_device)
    run = new_run(hil_device, "tkey", criteria="reference observation: PD4 (floating) vs PA2 (10 kOhm + 1 uF); values recorded, "
                                              "no pass/fail on them (a touch cannot be simulated)")
    port = _setup(request, hil_config, run, hil_dut("tkey"))
    try:
        res = run.phase("capture", captured, port.get("p"), "UART", UART_GP, 115200, lambda client: sleep(2.6))
        if res is not None:
            rows = v.parse_tkey(bytes(res[1].items))
            run.meta["raw_tail"] = bytes(res[1].items)[-100:].decode("ascii", "replace")
            run.meta["tkey"] = run.phase("record", v.tkey_record, rows)
    finally:
        _finish(request, run, port, f"{prefix}tkey")
