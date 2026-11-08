"""HIL: official WCH SDK timer_dma (book-code timer_dma-wch_sdk): 4-digit 7-segment scan by timer-triggered DMA.

DESTRUCTIVE: rebuilds and flashes the DUT. Run: uv run pytest --hil --hil-framework wch tests/hil/wch/test_timer_dma.py

The DUT (no UART output; PD5 is the display's SEL2) applies a new digit every ~100 us (full scan ~400 us) through
DMA writes to GPIOA/C/D->BSHR; digits show 0, 1, 2, 3. The Pico can only sample one pin per command at >= 1 ms, so the
scan is not resolved in time. What is judged is the fraction of High samples per pin (300 samples, 1.17 ms apart):
    cathodes SEL1 (PD6), SEL2 (PD5), SEL4 (PC0): Low only while their digit is active -> 3/4 High
    segments (High = lit): SA (PC4) 0,2,3 -> 3/4; SD (PD2) 0,2,3 -> 3/4; SE (PC7) 0,2 -> 1/2; SF (PC5) 0 -> 1/4;
    SG (PC6) 2,3 -> 1/2
Static outputs would read 0 % or 100 %. Tolerance +-0.10 (measured within ~0.02 of the expected fractions). A first attempt with 1 ms spacing aliased with the scan (PC7 read 2 runs, i.e. nearly constant).
Not observable with the fixed wiring: SB (PC3), SC (PD3), SEL3 (PD4), SDP (PA1 through the 10k/1 uF ADC network) and
the display itself, so "0123" on a real 4-digit display and the per-digit synchronisation of cathodes and segments are
unconfirmed. DMA channel configuration is checked in the code (static ELF symbols), not read back from registers.
"""
import time

import pytest

from .common import (_cleanup, _prepare, build_flash_readback, find_port, new_run, sample_gpio, save)
from .static_checks import symbols

pytestmark = [pytest.mark.hil, pytest.mark.wch, pytest.mark.gpio]

SAMPLE = "timer_dma"
TOLERANCE = 0.10
# 1000 us would beat with the 100.2 us digit step (10 steps = 1 ms: some pins read nearly constant); 1170 us is
# incommensurate with the 100.2/200.4/400.8 us periods, so the phase advances ~0.08..0.92 of a cycle per sample.
INTERVAL_US = 1170
# (DUT pin, Pico GPIO, expected fraction High)
# CH32V006: PC4 shows no signal on this DUT (cause not identified, see the PWM logs), so by the owner's decision PC4 SA is
# recorded but not judged there; the other seven pins are judged as before. Other devices judge all eight.
UNJUDGED = {"ch32v006": {"PC4 SA"}}
PINS = [("PD6 SEL1", 8, 0.75), ("PD5 SEL2", 9, 0.75), ("PC0 SEL4", 5, 0.75), ("PC4 SA", 15, 0.75),
        ("PD2 SD", 14, 0.75), ("PC7 SE", 4, 0.5), ("PC5 SF", 6, 0.25), ("PC6 SG", 7, 0.5)]


def _static_setup(elf):
    syms = symbols(elf)
    need = ("DMA_Init", "DMA_Cmd", "TIM_DMACmd", "TIM_OC1Init")
    missing = [n for n in need if n not in syms]
    if missing:
        raise AssertionError(f"timer/DMA setup functions not linked: {missing}")
    return "DMA_Init/DMA_Cmd/TIM_DMACmd/TIM_OC1Init linked"


def _fractions(port, unjudged=frozenset()):
    out = {}
    for name, gp, want in PINS:
        runs = sample_gpio(port, gp, 300, INTERVAL_US)
        high = sum(n for v, n in runs if v == "1")
        frac = high / 300
        out[name] = {"gp": gp, "high_fraction": round(frac, 3), "expected": want, "runs": len(runs)}
        if name in unjudged:
            out[name]["judged"] = False
        elif abs(frac - want) > TOLERANCE or not 0.1 < frac < 0.9:
            out[name]["fail"] = True
    bad = [k for k, v in out.items() if v.get("fail")]
    if bad:
        raise AssertionError(f"High fraction outside expectation for {bad}: {out}")
    return out


def test_wch_timer_dma(request, hil_device, hil_config, hil_dut):
    dut = hil_dut(SAMPLE)
    run = new_run(hil_device, SAMPLE, tolerance=TOLERANCE,
                  criteria="High fraction per pin over 300 x 1.17 ms samples: SEL1/SEL2/SEL4/SA/SD 0.75, SE/SG 0.5, SF 0.25 "
                           "(+-0.10); unobserved: SB, SC, SEL3, SDP, display")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.meta["static"] = run.phase("static_setup_check", _static_setup, dut.sample_dir / "main.elf")
        run.phase("dut_reset", dut.reset)
        # The scan starts ~100 ms after reset; sampling PD6 at once after reset read it low for the pre-init part
        # (High fraction 0.56-0.73 in 4 of 6 early attempts, 0.75 afterwards with the same code).
        run.phase("settle", time.sleep, 1.0)
        run.meta["fractions"] = run.phase("measure_fractions", _fractions, port.get("p"), UNJUDGED.get(hil_device.name, frozenset()))
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "wch_timer_dma")
    print(run.to_json())
    assert run.ok, run.to_json()
