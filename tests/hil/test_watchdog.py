"""Watchdog reset signature HIL; flashes DUT and resets it while Pico observes."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import time
import pytest
from serial.tools import list_ports
from ch32hil.dut import Dut, ROOT
from ch32hil.phases import Run
from ch32hil.pico import discover
from ch32hil.watchdog import analyse_signature
from test_blink_and_read import _prepare, _with_client, _cleanup

pytestmark = [pytest.mark.hil, pytest.mark.watchdog]


def _sequence(port, dut):
    # Let any in-flight sequence from flash/readback finish (3 pulses + ~1 s IWDG + 6 pulses < 4 s)
    # so only the sequence started by our reset is observed.
    dut.wait_ready("reset")  # probe before sampling so the reset below is not delayed
    time.sleep(4.5)
    def read():
        def action(client):
            client.negotiate(['GPIO_SEQUENCE'])
            return client.sample_gpio(5, 300, 15000, sequence=True)
        return _with_client(port, 8, action)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(read)
        time.sleep(.4)
        dut.reset(wait=False)
        samples = future.result(timeout=8)
    result = analyse_signature(samples, 15000)
    print(f"watchdog signature: 3+6 pulses, gap={result['gap_us']} us, highs={result['high_us']}")


def test_watchdog_reset(request):
    run = Run(meta={'sample': 'watchdog', 'target': 'CH32V003'})
    dut = Dut(ROOT / 'samples_ch32v003_ch32fun/watchdog')
    holder = {}
    print('HIL WATCHDOG: flash and reset CH32V003; observe PC0 -> Pico GP5')
    try:
        run.phase('pico_prepare', lambda: holder.setdefault('port', discover(list_ports.comports, request.config.getoption('--hil-port'), 30)))
        run.phase('fixture_setup', _prepare, holder.get('port'), 6)
        run.phase('dut_build', dut.build)
        run.phase('dut_flash', dut.flash)
        with tempfile.TemporaryDirectory() as tmp:
            run.phase('dut_readback', dut.readback, Path(tmp))
        run.phase('measure', _sequence, holder.get('port'), dut)
    finally:
        run.phase('cleanup', _cleanup, holder.get('port'), 6)
    assert run.ok, run.to_json()


def test_sleep_wake(request):
    from test_blink_and_read import _measure
    run = Run(meta={'sample': 'sleep_wake', 'target': 'CH32V003',
                    'limitation': 'GPIO wake signature only; power consumption not measured'})
    dut = Dut(ROOT / 'samples_ch32v003_ch32fun/sleep_wake')
    holder = {}
    print('HIL SLEEP: flash sleep_wake; observe PC0 -> Pico GP5')
    try:
        run.phase('pico_prepare', lambda: holder.setdefault('port', discover(list_ports.comports, request.config.getoption('--hil-port'), 30)))
        run.phase('fixture_setup', _prepare, holder.get('port'), 6)
        run.phase('dut_build', dut.build)
        run.phase('dut_flash', dut.flash)
        with tempfile.TemporaryDirectory() as tmp:
            run.phase('dut_readback', dut.readback, Path(tmp))
        run.phase('dut_reset', dut.reset)
        run.phase('measure', _measure, holder.get('port'), 6, 5)
    finally:
        run.phase('cleanup', _cleanup, holder.get('port'), 6)
    assert run.ok, run.to_json()
