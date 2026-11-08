"""Per-device / per-framework verification matrix loader and checks (hil/matrix*.json)."""
from __future__ import annotations

import json
from pathlib import Path

CLASSES = {"direct-port", "equivalent-standard-ch32fun", "extralibs-excluded", "not-yet-automatable",
           "helper-verification", "additional-not-in-book"}
# Rows of this class are repository-own samples that have no book-code counterpart: book_sample is null and they are not
# part of the one-to-one accounting of the book examples (use book_rows() for that).
ADDITIONAL = "additional-not-in-book"
ADDITIONAL_REQUIRED = ("sample", "peripheral", "note", "criteria")
# Helpers of the pinned externals/ch32fun that helper-verification samples may depend on.
ALLOWED_HELPERS = {
    "extralibs/ssd1306_i2c.h", "extralibs/ssd1306.h",
    "extralibs/ws2812b_dma_spi_led_driver.h", "examples/i2c_slave/i2c_slave.h",
}
HELPER_REQUIRED = ("sample", "helpers", "requires", "criteria")
STATES = {"not-ported", "not-automated", "build-only", "manually-verified", "hil-verified", "excluded"}
# Baseline states whose sample must have a row in every other device matrix.
COVERED_STATES = {"hil-verified", "not-automated", "build-only", "manually-verified"}
# book-code directory patterns accounted for by each framework's matrix.
BOOK_PATTERNS = {
    "ch32fun": ("*-ch32fun",),
    # Arduino Core CH32 sketches; *-arduino_ch32v003 / *-arduino_wch32v003 are another core and not listed.
    "arduino": ("*-arduino_core_ch32", "*_arduino_core_ch32"),
    # Official WCH SDK samples; all 13 book wch_sdk examples are tracked one to one.
    "wch": ("*-wch_sdk",),
}


def load(path):
    return json.loads(Path(path).read_text())["entries"]


def book_rows(entries):
    """Rows that stand for a book-code example (everything except the additional-not-in-book rows)."""
    return [e for e in entries if e.get("class") != ADDITIONAL]


def additional_rows(entries):
    return [e for e in entries if e.get("class") == ADDITIONAL]


def _test_exists(root: Path, ref: str) -> bool:
    path, _, name = ref.partition("::")
    file = root / path
    return bool(name) and file.is_file() and f"def {name}(" in file.read_text()


def problems(entries, book_dir=None, samples_dir=None, root=None, framework="ch32fun"):
    out = []
    for e in entries:
        if e.get("state") != "hil-verified":
            continue
        label = e.get("sample") or e.get("book_sample")
        if not e.get("hil_tests"):
            out.append(f"hil-verified without hil_tests: {label}")
        if not e.get("evidence"):
            out.append(f"hil-verified without evidence log: {label}")
        if root:
            for ref in e.get("hil_tests", []):
                if not _test_exists(Path(root), ref):
                    out.append(f"hil test not found: {ref}")
            for log in e.get("evidence", []):
                if not (Path(root) / log).is_file():
                    out.append(f"evidence log not found: {log}")
    for e in entries:
        if e["class"] not in CLASSES:
            out.append(f"bad class: {e}")
        if e["state"] not in STATES:
            out.append(f"bad state: {e}")
        if e["class"] == "extralibs-excluded" and e["state"] != "excluded":
            out.append(f"extralibs entry must be excluded: {e['book_sample']}")
        if e["class"] == "helper-verification":
            label = e.get("sample") or e.get("book_sample")
            for key in HELPER_REQUIRED:
                if not e.get(key):
                    out.append(f"helper-verification without {key}: {label}")
            for helper in e.get("helpers") or []:
                if helper not in ALLOWED_HELPERS:
                    out.append(f"unknown helper {helper}: {label}")
        if e["class"] == ADDITIONAL:
            label = e.get("sample") or "?"
            if e.get("book_sample"):
                out.append(f"additional-not-in-book row names a book sample: {label}")
            for key in ADDITIONAL_REQUIRED:
                if not e.get(key):
                    out.append(f"additional-not-in-book without {key}: {label}")
        if e["state"] == "hil-verified" and not e.get("requires_verified", True):
            out.append("hil-verified without capability")
        if samples_dir and e.get("sample") and e["state"] in ("build-only", "hil-verified") \
                and not (Path(samples_dir) / e["sample"]).is_dir():
            out.append(f"sample dir missing: {e['sample']}")
    if book_dir:
        listed = {e["book_sample"] for e in entries if e["book_sample"]}
        actual = {p.name for pattern in BOOK_PATTERNS[framework]
                  for p in Path(book_dir).glob(pattern) if p.is_dir()}
        for name in sorted(actual - listed):
            out.append(f"book-code sample not accounted for: {name}")
        for name in sorted(listed - actual):
            out.append(f"matrix lists unknown book-code sample: {name}")
    return out


def coverage_problems(baseline_entries, device_entries):
    """Every baseline sample that is HIL-targeted or not yet automated needs a row in the device matrix."""
    have = {e.get("sample") for e in device_entries}
    out = [f"device matrix lacks baseline sample: {e['sample']}"
           for e in baseline_entries
           if e.get("sample") and e.get("state") in COVERED_STATES and e["sample"] not in have]
    for e in device_entries:
        if not e.get("sample"):
            out.append(f"device matrix row without sample: {e}")
        elif e.get("state") in ("excluded", "not-ported") and not e.get("note"):
            out.append(f"{e['state']} without reason: {e['sample']}")
    return out
