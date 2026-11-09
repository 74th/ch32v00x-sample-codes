"""DUT timer PWM HIL, measured on Pico GP14. Flashes DUT."""
from pathlib import Path
import tempfile
import pytest
from serial.tools import list_ports
from ch32hil import judge
from ch32hil.phases import Run
from ch32hil.pico import discover
from capture_helpers import pwm_edge_survey
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


def _edge_judge(port):
    """EDGE_MEASURE of PD2 (GP14): 1 kHz (TIM1 PSC 1 MHz tick, ATRLR 999) +-3 %, duty 25 % (CH1CVR 250) +-1 point."""
    rows, timeouts = pwm_edge_survey(port, 14, count=10, periods=8)
    return judge.judge_pwm_survey(rows, timeouts, 1000, duty_expected_ppm=250_000, duty_tol_ppm=10_000, label='timer_pwm')


def test_pwm(request, hil_device, hil_dut):
    run = Run(meta={'sample': 'timer_pwm', 'target': hil_device.target_mcu})
    dut = hil_dut('timer_pwm')
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
        run.meta['edge'] = run.phase('measure_edge', _edge_judge, holder.get('port'))
        print('PWM edge record:', run.meta['edge'])
    finally:
        run.phase('cleanup', _cleanup, holder.get('port'), 6)
    assert run.ok, run.to_json()
