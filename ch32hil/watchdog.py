"""Analyse the bounded PC0 watchdog signature from the fixture sample stream."""
from itertools import groupby


def analyse_signature(samples: str, interval_us: int):
    if not samples or set(samples) - {'0', '1'} or interval_us <= 0:
        raise ValueError('invalid digital sample sequence')
    runs = [(int(value), len(list(group))) for value, group in groupby(samples)]
    highs = [n * interval_us for value, n in runs if value]
    gaps = [n * interval_us for value, n in runs if not value]
    if len(highs) != 9:
        raise ValueError(f'expected 3+6 pulses, observed {len(highs)}')
    if any(not 45000 <= width <= 160000 for width in highs):
        raise ValueError(f'bad pulse widths: {highs}')
    # Only an interior low gap can separate the two pulse groups.
    first_high = next(i for i, (value, _) in enumerate(runs) if value)
    gap_after_three = runs[first_high + 5]
    if gap_after_three[0] != 0 or gap_after_three[1] * interval_us < 400000:
        raise ValueError('missing watchdog reset gap after initial three pulses')
    return {'high_us': highs, 'gap_us': gap_after_three[1] * interval_us, 'runs': runs}
