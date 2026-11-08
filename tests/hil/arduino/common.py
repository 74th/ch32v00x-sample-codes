"""Shared helpers for Arduino Core CH32 HIL tests."""
from __future__ import annotations

import itertools
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from serial.tools import list_ports

from ch32hil import evidence
from ch32hil.dut import ROOT, MINICHLINK
from ch32hil.phases import Run
from ch32hil.pico import PicoError, discover
from test_blink_and_read import _cleanup, _prepare, _with_client  # tests/hil (ch32fun) helpers

CORE = "WCH:ch32v 1.0.6 (official)"
ARDUINO_CLI = ROOT / ".arduino/bin/arduino-cli"


def _arduino_cli_version():
    try:
        return subprocess.run([str(ARDUINO_CLI), "version"], capture_output=True, text=True).stdout.strip()
    except OSError:
        return "missing"


def new_run(hil_device, sample, **extra):
    meta = {"sample": sample, "target": hil_device.target_mcu, "device": hil_device.name,
            "framework": hil_device.framework, "core": CORE, "arduino_cli": _arduino_cli_version(),
            "minichlink": str(MINICHLINK), "readback_policy": "required"}
    meta.update(evidence.toolchain_meta(hil_device, sample))
    meta.update(extra)
    return Run(meta=meta)


def save(request, run, name):
    out = request.config.getoption("--hil-run-dir")
    if out:
        path = evidence.result_path(out, run.meta, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(run.to_json())


def find_port(request, cfg):
    return discover(list_ports.comports, request.config.getoption("--hil-port"),
                    cfg["timeouts"]["pico_enumeration"])


def build_flash_readback(run, dut):
    run.phase("dut_build", dut.build)
    run.phase("dut_flash", dut.flash)
    with tempfile.TemporaryDirectory() as tmp:
        run.phase("dut_readback", dut.readback, Path(tmp))


def uart_receive(port, count, timeout_ms, baud=115200):
    """Receive up to `count` bytes from DUT PD5 (Pico GP9). Returns (bytes, fields); partial data on timeout."""
    def action(client):
        reply = client.request("UART_XFER", "DUT", baud, 8, "N", 1, "-", count, timeout_ms)
        fields = dict(f.split("=", 1) for f in reply.fields if "=" in f)
        if "rx" not in fields:
            raise PicoError(f"UART_XFER failed: {reply.fields}")
        rx = b"" if fields["rx"] == "-" else bytes.fromhex(fields["rx"])
        return rx, fields
    return _with_client(port, timeout_ms / 1000 + 3, action)


def reset_during(dut, operation, timeout_s, lead_s=0.3, settle_s=0.0):
    """Start `operation()` in a thread, then reset the DUT so that its boot activity happens inside it.

    Every minichlink call with -b (readback, wait_ready) also restarts the DUT; `settle_s` lets the boot
    activity of that earlier restart finish before the operation is armed.
    """
    dut.wait_ready("reset")
    time.sleep(settle_s)
    box = {}

    def target():
        try:
            box["result"] = operation()
        except BaseException as exc:  # reported by the caller
            box["error"] = exc
    thread = threading.Thread(target=target)
    thread.start()
    time.sleep(lead_s)
    try:
        dut.reset(wait=False)
    finally:
        thread.join(timeout_s + 5)
    if "error" in box:
        raise box["error"]
    if "result" not in box:
        raise PicoError("operation during reset did not finish")
    return box["result"]


def reset_and_capture_uart(dut, port, count, timeout_ms, lead_s=0.3):
    """Start a UART capture, then reset the DUT so that its boot output is inside the capture window."""
    return reset_during(dut, lambda: uart_receive(port, count, timeout_ms), timeout_ms / 1000, lead_s)


def fields_of(reply):
    return dict(f.split("=", 1) for f in reply.fields if "=" in f)


def sample_gpio(port, pin, count=300, interval_us=10000):
    """GPIO_SAMPLE -> list of run lengths [(level, samples), ...]."""
    def action(client):
        result = client.request("GPIO_SAMPLE", pin, count, interval_us)
        if not result.ok:
            raise PicoError(f"GPIO_SAMPLE failed: {result.fields}")
        fields = dict(part.split("=", 1) for part in result.fields if "=" in part)
        samples = fields.get("samples", "")
        if len(samples) != count or set(samples) - {"0", "1"}:
            raise PicoError(f"unexpected samples: {fields}")
        return [(v, len(list(g))) for v, g in itertools.groupby(samples)]
    return _with_client(port, count * interval_us / 1e6 + 3, action)


def check_square(runs, high_samples, low_samples, tolerance):
    """Complete runs (first/last dropped) alternate and each lasts high/low_samples +- tolerance."""
    complete = runs[1:-1]
    if len(complete) < 3 or {v for v, _ in complete} != {"0", "1"}:
        raise AssertionError(f"runtime mismatch: no square wave, runs={runs}")
    for value, n in complete:
        want = high_samples if value == "1" else low_samples
        if abs(n - want) > tolerance:
            raise AssertionError(f"runtime mismatch: {value} run of {n} samples (want {want}+-{tolerance}), runs={runs}")
    return complete


__all__ = ["_cleanup", "_prepare", "_with_client", "build_flash_readback", "check_square", "fields_of", "find_port",
           "new_run", "reset_and_capture_uart", "reset_during", "sample_gpio", "save", "uart_receive"]
