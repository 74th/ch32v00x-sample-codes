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
