"""Per-device ch32fun verification matrix loader and checks (hil/matrix*.json)."""
from __future__ import annotations

import json
from pathlib import Path

CLASSES = {"direct-port", "equivalent-standard-ch32fun", "extralibs-excluded", "not-yet-automatable"}
STATES = {"not-ported", "not-automated", "build-only", "manually-verified", "hil-verified", "excluded"}
# Baseline states whose sample must have a row in every other device matrix.
COVERED_STATES = {"hil-verified", "not-automated", "build-only", "manually-verified"}


def load(path):
    return json.loads(Path(path).read_text())["entries"]


def _test_exists(root: Path, ref: str) -> bool:
    path, _, name = ref.partition("::")
    file = root / path
    return bool(name) and file.is_file() and f"def {name}(" in file.read_text()


def problems(entries, book_dir=None, samples_dir=None, root=None):
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
        if e["state"] == "hil-verified" and not e.get("requires_verified", True):
            out.append("hil-verified without capability")
        if samples_dir and e.get("sample") and e["state"] in ("build-only", "hil-verified") \
                and not (Path(samples_dir) / e["sample"]).is_dir():
            out.append(f"sample dir missing: {e['sample']}")
    if book_dir:
        listed = {e["book_sample"] for e in entries if e["book_sample"]}
        actual = {p.name for p in Path(book_dir).glob("*-ch32fun") if p.is_dir()}
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
