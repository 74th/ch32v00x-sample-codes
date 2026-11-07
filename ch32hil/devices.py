"""Per-device constants for HIL (single source of truth for device-specific values)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = "ch32v003"

# TSSOP20 physical pin numbers. CH32V003F4P6: CH32V003 datasheet pin table.
# CH32V002F4P6: CH32V002 datasheet V1.7 pinout (PDF p.13) and table 2-1 (PDF p.16-19);
# identical to CH32V003F4P6 (VSS=7 and VDD=9 are power, not listed).
_TSSOP20 = {"PD4": 1, "PD5": 2, "PD6": 3, "PD7": 4, "PA1": 5, "PA2": 6, "PD0": 8,
            "PC0": 10, "PC1": 11, "PC2": 12, "PC3": 13, "PC4": 14, "PC5": 15,
            "PC6": 16, "PC7": 17, "PD1": 18, "PD2": 19, "PD3": 20}

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

    @property
    def sample_root(self) -> Path:
        return ROOT / f"samples_{self.name}_ch32fun"

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
                       "hil/configs/ch32v002_gpio_blink.json", "hil/matrix_ch32v002.json"),
}
BY_PART = {d.part: d for d in DEVICES.values()}


def get(name: str) -> Device:
    try:
        return DEVICES[name]
    except (KeyError, TypeError):
        raise DeviceError(f"unknown HIL device {name!r}; use one of {sorted(DEVICES)}") from None
