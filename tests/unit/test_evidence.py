"""HIL result storage and toolchain identification for CH32V006 Arduino/WCH (simulated results, no hardware)."""
import json
from pathlib import Path
from types import SimpleNamespace

from ch32hil import devices, evidence
from ch32hil.phases import Run

ROOT = Path(__file__).resolve().parents[2]


def _meta(device, framework, sample="blink_and_read", **extra):
    return {"device": device, "framework": framework, "sample": sample, **extra}


def test_same_sample_name_never_collides_across_framework_or_device(tmp_path):
    paths = {evidence.result_path(tmp_path, _meta("ch32v006", fw, "blink_and_read"), "blink_and_read")
             for fw in ("arduino", "wch", "ch32fun")}
    assert len(paths) == 3
    other = evidence.result_path(tmp_path, _meta("ch32v006", "arduino", "adc"), "adc")
    assert other not in paths and other.parent.name == "default" and other.parent.parent.name == "adc"
    run_a, run_b = tmp_path / "run-a", tmp_path / "run-b"
    assert evidence.result_path(run_a, _meta("ch32v006", "wch"), "x") != evidence.result_path(run_b, _meta("ch32v006", "wch"), "x")


def test_variant_is_a_path_component(tmp_path):
    a = evidence.result_path(tmp_path, _meta("ch32v006", "wch", "timer_blink", variant="tim1"), "wch_timer_blink")
    b = evidence.result_path(tmp_path, _meta("ch32v006", "wch", "timer_blink", variant="tim2"), "wch_timer_blink")
    assert a != b and a.parent.name == "tim1" and b.parent.name == "tim2"
    hostile = evidence.result_path(tmp_path, _meta("ch32v006", "wch", "x", variant="../../etc"), "n")
    assert tmp_path in hostile.parents


def test_existing_devices_keep_the_flat_layout(tmp_path):
    for device in ("ch32v003", "ch32v002"):
        assert evidence.result_path(tmp_path, _meta(device, "arduino"), "arduino_adc") == tmp_path / "arduino_adc.json"


def test_simulated_results_are_stored_separately_and_keep_their_identity(tmp_path):
    for fw in ("arduino", "wch"):
        dev = devices.get("ch32v006", fw)
        meta = {"device": dev.name, "framework": fw, "sample": "blink_and_read", **evidence.toolchain_meta(dev, "blink_and_read")}
        path = evidence.result_path(tmp_path, meta, "blink_and_read")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(Run(meta=meta).to_json())
    files = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*.json"))
    assert files == ["ch32v006/arduino/blink_and_read/default/blink_and_read.json",
                     "ch32v006/wch/blink_and_read/default/blink_and_read.json"]
    arduino = json.loads((tmp_path / files[0]).read_text())["meta"]
    wch = json.loads((tmp_path / files[1]).read_text())["meta"]
    assert arduino["fqbn"] == "WCH:ch32v:CH32VM00X_EVT:pnum=CH32V006K8,clock=48MHz_HSI" and "sdk" not in arduino
    assert wch["sdk"].endswith("a835ede9ff3e2dca2c6aa652809b85c9775475d2") and "fqbn" not in wch
    assert arduino["source_revision"] and wch["source_revision"] and "compiler" in arduino and "compiler" in wch


def test_wch_memory_layout_is_read_from_the_map(tmp_path):
    (tmp_path / "main.map").write_text("FLASH            0x00000000         0x0000f800         xr\n"
                                       "RAM              0x20000000         0x00002000         xrw\n")
    assert evidence.memory_layout(tmp_path) == {"flash": 0xF800, "ram": 0x2000}
    assert evidence.memory_layout(tmp_path / "nothing") is None


def test_source_revision_marks_a_dirty_tree_and_compiler_reports_missing(tmp_path):
    answers = iter([SimpleNamespace(stdout="abc123\n"), SimpleNamespace(stdout=" M file\n")])
    assert evidence.source_revision(run=lambda *a, **k: next(answers)) == "abc123+dirty"
    assert evidence.compiler_version(tmp_path / "no-gcc") == "missing"


def test_each_device_has_its_own_sdk_revision():
    assert set(devices.DEVICES) <= set(evidence.SDK_REVISIONS)
    assert evidence.SDK_REVISIONS["ch32v003"] != evidence.SDK_REVISIONS["ch32v006"]
