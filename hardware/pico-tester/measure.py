#!/usr/bin/env python3
"""Acquire and check the v1 Pico GPIO sample protocol."""
import argparse
import itertools
import sys
import time

import serial
from serial.tools import list_ports


def analyse(line):
    parts = line.strip().split()
    if len(parts) != 3 or parts[0] != 'PICO_GPIO_V1' or parts[1] != '10000':
        raise ValueError('invalid protocol header')
    samples = parts[2]
    if len(samples) != 300 or set(samples) - {'0', '1'}:
        raise ValueError('invalid sample data')
    runs = [(value, len(list(group))) for value, group in itertools.groupby(samples)]
    complete = runs[1:-1]
    if len(complete) < 3 or {value for value, _ in complete} != {'0', '1'}:
        return False, runs
    return all(40 <= count <= 60 for _, count in complete), runs


def discover(timeout):
    deadline = time.monotonic() + timeout
    while True:
        ports = [p.device for p in list_ports.comports() if p.vid == 0x2e8a and p.pid == 0x000a]
        if len(ports) == 1:
            return ports[0]
        if len(ports) > 1:
            raise RuntimeError(f'expected one Pico, found {len(ports)}; specify --port')
        if time.monotonic() >= deadline:
            raise TimeoutError('Pico USB serial device not found')
        time.sleep(min(0.2, max(0, deadline - time.monotonic())))


def main():
    parser = argparse.ArgumentParser(description='Measure CH32V003 PC0 using Pico GP0')
    parser.add_argument('--port', help='Pico USB serial device')
    parser.add_argument('--timeout', type=float, default=6.0)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    try:
        port = args.port or discover(args.timeout)
        with serial.Serial(port, 115200, timeout=0.2, write_timeout=1) as device:
            device.reset_input_buffer()
            device.write(b's')
            deadline = time.monotonic() + args.timeout
            data = bytearray()
            while time.monotonic() < deadline and b'\n' not in data:
                data.extend(device.read(512))
                if len(data) > 1024:
                    raise ValueError('response too long')
            if b'\n' not in data:
                print('TIMEOUT: no complete Pico response', file=sys.stderr)
                return 2
            line = bytes(data).split(b'\n', 1)[0].decode('ascii')
        matched, runs = analyse(line)
        print(f'port: {port}\nresponse: {line}\nruns: {runs}')
        print('PASS: alternating 400–600 ms pulses' if matched else 'MISMATCH: expected alternating 400–600 ms pulses')
        return 0 if matched else 1
    except TimeoutError as exc:
        print(f'TIMEOUT: {exc}', file=sys.stderr)
        return 2
    except (serial.SerialException, OSError, RuntimeError, ValueError, UnicodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
