"""Expected frame buffer of the Arduino i2c_oled sketch, rendered on the host by the pinned OLED library.

tests/unit/arduino_oled/harness.cpp includes the sample's .ino and the library ("OLED SSD1306 - SH1106" 1.0.7, as
installed by the sketch.yaml profile) with host stubs of Arduino.h/Print.h, runs setup() and one loop(), and
prints the library's buffer: 4 pages x 128 bytes for the 128x32 panel the sketch declares.
"""
from __future__ import annotations

import glob
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HARNESS = ROOT / "tests/unit/arduino_oled"
LIBRARY_GLOB = ".arduino/official/data/internal/OLED_SSD1306_-_SH1106_1.0.7_*/OLED SSD1306 - SH1106/src"


def library_dir() -> Path | None:
    found = sorted(glob.glob(str(ROOT / LIBRARY_GLOB)))
    return Path(found[0]) if found else None


def expected_pages(sketch: Path, workdir: Path) -> list[bytes]:
    lib = library_dir()
    if lib is None:
        raise FileNotFoundError(f"OLED library not installed ({LIBRARY_GLOB}); build the i2c_oled sample first")
    exe = workdir / "oled_harness"
    subprocess.run(["g++", "-std=gnu++17", "-w", f"-I{HARNESS}", f"-I{lib}", str(HARNESS / "harness.cpp"),
                    str(lib / "oled.cpp"), f'-DSKETCH="{sketch}"', "-o", str(exe)], check=True)
    out = subprocess.run([str(exe)], check=True, capture_output=True, text=True).stdout.split()
    return [bytes.fromhex(line) for line in out]


def expected_uart_screens(sketch: Path, workdir: Path, answers: list[str]) -> list[list[bytes]]:
    """Frame buffer (pages of 128 bytes) after each loop() of the uart sketch; `answers[i]` is the hex the sensor
    sends before loop i ("-" = none). Rendered by the pinned library on the host."""
    lib = library_dir()
    if lib is None:
        raise FileNotFoundError(f"OLED library not installed ({LIBRARY_GLOB}); build the i2c_oled sample first")
    exe = workdir / "uart_harness"
    subprocess.run(["g++", "-std=gnu++17", "-w", f"-I{HARNESS}", f"-I{lib}", str(HARNESS / "uart_harness.cpp"),
                    str(lib / "oled.cpp"), f'-DSKETCH="{sketch}"', "-o", str(exe)], check=True)
    out = subprocess.run([str(exe), *answers], check=True, capture_output=True, text=True).stdout.split()
    pages = [bytes.fromhex(line) for line in out]
    per = len(pages) // len(answers)
    return [pages[i * per:(i + 1) * per] for i in range(len(answers))]
