#!/usr/bin/env python3
"""Explicit hardware test: GP16 TX <-> 1 kΩ <-> GP17 RX. Drives GP16."""
import argparse
import itertools
import time

import serial
from measure import discover


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', help='Pico serial port; otherwise require a unique Pico')
    args = parser.parse_args()
    port = args.port or discover(30)
    print(f'UART loopback: GP16 -> 1 kΩ -> GP17; Pico {port}; drives GP16', flush=True)
    with serial.Serial(port, 115200, timeout=6, write_timeout=1) as link:
        time.sleep(0.2)
        link.reset_input_buffer()
        request_id = 0

        def request(command):
            nonlocal request_id
            request_id += 1
            link.write(f'{request_id} {command}\n'.encode('ascii'))
            response = link.readline().decode('ascii').strip()
            prefix = f'{request_id} '
            if not response.startswith(prefix):
                raise RuntimeError(f'bad response: {response!r}')
            return response[len(prefix):]

        for baud, bits, parity, stop in itertools.product((1200, 115200), (7, 8), 'NEO', (1, 2)):
            data = '00557f' if bits == 7 else '0055ff'
            result = request(f'UART_XFER LOOPBACK {baud} {bits} {parity} {stop} {data} 3 1000')
            if not result.startswith('OK ') or f'rx={data}' not in result or 'uart_errors=0x0' not in result:
                raise RuntimeError(f'{baud} {bits}{parity}{stop}: {result}')
        print('24 baud/frame boundary cases: PASS')
        data = ''.join(f'{n:02x}' for n in range(32))
        result = request(f'UART_XFER LOOPBACK 115200 8 E 2 {data} 32 1000')
        if not result.startswith('OK ') or f'rx={data}' not in result or 'uart_errors=0x0' not in result:
            raise RuntimeError(f'32-byte case: {result}')
        for command, expected in (
            ('UART_XFER LOOPBACK 9600 8 N 1 - 1 100', 'ERR TIMEOUT '),
            ('UART_XFER LOOPBACK 1199 8 N 1 aa 1 100', 'ERR INVALID '),
            ('UART_XFER LOOPBACK 9600 7 N 1 ff 1 100', 'ERR INVALID '),
        ):
            result = request(command)
            if not result.startswith(expected):
                raise RuntimeError(f'{command}: {result}')
        for pin in (16, 17):
            result = request(f'GPIO_STATE {pin}')
            if 'output=0 pull_up=0 pull_down=0' not in result:
                raise RuntimeError(f'GP{pin}: {result}')
        print('32 bytes, timeout, invalid arguments, safe pin state: PASS')


if __name__ == '__main__':
    run()
