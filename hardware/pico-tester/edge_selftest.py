#!/usr/bin/env python3
"""Pico edge-time measurement self-test over a Pico-only loopback (default GP17 PWM -> GP18 input).

PWM and the PIO measurement share the Pico system clock, so this checks the measurement (cycle accounting,
resolution), the range checks, the timeout and the conflict handling, not the absolute clock accuracy.
Needs GP17 (or GP16) wired to GP18 through a resistor; drives the output pin. Run from the repository root.
"""
import argparse
import sys
import time

import serial
from serial.tools import list_ports

sys.path.insert(0, '.')
from ch32hil.pico import discover  # noqa: E402

# (hz, duty%); period must match within one resolution step (16 ns), High within two steps.
CASES = [(1000000, 50), (750000, 50), (750000, 25), (187500, 50), (100000, 10), (100000, 90), (10000, 50), (2000, 50)]


def fields(line):
    return dict(x.split('=', 1) for x in line.split() if '=' in x)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port'); p.add_argument('--output', default='17'); p.add_argument('--input', default='18')
    p.add_argument('--idle-pin', default='22', help='input with no signal, for the timeout case')
    a = p.parse_args()
    port = discover(list_ports.comports, a.port, timeout=30)
    print(f'EDGE selftest {port}: GP{a.output} -> GP{a.input}; output will be driven', flush=True)
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
            i, r = ask(f'EDGE_SELFTEST {a.output} {a.input} {hz} {duty}')
            if not r.startswith(f'{i} OK '):
                raise RuntimeError(f'failed {hz} Hz {duty}%: {r!r}')
            f = fields(r); res = int(f['res_ps'])
            if abs(int(f['period_ps_avg']) - int(f['target_period_ps'])) > res or \
               int(f['period_ps_max']) - int(f['period_ps_min']) > res:
                raise RuntimeError(f'period out of tolerance {hz} Hz {duty}%: {r!r}')
            if abs(int(f['high_ps_avg']) - int(f['target_high_ps'])) > 2 * res:
                raise RuntimeError(f'high width out of tolerance {hz} Hz {duty}%: {r!r}')
        # the same signal through EDGE_MEASURE needs a generator in the background; EDGE_SELFTEST covers it.
        invalid = [f'EDGE_MEASURE 99 10 100', f'EDGE_MEASURE 1 10 100', f'EDGE_MEASURE {a.input} 0 100',
                   f'EDGE_MEASURE {a.input} 256 100', f'EDGE_MEASURE {a.input} 10 9', f'EDGE_MEASURE {a.input} 10',
                   f'EDGE_SELFTEST {a.output} {a.output} 100000 50', f'EDGE_SELFTEST 18 {a.input} 100000 50',
                   f'EDGE_SELFTEST {a.output} {a.input} 1999 50', f'EDGE_SELFTEST {a.output} {a.input} 100000 91']
        for cmd in invalid:
            i, r = ask(cmd)
            if not r.startswith(f'{i} ERR '):
                raise RuntimeError(f'invalid request accepted: {cmd!r} -> {r!r}')
        i, r = ask(f'EDGE_MEASURE {a.idle_pin} 10 100')
        if not r.startswith(f'{i} ERR TIMEOUT'):
            raise RuntimeError(f'expected TIMEOUT without edges: {r!r}')
        i, r = ask(f'CAPTURE_START EDGE {a.idle_pin}')
        if not r.startswith(f'{i} OK '):
            raise RuntimeError(f'capture start failed: {r!r}')
        for cmd in (f'EDGE_MEASURE {a.input} 10 100', f'EDGE_SELFTEST {a.output} {a.input} 100000 50',
                    f'CAPTURE_START EDGE {a.idle_pin}', 'WS2812_SELFTEST OK'):
            i, r = ask(cmd)
            if not r.startswith(f'{i} ERR CONFLICT'):
                raise RuntimeError(f'expected CONFLICT while capturing: {cmd!r} -> {r!r}')
        i, r = ask('CAPTURE_STOP')
        if not r.startswith(f'{i} OK '):
            raise RuntimeError(f'stop failed: {r!r}')
        i, r = ask(f'EDGE_SELFTEST {a.output} {a.input} 100000 50')
        if not r.startswith(f'{i} OK '):
            raise RuntimeError(f'measurement after stop failed (resources leaked?): {r!r}')
        for pin in (int(a.output), int(a.input), int(a.idle_pin)):
            i, r = ask(f'GPIO_STATE {pin}')
            if 'output=0 pull_up=0 pull_down=0' not in r:
                raise RuntimeError(f'GP{pin} not safe: {r!r}')
    print('EDGE selftest: PASS')


if __name__ == '__main__':
    main()
