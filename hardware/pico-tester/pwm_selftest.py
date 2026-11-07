#!/usr/bin/env python3
"""Pico PWM generation/measurement self-test over an existing GP16-GP18 loopback.

Generator and measurer share the same Pico clock: this checks plumbing and the
documented functional range, not frequency calibration. Needs GP16-GP18 wired
(the I2C loopback wiring works; GP16-GP17 via a resistor also works).
"""
import argparse
import time
import serial
from measure import discover

# (hz, duty%) boundary set; tolerance: period +-5%, duty +-3 points.
CASES = [(100, 10), (100, 50), (100, 90), (10000, 10), (10000, 50), (10000, 90)]
INVALID = ['GPIO_SELFTEST_PWM 16 18 9 100', 'GPIO_SELFTEST_PWM 16 18 91 100',
           'GPIO_SELFTEST_PWM 16 18 50 1000', 'GPIO_SELFTEST_PWM 16 16 50 100',
           'GPIO_SELFTEST_PWM 18 16 50 100']


def fields(line):
    return dict(x.split('=', 1) for x in line.split() if '=' in x)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port'); p.add_argument('--output', default='16'); p.add_argument('--input', default='18')
    a = p.parse_args()
    port = a.port or discover(30)
    print(f'PWM selftest {port}: GP{a.output} -> GP{a.input}; output will be driven', flush=True)
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
        for hz, duty in CASES:
            i, r = ask(f'GPIO_SELFTEST_PWM {a.output} {a.input} {duty} {hz}')
            if not r.startswith(f'{i} OK '):
                raise RuntimeError(f'failed {hz} Hz {duty}%: {r!r}')
            f = fields(r); period, d = int(f['period_us']), int(f['duty_ppm'])
            want = 1000000 // hz
            if abs(period - want) > want * 0.05 or abs(d - duty * 10000) > 30000:
                raise RuntimeError(f'out of tolerance {hz} Hz {duty}%: period={period} duty_ppm={d}')
        for cmd in INVALID:
            i, r = ask(cmd)
            if not r.startswith(f'{i} ERR '):
                raise RuntimeError(f'invalid request accepted: {cmd!r} -> {r!r}')
        for pin in (16, 17, 18, 19):
            i, r = ask(f'GPIO_STATE {pin}')
            if 'output=0 pull_up=0 pull_down=0' not in r:
                raise RuntimeError(f'GP{pin} not safe: {r!r}')
    print('PWM selftest and safe pin state: PASS')


if __name__ == '__main__':
    main()
