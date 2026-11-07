"""HIL configuration schema + validation (public; no secrets, no host port names)."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from . import devices

REQUIRED = ["name", "dut", "pico", "pins", "voltage", "timeouts", "readback"]
READBACK = {"required", "optional", "disabled"}
UNSAFE_PICO_PINS = {23, 24, 25, 29}  # Pico SMPS/LED/VSYS-sense: not usable fixture pins
MAX_DUT_VOLTAGE = 3.6
PICO_PHYSICAL = {0:1,1:2,2:4,3:5,4:6,5:7,6:9,7:10,8:11,9:12,10:14,11:15,
                 12:16,13:17,14:19,15:20,16:21,17:22,18:24,19:25,20:26,21:27,22:29}
DUT_PHYSICAL = devices.DEVICES[devices.DEFAULT].physical  # backward-compatible alias


class ConfigError(ValueError):
    pass


def validate(cfg: dict, device: str | None = None) -> dict:
    """Validate `cfg`; with `device`, also require cfg dut.device to be that device's part."""
    if not isinstance(cfg, dict):
        raise ConfigError("configuration must be an object")
    errors = [f"missing field: {k}" for k in REQUIRED if k not in cfg]
    if errors:
        raise ConfigError("; ".join(errors))
    if not isinstance(cfg.get("dut"), dict) or not isinstance(cfg.get("pico"), dict) or not isinstance(cfg.get("pins"), dict) or not isinstance(cfg.get("voltage"), dict) or not isinstance(cfg.get("timeouts"), dict):
        raise ConfigError("dut, pico, pins, voltage and timeouts must be objects")
    pico = cfg["pico"]
    if not all(isinstance(pico.get(k), int) and not isinstance(pico.get(k), bool) and 0 < pico[k] <= 65535 for k in ("usb_vid", "usb_pid")):
        errors.append("pico USB identity missing or invalid")
    if pico.get("selection") != "explicit_or_unique":
        errors.append("pico.selection must be explicit_or_unique")
    if not isinstance(cfg["readback"], str) or cfg["readback"] not in READBACK:
        errors.append(f"readback must be one of {sorted(READBACK)}")
    dut = cfg["dut"]
    for k in ("device", "sample"):
        if k not in dut:
            errors.append(f"dut.{k} missing")
    dev = devices.BY_PART.get(dut.get("device"))
    if dev is None:
        errors.append(f"dut.device must be one of {sorted(devices.BY_PART)}")
    elif device is not None and dev.name != device:
        errors.append(f"dut.device {dut['device']} does not match selected HIL device {device}")
    physical = dev.physical if dev else {}
    if not isinstance(dut.get("sample"), str) or not re.fullmatch(r"[a-z0-9_]+", dut["sample"]):
        errors.append("dut.sample must be a simple sample name")
    v = cfg["voltage"]
    if any(not isinstance(v.get(k), (int, float)) or isinstance(v.get(k), bool) or not math.isfinite(v[k]) for k in ("dut_supply", "pico_io")):
        errors.append("voltage.dut_supply and voltage.pico_io must be numbers")
    else:
        if v["dut_supply"] < 2.7 or v["pico_io"] < 2.7:
            errors.append("unsafe voltage below supported 2.7 V")
        if v["dut_supply"] != v["pico_io"]:
            errors.append("DUT supply and Pico IO voltage differ (level mismatch)")
        if v["dut_supply"] > MAX_DUT_VOLTAGE or v["pico_io"] > MAX_DUT_VOLTAGE:
            errors.append(f"unsafe voltage above {MAX_DUT_VOLTAGE} V")
    if v.get("common_ground") is not True:
        errors.append("voltage.common_ground must be true")
    if v.get("power_pins_connected") is not False:
        errors.append("voltage.power_pins_connected must be false")
    if not v.get("dut_power") or not v.get("pico_power") or not v.get("source"):
        errors.append("voltage power sources and source of voltage values must be declared")
    if cfg.get("power_connection_pico_to_dut"):
        errors.append("Pico power must not be connected to DUT power")
    seen_dut, seen_pico = {}, {}
    if not cfg["pins"]:
        errors.append("pins must not be empty")
    for net, m in cfg["pins"].items():
        if not isinstance(m, dict):
            errors.append(f"pins.{net} must be an object")
            continue
        if "dut" not in m or "pico_gpio" not in m:
            errors.append(f"pins.{net} needs dut and pico_gpio")
            continue
        if not isinstance(m["dut"], str):
            errors.append(f"pins.{net}: DUT pin must be a string")
            continue
        pin = m["pico_gpio"]
        if not isinstance(pin, int) or isinstance(pin, bool) or not 0 <= pin <= 29:
            errors.append(f"pins.{net}: invalid Pico GPIO")
            continue
        if pin in UNSAFE_PICO_PINS or pin > 22:
            errors.append(f"pins.{net}: Pico GPIO{pin} is reserved")
            continue
        if not isinstance(m.get("series_ohm"), (int, float)) or isinstance(m.get("series_ohm"), bool) or not math.isfinite(m["series_ohm"]) or m["series_ohm"] <= 0:
            errors.append(f"pins.{net}: series_ohm must be positive")
        if m.get("direction") not in ("dut_to_pico", "pico_to_dut", "bidirectional"):
            errors.append(f"pins.{net}: invalid direction")
        if m.get("kind") not in ("digital", "i2c", "adc"):
            errors.append(f"pins.{net}: invalid kind")
        elif m["kind"] == "i2c" and (m.get("direction") != "bidirectional" or
             not isinstance(m.get("pull_up_ohm"), (int, float)) or isinstance(m.get("pull_up_ohm"), bool) or
             not math.isfinite(m["pull_up_ohm"]) or not 1000 <= m["pull_up_ohm"] <= 10000 or m.get("pull_up_to") != "dut_vdd"):
            errors.append(f"pins.{net}: I2C requires bidirectional wiring and 1k–10k DUT pull-up")
        elif m["kind"] == "adc" and (m.get("direction") != "pico_to_dut" or
             not isinstance(m.get("capacitance_nf"), (int, float)) or isinstance(m.get("capacitance_nf"), bool) or
             not math.isfinite(m["capacitance_nf"]) or not 1 <= m["capacitance_nf"] <= 10000):
            errors.append(f"pins.{net}: ADC RC capacitance missing or unsafe")
        if not isinstance(m.get("dut_physical"), int) or not 1 <= m["dut_physical"] <= 20 or not isinstance(m.get("pico_physical"), int) or not 1 <= m["pico_physical"] <= 40:
            errors.append(f"pins.{net}: physical pin numbers required")
        if m.get("dut") not in physical or m.get("dut_physical") != physical.get(m.get("dut")):
            errors.append(f"pins.{net}: DUT physical pin mismatch")
        if m.get("pico_physical") != PICO_PHYSICAL.get(pin):
            errors.append(f"pins.{net}: Pico physical pin mismatch")
        if m["dut"] == "PD1":
            errors.append(f"pins.{net}: PD1 is reserved for SWIO")
        if m["dut"] in seen_dut:
            errors.append(f"DUT pin {m['dut']} used by {seen_dut[m['dut']]} and {net}")
        if m["pico_gpio"] in seen_pico:
            errors.append(f"Pico GPIO{m['pico_gpio']} used by {seen_pico[m['pico_gpio']]} and {net}")
        seen_dut[m["dut"]], seen_pico[m["pico_gpio"]] = net, net
    t = cfg["timeouts"]
    if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x > 0 for x in t.values()) or not {"build", "flash", "pico_enumeration", "measure"}.issubset(t):
        errors.append("timeouts must be positive numbers")
    if errors:
        raise ConfigError("; ".join(errors))
    return cfg


def load(path, device: str | None = None) -> dict:
    return validate(json.loads(Path(path).read_text()), device)


def select(device_name: str | None = None, config_path=None, root: Path | None = None,
           framework: str | None = None):
    """Resolve the HIL device and its configuration before any hardware access.

    Returns (Device, config Path, validated config). Without a device the default
    (CH32V003) is used; without a config path the device's default config is used.
    Without a framework the default (ch32fun) samples and matrix are used.
    """
    device = devices.get(device_name or devices.DEFAULT, framework or devices.DEFAULT_FRAMEWORK)
    root = Path(root) if root else devices.ROOT
    path = root / (config_path or device.default_config)
    if not path.is_file():
        raise ConfigError(f"HIL config {path} not found for device {device.name}")
    return device, path, load(path, device.name)
