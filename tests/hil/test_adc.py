"""DUT ADC functional HIL; flashes ADC sample and drives GP13 PWM/RC."""
from pathlib import Path
import tempfile

import pytest
from serial.tools import list_ports
from ch32hil.phases import Run
from ch32hil.pico import PicoError, discover
from test_blink_and_read import _prepare, _with_client, _cleanup

pytestmark = [pytest.mark.hil, pytest.mark.adc]


def _adc_sweep(port, adc_max):
    def action(client):
        client.negotiate(['ADC_OBSERVE'])
        values = []
        for duty in (10, 20, 50, 80, 90):
            reply = client.request('ADC_OBSERVE', duty, 500, 1500)
            if not reply.ok:
                raise PicoError(f'ADC_OBSERVE failed: {reply.fields}')
            fields = dict(f.split('=', 1) for f in reply.fields if '=' in f)
            if fields.get('duty') != str(duty) or fields.get('calibrated') != '0':
                raise AssertionError(f'bad ADC settings: {fields}')
            values.append(int(fields['adc']))
        print('ADC uncalibrated duty/reading:', list(zip((10, 20, 50, 80, 90), values)))
        if not (all(0 <= value <= adc_max for value in values) and all(a < b for a, b in zip(values, values[1:]))):
            raise AssertionError(f'ADC values not increasing: {values}')
        return values
    return _with_client(port, 5, action)


def test_adc_functional(request, hil_device, hil_dut):
    run = Run(meta={'sample': 'adc', 'target': hil_device.target_mcu, 'uncalibrated': True})
    dut = hil_dut('adc')
    holder = {}
    print('HIL ADC: flash DUT ADC sample; PWM GP13 -> RC -> PA2, UART PD5 -> GP9')
    try:
        run.phase('pico_prepare', lambda: holder.setdefault('port', discover(list_ports.comports, request.config.getoption('--hil-port'), 30)))
        run.phase('fixture_setup', _prepare, holder.get('port'), 6)
        run.phase('dut_build', dut.build)
        run.phase('dut_flash', dut.flash)
        with tempfile.TemporaryDirectory() as tmp:
            run.phase('dut_readback', dut.readback, Path(tmp))
        run.phase('dut_reset', dut.reset)
        run.phase('measure', _adc_sweep, holder.get('port'), hil_device.adc_max)
    finally:
        run.phase('cleanup', _cleanup, holder.get('port'), 6)
    assert run.ok, run.to_json()
