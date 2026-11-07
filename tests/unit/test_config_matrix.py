import copy, json
from pathlib import Path
import pytest
from ch32hil import config, matrix

ROOT = Path(__file__).resolve().parents[2]
BASE = json.loads((ROOT / "hil/configs/gpio_blink.json").read_text())


def bad(**mut):
    c = copy.deepcopy(BASE); c.update(mut); return c


def test_shipped_config_valid():
    config.validate(copy.deepcopy(BASE))


@pytest.mark.parametrize("cfg,msg", [
    (lambda: {k: v for k, v in BASE.items() if k != "voltage"}, "missing field"),
    (lambda: bad(readback="sometimes"), "readback"),
    (lambda: bad(voltage={"dut_supply": 5.0, "pico_io": 5.0}), "unsafe"),
    (lambda: bad(voltage={"dut_supply": 3.3, "pico_io": 1.8}), "differ"),
    (lambda: bad(power_connection_pico_to_dut=True), "power"),
    (lambda: bad(pins={"A": {"dut": "PC0", "pico_gpio": 0}, "B": {"dut": "PC0", "pico_gpio": 1}}), "DUT pin"),
    (lambda: bad(pins={"A": {"dut": "PC0", "pico_gpio": 0}, "B": {"dut": "PC1", "pico_gpio": 0}}), "Pico GPIO0"),
    (lambda: bad(pins={"A": {"dut": "PC0", "pico_gpio": 25}}), "reserved"),
    (lambda: bad(timeouts={"measure": 0}), "timeouts"),
])
def test_invalid_configs(cfg, msg):
    with pytest.raises(config.ConfigError, match=msg):
        config.validate(cfg())


def test_matrix_accounts_for_every_book_sample():
    book = ROOT / "externals/ch32v003-book-code"
    if not book.is_dir():
        pytest.skip("book-code reference not checked out")
    entries = matrix.load(ROOT / "hil/matrix.json")
    assert matrix.problems(entries, book_dir=book) == []


def test_matrix_detects_unaccounted_and_bad_entries(tmp_path):
    (tmp_path / "new-ch32fun").mkdir()
    entries = [{"book_sample": None, "class": "extralibs-excluded", "state": "build-only"}]
    p = matrix.problems(entries, book_dir=tmp_path)
    assert any("not accounted" in x for x in p) and any("excluded" in x for x in p)


def test_rejects_unrecorded_power_and_protection():
    for mutate in (
        lambda c: c['voltage'].pop('common_ground'),
        lambda c: c['voltage'].update(power_pins_connected=True),
        lambda c: c['voltage'].update(dut_supply=float('nan')),
        lambda c: c['pins']['BLINK'].pop('series_ohm'),
        lambda c: c['pins']['BLINK'].update(dut_physical=11),
        lambda c: c['pins']['BLINK'].update(pico_physical=1),
        lambda c: c['dut'].update(sample='../other'),
        lambda c: c['pico'].pop('usb_vid'),
    ):
        c = copy.deepcopy(BASE)
        mutate(c)
        with pytest.raises(config.ConfigError):
            config.validate(c)


def test_bus_and_rc_require_protection():
    for net, key, value in (
        ('I2C_SDA', 'pull_up_ohm', 0),
        ('I2C_SCL', 'pull_up_to', 'pico_vbus'),
        ('ADC_A0', 'capacitance_nf', 0),
    ):
        c = copy.deepcopy(BASE)
        c['pins'][net][key] = value
        with pytest.raises(config.ConfigError):
            config.validate(c)


@pytest.mark.parametrize('broken', [None, [], {'readback': []}])
def test_malformed_top_level_is_config_error(broken):
    with pytest.raises(config.ConfigError):
        config.validate(broken)


def test_malformed_nested_pin_is_config_error():
    c = copy.deepcopy(BASE)
    c['pins']['BLINK']['dut'] = []
    with pytest.raises(config.ConfigError):
        config.validate(c)
