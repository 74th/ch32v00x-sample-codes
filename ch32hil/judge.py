"""Host-side judgements for the Pico edge-time measurements and the DUT log text (pure functions, unit-tested).

All times are picoseconds on the Pico's clock, which is not calibrated; tolerances therefore include the DUT's HSI
tolerance (-2.0..+2.0 %, CH32V006 DS, -10..70 degC) and the Pico crystal error, which is not measured here.
"""
from __future__ import annotations

import statistics

from .pico import edge_widths

# SCK / PWM: expected +-3 % (HSI +-2 % plus margin). I2C SCL: the real frequency is below the configured one (rise time
# of the 4.7 kOhm pull-ups with the line capacitance, clock stretching), so the frequency window is -25 %..+3 %; the
# first measurements decide whether it is kept (see the log of the change that introduced it).
PERIOD_TOL_PCT = (3.0, 3.0)
I2C_SCL_TOL_PCT = (25.0, 3.0)


def edge_summary(words, res_ps, k_period=9, k_high=4, min_periods=8, burst_factor=3.0):
    """Reduce raw EDGE capture words to period statistics.

    Bursty clocks (SPI SCK, I2C SCL) contain long gaps between bytes/transactions: those periods are far above the
    clock period. `median` is the clock period; `in_burst` counts the periods within `burst_factor` x median."""
    pairs = edge_widths(words, res_ps, k_period, k_high)
    if len(pairs) < min_periods:
        raise AssertionError(f"only {len(pairs)} periods captured (need {min_periods}); words={len(words)}")
    periods = [p for p, _ in pairs]
    highs = [h for _, h in pairs]
    median = statistics.median(periods)
    burst = [p for p in periods if p <= burst_factor * median]
    return {"periods": len(periods), "in_burst": len(burst), "median_ps": int(median), "min_ps": min(periods),
            "max_burst_ps": max(burst), "high_median_ps": int(statistics.median(highs)),
            "frequency_hz": round(1e12 / median, 1), "res_ps": res_ps}


def judge_period(summary, expected_hz, tol_pct=PERIOD_TOL_PCT, label="clock"):
    """The median frequency must lie in [expected * (1 - minus), expected * (1 + plus)]. Returns a record."""
    freq = summary["frequency_hz"]
    low, high = expected_hz * (1 - tol_pct[0] / 100), expected_hz * (1 + tol_pct[1] / 100)
    record = {"label": label, "expected_hz": expected_hz, "measured_hz": freq, "window_hz": [round(low, 1), round(high, 1)],
              "deviation_pct": round((freq / expected_hz - 1) * 100, 2), "median_period_ns": summary["median_ps"] / 1000,
              "periods": summary["periods"], "in_burst": summary["in_burst"]}
    if not low <= freq <= high:
        raise AssertionError(f"{label} {freq} Hz outside {low:.0f}..{high:.0f} Hz (expected {expected_hz} Hz): {record}")
    return record


def judge_duty(high_ps, period_ps, expected_ppm, tol_ppm, label="pwm"):
    duty = round(high_ps * 1e6 / period_ps)
    record = {"label": label, "duty_ppm": duty, "expected_ppm": expected_ppm, "tolerance_ppm": tol_ppm}
    if abs(duty - expected_ppm) > tol_ppm:
        raise AssertionError(f"{label} duty {duty} ppm outside {expected_ppm}+-{tol_ppm}: {record}")
    return record


# ---- expected DUT log text, computed from the simulated peripheral values ----

def sht31_values(t_raw, h_raw):
    """The book's formulas (integer): temperature = (t * 175 >> 16) - 45, humidity = h * 100 >> 16."""
    return ((t_raw * 175) >> 16) - 45, (h_raw * 100) >> 16


def arduino_i2c_master_text(t_raw, h_raw):
    t, h = sht31_values(t_raw, h_raw)
    return f"temperature: {t} humidity: {h}\r\n".encode()


def adt7310_values(raw):
    raw13 = raw >> 3
    raw_int = raw13 - 0x2000 if raw13 & 0x1000 else raw13
    return raw_int, raw_int >> 4, (raw_int & 0x0F) * 625


def arduino_spi_master_text(raw):
    raw_int, whole, frac = adt7310_values(raw)
    return f"raw: {raw:04X}\r\nraw_int:{raw_int}\r\ntemp:{whole:3d}.{frac:04d}\r\n".encode()


def arduino_test_master_read_text(reply_hex):
    data = bytes.fromhex(reply_hex)
    return (f"receive available: {len(data)}\r\nread :" + " ".join(f"{b:X}" for b in data) + "\r\n").encode()


def wch_i2c_slave_reg_lines(reg20=(0x00, 0x10, 0x20, 0x30), reg10=(0xAA, 0xBB, 0xCC, 0xDD)):
    """Register dumps printed by the book's i2c_slave after a read of 0x20.. and after the write 10 aa bb cc dd."""
    return (("reg[0x20]: " + " ".join(f"{b:x}" for b in reg20) + "\r\n").encode(),
            ("reg[0x10]: " + " ".join(f"{b:x}" for b in reg10) + "\r\n").encode())


def judge_log(capture, expected, label="log"):
    """`capture` is a ch32hil.pico.Capture (UART). Fails when data was lost or bytes are missing; never succeeds on an
    empty capture. `expected` is a bytes or a list of bytes that must each appear in the captured text."""
    if capture.kind != "UART":
        raise AssertionError(f"{label}: not a UART capture")
    if capture.overflow or capture.frame_errors:
        raise AssertionError(f"{label}: capture lost data (overflow={capture.overflow}, frame_errors={capture.frame_errors})")
    if not capture.received:
        raise AssertionError(f"{label}: nothing captured (the log was not received)")
    wanted = [expected] if isinstance(expected, (bytes, bytearray)) else list(expected)
    missing = [w for w in wanted if w not in capture.items]
    if missing:
        raise AssertionError(f"{label}: expected {missing} not in captured {bytes(capture.items)!r}")
    return {"label": label, "received": capture.received, "text": bytes(capture.items).decode("ascii", "replace")}


def judge_pwm_survey(rows, timeouts, expected_hz, tol_pct=PERIOD_TOL_PCT, duty_expected_ppm=None, duty_grid=None,
                     duty_tol_ppm=20_000, min_ok=8, min_duty_ok_fraction=0.8, label="pwm"):
    """Judge repeated EDGE_MEASURE results (dicts, picoseconds) of a PWM output.

    Every measurement's mean period must lie within `tol_pct` of 1/expected_hz (a wrong period is never excused), and
    its max-min spread must stay within the same window. The duty is judged against a constant (`duty_expected_ppm`) or
    the nearest k/`duty_grid` step, for at least `min_duty_ok_fraction` of the measurements: a ramping duty can change
    inside the short measurement window (the measurement mixes two steps), which is recorded, not hidden."""
    if len(rows) < min_ok:
        raise AssertionError(f"{label}: only {len(rows)} measurements ({timeouts} without edges), need {min_ok}")
    expected_ps = 1e12 / expected_hz
    low, high = expected_ps * (1 - tol_pct[1] / 100), expected_ps * (1 + tol_pct[0] / 100)
    bad_period = [r for r in rows if not low <= r["period_ps_avg"] <= high
                  or r["period_ps_max"] > high or r["period_ps_min"] < low]
    if bad_period:
        raise AssertionError(f"{label}: period outside {low / 1000:.1f}..{high / 1000:.1f} ns in {len(bad_period)} of {len(rows)}: {bad_period[:3]}")
    duties = [r["duty_ppm"] for r in rows]
    duty_ok = []
    for d in duties:
        if duty_expected_ppm is not None:
            target = duty_expected_ppm
        elif duty_grid:
            step = 1_000_000 / duty_grid
            target = round(d / step) * step
        else:
            continue
        duty_ok.append(abs(d - target) <= duty_tol_ppm)
    if duty_ok and sum(duty_ok) / len(duty_ok) < min_duty_ok_fraction:
        raise AssertionError(f"{label}: duty off target in {len(duty_ok) - sum(duty_ok)} of {len(duty_ok)} (tolerance {duty_tol_ppm} ppm): {duties}")
    avg = sum(r["period_ps_avg"] for r in rows) / len(rows)
    return {"label": label, "measurements": len(rows), "without_edges": timeouts, "expected_hz": expected_hz,
            "mean_period_ns": round(avg / 1000, 1), "mean_frequency_hz": round(1e12 / avg, 1),
            "deviation_pct": round((1e12 / avg / expected_hz - 1) * 100, 2), "duty_ppm": duties,
            "duty_ok": f"{sum(duty_ok)}/{len(duty_ok)}" if duty_ok else None}
