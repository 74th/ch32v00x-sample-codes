"""HIL: Arduino Core CH32 uart (book-code uart-arduino_core_ch32): CO2 sensor over UART, result shown on an OLED.

DESTRUCTIVE: rebuilds and flashes the DUT with the pinned minichlink.

The sketch sends a 9-byte read command at 9600 baud, waits up to 1 s (Serial.readBytes default) for a 9-byte reply,
and draws "loop: n" plus "co2 : <ppm> ppm" (or "timeout" / an error text) with the OLED library. The Pico plays the
sensor (UART) and the SSD1306 (I2C slave), but its commands are exclusive. So the reply is queued in the DUT's
interrupt-driven RX buffer first, and the capture is armed after that, before the DUT's next loop():

  reset -> Pico captures the DUT's read command of loop 1 (no answer: loop 1 shows "timeout")
  -> sleep over the 1 s timeout and display -> Pico sends the known frame (1234 ppm) into the RX buffer
  -> Pico arms SSD1306_CAPTURE without INIT, with a 1.5 s limit -> DUT loop 2 sends its command, reads the queued
     frame at once and draws "co2 : 1234 ppm" (~0.75 s after the arm, display ~0.15 s); loop 3 would draw ~2.8 s after.

Two properties of the Pico model, measured on CH32V003, shape the judgement:
- Without INIT the model has not seen the display initialisation, so it stays in page addressing mode: each display()
  overwrites pages 0..N-1 and no frame ever completes (the capture ends with ERR TIMEOUT by design). The 1.5 s limit
  lies between the loop 2 and loop 3 displays, so the model holds the loop 2 screen.
- The data of the last I2C transfer is committed only at the next START, so the last page of the last display is
  not in the model yet. Only pages 0..N-2 are compared (the sketch draws the CO2 line in them: y=20 on 128x32, whose
  top half is in page 2; y=0 in the 96x16 variant).

Expected screens are rendered on the host from the sketch itself and the pinned library with the same scripted
sensor answers (oled_expected.expected_uart_screens), so the value read by the DUT is checked as drawn pixels.
The calibration command at boot is not asserted: it is sent before the Pico UART is listening.
"""
import tempfile
import time
from pathlib import Path

import pytest

from ch32hil.pico import PicoError

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, fields_of, find_port, new_run, save)
from .oled_expected import expected_uart_screens

pytestmark = [pytest.mark.hil, pytest.mark.arduino, pytest.mark.uart, pytest.mark.i2c]

SAMPLE = "uart"
# CH32V003 cannot allocate the 128x32 buffer (heap 504 B), so it runs the 96x16 variant (2 pages of 96 columns,
# status line moved to y=0 so that it is in a committed page).
GEOMETRY = {"default": {"sample": SAMPLE, "width": 128, "pages": 4},
            "ch32v003": {"sample": "uart_96x16", "width": 96, "pages": 2}}
CAPTURE_MS = 1500
BAUD = 9600
PPM = 1234
CMD_SELF_CAL = bytes([0xFF, 0x01, 0x79, 0xA0, 0, 0, 0, 0, 0xE6])
CMD_READ = bytes([0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0x79])
SETTLE_S = 1.3        # loop 1: readBytes timeout (1 s) + display, then delay(1000) is running when the frame is sent


def frame(ppm):
    f = bytearray([0xFF, 0x86, ppm >> 8, ppm & 0xFF, 0, 0, 0, 0, 0])
    f[8] = (0xFF - sum(f[1:8]) + 1) & 0xFF
    return bytes(f)


def xfer(port, tx: bytes, rx_count: int, timeout_ms: int):
    def action(client):
        reply = client.request("UART_XFER", "DUT", BAUD, 8, "N", 1, tx.hex() if tx else "-", rx_count, timeout_ms)
        fields = fields_of(reply)
        if not reply.ok and "rx" not in fields:
            raise PicoError(f"UART_XFER failed: {reply.fields}")
        return (b"" if fields.get("rx", "-") == "-" else bytes.fromhex(fields["rx"])), fields
    return _with_client(port, timeout_ms / 1000 + 3, action)


def capture_read_command(port):
    """Read 9-byte frames from the DUT until the read command of loop 1 arrives (a leading self-calibration
    command may be caught first, depending on when the Pico UART starts listening)."""
    seen = []
    for _ in range(3):
        rx, _ = xfer(port, b"", 9, 4000)
        seen.append(rx.hex())
        if rx == CMD_READ:
            return seen
    raise AssertionError(f"read command not seen: {seen}")


def arm_capture(port):
    def action(client):
        client.negotiate(["SSD1306_CAPTURE", "SSD1306_PAGE"])
        reply = client.request("SSD1306_CAPTURE", 1, CAPTURE_MS)
        fields = fields_of(reply)
        pages = []
        for page in range(8):
            res = client.request("SSD1306_PAGE", page)
            pages.append(fields_of(res).get("fb") if res.ok else None)
        return reply.ok, fields, pages
    return _with_client(port, CAPTURE_MS / 1000 + 12, action)


def _check(capture, expected, geometry):
    ok, fields, pages = capture
    width, per = geometry["width"], geometry["pages"]
    problems = []
    for key, want in (("bad_control", "0"), ("overflow", "0")):
        if fields.get(key) != want:
            problems.append(f"{key}={fields.get(key)} (want {want})")
    if int(fields.get("data", "0")) < (per - 1) * width:
        problems.append(f"loop 2 display() not seen: data={fields.get('data')}")
    screen = expected[1]                               # loop 2: the answered one
    diff = []
    for p in range(per - 1):                           # the last page is still pending in the model (see docstring)
        page = bytes.fromhex(pages[p]) if pages[p] else None
        if page is None or page[:width] != screen[p] or any(page[width:]):
            diff.append(p)
    if not any(any(page) for page in screen[:per - 1]):
        problems.append("host-rendered expected screen is blank")
    if diff:
        problems.append(f"co2 screen (loop 2): model pages differing from the host-rendered buffer: {diff}")
    if problems:
        raise AssertionError("; ".join(problems) + f" | capture={fields}")
    return {"data": fields.get("data"), "crc32": fields.get("crc32")}


def test_arduino_uart_co2_to_oled(request, hil_device, hil_config, hil_dut):
    geometry = GEOMETRY.get(hil_device.name, GEOMETRY["default"])
    sample = geometry["sample"]
    if not (hil_device.sample_dir(sample) / "Makefile").is_file():
        pytest.skip(f"{hil_device.name}: no {sample} sample")
    dut = hil_dut(sample)
    run = new_run(hil_device, sample, panel=f"{geometry['width']}x{geometry['pages'] * 8}", library="OLED SSD1306 - SH1106 1.0.7", sensor_ppm=PPM,
                  criteria="OLED model after loop 2 shows the 1234 ppm the Pico sensor sent; "
                           "pixels equal the host-rendered library buffer")
    port = {}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            expected = run.phase("expected", expected_uart_screens, dut.sample_dir / f"{sample}.ino", Path(tmp),
                                 ["-", frame(PPM).hex()])
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.phase("dut_restart", dut.wait_ready, "reset")
        run.meta["commands_seen"] = run.phase("read_command_loop1", capture_read_command, port["p"])
        run.phase("settle", time.sleep, SETTLE_S)
        run.phase("send_frame", xfer, port["p"], frame(PPM), 0, 500)
        captured = run.phase("capture_display", arm_capture, port["p"])
        if captured is not None and expected is not None:
            ok, fields, pages = captured
            run.meta["capture"] = fields
            run.meta["pages"] = pages
            run.meta["expected_screens"] = [[p.hex() for p in s] for s in expected]
            run.meta["summary"] = run.phase("check", _check, captured, expected, geometry)
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "arduino_uart")
    print(run.to_json())
    assert run.ok, run.to_json()
