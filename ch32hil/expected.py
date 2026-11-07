"""Expected-value generators that run on the host (gcc) and never touch hardware."""
from __future__ import annotations

import subprocess
from pathlib import Path

from .dut import ROOT

SSD1306_SAMPLE = ROOT / "samples_ch32v003_ch32fun/ssd1306_i2c"
EXTRALIBS = ROOT / "externals/ch32fun/extralibs"


def ssd1306_expected_frame(work_dir: Path):
    """Run the pinned ssd1306.h drawing code with the DUT's scene.h and the Pico model.

    Returns (fields, pages): fields from the first output line (init_frames, blank_crc32, frames,
    unknown, bad_control, display_on, charge_pump, crc32), pages = 8 hex strings of 128 bytes."""
    out = Path(work_dir) / "ssd1306_expected"
    subprocess.run(["gcc", "-std=gnu11", "-Wall", "-Werror",
                    "-I", str(ROOT / "hardware/pico-tester"), "-I", str(EXTRALIBS), "-I", str(SSD1306_SAMPLE),
                    str(ROOT / "hardware/pico-tester/ssd1306_model.c"),
                    str(ROOT / "tests/unit/ssd1306_expected_harness.c"), "-o", str(out)], check=True)
    lines = subprocess.run([str(out)], capture_output=True, text=True, check=True).stdout.splitlines()
    fields = dict(kv.split("=", 1) for kv in lines[0].split())
    pages = [line.split(" ", 1)[1] for line in lines[1:9]]
    return fields, pages


WS2812_HELPER = EXTRALIBS / "ws2812b_dma_spi_led_driver.h"
WS2812_SAMPLE = ROOT / "samples_ch32v003_ch32fun/ws2812_spi"


def ws2812_nibble_shifts(order: str = "WSGRB", helper: Path = WS2812_HELPER):
    """Shifts of the 24-bit callback value in the order the nibbles are sent, read from the helper's source.

    Parses the `ptr[k] = bitquartets[(ledval24bit>>S)&0xf];` lines of the branch for `order` (WSRBG, WSGRB, or the
    default RGB-order `#else` branch when order is "default")."""
    text = Path(helper).read_text()
    start = text.index("#ifdef WSRBG")
    end = text.index("#endif", start)
    branch = text[start:end]
    parts = {"WSRBG": branch[:branch.index("#elif defined( WSGRB )")],
             "WSGRB": branch[branch.index("#elif defined( WSGRB )"):branch.index("#else")],
             "default": branch[branch.index("#else"):]}
    import re
    found = re.findall(r"ptr\[(\d)\]\s*=\s*bitquartets\[\(ledval24bit>>(\d+)\)&0xf\]", parts[order])
    shifts = [None] * 6
    for index, shift in found:
        shifts[int(index)] = int(shift)
    if None in shifts:
        raise ValueError(f"could not read all six nibble shifts for {order}: {found}")
    return shifts


def ws2812_wire_bytes(values, order: str = "WSGRB", helper: Path = WS2812_HELPER) -> bytes:
    """Bytes on the wire for callback values (24-bit each), as the helper's nibble order sends them."""
    s = ws2812_nibble_shifts(order, helper)
    out = bytearray()
    for v in values:
        for k in range(3):
            out.append((((v >> s[2 * k]) & 0xF) << 4) | ((v >> s[2 * k + 1]) & 0xF))
    return bytes(out)


def ws2812_sample_values(main_c: Path = WS2812_SAMPLE / "main.c"):
    """The COLOR(g, r, b) entries of the sample, packed as the sample's COLOR macro does (R | G<<8 | B<<16)."""
    import re
    text = Path(main_c).read_text()
    return [r | (g << 8) | (b << 16)
            for g, r, b in ((int(x, 16) for x in m) for m in re.findall(r"COLOR\(\s*(0x[0-9A-Fa-f]+),\s*(0x[0-9A-Fa-f]+),\s*(0x[0-9A-Fa-f]+)\)", text))]
