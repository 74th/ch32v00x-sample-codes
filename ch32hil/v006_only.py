"""Judgements for the CH32V006-only WCH SDK samples (usart2, opa, tim3, tkey): pure functions, unit-tested.

Voltages are not calibrated: OPA is judged by the ratio of two ADC readings, TIM3 by a period, TKEY is only recorded."""
from __future__ import annotations

import re
import statistics

HCLK_HZ = 48_000_000
TIM3_RELOAD = 47_999          # samples_ch32v006_wch/tim3/main.c: ATRLR
USART2_TEXT = b"usart2 0123456789\r\n"
OPA_LINE = re.compile(rb"opa gain=(\d+) in=(\d+) out=(\d+)\r\n")
TKEY_LINE = re.compile(rb"tkey pd4=(\d+) pa2=(\d+)\r\n")
ADC_FULL_SCALE = 4095         # 12 bit


def tim3_expected_hz(reload=TIM3_RELOAD, hclk=HCLK_HZ):
    """TIM3 has no prescaler: one DMA request (one PC0 edge) every (reload + 1) HCLK counts; one PC0 period = 2 edges."""
    return hclk / (reload + 1) / 2


def parse_opa(data: bytes):
    """[(gain, in_raw, out_raw)] of every complete `opa ...` line in the captured text."""
    return [tuple(int(x) for x in m.groups()) for m in OPA_LINE.finditer(data)]


def judge_opa(rows, gain, tol_pct=15.0, min_in=150, max_out_fraction=0.9, min_rows=3, label="opa"):
    """The median of out/in over the readings that carry a usable input must be gain * (1 +- tol_pct %).

    Readings with in < min_in (input at the noise/offset floor: the RC is discharged) or out above
    `max_out_fraction` of full scale (output near the rail: saturated) are counted separately, not judged."""
    usable = [(i, o) for g, i, o in rows if g == gain and i >= min_in and o <= max_out_fraction * ADC_FULL_SCALE]
    wrong_gain = [g for g, _, _ in rows if g != gain]
    if wrong_gain:
        raise AssertionError(f"{label}: log shows gain {sorted(set(wrong_gain))}, expected {gain}")
    if len(usable) < min_rows:
        raise AssertionError(f"{label}: only {len(usable)} usable readings (in >= {min_in}, out <= {max_out_fraction:.0%} FS) "
                             f"of {len(rows)}: {rows[:6]}")
    ratios = [o / i for i, o in usable]
    ratio = statistics.median(ratios)
    low, high = gain * (1 - tol_pct / 100), gain * (1 + tol_pct / 100)
    record = {"label": label, "gain": gain, "ratio_median": round(ratio, 3), "window": [round(low, 3), round(high, 3)],
              "usable": len(usable), "readings": len(rows), "in_median": int(statistics.median(i for i, _ in usable)),
              "out_median": int(statistics.median(o for _, o in usable)), "ratio_min": round(min(ratios), 3),
              "ratio_max": round(max(ratios), 3)}
    if not low <= ratio <= high:
        raise AssertionError(f"{label}: out/in = {ratio:.3f} outside {low:.3f}..{high:.3f} (gain {gain}): {record}")
    return record


def saturation_record(rows, gain, threshold_fraction=0.9):
    """Readings whose output reached `threshold_fraction` of full scale (recorded for a high input, not judged)."""
    saturated = [o for g, _, o in rows if g == gain and o >= threshold_fraction * ADC_FULL_SCALE]
    return {"gain": gain, "readings": len(rows), "saturated": len(saturated), "max_out": max((o for _, _, o in rows), default=None)}


def parse_tkey(data: bytes):
    return [tuple(int(x) for x in m.groups()) for m in TKEY_LINE.finditer(data)]


def tkey_record(rows, min_rows=2):
    """Reference observation of the two TKEY channels (no pass/fail on the values; only an empty log fails)."""
    if len(rows) < min_rows:
        raise AssertionError(f"tkey: only {len(rows)} readings parsed")
    pd4 = [a for a, _ in rows]
    pa2 = [b for _, b in rows]
    return {"readings": len(rows), "pd4_median": int(statistics.median(pd4)), "pa2_median": int(statistics.median(pa2)),
            "pd4_range": [min(pd4), max(pd4)], "pa2_range": [min(pa2), max(pa2)],
            "pa2_minus_pd4": int(statistics.median(pa2) - statistics.median(pd4))}


def judge_usart2(capture, min_repeats=2, label="usart2"):
    """`capture` is a ch32hil.pico.Capture (UART, 115200 8N1 on GP14). The fixed text must be received at least
    `min_repeats` times, complete and without data loss."""
    if capture.kind != "UART":
        raise AssertionError(f"{label}: not a UART capture")
    if capture.overflow or capture.frame_errors:
        raise AssertionError(f"{label}: capture lost data (overflow={capture.overflow}, frame_errors={capture.frame_errors})")
    data = bytes(capture.items)
    count = data.count(USART2_TEXT)
    if count < min_repeats:
        raise AssertionError(f"{label}: text {USART2_TEXT!r} seen {count} times (need {min_repeats}) in {data!r}")
    return {"label": label, "received": capture.received, "repeats": count}
