"""CH32V003/ch32fun verification matrix loader and checks."""
from __future__ import annotations

import json
from pathlib import Path

CLASSES = {"direct-port", "equivalent-standard-ch32fun", "extralibs-excluded", "not-yet-automatable"}
STATES = {"not-automated", "build-only", "manually-verified", "hil-verified", "excluded"}


def load(path):
    return json.loads(Path(path).read_text())["entries"]


def problems(entries, book_dir=None, samples_dir=None):
    out = []
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
