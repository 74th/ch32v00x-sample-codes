#!/usr/bin/env python3
"""Hardware test of the SSD1306 stand-in: needs the I2C loopback wiring
(GP16-GP18 SDA, GP17-GP19 SCL, external 4.7k pull-ups to 3V3). DUT-facing GP10/GP11 are not used."""
import argparse
import time
import serial
from measure import discover


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port')
    args = parser.parse_args()
    port = args.port or discover(30)
    print(f'SSD1306 loopback {port}: GP16-18 SDA, GP17-19 SCL; external 4.7k pull-ups', flush=True)
    with serial.Serial(port, 115200, timeout=3, write_timeout=1) as link:
        time.sleep(.2)
        link.reset_input_buffer()
        for ident, cmd in enumerate(('SSD1306_SELFTEST', 'SSD1306_SELFTEST', 'SSD1306_SELFTEST x',
                                     'GPIO_STATE 16', 'GPIO_STATE 17', 'GPIO_STATE 18', 'GPIO_STATE 19'), 1):
            link.write(f'{ident} {cmd}\n'.encode())
            result = link.readline().decode().strip()
            print(result, flush=True)
            if cmd == 'SSD1306_SELFTEST':
                f = dict(p.split('=', 1) for p in result.split()[2:] if '=' in p)
                if not result.startswith(f'{ident} OK ') or f.get('crc32') != f.get('expected_crc32') \
                        or f.get('frames') != '2' or f.get('unknown') != '1' or f.get('idle_frames') != '0':
                    raise RuntimeError(f'SSD1306 selftest failure: {result!r}')
            elif cmd == 'SSD1306_SELFTEST x':
                if not result.startswith(f'{ident} ERR INVALID '):
                    raise RuntimeError(f'invalid request accepted: {result!r}')
            elif 'output=0 pull_up=0 pull_down=0' not in result:
                raise RuntimeError(f'pin not safe: {result!r}')
    print('SSD1306 loopback and safe pin state: PASS')


if __name__ == '__main__':
    main()
