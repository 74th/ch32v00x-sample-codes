import pytest
from ch32hil.phases import Run


def boom(): raise RuntimeError("flash broke")


def test_failure_skips_later_but_cleanup_runs_and_reports():
    r = Run(); cleaned = []
    r.phase("dut_flash", boom)
    r.phase("measure", lambda: 1 / 0)
    r.phase("cleanup", lambda: cleaned.append(1))
    st = {p.name: p.status for p in r.results}
    assert st == {"dut_flash": "fail", "measure": "skipped", "cleanup": "pass"} and cleaned
    assert "flash broke" in r.primary_failure and not r.ok


def test_cleanup_failure_kept_with_primary():
    r = Run()
    r.phase("measure", boom)
    r.phase("cleanup", lambda: (_ for _ in ()).throw(OSError("serial gone")))
    assert "measure" in r.primary_failure
    assert [p.status for p in r.results] == ["fail", "fail"]


def test_cleanup_failure_alone_is_not_ok():
    r = Run(); r.phase("cleanup", boom); assert not r.ok


def test_interrupt_recorded_and_reraised():
    r = Run()
    with pytest.raises(KeyboardInterrupt):
        r.phase("measure", lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
    r.phase("cleanup", lambda: None)
    assert r.results[0].status == "fail" and r.results[1].status == "pass"


def test_json_machine_readable():
    import json
    r = Run(meta={"x": 1}); r.phase("environment", lambda: None)
    assert json.loads(r.to_json())["phases"][0]["status"] == "pass"


@pytest.mark.parametrize('failed', [
    'environment', 'pico_prepare', 'fixture_setup', 'dut_build', 'dut_flash',
    'dut_readback', 'dut_reset', 'measure',
])
def test_each_stage_failure_preserves_primary_and_cleanup(failed):
    stages = ['environment', 'pico_prepare', 'fixture_setup', 'dut_build', 'dut_flash',
              'dut_readback', 'dut_reset', 'measure']
    run = Run()
    visited = []
    for stage in stages:
        def execute(name=stage):
            visited.append(name)
            if name == failed:
                raise RuntimeError(f'injected {name}')
        run.phase(stage, execute)
    run.phase('cleanup', lambda: visited.append('cleanup'))
    assert run.primary_failure == f'{failed}: injected {failed}'
    assert visited[-1] == 'cleanup'
    assert visited[:-1] == stages[:stages.index(failed) + 1]
    assert run.results[-1].status == 'pass'
    assert not run.ok


def test_result_identifies_device_target_source_artifact_and_variant(tmp_path):
    import hashlib, json
    from ch32hil.dut import CmdResult, Dut
    out = {}
    for name in ("ch32v002", "ch32v006"):
        art = tmp_path / "build" / name / "main.bin"
        art.parent.mkdir(parents=True, exist_ok=True)
        art.write_bytes(name.encode())
        dut = Dut(tmp_path, target=name, run=lambda a, t: CmdResult(0, ""), make_args=("HELPER_CLOCK=1",))
        run = Run(meta={"sample": "x"})
        run.phase("dut_build", dut.build)
        out[name] = json.loads(run.to_json())["meta"]["dut"]
    a, b = out["ch32v002"], out["ch32v006"]
    assert (a["device"], a["build_target"], a["part"]) == ("ch32v002", "CH32V002", "CH32V002F4P6")
    assert (b["device"], b["build_target"], b["part"]) == ("ch32v006", "CH32V006", "CH32V006F8P6")
    assert a["source_dir"] == b["source_dir"] and a["artifact"] != b["artifact"]
    assert b["artifact"].endswith("build/ch32v006/main.bin") and a["framework"] == b["framework"] == "ch32fun"
    assert b["artifact_sha256"] == hashlib.sha256(b"ch32v006").hexdigest() != a["artifact_sha256"]
    assert b["variant"] == ["HELPER_CLOCK=1"] and b["chip_id"] is None


def test_result_without_dut_is_unchanged():
    import json
    assert "dut" not in json.loads(Run(meta={"a": 1}).to_json())["meta"]
