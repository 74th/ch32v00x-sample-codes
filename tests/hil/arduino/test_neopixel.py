"""HIL: Arduino Core CH32 neopixel (book-code neopixel-arduino_core_ch32, corrected), Pico WS2812 decoder.

DESTRUCTIVE: rebuilds and flashes the DUT with the pinned minichlink.

Sample changes (samples_<device>_arduino/neopixel/neopixel.ino):
- data pin PC0 -> PC6, the fixed wiring's WS2812 decoder input (Pico GP7);
- bytes sent MSB first (the book code sends LSB first, which WS2812 does not expect);
- bit timing set by per-series nop counts tuned to the centre of the WS2812B datasheet timing
  (T0H 0.4 us, T1H 0.8 us, T0L 0.85 us, T1L 0.45 us, each +-150 ns); interrupts off while sending.
Expected values from the sketch: every ~300 ms one frame of 6 LEDs x 3 bytes; LED i gets colour pattern
(count + i) % 6 of [20 00 00], [20 20 00], [00 20 00], [00 20 20], [00 00 20], [20 00 20]; count +1 per frame.
Judgement uses the decoder's measured width ranges (h0/h1/l0/l1, about +-16 ns), not its fixed 0/1 windows
(830 ns lower bound for a 1 was set for the ch32fun SPI helper and is above a centred 0.8 us T1H).
The Low after the last bit of a byte includes loading the next byte; it is allowed up to 1200 ns (CH32V003) or
1300 ns (CH32V002) and recorded.
"""
import pytest

from ch32hil.pico import PicoError

from .common import (_cleanup, _prepare, _with_client, build_flash_readback, fields_of, find_port, new_run, save)

pytestmark = [pytest.mark.hil, pytest.mark.arduino, pytest.mark.gpio]

SAMPLE = "neopixel"
DECODER_GP = 7
LED_NUM = 6
PATTERNS = [(0x20, 0, 0), (0x20, 0x20, 0), (0, 0x20, 0), (0, 0x20, 0x20), (0, 0, 0x20), (0x20, 0, 0x20)]


# WS2812B datasheet timing (ns): centre +- 150
SPEC = {"h0": (250, 550), "h1": (650, 950), "l0": (700, 1000), "l1": (300, 600)}
# Low after the last bit of a byte also covers loading the next byte (about 12 cycles on CH32V003, more on the
# CH32V002 build): allowed above the datasheet 1000 ns and recorded (okf/log/2026-11-07-2310-arduino-neopixel-timing.md).
L0_BYTE_BOUNDARY_MAX = {"ch32v003": 1200, "ch32v002": 1300}


def frame_for(count):
    return bytes(v for i in range(LED_NUM) for v in PATTERNS[(count + i) % 6])


def phase_of(frame):
    matches = [k for k in range(6) if frame_for(k) == frame]
    return matches[0] if matches else None


def _capture(port, n):
    def action(client):
        client.negotiate(["WS2812_CAPTURE"])
        frames = []
        for _ in range(n):
            r = client.request("WS2812_CAPTURE", DECODER_GP, LED_NUM * 3, 2000)
            f = fields_of(r)
            frames.append({"ok": r.ok, "status": r.fields[0] if r.fields and "=" not in r.fields[0] else "OK", **f})
        return frames
    return _with_client(port, n * 2.5 + 3, action)


def _range(text):
    lo, hi = (int(x) for x in text.split("-"))
    return lo, hi


def _check(frames, l0_boundary_max):
    phases, widths = [], []
    for f in frames:
        if f.get("bits") != str(LED_NUM * 24) or "rx" not in f or not all(f"{k}_ns" in f for k in SPEC):
            raise AssertionError(f"WS2812 capture failed: {f}")
        k = phase_of(bytes.fromhex(f["rx"]))
        if k is None:
            raise AssertionError(f"frame {f['rx']} is none of the 6 expected rotations; e.g. {frame_for(0).hex()}")
        phases.append(k)
        w = {key: _range(f[f"{key}_ns"]) for key in SPEC}
        widths.append(w)
        for key, (lo, hi) in SPEC.items():
            got_lo, got_hi = w[key]
            limit_hi = l0_boundary_max if key == "l0" else hi
            if got_lo < lo or got_hi > limit_hi or (key == "l0" and got_lo > hi):
                raise AssertionError(f"{key} {got_lo}-{got_hi} ns outside WS2812B {lo}-{hi} ns: {f}")
    steps = [(b - a) % 6 for a, b in zip(phases, phases[1:])]
    if any(s != 1 for s in steps):
        raise AssertionError(f"frames do not advance by one colour step: phases={phases}")
    return {"phases": phases, "widths_ns": widths, "decoder_bad_pulses": [f.get("bad_pulses") for f in frames]}


def test_arduino_neopixel(request, hil_device, hil_config, hil_dut):
    dut = hil_dut(SAMPLE)
    run = new_run(hil_device, SAMPLE, data_pin="PC6 (sample change)", spec_ns=SPEC,
                  criteria="3 consecutive 18-byte frames, each one of the 6 expected rotations (MSB first), "
                           "advancing by one step; High/Low widths inside WS2812B 0.4/0.8/0.85/0.45 us +-150 ns "
                           f"(byte-boundary T0L up to {L0_BYTE_BOUNDARY_MAX[hil_device.name]} ns)")
    print("HIL ARDUINO neopixel: DUT PC6 -> Pico GP7 WS2812 decoder")
    port = {}
    try:
        run.phase("pico_prepare", lambda: port.setdefault("p", find_port(request, hil_config)))
        run.phase("fixture_setup", _prepare, port.get("p"), 6)
        build_flash_readback(run, dut)
        run.phase("dut_reset", dut.reset)
        frames = run.phase("measure", _capture, port.get("p"), 3)
        run.meta["frames"] = frames
        if frames is not None:
            run.meta["summary"] = run.phase("check", _check, frames, L0_BYTE_BOUNDARY_MAX[hil_device.name])
    finally:
        run.phase("cleanup", _cleanup, port.get("p"), 6)
        save(request, run, "arduino_neopixel")
    print(run.to_json())
    assert run.ok, run.to_json()
