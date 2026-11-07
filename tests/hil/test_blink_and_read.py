"""HIL: blink_and_read (selected --hil-device, default CH32V003), observed by Pico GPIO protocol v2.

DESTRUCTIVE: rebuilds and flashes the connected DUT via WCH-LinkE.
Run: uv run pytest --hil -m "hil and gpio" --hil-port /dev/serial/by-id/...
"""
import subprocess
import tempfile
from pathlib import Path

import pytest
import serial
from serial.tools import list_ports

import measure
from ch32hil.dut import ROOT, MINICHLINK
from ch32hil.phases import Run
from ch32hil.pico import PicoClient, PicoError, discover, wait_ready

pytestmark = [pytest.mark.hil, pytest.mark.gpio]


def _revision():
    return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def _with_client(port, timeout, operation):
    with serial.Serial(port, 115200, timeout=0.2, write_timeout=1) as dev:
        dev.reset_input_buffer()
        return operation(PicoClient(dev, timeout=timeout))


def _prepare(port, timeout):
    def action(client):
        caps = client.negotiate(["GPIO_SAMPLE", "RESET_SAFE"])
        if caps.get("proto") != "2":
            raise PicoError(f"expected protocol 2, got {caps.get('proto')!r}")
        client.reset_safe()
        return caps
    return _with_client(port, timeout, action)


def _measure(port, timeout, pin):
    def action(client):
        result = client.request("GPIO_SAMPLE", pin, 300, 10000)
        if not result.ok:
            raise PicoError(f"GPIO_SAMPLE failed: {result.fields}")
        fields = dict(part.split("=", 1) for part in result.fields if "=" in part)
        if fields.get("pin") != str(pin) or fields.get("count") != "300" or fields.get("interval_us") != "10000":
            raise PicoError(f"unexpected sample settings: {fields}")
        matched, runs = measure.analyse("PICO_GPIO_V1 10000 " + fields.get("samples", ""))
        if not matched:
            raise AssertionError(f"runtime mismatch: runs={runs}")
        return runs
    return _with_client(port, timeout, action)


def _cleanup(port, timeout):
    if port:
        def action(client):
            client.reset_safe()
            for pin in (5, 8, 9, 10, 12, 13):
                state = client.request("GPIO_STATE", pin)
                if not state.ok or not {"output=0", "pull_up=0", "pull_down=0"}.issubset(state.fields):
                    raise PicoError(f"GP{pin} is not safe: {state.fields}")
        _with_client(port, timeout, action)


def test_blink_and_read(request, hil_device, hil_config, hil_dut):
    cfg = hil_config
    dut = hil_dut(cfg["dut"]["sample"])
    port_opt = request.config.getoption("--hil-port")
    pin = cfg["pins"]["BLINK"]["pico_gpio"]
    print(f"HIL TARGET: {cfg['dut']['device']} sample={cfg['dut']['sample']}; "
          f"will BUILD, FLASH and READBACK the DUT; Pico GP{pin} input")
    run = Run(meta={"config": cfg["name"], "target": hil_device.target_mcu, "revision": _revision(), "minichlink": str(MINICHLINK),
                    "readback_policy": cfg["readback"], "dut_command_log": []})
    t = cfg["timeouts"]
    port = {}
    try:
        run.phase("environment", lambda: MINICHLINK.is_file() or (_ for _ in ()).throw(FileNotFoundError(MINICHLINK)))
        def prepare_port():
            selected, caps = wait_ready(list_ports.comports,
                lambda device, timeout: serial.Serial(device, 115200, timeout=min(0.2, timeout), write_timeout=1),
                port=port_opt, timeout=t["pico_enumeration"])
            port["p"] = selected
            return caps
        run.phase("pico_prepare", prepare_port)
        run.phase("fixture_setup", lambda: _prepare(port["p"], t["measure"]))
        run.phase("dut_build", dut.build)
        run.phase("dut_flash", dut.flash)
        if cfg["readback"] != "disabled":
            with tempfile.TemporaryDirectory() as tmp:
                run.phase("dut_readback", dut.readback, Path(tmp))
        run.phase("dut_reset", dut.reset)
        run.phase("measure", _measure, port.get("p"), t["measure"], pin)
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), t["measure"])
        out = request.config.getoption("--hil-run-dir")
        if out:
            Path(out).mkdir(parents=True, exist_ok=True)
            (Path(out) / "run.json").write_text(run.to_json())
    assert run.ok, run.to_json()


def test_intentional_mismatch_cleanup(request, hil_config):
    """GP10 is the normally pulled-up I2C SDA, not the blinking PC0 signal."""
    cfg = hil_config
    port = discover(list_ports.comports, request.config.getoption("--hil-port"),
                    cfg["timeouts"]["pico_enumeration"])
    run = Run(meta={"test": "intentional_mismatch", "pin": 10})
    try:
        run.phase("fixture_setup", _prepare, port, cfg["timeouts"]["measure"])
        run.phase("measure", _measure, port, cfg["timeouts"]["measure"], 10)
    finally:
        run.phase("cleanup", _cleanup, port, cfg["timeouts"]["measure"])
    statuses = {phase.name: phase.status for phase in run.results}
    assert statuses == {"fixture_setup": "pass", "measure": "fail", "cleanup": "pass"}, run.to_json()
    assert "runtime mismatch" in run.primary_failure, run.to_json()
    state = _with_client(port, cfg["timeouts"]["measure"], lambda c: c.request("GPIO_STATE", 10))
    assert state.ok and {"output=0", "pull_up=0", "pull_down=0"}.issubset(state.fields)


def test_button_input(request, hil_device, hil_config, hil_dut):
    """GP12 drives the PA1 RC low; verify blink pauses and resumes."""
    cfg = hil_config
    dut = hil_dut('blink_and_read')
    port = discover(list_ports.comports, request.config.getoption('--hil-port'), cfg['timeouts']['pico_enumeration'])
    run = Run(meta={'test': 'button_input', 'sample': 'blink_and_read', 'target': hil_device.target_mcu})
    print('HIL GPIO: flash blink; GP12 drives DUT PA1 low via 10k/RC')
    def exercise(client):
        client.negotiate(['GPIO_BUTTON_TEST', 'GPIO_SAMPLE'])
        result = client.request('GPIO_BUTTON_TEST', 3000)
        if not result.ok:
            raise PicoError(f'button drive failed: {result.fields}')
        fields = dict(x.split('=', 1) for x in result.fields if '=' in x)
        if int(fields.get('samples', '0')) < 30 or fields.get('high') != '0':
            raise AssertionError(f'blink did not pause: {fields}')
    try:
        run.phase('fixture_setup', _prepare, port, 6)
        run.phase('dut_build', dut.build)
        run.phase('dut_flash', dut.flash)
        with tempfile.TemporaryDirectory() as tmp:
            run.phase('dut_readback', dut.readback, Path(tmp))
        run.phase('dut_reset', dut.reset)
        run.phase('stimulate', _with_client, port, 6, exercise)
        run.phase('measure_resume', _measure, port, 6, 5)
    finally:
        run.phase('cleanup', _cleanup, port, 6)
    assert run.ok, run.to_json()
