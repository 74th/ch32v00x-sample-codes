"""Host tests for the i2c_master sample's SHT31 conversion (samples_ch32v003_wch/i2c_master/sht31.c)."""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "samples_ch32v003_wch/i2c_master"


@pytest.fixture(scope="module")
def binary(tmp_path_factory):
    out = tmp_path_factory.mktemp("sht31") / "sht31"
    subprocess.run(["gcc", "-std=c11", "-Wall", "-Werror", "-I", str(SRC), str(SRC / "sht31.c"),
                    str(ROOT / "tests/unit/sht31_harness.c"), "-o", str(out)], check=True)
    return out


def convert(binary, reply: str):
    out = subprocess.run([str(binary)], input=reply, text=True, capture_output=True, check=True).stdout
    return dict(kv.split("=") for kv in out.split())


@pytest.mark.parametrize("reply,t,h", [
    # literals worked out by hand with the book's integer formulas:
    # 0x6666: 26214*175 = 4587450, >>16 = 69 (69.99 truncated), -45 = 24; 0x8000 -> 100*32768>>16 = 50
    ("666600" "800000", 24, 50),
    # 0xffff: 65535*175>>16 = 174 -> 129; 65535*100>>16 = 99
    ("ffff00" "ffff00", 129, 99),
    # 0x8000: 32768*175>>16 = 87 -> 42; humidity raw 0 -> 0
    ("800000" "000000", 42, 0),
])
def test_known_readings(binary, reply, t, h):
    assert convert(binary, reply) == {"t": str(t), "h": str(h)}


def test_below_zero_wraps_like_the_book(binary):
    # raw 0 -> 0 - 45 in uint32_t: documented behaviour inherited from the book
    assert convert(binary, "000000" "000000")["t"] == str((2**32) - 45)
