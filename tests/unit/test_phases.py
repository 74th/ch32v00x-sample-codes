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
