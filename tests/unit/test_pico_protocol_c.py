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
