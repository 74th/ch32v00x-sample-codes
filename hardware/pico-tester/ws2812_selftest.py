#!/usr/bin/env python3
"""Hardware test of the WS2812 decoder: needs GP19 -> GP20 joined through 1 kOhm (the SPI loopback wiring).
No pull-ups may remain on GP16-GP19 (remove the I2C loopback wiring first). DUT-facing GP7 is not used."""
import argparse
import time
import serial
from measure import discover

EXPECTED_TX = '00ffa55a0180'   # bytes sent by the self-test


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port')
    args = parser.parse_args()
    port = args.port or discover(30)
    print(f'WS2812 loopback {port}: GP19 -> 1k -> GP20, no pull-ups on GP16-19', flush=True)

    def fields(result):
        return dict(p.split('=', 1) for p in result.split()[2:] if '=' in p)

    with serial.Serial(port, 115200, timeout=3, write_timeout=1) as link:
        time.sleep(.2)
        link.reset_input_buffer()
        steps = [('WS2812_SELFTEST OK', 3)] * 3 + [('WS2812_SELFTEST BADWIDTH', 3), ('WS2812_SELFTEST TIMEOUT', 3),
                 ('WS2812_SELFTEST', 1), ('WS2812_SELFTEST FAST', 1), ('WS2812_CAPTURE 20 6 50', 1)]
        for ident, (cmd, _) in enumerate(steps, 1):
            link.write(f'{ident} {cmd}\n'.encode())
            result = link.readline().decode().strip()
            print(result, flush=True)
            f = fields(result)
            if cmd == 'WS2812_SELFTEST OK':
                if not result.startswith(f'{ident} OK ') or f.get('rx') != EXPECTED_TX or f.get('tx') != EXPECTED_TX \
                        or f.get('bad_pulses') != '0' or f.get('bits') != '48':
                    raise RuntimeError(f'OK selftest failure: {result!r}')
            elif cmd == 'WS2812_SELFTEST BADWIDTH':
                if not result.startswith(f'{ident} OK ') or f.get('bad_pulses') != '1' or f.get('bits') != '48':
                    raise RuntimeError(f'BADWIDTH not detected: {result!r}')
            elif cmd == 'WS2812_SELFTEST TIMEOUT':
                if not result.startswith(f'{ident} OK ') or f.get('words') != '0':
                    raise RuntimeError(f'TIMEOUT not reported: {result!r}')
            elif cmd in ('WS2812_SELFTEST', 'WS2812_SELFTEST FAST'):
                if not result.startswith(f'{ident} ERR INVALID '):
                    raise RuntimeError(f'invalid request accepted: {result!r}')
            else:  # capture with nothing on the line
                if not result.startswith(f'{ident} ERR TIMEOUT '):
                    raise RuntimeError(f'idle capture did not time out: {result!r}')
        for ident, pin in enumerate((7, 19, 20, 21), 100):
            link.write(f'{ident} GPIO_STATE {pin}\n'.encode())
            result = link.readline().decode().strip()
            print(result, flush=True)
            if 'output=0 pull_up=0 pull_down=0' not in result:
                raise RuntimeError(f'pin not safe: {result!r}')
    print('WS2812 loopback and safe pin state: PASS')


if __name__ == '__main__':
    main()
