"""I2C HIL; writes DUT master/slave samples and uses Pico GP10/11."""
from pathlib import Path
import tempfile
import pytest
from serial.tools import list_ports
from ch32hil.phases import Run
from ch32hil import judge
from ch32hil.pico import PicoError, discover
from capture_helpers import captured, edge_record, observe_i2c_bus_error
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


SCL_GP = 11
SCL_HZ = 100_000    # ch32fun i2c_master: CKCFGR = 48 MHz / (2 * 100 kHz)


def _scl_period(port):
    """SCL period during a DUT-master transaction (the Pico answers as slave 0x42): median of the clock periods."""
    def action(client):
        result = client.request('I2C_SLAVE', 66, 2, '1234', 4000)
        if not result.ok:
            raise AssertionError(f'I2C transaction during the SCL measurement failed: {result.fields}')
    _, cap, start = captured(port, 'EDGE', SCL_GP, None, action, timeout=10)
    return judge.judge_period(edge_record(cap, start), SCL_HZ, judge.I2C_SCL_TOL_PCT, label='i2c_scl')


@pytest.mark.parametrize(('sample', 'operation'), [('i2c_slave', _i2c_master), ('i2c_master', _i2c_slave)])
def test_i2c_roles(request, sample, operation, hil_device, hil_dut):
    run = Run(meta={'sample': sample, 'target': hil_device.target_mcu, 'readback_policy': 'required'})
    dut = hil_dut(sample)
    holder = {}
    print(f'HIL I2C: flash DUT {sample}; Pico GP10 SDA/GP11 SCL')
    try:
        run.phase('pico_prepare', lambda: holder.setdefault('port', discover(list_ports.comports, request.config.getoption('--hil-port'), 30)))
        run.phase('fixture_setup', _prepare, holder.get('port'), 6)
        run.phase('dut_build', dut.build)
        run.phase('dut_flash', dut.flash)
        with tempfile.TemporaryDirectory() as tmp:
            run.phase('dut_readback', dut.readback, Path(tmp))
        run.phase('dut_reset', dut.reset)
        run.phase('measure', operation, holder.get('port'))
        if sample == 'i2c_master':
            run.meta['scl'] = run.phase('measure_scl', _scl_period, holder.get('port'))
            print('SCL record:', run.meta['scl'])
    finally:
        run.phase('cleanup', _cleanup, holder.get('port'), 6)
    assert run.ok, run.to_json()


def test_i2c_master_bus_error_observation(request, hil_device, hil_dut):
    """Observation only: hold SDA, then SCL, Low while the DUT master retries, and record whether it recovers.
    The book's sample has no bus recovery; only a fixture fault (the Pico not releasing the line) fails this test."""
    run = Run(meta={'sample': 'i2c_master', 'target': hil_device.target_mcu, 'observation': 'i2c_bus_error'})
    dut = hil_dut('i2c_master')
    holder = {}
    print('HIL I2C bus error (observation): DUT master; Pico holds GP10/GP11 Low')
    try:
        run.phase('pico_prepare', lambda: holder.setdefault('port', discover(list_ports.comports, request.config.getoption('--hil-port'), 30)))
        run.phase('fixture_setup', _prepare, holder.get('port'), 6)
        run.phase('dut_build', dut.build)
        run.phase('dut_flash', dut.flash)
        with tempfile.TemporaryDirectory() as tmp:
            run.phase('dut_readback', dut.readback, Path(tmp))
        run.phase('dut_reset', dut.reset)
        run.meta['observation_result'] = run.phase(
            'observe', observe_i2c_bus_error, holder.get('port'), 66, '1234', '1234', 1000, None)
        print('BUS ERROR observation:', run.meta['observation_result'])
    finally:
        run.phase('cleanup', _cleanup, holder.get('port'), 6)
    assert run.ok, run.to_json()
