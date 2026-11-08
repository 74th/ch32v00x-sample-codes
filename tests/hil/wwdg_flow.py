"""Shared HIL flow of the WWDG samples (WCH SDK and ch32fun): one -DWWDG_MODE build per call.

DESTRUCTIVE: rebuilds and flashes the DUT. At the end a known sample is flashed again and read back (recovery): an enabled
WWDG cannot be stopped, so the wwdg build keeps resetting the chip until it is overwritten.

DUT: UART (PD5 -> Pico GP9, 115200) prints "cause=<WWDG|IWDG|other>\\n" at every start, waits 1.5 s, enables the WWDG
(counter 0x7F, window 0x5F, /8 at 48 MHz: ~683 us per count, ~43.7 ms to the reset) and prints "." every 5 ms.
Judged (ch32hil/wwdg.py): mode 0 runs without a reset (one start, dots only, later captures dots only); mode 1 resets after
the first (too early) feed; mode 2 resets after ~9 dots. A debugger reset starts every observation, so the first start is
`cause=other` and the second one `cause=WWDG`. Not judged: EWI, behaviour while debugging, absolute reset time accuracy.
"""
import dataclasses
import tempfile
import time
from pathlib import Path

from arduino.common import (_cleanup, _prepare, build_flash_readback, find_port, new_run, reset_and_capture_uart, save,
                            uart_receive)
from ch32hil import wwdg
from ch32hil.dut import Dut

SAMPLE = "wwdg"
RESETS = 3            # observations of a build that resets (each starts with a debugger reset)
RUNNING_CHECKS = 3    # later captures of the mode 0 build, 3 s apart
CAPTURE_MS = 4000     # a mode 1/2 capture holds two starts (about 1.6 s each)


def _capture(dut, port):
    rx, fields = reset_and_capture_uart(dut, port, 32, CAPTURE_MS, 0.3)
    if fields.get("uart_errors") not in ("0x0", None):
        raise AssertionError(f"UART errors {fields.get('uart_errors')}: {rx!r}")
    return rx


def _observe(mode, dut, port):
    if mode == 0:
        rx = _capture(dut, port)
        out = {"start": rx.decode("latin-1"), "parsed": wwdg.judge_reset_capture(0, rx), "later": []}
        for _ in range(RUNNING_CHECKS):
            time.sleep(3.0)
            later, fields = uart_receive(port, 32, 3000)
            if fields.get("uart_errors") not in ("0x0", None):
                raise AssertionError(f"UART errors {fields.get('uart_errors')}: {later!r}")
            wwdg.judge_running(later)
            out["later"].append(later.decode("latin-1"))
        return out
    captures = []
    for _ in range(RESETS):
        rx = _capture(dut, port)
        captures.append({"rx": rx.decode("latin-1"), "parsed": wwdg.judge_reset_capture(mode, rx)})
    return {"captures": captures}


def _recover(hil_device, recovery_sample):
    """Overwrite the resetting wwdg build with a known sample; detection, full readback and reset are checked."""
    known = Dut(hil_device.sample_dir(recovery_sample), target=hil_device.name, framework=hil_device.framework)
    known.build()
    known.flash()
    with tempfile.TemporaryDirectory() as tmp:
        known.readback(Path(tmp))
    known.reset()
    return f"{recovery_sample} flashed, detected and read back"


def run_mode(request, hil_device, hil_config, hil_dut, mode, recovery_sample, name):
    dut = dataclasses.replace(hil_dut(SAMPLE), make_args=(f"EXTRA_CFLAGS=-DWWDG_MODE={mode}",))
    run = new_run(hil_device, SAMPLE, variant=f"WWDG_MODE={mode} ({wwdg.MODES[mode]})",
                  limitation="EWI, debug-mode behaviour and the absolute reset time are not observed",
                  criteria={0: "cause=other then dots only, no second start; later captures dots only",
                            1: "cause=other, 1..2 dots, then cause=WWDG (reset by the early feed)",
                            2: "cause=other, 8..10 dots, then cause=WWDG (reset below 0x40)"}[mode])
    port, out = {}, {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.phase("dut_restart", dut.wait_ready, "reset")
        observed = run.phase("observe", _observe, mode, dut, port.get("p"))
        if observed is not None:
            out["observed"] = observed
    finally:
        run.meta["observed"] = out
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        # Recovery runs even after a failure (recorded as "cleanup", the only phase that runs after an earlier failure).
        run.meta["recovery"] = run.phase("cleanup", _recover, hil_device, recovery_sample)
        save(request, run, f"{name}_mode{mode}")
    print(run.to_json())
    assert run.ok, run.to_json()
