"""Exercise the firmware's real line parser on the host with hardware actions stubbed."""
import subprocess
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def parser_binary(tmp_path_factory):
    output = tmp_path_factory.mktemp('pico-parser') / 'parser'
    subprocess.run(['gcc', '-std=c11', '-D_POSIX_C_SOURCE=200809L', '-Wall', '-Werror',
                    '-I', str(ROOT / 'hardware/pico-tester'),
                    str(ROOT / 'hardware/pico-tester/protocol.c'),
                    str(ROOT / 'hardware/pico-tester/ssd1306_fixture.c'),
                    str(ROOT / 'hardware/pico-tester/ssd1306_model.c'),
                    str(ROOT / 'hardware/pico-tester/ws2812_fixture.c'),
                    str(ROOT / 'hardware/pico-tester/ws2812_classify.c'),
                    str(ROOT / 'tests/unit/pico_protocol_harness.c'), '-o', str(output)], check=True)
    return output


def test_real_parser_caps_safe_and_errors(parser_binary):
    result = subprocess.run([str(parser_binary)], input='1 CAPS\n2 RESET_SAFE\n3 UNKNOWN\n4 CAPS extra\nxyz CAPS\n4294967296 CAPS\n',
                            text=True, capture_output=True, check=True).stdout.splitlines()
    assert result[0].startswith('1 OK proto=2 ')
    assert result[1] == '2 OK safe=1'
    assert result[2] == '3 ERR UNSUPPORTED command'
    assert result[3] == '4 ERR INVALID arguments'
    assert result[4:] == ['0 ERR INVALID request_id', '0 ERR INVALID request_id']


def _run(parser_binary, *lines):
    return subprocess.run([str(parser_binary)], input='\n'.join(lines) + '\n', text=True, capture_output=True, check=True).stdout.splitlines()


def test_caps_lists_ssd1306_commands(parser_binary):
    cmds = _run(parser_binary, '1 CAPS')[0].split('cmds=')[1].split()[0].split(',')
    assert 'SSD1306_CAPTURE' in cmds and 'SSD1306_PAGE' in cmds


@pytest.mark.parametrize('line', [
    '1 SSD1306_CAPTURE', '1 SSD1306_CAPTURE 1', '1 SSD1306_CAPTURE 0 100', '1 SSD1306_CAPTURE 9 100',
    '1 SSD1306_CAPTURE 1 9', '1 SSD1306_CAPTURE 1 5001', '1 SSD1306_CAPTURE 1 100 x', '1 SSD1306_CAPTURE a 100',
    '1 SSD1306_CAPTURE 1 100 init', '1 SSD1306_CAPTURE 1 100 INIT x',
])
def test_ssd1306_capture_rejects_bad_arguments(parser_binary, line):
    assert _run(parser_binary, line) == ['1 ERR INVALID ssd1306_capture_arguments']


@pytest.mark.parametrize('line', ['1 SSD1306_PAGE', '1 SSD1306_PAGE 8', '1 SSD1306_PAGE -1', '1 SSD1306_PAGE 1 2'])
def test_ssd1306_page_rejects_bad_arguments(parser_binary, line):
    assert _run(parser_binary, line) == ['1 ERR INVALID ssd1306_page_arguments']


def test_ssd1306_page_before_capture_is_an_error(parser_binary):
    assert _run(parser_binary, '1 SSD1306_PAGE 0') == ['1 ERR INVALID no_capture']


def test_ssd1306_capture_reports_frame_and_page(parser_binary):
    import zlib
    out = _run(parser_binary, '1 SSD1306_CAPTURE 2 100', '2 SSD1306_PAGE 7')
    fields = dict(f.split('=', 1) for f in out[0].split()[2:] if '=' in f)
    fb = bytes((i * 3) & 0xFF for i in range(1024))
    assert out[0].startswith('1 OK ') and fields['frames'] == '2' and fields['unknown'] == '0'
    assert fields['display_on'] == '1' and fields['display_on_seen'] == '1'
    assert fields['crc32'] == f'{zlib.crc32(fb):08x}' and fields['safe'] == '1'
    page = dict(f.split('=', 1) for f in out[1].split()[2:] if '=' in f)
    assert page['fb'] == fb[896:].hex() and len(page['fb']) == 256


def test_ssd1306_capture_timeout_is_not_success_and_invalidates_previous_capture(parser_binary):
    out = _run(parser_binary, '1 SSD1306_CAPTURE 1 100', '2 SSD1306_CAPTURE 1 77', '3 SSD1306_PAGE 0')
    assert out[0].startswith('1 OK ')
    assert out[1].startswith('2 ERR TIMEOUT frames=0 ')
    assert out[2].split()[:3] == ['3', 'OK', 'page=0']  # partial state remains readable for diagnosis


def test_ssd1306_selftest_command_is_wired_and_rejects_arguments(parser_binary):
    out = _run(parser_binary, '1 SSD1306_SELFTEST', '2 SSD1306_SELFTEST x', '3 CAPS')
    assert out[0].startswith('1 OK frames=2 unknown=1 ') and 'wrong_address_rc=-1' in out[0] and out[0].endswith('safe=1')
    assert out[1] == '2 ERR INVALID arguments'
    assert 'SSD1306_SELFTEST' in out[2].split('cmds=')[1].split()[0].split(',')


def test_ssd1306_capture_accepts_init_option(parser_binary):
    assert _run(parser_binary, '1 SSD1306_CAPTURE 1 100 INIT')[0].startswith('1 OK frames=1 ')


def _fields(line):
    return dict(f.split('=', 1) for f in line.split()[2:] if '=' in f)


def test_caps_lists_ws2812_commands(parser_binary):
    cmds = _run(parser_binary, '1 CAPS')[0].split('cmds=')[1].split()[0].split(',')
    assert 'WS2812_CAPTURE' in cmds and 'WS2812_SELFTEST' in cmds


@pytest.mark.parametrize('line', [
    '1 WS2812_CAPTURE', '1 WS2812_CAPTURE 7', '1 WS2812_CAPTURE 7 18', '1 WS2812_CAPTURE 6 18 100',
    '1 WS2812_CAPTURE 8 18 100', '1 WS2812_CAPTURE 21 18 100', '1 WS2812_CAPTURE 7 0 100', '1 WS2812_CAPTURE 7 2 100',
    '1 WS2812_CAPTURE 7 97 100', '1 WS2812_CAPTURE 7 18 9', '1 WS2812_CAPTURE 7 18 5001', '1 WS2812_CAPTURE 7 18 100 x',
    '1 WS2812_CAPTURE x 18 100',
])
def test_ws2812_capture_rejects_bad_arguments(parser_binary, line):
    assert _run(parser_binary, line) == ['1 ERR INVALID ws2812_capture_arguments']


def test_ws2812_capture_success_reports_bytes_and_widths(parser_binary):
    line = _run(parser_binary, '1 WS2812_CAPTURE 7 18 100')[0]
    f = _fields(line)
    assert line.startswith('1 OK ') and f['pin'] == '7' and f['bits'] == '144' and f['bad_pulses'] == '0'
    assert f['rx'] == 'a55aa55aa55aa55aa55aa55aa55aa55aa55a' and f['safe'] == '1'
    assert f['t0h_ns'] == '336' and f['t1h_ns'] == '992' and f['threshold_ns'] == '655' and f['ns_per_count'] == '16'


def test_ws2812_capture_timeout_with_nothing(parser_binary):
    assert _run(parser_binary, '1 WS2812_CAPTURE 7 18 77') == ['1 ERR TIMEOUT ws2812 bits=0 safe=1']


def test_ws2812_capture_short_frame_is_reported_with_both_lengths(parser_binary):
    line = _run(parser_binary, '1 WS2812_CAPTURE 7 18 78')[0]
    assert line.startswith('1 ERR WS2812 frame_bits=136 expected=144 bad_pulses=0 tail_bits=0 tail=00 last_high_ns=992 idle_high=0 ')


def test_ws2812_capture_long_frame_is_reported(parser_binary):
    assert _run(parser_binary, '1 WS2812_CAPTURE 7 18 79') == ['1 ERR WS2812 frame_too_long expected=144 safe=1']


def test_ws2812_capture_out_of_range_pulse_is_an_error_with_the_data(parser_binary):
    line = _run(parser_binary, '1 WS2812_CAPTURE 20 18 80')[0]
    assert line.startswith('1 ERR WS2812 ') and _fields(line)['bad_pulses'] == '1' and 'rx=' in line


@pytest.mark.parametrize('arg', ['', 'ok', 'OK BAD', 'FAST', 'OK x'])
def test_ws2812_selftest_rejects_bad_arguments(parser_binary, arg):
    assert _run(parser_binary, f'1 WS2812_SELFTEST {arg}'.rstrip()) == ['1 ERR INVALID ws2812_selftest_arguments']


def test_ws2812_selftest_modes(parser_binary):
    ok, bad, timeout = _run(parser_binary, '1 WS2812_SELFTEST OK', '2 WS2812_SELFTEST BADWIDTH', '3 WS2812_SELFTEST TIMEOUT')
    assert ok.startswith('1 OK mode=OK ') and _fields(ok)['rx'] == _fields(ok)['tx'] == 'a55aa55aa55a'
    assert bad.startswith('2 OK mode=BADWIDTH ') and _fields(bad)['bad_pulses'] == '1'
    assert timeout.startswith('3 OK mode=TIMEOUT ') and _fields(timeout)['words'] == '0' and _fields(timeout)['tx'] == '-'


def test_caps_lists_capture_commands_and_limits(parser_binary):
    caps = _run(parser_binary, '1 CAPS')[0]
    cmds = caps.split('cmds=')[1].split()[0].split(',')
    for name in ('EDGE_MEASURE', 'EDGE_SELFTEST', 'CAPTURE_START', 'CAPTURE_READ', 'CAPTURE_STOP', 'I2C_HOLD'):
        assert name in cmds
    for key in ('cap_edge=1', 'edge_res_ps=16000', 'capture_uart_baud_max=921600', 'capture_uart_pins=5,6,7,9,10,11,14,15,17,18,20,21,22',
                'i2c_hold_pins=10,11', 'uart_baud_max=921600'):
        assert key in caps


def test_capture_commands_are_dispatched(parser_binary):
    out = _run(parser_binary, '1 EDGE_MEASURE 5 10 100', '2 EDGE_SELFTEST 17 18 100000 50', '3 CAPTURE_START EDGE 5',
               '4 CAPTURE_READ 0 10', '5 CAPTURE_STOP', '6 I2C_HOLD SDA 100')
    assert [line.split('stub=')[1] for line in out] == ['EDGE_MEASURE', 'EDGE_SELFTEST', 'CAPTURE_START', 'CAPTURE_READ',
                                                        'CAPTURE_STOP', 'I2C_HOLD']


def test_ws2812_commands_conflict_while_a_capture_owns_pio1(parser_binary):
    out = _run(parser_binary, '1 CAPTURE_START EDGE 5', '2 WS2812_CAPTURE 7 3 100', '3 WS2812_SELFTEST OK', '4 RESET_SAFE',
               '5 WS2812_SELFTEST BAD')
    assert out[1] == '2 ERR CONFLICT capture_active' and out[2] == '3 ERR CONFLICT capture_active'
    assert out[3] == '4 OK safe=1'
    assert not out[4].startswith('5 ERR CONFLICT')
