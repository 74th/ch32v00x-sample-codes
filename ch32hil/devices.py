"""Per-device constants for HIL (single source of truth for device-specific values)."""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = "ch32v003"
# Sample frameworks: samples live in samples_<device>_<framework>/. ch32fun is the default.
FRAMEWORKS = ("ch32fun", "arduino", "wch")
DEFAULT_FRAMEWORK = "ch32fun"

# TSSOP20 physical pin numbers. CH32V003F4P6: CH32V003 datasheet pin table.
# CH32V002F4P6: CH32V002 datasheet V1.7 pinout (PDF p.13) and table 2-1 (PDF p.16-19);
# identical to CH32V003F4P6 (VSS=7 and VDD=9 are power, not listed).
_TSSOP20 = {"PD4": 1, "PD5": 2, "PD6": 3, "PD7": 4, "PA1": 5, "PA2": 6, "PD0": 8,
            "PC0": 10, "PC1": 11, "PC2": 12, "PC3": 13, "PC4": 14, "PC5": 15,
            "PC6": 16, "PC7": 17, "PD1": 18, "PD2": 19, "PD3": 20}

# ch32fun application sources shared by CH32V002 and CH32V006 (formerly samples_ch32v002_ch32fun/). "00x" names the
# shared layout, not support for untested devices: only CH32V002F4P6 and CH32V006F8P6 are verified.
FUN_SHARED_ROOT = "samples_ch32v00x_ch32fun"

# Matrix states for which a HIL test of the sample is skipped on that device.
SKIP_STATES = {"excluded", "not-ported"}


class DeviceError(ValueError):
    pass


@dataclass(frozen=True)
class Device:
    name: str            # CLI / sample-directory name, e.g. "ch32v002"
    part: str            # HIL config dut.device, e.g. "CH32V002F4P6"
    target_mcu: str      # ch32fun TARGET_MCU and result metadata `target`
    chip: str            # fixed minichlink "Detected <chip>"
    chip_id_type: int | None  # expected upper 12 bits of 0x1ffff704, checked before flash
    physical: dict
    default_config: str
    matrix: str
    framework: str = DEFAULT_FRAMEWORK
    # Explicit ch32fun source root (repo-relative), decoupled from the device name so that devices can share
    # application sources. A shared root is built once per target into build/<name>/ (see samples_*/target.mk).
    # None keeps the legacy layout samples_<name>_<framework>/ with the artifact directly in the sample directory.
    fun_root: str | None = None

    @property
    def sample_root(self) -> Path:
        if self.framework == DEFAULT_FRAMEWORK and self.fun_root:
            return ROOT / self.fun_root
        return ROOT / f"samples_{self.name}_{self.framework}"

    @property
    def per_target_build(self) -> bool:
        """True when artifacts live in <sample>/build/<name>/ (shared ch32fun sources)."""
        return self.framework == DEFAULT_FRAMEWORK and self.fun_root is not None

    def artifact(self, sample_dir: Path, name: str = "main.bin") -> Path:
        return sample_dir / "build" / self.name / name if self.per_target_build else sample_dir / name

    def sample_dir(self, sample: str) -> Path:
        return self.sample_root / sample

    def matrix_entries(self) -> list:
        path = ROOT / self.matrix
        return json.loads(path.read_text())["entries"] if path.is_file() else []

    def skip_reason(self, sample: str) -> str | None:
        """Why a HIL test of `sample` cannot run on this device, or None."""
        for entry in self.matrix_entries():
            if entry.get("sample") == sample and entry.get("state") in SKIP_STATES:
                return f"{self.name}: {sample} is {entry['state']} in {self.matrix}: {entry.get('note', '')}"
        if not (self.sample_dir(sample) / "Makefile").is_file():
            return f"{self.name}: sample {self.sample_dir(sample).relative_to(ROOT)} does not exist"
        return None


DEVICES = {
    "ch32v003": Device("ch32v003", "CH32V003F4P6", "CH32V003", "CH32V003", None, _TSSOP20,
                       "hil/configs/gpio_blink.json", "hil/matrix.json"),
    "ch32v002": Device("ch32v002", "CH32V002F4P6", "CH32V002", "CH32V002", 0x002, _TSSOP20,
                       "hil/configs/ch32v002_gpio_blink.json", "hil/matrix_ch32v002.json",
                       fun_root=FUN_SHARED_ROOT),
    # Physical pins follow the CH32V006F8P7 TSSOP20 definition (identical to F4P6); F8P6 itself is unverified.
    "ch32v006": Device("ch32v006", "CH32V006F8P6", "CH32V006", "CH32V006", 0x006, _TSSOP20,
                       "hil/configs/ch32v006_gpio_blink.json", "hil/matrix_ch32v006.json",
                       fun_root=FUN_SHARED_ROOT),
}
BY_PART = {d.part: d for d in DEVICES.values()}
# Verification matrix per (device, non-default framework); the ch32fun matrix is Device.matrix.
FRAMEWORK_MATRICES = {
    ("ch32v003", "arduino"): "hil/matrix_arduino.json",
    ("ch32v002", "arduino"): "hil/matrix_ch32v002_arduino.json",
    ("ch32v003", "wch"): "hil/matrix_wch.json",
    ("ch32v002", "wch"): "hil/matrix_ch32v002_wch.json",
    ("ch32v006", "arduino"): "hil/matrix_ch32v006_arduino.json",
    ("ch32v006", "wch"): "hil/matrix_ch32v006_wch.json",
}  # A (device, framework) pair missing here is rejected by get() before any hardware access.


def check_framework(framework: str) -> str:
    if framework not in FRAMEWORKS:
        raise DeviceError(f"unknown HIL framework {framework!r}; use one of {list(FRAMEWORKS)}")
    return framework


def get(name: str, framework: str = DEFAULT_FRAMEWORK) -> Device:
    """Device for `name`; with a non-default framework, its sample root and matrix follow that framework."""
    try:
        device = DEVICES[name]
    except (KeyError, TypeError):
        raise DeviceError(f"unknown HIL device {name!r}; use one of {sorted(DEVICES)}") from None
    if check_framework(framework) == DEFAULT_FRAMEWORK:
        return device
    if (name, framework) not in FRAMEWORK_MATRICES:
        raise DeviceError(f"framework {framework!r} is not available for HIL device {name!r}")
    return dataclasses.replace(device, framework=framework, matrix=FRAMEWORK_MATRICES[(name, framework)])
