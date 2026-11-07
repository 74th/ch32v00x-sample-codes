#!/usr/bin/env python3
"""Explicit Pico HIL: connect output to input via a 1 kΩ resistor first."""
import argparse
import time
import serial
from measure import discover


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port')
    p.add_argument('--output', type=int, default=16, choices=(16, 17))
    p.add_argument('--input', type=int, default=17, choices=(16, 17, 18, 19, 20, 21, 22, 26))
    args = p.parse_args()
    if args.output == args.input:
        p.error('output and input must be different')
    port = args.port or discover(30)
    print(f'GPIO loopback: GP{args.output} -> 1 kΩ -> GP{args.input}, Pico {port}; output will be driven')
    with serial.Serial(port, 115200, timeout=4, write_timeout=1) as link:
        time.sleep(.2); link.reset_input_buffer()
        ident = 0
        def req(command):
            nonlocal ident
            ident += 1
            link.write(f'{ident} {command}\n'.encode())
            line = link.readline().decode().strip()
            if not line.startswith(f'{ident} '):
                raise RuntimeError(f'invalid response {line!r}')
            return line
        try:
            for level in (0, 1):
                result = req(f'GPIO_LOOPBACK {args.output} {args.input} {level} 100')
                fields = dict(x.split('=', 1) for x in result.split()[2:] if '=' in x)
                if ' OK ' not in result or int(fields.get('high' if level else 'low', 0)) < 20 or int(fields.get('low' if level else 'high', -1)):
                    raise RuntimeError(f'loopback mismatch: {result}')
            result = req(f'GPIO_LOOPBACK {args.output} {args.output} 0 100')
            if ' ERR CONFLICT ' not in result:
                raise RuntimeError(f'conflict not rejected: {result}')
            result = req(f'GPIO_DRIVE {args.output} 1 2001')
            if ' ERR INVALID ' not in result:
                raise RuntimeError(f'invalid duration accepted: {result}')
            print('High/Low, conflict and invalid duration: PASS')
        finally:
            result = req('RESET_SAFE')
            if ' OK ' not in result:
                raise RuntimeError(f'safe reset failed: {result}')
            for pin in (args.output, args.input):
                result = req(f'GPIO_STATE {pin}')
                if 'output=0 pull_up=0 pull_down=0' not in result:
                    raise RuntimeError(f'unsafe GP{pin}: {result}')
            print('Safe pin settings: PASS')


if __name__ == '__main__':
    main()
