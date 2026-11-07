"""CH32V003 timer PWM HIL, measured on Pico GP14. Flashes DUT."""
from pathlib import Path
import tempfile
import pytest
from serial.tools import list_ports
from ch32hil.dut import Dut, ROOT
from ch32hil.phases import Run
from ch32hil.pico import discover
from test_blink_and_read import _prepare, _with_client, _cleanup

pytestmark = [pytest.mark.hil, pytest.mark.pwm]


def _measure_pwm(port):
    def action(client):
        client.negotiate(['GPIO_PULSE'])
        result = client.request('GPIO_PULSE', 14, 3000)
        if not result.ok:
            raise AssertionError(f'PWM measurement failed: {result.fields}')
        fields = dict(x.split('=', 1) for x in result.fields if '=' in x)
        period, duty = int(fields['period_us']), int(fields['duty_ppm'])
        print(f'PWM period={period} us duty={duty} ppm; limits 800..1200 us, 200000..300000 ppm')
        if not (800 <= period <= 1200 and 200000 <= duty <= 300000):
            raise AssertionError(f'PWM outside functional tolerance: {fields}')
    return _with_client(port, 5, action)


def test_pwm(request):
    run = Run(meta={'sample': 'timer_pwm', 'target': 'CH32V003'})
    dut = Dut(ROOT / 'samples_ch32v003_ch32fun/timer_pwm')
    holder = {}
    print('HIL PWM: flash timer_pwm; DUT PD2 -> Pico GP14')
    try:
        run.phase('pico_prepare', lambda: holder.setdefault('port', discover(list_ports.comports, request.config.getoption('--hil-port'), 30)))
        run.phase('fixture_setup', _prepare, holder.get('port'), 6)
        run.phase('dut_build', dut.build)
        run.phase('dut_flash', dut.flash)
        with tempfile.TemporaryDirectory() as tmp:
            run.phase('dut_readback', dut.readback, Path(tmp))
        run.phase('dut_reset', dut.reset)
        run.phase('measure', _measure_pwm, holder.get('port'))
    finally:
        run.phase('cleanup', _cleanup, holder.get('port'), 6)
    assert run.ok, run.to_json()
