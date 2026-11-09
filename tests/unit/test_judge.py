import pytest

from ch32hil import judge
from ch32hil.pico import Capture


def words_for(period_cycles, high_cycles, pairs, k_period=9, k_high=4):
    """Loop counts the PIO would report for a clock of the given High/period (PIO cycles)."""
    nh = (high_cycles - k_high) // 2
    nl = (period_cycles - k_period) // 2 - nh
    return [nh, nl] * pairs


def test_edge_summary_median_ignores_gaps_between_bursts():
    # 750 kHz: period 167 cycles (1336 ns); two 8-clock bursts separated by a ~100 us gap
    burst = words_for(167, 83, 8)
    gap = [41, 6000]
    s = judge.edge_summary([5, 5] + burst + gap + burst, 16000)
    assert s["median_ps"] == 1_336_000 and s["frequency_hz"] == pytest.approx(748_503, abs=2)
    assert s["periods"] == 17 and s["in_burst"] == 16      # 8 + gap + 8; the gap period is out of the burst
    assert s["max_burst_ps"] == 1_336_000


def test_edge_summary_needs_enough_periods():
    with pytest.raises(AssertionError, match="only 3 periods"):
        judge.edge_summary([1, 1] + words_for(167, 83, 3), 16000)


def test_judge_period_window_and_record():
    s = {"frequency_hz": 748_503.0, "median_ps": 1_336_000, "periods": 16, "in_burst": 15}
    rec = judge.judge_period(s, 750_000, label="sck")
    assert rec["deviation_pct"] == pytest.approx(-0.2, abs=0.01) and rec["window_hz"] == [727500.0, 772500.0]
    for hz in (727_000.0, 773_000.0):
        with pytest.raises(AssertionError, match="sck"):
            judge.judge_period({**s, "frequency_hz": hz}, 750_000, label="sck")
    # I2C window is asymmetric: -25 % .. +3 %
    judge.judge_period({**s, "frequency_hz": 76_000.0}, 100_000, judge.I2C_SCL_TOL_PCT)
    with pytest.raises(AssertionError):
        judge.judge_period({**s, "frequency_hz": 74_000.0}, 100_000, judge.I2C_SCL_TOL_PCT)
    with pytest.raises(AssertionError):
        judge.judge_period({**s, "frequency_hz": 104_000.0}, 100_000, judge.I2C_SCL_TOL_PCT)


def test_judge_duty():
    assert judge.judge_duty(250_000, 1_000_000, 250_000, 5_000)["duty_ppm"] == 250_000
    with pytest.raises(AssertionError):
        judge.judge_duty(300_000, 1_000_000, 250_000, 5_000)


def test_expected_texts_from_simulated_values():
    assert judge.sht31_values(0x6666, 0x8000) == (24, 50)
    assert judge.arduino_i2c_master_text(0x6666, 0x8000) == b"temperature: 24 humidity: 50\r\n"
    assert judge.adt7310_values(0x0C80) == (400, 25, 0)
    assert judge.arduino_spi_master_text(0x0C80) == b"raw: 0C80\r\nraw_int:400\r\ntemp: 25.0000\r\n"
    # -25.0 degC (0xF380): raw13 = 0x1E70, raw_int = -400; printf %3d.%04d of (-400 >> 4, (-400 & 15) * 625)
    assert judge.adt7310_values(0xF380) == (-400, -25, 0)
    assert judge.arduino_test_master_read_text("a1b2c3d4") == b"receive available: 4\r\nread :A1 B2 C3 D4\r\n"
    assert judge.wch_i2c_slave_reg_lines() == (b"reg[0x20]: 0 10 20 30\r\n", b"reg[0x10]: aa bb cc dd\r\n")


def cap(text, **kw):
    f = dict(kind="UART", items=text, received=len(text), capacity=4096, full=False, overflow=False, frame_errors=False)
    f.update(kw)
    return Capture(**f)


def test_judge_log_passes_and_fails_closed():
    rec = judge.judge_log(cap(b"loop 3\r\ntemperature: 24 humidity: 50\r\n"), b"temperature: 24 humidity: 50\r\n")
    assert rec["received"] == len(b"loop 3\r\ntemperature: 24 humidity: 50\r\n")
    with pytest.raises(AssertionError, match="nothing captured"):
        judge.judge_log(cap(b""), b"x")
    with pytest.raises(AssertionError, match="lost data"):
        judge.judge_log(cap(b"abc", overflow=True), b"abc")
    with pytest.raises(AssertionError, match="lost data"):
        judge.judge_log(cap(b"abc", frame_errors=True), b"abc")
    with pytest.raises(AssertionError, match="not in captured"):
        judge.judge_log(cap(b"temperature: 25 humidity: 50\r\n"), b"temperature: 24 humidity: 50\r\n")
    with pytest.raises(AssertionError, match="not a UART"):
        judge.judge_log(Capture("EDGE", [1], 1, 4096, False, False), b"x")
    judge.judge_log(cap(b"aXb"), [b"a", b"b"])
    with pytest.raises(AssertionError):
        judge.judge_log(cap(b"aXb"), [b"a", b"c"])


def row(period_ps, duty_ppm, spread=16_000):
    return {"period_ps_avg": period_ps, "period_ps_min": period_ps - spread // 2, "period_ps_max": period_ps + spread // 2,
            "duty_ppm": duty_ppm}


def test_judge_pwm_survey_period_duty_and_limits():
    rows = [row(1_000_000, 250_000 + d) for d in range(0, 8000, 1000)] + [row(1_001_000, 250_000)]
    rec = judge.judge_pwm_survey(rows, 2, 1_000_000, duty_expected_ppm=250_000, duty_tol_ppm=10_000)
    assert rec["measurements"] == 9 and rec["without_edges"] == 2 and rec["duty_ok"] == "9/9"
    with pytest.raises(AssertionError, match="only 3 measurements"):
        judge.judge_pwm_survey(rows[:3], 0, 1_000_000)
    with pytest.raises(AssertionError, match="period outside"):          # one wrong period fails the whole run
        judge.judge_pwm_survey(rows + [row(1_050_000, 250_000)], 0, 1_000_000)
    with pytest.raises(AssertionError, match="period outside"):          # spread beyond the window
        judge.judge_pwm_survey(rows + [row(1_000_000, 250_000, spread=100_000)], 0, 1_000_000)
    with pytest.raises(AssertionError, match="duty off target"):
        judge.judge_pwm_survey([row(1_000_000, 400_000)] * 9, 0, 1_000_000, duty_expected_ppm=250_000, duty_tol_ppm=10_000)


def test_judge_pwm_survey_duty_grid_allows_a_few_mixed_steps():
    grid = [row(1_000_000, round(k * 1e6 / 32) + 2000) for k in range(1, 10)]
    mixed = [row(1_000_000, round(1e6 / 64) + round(5e6 / 32) // 1)]     # off-grid reading from a window spanning two steps
    rec = judge.judge_pwm_survey(grid + mixed[:0], 0, 1_000_000, duty_grid=32, duty_tol_ppm=15_000)
    assert rec["duty_ok"] == "9/9"
    rec = judge.judge_pwm_survey(grid + [row(1_000_000, 15_625)], 0, 1_000_000, duty_grid=32, duty_tol_ppm=5_000)
    assert rec["duty_ok"] in ("9/10", "10/10")
    with pytest.raises(AssertionError, match="duty off target"):
        judge.judge_pwm_survey([row(1_000_000, round(k * 1e6 / 32) + 15_625) for k in range(1, 10)], 0, 1_000_000,
                               duty_grid=32, duty_tol_ppm=3_000)
