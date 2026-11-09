#!/usr/bin/env python3
"""I2C_HOLD check on the fixed DUT wiring (GP10 = SDA, GP11 = SCL, 4.7 kOhm pull-ups to the DUT's VDD).

Holds each line Low through an open-drain style output, checks the level during the hold, that the line returns High
after the release (pull-up only, never driven High), the safe pin state and the argument checks. Drives GP10/GP11 Low.
Run before the DUT is reflashed, or while the DUT does not use I2C. Run from the repository root.
"""
import argparse
import sys
import time

import serial
from serial.tools import list_ports

sys.path.insert(0, '.')
from ch32hil.pico import discover  # noqa: E402


def fields(line):
    return dict(x.split('=', 1) for x in line.split() if '=' in x)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port')
    a = p.parse_args()
    port = discover(list_ports.comports, a.port, timeout=30)
    print(f'I2C_HOLD selftest {port}: GP10/GP11 will be held Low', flush=True)
    ident = 0
    with serial.Serial(port, 115200, timeout=3, write_timeout=1) as link:
        time.sleep(.2); link.reset_input_buffer()

        def ask(cmd):
            nonlocal ident
            ident += 1
            link.write(f'{ident} {cmd}\n'.encode())
            r = link.readline().decode().strip()
            print(r, flush=True)
            return ident, r

        for line, sda, scl in (('SDA', 0, 1), ('SCL', 1, 0), ('BOTH', 0, 0)):
            i, r = ask(f'I2C_HOLD {line} 100')
            f = fields(r)
            if not r.startswith(f'{i} OK ') or (int(f['during_sda']), int(f['during_scl'])) != (sda, scl) \
               or (f['after_sda'], f['after_scl']) != ('1', '1'):
                raise RuntimeError(f'{line}: unexpected levels: {r!r}')
            for pin in (10, 11):
                i, r = ask(f'GPIO_STATE {pin}')
                if 'output=0 pull_up=0 pull_down=0' not in r:
                    raise RuntimeError(f'GP{pin} not safe after hold: {r!r}')
        for cmd in ('I2C_HOLD FOO 100', 'I2C_HOLD SDA 9', 'I2C_HOLD SDA 2001', 'I2C_HOLD SDA', 'I2C_HOLD SDA 100 x',
                    'I2C_HOLD sda 100'):
            i, r = ask(cmd)
            if not r.startswith(f'{i} ERR '):
                raise RuntimeError(f'invalid request accepted: {cmd!r} -> {r!r}')
    print('I2C_HOLD selftest: PASS')


if __name__ == '__main__':
    main()
