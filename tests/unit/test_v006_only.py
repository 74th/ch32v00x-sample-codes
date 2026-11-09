import pytest

from ch32hil import v006_only as v
from ch32hil.pico import Capture


def opa_text(rows, gain=4):
    return b"init opa gain=4\r\n" + b"".join(f"opa gain={g} in={i} out={o}\r\n".encode() for g, i, o in rows)


def test_tim3_expected_frequency():
    assert v.tim3_expected_hz() == pytest.approx(500.0)
    assert v.tim3_expected_hz(reload=23_999) == pytest.approx(1000.0)     # half the reload: twice the frequency


def test_parse_opa_ignores_init_line_and_partial_lines():
    data = opa_text([(4, 400, 1600), (4, 410, 1640)]) + b"opa gain=4 in=41"
    assert v.parse_opa(data) == [(4, 400, 1600), (4, 410, 1640)]


def test_judge_opa_median_ratio_window():
    rows = [(4, 400, 1600), (4, 405, 1650), (4, 398, 1590), (4, 0, 3)]       # the last reading is the discharged floor
    rec = v.judge_opa(rows, 4)
    assert rec["usable"] == 3 and rec["ratio_median"] == pytest.approx(4.0, abs=0.1) and rec["readings"] == 4
    with pytest.raises(AssertionError, match="outside"):                     # 3x instead of 4x
        v.judge_opa([(4, 400, 1200)] * 4, 4)
    v.judge_opa([(4, 400, 1200)] * 4, 4, tol_pct=30)                         # the window is a parameter
    with pytest.raises(AssertionError, match="usable"):                      # saturated output is not judged
        v.judge_opa([(4, 1000, 4000)] * 5, 4)
    with pytest.raises(AssertionError, match="usable"):
        v.judge_opa([(4, 20, 80)] * 5, 4)
    with pytest.raises(AssertionError, match="gain"):                        # the log must show the built gain
        v.judge_opa([(8, 400, 3200)] * 4, 4)


def test_saturation_record():
    rows = [(4, 1000, 4090), (4, 900, 3700), (4, 400, 1600)]
    assert v.saturation_record(rows, 4) == {"gain": 4, "readings": 3, "saturated": 2, "max_out": 4090}


def test_tkey_record_never_judges_values_but_needs_data():
    rows = v.parse_tkey(b"init tkey\r\ntkey pd4=120 pa2=980\r\ntkey pd4=124 pa2=990\r\ntkey pd4=9")
    assert rows == [(120, 980), (124, 990)]
    rec = v.tkey_record(rows)
    assert rec["pa2_minus_pd4"] == 863 and rec["pd4_range"] == [120, 124]
    with pytest.raises(AssertionError, match="only 1"):
        v.tkey_record(rows[:1])
    assert v.tkey_record([(5, 5), (5, 5)])["pa2_minus_pd4"] == 0           # equal values are recorded, not failed


def cap(data, **kw):
    f = dict(kind="UART", items=data, received=len(data), capacity=4096, full=False, overflow=False, frame_errors=False)
    f.update(kw)
    return Capture(**f)


def test_judge_usart2_text_count_and_data_loss():
    ok = v.judge_usart2(cap(b"xx" + v.USART2_TEXT * 3))
    assert ok["repeats"] == 3
    with pytest.raises(AssertionError, match="seen 1 times"):
        v.judge_usart2(cap(v.USART2_TEXT + b"usart2 01234"))
    with pytest.raises(AssertionError, match="seen 0 times"):
        v.judge_usart2(cap(b""))
    with pytest.raises(AssertionError, match="lost data"):
        v.judge_usart2(cap(v.USART2_TEXT * 3, overflow=True))
    with pytest.raises(AssertionError, match="lost data"):
        v.judge_usart2(cap(v.USART2_TEXT * 3, frame_errors=True))
    with pytest.raises(AssertionError, match="not a UART"):
        v.judge_usart2(Capture("EDGE", [1, 2], 2, 4096, False, False))
