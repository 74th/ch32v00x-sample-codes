"""Expected WS2812 wire bytes, derived from the pinned helper's source (not from the DUT or the Pico)."""
import pytest

from ch32hil.expected import (EXTRALIBS, ws2812_nibble_shifts, ws2812_sample_values, ws2812_wire_bytes)

pytestmark = pytest.mark.skipif(not EXTRALIBS.is_dir(), reason="externals/ch32fun not checked out")


def test_helper_nibble_order_per_colour_order():
    assert ws2812_nibble_shifts("WSGRB") == [12, 8, 4, 0, 20, 16]
    assert ws2812_nibble_shifts("WSRBG") == [12, 8, 20, 16, 4, 0]
    assert ws2812_nibble_shifts("default") == [20, 16, 12, 8, 4, 0]


def test_wire_bytes_for_one_value_in_each_order():
    v = 0xAABBCC          # bits 23:16 = AA, 15:8 = BB, 7:0 = CC
    assert ws2812_wire_bytes([v], "WSGRB") == bytes([0xBB, 0xCC, 0xAA])
    assert ws2812_wire_bytes([v], "WSRBG") == bytes([0xBB, 0xAA, 0xCC])
    assert ws2812_wire_bytes([v], "default") == bytes([0xAA, 0xBB, 0xCC])


def test_sample_colors_go_out_as_g_r_b():
    values = ws2812_sample_values()
    assert len(values) == 6
    wire = ws2812_wire_bytes(values)
    assert wire.hex() == '00ffa55a0180ff000ff033cc55aa7e8118c3'
    assert len(wire) == 18


def test_unreadable_helper_is_an_error(tmp_path):
    bad = tmp_path / 'h.h'
    bad.write_text('#ifdef WSRBG\n#elif defined( WSGRB )\n#else\n#endif\n')
    with pytest.raises(ValueError):
        ws2812_nibble_shifts("WSGRB", bad)
