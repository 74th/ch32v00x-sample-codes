"""Host tests for the Pico fixture's WS2812 pulse classifier (hardware/pico-tester/ws2812_classify.c)."""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MARK = 0xFFFFFFFF
NS = 16          # ns per PIO count at 125 MHz (2 cycles per loop iteration)
ZERO, ONE = 21, 62   # nominal counts for 336 ns / 992 ns High


@pytest.fixture(scope='module')
def binary(tmp_path_factory):
    out = tmp_path_factory.mktemp('ws2812') / 'classify'
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Werror', '-I', str(ROOT / 'hardware/pico-tester'),
                    str(ROOT / 'hardware/pico-tester/ws2812_classify.c'),
                    str(ROOT / 'tests/unit/ws2812_classify_harness.c'), '-o', str(out)], check=True)
    return out


def words_for(data: bytes, high0=ZERO, high1=ONE, end=True, bad_at=None, bad_high=42):
    ws = []
    bits = [(b >> (7 - i)) & 1 for b in data for i in range(8)]
    for k, bit in enumerate(bits):
        h = bad_high if k == bad_at else (high1 if bit else high0)
        low = MARK if (end and k == len(bits) - 1) else 30
        ws += [h, low]
    return ws


def decode(binary, ws, npc=NS):
    text = f'{npc} ' + ' '.join(f'{w:x}' for w in ws) + '\n'
    out = subprocess.run([str(binary)], input=text, text=True, capture_output=True, check=True).stdout.strip()
    return dict(kv.split('=', 1) for kv in out.split())


def test_typical_frame_round_trips(binary):
    data = bytes([0x00, 0xFF, 0xA5, 0x5A, 0x01, 0x80])
    r = decode(binary, words_for(data))
    assert r['rx'] == data.hex() and r['bits'] == '48' and r['bytes'] == '6' and r['ended'] == '1'
    assert r['bad'] == '0' and r['partial'] == '0'
    assert r['t0h'] == str(ZERO * NS) and r['t1h'] == str(ONE * NS)


def test_out_of_range_pulse_is_counted_and_not_in_medians(binary):
    data = bytes([0xFF, 0x00])
    r = decode(binary, words_for(data, bad_at=3, bad_high=42))       # 672 ns: between the classes
    assert r['bad'] == '1' and r['bits'] == '16'
    assert r['rx'][2:] == '00'                                         # the other bits are intact
    assert r['t1h'] == str(ONE * NS)                                   # the bad pulse is not part of the 1-bit median


# 190..480 ns is a 0, 830..1150 ns is a 1 (16 ns per count)
@pytest.mark.parametrize('high,bad', [(11, 1), (12, 0), (30, 0), (31, 1), (51, 1), (52, 0), (71, 0), (72, 1), (200, 1)])
def test_class_boundaries(binary, high, bad):
    r = decode(binary, [high, MARK])
    assert r['bad'] == str(bad)


def test_bit_value_of_out_of_range_pulse_follows_the_threshold(binary):
    ws = []
    for i in range(8):
        ws += [40, MARK if i == 7 else 30]
    assert decode(binary, ws)['rx'] == '00' and decode(binary, ws)['bad'] == '8'
    ws = []
    for i in range(8):
        ws += [42, MARK if i == 7 else 30]            # 672 ns (> 655 ns)
    assert decode(binary, ws)['rx'] == 'ff' and decode(binary, ws)['bad'] == '8'


def test_missing_marker_means_frame_not_ended(binary):
    r = decode(binary, words_for(b'\xa5', end=False))
    assert r['ended'] == '0' and r['bits'] == '8' and r['rx'] == 'a5'


def test_partial_byte_is_reported(binary):
    ws = words_for(b'\xff')[:2 * 5]
    ws[-1] = MARK
    r = decode(binary, ws)
    assert r['bits'] == '5' and r['partial'] == '1' and r['bytes'] == '0' and r['ended'] == '1'


def test_decoding_stops_at_first_marker_even_if_more_words_follow(binary):
    ws = words_for(b'\x12') + words_for(b'\x34')
    r = decode(binary, ws)
    assert r['rx'] == '12' and r['bits'] == '8'


def test_empty_and_odd_word_counts(binary):
    assert decode(binary, [])['bits'] == '0'
    assert decode(binary, [ZERO])['bits'] == '0'                       # unpaired word is ignored


def test_scales_with_ns_per_count(binary):
    r = decode(binary, words_for(b'\x80', high0=10, high1=31), npc=32)  # 320 ns / 992 ns
    assert r['rx'] == '80' and r['bad'] == '0'


def test_tail_bits_are_reported_left_aligned(binary):
    ws = words_for(b'\xa5', end=False) + [ONE, MARK]      # one extra 1-bit after a complete byte
    r = decode(binary, ws)
    assert r['bits'] == '9' and r['bytes'] == '1' and r['tail_bits'] == '1' and r['tail'] == '80' and r['rx'] == 'a5'
    ws = words_for(b'\xa5', end=False) + [ZERO, MARK]
    r = decode(binary, ws)
    assert r['tail'] == '00' and r['tail_bits'] == '1'


def test_last_high_width_is_reported(binary):
    assert decode(binary, words_for(b'\x01') [:-2] + [100, MARK])['last'] == str(100 * NS)


def test_trailing_idle_high_pulse_is_not_a_bit(binary):
    ws = words_for(b'\xa5', end=False) + [100000, MARK]               # 1.6 ms High before the reset gap
    r = decode(binary, ws)
    assert r['bits'] == '8' and r['rx'] == 'a5' and r['idle'] == '1' and r['ended'] == '1' and r['bad'] == '0'
    r = decode(binary, words_for(b'\xa5', end=False) + [0xFFFFFFFE, MARK])   # saturated count
    assert r['idle'] == '1' and r['bits'] == '8'


def test_wide_pulse_inside_a_frame_is_still_a_bad_pulse(binary):
    r = decode(binary, [ZERO, 30, 100000, 30, ONE, MARK])
    assert r['idle'] == '0' and r['bad'] == '1' and r['bits'] == '3'


def test_boundary_of_the_idle_high_limit(binary):
    assert decode(binary, [6250, MARK])['idle'] == '0'                 # exactly 100 us is still a pulse
    assert decode(binary, [6251, MARK])['idle'] == '1'


def test_high_and_low_ranges_per_bit_value(binary):
    """h0/h1: High widths of all 0/1 bits (in-range or not, split by the threshold); l0/l1: the Low after each bit
    except the last one, measured as GAP_LIMIT (3125) minus the remaining Low counter."""
    ws = []
    for h, low_left in ((19, 3125 - 53), (50, 3125 - 28), (21, 3125 - 52), (45, 3125 - 25)):   # 0 1 0 1 at 16 ns
        ws += [h, low_left]
    ws += [19, MARK]
    r = decode(binary, ws)
    assert r['h0'] == f'{19 * NS}-{21 * NS}' and r['h1'] == f'{45 * NS}-{50 * NS}'
    assert r['l0'] == f'{52 * NS}-{53 * NS}' and r['l1'] == f'{25 * NS}-{28 * NS}'
    assert r['bad'] == '2'                      # 720 and 800 ns: 1 by threshold, below the 830 ns window


def test_ranges_are_zero_without_such_bits(binary):
    r = decode(binary, [19, MARK])
    assert r['h0'] == f'{19 * NS}-{19 * NS}' and r['h1'] == '0-0' and r['l0'] == '0-0' and r['l1'] == '0-0'
