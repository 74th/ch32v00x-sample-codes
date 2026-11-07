"""Device selection (CH32V003 default / CH32V002) without hardware."""
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from ch32hil import config, devices, matrix
from ch32hil.dut import CmdResult, Dut, DutError, check_chip_id
from ch32hil.wiring import problems as wiring_problems

ROOT = Path(__file__).resolve().parents[2]
V002_ID = "1ffff704: 20 06 20 00\n"   # observed on CH32V002F4P6 (okf/log/2026-11-07-1156-ch32v002-flash-measure.md)


def test_unknown_device_is_rejected_before_hardware(tmp_path):
    with pytest.raises(devices.DeviceError):
        devices.get("ch32v999")
    with pytest.raises(devices.DeviceError):
        config.select("ch32v999")
    calls = []
    with pytest.raises(devices.DeviceError):
        Dut(tmp_path, target="ch32v999", run=lambda a, t: calls.append(a))
    assert calls == []


def test_unknown_device_option_is_usage_error():
    p = subprocess.run([sys.executable, "-m", "pytest", "--hil-device", "ch32v999", "--collect-only", "-q",
                        "-p", "no:cacheprovider", "tests/hil"], cwd=ROOT, capture_output=True, text=True)
    assert p.returncode != 0 and "unknown HIL device" in p.stderr + p.stdout


def test_default_selection_is_unchanged_ch32v003():
    device, path, cfg = config.select(None, None)
    assert device.name == "ch32v003" and path == ROOT / "hil/configs/gpio_blink.json"
    assert cfg["dut"]["device"] == "CH32V003F4P6"
    assert device.sample_dir("uart") == ROOT / "samples_ch32v003_ch32fun/uart"
    assert device.target_mcu == "CH32V003" and device.chip_id_type is None
    assert Dut(device.sample_dir("uart")).target == "ch32v003"
    assert config.DUT_PHYSICAL is device.physical


def test_ch32v002_selection():
    device, path, cfg = config.select("ch32v002")
    assert path == ROOT / "hil/configs/ch32v002_gpio_blink.json"
    assert cfg["dut"]["device"] == "CH32V002F4P6"
    assert device.sample_dir("uart") == ROOT / "samples_ch32v002_ch32fun/uart"
    assert device.target_mcu == "CH32V002" and device.chip_id_type == 0x002


@pytest.mark.parametrize("device,cfg", [("ch32v002", "hil/configs/gpio_blink.json"),
                                        ("ch32v003", "hil/configs/ch32v002_gpio_blink.json")])
def test_config_device_mismatch_is_rejected(device, cfg):
    with pytest.raises(config.ConfigError, match="does not match"):
        config.select(device, cfg)


def test_ch32v002_config_rejects_ch32v003_values():
    base = json.loads((ROOT / "hil/configs/ch32v002_gpio_blink.json").read_text())
    config.validate(copy.deepcopy(base), "ch32v002")
    for mutate in (lambda c: c["dut"].update(device="CH32V003F4P6"),
                   lambda c: c["dut"].update(device="CH32V002"),
                   lambda c: c["pins"]["BLINK"].update(dut_physical=11)):
        c = copy.deepcopy(base)
        mutate(c)
        with pytest.raises(config.ConfigError):
            config.validate(c, "ch32v002")


def test_ch32v002_config_matches_wiring_document():
    cfg = config.load(ROOT / "hil/configs/ch32v002_gpio_blink.json", "ch32v002")
    assert wiring_problems(cfg, (ROOT / "hardware/wiring-proposal.md").read_text()) == []


@pytest.mark.parametrize("result", [
    CmdResult(0, V002_ID),
    CmdResult(0, "Found WCH Link\nDetected CH32V002\n" + V002_ID),
])
def test_chip_id_ok(result):
    assert check_chip_id(result, 0x002) == 0x00200620


@pytest.mark.parametrize("result,msg", [
    (CmdResult(0, "1ffff704: 30 05 30 00\n"), "type 0x003"),
    (CmdResult(1, V002_ID), "exit 1"),
    (CmdResult(0, ""), "not readable"),
    (CmdResult(0, "No detected chip.\n" + V002_ID), "negative"),
    (CmdResult(0, "1ffff704: 20 06\n"), "not readable"),
])
def test_chip_id_failures(result, msg):
    with pytest.raises(DutError, match=msg) as e:
        check_chip_id(result, 0x002)
    assert e.value.phase == "flash"


@pytest.mark.parametrize("id_output", ["1ffff704: 30 05 30 00\n", "", None])
def test_ch32v002_flash_stops_before_write(tmp_path, id_output):
    (tmp_path / "main.bin").write_bytes(b"\x01")
    calls = []

    def runner(argv, t):
        calls.append(argv)
        if "-r" in argv:
            return CmdResult(0 if id_output is not None else 1, id_output or "")
        return CmdResult(0, "Detected CH32V002\nImage written.\n")

    dut = Dut(tmp_path, target="ch32v002", run=runner, minichlink=tmp_path / "mc", ready_timeout=0)
    with pytest.raises(DutError) as e:
        dut.flash()
    assert e.value.phase == "flash"
    assert not any("-w" in argv for argv in calls)


def test_ch32v002_flash_checks_id_then_writes(tmp_path):
    (tmp_path / "main.bin").write_bytes(b"\x01")
    calls = []

    def runner(argv, t):
        calls.append(argv)
        return CmdResult(0, V002_ID if "-r" in argv else "Detected CH32V002\nImage written.\n")

    dut = Dut(tmp_path, target="ch32v002", run=runner, minichlink=tmp_path / "mc", ready_timeout=0)
    dut.flash()
    assert calls[0][1:] == ["-r", "+", "0x1ffff704", "4", "-b"] and calls[1][1] == "-w"
    assert dut.chip_id == 0x00200620


def test_ch32v003_flash_has_no_id_read(tmp_path):
    (tmp_path / "main.bin").write_bytes(b"\x01")
    calls = []

    def runner(argv, t):
        calls.append(argv)
        return CmdResult(0, "Detected CH32V003\nImage written.\n")

    Dut(tmp_path, run=runner, minichlink=tmp_path / "mc", ready_timeout=0).flash()
    assert [argv[1] for argv in calls] == ["-w"]


def test_skip_reason_for_unported_or_missing_sample(tmp_path):
    m = tmp_path / "m.json"
    m.write_text(json.dumps({"entries": [{"sample": "uart", "state": "not-ported", "note": "todo"}]}))
    import dataclasses
    dev = dataclasses.replace(devices.get("ch32v002"), matrix=str(m))
    assert "not-ported" in dev.skip_reason("uart")
    assert "does not exist" in dev.skip_reason("no_such_sample")
    assert devices.get("ch32v003").skip_reason("uart") is None


def test_hil_skip_reason_is_reported_without_hardware(tmp_path):
    """Run the real fixture with --hil on a sample that cannot exist: it must skip, never touch hardware."""
    test = tmp_path / "test_fake_hil.py"
    test.write_text("import pytest\n\n@pytest.mark.hil\ndef test_x(hil_dut):\n    hil_dut('no_such_sample')\n")
    p = subprocess.run([sys.executable, "-m", "pytest", "-p", "conftest", "-p", "no:cacheprovider",
                        "--rootdir", str(ROOT), "-c", str(ROOT / "pyproject.toml"),
                        "--hil", "--hil-device", "ch32v002", "-rs", "-q", str(test)],
                       cwd=ROOT, capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "ch32v002: sample samples_ch32v002_ch32fun/no_such_sample does not exist" in p.stdout
    assert "1 skipped" in p.stdout


@pytest.mark.parametrize("name", sorted(devices.DEVICES))
def test_device_matrix_states_are_backed(name):
    dev = devices.get(name)
    entries = matrix.load(ROOT / dev.matrix)
    assert matrix.problems(entries, samples_dir=dev.sample_root, root=ROOT) == []


def test_ch32v002_matrix_covers_ch32v003_samples():
    base = matrix.load(ROOT / "hil/matrix.json")
    assert matrix.coverage_problems(base, matrix.load(ROOT / "hil/matrix_ch32v002.json")) == []
    missing = [e for e in matrix.load(ROOT / "hil/matrix_ch32v002.json") if e["sample"] != "uart"]
    assert matrix.coverage_problems(base, missing) == ["device matrix lacks baseline sample: uart"]
    unreasoned = [{"sample": s["sample"], "state": "excluded"} for s in base if s.get("sample")]
    assert any("without reason" in p for p in matrix.coverage_problems(base, unreasoned))


def test_ch32v002_matrix_hil_verified_requires_tests_and_evidence():
    entries = copy.deepcopy(matrix.load(ROOT / "hil/matrix_ch32v002.json"))
    entries[0].update(state="hil-verified", hil_tests=[], evidence=[])
    p = matrix.problems(entries, root=ROOT)
    assert any("without hil_tests" in x for x in p) and any("without evidence" in x for x in p)


def test_adc_full_scale_is_per_device():
    assert devices.get("ch32v003").adc_max == 1023 and devices.get("ch32v002").adc_max == 4095
