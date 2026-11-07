"""HIL: official WCH SDK timer_blink (book-code timer_blink-wch_sdk): LED toggled from TIM1 / TIM2 update interrupts.

DESTRUCTIVE: rebuilds (twice: USE_TIM1=1 and USE_TIM1=0) and flashes the DUT.
Run: uv run pytest --hil --hil-framework wch tests/hil/wch/test_timer_blink.py

Both variants toggle PC0 (-> GP5) every 500 ms (TIM1: 100 ms period x repetition 5; TIM2: 500 ms period) and print the
book's event text on PD5: "1sec event" (TIM1) / "500ms event" (TIM2). The two are told apart by that text. Interrupt
attributes are checked statically on the ELF: the handler sits in the vector slot of its IRQ number (TIM1_UP = 35,
TIM2 = 38) and returns with mret (WCH-Interrupt-fast).
"""
import pytest

from .common import (_cleanup, _prepare, build_flash_readback, check_square, find_port, new_run, reset_and_capture_uart,
                     sample_gpio, save, uart_receive)
from .static_checks import check_irq_handler
from ch32hil.dut import ROOT

pytestmark = [pytest.mark.hil, pytest.mark.wch, pytest.mark.gpio]

SAMPLE = "timer_blink"
BLINK_GP, INTERVAL_US, HALF = 5, 10000, 50
TOLERANCE = 10          # +-100 ms, as the other blink tests
VARIANTS = {
    "tim1": ("EXTRA_CFLAGS=-DUSE_TIM1=1", b"1sec event\r\n", "TIM1_UP_IRQHandler", 35),
    "tim2": ("EXTRA_CFLAGS=-DUSE_TIM1=0", b"500ms event\r\n", "TIM2_IRQHandler", 38),
}


def _event_text(port, event):
    """Mid-run capture (the boot register dump is longer than one 32 B capture): >= 2 event lines, none of the other timer's."""
    rx, fields = uart_receive(port, 32, 3000)
    other = b"500ms event" if event.startswith(b"1sec") else b"1sec event"
    if rx.count(event) < 2 or other in rx or fields.get("uart_errors") != "0x0":
        raise AssertionError(f"event text {event!r} (x2) not seen: rx={rx!r} {fields}")
    return rx.decode("ascii", "replace")


@pytest.mark.parametrize("variant", sorted(VARIANTS))
def test_wch_timer_blink(request, hil_device, hil_config, hil_dut, variant):
    flag, event, handler, irqn = VARIANTS[variant]
    dut = hil_dut(SAMPLE)
    dut.make_args = (flag,)          # cleans first, so the other variant can never be flashed by mistake
    run = new_run(hil_device, SAMPLE, variant=variant, make_args=flag,
                  criteria=f"PC0 500/500 ms (+-100 ms); '{event.decode().strip()}' text; {handler} in vector slot "
                           f"{16 + irqn} and returns with mret")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.meta["interrupt"] = run.phase("static_interrupt_check", check_irq_handler,
                                          dut.sample_dir / "main.elf", handler, irqn)
        boot = run.phase("dut_reset", reset_and_capture_uart, dut, port.get("p"), 32, 5000)
        run.meta["boot_uart"] = boot and boot[0].decode("ascii", "replace")
        runs = run.phase("measure_blink", sample_gpio, port.get("p"), BLINK_GP, 300, INTERVAL_US)
        if runs is not None:
            run.meta["blink_runs"] = runs
            run.phase("check_blink", check_square, runs, HALF, HALF, TOLERANCE)
        run.meta["uart"] = run.phase("check_event_text", _event_text, port.get("p"), event)
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, f"wch_timer_blink_{variant}")
    print(run.to_json())
    assert run.ok, run.to_json()
