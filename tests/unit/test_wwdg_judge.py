"""WWDG sample judgement (no hardware): tolerances match the three -DWWDG_MODE builds and wrong modes are rejected."""
from pathlib import Path

import pytest

from ch32hil import wwdg

ROOT = Path(__file__).resolve().parents[2]
# Captures observed on CH32V002 (okf/log/2026-11-09-0013-add-wwdg-sample.md); each starts with a debugger reset.
MODE0 = b"cause=other\n" + b"." * 20
MODE1 = b"cause=other\n.cause=WWDG\n.cause=W"
MODE2 = b"cause=other\n" + b"." * 9 + b"cause=WWDG\n"
CAPTURES = {0: MODE0, 1: MODE1, 2: MODE2}


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_each_observed_capture_passes_its_own_mode(mode):
    wwdg.judge_reset_capture(mode, CAPTURES[mode])


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_each_capture_fails_the_other_modes(mode):
    for other, rx in CAPTURES.items():
        if other != mode:
            with pytest.raises(AssertionError):
                wwdg.judge_reset_capture(mode, rx)


def test_parse_accepts_a_start_truncated_by_the_32_byte_limit():
    p = wwdg.parse(b"cause=other\n" + b"." * 10 + b"cause=WWDG")      # 10 dots: the newline of the second start is cut
    assert p["segments"] == [("other", 10), ("WWDG", 0)] and p["junk"] == []
    p = wwdg.parse(b"cause=other\n.cause=WWDG\n.cause=W")
    assert p["segments"] == [("other", 1), ("WWDG", 1)] and p["junk"] == []


def test_mode2_dot_count_tolerance_brackets_the_nominal_nine():
    ok = lambda n: wwdg.judge_reset_capture(2, b"cause=other\n" + b"." * n + b"cause=WWDG")
    for n in (8, 9, 10):
        ok(n)
    for n in (0, 1, 7, 11, 20):
        with pytest.raises(AssertionError):
            ok(n)


def test_mode1_dot_count_is_one_or_two_and_the_reset_cause_must_be_wwdg():
    ok = lambda rx: wwdg.judge_reset_capture(1, rx)
    ok(b"cause=other\n.cause=WWDG\n")
    ok(b"cause=other\n..cause=WWDG\n")
    for rx in (b"cause=other\ncause=WWDG\n", b"cause=other\n...cause=WWDG\n", b"cause=other\n.cause=IWDG\n",
               b"cause=other\n.cause=other\n"):
        with pytest.raises(AssertionError):
            ok(rx)


def test_mode0_needs_a_single_start_and_no_reset():
    with pytest.raises(AssertionError):
        wwdg.judge_reset_capture(0, b"cause=other\n.....cause=WWDG\n")      # restarted
    with pytest.raises(AssertionError):
        wwdg.judge_reset_capture(0, b"cause=other\n.....")                  # too few dots to say it survived


def test_a_capture_must_start_at_the_debugger_reset_and_have_no_garbage():
    for rx in (b"....cause=other\n" + b"." * 20, b"cause=WWDG\n" + b"." * 20, b"cause=other\nxx" + b"." * 20, b""):
        with pytest.raises(AssertionError):
            wwdg.judge_reset_capture(0, rx)


def test_running_capture_is_dots_only():
    assert wwdg.judge_running(b"." * 32) == {"dots": 32}
    for rx in (b"", b"...", b"." * 20 + b"cause=WWDG\n", b"cause=other\n" + b"." * 20):
        with pytest.raises(AssertionError):
            wwdg.judge_running(rx)


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError):
        wwdg.judge_reset_capture(3, MODE0)


def test_nominal_numbers_follow_from_the_sample_constants():
    """The dot counts come from the sample's window/prescaler, not from magic numbers in the judgement."""
    counts_to_reset = 0x7F - 0x3F                       # 64 counts from 0x7F until the counter falls below 0x40
    t_count_us = 4096 * 8 / 48                           # HCLK 48 MHz, WDGTB prescaler /8
    reset_ms = counts_to_reset * t_count_us / 1000
    assert 43 < reset_ms < 44
    dots = int(reset_ms // 5) + 1                        # a dot at 0, 5, ... before the reset
    assert wwdg.MODE2_DOTS[0] <= dots <= wwdg.MODE2_DOTS[1] and dots == 9
    window_ms = (0x7F - 0x5F) * t_count_us / 1000        # a feed before ~22 ms is "too early"
    assert 5 < window_ms and 5 < 22 < window_ms + 1      # the 5 ms feed of mode 1 is far inside the closed window


@pytest.mark.parametrize("main", ["samples_ch32v002_wch/wwdg/main.c", "samples_ch32v006_wch/wwdg/main.c",
                                  "samples_ch32v00x_ch32fun/wwdg/main.c"])
def test_samples_use_the_constants_the_judgement_assumes(main):
    src = (ROOT / main).read_text()
    for text in ("#define WWDG_CNT 0x7F", "#define WWDG_WINDOW 0x5F", "#define WWDG_WAIT_MS 1500", "Delay_Ms(5)",
                 "WWDG_MODE"):
        assert text in src, (main, text)
    assert "cause=" in src and 'wait\\r\\n' not in src      # the start text stays short: two starts fit in 32 bytes


def test_wch_002_and_006_wwdg_sources_are_identical():
    a = (ROOT / "samples_ch32v002_wch/wwdg/main.c").read_text()
    b = (ROOT / "samples_ch32v006_wch/wwdg/main.c").read_text()
    assert a == b
    assert (ROOT / "samples_ch32v002_wch/wwdg/Makefile").read_text() == (ROOT / "samples_ch32v006_wch/wwdg/Makefile").read_text()
