"""HIL: official WCH SDK pwm (book-code pwm-wch_sdk), measured by the Pico with GPIO_PULSE.

DESTRUCTIVE: rebuilds and flashes the DUT. Run: uv run pytest --hil --hil-framework wch tests/hil/wch/test_pwm.py

DUT: TIM1, 256 counts per period at 48 MHz / 2 -> period 10.67 us (93.75 kHz). CH1 (PD2 -> GP14) ramps 1/32 steps up
and back down (31 ms steps, ~2.1 s per cycle). CH4 (PC4 -> GP15) gets the book's 128*(33-i)-1, which is above the
8-bit period for almost every step: it stays high (no edges) during most of the up phase and ramps only at its end
and during the down phase. GPIO_PULSE has 1 us resolution (duty steps of ~9 %) and is uncalibrated, so only coarse
properties are judged: period 9..12 us (the Pico quantises 10.67 us to 10 or 11), several distinct duty levels on PD2
spread over at least 35 %, (readings whose High pulse is under 2 us or Low pulse under 3 us, or duty outside 15..95 %, are counted as unresolved, not judged), and CH4 showing both high-constant (timeout) and ramping readings. One capture lasts
longer than one ramp cycle (~2.1 s) so that both directions occur.
"""
import time

import pytest

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, find_port, new_run, save)

pytestmark = [pytest.mark.hil, pytest.mark.wch, pytest.mark.pwm]

SAMPLE = "pwm"
PD2_GP, PC4_GP = 14, 15
PERIOD_US = (9, 12)
PAIRS, PAIR_GAP_S = 36, 0.04   # ~2.2 s: longer than one ~2.1 s ramp cycle
SATURATED_PPM = 950_000
UNRESOLVED_LOW_PPM = 150_000   # High pulse under ~1.6 us: edges are lost


def _pulse(client, pin):
    reply = client.request("GPIO_PULSE", pin, 30)
    fields = dict(f.split("=", 1) for f in reply.fields if "=" in f)
    if not reply.ok:
        return {"pin": pin, "timeout": True}
    return {"pin": pin, "period_us": int(fields["period_us"]), "high_us": int(fields["high_us"]),
            "duty_ppm": int(fields["duty_ppm"])}


def _capture(port):
    def action(client):
        client.negotiate(["GPIO_PULSE"])
        out, t0 = [], time.monotonic()
        for _ in range(PAIRS):
            out.append((_pulse(client, PD2_GP), _pulse(client, PC4_GP), round(time.monotonic() - t0, 3)))
            time.sleep(PAIR_GAP_S)
        return out
    return _with_client(port, PAIRS * 0.4 + 5, action)


def _check(pairs):
    pd2 = [a for a, _, _ in pairs if "duty_ppm" in a]
    pc4 = [b for _, b, _ in pairs if "duty_ppm" in b]
    pc4_const = [b for _, b, _ in pairs if b.get("timeout")]
    # The Pico sees 1 us steps: a High pulse under 2 us or a Low pulse under 3 us (duty near 0 % or 100 %, e.g. k=1 is 0.33 us) can
    # lose edges and yields meaningless periods (seen: 33, 43, 86, 22, 235 us). Such readings are counted as out of
    # resolution instead of judged; they only occur at the extreme duties of the ramp.
    def resolvable(m):
        return (m["high_us"] >= 2 and m["period_us"] - m["high_us"] >= 3
                and UNRESOLVED_LOW_PPM <= m["duty_ppm"] <= SATURATED_PPM)
    unresolved = [m for m in pd2 + pc4 if not resolvable(m)]
    pd2 = [m for m in pd2 if resolvable(m)]
    pc4 = [m for m in pc4 if resolvable(m)]
    bad = [m for m in pd2 + pc4 if not PERIOD_US[0] <= m["period_us"] <= PERIOD_US[1]]
    if bad:
        raise AssertionError(f"period outside {PERIOD_US} us (expected 10.67 us): {bad}")
    if len(pd2) < 10:
        raise AssertionError(f"too few PD2 measurements ({len(pd2)}/{PAIRS}): {pairs}")
    duties = [m["duty_ppm"] for m in pd2]
    levels = sorted({m["high_us"] for m in pd2})
    if max(duties) - min(duties) < 350_000 or len(levels) < 3:
        raise AssertionError(f"PD2 duty does not ramp (range {min(duties)}..{max(duties)} ppm, high_us levels {levels})")
    if len(pc4) < 3 or max(m["duty_ppm"] for m in pc4) - min(m["duty_ppm"] for m in pc4) < 200_000:
        raise AssertionError(f"PC4 (CH4) shows no ramp: {pc4}")
    if not pc4_const:
        raise AssertionError("PC4 never stayed high (book formula 128*(33-i)-1 exceeds the period): unexpected")
    return {"pd2_duty_range_ppm": [min(duties), max(duties)], "pd2_high_us_levels": levels,
            "pd2_measurements": len(pd2), "unresolved_readings": len(unresolved), "pc4_measurements": len(pc4), "pc4_high_constant_readings": len(pc4_const),
            "pc4_duty_ppm": [m["duty_ppm"] for m in pc4]}


def test_wch_pwm(request, hil_device, hil_config, hil_dut):
    dut = hil_dut(SAMPLE)
    run = new_run(hil_device, SAMPLE, criteria="period 9..12 us (10.67 us nominal); PD2 several duty levels over >=35 %; "
                                              "PC4 high-constant and ramping readings; coarse, uncalibrated")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.phase("dut_reset", dut.reset)
        pairs = run.phase("capture", _capture, port.get("p"))
        if pairs is not None:
            run.meta["pairs"] = [[a, b, t] for a, b, t in pairs]
            run.meta["summary"] = run.phase("check", _check, pairs)
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "wch_pwm")
    print(run.to_json())
    assert run.ok, run.to_json()
