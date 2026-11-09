from types import SimpleNamespace as NS
import pytest
from ch32hil.pico import (PicoClient, PicoError, PicoProtocolError, PicoTimeout, discover)


class Link:
    def __init__(self, replies):
        self.replies, self.sent = list(replies), []
    def write(self, b): self.sent.append(b)
    def readline(self): return self.replies.pop(0) if self.replies else b""


class Clock:
    def __init__(self): self.t = 0.0
    def __call__(self): self.t += 0.1; return self.t


def pico(dev): return NS(device=dev, vid=0x2E8A, pid=0x000A)


def test_discover_zero_then_one():
    seq = iter([[], [], [pico("/dev/a")]])
    assert discover(lambda: next(seq), sleep=lambda s: None) == "/dev/a"


def test_discover_zero_times_out():
    c = Clock()
    with pytest.raises(PicoTimeout):
        discover(lambda: [], timeout=1, sleep=lambda s: None, clock=c)


def test_discover_multiple_refuses():
    with pytest.raises(PicoError, match="2 Picos"):
        discover(lambda: [pico("a"), pico("b")])


def test_discover_explicit_port():
    assert discover(lambda: [pico("a"), pico("b")], port="/dev/x") == "/dev/x"


def test_negotiate_and_missing_cap():
    link = Link([b"1 OK proto=2 cmds=CAPS,RESET_SAFE,GPIO_SAMPLE\n"])
    assert PicoClient(link, clock=Clock()).negotiate(["GPIO_SAMPLE"])["proto"] == "2"
    link = Link([b"1 OK proto=2 cmds=CAPS\n"])
    with pytest.raises(PicoError, match="GPIO_SAMPLE"):
        PicoClient(link, clock=Clock()).negotiate(["GPIO_SAMPLE"])


def test_restart_stale_response_ignored():
    link = Link([b"9 OK stale\n", b"1 OK fine\n"])
    assert PicoClient(link, clock=Clock()).request("CAPS").fields == ["fine"]


def test_invalid_response():
    with pytest.raises(PicoProtocolError):
        PicoClient(Link([b"garbage\n"]), clock=Clock()).request("CAPS")
    with pytest.raises(PicoProtocolError):
        PicoClient(Link([b"1 MAYBE\n"]), clock=Clock()).request("CAPS")


def test_timeout():
    with pytest.raises(PicoTimeout):
        PicoClient(Link([]), timeout=1, clock=Clock()).request("CAPS")


def test_err_response_is_not_success():
    r = PicoClient(Link([b"1 ERR UNSUPPORTED nope\n"]), clock=Clock()).request("X")
    assert not r.ok
    with pytest.raises(PicoError):
        PicoClient(Link([b"1 ERR BUSY x\n"]), clock=Clock()).reset_safe()


def test_legacy_v1_samples_and_constraints():
    samples = '01' * 150
    link = Link([f'PICO_GPIO_V1 10000 {samples}\n'.encode()])
    client = PicoClient(link, clock=Clock())
    assert client.sample_gpio(0, legacy=True) == samples
    assert link.sent == [b's']
    with pytest.raises(PicoError, match='GP0'):
        client.sample_gpio(5, legacy=True)


def test_legacy_timeout_and_bad_frame():
    with pytest.raises(PicoTimeout):
        PicoClient(Link([]), timeout=1, clock=Clock()).sample_gpio(0, legacy=True)
    with pytest.raises(PicoProtocolError):
        PicoClient(Link([b'PICO_GPIO_V1 10000 01\n']), clock=Clock()).sample_gpio(0, legacy=True)


def test_v2_sample_validates_settings_and_data():
    link = Link([b'1 OK pin=5 count=3 interval_us=1000 samples=010\n'])
    assert PicoClient(link, clock=Clock()).sample_gpio(5, 3, 1000) == '010'
    link = Link([b'1 OK pin=4 count=3 interval_us=1000 samples=010\n'])
    with pytest.raises(PicoProtocolError, match='settings'):
        PicoClient(link, clock=Clock()).sample_gpio(5, 3, 1000)


def test_wait_ready_retries_enumeration_and_handshake():
    from ch32hil.pico import wait_ready
    class Opened(Link):
        def __enter__(self): return self
        def __exit__(self, *args): pass
    clock = Clock()
    ports = iter([[], [pico('a')]])
    port, caps = wait_ready(lambda: next(ports), lambda p, t: Opened([b'1 OK proto=2 cmds=CAPS\n']),
                            timeout=5, clock=clock, sleep=lambda _: None)
    assert port == 'a' and caps['proto'] == '2'


def test_wait_ready_rejects_ambiguous_devices_and_times_out():
    from ch32hil.pico import wait_ready
    with pytest.raises(PicoError, match='2 Picos'):
        wait_ready(lambda: [pico('a'), pico('b')], lambda *args: None, timeout=2, clock=Clock(), sleep=lambda _: None)
    with pytest.raises(PicoTimeout):
        wait_ready(lambda: [], lambda *args: None, timeout=1, clock=Clock(), sleep=lambda _: None)


def test_cancellable_sequence_classification():
    from ch32hil.pico import PicoCanceled
    link = Link([b'1 ERR CANCELED host_request\n'])
    client = PicoClient(link, clock=Clock())
    with pytest.raises(PicoCanceled):
        client.sample_gpio(5, 3, 1000, sequence=True)
    assert link.sent == [b'1 GPIO_SEQUENCE 5 3 1000\n']
    client.cancel_sequence()
    assert link.sent[-1] == b'!'


def test_long_ssd1306_page_response_line_is_parsed():
    page = "ab" * 128
    line = f"1 OK page=3 fb={page} safe=1\n".encode()
    r = PicoClient(Link([line]), timeout=1).request("SSD1306_PAGE", 3)
    assert r.ok and f"fb={page}" in r.fields and len(line) > 256


# ---- edge measurement / background capture / I2C hold ----
from ch32hil.pico import Capture, PicoEdgeTimeout, edge_widths


def client(*replies):
    link = Link([r.encode() + b"\n" for r in replies])
    return PicoClient(link, timeout=0.5, clock=Clock()), link


EDGE_OK = ("1 OK pin=6 periods=10 res_ps=16000 period_ps_min=1336000 period_ps_max=1352000 period_ps_avg=1340000 "
           "high_ps_min=656000 high_ps_max=656000 high_ps_avg=656000 duty_ppm=489000 safe=1")


def test_edge_measure_parses_picoseconds_and_sends_the_request():
    c, link = client(EDGE_OK)
    r = c.edge_measure(6, 10, 500)
    assert link.sent == [b"1 EDGE_MEASURE 6 10 500\n"]
    assert r["period_ps_avg"] == 1340000 and r["res_ps"] == 16000 and r["pin"] == 6 and "safe" not in r


def test_edge_measure_timeout_is_a_distinct_error():
    c, _ = client("1 ERR TIMEOUT edge_words=0 of=22")
    with pytest.raises(PicoEdgeTimeout):
        c.edge_measure(6)


def test_edge_measure_rejection_and_garbage():
    c, _ = client("1 ERR CONFLICT capture_active")
    with pytest.raises(PicoError, match="CONFLICT"):
        c.edge_measure(6)
    c, _ = client("1 OK pin=6 periods=x")
    with pytest.raises(PicoProtocolError):
        c.edge_measure(6)


def test_capture_start_arguments_and_rejection():
    c, link = client("1 OK kind=UART pin=9 capacity=4096 baud=115200 active=1", "2 OK kind=EDGE pin=6 capacity=4096 active=1",
                     "3 ERR CONFLICT capture_active")
    assert c.capture_start("UART", 9, 115200)["capacity"] == "4096"
    assert c.capture_start("EDGE", 6)["kind"] == "EDGE"
    assert link.sent == [b"1 CAPTURE_START UART 9 115200\n", b"2 CAPTURE_START EDGE 6\n"]
    with pytest.raises(PicoError, match="CONFLICT"):
        c.capture_start("EDGE", 6)


def read(kind, data, count, received, **kw):
    f = dict(kind=kind, pin=9, active=0, received=received, capacity=4096, full=0, overflow=0, offset=0, count=count, data=data)
    f.update(kw)
    return "OK " + " ".join(f"{k}={v}" for k, v in f.items())


def test_capture_collect_uart_stops_then_reads_in_chunks():
    c, link = client("1 OK was_active=1 valid=1 received=3 overflow=0 active=0",
                     "2 " + read("UART", "6869 21".replace(" ", ""), 3, 3, frame_errors=0))
    cap = c.capture_collect()
    assert cap == Capture("UART", b"hi!", 3, 4096, False, False, False)
    assert [s.split()[1] for s in link.sent] == [b"CAPTURE_STOP", b"CAPTURE_READ"]


def test_capture_collect_reports_overflow_and_frame_errors_without_raising():
    c, _ = client("1 OK was_active=1 valid=1 received=4096 overflow=1 active=0",
                  "2 " + read("UART", "41", 1, 1, full=1, overflow=1, frame_errors=1),
                  "3 " + read("UART", "-", 0, 1, full=1, overflow=1, frame_errors=1))
    cap = c.capture_collect()
    assert cap.overflow and cap.full and cap.frame_errors and cap.items == b"A"


def test_capture_collect_edge_words_and_empty_capture():
    c, _ = client("1 OK was_active=1 valid=1 received=4 overflow=0 active=0",
                  "2 " + read("EDGE", "40,41,42,43", 4, 4))
    assert c.capture_collect().items == [40, 41, 42, 43]
    c, _ = client("1 OK was_active=1 valid=1 received=0 overflow=0 active=0", "2 " + read("EDGE", "-", 0, 0))
    cap = c.capture_collect()
    assert cap.items == [] and cap.received == 0


def test_capture_read_rejects_inconsistent_replies():
    c, _ = client("1 " + read("UART", "6869", 3, 3))        # count says 3, data has 2
    with pytest.raises(PicoProtocolError):
        c.capture_read()
    c, _ = client("1 " + read("UART", "zz", 1, 1))
    with pytest.raises(PicoProtocolError):
        c.capture_read()
    c, _ = client("1 ERR INVALID no_capture")
    with pytest.raises(PicoError, match="no_capture"):
        c.capture_read()


def test_i2c_hold_returns_levels_and_rejects():
    c, link = client("1 OK line=SDA hold_ms=100 during_sda=0 during_scl=1 after_sda=1 after_scl=1 safe=1", "2 ERR INVALID hold_arguments")
    f = c.i2c_hold("SDA", 100)
    assert f["during_sda"] == "0" and f["after_sda"] == "1" and link.sent == [b"1 I2C_HOLD SDA 100\n"]
    with pytest.raises(PicoError):
        c.i2c_hold("FOO", 100)


def test_edge_widths_drops_first_pair_and_applies_cycle_overheads():
    # 83 + 82 loop counts at 16 ns/count: period = (2*(83+82)+9) cycles of 8 ns; High = (2*83+4) cycles
    words = [10, 10, 83, 82, 83, 82]
    assert edge_widths(words, 16000) == [((2 * 165 + 9) * 8000, (2 * 83 + 4) * 8000)] * 2
    assert edge_widths([83, 82], 16000, skip_first=False) == [((2 * 165 + 9) * 8000, (2 * 83 + 4) * 8000)]
    assert edge_widths([83, 82, 5], 16000) == []        # one pair only (plus a dangling word): nothing left after the drop
