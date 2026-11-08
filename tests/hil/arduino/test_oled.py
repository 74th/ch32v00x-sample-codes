"""HIL: Arduino Core CH32 i2c_oled (book-code i2c_oled-arduino_core_ch32), observed by the Pico SSD1306 model.

DESTRUCTIVE: rebuilds and flashes the DUT with the pinned minichlink.

The sketch draws a 32x32 bitmap, "@74th", "CH32V003" and a rectangle on a 128x32 SSD1306 at 0x3C, through the
library "OLED SSD1306 - SH1106" 1.0.7 (software I2C on PC1/PC2 = the fixed I2C wiring to Pico GP10/GP11), then
display() every ~500 ms. The library uses horizontal addressing and sends 0xB0+page and 0x21 0 127 before each
128-byte page, never 0x22. With the datasheet behaviour now modelled by the Pico (0x21 resets only the column
pointer), successive pages and successive display() calls fill pages 0..3 then 4..7 of the 128x64 model.

Expected values: the library buffer rendered on the host from the same sketch and library (oled_expected.py).
Judgement: model pages 0..3 equal the rendered pages 0..3 (what a 128x32 panel shows) and pages 4..7 equal them as
well (the next display() call); display on, charge pump on, no bad control bytes or overflow. A real OLED is not
used.
"""
import tempfile
from pathlib import Path

import pytest

from test_extralibs import _capture_across_dut_reset  # tests/hil (ch32fun) helper: arm capture, then reset

from .common import _cleanup, _prepare, build_flash_readback, find_port, new_run, save
from .oled_expected import expected_pages

pytestmark = [pytest.mark.hil, pytest.mark.arduino, pytest.mark.i2c]

SAMPLE = "i2c_oled"


def _check(got, pages, expected):
    ok, fields = got
    problems = []
    if not ok:
        problems.append("capture did not complete")
    for key, want in (("bad_control", "0"), ("overflow", "0"), ("display_on", "1"), ("display_on_seen", "1"),
                      ("charge_pump", "1")):
        if fields.get(key) != want:
            problems.append(f"{key}={fields.get(key)} (want {want})")
    diff = [p for p in range(8) if pages[p] is None or bytes.fromhex(pages[p]) != expected[p % 4]]
    if diff:
        problems.append(f"model pages differing from the host-rendered buffer: {diff}")
    if problems:
        raise AssertionError("; ".join(problems) + f" | capture={fields}")
    return {"frames": fields.get("frames"), "unknown": fields.get("unknown"), "crc32": fields.get("crc32")}


# CH32V003 + official core 1.0.6: the library's malloc(512) for the frame buffer fails (heap 0x20000448..0x20000640 =
# 504 B; GCC 15 newlib's __sf/__atexit0 take RAM), the buffer is NULL and display() sends flash from address 0
# (okf/log/2026-11-07-2232-ch32v003-after-swap-uart-fault.md). Strict: an XPASS shows the problem went away.
KNOWN_FAILURE = {"ch32v003": "official core 1.0.6 on CH32V003: malloc(512) for the OLED buffer fails (heap 504 B)"}


def test_arduino_i2c_oled(request, hil_device, hil_config, hil_dut):
    if hil_device.name in KNOWN_FAILURE:
        request.node.add_marker(pytest.mark.xfail(reason=KNOWN_FAILURE[hil_device.name], strict=True))
    dut = hil_dut(SAMPLE)
    run = new_run(hil_device, SAMPLE, library="OLED SSD1306 - SH1106 1.0.7",
                  criteria="SSD1306 model pages 0..3 and 4..7 equal the host-rendered 128x32 buffer; display on")
    print("HIL ARDUINO i2c_oled: DUT software I2C PC1/PC2 -> Pico SSD1306 model at 0x3C on GP10/GP11")
    port = {}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            expected = run.phase("expected", expected_pages, dut.sample_dir / f"{SAMPLE}.ino", Path(tmp))
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        captured = run.phase("measure", _capture_across_dut_reset, port.get("p"), dut, 2, 5000)
        if captured is not None and expected is not None:
            ok, fields, pages = captured
            run.meta["capture"] = fields
            run.meta["pages"] = pages
            run.meta["expected_pages"] = [p.hex() for p in expected]
            run.meta["summary"] = run.phase("check", _check, (ok, fields), pages, expected)
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "arduino_i2c_oled")
    print(run.to_json())
    assert run.ok, run.to_json()


# ---- CH32V003 only: 96x16 variant (192 B buffer) so that the library's malloc fits in the 504 B heap ----
SMALL_SAMPLE = "i2c_oled_96x16"
SMALL_WIDTH, SMALL_PAGES = 96, 2


def _check_small(got, pages, expected):
    """The 96x16 sketch fills two pages of 96 columns per display(); the model holds 128x64, so 4 display() calls
    cover pages 0..7. Columns 96..127 are never written and must stay 0."""
    ok, fields = got
    problems = []
    if not ok:
        problems.append("capture did not complete")
    for key, want in (("bad_control", "0"), ("overflow", "0"), ("display_on", "1"), ("display_on_seen", "1"),
                      ("charge_pump", "1")):
        if fields.get(key) != want:
            problems.append(f"{key}={fields.get(key)} (want {want})")
    diff = []
    for p in range(8):
        page = bytes.fromhex(pages[p]) if pages[p] else None
        # begin() sends one blank display() (measured), so pages 0..1 are blank; display() calls 2..4 fill pages 2..7.
        want = bytes(SMALL_WIDTH) if p < SMALL_PAGES else expected[p % SMALL_PAGES]
        if page is None or page[:SMALL_WIDTH] != want or any(page[SMALL_WIDTH:]):
            diff.append(p)
    if diff:
        problems.append(f"model pages differing from the host-rendered 96x16 buffer: {diff}")
    if not any(any(e) for e in expected):
        problems.append("host-rendered expected buffer is blank")
    if problems:
        raise AssertionError("; ".join(problems) + f" | capture={fields}")
    return {"frames": fields.get("frames"), "unknown": fields.get("unknown"), "crc32": fields.get("crc32")}


def test_arduino_i2c_oled_small_buffer(request, hil_device, hil_config, hil_dut):
    if not (hil_device.sample_dir(SMALL_SAMPLE) / "Makefile").is_file():
        pytest.skip(f"{hil_device.name}: no {SMALL_SAMPLE} sample (CH32V003 only variant)")
    dut = hil_dut(SMALL_SAMPLE)
    run = new_run(hil_device, SMALL_SAMPLE, library="OLED SSD1306 - SH1106 1.0.7", panel="96x16 (book: 128x32)",
                  criteria="SSD1306 model: pages 0..1 blank (begin), pages 2..7 = host-rendered 96x16 buffer; columns 96..127 zero; display on")
    port = {}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            expected = run.phase("expected", expected_pages, dut.sample_dir / f"{SMALL_SAMPLE}.ino", Path(tmp))
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        captured = run.phase("measure", _capture_across_dut_reset, port.get("p"), dut, 1, 5000)
        if captured is not None and expected is not None:
            ok, fields, pages = captured
            run.meta["capture"] = fields
            run.meta["pages"] = pages
            run.meta["expected_pages"] = [p.hex() for p in expected]
            run.meta["summary"] = run.phase("check", _check_small, (ok, fields), pages, expected)
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "arduino_i2c_oled_96x16")
    print(run.to_json())
    assert run.ok, run.to_json()
