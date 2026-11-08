"""scripts/ch32fun.sh flash with a simulated programmer (CH32FUN_TEST_MINICHLINK): no hardware is touched."""
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/ch32fun.sh"
SAMPLE = ROOT / "samples_ch32v00x_ch32fun/blink_and_read"
# Synthetic identification words (little-endian): type is the upper 12 bits. Not measured on real chips.
ID = {"v002": "20 06 20 00", "v006": "20 06 60 00", "v003": "30 05 30 00"}

FAKE = r'''#!/usr/bin/env bash
echo "$*" >> "$FAKE_LOG"
case "$*" in
  *0x1ffff704*) [[ -n "$FAKE_ID" ]] && echo "1ffff704: $FAKE_ID"; echo "$FAKE_DETECT_ID"; exit "${FAKE_ID_RC:-0}";;
  *-w*) echo "$FAKE_DETECT_WRITE"; [[ "$FAKE_WRITTEN" == 1 ]] && echo "Image written."; exit "${FAKE_WRITE_RC:-0}";;
  *-r*) out="$2"; if [[ "$FAKE_READBACK" == same ]]; then cp "$FAKE_BIN" "$out"; else printf 'x' > "$out"; fi
        echo "$FAKE_DETECT_WRITE"; exit 0;;
esac
'''


@pytest.fixture
def artifact():
    made = []

    def make(target):
        path = SAMPLE / "build" / target / "main.bin"
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"\x01\x02\x03\x04")
            made.append(path)
        return path
    yield make
    for path in made:
        path.unlink()


def flash(tmp_path, artifact, target, **env):
    fake = tmp_path / "minichlink"
    fake.write_text(FAKE)
    fake.chmod(0o755)
    log = tmp_path / "calls.log"
    log.write_text("")
    bin_path = artifact(target)
    base = {"CH32FUN_TEST_MINICHLINK": str(fake), "FAKE_LOG": str(log), "FAKE_BIN": str(bin_path),
            "FAKE_ID": ID["v006"], "FAKE_DETECT_ID": "Detected CH32V006", "FAKE_DETECT_WRITE": "Detected CH32V006",
            "FAKE_WRITTEN": "1", "FAKE_READBACK": "same"}
    base.update({k.upper(): v for k, v in env.items()})
    r = subprocess.run([str(SCRIPT), "flash", target], capture_output=True, text=True, env={**os.environ, **base})
    return r, log.read_text()


def wrote(calls):
    return any(" -w " in f" {line} " or line.startswith("-w ") for line in calls.splitlines())


def test_ch32v006_ok_requires_identifier_then_write_then_full_readback(tmp_path, artifact):
    r, calls = flash(tmp_path, artifact, "ch32v006")
    size = artifact("ch32v006").stat().st_size
    assert r.returncode == 0, r.stdout + r.stderr
    assert "READBACK MATCHED" in r.stdout and "CH32V006 identifier: 0x00600620" in r.stdout
    lines = calls.splitlines()
    assert "0x1ffff704" in lines[0] and lines[1].startswith("-w") and lines[2].startswith("-r") and f"flash {size} -b" in lines[2]


@pytest.mark.parametrize("env", [
    {"fake_id": ID["v002"]},                    # CH32V002 connected while CH32V006 selected
    {"fake_id": ID["v003"]},
    {"fake_id": ""},                             # unreadable identification area
    {"fake_id_rc": "1"},                         # programmer error
    {"fake_detect_id": "No detected chip."},    # DUT not connected, exit 0
    {"fake_id": "20 06"},                        # truncated read
])
def test_ch32v006_stops_before_write(tmp_path, artifact, env):
    r, calls = flash(tmp_path, artifact, "ch32v006", **env)
    assert r.returncode != 0 and "FLASH FAILED" in r.stderr
    assert not wrote(calls)


@pytest.mark.parametrize("env,msg", [
    ({"fake_detect_write": "Detected CH32V002"}, "did not confirm"),    # mix-up reported at write time
    ({"fake_detect_write": "No detected chip."}, "did not confirm"),
    ({"fake_written": "0"}, "did not confirm"),                         # exit 0 without 'Image written.'
    ({"fake_write_rc": "1"}, "did not confirm"),
    ({"fake_readback": "differs"}, "readback is not identical"),        # false success
])
def test_ch32v006_write_phase_failures(tmp_path, artifact, env, msg):
    r, _ = flash(tmp_path, artifact, "ch32v006", **env)
    assert r.returncode != 0 and msg in r.stderr and "FLASH OK" not in r.stdout


def test_ch32v002_selected_with_ch32v006_connected_stops_before_write(tmp_path, artifact):
    r, calls = flash(tmp_path, artifact, "ch32v002", fake_id=ID["v006"], fake_detect_id="Detected CH32V006",
                     fake_detect_write="Detected CH32V006")
    assert r.returncode != 0 and not wrote(calls)


def test_ch32v002_ok_keeps_existing_behaviour_without_readback(tmp_path, artifact):
    r, calls = flash(tmp_path, artifact, "ch32v002", fake_id=ID["v002"], fake_detect_write="Detected CH32V002")
    assert r.returncode == 0 and "FLASH OK" in r.stdout
    assert not any(line.startswith("-r") and "0x1ffff704" not in line for line in calls.splitlines())


def test_missing_artifact_is_refused_without_programmer_access(tmp_path):
    path = SAMPLE / "build/ch32v006/main.bin"
    backup = path.read_bytes() if path.exists() else None
    if backup is not None:
        path.unlink()
    try:
        log = tmp_path / "calls.log"
        r = subprocess.run([str(SCRIPT), "flash", "ch32v006"], capture_output=True, text=True,
                           env={**os.environ, "FAKE_LOG": str(log), "CH32FUN_TEST_MINICHLINK": "/nonexistent"})
        assert r.returncode != 0 and "artifact" in r.stderr and not log.exists()
    finally:
        if backup is not None:
            path.write_bytes(backup)
