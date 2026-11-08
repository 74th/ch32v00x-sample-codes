"""Staged HIL run recorder: each phase result is kept separately; cleanup never hides failure."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

PHASES = ["environment", "pico_prepare", "dut_build", "dut_flash", "dut_readback",
          "dut_reset", "fixture_setup", "measure", "cleanup"]


@dataclass
class PhaseResult:
    name: str
    status: str  # pass | fail | skipped | not_run
    detail: str = ""


@dataclass
class Run:
    meta: dict = field(default_factory=dict)
    results: list = field(default_factory=list)
    primary_failure: str | None = None
    dut: object = None  # the Dut whose build/flash/... was run through phase(); its identity goes into the result

    def phase(self, name, fn, *args):
        owner = getattr(fn, "__self__", None)
        if hasattr(owner, "metadata") and hasattr(owner, "sample_dir"):
            self.dut = owner
        if self.primary_failure and name != "cleanup":
            self.results.append(PhaseResult(name, "skipped", "earlier phase failed"))
            return None
        try:
            out = fn(*args)
        except BaseException as exc:  # includes KeyboardInterrupt: record then re-raise path below
            self.results.append(PhaseResult(name, "fail", f"{type(exc).__name__}: {exc}"))
            if name != "cleanup" and self.primary_failure is None:
                self.primary_failure = f"{name}: {exc}"
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            return None
        self.results.append(PhaseResult(name, "pass"))
        return out

    def to_json(self):
        meta = dict(self.meta)
        if self.dut is not None:
            meta["dut"] = self.dut.metadata()
        return json.dumps({"meta": meta, "primary_failure": self.primary_failure,
                           "phases": [r.__dict__ for r in self.results],
                           "recorded_at_unix": time.time()}, indent=2)

    @property
    def ok(self):
        return all(r.status in ("pass", "skipped") for r in self.results) and not self.primary_failure
