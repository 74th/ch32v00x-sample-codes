"""Host tests for the Pico fixture's SSD1306 interpreter (hardware/pico-tester/ssd1306_model.c)."""
import subprocess
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def binary(tmp_path_factory):
    out = tmp_path_factory.mktemp('ssd1306') / 'model'
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Werror', '-I', str(ROOT / 'hardware/pico-tester'),
                    str(ROOT / 'hardware/pico-tester/ssd1306_model.c'),
                    str(ROOT / 'tests/unit/ssd1306_model_harness.c'), '-o', str(out)], check=True)
    return out


def run(binary, *lines):
    out = subprocess.run([str(binary)], input='\n'.join(lines) + '\n', text=True, capture_output=True, check=True).stdout.splitlines()
    return out


def stats(line):
    return dict(kv.split('=', 1) for kv in line.split())


def cmd(*b):
    """One transfer carrying a command stream (control byte 0x00)."""
    return 'T 00' + bytes(b).hex()


def cmd_each(*b):
    """The helper's style: one transfer per command byte."""
    return [cmd(x) for x in b]


def data(payload):
    return 'T 40' + bytes(payload).hex()


FULL = [cmd(0x21, 0, 127), cmd(0x22, 0, 7)]


def test_full_frame_horizontal_matches_input_and_crc(binary):
    fb = bytes((i * 7 + 3) & 0xFF for i in range(1024))
    lines = [cmd(0x20, 0)] + FULL + [data(fb[i:i + 32]) for i in range(0, 1024, 32)] + ['S', 'P 0', 'P 7']
    out = run(binary, *lines)
    s = stats(out[0])
    assert s['frames'] == '1' and s['data'] == '1024' and s['unknown'] == '0' and s['bad_control'] == '0'
    assert s['crc'] == f'{zlib.crc32(fb):08x}'
    assert out[1] == fb[:128].hex() and out[2] == fb[896:].hex()


def test_arguments_may_span_transfers_like_the_helper(binary):
    lines = cmd_each(0x21, 0, 127, 0x22, 0, 7) + [data([0xAA]), 'S', 'P 0']
    out = run(binary, *lines)
    assert stats(out[0])['cmds'] == '6' and stats(out[0])['unknown'] == '0'
    assert out[1].startswith('aa00')


def test_window_wrap_and_frame_boundary(binary):
    # 2 columns x 2 pages window, horizontal: 4 bytes complete one frame, the 5th overwrites the first cell.
    out = run(binary, cmd(0x20, 0), cmd(0x21, 10, 11), cmd(0x22, 1, 2), data([1, 2, 3, 4, 5]), 'S', 'P 1', 'P 2')
    s = stats(out[0])
    assert s['frames'] == '1' and s['col'] == '11' and s['page'] == '1'
    assert out[1][20:24] == '0502' and out[2][20:24] == '0304'


def test_vertical_mode_order(binary):
    out = run(binary, cmd(0x20, 1), cmd(0x21, 0, 1), cmd(0x22, 0, 1), data([1, 2, 3, 4]), 'P 0', 'P 1')
    assert out[0][:4] == '0103' and out[1][:4] == '0204'


def test_page_mode_with_column_and_page_commands(binary):
    # default mode is page addressing: B3 selects the page, 0x05/0x12 set column 0x25
    out = run(binary, cmd(0xB3), cmd(0x05), cmd(0x12), data([0x77]), 'S', 'P 3')
    s = stats(out[0])
    assert s['mode'] == '2' and s['col'] == '38' and s['page'] == '3' and s['frames'] == '0'
    assert out[1][0x25 * 2:0x25 * 2 + 2] == '77'


def test_display_and_charge_pump_state(binary):
    out = run(binary, 'S', cmd(0x8D, 0x14, 0xAF), 'S', cmd(0xAE), 'S')
    a, b, c = (stats(x) for x in out)
    assert (a['display_on'], a['seen']) == ('0', '0')
    assert (b['display_on'], b['seen'], b['charge_pump']) == ('1', '1', '1')
    assert c['display_on'] == '0' and c['seen'] == '1'


def test_unknown_commands_and_bad_control_are_reported(binary):
    out = run(binary, cmd(0xDC, 0xFE, 0xAF), 'T 3f01', 'S')
    s = stats(out[0])
    assert s['unknown'] == '2' and s['unk'] == 'dcfe'
    assert s['bad_control'] == '1' and s['display_on'] == '1'


def test_unknown_values_are_kept_in_order(binary):
    out = run(binary, cmd(0xDC), cmd(0xFE), 'S')
    assert stats(out[0])['unk'] == 'dcfe'


def test_invalid_window_is_rejected_and_incomplete_transfers_are_tolerated(binary):
    out = run(binary, cmd(0x21, 100, 5), cmd(0x22, 0, 9), 'T 40', 'T 80', 'T', 'S')
    s = stats(out[0])
    assert s['unknown'] == '2' and s['data'] == '0' and s['frames'] == '0'


def test_co_bit_alternates_command_and_data(binary):
    # control 0xC0 = Co=1,D/C=1 -> one data byte, then a new control byte follows
    out = run(binary, 'T c011c022', 'S', 'P 0')
    s = stats(out[0])
    assert s['data'] == '2' and out[1].startswith('1122')


def test_column_command_keeps_page_pointer_like_the_arduino_oled_library(binary):
    """Horizontal mode, per page 0xB0+page (ignored outside page mode) and 0x21 0 127, then 128 data bytes, as the
    Arduino "OLED SSD1306 - SH1106" library does for a 128x32 panel. 0x21 resets only the column pointer
    (datasheet), so pages advance instead of overlapping on page 0."""
    def display(fill):
        lines = []
        for page in range(4):
            lines += [cmd(0xB0 + page, 0x21, 0, 127), data([fill + page] * 128)]
        return lines
    out = run(binary, cmd(0x20, 0), *display(0x10), 'S', *display(0x20), 'S', *[f'P {n}' for n in range(8)])
    first, second = stats(out[0]), stats(out[1])
    assert first['frames'] == '0' and first['page'] == '4' and first['col'] == '0'
    assert second['frames'] == '1' and second['page'] == '0'
    assert [out[2 + n][:2] for n in range(8)] == ['10', '11', '12', '13', '20', '21', '22', '23']


def test_page_command_resets_only_the_page_pointer(binary):
    out = run(binary, cmd(0x20, 0), cmd(0x21, 0, 127, 0x22, 0, 7), data([1] * 130), cmd(0x22, 2, 7), 'S')
    s = stats(out[0])
    assert s['page'] == '2' and s['col'] == '2' and s['frames'] == '0'
