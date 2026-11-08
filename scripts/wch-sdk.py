#!/usr/bin/env python3
"""WCH official SDK CLI: build, guarded flash/readback, and (blink only) Pico observation.

Without options the CH32V003 `blink` sample is used, as before. `--device` and `--sample` select
another sample; both are validated before any build or programmer access.
"""
import argparse
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ch32hil.dut import Dut
from ch32hil.pico import PicoClient, discover

from ch32hil import devices

DEFAULT_DEVICE, DEFAULT_SAMPLE = "ch32v003", "blink"
SAMPLE = ROOT / f"samples_{DEFAULT_DEVICE}_wch/{DEFAULT_SAMPLE}"  # backward-compatible default


class SelectionError(ValueError):
    pass


def resolve(device: str = DEFAULT_DEVICE, sample: str = DEFAULT_SAMPLE) -> Path:
    """Sample directory for (device, sample); raises SelectionError before touching hardware."""
    if device not in devices.DEVICES:
        raise SelectionError(f"unknown device {device!r}; use one of {sorted(devices.DEVICES)}")
    root = ROOT / f"samples_{device}_wch"
    if not re.fullmatch(r"[a-z0-9_]+", sample or ""):
        raise SelectionError(f"invalid sample name {sample!r}")
    path = root / sample
    if not (path / "Makefile").is_file():
        have = sorted(p.name for p in (m.parent for m in root.glob("*/Makefile"))) if root.is_dir() else []
        raise SelectionError(f"sample {sample!r} not found for {device} under {root.name}; available: {have}")
    return path


TOOLS = ROOT / ".arduino/official/data/packages/WCH/tools/riscv-wch-gcc/15.2.0/bin/riscv32-wch-elf-"
LAYOUT = {"ch32v003": (0x4000, 0x800), "ch32v002": (0x4000, 0x1000), "ch32v006": (0xF800, 0x2000)}   # (FLASH, RAM) bytes


def check_layout(map_text: str, device: str) -> list:
    """The linker map must show the device's memory (CH32V003 16K/2K, CH32V002 16K/4K, CH32V006 62K/8K)."""
    m = re.search(r"(?m)^FLASH\s+0x0*\s+(0x[0-9a-f]+)\s.*\n^RAM\s+0x20000000\s+(0x[0-9a-f]+)", map_text)
    got = (int(m.group(1), 16), int(m.group(2), 16)) if m else None
    return [] if got == LAYOUT[device] else [f"memory layout {got} is not FLASH/RAM {LAYOUT[device]}"]


def check_sources(nm_l_output: str, device: str, root: Path = ROOT) -> list:
    """Source files recorded in the ELF (nm -l) must be the sample's own or its device SDK: never externals/ or another device."""
    problems = []
    own = (root / f"samples_{device}_wch").resolve()
    paths = {os.path.normpath(m) for m in re.findall(r"\t(/[^:\n]*):\d+", nm_l_output)}
    repo = [p for p in paths if p.startswith(str(root.resolve()))]
    if not any(p.startswith(str(own / "sdk")) for p in repo):
        problems.append(f"no source from samples_{device}_wch/sdk in the ELF")
    for p in repo:
        if "/externals/" in p:
            problems.append(f"externals source linked: {p}")
        elif not p.startswith(str(own)):
            problems.append(f"source outside samples_{device}_wch: {p}")
    return problems


def all_samples(device: str) -> list:
    root = ROOT / f"samples_{device}_wch"
    return sorted(p.parent.name for p in root.glob("*/Makefile"))


def build_all(run=subprocess.run) -> list:
    """Build every sample of every device from clean. Returns rows (device, sample, flash, ram, problems)."""
    rows = []
    for device in sorted(devices.DEVICES):
        for sample in all_samples(device):
            path = ROOT / f"samples_{device}_wch/{sample}"
            run(["make", "-C", str(path), "clean"], capture_output=True)
            r = run(["make", "-C", str(path), "build"], capture_output=True, text=True)
            problems = []
            if r.returncode != 0:
                problems.append("build failed (e.g. memory overflow)")
            mem = dict(re.findall(r"(?m)^\s*(FLASH|RAM):\s+(\d+) B", r.stdout + r.stderr))
            mapfile, elf = path / "main.map", path / "main.elf"
            if mapfile.is_file() and elf.is_file():
                problems += check_layout(mapfile.read_text(), device)
                nm = run([str(TOOLS) + "nm", "-l", str(elf)], capture_output=True, text=True).stdout
                problems += check_sources(nm, device)
            else:
                problems.append("main.map/main.elf missing")
            rows.append((device, sample, mem.get("FLASH"), mem.get("RAM"), problems))
    return rows


def flash(dut: Dut) -> None:
    """Guarded write: Dut.flash checks the chip (and 0x1ffff704) and the artifact before writing."""
    print(dut.flash().output)
    with tempfile.TemporaryDirectory() as tmp:
        dut.readback(Path(tmp))
    print("READBACK OK: all binary bytes match")
    print(dut.reset().output)
    print("FLASH OK (runtime unverified; run observe separately)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("build", "flash", "observe"))
    parser.add_argument("--device", default=DEFAULT_DEVICE, help=f"target device (default {DEFAULT_DEVICE})")
    parser.add_argument("--sample", default=DEFAULT_SAMPLE, help=f"sample directory name (default {DEFAULT_SAMPLE})")
    parser.add_argument("--output", type=Path, help="write observation JSON")
    parser.add_argument("--all", action="store_true", help="build: every sample of every device from clean, with checks")
    args = parser.parse_args()
    if args.all:
        if args.phase != "build":
            parser.error("--all is only for the build phase")
        rows = build_all()
        for device, sample, flash_b, ram_b, problems in rows:
            print(f"{device:9} {sample:16} flash={flash_b or '?':>6} ram={ram_b or '?':>5} {'OK' if not problems else 'NG ' + '; '.join(problems)}")
        bad = [r for r in rows if r[4]]
        print(f"{len(rows)} samples built, {len(bad)} with problems")
        sys.exit(1 if bad else 0)
    try:
        sample_dir = resolve(args.device, args.sample)
        if args.phase == "observe" and args.sample != DEFAULT_SAMPLE:
            raise SelectionError("observe is only defined for the blink sample; use the HIL tests for others")
    except SelectionError as exc:
        parser.error(str(exc))
    if args.phase == "build":
        subprocess.run(["make", "-C", str(sample_dir), "build"], check=True)
    elif args.phase == "flash":
        # Same chip/output guards used by existing HIL; never use a PATH programmer.
        subprocess.run([str(ROOT / "scripts/ch32fun.sh"), "programmer"], check=True)
        flash(Dut(sample_dir, target=args.device, framework="wch"))
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
