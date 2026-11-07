"""I2C HIL; writes DUT master/slave samples and uses Pico GP10/11."""
from pathlib import Path
import tempfile
import pytest
from serial.tools import list_ports
from ch32hil.dut import Dut, ROOT
from ch32hil.phases import Run
from ch32hil.pico import PicoError, discover
from test_blink_and_read import _prepare, _with_client, _cleanup

pytestmark = [pytest.mark.hil, pytest.mark.i2c]


def _i2c_master(port):
    def action(client):
        client.negotiate(['I2C_MASTER', 'I2C_PROBE'])
        for address, expected in ((66, 'ack=1'), (67, 'ack=0')):
            probe = client.request('I2C_PROBE', address, 500)
            if not probe.ok or expected not in probe.fields:
                raise AssertionError(f'I2C ACK/NACK mismatch: {probe.fields}')
        res = client.request('I2C_MASTER', 66, '1234', 2, 500)
        if not res.ok or 'rx=1234' not in res.fields:
            raise AssertionError(f'I2C master transfer mismatch: {res.fields}')
        timeout = client.request('I2C_SLAVE', 66, 1, '-', 100)
        if timeout.ok or not timeout.fields or timeout.fields[0] != 'TIMEOUT':
            raise AssertionError(f'I2C idle slave timeout not reported: {timeout.fields}')
        negative = client.request('I2C_MASTER', 67, '55', 0, 500)
        if negative.ok or not negative.fields or negative.fields[0] not in ('I2C', 'TIMEOUT'):
            raise AssertionError(f'I2C wrong address accepted: {negative.fields}')
    return _with_client(port, 5, action)


def _i2c_slave(port):
    def action(client):
        client.negotiate(['I2C_SLAVE'])
        res = client.request('I2C_SLAVE', 66, 2, '1234', 4000)
        if not res.ok or not {'rx=55aa', 'received=2', 'sent=2'}.issubset(res.fields):
            raise AssertionError(f'I2C slave transaction mismatch: {res.fields}')
        indicator = client.request('GPIO_SAMPLE', 5, 1, 1000)
        if not indicator.ok or 'samples=1' not in indicator.fields:
            raise AssertionError(f'DUT did not confirm received bytes: {indicator.fields}')
        bad = client.request('I2C_SLAVE', 66, 2, 'dead', 4000)
        if not bad.ok or 'rx=55aa' not in bad.fields:
            raise AssertionError(f'negative I2C transaction failed: {bad.fields}')
        indicator = client.request('GPIO_SAMPLE', 5, 1, 1000)
        if not indicator.ok or 'samples=0' not in indicator.fields:
            raise AssertionError(f'DUT failed to reject wrong received bytes: {indicator.fields}')
    return _with_client(port, 6, action)


@pytest.mark.parametrize(('sample', 'operation'), [('i2c_slave', _i2c_master), ('i2c_master', _i2c_slave)])
def test_i2c_roles(request, sample, operation):
    run = Run(meta={'sample': sample, 'target': 'CH32V003', 'readback_policy': 'required'})
    dut = Dut(ROOT / 'samples_ch32v003_ch32fun' / sample)
    holder = {}
    print(f'HIL I2C: flash CH32V003 {sample}; Pico GP10 SDA/GP11 SCL')
    try:
        run.phase('pico_prepare', lambda: holder.setdefault('port', discover(list_ports.comports, request.config.getoption('--hil-port'), 30)))
        run.phase('fixture_setup', _prepare, holder.get('port'), 6)
        run.phase('dut_build', dut.build)
        run.phase('dut_flash', dut.flash)
        with tempfile.TemporaryDirectory() as tmp:
            run.phase('dut_readback', dut.readback, Path(tmp))
        run.phase('dut_reset', dut.reset)
        run.phase('measure', operation, holder.get('port'))
    finally:
        run.phase('cleanup', _cleanup, holder.get('port'), 6)
    assert run.ok, run.to_json()
