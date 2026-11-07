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
