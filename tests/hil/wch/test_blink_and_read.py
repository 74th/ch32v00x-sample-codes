"""HIL: official WCH SDK blink_and_read (book-code blink_and_read-wch_sdk), Pico GPIO/UART.

DESTRUCTIVE: rebuilds (WCH GCC, official SDK) and flashes the DUT with the pinned minichlink.
Run: uv run pytest --hil --hil-framework wch -m "hil and wch" tests/hil/wch/test_blink_and_read.py --hil-port=...

Expected values derived from samples_ch32v003_wch/blink_and_read/main.c:
- USART printf 115200 on PD5 (-> Pico GP9): "init\\r\\n", "start\\r\\n", then "loop <n>\\r\\n" with n = 0, 1, 2, ...
- PA1 (INPUT_PULLUP, <- Pico GP12 via RC) high: PC0 (-> Pico GP5) 500 ms high / 500 ms low.
- PA1 low: PC0 stays low (delay(1000) without toggling); blinking resumes when released.
"""
import re
import time

import pytest

from ch32hil.pico import PicoError

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, check_square, find_port, new_run,
                     reset_during, sample_gpio, save, uart_receive)

pytestmark = [pytest.mark.hil, pytest.mark.wch, pytest.mark.gpio, pytest.mark.uart]

SAMPLE = "blink_and_read"
BLINK_GP, SAMPLE_INTERVAL_US = 5, 10000
HALF_PERIOD_SAMPLES = 50          # delay(500) / 10 ms
TOLERANCE = 10                    # same +-100 ms window as the ch32fun blink test
# `minichlink -b` restarts the DUT twice within ~0.5 s (seen on this rig as "init start loop 0 init start"), so only the
# first three lines of a boot are required; "loop 1" is covered by the periodic blink/loop checks below.
BOOT_TEXT = b"init\r\nstart\r\nloop 0\r\n"


def _check_boot_uart(result):
    rx, fields = result
    text = rx.decode("ascii", "replace")
    if BOOT_TEXT not in rx:
        raise AssertionError(f"UART boot output mismatch: rx={text!r} fields={fields}")
    numbers = [int(n) for n in re.findall(r"loop (\d+)\r\n", text)]
    if numbers != list(range(len(numbers))):
        raise AssertionError(f"loop counter not consecutive from 0: {numbers} rx={text!r}")
    return {"rx": text, "uart_errors": fields.get("uart_errors"), "received": fields.get("received")}


def _button_pauses_blink(port):
    def action(client):
        client.negotiate(["GPIO_BUTTON_TEST", "GPIO_SAMPLE"])
        result = client.request("GPIO_BUTTON_TEST", 3000)
        if not result.ok:
            raise PicoError(f"button drive failed: {result.fields}")
        fields = dict(x.split("=", 1) for x in result.fields if "=" in x)
        if int(fields.get("samples", "0")) < 30 or fields.get("high") != "0":
            raise AssertionError(f"blink did not pause while PA1 was low: {fields}")
        return fields
    return _with_client(port, 6, action)


def test_wch_blink_and_read(request, hil_device, hil_config, hil_dut):
    dut = hil_dut(SAMPLE)
    run = new_run(hil_device, SAMPLE, criteria="boot Serial text; PC0 500/500 ms; PA1 low pauses blink")
    print(f"HIL ARDUINO: {hil_device.part} {SAMPLE}; Pico GP5 (PC0), GP9 (PD5 TX), GP12 (PA1)")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        # Every minichlink call restarts the DUT; settle 1.5 s so the earlier restart's boot output is over before the capture
        # is armed (with settle 0 the capture could fill with two overlapping boots: "init start loop 0 init start").
        boot = run.phase("dut_reset", reset_during, dut, lambda: uart_receive(port.get("p"), 32, 5000), 5, 0.3, 1.5)
        run.meta["uart_boot"] = run.phase("measure_uart", _check_boot_uart, boot) if boot else None
        runs = run.phase("measure_blink", sample_gpio, port.get("p"), BLINK_GP, 300, SAMPLE_INTERVAL_US)
        if runs is not None:
            run.meta["blink_runs"] = runs
            run.phase("check_blink", check_square, runs, HALF_PERIOD_SAMPLES, HALF_PERIOD_SAMPLES, TOLERANCE)
        run.meta["button"] = run.phase("measure_button", _button_pauses_blink, port.get("p"))
        # The pause is a 1 s Delay_Ms, so up to 1 s of low can follow the release (GPIO_SAMPLE max is 300 points):
        # wait that out before sampling the resumed blink.
        time.sleep(1.2)
        resumed = run.phase("measure_resume", sample_gpio, port.get("p"), BLINK_GP, 300, SAMPLE_INTERVAL_US)
        if resumed is not None:
            run.meta["resume_runs"] = resumed
            run.phase("check_resume", check_square, resumed, HALF_PERIOD_SAMPLES, HALF_PERIOD_SAMPLES, TOLERANCE)
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "wch_blink_and_read")
    print(run.to_json())
    assert run.ok, run.to_json()
