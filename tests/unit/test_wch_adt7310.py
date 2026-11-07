"""Host tests for the spi_master sample's temperature conversion (samples_ch32v003_wch/spi_master/adt7310.c)."""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "samples_ch32v003_wch/spi_master"


@pytest.fixture(scope="module")
def binary(tmp_path_factory):
    out = tmp_path_factory.mktemp("adt7310") / "adt7310"
    subprocess.run(["gcc", "-std=c11", "-Wall", "-Werror", "-I", str(SRC), str(SRC / "adt7310.c"),
                    str(ROOT / "tests/unit/adt7310_harness.c"), "-o", str(out)], check=True)
    return out


def convert(binary, raw: str):
    out = subprocess.run([str(binary)], input=raw, text=True, capture_output=True, check=True).stdout.strip()
    return dict(part.split("=", 1) for part in out.replace("text=", "text=").split(" ", 3)[:3]) | \
        {"text": out.split("text=", 1)[1]}


# Literals worked out by hand: raw >> 3 gives the 13-bit value in 1/16 degC.
@pytest.mark.parametrize("raw,raw_int,int_t,frac,text", [
    ("0c80", 400, 25, 0, "temp: 25.0000"),       # 0x0c80>>3 = 0x190 = 400 -> 25.0 degC
    ("0c88", 401, 25, 1, "temp: 25.0625"),       # +1 LSB (1/16 degC)
    ("0000", 0, 0, 0, "temp:  0.0000"),
    ("f380", -400, -25, 0, "temp:-25.0000"),     # 0xf380>>3 = 0x1e70 -> -400
    ("ffff", -1, -1, 15, "temp: -1.9375"),       # all ones: -1/16 shown as -1 + 15/16 (floor form, as in the book)
    ("7ff8", 4095, 255, 15, "temp:255.9375"),    # largest positive 13-bit value
])
def test_known_values(binary, raw, raw_int, int_t, frac, text):
    r = convert(binary, raw)
    assert (int(r["raw_int"]), int(r["int"]), int(r["frac"]), r["text"]) == (raw_int, int_t, frac, text)


def test_negative_half_degree_keeps_the_books_floor_format(binary):
    # -25.5 degC = raw_int -408: the book prints floor(-25.5) = -26 with fraction 8/16 -> "-26.5000" (not -25.5).
    assert convert(binary, "f340")["text"] == "temp:-26.5000"
