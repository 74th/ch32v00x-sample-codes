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


def _artifact(sample_dir, name, data=b"\x01"):
    """Shared ch32fun sources keep one artifact per target: <sample>/build/<name>/main.bin."""
    path = sample_dir / "build" / name / "main.bin"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


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
    assert device.sample_dir("uart") == ROOT / "samples_ch32v00x_ch32fun/uart"
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
    _artifact(tmp_path, "ch32v002")
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
    _artifact(tmp_path, "ch32v002")
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
    assert "ch32v002: sample samples_ch32v00x_ch32fun/no_such_sample does not exist" in p.stdout
    assert "1 skipped" in p.stdout


_AVAILABLE = [(n, f) for n in sorted(devices.DEVICES) for f in devices.FRAMEWORKS
              if f == devices.DEFAULT_FRAMEWORK or (n, f) in devices.FRAMEWORK_MATRICES]


@pytest.mark.parametrize("name,framework", _AVAILABLE)
def test_device_matrix_states_are_backed(name, framework):
    dev = devices.get(name, framework)
    entries = matrix.load(ROOT / dev.matrix)
    assert matrix.problems(entries, samples_dir=dev.sample_root, root=ROOT, framework=framework) == []


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


def test_default_framework_keeps_ch32fun_values():
    for name in devices.DEVICES:
        assert devices.get(name) is devices.DEVICES[name]
        assert devices.get(name, "ch32fun") is devices.DEVICES[name]
        assert devices.get(name).framework == "ch32fun"
    assert devices.get("ch32v003").sample_root == ROOT / "samples_ch32v003_ch32fun"
    assert devices.get("ch32v003").matrix == "hil/matrix.json"
    assert devices.get("ch32v002").matrix == "hil/matrix_ch32v002.json"
    device, _, _ = config.select(None, None, framework=None)
    assert device.framework == "ch32fun"


@pytest.mark.parametrize("name,matrix_path", [("ch32v003", "hil/matrix_arduino.json"),
                                              ("ch32v002", "hil/matrix_ch32v002_arduino.json")])
def test_arduino_framework_paths(name, matrix_path):
    dev = devices.get(name, "arduino")
    assert dev.framework == "arduino" and dev.matrix == matrix_path
    assert dev.sample_dir("blink_and_read") == ROOT / f"samples_{name}_arduino/blink_and_read"
    # device identity (programmer checks) does not depend on the framework
    base = devices.get(name)
    assert (dev.part, dev.chip, dev.chip_id_type, dev.default_config) == \
        (base.part, base.chip, base.chip_id_type, base.default_config)
    device, _, _ = config.select(name, framework="arduino")
    assert device == dev


def test_unknown_framework_is_rejected_before_hardware():
    with pytest.raises(devices.DeviceError, match="unknown HIL framework"):
        devices.get("ch32v003", "platformio")
    with pytest.raises(devices.DeviceError):
        config.select("ch32v003", framework="platformio")


def test_unknown_framework_option_is_usage_error():
    p = subprocess.run([sys.executable, "-m", "pytest", "--hil-framework", "platformio", "--collect-only", "-q",
                        "-p", "no:cacheprovider", "tests/hil"], cwd=ROOT, capture_output=True, text=True)
    assert p.returncode != 0 and "unknown HIL framework" in p.stderr + p.stdout


def _run_fake_hil(tmp_path, *args):
    test = tmp_path / "test_fake_fw.py"
    test.write_text("import pytest\n\n"
                    "@pytest.mark.hil\ndef test_ch32fun_side():\n    pass\n\n"
                    "@pytest.mark.hil\n@pytest.mark.arduino\ndef test_arduino_side():\n    pass\n")
    return subprocess.run([sys.executable, "-m", "pytest", "-p", "conftest", "-p", "no:cacheprovider",
                           "--rootdir", str(ROOT), "-c", str(ROOT / "pyproject.toml"), "-rs", "-q",
                           *args, str(test)], cwd=ROOT, capture_output=True, text=True)


def test_framework_mismatched_hil_tests_are_skipped_with_reason(tmp_path):
    p = _run_fake_hil(tmp_path, "--hil")
    assert "1 passed, 1 skipped" in p.stdout, p.stdout
    assert "arduino HIL test; --hil-framework ch32fun selected" in p.stdout
    p = _run_fake_hil(tmp_path, "--hil", "--hil-framework", "arduino")
    assert "1 passed, 1 skipped" in p.stdout, p.stdout
    assert "ch32fun HIL test; --hil-framework arduino selected" in p.stdout
    p = _run_fake_hil(tmp_path)
    assert "2 skipped" in p.stdout and "pass --hil" in p.stdout, p.stdout


def test_arduino_missing_sample_is_reasoned_skip(tmp_path):
    test = tmp_path / "test_fake_ard.py"
    test.write_text("import pytest\n\n@pytest.mark.hil\n@pytest.mark.arduino\n"
                    "def test_x(hil_dut):\n    hil_dut('no_such_sample')\n")
    p = subprocess.run([sys.executable, "-m", "pytest", "-p", "conftest", "-p", "no:cacheprovider",
                        "--rootdir", str(ROOT), "-c", str(ROOT / "pyproject.toml"),
                        "--hil", "--hil-framework", "arduino", "-rs", "-q", str(test)],
                       cwd=ROOT, capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "samples_ch32v003_arduino/no_such_sample does not exist" in p.stdout


def test_wch_framework_selection_and_existing_frameworks_kept():
    dev = devices.get("ch32v003", "wch")
    assert dev.framework == "wch" and dev.matrix == "hil/matrix_wch.json"
    assert dev.sample_dir("uart") == ROOT / "samples_ch32v003_wch/uart"
    base = devices.get("ch32v003")
    assert (dev.part, dev.chip, dev.chip_id_type) == (base.part, base.chip, base.chip_id_type)
    assert devices.get("ch32v003", "arduino").framework == "arduino"
    assert devices.get("ch32v003") is devices.DEVICES["ch32v003"]
    # CH32V002 has its own WCH matrix and sample root (never the 003 files)
    d2 = devices.get("ch32v002", "wch")
    assert d2.matrix == "hil/matrix_ch32v002_wch.json" and d2.sample_dir("uart") == ROOT / "samples_ch32v002_wch/uart"
    assert d2.chip_id_type == 0x002 and d2.part == "CH32V002F4P6"


def test_wch_build_does_not_pass_generic_prefix(tmp_path):
    from ch32hil.dut import CmdResult, Dut
    calls = []
    (tmp_path / "main.bin").write_bytes(b"x")

    def run(argv, timeout):
        calls.append(argv)
        return CmdResult(0, "")
    Dut(tmp_path, run=run, framework="wch").build()
    Dut(tmp_path, run=run).build()
    assert not any(a.startswith("PREFIX=") for a in calls[0])
    assert "PREFIX=riscv64-unknown-elf" in calls[1]


def test_wch_marked_hil_tests_follow_framework_option(tmp_path):
    test = tmp_path / "test_fake_wch.py"
    test.write_text("import pytest\n\n@pytest.mark.hil\n@pytest.mark.wch\ndef test_wch_side():\n    pass\n")
    for args, outcome in (("--hil-framework", "wch"), ("--hil-framework", "ch32fun")):
        p = subprocess.run([sys.executable, "-m", "pytest", "-p", "conftest", "-p", "no:cacheprovider",
                            "--rootdir", str(ROOT), "-c", str(ROOT / "pyproject.toml"), "-rs", "-q",
                            "--hil", args, outcome, str(test)], cwd=ROOT, capture_output=True, text=True)
        expected = "1 passed" if outcome == "wch" else "1 skipped"
        assert expected in p.stdout, p.stdout


V006_ID = "1ffff704: 20 06 60 00\n"   # synthetic value for host tests only (type 0x006); real read-out is unmeasured


def test_ch32v006_selection_shares_ch32v002_sources():
    device, path, cfg = config.select("ch32v006")
    assert path == ROOT / "hil/configs/ch32v006_gpio_blink.json"
    assert cfg["dut"]["device"] == "CH32V006F8P6"
    assert device.target_mcu == "CH32V006" and device.chip == "CH32V006" and device.chip_id_type == 0x006
    # provisional route: the same application sources as CH32V002, but a separate artifact per target
    assert device.sample_dir("uart") == ROOT / "samples_ch32v00x_ch32fun/uart"
    assert devices.get("ch32v002").sample_dir("uart") == device.sample_dir("uart")
    assert device.artifact(device.sample_dir("uart")).parts[-3:] == ("build", "ch32v006", "main.bin")
    assert devices.get("ch32v002").artifact(device.sample_dir("uart")).parts[-3:] == ("build", "ch32v002", "main.bin")


def test_existing_devices_keep_their_artifact_layout():
    v003 = devices.get("ch32v003")
    assert v003.fun_root is None and v003.artifact(v003.sample_dir("uart")) == v003.sample_dir("uart") / "main.bin"
    for framework in ("arduino", "wch"):
        for name in ("ch32v003", "ch32v002"):
            dev = devices.get(name, framework)
            assert dev.sample_root == ROOT / f"samples_{name}_{framework}"
            assert dev.artifact(dev.sample_dir("x")) == dev.sample_dir("x") / "main.bin"


@pytest.mark.parametrize("framework", ["arduino", "wch"])
def test_ch32v006_framework_selection_uses_its_own_samples_and_matrix(framework):
    dev = devices.get("ch32v006", framework)
    assert dev.sample_root == ROOT / f"samples_ch32v006_{framework}"
    assert dev.matrix == f"hil/matrix_ch32v006_{framework}.json"
    assert dev.artifact(dev.sample_dir("x")) == dev.sample_dir("x") / "main.bin"
    assert dev.chip_id_type == 0x006 and dev.part == "CH32V006F8P6"
    device, path, cfg = config.select("ch32v006", framework=framework)
    assert path == ROOT / "hil/configs/ch32v006_gpio_blink.json" and device.framework == framework


def test_unknown_framework_pair_is_rejected_before_hardware(tmp_path):
    with pytest.raises(devices.DeviceError, match="unknown HIL framework"):
        devices.get("ch32v006", "bogus")
    calls = []
    with pytest.raises(devices.DeviceError):
        Dut(tmp_path, target="ch32v006", framework="bogus", run=lambda a, t: calls.append(a)).binary
    assert calls == []


@pytest.mark.parametrize("device,cfg", [("ch32v006", "hil/configs/ch32v002_gpio_blink.json"),
                                        ("ch32v002", "hil/configs/ch32v006_gpio_blink.json"),
                                        ("ch32v006", "hil/configs/gpio_blink.json")])
def test_ch32v006_config_mismatch_is_rejected(device, cfg):
    with pytest.raises(config.ConfigError, match="does not match"):
        config.select(device, cfg)


def test_ch32v006_config_validates_physical_pins():
    base = json.loads((ROOT / "hil/configs/ch32v006_gpio_blink.json").read_text())
    config.validate(copy.deepcopy(base), "ch32v006")
    for mutate in (lambda c: c["dut"].update(device="CH32V002F4P6"),
                   lambda c: c["pins"]["BLINK"].update(dut_physical=11),
                   lambda c: c["pins"]["UART_TX"].update(dut="PA1")):
        c = copy.deepcopy(base)
        mutate(c)
        with pytest.raises(config.ConfigError):
            config.validate(c, "ch32v006")


def test_ch32v006_config_matches_wiring_document():
    cfg = config.load(ROOT / "hil/configs/ch32v006_gpio_blink.json", "ch32v006")
    assert wiring_problems(cfg, (ROOT / "hardware/wiring-proposal.md").read_text()) == []


def test_build_passes_target_and_uses_per_target_artifact(tmp_path):
    calls = []

    def runner(argv, t):
        calls.append(argv)
        _artifact(tmp_path, "ch32v006")
        return CmdResult(0, "")

    dut = Dut(tmp_path, target="ch32v006", run=runner, ready_timeout=0)
    assert dut.build() == tmp_path / "build" / "ch32v006" / "main.bin"
    assert "TARGET_MCU=CH32V006" in calls[0] and "PREFIX=riscv64-unknown-elf" in calls[0]
    calls.clear()
    _artifact(tmp_path, "ch32v002")
    assert Dut(tmp_path, target="ch32v002", run=lambda a, t: calls.append(a) or CmdResult(0, ""),
               ready_timeout=0).build() == tmp_path / "build" / "ch32v002" / "main.bin"
    assert "TARGET_MCU=CH32V002" in calls[-1]


def test_other_target_artifact_is_never_flashed(tmp_path):
    _artifact(tmp_path, "ch32v002")    # only the CH32V002 artifact exists
    calls = []
    dut = Dut(tmp_path, target="ch32v006", run=lambda a, t: calls.append(a), ready_timeout=0)
    with pytest.raises(DutError, match="missing") as e:
        dut.flash()
    assert e.value.phase == "flash" and calls == []


def test_ch32v003_build_has_no_target_argument(tmp_path):
    calls = []

    def runner(argv, t):
        calls.append(argv)
        (tmp_path / "main.bin").write_bytes(b"\x01")
        return CmdResult(0, "")

    assert Dut(tmp_path, run=runner, ready_timeout=0).build() == tmp_path / "main.bin"
    assert not any(a.startswith("TARGET_MCU=") for a in calls[0])


@pytest.mark.parametrize("id_output", ["1ffff704: 20 06 20 00\n", "1ffff704: 30 05 30 00\n", "", None])
def test_ch32v006_flash_stops_before_write_on_wrong_or_unreadable_id(tmp_path, id_output):
    _artifact(tmp_path, "ch32v006")
    calls = []

    def runner(argv, t):
        calls.append(argv)
        if "-r" in argv:
            return CmdResult(0 if id_output is not None else 1, id_output or "")
        return CmdResult(0, "Detected CH32V006\nImage written.\n")

    with pytest.raises(DutError) as e:
        Dut(tmp_path, target="ch32v006", run=runner, minichlink=tmp_path / "mc", ready_timeout=0).flash()
    assert e.value.phase == "flash" and not any("-w" in a for a in calls)


@pytest.mark.parametrize("detect", ["Detected CH32V002\n", "No detected chip.\n", ""])
def test_ch32v006_selected_but_other_chip_or_none_detected(tmp_path, detect):
    """002/006 mix-up or an unconnected DUT: stop in wait_ready, before any identifier read or write."""
    _artifact(tmp_path, "ch32v006")
    calls = []

    def runner(argv, t):
        calls.append(argv)
        return CmdResult(0, "Found WCH Link\n" + detect)

    dut = Dut(tmp_path, target="ch32v006", run=runner, minichlink=tmp_path / "mc", ready_timeout=1,
              ready_interval=0, sleep=lambda s: None)
    with pytest.raises(DutError):
        dut.flash()
    assert not any("-w" in a or "-r" in a for a in calls)


def test_ch32v006_flash_checks_id_then_writes_and_requires_readback_match(tmp_path):
    binary = _artifact(tmp_path, "ch32v006", b"\x01\x02\x03")
    calls = []

    def runner(argv, t):
        calls.append(argv)
        if "-w" in argv:
            return CmdResult(0, "Detected CH32V006\nImage written.\n")
        if "-r" in argv and "0x1ffff704" in argv:
            return CmdResult(0, V006_ID)
        (tmp_path / "readback.bin").write_bytes(b"\x01\x02\xff")   # false-success readback
        return CmdResult(0, "Detected CH32V006\n")

    dut = Dut(tmp_path, target="ch32v006", run=runner, minichlink=tmp_path / "mc", ready_timeout=0)
    dut.flash()
    assert calls[0][1:] == ["-r", "+", "0x1ffff704", "4", "-b"] and calls[1][1] == "-w"
    assert dut.chip_id == 0x00600620
    with pytest.raises(DutError, match="differ"):
        dut.readback(tmp_path)
    assert binary.read_bytes() == b"\x01\x02\x03"


# ---- CH32V006 Arduino/WCH: own artifact, guarded flash, full readback (no hardware) ----
def _fw_artifact(sample_dir, data=b"\x01"):
    (sample_dir / "main.bin").write_bytes(data)      # arduino/wch keep the artifact directly in the sample directory
    return sample_dir / "main.bin"


@pytest.mark.parametrize("framework", ["arduino", "wch"])
def test_ch32v006_framework_artifact_is_the_sample_main_bin_and_never_another_devices(tmp_path, framework):
    dut = Dut(tmp_path, target="ch32v006", framework=framework, ready_timeout=0)
    assert dut.binary == tmp_path / "main.bin"
    assert dut.metadata()["framework"] == framework and dut.metadata()["device"] == "ch32v006"
    assert dut.metadata()["part"] == "CH32V006F8P6" and dut.metadata()["build_target"] is None
    calls = []
    _artifact(tmp_path, "ch32v006")                  # a ch32fun per-target artifact is not the framework artifact
    with pytest.raises(DutError, match="missing"):
        Dut(tmp_path, target="ch32v006", framework=framework, run=lambda a, t: calls.append(a), ready_timeout=0).flash()


@pytest.mark.parametrize("framework", ["arduino", "wch"])
def test_ch32v006_framework_build_arguments(tmp_path, framework):
    calls = []

    def runner(argv, t):
        calls.append(argv)
        _fw_artifact(tmp_path)
        return CmdResult(0, "")

    Dut(tmp_path, target="ch32v006", framework=framework, run=runner, ready_timeout=0).build()
    assert not any(a.startswith("TARGET_MCU=") for a in calls[0])
    assert ("PREFIX=riscv64-unknown-elf" in calls[0]) == (framework == "arduino")


@pytest.mark.parametrize("framework", ["arduino", "wch"])
@pytest.mark.parametrize("id_output", [V002_ID, "1ffff704: 30 05 30 00\n", "", None])
def test_ch32v006_framework_flash_stops_before_write_on_wrong_or_unreadable_id(tmp_path, framework, id_output):
    _fw_artifact(tmp_path)
    calls = []

    def runner(argv, t):
        calls.append(argv)
        if "-r" in argv:
            return CmdResult(0 if id_output is not None else 1, id_output or "")
        return CmdResult(0, "Detected CH32V006\nImage written.\n")

    with pytest.raises(DutError) as e:
        Dut(tmp_path, target="ch32v006", framework=framework, run=runner, minichlink=tmp_path / "mc",
            ready_timeout=0).flash()
    assert e.value.phase == "flash" and not any("-w" in a for a in calls)


@pytest.mark.parametrize("framework", ["arduino", "wch"])
@pytest.mark.parametrize("detect", ["Detected CH32V002\n", "No detected chip.\n", ""])
def test_ch32v006_framework_wrong_chip_or_unconnected_never_writes(tmp_path, framework, detect):
    _fw_artifact(tmp_path)
    calls = []

    def runner(argv, t):
        calls.append(argv)
        return CmdResult(0, "Found WCH Link\n" + detect)

    dut = Dut(tmp_path, target="ch32v006", framework=framework, run=runner, minichlink=tmp_path / "mc",
              ready_timeout=1, ready_interval=0, sleep=lambda s: None)
    with pytest.raises(DutError):
        dut.flash()
    assert not any("-w" in a or "-r" in a for a in calls)


@pytest.mark.parametrize("framework", ["arduino", "wch"])
def test_ch32v006_framework_false_success_is_not_written(tmp_path, framework):
    """minichlink exiting 0 without 'Detected CH32V006' / with a negative message must not count as flashed."""
    _fw_artifact(tmp_path)

    def runner(argv, t):
        if "-r" in argv:
            return CmdResult(0, V006_ID)
        return CmdResult(0, "No detected chip.\n")

    with pytest.raises(DutError):
        Dut(tmp_path, target="ch32v006", framework=framework, run=runner, minichlink=tmp_path / "mc",
            ready_timeout=0).flash()


@pytest.mark.parametrize("framework", ["arduino", "wch"])
def test_ch32v006_framework_readback_mismatch_fails_before_observation(tmp_path, framework):
    _fw_artifact(tmp_path, b"\x01\x02\x03\x04")

    def runner(argv, t):
        (tmp_path / "readback.bin").write_bytes(b"\x01\x02\x03\xff")     # last byte differs
        return CmdResult(0, "Detected CH32V006\n")

    dut = Dut(tmp_path, target="ch32v006", framework=framework, run=runner, minichlink=tmp_path / "mc",
              ready_timeout=0)
    with pytest.raises(DutError, match="differ") as e:
        dut.readback(tmp_path)
    assert e.value.phase == "readback"


def test_default_selection_and_existing_framework_behaviour_are_kept():
    assert devices.get("ch32v003").framework == "ch32fun" and devices.DEFAULT == "ch32v003"
    for name in ("ch32v003", "ch32v002"):
        for fw in ("arduino", "wch"):
            assert devices.get(name, fw).sample_root == ROOT / f"samples_{name}_{fw}"
    assert devices.get("ch32v006").per_target_build            # ch32fun layout stays shared and per target
