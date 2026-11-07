"""SPI HIL: flash CH32V003 SPI master and exercise Pico PIO slave."""
from pathlib import Path
import tempfile
import pytest
from serial.tools import list_ports
from ch32hil.dut import Dut, ROOT
from ch32hil.phases import Run
from ch32hil.pico import discover
from test_blink_and_read import _prepare, _with_client, _cleanup

pytestmark = [pytest.mark.hil, pytest.mark.spi]


def _spi_slave(port):
    def action(client):
        client.negotiate(['SPI_SLAVE'])
        invalid = client.request('SPI_SLAVE', '3cc3', 'MODE3')
        if invalid.ok or not invalid.fields or invalid.fields[0] != 'UNSUPPORTED':
            raise AssertionError(f'unsupported mode accepted: {invalid.fields}')
        for reply, expected in (('3cc3', 'samples=1'), ('0000', 'samples=0')):
            result = client.request('SPI_SLAVE', reply, 'MODE0')
            if not result.ok or not {'rx=a55a', f'tx={reply}', 'mode=0'}.issubset(result.fields):
                raise AssertionError(f'SPI transfer mismatch: {result.fields}')
            indicator = client.request('GPIO_SAMPLE', 14, 1, 1000)
            if not indicator.ok or expected not in indicator.fields:
                raise AssertionError(f'DUT SPI response validation failed: {indicator.fields}')
    return _with_client(port, 5, action)


def test_spi_master_with_pico_slave(request):
    run = Run(meta={'sample': 'spi_master', 'target': 'CH32V003'})
    dut = Dut(ROOT / 'samples_ch32v003_ch32fun/spi_master')
    holder = {}
    print('HIL SPI: flash CH32V003 SPI master; Pico GP4..7 slave')
    try:
        run.phase('pico_prepare', lambda: holder.setdefault('port', discover(list_ports.comports, request.config.getoption('--hil-port'), 30)))
        run.phase('fixture_setup', _prepare, holder.get('port'), 6)
        run.phase('dut_build', dut.build)
        run.phase('dut_flash', dut.flash)
        with tempfile.TemporaryDirectory() as tmp:
            run.phase('dut_readback', dut.readback, Path(tmp))
        run.phase('dut_reset', dut.reset)
        run.phase('measure', _spi_slave, holder.get('port'))
    finally:
        run.phase('cleanup', _cleanup, holder.get('port'), 6)
    assert run.ok, run.to_json()
