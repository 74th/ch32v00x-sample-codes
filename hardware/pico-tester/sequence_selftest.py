#!/usr/bin/env python3
"""Pico GPIO_SEQUENCE self-test: bounded run, cancel, busy input, recovery. Input only; no output is driven."""
import argparse
import time
import serial
from measure import discover


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port'); p.add_argument('--pin', default='5')
    a = p.parse_args()
    port = a.port or discover(30)
    print(f'GPIO_SEQUENCE selftest {port}: input GP{a.pin}', flush=True)
    with serial.Serial(port, 115200, timeout=6, write_timeout=1) as link:
        time.sleep(.2); link.reset_input_buffer()
        def line():
            r = link.readline().decode().strip(); print(r, flush=True); return r
        # 1. bounded run completes (300 x 10 ms ~ 3 s)
        t = time.monotonic(); link.write(f'1 GPIO_SEQUENCE {a.pin} 300 10000\n'.encode()); r = line()
        el = time.monotonic() - t
        if not r.startswith('1 OK ') or not 2.5 <= el <= 5: raise RuntimeError(f'bounded run failed: {r!r} {el:.1f}s')
        # 2. cancel mid-run with '!'
        link.write(f'2 GPIO_SEQUENCE {a.pin} 300 10000\n'.encode()); time.sleep(.5); t = time.monotonic(); link.write(b'!'); r = line()
        el = time.monotonic() - t
        if not r.startswith('2 ERR CANCELED') or el > 1: raise RuntimeError(f'cancel failed: {r!r} {el:.2f}s')
        # 3. other input while busy aborts the sequence
        link.write(f'3 GPIO_SEQUENCE {a.pin} 300 10000\n'.encode()); time.sleep(.5); link.write(b'x'); r = line()
        if not r.startswith('3 ERR INVALID'): raise RuntimeError(f'busy input not rejected: {r!r}')
        link.reset_input_buffer(); time.sleep(.2); link.reset_input_buffer()
        # 4. out-of-range requests rejected
        for ident, args in ((4, f'{a.pin} 301 10000'), (5, f'{a.pin} 10 500'), (6, '2 10 10000')):
            link.write(f'{ident} GPIO_SEQUENCE {args}\n'.encode()); r = line()
            if not r.startswith(f'{ident} ERR '): raise RuntimeError(f'invalid accepted: {args!r} -> {r!r}')
        # 5. recovery and safe state
        link.write(b'7 RESET_SAFE\n'); r = line()
        if not r.startswith('7 OK'): raise RuntimeError(f'reset_safe failed: {r!r}')
        link.write(f'8 GPIO_STATE {a.pin}\n'.encode()); r = line()
        if 'output=0 pull_up=0 pull_down=0' not in r: raise RuntimeError(f'not safe: {r!r}')
    print('GPIO_SEQUENCE selftest: PASS')


if __name__ == '__main__':
    main()
