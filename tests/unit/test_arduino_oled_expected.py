"""Host check of the i2c_oled expected-buffer harness (tests/unit/arduino_oled, tests/hil/arduino/oled_expected.py)."""
import re
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests/hil/arduino"))
from oled_expected import expected_pages, library_dir  # noqa: E402

SKETCH = ROOT / "samples_ch32v003_arduino/i2c_oled/i2c_oled.ino"


@pytest.mark.skipif(library_dir() is None or shutil.which("g++") is None,
                    reason="OLED library not installed (build samples_*_arduino/i2c_oled) or no g++")
def test_rendered_buffer_contains_the_sketch_bitmap(tmp_path):
    pages = expected_pages(SKETCH, tmp_path)
    assert len(pages) == 4 and all(len(p) == 128 for p in pages)
    src = SKETCH.read_text()
    body = src[src.index("BUNCHO_74TH[]"):]
    body = body[body.index("{") + 1:body.index("};")]
    bitmap = bytes(int(x, 16) for x in re.findall(r"0x([0-9a-fA-F]{2})", body))
    assert len(bitmap) == 128                       # 32x32, vertical bytes, 4 pages x 32 columns
    for page in range(4):                           # draw_bitmap_P(0, 0, 32, 32, ...) is page aligned
        assert pages[page][:32] == bitmap[page * 32:(page + 1) * 32]
    assert any(pages[page][60:118] != bytes(58) for page in range(4))   # text and rectangle area is not blank
