"""HIL: official WCH SDK sleep_wake (book-code sleep_mode_blink-wch_sdk): Sleep (WFI) woken by a TIM1 update interrupt.

DESTRUCTIVE: rebuilds and flashes the DUT. Run: uv run pytest --hil --hil-framework wch tests/hil/wch/test_sleep_wake.py

DUT: every 2 s the TIM1_UP interrupt fires. The main loop toggles the LED (PC0 -> GP5), prints "sleep" on PD5 and executes
__WFI(). Per cycle the UART shows the wake chain: "tim" (interrupt handler) -> "awake" -> "sleep" (19 bytes, every 2 s).
If WFI returned at once the text would be "sleep awake sleep awake ..." with no "tim" and no 2 s spacing.
Judged: (a) the ELF contains a wfi instruction, (b) the UART lines follow the cycle tim -> awake -> sleep, and 32 bytes (more than one 19-byte burst) take
>= 1.8 s to arrive (not a busy loop), (c) the LED toggles every ~2 s (half period 1.6..2.4 s).
Power consumption is NOT measured: nothing here shows that the core is clock-gated, only that it waits for the interrupt.
"""
import time

import pytest

from .common import (_cleanup, _prepare, build_flash_readback, find_port, new_run, sample_gpio, save, uart_receive)
from ch32hil.dut import ROOT
from .static_checks import _run

pytestmark = [pytest.mark.hil, pytest.mark.wch, pytest.mark.gpio]

SAMPLE = "sleep_wake"
BLINK_GP = 5
INTERVAL_US = 50000          # 300 samples x 50 ms = 15 s: more than 3 half periods
CYCLE = ["tim", "awake", "sleep"]


def _has_wfi(elf):
    if "wfi" not in _run("objdump", "-d", elf):
        raise AssertionError("no wfi instruction in the ELF")
    return "wfi present"


def _cycle_text(port):
    t0 = time.monotonic()
    rx, fields = uart_receive(port, 32, 5000)
    elapsed = round(time.monotonic() - t0, 2)
    lines = rx.decode("ascii", "replace").split("\r\n")
    lines = [l for l in lines[1:-1] if l]      # drop the possibly partial first and last line
    if len(lines) < 2 or fields.get("uart_errors") != "0x0":
        raise AssertionError(f"too few lines: {rx!r} {fields}")
    for a, b in zip(lines, lines[1:]):
        if CYCLE[(CYCLE.index(a) + 1) % 3] != b:
            raise AssertionError(f"line order broken ({a} -> {b}): {lines}")
    if elapsed < 1.8:
        raise AssertionError(f"32 bytes arrived in {elapsed} s: the DUT is not waiting 2 s between wakes")
    return {"lines": lines, "elapsed_s": elapsed}


def _check_toggle(runs):
    complete = runs[1:-1]
    if len(complete) < 3 or {v for v, _ in complete} != {"0", "1"}:
        raise AssertionError(f"LED does not toggle: {runs}")
    half_s = [n * INTERVAL_US / 1e6 for _, n in complete]
    if not all(1.6 <= h <= 2.4 for h in half_s):
        raise AssertionError(f"half periods {half_s} s outside 1.6..2.4 s: {runs}")
    return half_s


def test_wch_sleep_wake(request, hil_device, hil_config, hil_dut):
    dut = hil_dut(SAMPLE)
    run = new_run(hil_device, SAMPLE, limitation="power consumption not measured",
                  criteria="wfi in ELF; UART cycle tim -> awake -> sleep every ~2 s; LED half period 1.6..2.4 s")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.meta["static"] = run.phase("static_wfi_check", _has_wfi, dut.sample_dir / "main.elf")
        run.phase("dut_reset", dut.reset)
        run.phase("settle", time.sleep, 1.0)
        run.meta["uart"] = run.phase("check_uart_cycle", _cycle_text, port.get("p"))
        runs = run.phase("measure_led", sample_gpio, port.get("p"), BLINK_GP, 300, INTERVAL_US)
        if runs is not None:
            run.meta["led_runs"] = runs
            run.meta["half_periods_s"] = run.phase("check_led_toggle", _check_toggle, runs)
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "wch_sleep_wake")
    print(run.to_json())
    assert run.ok, run.to_json()
