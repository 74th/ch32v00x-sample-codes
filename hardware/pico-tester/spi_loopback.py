#!/usr/bin/env python3
"""Hardware test: Pico SPI0 master (GP16 MISO, GP17 CS, GP18 SCK, GP19 MOSI) <-> PIO slave
(GP20 MOSI, GP21 SCK, GP22 CS, GP26 MISO), 1k ohm in each line. Outputs will be driven."""
import argparse
import time
import serial
from measure import discover


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port')
    a = p.parse_args()
    port = a.port or discover(30)
    print(f'SPI loopback {port}: GP19->GP20, GP18->GP21, GP17->GP22, GP26->GP16 (1k each)', flush=True)
    cmds = ['SPI_SELFTEST MODE0', 'SPI_SELFTEST MODE0', 'SPI_SELFTEST MODE3', 'SPI_SELFTEST MODE0 x']
    cmds += [f'GPIO_STATE {n}' for n in (16, 17, 18, 19, 20, 21, 22, 26)]
    with serial.Serial(port, 115200, timeout=3, write_timeout=1) as link:
        time.sleep(.2)
        link.reset_input_buffer()
        for ident, cmd in enumerate(cmds, 1):
            link.write(f'{ident} {cmd}\n'.encode())
            r = link.readline().decode().strip()
            print(r, flush=True)
            if cmd == 'SPI_SELFTEST MODE0':
                if not r.startswith(f'{ident} OK ') or 'master_tx=a5 master_rx=3c slave_rx=a5' not in r:
                    raise RuntimeError(f'loopback failure: {r!r}')
            elif cmd.startswith('SPI_SELFTEST'):
                if not r.startswith(f'{ident} ERR INVALID'):
                    raise RuntimeError(f'invalid request accepted: {r!r}')
            elif 'output=0 pull_up=0 pull_down=0' not in r:
                raise RuntimeError(f'pin not safe: {r!r}')
    print('SPI loopback and safe pin state: PASS')


if __name__ == '__main__':
    main()
