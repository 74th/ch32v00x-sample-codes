#!/usr/bin/env python3
"""CH32V003 WCH SDK CLI build, guarded flash/readback, and Pico observation."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ch32hil.dut import Dut
from ch32hil.pico import PicoClient, discover

SAMPLE = ROOT / "samples_ch32v003_wch/blink"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("build", "flash", "observe"))
    parser.add_argument("--output", type=Path, help="write observation JSON")
    args = parser.parse_args()
    if args.phase == "build":
        subprocess.run(["make", "-C", str(SAMPLE), "build"], check=True)
    elif args.phase == "flash":
        # Same chip/output guards used by existing HIL; never use a PATH programmer.
        subprocess.run([str(ROOT / "scripts/ch32fun.sh"), "programmer"], check=True)
        dut = Dut(SAMPLE)
        print(dut.flash().output)
        with tempfile.TemporaryDirectory() as tmp:
            dut.readback(Path(tmp))
        print("READBACK OK: all binary bytes match")
        print(dut.reset().output)
        print("FLASH OK (runtime unverified; run observe separately)")
    else:
        import itertools
        import serial
        from serial.tools import list_ports

        port = discover(list_ports.comports, timeout=30)
        with serial.Serial(port, 115200, timeout=0.2, write_timeout=1) as dev:
            dev.reset_input_buffer()
            client = PicoClient(dev, timeout=6)
            caps = client.negotiate(["GPIO_SAMPLE", "RESET_SAFE"])
            if caps.get("proto") != "2":
                raise RuntimeError(f"expected protocol 2: {caps}")
            try:
                client.reset_safe()
                samples = client.sample_gpio(5, 300, 10000)
                runs = [(level, len(list(group))) for level, group in itertools.groupby(samples)]
                full = runs[1:-1]  # first/last runs may be truncated by the capture window
                passed = len(full) >= 4 and all(40 <= count <= 60 for _, count in full)
                result = {"port": port, "pin": "PC0 -> Pico GP5", "count": 300,
                          "interval_us": 10000, "runs": runs, "pass": passed,
                          "criterion": "at least 4 complete half-periods, each 400..600 ms"}
                print(json.dumps(result, indent=2))
                if args.output:
                    args.output.write_text(json.dumps(result, indent=2) + "\n")
                if not passed:
                    raise RuntimeError("PC0 did not match the expected 500 ms high/low signal")
            finally:
                client.reset_safe()


if __name__ == "__main__":
    main()
