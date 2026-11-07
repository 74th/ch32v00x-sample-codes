"""CH32V002 official-SDK samples: device guard, matrix coverage and no leakage of CH32V003 settings (no hardware)."""
import json
import re
from pathlib import Path

import pytest

from ch32hil import devices, matrix
from ch32hil.dut import CmdResult, Dut, DutError

ROOT = Path(__file__).resolve().parents[2]
S2, S3 = ROOT / "samples_ch32v002_wch", ROOT / "samples_ch32v003_wch"
V002_ID = "1ffff704: 20 06 20 00\n"


def samples(root):
    return sorted(p.parent.name for p in root.glob("*/Makefile"))


def test_every_ch32v003_sample_has_a_ch32v002_port():
    assert samples(S2) == samples(S3)


def test_ch32v002_matrix_covers_ch32v003_matrix_one_to_one():
    base = matrix.load(ROOT / "hil/matrix_wch.json")
    entries = matrix.load(ROOT / "hil/matrix_ch32v002_wch.json")
    assert matrix.coverage_problems(base, entries) == []
    assert sorted(e["sample"] for e in entries) == sorted(e["sample"] for e in base)
    book = ROOT / "externals/ch32v003-book-code"
    if book.is_dir():
        assert matrix.problems(entries, book_dir=book, samples_dir=S2, root=ROOT, framework="wch") == []


def test_ch32v002_state_is_never_inherited_from_ch32v003():
    """A 003 hil-verified row must not make the 002 row verified: that needs 002 hardware, tests and evidence."""
    base = {e["sample"]: e for e in matrix.load(ROOT / "hil/matrix_wch.json")}
    for e in matrix.load(ROOT / "hil/matrix_ch32v002_wch.json"):
        assert e["003_state"] == base[e["sample"]]["state"]
        if e["state"] == "hil-verified":
            assert e.get("hil_tests") and e.get("evidence"), e["sample"]
            assert not set(e["evidence"]) & set(base[e["sample"]].get("evidence", [])), \
                f"{e['sample']}: 002 evidence must not reuse the 003 log"


def test_ch32v002_build_configuration_is_its_own():
    mk = (S2 / "wch.mk").read_text()
    assert "-DCH32V002" in mk and "samples_ch32v003" not in mk and "ch32v00x_" not in mk.replace("ch32v00x.h", "")
    ld = re.sub(r"/\*.*?\*/", "", (S2 / "sdk/Ld/Link.ld").read_text(), flags=re.S)     # only the active MEMORY block
    assert re.search(r"(?m)^\s*FLASH \(rx\) : ORIGIN = 0x00000000, LENGTH = 16K$", ld)
    assert re.search(r"(?m)^\s*RAM \(xrw\)  : ORIGIN = 0x20000000, LENGTH = 4K$", ld)
    assert not re.search(r"LENGTH = (62K|8K|32K|6K)", ld)       # the CH32V004/5/6 blocks stay commented out
    assert (S2 / "sdk/Peripheral/inc/ch32v00X.h").is_file()                      # 002 SDK naming (capital X)
    assert not (S2 / "sdk/Peripheral/inc/ch32v00x_gpio.h").exists()               # no 003 header copy under the old name
    for makefile in S2.glob("*/Makefile"):
        assert "include ../wch.mk" in makefile.read_text() and "003" not in makefile.read_text()
    for source in list(S2.glob("*/*.c")) + list(S2.glob("*/*.h")):
        assert "ch32v00x_" not in source.read_text(), source      # 003 driver headers (lower-case x)


def test_ch32v003_build_configuration_has_no_ch32v002_flag():
    assert "CH32V002" not in (S3 / "wch.mk").read_text()
    assert "LENGTH = 16K" in (S3 / "sdk/Ld/Link.ld").read_text()


def test_ch32v002_wch_flash_checks_the_identifier_before_writing(tmp_path):
    (tmp_path / "main.bin").write_bytes(b"\x01")
    for output, writes in (("1ffff704: 30 05 30 00\n", False), (V002_ID, True)):
        calls = []

        def runner(argv, t, output=output):
            calls.append(argv)
            return CmdResult(0, output if "-r" in argv else "Detected CH32V002\nImage written.\n")

        dut = Dut(tmp_path, target="ch32v002", run=runner, minichlink=tmp_path / "mc", ready_timeout=0, framework="wch")
        if writes:
            dut.flash()
        else:
            with pytest.raises(DutError):
                dut.flash()
        assert any("-w" in a for a in calls) == writes


def test_cli_accepts_ch32v002_selection_but_the_003_chip_is_refused(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("wch_sdk_cli", ROOT / "scripts/wch-sdk.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    assert cli.resolve("ch32v002", "blink") == S2 / "blink"
    (tmp_path / "main.bin").write_bytes(b"\x01")
    calls = []

    def runner(argv, t):
        calls.append(argv)
        return CmdResult(0, "Found WCH Link\nDetected CH32V003\n")      # a CH32V003 is connected

    dut = Dut(tmp_path, target="ch32v002", run=runner, minichlink=tmp_path / "mc", ready_timeout=1, framework="wch",
              sleep=lambda s: None)
    with pytest.raises(DutError):
        cli.flash(dut)
    assert not any("-w" in a for a in calls)
