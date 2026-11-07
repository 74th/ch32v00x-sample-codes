"""HIL: official WCH SDK uart (book-code uart-wch_sdk): the Pico plays the CO2 sensor on PD5/PD6 (9600 8N1).

DESTRUCTIVE: rebuilds and flashes the DUT. Run: uv run pytest --hil --hil-framework wch tests/hil/wch/test_uart.py
Sequence (the Pico UART is half-duplex per call; the DUT waits 500 ms per byte and 1 s between loops):
  reset -> DUT sends self-calibration command -> Pico answers 9 bytes -> DUT prints "start"
  -> DUT sends read command -> Pico answers a known frame -> DUT prints "CO2:  1234 ppm"
  -> bad checksum frame -> "invalid checksum" + value -> no answer -> "read timeout"
"""
import pytest

from ch32hil.pico import PicoError
from .common import (_cleanup, _prepare, _with_client, build_flash_readback, fields_of, find_port,
                     new_run, save)

pytestmark = [pytest.mark.hil, pytest.mark.wch, pytest.mark.uart]

SAMPLE = "uart"
BAUD = 9600
CMD_SELF_CAL = bytes([0xFF, 0x01, 0x79, 0xA0, 0, 0, 0, 0, 0xE6])
CMD_READ = bytes([0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0x79])


def frame(ppm, bad=False):
    f = bytearray([0xFF, 0x86, ppm >> 8, ppm & 0xFF, 0, 0, 0, 0, 0])
    f[8] = (0xFF - sum(f[1:8]) + 1) & 0xFF
    if bad:
        f[8] ^= 0x01
    return bytes(f)


def xfer(port, tx: bytes, rx_count: int, timeout_ms: int):
    def action(client):
        reply = client.request("UART_XFER", "DUT", BAUD, 8, "N", 1, tx.hex() if tx else "-", rx_count, timeout_ms)
        fields = fields_of(reply)
        if "rx" not in fields:
            raise PicoError(f"UART_XFER failed: {reply.fields}")
        return (b"" if fields["rx"] == "-" else bytes.fromhex(fields["rx"])), fields
    return _with_client(port, timeout_ms / 1000 + 3, action)


def expect_command(port, want):
    rx, fields = xfer(port, b"", 9, 3000)
    if rx != want:
        raise AssertionError(f"DUT command mismatch: got {rx.hex()} want {want.hex()} {fields}")
    return rx.hex()


def answer(port, tx, text):
    rx, fields = xfer(port, tx, len(text), 3000)
    if rx != text:
        raise AssertionError(f"DUT text mismatch: got {rx!r} want {text!r} {fields}")
    if fields.get("uart_errors") != "0x0":
        raise AssertionError(f"uart errors: {fields}")
    return rx.decode()


def test_wch_uart_co2(request, hil_device, hil_config, hil_dut):
    dut = hil_dut(SAMPLE)
    run = new_run(hil_device, SAMPLE, criteria="Pico as sensor: known frame -> CO2 text; bad checksum; timeout")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        # Boot: `minichlink -i` (wait_ready) restarts the DUT, which then waits 200 ms before its first frame,
        # the self-calibration request. Capture it right after wait_ready; an extra reset would repeat the boot
        # and, in a first attempt, produced the command twice.
        run.phase("dut_restart", dut.wait_ready, "reset")
        rx, _ = run.phase("capture_boot_command", xfer, port["p"], b"", 9, 4000) or (None, None)
        run.phase("check_self_calibration_command", lambda: rx == CMD_SELF_CAL or (_ for _ in ()).throw(
            AssertionError(f"self calibration command mismatch: {rx!r}")))
        run.meta["start"] = run.phase("answer_self_calibration", answer, port["p"], frame(0), b"start\r\n")
        run.phase("read_command_1", expect_command, port["p"], CMD_READ)
        run.meta["known"] = run.phase("known_frame", answer, port["p"], frame(1234), b"CO2:  1234 ppm\r\n")
        run.phase("read_command_2", expect_command, port["p"], CMD_READ)
        run.meta["bad_checksum"] = run.phase("bad_checksum", answer, port["p"], frame(800, bad=True),
                                             b"invalid checksum\r\n")
        run.phase("rest_of_bad_line", xfer, port["p"], b"", 16, 3000)  # drains "CO2:   800 ppm"
        run.phase("read_command_3", expect_command, port["p"], CMD_READ)
        # No answer: the DUT times out after 500 ms and says so.
        rx, _ = run.phase("no_answer", xfer, port["p"], b"", 14, 3000) or (None, None)
        run.phase("check_timeout_text", lambda: rx == b"read timeout\r\n" or (_ for _ in ()).throw(
            AssertionError(f"timeout text mismatch: {rx!r}")))
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "wch_uart")
    print(run.to_json())
    assert run.ok, run.to_json()
