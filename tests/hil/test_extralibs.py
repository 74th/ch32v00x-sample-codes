"""helper-verification HIL: samples that include pinned externals/ch32fun helpers.

DESTRUCTIVE: rebuilds and flashes the connected DUT. Judges only what the Pico observes
(see openspec change verify-ch32fun-extralibs-with-pico); real display/LED output is not verified.
"""
import dataclasses
import tempfile
import time
from pathlib import Path

import pytest
import serial
from serial.tools import list_ports

from ch32hil.expected import ssd1306_expected_frame
from ch32hil.phases import Run
from ch32hil.pico import PicoClient, PicoError, discover
from test_blink_and_read import _prepare, _with_client, _cleanup

pytestmark = [pytest.mark.hil, pytest.mark.extralibs]


def _fields(res):
    return dict(f.split('=', 1) for f in res.fields if '=' in f)


def _read(client, addr, reg, count):
    res = client.request('I2C_MASTER', addr, f'{reg:02x}', count, 500)
    if not res.ok:
        raise AssertionError(f'I2C read failed: {res.fields}')
    return _fields(res)['rx']


def _i2c_slave_helper(port, dut):
    def action(client):
        client.negotiate(['I2C_MASTER', 'I2C_PROBE', 'GPIO_SAMPLE'])
        for address, expected in ((0x42, 'ack=1'), (0x43, 'ack=0')):
            probe = client.request('I2C_PROBE', address, 500)
            if not probe.ok or expected not in probe.fields:
                raise AssertionError(f'ACK/NACK mismatch at {address:#x}: {probe.fields}')
        before = client.request('GPIO_SAMPLE', 5, 1, 1000)
        if not before.ok or 'samples=0' not in before.fields:
            raise AssertionError(f'PC0 must be Low before the write: {before.fields}')
        wr = client.request('I2C_MASTER', 0x42, '10aabbccdd', 0, 500)
        if not wr.ok:
            raise AssertionError(f'register write failed: {wr.fields}')
        after = client.request('GPIO_SAMPLE', 5, 1, 1000)
        if not after.ok or 'samples=1' not in after.fields:
            raise AssertionError(f'write callback (reg=0x10,len=4) not signalled on PC0: {after.fields}')
        if _read(client, 0x42, 0x10, 4) != 'aabbccdd':
            raise AssertionError('written registers not read back')
        if _read(client, 0x42, 0x20, 4) != '00102030':
            raise AssertionError('initial 0x20 region mismatch')
        # Observation registers, measured on hardware (okf/log): the write callback runs once per STOP of a
        # write-direction transaction (the address-only probe counts; read transactions end with NACK and do not),
        # and the read callback runs per byte read plus one extra byte per read transaction.
        # Sequence from reset: probe 0x42 (1 write cb), write 10aabbccdd (2), read 4 (5 read cb),
        # read 4 (5), observation read up to reg 3 (3) -> read count 13, last read reg 3.
        obs = _read(client, 0x42, 0x00, 5)
        write_count, write_reg, write_len, read_count, read_reg = bytes.fromhex(obs)
        if (write_count, write_reg, write_len, read_count, read_reg) != (2, 0x10, 4, 13, 3):
            raise AssertionError(f'callback observation mismatch: {obs}')
    return _with_client(port, 6, action)


@pytest.mark.parametrize(('sample', 'operation'), [('i2c_slave_helper', _i2c_slave_helper)])
def test_extralibs_helper(request, sample, operation, hil_device, hil_dut):
    run = Run(meta={'sample': sample, 'target': hil_device.target_mcu, 'readback_policy': 'required'})
    dut = hil_dut(sample)
    holder = {}
    print(f'HIL extralibs: flash DUT {sample}')
    try:
        run.phase('pico_prepare', lambda: holder.setdefault('port', discover(list_ports.comports, request.config.getoption('--hil-port'), 30)))
        run.phase('fixture_setup', _prepare, holder.get('port'), 6)
        run.phase('dut_build', dut.build)
        run.phase('dut_flash', dut.flash)
        with tempfile.TemporaryDirectory() as tmp:
            run.phase('dut_readback', dut.readback, Path(tmp))
        run.phase('dut_reset', dut.reset)
        run.phase('measure', operation, holder.get('port'), dut)
    finally:
        run.phase('cleanup', _cleanup, holder.get('port'), 6)
    assert run.ok, run.to_json()


def _capture_across_dut_reset(port, dut, frames, timeout_ms):
    """Arm SSD1306_CAPTURE first, then reset the DUT so its init commands are observed too.
    INIT restarts the capture at each display-off (initialisation), so traffic from before the reset or from an
    earlier boot of the DUT does not count. No minichlink detection call (-i) is made between arming and the reset:
    measured on hardware, `-i` itself restarts the DUT and would add a second boot to the capture window."""
    with serial.Serial(port, 115200, timeout=0.2, write_timeout=1) as link:
        link.reset_input_buffer()
        client = PicoClient(link, timeout=6)
        client.negotiate(['SSD1306_CAPTURE', 'SSD1306_PAGE'])
        client._id += 1
        rid = client._id
        link.write(f'{rid} SSD1306_CAPTURE {frames} {timeout_ms} INIT\n'.encode())
        time.sleep(0.2)
        dut.reset(wait=False)
        deadline = time.monotonic() + timeout_ms / 1000 + 3
        while time.monotonic() < deadline:
            raw = link.readline()
            if not raw:
                continue
            parts = raw.decode('ascii').split()
            if int(parts[0]) != rid:
                continue
            fields = dict(f.split('=', 1) for f in parts[2:] if '=' in f)
            pages = []
            for page in range(8):                      # fetched while the port is open; used only to explain a CRC mismatch
                res = client.request('SSD1306_PAGE', page)
                pages.append(dict(f.split('=', 1) for f in res.fields if '=' in f).get('fb') if res.ok else None)
            return parts[1] == 'OK', fields, pages
        raise PicoError('no SSD1306_CAPTURE response')


def _ssd1306(port, dut, expect_ok=True):
    with tempfile.TemporaryDirectory() as tmp:
        exp_fields, exp_pages = ssd1306_expected_frame(Path(tmp))
    ok, got, pages = _capture_across_dut_reset(port, dut, 2, 4000)
    if not ok:
        raise AssertionError(f'SSD1306 capture did not complete: {got}')
    problems = []
    for key, want in (('unknown', '0'), ('bad_control', '0'), ('overflow', '0'), ('display_on', '1'),
                      ('display_on_seen', '1'), ('charge_pump', '1')):
        if got.get(key) != want:
            problems.append(f'{key}={got.get(key)} (want {want})')
    if got.get('crc32') != exp_fields['crc32']:
        diff = [page for page in range(8) if pages[page] != exp_pages[page]]
        problems.append(f'frame CRC {got.get("crc32")} != expected {exp_fields["crc32"]}; differing pages {diff}')
    if problems:
        raise AssertionError('; '.join(problems) + f' | capture={got}')
    return got


ONE_MHZ = pytest.param('helper_1mhz', ('HELPER_CLOCK=1',), marks=pytest.mark.xfail(
    strict=False, reason='informational: helper default 1 MHz; Pico observed 0 transfers on 2026-11-07 (cause not isolated), '
                         'see okf/log/2026-11-07-2012-ssd1306-helper-hil.md'))


@pytest.mark.parametrize(('variant', 'make_args'), [('100khz', ('HELPER_CLOCK=0',)), ONE_MHZ])
def test_ssd1306_helper(request, variant, make_args, hil_device, hil_dut):
    """100 kHz is the primary judgement; the helper's default 1 MHz is recorded as its own result."""
    sample = 'ssd1306_i2c'
    run = Run(meta={'sample': sample, 'variant': variant, 'target': hil_device.target_mcu, 'readback_policy': 'required'})
    dut = dataclasses.replace(hil_dut(sample), make_args=make_args)
    holder = {}
    print(f'HIL extralibs: flash DUT {sample} variant={variant}')
    try:
        run.phase('pico_prepare', lambda: holder.setdefault('port', discover(list_ports.comports, request.config.getoption('--hil-port'), 30)))
        run.phase('fixture_setup', _prepare, holder.get('port'), 6)
        run.phase('dut_build', dut.build)
        run.phase('dut_flash', dut.flash)
        with tempfile.TemporaryDirectory() as tmp:
            run.phase('dut_readback', dut.readback, Path(tmp))
        run.phase('measure', _ssd1306, holder.get('port'), dut)
    finally:
        run.phase('cleanup', _cleanup, holder.get('port'), 6)
    assert run.ok, run.to_json()
