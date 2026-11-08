"""Where HIL results are stored and what identifies the toolchain/source behind them (no hardware access)."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from . import devices

ROOT = Path(__file__).resolve().parent.parent
COMPILER = ROOT / ".arduino/official/data/packages/WCH/tools/riscv-wch-gcc/15.2.0/bin/riscv32-wch-elf-gcc"
# Devices whose Arduino/WCH results go to <run-dir>/<device>/<framework>/<sample>/<variant>/. The older
# devices keep the flat <run-dir>/<name>.json layout so existing commands and records stay valid.
STRUCTURED_DEVICES = {"ch32v006"}
SDK_REVISIONS = {
    "ch32v003": "openwch/ch32v003 4e1b7437ada5d3ae8831a6f4b811a6320e4e23c7",
    "ch32v002": "openwch/ch32v002_004_005_006_007 a835ede9ff3e2dca2c6aa652809b85c9775475d2",
    "ch32v006": "openwch/ch32v002_004_005_006_007 a835ede9ff3e2dca2c6aa652809b85c9775475d2",
}


def _slug(text) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(text)).strip("-") or "default"


def result_path(run_dir, meta: dict, name: str) -> Path:
    """File for one saved result. Structured devices are separated by device/framework/sample/variant; the run is
    the `--hil-run-dir` the caller chose, so two runs never share a directory unless asked to."""
    base = Path(run_dir)
    if meta.get("device") not in STRUCTURED_DEVICES:
        return base / f"{name}.json"
    variant = meta.get("variant") or "default"
    return base / _slug(meta["device"]) / _slug(meta["framework"]) / _slug(meta["sample"]) / _slug(variant) / f"{name}.json"


def source_revision(root: Path = ROOT, run=subprocess.run) -> str:
    try:
        head = run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                    capture_output=True, text=True).stdout.strip()
    except OSError:
        return "unknown"
    return f"{head}{'+dirty' if dirty else ''}" if head else "unknown"


def compiler_version(compiler: Path = COMPILER, run=subprocess.run) -> str:
    try:
        out = run([str(compiler), "--version"], capture_output=True, text=True).stdout.splitlines()
    except OSError:
        return "missing"
    return out[0].strip() if out else "unknown"


def fqbn(sample_dir: Path):
    path = Path(sample_dir) / "sketch.yaml"
    match = re.search(r"(?m)^\s*fqbn:\s*(\S+)", path.read_text()) if path.is_file() else None
    return match.group(1) if match else None


def memory_layout(sample_dir: Path):
    """FLASH/RAM region sizes the WCH sample was linked with, from its main.map."""
    path = Path(sample_dir) / "main.map"
    match = re.search(r"(?m)^FLASH\s+0x0*\s+(0x[0-9a-f]+)\s.*\n^RAM\s+0x20000000\s+(0x[0-9a-f]+)",
                      path.read_text()) if path.is_file() else None
    return {"flash": int(match.group(1), 16), "ram": int(match.group(2), 16)} if match else None


def toolchain_meta(device: devices.Device, sample: str, root: Path = ROOT) -> dict:
    """Identification stored with every Arduino/WCH result (BIN hash and device come from Dut.metadata())."""
    sample_dir = device.sample_dir(sample)
    meta = {"source_revision": source_revision(root), "compiler": compiler_version()}
    if device.framework == "arduino":
        meta["fqbn"] = fqbn(sample_dir)
    elif device.framework == "wch":
        meta["sdk"] = SDK_REVISIONS.get(device.name)
        meta["memory"] = memory_layout(sample_dir)
    return meta
