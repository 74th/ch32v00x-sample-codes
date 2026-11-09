#!/usr/bin/env python3
"""Pico background-capture self-test over the Pico-only UART loopback GP16 (TX) -> 1 kOhm -> GP17 (RX).

A PIO capture is armed on GP17, then `UART_XFER LOOPBACK` (another command) sends bytes on GP16 while the capture runs
in the background. Checks the received bytes at each baud rate, frame errors, buffer overflow reporting, edge-width
capture of the same traffic, the rejection of invalid requests and the safe pin state. Drives GP16. Run from the
repository root. Needs GP16 -> GP17 wired (GP17 -> GP18 may stay wired).
"""
import argparse
import sys
import time

import serial
from serial.tools import list_ports

sys.path.insert(0, '.')
from ch32hil.pico import discover  # noqa: E402

BAUDS = [1200, 9600, 115200, 230400, 460800, 921600]
CAPACITY = 4096


def fields(line):
    return dict(x.split('=', 1) for x in line.split() if '=' in x)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port'); p.add_argument('--rx', default='17')
    p.add_argument('--bauds', default=','.join(map(str, BAUDS)))
    p.add_argument('--skip-overflow', action='store_true')
    a = p.parse_args()
    port = discover(list_ports.comports, a.port, timeout=30)
    print(f'capture selftest {port}: GP16 TX -> GP{a.rx} RX; GP16 will be driven', flush=True)
    ident = 0
    summary = {}
    with serial.Serial(port, 115200, timeout=5, write_timeout=1) as link:
        time.sleep(.2); link.reset_input_buffer()

        def ask(cmd, quiet=False):
            nonlocal ident
            ident += 1
            link.write(f'{ident} {cmd}\n'.encode())
            r = link.readline().decode().strip()
            if not quiet:
                print(r[:300], flush=True)
            if not r.startswith(f'{ident} '):
                raise RuntimeError(f'bad response to {cmd!r}: {r!r}')
            return r[len(str(ident)) + 1:]

        def xfer(baud, payload, expect_ok=True):
            r = ask(f'UART_XFER LOOPBACK {baud} 8 N 1 {payload.hex()} {len(payload)} 1000', quiet=True)
            if expect_ok and (not r.startswith('OK ') or f'rx={payload.hex()}' not in r):
                raise RuntimeError(f'UART_XFER failed at {baud}: {r}')
            return r

        def read_all(total):
            data = b''
            last = None
            while len(data) < total:
                r = ask(f'CAPTURE_READ {len(data)} 256', quiet=True)
                last = fields(r)
                if int(last['count']) == 0:
                    break
                data += bytes.fromhex(last['data'])
            return data, last

        for baud in map(int, a.bauds.split(',')):
            payload = bytes(range(0, 32)) if baud >= 9600 else bytes([0x00, 0x55, 0xff, 0xa5])
            r = ask(f'CAPTURE_START UART {a.rx} {baud}')
            if not r.startswith('OK '):
                raise RuntimeError(f'start failed: {r}')
            sent = b''
            rounds = 8 if baud >= 9600 else 2
            for _ in range(rounds):          # another command runs while the capture is active
                xfer(baud, payload); sent += payload
            r = ask('CAPTURE_STOP', quiet=True)
            got, last = read_all(len(sent))
            ok = got == sent and last['overflow'] == '0' and last['frame_errors'] == '0' and last['active'] == '0'
            print(f'  baud {baud}: sent={len(sent)} captured={len(got)} {"OK" if ok else "MISMATCH"}', flush=True)
            summary[baud] = ok
            if not ok:
                print('   sent', sent.hex()); print('   got ', got.hex(), last)
        if not all(summary.values()):
            raise RuntimeError(f'baud results: {summary}')

        if not a.skip_overflow:
            baud = 921600
            r = ask(f'CAPTURE_START UART {a.rx} {baud}')
            payload = bytes(range(32)); sent = 0
            while sent < CAPACITY + 64:      # 4096 + 64 bytes: the capture buffer must report overflow
                xfer(baud, payload); sent += 32
            r = fields(ask('CAPTURE_READ 0 0'))
            if not (r['full'] == '1' and r['overflow'] == '1' and r['received'] == str(CAPACITY)):
                raise RuntimeError(f'overflow not reported: {r}')
            got, _ = read_all(CAPACITY)
            ask('CAPTURE_STOP')
            if got != bytes(range(32)) * (CAPACITY // 32):
                raise RuntimeError('the kept head of the overflowed capture is wrong')
            print('  overflow: full=1 overflow=1 received=4096, kept data intact', flush=True)

        # edge widths of the same UART traffic, captured in the background during another command
        ask(f'CAPTURE_START EDGE {a.rx}')
        xfer(115200, bytes([0x55] * 8))
        r = fields(ask('CAPTURE_STOP', quiet=True))
        r = fields(ask('CAPTURE_READ 0 256', quiet=True))
        words = [int(x) for x in r['data'].split(',')]
        res_ns = 16
        lows = words[1::2]
        bit_ns = 1e9 / 115200
        short = min(w * res_ns for w in words)
        if not (len(words) >= 8 and abs(short - bit_ns) < bit_ns * 0.1):
            raise RuntimeError(f'edge widths of 0x55 at 115200 do not match a bit time: min={short} ns words={words[:16]}')
        print(f'  edge capture of 0x55 x8 at 115200: {len(words)} words, shortest level {short:.0f} ns (bit {bit_ns:.0f} ns)')

        invalid = [f'CAPTURE_START UART 4 9600', f'CAPTURE_START UART 8 9600', f'CAPTURE_START UART 12 9600',
                   f'CAPTURE_START UART 99 9600', f'CAPTURE_START UART {a.rx} 1199', f'CAPTURE_START UART {a.rx} 921601',
                   f'CAPTURE_START UART {a.rx}', f'CAPTURE_START EDGE {a.rx} 9600', 'CAPTURE_START FOO 17 9600',
                   'CAPTURE_START EDGE 99', 'CAPTURE_READ 0 257', 'CAPTURE_READ x 1', 'CAPTURE_STOP now']
        for cmd in invalid:
            r = ask(cmd, quiet=True)
            if not r.startswith('ERR '):
                raise RuntimeError(f'invalid request accepted: {cmd!r} -> {r!r}')
        print(f'  {len(invalid)} invalid requests rejected', flush=True)
        r = ask(f'CAPTURE_START UART {a.rx} 9600', quiet=True)
        r = ask('RESET_SAFE', quiet=True)
        r = ask(f'CAPTURE_START UART {a.rx} 9600', quiet=True)
        if not r.startswith('OK '):
            raise RuntimeError(f'RESET_SAFE did not stop the capture: {r}')
        ask('CAPTURE_STOP', quiet=True)
        for pin in (16, int(a.rx)):
            r = ask(f'GPIO_STATE {pin}', quiet=True)
            if 'output=0 pull_up=0 pull_down=0' not in r:
                raise RuntimeError(f'GP{pin} not safe: {r}')
    print('capture selftest: PASS', summary)


if __name__ == '__main__':
    main()
