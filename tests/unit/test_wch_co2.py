"""Host tests for the uart sample's CO2 frame handling (samples_ch32v003_wch/uart/co2.c)."""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "samples_ch32v003_wch/uart"


@pytest.fixture(scope="module")
def binary(tmp_path_factory):
    out = tmp_path_factory.mktemp("co2") / "co2"
    subprocess.run(["gcc", "-std=c11", "-Wall", "-Werror", "-I", str(SRC), str(SRC / "co2.c"),
                    str(ROOT / "tests/unit/co2_harness.c"), "-o", str(out)], check=True)
    return out


def run(binary, frame: bytes):
    out = subprocess.run([str(binary)], input=frame.hex(), text=True, capture_output=True, check=True).stdout
    return dict(kv.split("=") for kv in out.split())


def frame(ppm, bad=False):
    f = bytearray([0xFF, 0x86, ppm >> 8, ppm & 0xFF, 0, 0, 0, 0, 0])
    f[8] = (0xFF - sum(f[1:8]) + 1) & 0xFF
    if bad:
        f[8] ^= 0x01
    return bytes(f)


def test_known_response(binary):
    # 0x04D2 = 1234 ppm; checksum 0xA4 computed by hand: 0x86+0x04+0xD2 = 0x15C -> 0xff-0x5C+1 = 0xA4
    r = run(binary, bytes.fromhex("ff8604d200000000a4"))
    assert r == {"status": "0", "ppm": "1234", "checksum": "a4"}


def test_book_command_checksums(binary):
    # the book's two fixed commands carry their own checksums (read: 0x79, self calibration: 0xE6)
    assert run(binary, bytes.fromhex("ff01860000000000" + "79"))["checksum"] == "79"
    assert run(binary, bytes.fromhex("ff0179a000000000" + "e6"))["checksum"] == "e6"


@pytest.mark.parametrize("ppm", [0, 400, 1234, 5000, 65535])
def test_values(binary, ppm):
    assert run(binary, frame(ppm)) == {"status": "0", "ppm": str(ppm), "checksum": f"{frame(ppm)[8]:02x}"}


def test_checksum_error_is_reported_but_value_kept(binary):
    r = run(binary, frame(800, bad=True))
    assert r["status"] == "2" and r["ppm"] == "800"


def test_bad_header(binary):
    assert run(binary, bytes.fromhex("ff8704d200000000a4"))["status"] == "1"
    assert run(binary, bytes.fromhex("fe8604d200000000a4"))["status"] == "1"
