import re
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


def test_shipped_matrix_states_are_backed_by_tests_and_logs():
    entries = matrix.load(ROOT / "hil/matrix.json")
    assert matrix.problems(entries, samples_dir=ROOT / "samples_ch32v003_ch32fun", root=ROOT) == []


def test_every_hil_test_is_referenced_by_matrix():
    import re
    referenced = {ref for e in matrix.load(ROOT / "hil/matrix.json") for ref in e.get("hil_tests", []) + e.get("hil_tests_variants", [])}
    defined = {f"tests/hil/{p.name}::{name}"
               for p in (ROOT / "tests/hil").glob("test_*.py")
               for name in re.findall(r"(?m)^def (test_\w+)\(", p.read_text())}
    assert defined - referenced == set()


def test_hil_verified_requires_tests_and_existing_evidence(tmp_path):
    base = {"book_sample": None, "class": "equivalent-standard-ch32fun", "sample": "x", "state": "hil-verified"}
    p = matrix.problems([dict(base)])
    assert any("without hil_tests" in x for x in p) and any("without evidence" in x for x in p)
    p = matrix.problems([dict(base, hil_tests=["tests/hil/none.py::test_x"], evidence=["okf/log/none.md"])],
                        root=tmp_path)
    assert any("hil test not found" in x for x in p) and any("evidence log not found" in x for x in p)


def _helper_entry(**mut):
    e = {"book_sample": None, "class": "helper-verification", "peripheral": "i2c", "state": "not-automated",
         "sample": "i2c_slave_helper", "helpers": ["examples/i2c_slave/i2c_slave.h"],
         "requires": ["i2c-master"], "criteria": "x"}
    e.update(mut)
    return e


def test_helper_verification_entry_valid_and_strict():
    assert matrix.problems([_helper_entry()]) == []
    for key in ("sample", "helpers", "requires", "criteria"):
        p = matrix.problems([_helper_entry(**{key: None})])
        assert any(f"without {key}" in x for x in p), key
    p = matrix.problems([_helper_entry(helpers=["extralibs/ssd1306_spi.h"])])
    assert any("unknown helper" in x for x in p)
    p = matrix.problems([_helper_entry(state="hil-verified")])
    assert any("without hil_tests" in x for x in p) and any("without evidence" in x for x in p)


ARDUINO_MATRICES = ["hil/matrix_arduino.json", "hil/matrix_ch32v002_arduino.json"]


@pytest.mark.parametrize("path", ARDUINO_MATRICES)
def test_arduino_matrix_lists_every_arduino_core_sketch(path):
    book = ROOT / "externals/ch32v003-book-code"
    if not book.is_dir():
        pytest.skip("book-code reference not checked out")
    entries = matrix.load(ROOT / path)
    assert matrix.problems(entries, book_dir=book, framework="arduino") == []
    assert len({e["book_sample"] for e in entries}) == len(entries) == 10
    # arduino-wch32v003 (another core) sketches are not part of the Arduino Core CH32 matrix
    assert not any("arduino_ch32v003" in e["book_sample"] or "wch32v003" in e["book_sample"] for e in entries)


@pytest.mark.parametrize("path", ARDUINO_MATRICES)
def test_arduino_matrix_hil_verified_requires_tests_and_evidence(path):
    entries = copy.deepcopy(matrix.load(ROOT / path))
    entries[0].update(state="hil-verified")
    entries[0].pop("hil_tests", None)
    entries[0].pop("evidence", None)
    p = matrix.problems(entries, root=ROOT, framework="arduino")
    assert any("without hil_tests" in x for x in p) and any("without evidence" in x for x in p)


def test_arduino_matrix_detects_unaccounted_sketch(tmp_path):
    (tmp_path / "new-arduino_core_ch32").mkdir()
    (tmp_path / "other-arduino_ch32v003").mkdir()
    p = matrix.problems([], book_dir=tmp_path, framework="arduino")
    assert p == ["book-code sample not accounted for: new-arduino_core_ch32"]


def test_every_arduino_hil_test_is_referenced_by_matrix():
    import re
    referenced = {ref for path in ARDUINO_MATRICES + ["hil/matrix_ch32v006_arduino.json"] for e in matrix.load(ROOT / path) for ref in e.get("hil_tests", []) + e.get("hil_tests_variants", [])}
    defined = {f"tests/hil/arduino/{p.name}::{name}"
               for p in (ROOT / "tests/hil/arduino").glob("test_*.py")
               for name in re.findall(r"(?m)^def (test_\w+)\(", p.read_text())}
    assert defined - referenced == set()


WCH_BOOK_DIRS = ["adc", "adc_dma", "blink_and_read", "i2c_master", "i2c_slave", "pwm", "sleep_mode_blink",
                 "spi_master", "standby_mode_blink", "timer_blink", "timer_dma", "uart", "watchdogtimer"]


def test_wch_matrix_tracks_all_thirteen_book_examples_one_to_one():
    entries = matrix.load(ROOT / "hil/matrix_wch.json")
    assert sorted(e["book_sample"] for e in entries) == sorted(f"{d}-wch_sdk" for d in WCH_BOOK_DIRS)
    assert len({e["sample"] for e in entries}) == 13
    book = ROOT / "externals/ch32v003-book-code"
    if book.is_dir():
        assert matrix.problems(entries, book_dir=book, framework="wch") == []


def test_wch_matrix_detects_missing_book_example(tmp_path):
    for d in WCH_BOOK_DIRS + ["extra"]:
        (tmp_path / f"{d}-wch_sdk").mkdir()
    entries = matrix.load(ROOT / "hil/matrix_wch.json")
    p = matrix.problems(entries, book_dir=tmp_path, framework="wch")
    assert p == ["book-code sample not accounted for: extra-wch_sdk"]


def _readme_rows(path):
    rows = {}
    for line in Path(path).read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        m = line.startswith("| `") and re.match(r"`(\S+-wch_sdk)`", cells[0])
        if m:
            rows[m.group(1)] = cells
    return rows


@pytest.mark.parametrize("readme,matrix_file,state_col", [
    ("samples_ch32v003_wch/README.md", "hil/matrix_wch.json", 2),
    ("samples_ch32v002_wch/README.md", "hil/matrix_ch32v002_wch.json", 2),
])
def test_wch_readme_table_matches_matrix(readme, matrix_file, state_col):
    """All 13 rows: README state (and, for 003, the evidence logs) equal the matrix; nothing is claimed beyond it."""
    entries = {e["book_sample"]: e for e in matrix.load(ROOT / matrix_file)}
    rows = _readme_rows(ROOT / readme)
    assert set(rows) == set(entries) and len(rows) == 13
    for book, e in entries.items():
        assert rows[book][1] == f"`{e['sample']}`"
        assert rows[book][state_col] == e["state"], (book, rows[book][state_col], e["state"])
        if readme.startswith("samples_ch32v003"):
            for log in e.get("evidence", []):
                assert Path(log).name in rows[book][3], (book, log)
            if e["state"] != "hil-verified":
                assert not e.get("evidence"), book


def test_hil_verified_wch_rows_have_a_checkable_basis():
    for matrix_file in ("hil/matrix_wch.json", "hil/matrix_ch32v002_wch.json"):
        entries = matrix.load(ROOT / matrix_file)
        assert matrix.problems(entries, root=ROOT, samples_dir=None, framework="wch") == []
        for e in entries:
            if e["state"] == "hil-verified":
                assert e.get("hil_tests") and e.get("evidence") and e.get("criteria"), e["sample"]


def test_ch32v006_matrix_covers_every_ch32v002_row_without_borrowed_results():
    v002 = matrix.load(ROOT / "hil/matrix_ch32v002.json")
    v006 = matrix.load(ROOT / "hil/matrix_ch32v006.json")
    assert [e["sample"] for e in v006] == [e["sample"] for e in v002] and len(v006) == 13
    assert matrix.coverage_problems(matrix.load(ROOT / "hil/matrix.json"), v006) == []
    assert matrix.problems(v006, samples_dir=ROOT / "samples_ch32v00x_ch32fun", root=ROOT) == []
    # CH32V002 results are never carried over: a hil-verified row needs its own evidence log naming CH32V006.
    for e in v006:
        assert e["state"] in {"build-only", "excluded"} or all("ch32v006" in log for log in e["evidence"]), e["sample"]
        assert "gpio_input" != e["sample"] or e["state"] == "excluded"


def _v006_rows(name):
    return matrix.load(ROOT / f"hil/matrix_ch32v006_{name}.json")


def test_ch32v006_arduino_matrix_has_ten_rows_without_borrowed_results():
    v002 = matrix.load(ROOT / "hil/matrix_ch32v002_arduino.json")
    v006 = _v006_rows("arduino")
    assert [e["sample"] for e in v006] == [e["sample"] for e in v002] and len(v006) == 10
    assert matrix.problems(v006, samples_dir=ROOT / "samples_ch32v006_arduino", root=ROOT, framework="arduino") == []
    for e in v006:
        assert e["state"] in {"not-ported", "build-only", "excluded"} or \
            (e.get("hil_tests") and e.get("evidence") and all("ch32v006" in log for log in e["evidence"])), e["sample"]


def test_ch32v006_wch_matrix_has_thirteen_rows_without_borrowed_results():
    v002 = matrix.load(ROOT / "hil/matrix_ch32v002_wch.json")
    v006 = _v006_rows("wch")
    assert [e["sample"] for e in v006] == [e["sample"] for e in v002] and len(v006) == 13
    assert matrix.problems(v006, samples_dir=ROOT / "samples_ch32v006_wch", root=ROOT, framework="wch") == []
    assert all("003_state" not in e and "002_state" not in e for e in v006)
    for e in v006:
        assert e["state"] in {"not-ported", "build-only", "excluded"} or \
            (e.get("hil_tests") and e.get("evidence") and all("ch32v006" in log for log in e["evidence"])), e["sample"]


def test_ch32v006_matrix_rows_that_are_skipped_state_a_reason():
    for name in ("arduino", "wch"):
        for e in _v006_rows(name):
            if e["state"] in ("not-ported", "excluded"):
                assert e.get("note"), (name, e["sample"])
