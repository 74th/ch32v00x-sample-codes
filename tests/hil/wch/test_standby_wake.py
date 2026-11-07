"""HIL: official WCH SDK standby_wake (book-code standby_mode_blink-wch_sdk): Standby woken by the AWU every 2 s.

DESTRUCTIVE: rebuilds and flashes the DUT; at the end it re-flashes the known `blink` sample and checks that the chip is
detected again (recovery). Run: uv run pytest --hil --hil-framework wch tests/hil/wch/test_standby_wake.py

DUT: prints "wait", waits 5 s, prints "init"/"start", then loops: "go to standby: N", Standby (WFE), AWU wake after ~2 s,
SystemInit(), "Auto wake up: N", LED (PC0 -> GP5) toggles. On wake the UART shows
    "\r\nAuto wake up: N \r\n" immediately followed by "go to standby: N+1\r\n\r\n"  (40 bytes, every ~2 s).
Judged: three consecutive wake bursts carry consecutive counts N, N+1, N+2 (execution resumes after the WFE, RAM kept, no
restart text) and their arrival times are 1.7..2.3 s apart; the LED toggles with a half period of 1.6..2.4 s.
Standby current / the stopped clock are NOT measured. After the test the chip is recovered with the known blink sample.
Standby blocks the debugger (minichlink: "nothing connected to linker", seen on this rig): recovery power-cycles the DUT
3.3 V through the WCH-LinkE (minichlink -t / -3) and flashes blink within the sample's 5 s initial wait.
"""
import re
import tempfile
import time
from pathlib import Path

import pytest

from ch32hil.dut import Dut, ROOT
from .common import (_cleanup, _prepare, build_flash_readback, find_port, new_run, sample_gpio, save, uart_receive)

pytestmark = [pytest.mark.hil, pytest.mark.wch, pytest.mark.gpio]

SAMPLE = "standby_wake"
BLINK_GP = 5
INTERVAL_US = 50000
# CH32V003 shows at most one corrupted byte before "\nAuto wake up"; the CH32V002 was observed with ~12 corrupted bytes
# ("\r\nAuto wake " garbled, framing errors) right after the wake, so only "up: N \r\ngo to stan" is required.
WAKE = re.compile(rb"([\x00-\xff]{0,16}?)up: (\d+) \r\ngo to stan")


def _wake_burst(port):
    rx, fields = uart_receive(port, 32, 5000)       # first 32 of the 41 bytes of one wake burst
    m = WAKE.search(rx)
    if not m:
        raise AssertionError(f"no wake burst in {rx!r} {fields}")
    # The first byte after the wake is the "\r" of "\r\nAuto wake up": observed corrupted (0x80) while the clock restarts.
    return int(m.group(2)), m.group(1).hex(), time.monotonic(), rx.decode("latin-1")


def _wakes(port):
    out = [_wake_burst(port) for _ in range(3)]
    counts = [o[0] for o in out]
    if counts != list(range(counts[0], counts[0] + 3)):
        raise AssertionError(f"counts not consecutive (execution did not resume cleanly): {out}")
    gaps = [round(b[2] - a[2], 3) for a, b in zip(out, out[1:])]
    if not all(1.7 <= g <= 2.3 for g in gaps):
        raise AssertionError(f"wake intervals {gaps} s outside 1.7..2.3 s: {out}")
    return {"counts": counts, "gaps_s": gaps, "byte_before_newline_hex": [o[1] for o in out], "first_rx": out[0][3]}


def _check_toggle(runs):
    complete = runs[1:-1]
    if len(complete) < 3 or {v for v, _ in complete} != {"0", "1"}:
        raise AssertionError(f"LED does not toggle: {runs}")
    half_s = [n * INTERVAL_US / 1e6 for _, n in complete]
    if not all(1.6 <= h <= 2.4 for h in half_s):
        raise AssertionError(f"half periods {half_s} s outside 1.6..2.4 s: {runs}")
    return half_s


def _recover_with_blink(request, cfg, hil_device):
    """Recover a DUT that sleeps in Standby: the debugger cannot attach, so cycle the DUT supply and flash the known blink
    sample inside the sample's 5 s initial wait. Only done when the DUT is powered by the WCH-LinkE (declared in the
    configuration); then detection, full readback and the blink are checked."""
    import subprocess
    from ch32hil.dut import MINICHLINK
    if cfg["voltage"].get("dut_power") != "wch_linke_3v3":
        raise AssertionError("DUT is not powered by the WCH-LinkE: power-cycle it by hand and re-flash blink")
    blink = Dut(hil_device.sample_dir("blink"), target=hil_device.name, framework="wch", ready_timeout=0)
    blink.build()
    subprocess.run([str(MINICHLINK), "-t"], capture_output=True, timeout=30)    # DUT 3.3 V off
    time.sleep(1.5)
    subprocess.run([str(MINICHLINK), "-3"], capture_output=True, timeout=30)    # DUT 3.3 V on: the 5 s wait starts
    r = subprocess.run([str(MINICHLINK), "-w", str(blink.binary), "flash", "-b"], capture_output=True, text=True, timeout=60)
    if "Image written." not in r.stdout + r.stderr:
        raise AssertionError(f"recovery flash failed: {r.stdout[-300:]} {r.stderr[-300:]}")
    blink.ready_timeout = 20.0
    with tempfile.TemporaryDirectory() as tmp:
        blink.readback(Path(tmp))          # detection (expected chip only) + full readback comparison
    blink.reset()
    return "DUT supply cycled; blink flashed, detected and read back"


def test_wch_standby_wake(request, hil_device, hil_config, hil_dut):
    dut = hil_dut(SAMPLE)
    run = new_run(hil_device, SAMPLE, limitation="standby current / clock stop not measured",
                  criteria="3 wake bursts with consecutive counts, 1.7..2.3 s apart; LED half period 1.6..2.4 s; "
                           "recovery: known blink re-flashed and read back")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)       # the 5 s initial wait is what makes flash/readback possible
        run.phase("dut_reset", dut.reset)
        run.phase("initial_wait", time.sleep, 7.0)      # 5 s "wait" + start; the DUT then enters Standby
        run.meta["wakes"] = run.phase("check_wake_bursts", _wakes, port.get("p"))
        runs = run.phase("measure_led", sample_gpio, port.get("p"), BLINK_GP, 300, INTERVAL_US)
        if runs is not None:
            run.meta["led_runs"] = runs
            run.meta["half_periods_s"] = run.phase("check_led_toggle", _check_toggle, runs)
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        # Recovery is part of the test even if the observation failed (it is recorded under the phase name "cleanup", the only one that also
        # runs after an earlier failure): the DUT must not be left sleeping in Standby.
        run.meta["recovery"] = run.phase("cleanup", _recover_with_blink, request, hil_config, hil_device)
        save(request, run, "wch_standby_wake")
    print(run.to_json())
    assert run.ok, run.to_json()
