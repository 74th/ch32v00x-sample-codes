from pathlib import Path

from ch32hil.config import load
from ch32hil.wiring import problems

ROOT = Path(__file__).resolve().parents[2]


def test_wiring_and_config_match():
    cfg = load(ROOT / 'hil/configs/gpio_blink.json')
    doc = (ROOT / 'hardware/wiring-proposal.md').read_text()
    assert problems(cfg, doc) == []


def test_wrong_pico_pin_and_wrong_pullup_are_detected():
    cfg = load(ROOT / 'hil/configs/gpio_blink.json')
    doc = (ROOT / 'hardware/wiring-proposal.md').read_text()
    broken = doc.replace('GP5 (7)', 'GP5 (8)', 1).replace('4.7 kΩ pull-up', '10 kΩ pull-up', 1)
    failures = problems(cfg, broken)
    assert any('BLINK: pico_no' in e for e in failures)
    assert any('I2C_SDA: pull_up_ohm' in e for e in failures)
