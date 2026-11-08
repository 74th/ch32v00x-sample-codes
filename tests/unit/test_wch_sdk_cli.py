"""wch-sdk.py selection and guarded-flash checks; no hardware is touched."""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from ch32hil.dut import CmdResult, Dut, DutError

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("wch_sdk_cli", ROOT / "scripts/wch-sdk.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def test_default_is_blink_on_ch32v003():
    assert cli.resolve() == ROOT / "samples_ch32v003_wch/blink" == cli.SAMPLE


@pytest.mark.parametrize("device,sample", [("ch32v999", "blink"), ("ch32v003", "../blink"), ("ch32v003", "nope"),
                                           ("ch32v003", ""), ("ch32v002", "nope"), ("ch32v002", "../blink")])
def test_invalid_selection_is_rejected(device, sample):
    with pytest.raises(cli.SelectionError):
        cli.resolve(device, sample)


def _run(*args):
    return subprocess.run([sys.executable, str(ROOT / "scripts/wch-sdk.py"), *args], cwd=ROOT,
                          capture_output=True, text=True)


def test_cli_rejects_before_any_action():
    # (never a valid device/sample pair here: a valid one would reach the programmer)
    for args in (("flash", "--sample", "nope"), ("flash", "--device", "ch32v002", "--sample", "nope"),
                 ("flash", "--device", "ch32v999"), ("observe", "--sample", "uart")):
        p = _run(*args)
        assert p.returncode == 2 and "Found WCH Link" not in p.stdout + p.stderr, (args, p.stderr)


def _dut(tmp_path, outputs, bin_present=True):
    if bin_present:
        (tmp_path / "main.bin").write_bytes(b"\x01\x02")
    calls = []

    def run(argv, timeout):
        calls.append(argv)
        return outputs(argv)
    return Dut(tmp_path, run=run, ready_timeout=0, framework="wch"), calls


def test_chip_mismatch_never_writes(tmp_path):
    dut, calls = _dut(tmp_path, lambda a: CmdResult(0, "Found WCH Link\nDetected CH32V006\n"))
    dut.ready_timeout = 1  # enable detection check
    dut.sleep = lambda s: None
    with pytest.raises(DutError):
        cli.flash(dut)
    assert not any("-w" in c for c in calls)


def test_missing_artifact_never_touches_programmer(tmp_path):
    dut, calls = _dut(tmp_path, lambda a: CmdResult(0, ""), bin_present=False)
    with pytest.raises(DutError, match="artifact missing"):
        cli.flash(dut)
    assert calls == []


# ---- build --all checks (synthetic inputs; the real build is `scripts/wch-sdk.py build --all`) ----
def _nm(*paths):
    return "".join(f"00000010 T sym{i}\t{p}:{i + 1}\n" for i, p in enumerate(paths))


def test_check_sources_accepts_own_sdk_and_rejects_externals_or_other_device():
    r = ROOT
    good = _nm(f"{r}/samples_ch32v003_wch/blink/main.c", f"{r}/samples_ch32v003_wch/blink/../sdk/Debug/debug.c",
               "/home/wch/riscv-gnu-toolchain/libgcc/div.S")
    assert cli.check_sources(good, "ch32v003") == []
    ext = _nm(f"{r}/samples_ch32v003_wch/sdk/Debug/debug.c", f"{r}/externals/ch32v003/EVT/EXAM/SRC/Debug/debug.c")
    assert any("externals" in p for p in cli.check_sources(ext, "ch32v003"))
    other = _nm(f"{r}/samples_ch32v002_wch/sdk/Debug/debug.c")
    probs = cli.check_sources(other, "ch32v003")
    assert any("no source from samples_ch32v003_wch/sdk" in p for p in probs) and any("outside" in p for p in probs)


def test_check_layout_detects_a_wrong_memory_map():
    ok3 = "FLASH            0x00000000         0x00004000         xr\nRAM              0x20000000         0x00000800         xrw\n"
    ok2 = ok3.replace("0x00000800", "0x00001000")
    assert cli.check_layout(ok3, "ch32v003") == [] and cli.check_layout(ok2, "ch32v002") == []
    assert cli.check_layout(ok3, "ch32v002") and cli.check_layout(ok2, "ch32v003")      # 003 layout in a 002 build and vice versa
    assert cli.check_layout("FLASH 0x0 0xf800 xr\nRAM 0x20000000 0x2000 xrw\n", "ch32v002")   # CH32V006's 62K/8K


def test_every_matrix_row_is_a_built_sample_for_both_devices():
    import json
    for device, matrix_file in (("ch32v003", "hil/matrix_wch.json"), ("ch32v002", "hil/matrix_ch32v002_wch.json")):
        rows = {e["sample"] for e in json.loads((ROOT / matrix_file).read_text())["entries"]}
        assert set(cli.all_samples(device)) == rows | {"blink"}, device


def test_ch32v006_layout_is_62k_8k_and_rejects_the_ch32v002_layout():
    ok6 = "FLASH            0x00000000         0x0000f800         xr\nRAM              0x20000000         0x00002000         xrw\n"
    assert cli.check_layout(ok6, "ch32v006") == []
    ok2 = ok6.replace("0x0000f800", "0x00004000").replace("0x00002000", "0x00001000")
    assert cli.check_layout(ok2, "ch32v006") and cli.check_layout(ok6, "ch32v002") and cli.check_layout(ok6, "ch32v003")


def test_ch32v006_selection_resolves_only_its_own_samples():
    assert cli.resolve("ch32v006", "blink") == ROOT / "samples_ch32v006_wch/blink"
    with pytest.raises(cli.SelectionError):
        cli.resolve("ch32v006", "nope")


def test_ch32v006_sources_reject_ch32v002_sdk_and_externals():
    r = ROOT
    good = _nm(f"{r}/samples_ch32v006_wch/blink/main.c", f"{r}/samples_ch32v006_wch/blink/../sdk/Debug/debug.c")
    assert cli.check_sources(good, "ch32v006") == []
    other = _nm(f"{r}/samples_ch32v002_wch/sdk/Debug/debug.c", f"{r}/samples_ch32v006_wch/blink/main.c")
    assert any("outside" in p for p in cli.check_sources(other, "ch32v006"))
    ext = _nm(f"{r}/samples_ch32v006_wch/sdk/Debug/debug.c",
              f"{r}/externals/ch32v002_004_005_006_007/EVT/EXAM/SRC/Debug/debug.c")
    assert any("externals" in p for p in cli.check_sources(ext, "ch32v006"))


def test_ch32v006_built_samples_are_tracked_in_its_matrix():
    import json
    rows = {e["sample"]: e["state"] for e in json.loads((ROOT / "hil/matrix_ch32v006_wch.json").read_text())["entries"]}
    built = set(cli.all_samples("ch32v006"))
    assert built <= set(rows) | {"blink"}                  # blink is the reference sample, tracked in README/log
    assert {s for s, st in rows.items() if st in ("build-only", "hil-verified")} <= built
