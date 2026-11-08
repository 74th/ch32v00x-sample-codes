"""DUT build / flash / readback / reset using only the pinned externals/ch32fun."""
from __future__ import annotations

import hashlib
import subprocess
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import devices

ROOT = Path(__file__).resolve().parent.parent
CH32FUN = ROOT / "externals" / "ch32fun"
MINICHLINK = CH32FUN / "minichlink" / "minichlink"

EXPECTED_CHIP = {name: f"Detected {d.chip}" for name, d in devices.DEVICES.items()}
CHIP_ID_ADDRESS = 0x1FFFF704
_CHIP_ID_LINE = re.compile(r"(?m)^1ffff704:((?:\s+[0-9a-fA-F]{2}){4})\b")
NEGATIVE = ("No detected chip.", "Unknown chip", "Could not initialize", "Could not find")


class DutError(Exception):
    """A DUT phase failed; `phase` names it (build/flash/readback/reset)."""

    def __init__(self, phase: str, message: str):
        super().__init__(f"{phase}: {message}")
        self.phase = phase


@dataclass
class CmdResult:
    returncode: int
    output: str


Runner = "Callable[[list[str], float], CmdResult]"


def run_cmd(argv, timeout):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise DutError("timeout", f"{argv[0]} exceeded {timeout}s") from exc
    return CmdResult(p.returncode, (p.stdout or "") + (p.stderr or ""))


def _check_detected(output: str, target: str, phase: str) -> None:
    expected = EXPECTED_CHIP[target].split()[-1]
    detected = re.findall(r"(?m)^Detected\s+(CH32V[0-9A-Za-z]+)\s*$", output)
    if not detected or any(chip != expected for chip in detected):
        raise DutError(phase, f"expected only {expected}, detected {detected}")
    if any(negative in output for negative in NEGATIVE):
        raise DutError(phase, "negative programmer output")


def check_chip_id(result: CmdResult, expected_type: int) -> int:
    """Check `minichlink -r + 0x1ffff704 4` output; the upper 12 bits of the LE word are the type."""
    if result.returncode != 0:
        raise DutError("flash", f"chip identifier read failed (exit {result.returncode})")
    for neg in NEGATIVE:
        if neg in result.output:
            raise DutError("flash", f"chip identifier read: negative output: {neg}")
    found = _CHIP_ID_LINE.findall(result.output)
    if len(found) != 1:
        raise DutError("flash", f"chip identifier at 0x{CHIP_ID_ADDRESS:08x} not readable")
    value = int.from_bytes(bytes.fromhex("".join(found[0].split())), "little")
    if value >> 20 != expected_type:
        raise DutError("flash", f"chip identifier 0x{value:08x}: type 0x{value >> 20:03x}, "
                                f"expected 0x{expected_type:03x}")
    return value


def check_flash_output(result: CmdResult, target: str = "ch32v003") -> None:
    """Reject exit-0 false successes: need expected chip + 'Image written.' and no negatives."""
    out = result.output
    if result.returncode != 0:
        raise DutError("flash", f"minichlink exit code {result.returncode}")
    _check_detected(out, target, "flash")
    if "Image written." not in out:
        raise DutError("flash", "'Image written.' not confirmed")
    for neg in NEGATIVE:
        if neg in out:
            raise DutError("flash", f"negative output: {neg}")


def check_readback_output(result: CmdResult, target: str = "ch32v003") -> None:
    if result.returncode != 0:
        raise DutError("readback", f"minichlink exit code {result.returncode}")
    _check_detected(result.output, target, "readback")
    for neg in NEGATIVE:
        if neg in result.output:
            raise DutError("readback", f"negative output: {neg}")


@dataclass
class Dut:
    sample_dir: Path
    target: str = "ch32v003"
    run: object = field(default=run_cmd)
    minichlink: Path = MINICHLINK
    timeout: float = 60.0
    # The WCH-Link USB connection has been observed to drop and re-enumerate; wait for
    # `minichlink -i` to detect the expected chip before each programmer operation.
    # Only the detection is retried, never the flash itself.
    ready_timeout: float = 20.0
    ready_interval: float = 1.0
    sleep: object = field(default=time.sleep)
    # Extra `make` variables (e.g. ("HELPER_CLOCK=1",)). Because make does not notice changed variables,
    # a non-empty value cleans the sample first so a previous variant cannot be flashed by mistake.
    make_args: tuple = ()
    # Sample framework; `wch` samples build with the WCH GCC chosen by their own Makefile, so the
    # generic PREFIX (riscv64-unknown-elf, used by ch32fun/arduino builds) must not be passed.
    framework: str = "ch32fun"

    def __post_init__(self):
        devices.get(self.target)  # unknown device -> DeviceError before any programmer access
        self.chip_id = None

    @property
    def binary(self) -> Path:
        return devices.get(self.target, self.framework).artifact(self.sample_dir)

    def metadata(self) -> dict:
        """What the result must record to tell devices/targets apart: device, framework, build target,
        source placement, artifact hash, build variant and the identification word read before flashing."""
        dev = devices.get(self.target, self.framework)
        binary = self.binary

        def rel(path):
            try:
                return str(path.relative_to(ROOT))
            except ValueError:
                return str(path)
        return {"device": dev.name, "part": dev.part, "framework": self.framework,
                "build_target": dev.target_mcu if dev.per_target_build or self.framework == "ch32fun" else None,
                "source_dir": rel(self.sample_dir), "artifact": rel(binary),
                "artifact_sha256": hashlib.sha256(binary.read_bytes()).hexdigest() if binary.is_file() else None,
                "variant": list(self.make_args),
                "chip_id": f"0x{self.chip_id:08x}" if self.chip_id is not None else None}

    def _target_args(self) -> list:
        """Shared ch32fun sources are selected per target; the artifact never falls back to another target's."""
        dev = devices.get(self.target, self.framework)
        return [f"TARGET_MCU={dev.target_mcu}"] if dev.per_target_build else []

    def build(self) -> Path:
        prefix = ([] if self.framework == "wch" else ["PREFIX=riscv64-unknown-elf"]) + self._target_args()
        if self.make_args:
            self.run(["make", "-C", str(self.sample_dir), "clean", *prefix], 300)
        r = self.run(["make", "-C", str(self.sample_dir), "build", *prefix, *self.make_args], 300)
        if r.returncode != 0 or not self.binary.is_file():
            raise DutError("build", f"make failed (exit {r.returncode})")
        return self.binary

    def wait_ready(self, phase: str) -> None:
        if self.ready_timeout <= 0:
            return
        deadline = time.monotonic() + self.ready_timeout
        last = "no output"
        while True:
            try:
                r = self.run([str(self.minichlink), "-i"], 10)
                last = f"exit {r.returncode}: {r.output.strip().splitlines()[-1:] or ['no output']}"
                if r.returncode == 0 and "Found WCH Link" in r.output:
                    _check_detected(r.output, self.target, phase)
                    return
            except DutError as exc:
                if "detected" in str(exc):
                    raise
                last = str(exc)
            if time.monotonic() >= deadline:
                raise DutError(phase, f"programmer/chip not detected within {self.ready_timeout}s ({last})")
            self.sleep(self.ready_interval)

    @property
    def device(self) -> devices.Device:
        return devices.get(self.target)

    def verify_chip_id(self):
        """For devices whose minichlink name alone is not trusted, check 0x1ffff704 before writing."""
        expected = self.device.chip_id_type
        if expected is None:
            return None
        r = self.run([str(self.minichlink), "-r", "+", hex(CHIP_ID_ADDRESS), "4", "-b"], self.timeout)
        self.chip_id = check_chip_id(r, expected)
        return self.chip_id

    def flash(self) -> CmdResult:
        if not self.binary.is_file():
            raise DutError("flash", "build artifact missing")
        self.wait_ready("flash")
        self.verify_chip_id()
        r = self.run([str(self.minichlink), "-w", str(self.binary), "flash", "-b"], self.timeout)
        check_flash_output(r, self.target)
        return r

    def readback(self, tmp: Path) -> None:
        size = self.binary.stat().st_size
        self.wait_ready("readback")
        out = tmp / "readback.bin"
        r = self.run([str(self.minichlink), "-r", str(out), "flash", str(size), "-b"], self.timeout)
        check_readback_output(r, self.target)
        if not out.is_file():
            raise DutError("readback", "no readback file produced")
        if out.read_bytes() != self.binary.read_bytes():
            raise DutError("readback", "readback bytes differ from artifact")

    def reset(self, wait: bool = True) -> CmdResult:
        """Reset the DUT. Timing-sensitive callers pass wait=False after their own wait_ready()."""
        if wait:
            self.wait_ready("reset")
        r = self.run([str(self.minichlink), "-b"], self.timeout)
        if r.returncode != 0:
            raise DutError("reset", f"reset failed (exit {r.returncode})")
        _check_detected(r.output, self.target, "reset")
        return r
