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
