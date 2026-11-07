"""DUT build / flash / readback / reset using only the pinned externals/ch32fun."""
from __future__ import annotations

import subprocess
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CH32FUN = ROOT / "externals" / "ch32fun"
MINICHLINK = CH32FUN / "minichlink" / "minichlink"

EXPECTED_CHIP = {"ch32v003": "Detected CH32V003", "ch32v002": "Detected CH32V002"}
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

    @property
    def binary(self) -> Path:
        return self.sample_dir / "main.bin"

    def build(self) -> Path:
        r = self.run(["make", "-C", str(self.sample_dir), "build", "PREFIX=riscv64-unknown-elf"], 300)
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

    def flash(self) -> CmdResult:
        if not self.binary.is_file():
            raise DutError("flash", "build artifact missing")
        self.wait_ready("flash")
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
