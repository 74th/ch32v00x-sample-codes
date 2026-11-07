"""Compare documented fixed net/pin/component values with the HIL configuration."""
from __future__ import annotations

import re
from pathlib import Path

from .config import load

ROOT = Path(__file__).resolve().parent.parent
_ROW = re.compile(r'^\| `(?P<net>[A-Z0-9_]+)` \| (?P<dut>P[ACD]\d) \((?P<dut_no>\d+)\) \| GP(?P<gpio>\d+) \((?P<pico_no>\d+)\) \| (?P<details>.*) \|$', re.M)


def _ohms(value):
    return f'{value / 1000:g} kΩ' if value >= 1000 else f'{value:g} Ω'


def problems(config, markdown):
    rows = {m['net']: m.groupdict() for m in _ROW.finditer(markdown)}
    errors = []
    for name, pin in config['pins'].items():
        row = rows.get(name)
        if not row:
            errors.append(f'{name}: no matching documentation row')
            continue
        for field, expected in (('dut', pin['dut']), ('dut_no', str(pin['dut_physical'])),
                                ('gpio', str(pin['pico_gpio'])), ('pico_no', str(pin['pico_physical']))):
            if row[field] != expected:
                errors.append(f'{name}: {field} documentation={row[field]} config={expected}')
        for field in ('series_ohm', 'pull_up_ohm'):
            if field in pin and _ohms(pin[field]) not in row['details']:
                errors.append(f'{name}: {field} {_ohms(pin[field])} not in documentation')
        if 'capacitance_nf' in pin:
            nf = pin['capacitance_nf']
            label = f'{nf / 1000:g} µF' if nf >= 1000 else f'{nf:g} nF'
            if label not in row['details']:
                errors.append(f'{name}: capacitor {label} not in documentation')
    return errors


def main():
    from .devices import DEVICES
    doc = (ROOT / 'hardware/wiring-proposal.md').read_text()
    errors = [f'{d.name}: {e}' for d in DEVICES.values()
              for e in problems(load(ROOT / d.default_config, d.name), doc)]
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print('Wiring/config pin and documented component fields match.')
    print('Human review still required: directions, switches, voltage, power, grounding, real wiring.')


if __name__ == '__main__':
    main()
