"""DUT UART echo HIL; flashes UART sample. Requires reviewed UART wiring."""
from pathlib import Path
import tempfile

import pytest
from serial.tools import list_ports

from ch32hil.phases import Run
from ch32hil.pico import PicoError, discover
from test_blink_and_read import _prepare, _with_client, _cleanup

pytestmark = [pytest.mark.hil, pytest.mark.uart]


def _echo(port, payload):
    def action(client):
        reply = client.request('UART_XFER', 'DUT', 115200, 8, 'N', 1,
                               payload.hex(), len(payload), 2000)
        if not reply.ok:
            raise PicoError(f'UART_XFER failed: {reply.fields}')
        fields = dict(f.split('=', 1) for f in reply.fields if '=' in f)
        if fields.get('rx') != payload.hex() or fields.get('uart_errors') != '0x0':
            raise AssertionError(f'UART mismatch: {fields}')
        return fields
    return _with_client(port, 4, action)


def _no_data_timeout(port):
    def action(client):
        result = client.request('UART_XFER', 'DUT', 115200, 8, 'N', 1, '-', 1, 150)
        if result.ok or not result.fields or result.fields[0] != 'TIMEOUT':
            raise AssertionError(f'expected UART timeout, got {result}')
    return _with_client(port, 4, action)


def test_uart_echo(request, hil_device, hil_dut):
    port_opt = request.config.getoption('--hil-port')
    run = Run(meta={'sample': 'uart', 'target': hil_device.target_mcu, 'readback_policy': 'required'})
    dut = hil_dut('uart')
    holder = {}
    print('HIL UART: flash DUT uart sample; Pico GP8 TX/GP9 RX')
    try:
        run.phase('pico_prepare', lambda: holder.setdefault('port', discover(list_ports.comports, port_opt, 30)))
        run.phase('fixture_setup', _prepare, holder.get('port'), 6)
        run.phase('dut_build', dut.build)
        run.phase('dut_flash', dut.flash)
        with tempfile.TemporaryDirectory() as tmp:
            run.phase('dut_readback', dut.readback, Path(tmp))
        run.phase('dut_reset', dut.reset)
        run.phase('measure', _echo, holder.get('port'), bytes.fromhex('0055a5ff'))
        run.phase('measure_32', _echo, holder.get('port'), bytes(range(32)))
        run.phase('timeout_check', _no_data_timeout, holder.get('port'))
    finally:
        run.phase('cleanup', _cleanup, holder.get('port'), 6)
    assert run.ok, run.to_json()
