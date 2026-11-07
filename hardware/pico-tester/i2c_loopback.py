#!/usr/bin/env python3
"""Hardware test: GP16–GP18 SDA, GP17–GP19 SCL, external 4.7k pull-ups."""
import argparse
import time
import serial
from measure import discover


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port')
    args = parser.parse_args()
    port = args.port or discover(30)
    print(f'I2C loopback {port}: GP16–18 SDA, GP17–19 SCL; external 4.7k pull-ups', flush=True)
    with serial.Serial(port, 115200, timeout=3, write_timeout=1) as link:
        time.sleep(.2)
        link.reset_input_buffer()
        for ident, cmd in enumerate(('I2C_SELFTEST MASTER0', 'I2C_SELFTEST MASTER1',
                                     'I2C_SELFTEST INVALID', 'I2C_FAULTTEST SDA', 'I2C_FAULTTEST SCL', 'GPIO_STATE 16', 'GPIO_STATE 17',
                                     'GPIO_STATE 18', 'GPIO_STATE 19'), 1):
            link.write(f'{ident} {cmd}\n'.encode())
            result = link.readline().decode().strip()
            print(result, flush=True)
            if cmd.startswith('I2C_SELFTEST MASTER'):
                if not result.startswith(f'{ident} OK ') or 'write=55aa read=55aa wrong_address_rc=-1' not in result:
                    raise RuntimeError(f'loopback failure: {result!r}')
            elif cmd == 'I2C_SELFTEST INVALID':
                if not result.startswith(f'{ident} ERR INVALID '):
                    raise RuntimeError(f'invalid request accepted: {result!r}')
            elif cmd.startswith('I2C_FAULTTEST'):
                expected = 'observed=BUS_CONFLICT' if cmd.endswith('SDA') else 'observed=TIMEOUT'
                if not result.startswith(f'{ident} OK ') or expected not in result:
                    raise RuntimeError(f'fault not detected: {result!r}')
            elif 'output=0 pull_up=0 pull_down=0' not in result:
                raise RuntimeError(f'pin not safe: {result!r}')
    print('I2C loopback and safe pin state: PASS')


if __name__ == '__main__':
    main()
