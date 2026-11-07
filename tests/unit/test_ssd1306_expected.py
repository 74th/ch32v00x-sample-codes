"""Expected SSD1306 frame for samples_ch32v003_ch32fun/ssd1306_i2c, produced on the host by running the
pinned externals/ch32fun ssd1306.h drawing code with the same scene.h as the DUT."""
import zlib
from pathlib import Path

import pytest

from ch32hil.expected import ssd1306_expected_frame as expected_frame

ROOT = Path(__file__).resolve().parents[2]
EXTRALIBS = ROOT / 'externals/ch32fun/extralibs'


@pytest.fixture(scope='module')
def expected(tmp_path_factory):
    if not EXTRALIBS.is_dir():
        pytest.skip('externals/ch32fun not checked out')
    return expected_frame(tmp_path_factory.mktemp('ssd1306-expected'))


def test_expected_frame_is_deterministic(tmp_path, expected):
    again = expected_frame(tmp_path)
    assert again == expected


def test_helper_sends_blank_frame_then_scene_frame(expected):
    fields, _ = expected
    assert fields['init_frames'] == '1' and fields['frames'] == '2'
    assert fields['blank_crc32'] == f'{zlib.crc32(bytes(1024)):08x}'   # a blank 128x64 frame
    assert fields['crc32'] != fields['blank_crc32']
    assert fields['unknown'] == '0' and fields['bad_control'] == '0'
    assert fields['display_on'] == '1' and fields['charge_pump'] == '1'


def test_scene_pixels_match_the_drawing_intent(expected):
    """Independent spot checks (not via the helper's own pixel code): frame border, sprite corner, diagonal-ish dots."""
    _, pages = expected
    fb = [bytes.fromhex(p) for p in pages]

    def pixel(x, y):
        return (fb[y // 8][x] >> (y % 8)) & 1
    assert all(pixel(x, 0) and pixel(x, 63) for x in range(128))        # rect border top/bottom
    assert all(pixel(0, y) and pixel(127, y) for y in range(64))        # rect border left/right
    assert pixel(100, 30) == 1 and pixel(115, 45) == 1                  # sprite corners are set (0xff rows)
    assert pixel(100, 32) == 1 and pixel(101, 32) == 0                  # sprite row 2 = 0xbf (1011 1111), MSB = leftmost
    assert pixel(4, 28) == 1 and pixel(6, 29) == 1                      # drawPixel dots 4+2i, 28+(i%8)
    assert pixel(60, 40) == 0                                           # empty area
    assert sum(bin(b).count('1') for p in fb for b in p) > 400          # text, sprite, border present


def test_v002_port_uses_the_same_scene_and_colors():
    v3, v2 = ROOT / 'samples_ch32v003_ch32fun', ROOT / 'samples_ch32v002_ch32fun'
    assert (v3 / 'ssd1306_i2c/scene.h').read_text() == (v2 / 'ssd1306_i2c/scene.h').read_text()
    from ch32hil.expected import ws2812_sample_values
    assert ws2812_sample_values(v2 / 'ws2812_spi/main.c') == ws2812_sample_values(v3 / 'ws2812_spi/main.c')
