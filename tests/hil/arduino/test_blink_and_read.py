"""HIL: Arduino Core CH32 blink_and_read (book-code blink_and_read-arduino_core_ch32), Pico GPIO/UART.

DESTRUCTIVE: rebuilds (arduino-cli, official core) and flashes the DUT with the pinned minichlink.
Run: uv run pytest --hil --hil-framework arduino -m 'hil and arduino' tests/hil/arduino/test_blink_and_read.py --hil-port=...

Expected values derived from samples_ch32v003_arduino/blink_and_read/blink_and_read.ino:
- Serial 115200 on PD5 (-> Pico GP9): "init\\r\\n", "start\\r\\n", then "loop <n>\\r\\n" with n = 0, 1, 2, ...
- PA1 (INPUT_PULLUP, <- Pico GP12 via RC) high: PC0 (-> Pico GP5) 500 ms high / 500 ms low.
- PA1 low: PC0 stays low (delay(1000) without toggling); blinking resumes when released.
"""
import re

import pytest

from ch32hil.pico import PicoError

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, check_square, find_port, new_run,
                     reset_and_capture_uart, sample_gpio, save)

pytestmark = [pytest.mark.hil, pytest.mark.arduino, pytest.mark.gpio, pytest.mark.uart]

SAMPLE = "blink_and_read"
BLINK_GP, SAMPLE_INTERVAL_US = 5, 10000
HALF_PERIOD_SAMPLES = 50          # delay(500) / 10 ms
TOLERANCE = 10                    # same +-100 ms window as the ch32fun blink test
BOOT_TEXT = b"init\r\nstart\r\nloop 0\r\nloop 1\r\n"


def _check_boot_uart(result):
    rx, fields = result
    text = rx.decode("ascii", "replace")
    if BOOT_TEXT not in rx:
        raise AssertionError(f"Serial boot output mismatch: rx={text!r} fields={fields}")
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


def test_arduino_blink_and_read(request, hil_device, hil_config, hil_dut):
    dut = hil_dut(SAMPLE)
    run = new_run(hil_device, SAMPLE, criteria="boot Serial text; PC0 500/500 ms; PA1 low pauses blink")
    print(f"HIL ARDUINO: {hil_device.part} {SAMPLE}; Pico GP5 (PC0), GP9 (PD5 TX), GP12 (PA1)")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        boot = run.phase("dut_reset", reset_and_capture_uart, dut, port.get("p"), 32, 5000)
        run.meta["uart_boot"] = run.phase("measure_uart", _check_boot_uart, boot) if boot else None
        runs = run.phase("measure_blink", sample_gpio, port.get("p"), BLINK_GP, 300, SAMPLE_INTERVAL_US)
        if runs is not None:
            run.meta["blink_runs"] = runs
            run.phase("check_blink", check_square, runs, HALF_PERIOD_SAMPLES, HALF_PERIOD_SAMPLES, TOLERANCE)
        run.meta["button"] = run.phase("measure_button", _button_pauses_blink, port.get("p"))
        resumed = run.phase("measure_resume", sample_gpio, port.get("p"), BLINK_GP, 300, SAMPLE_INTERVAL_US)
        if resumed is not None:
            run.meta["resume_runs"] = resumed
            run.phase("check_resume", check_square, resumed, HALF_PERIOD_SAMPLES, HALF_PERIOD_SAMPLES, TOLERANCE)
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "arduino_blink_and_read")
    print(run.to_json())
    assert run.ok, run.to_json()
