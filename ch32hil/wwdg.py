"""Judge the UART text of the `wwdg` samples (samples_*/wwdg) for each -DWWDG_MODE build.

The sample prints "cause=<WWDG|IWDG|other>\\n" at every start, waits 1.5 s, enables the WWDG (counter 0x7F, window 0x5F,
~683 us per count, reset below 0x40 after ~43.7 ms) and prints "." every 5 ms (dot first, then the 5 ms). Pico captures at
most 32 bytes per UART_XFER, so the captured text is a start, its dots and possibly the next start:
  mode 0 (feed inside the window): "cause=other\\n" then only dots, no second "cause=" (never reset)
  mode 1 (feed too early):         "cause=other\\n" "." "cause=WWDG\\n" "." ...  (reset after the first feed)
  mode 2 (never feed):             "cause=other\\n" 9 dots "cause=WWDG\\n"       (reset at ~43.7 ms: dots at 0,5..40 ms)
The numbers of dots are a coarse indicator of the feed timing, not a time measurement (HSI is not calibrated).
"""
from __future__ import annotations

import re

MODES = {0: "feed inside the window", 1: "feed too early", 2: "never feed"}
START = re.compile(rb"cause=(WWDG|IWDG|other)\n?")
FULL = b"cause=WWDG\n"
# Accepted dot counts per mode (nominal: mode 1 -> 1, mode 2 -> 9; +-1 for the UART/loop timing)
MODE1_DOTS = (1, 2)
MODE2_DOTS = (8, 10)
MODE0_MIN_DOTS = 10


def parse(rx: bytes):
    """Split the capture into [(cause, dots)], plus whether the tail after the last segment is clean.

    The capture may end inside the next "cause=..." line (32-byte limit); that partial text is accepted as the tail.
    Anything else between the segments (garbled bytes, other text) is reported in `junk`."""
    matches = list(START.finditer(rx))
    segments, junk = [], []
    lead = rx[:matches[0].start()] if matches else rx
    # Bytes before the first start belong to a capture that began in the middle of a run: only dots are tolerated.
    if lead.strip(b"."):
        junk.append(lead)
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(rx)
        body = rx[m.end():end]
        dots = len(body) - len(body.lstrip(b"."))
        rest = body[dots:]
        if rest and not (i + 1 == len(matches) and FULL.startswith(rest)):
            junk.append(rest)
        segments.append((m.group(1).decode(), dots))
    return {"segments": segments, "leading_dots": len(lead) - len(lead.lstrip(b".")) if not lead.strip(b".") else 0,
            "junk": junk}


def judge_reset_capture(mode: int, rx: bytes):
    """Judge a capture armed before a debugger reset (it starts at the DUT's start text). Returns the parsed dict."""
    if mode not in MODES:
        raise ValueError(f"unknown WWDG_MODE {mode!r}")
    parsed = parse(rx)
    seg, junk = parsed["segments"], parsed["junk"]
    if junk:
        raise AssertionError(f"mode {mode}: unexpected bytes {junk} in {rx!r}")
    if not seg or seg[0][0] != "other" or parsed["leading_dots"]:
        raise AssertionError(f"mode {mode}: capture does not start with 'cause=other' (debugger reset): {rx!r}")
    if mode == 0:
        if len(seg) != 1 or seg[0][1] < MODE0_MIN_DOTS:
            raise AssertionError(f"mode 0: expected one start and >= {MODE0_MIN_DOTS} dots without a reset: {rx!r}")
    elif mode == 1:
        if len(seg) < 2 or not MODE1_DOTS[0] <= seg[0][1] <= MODE1_DOTS[1] or seg[1][0] != "WWDG":
            raise AssertionError(f"mode 1: expected {MODE1_DOTS} dots then a WWDG reset: {rx!r}")
        if len(seg) > 2 and not MODE1_DOTS[0] <= seg[1][1] <= MODE1_DOTS[1]:
            raise AssertionError(f"mode 1: the dots after the WWDG reset are {seg[1][1]}, expected {MODE1_DOTS}: {rx!r}")
    else:
        if len(seg) < 2 or not MODE2_DOTS[0] <= seg[0][1] <= MODE2_DOTS[1] or seg[1][0] != "WWDG":
            raise AssertionError(f"mode 2: expected {MODE2_DOTS} dots then a WWDG reset: {rx!r}")
    return parsed


def judge_running(rx: bytes):
    """A later capture of a build that must keep running (mode 0): dots only, no start text (a restart loop would put
    'cause=' into every 32-byte capture because a start is at most 12 bytes + 9 dots)."""
    if len(rx) < 8 or rx.strip(b"."):
        raise AssertionError(f"mode 0: expected a continuous run of dots, got {rx!r}")
    return {"dots": len(rx)}
