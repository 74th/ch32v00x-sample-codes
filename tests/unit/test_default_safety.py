"""Plain `pytest` must never touch hardware."""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_hil_is_skipped_without_flag():
    p = subprocess.run([sys.executable, "-m", "pytest", "tests/hil", "-q", "-rs", "-p", "no:cacheprovider"],
                       cwd=ROOT, capture_output=True, text=True)
    assert p.returncode == 0, p.stdout
    assert "HIL not selected" in p.stdout and "passed" not in p.stdout.split("\n")[-2]


def test_hil_tests_are_marked():
    text = (ROOT / "tests/hil/test_blink_and_read.py").read_text()
    assert "pytest.mark.hil" in text
