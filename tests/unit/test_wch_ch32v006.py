"""CH32V006 official-SDK samples: build configuration is its own and keeps no CH32V002 settings (no hardware)."""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S6, S2 = ROOT / "samples_ch32v006_wch", ROOT / "samples_ch32v002_wch"


def test_ch32v006_build_configuration_is_its_own():
    mk = (S6 / "wch.mk").read_text()
    assert "-DCH32V006" in mk and "-DCH32V002" not in mk
    assert "samples_ch32v003" not in mk and "samples_ch32v002" not in mk and "externals" not in mk.replace("externals/ are", "")
    ld = re.sub(r"/\*.*?\*/", "", (S6 / "sdk/Ld/Link.ld").read_text(), flags=re.S)
    assert re.search(r"(?m)^\s*FLASH \(rx\) : ORIGIN = 0x00000000, LENGTH = 62K$", ld)
    assert re.search(r"(?m)^\s*RAM \(xrw\)  : ORIGIN = 0x20000000, LENGTH = 8K$", ld)
    assert not re.search(r"LENGTH = (16K|4K|32K|6K)", ld)
    assert (S6 / "sdk/Peripheral/inc/ch32v00X.h").is_file()
    assert not (S6 / "sdk/Peripheral/inc/ch32v00x_gpio.h").exists()
    for makefile in S6.glob("*/Makefile"):
        assert "include ../wch.mk" in makefile.read_text()
    for source in list(S6.glob("*/*.c")) + list(S6.glob("*/*.h")):
        assert "ch32v00x_" not in source.read_text(), source


def test_ch32v006_link_script_is_the_unmodified_official_one():
    provenance = (S6 / "PROVENANCE.md").read_text()
    digest = hashlib.sha256((S6 / "sdk/Ld/Link.ld").read_bytes()).hexdigest()
    assert digest in provenance and "a835ede9ff3e2dca2c6aa652809b85c9775475d2" in provenance


def test_ch32v002_wch_keeps_its_own_flag_and_link_script():
    assert "-DCH32V002" in (S2 / "wch.mk").read_text() and "-DCH32V006" not in (S2 / "wch.mk").read_text()
    assert (S2 / "sdk/Ld/Link.ld").read_bytes() != (S6 / "sdk/Ld/Link.ld").read_bytes()
