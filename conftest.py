"""Safety gate: HIL tests run only when explicitly selected with `--hil`."""
import pytest


def pytest_addoption(parser):
    parser.addoption("--hil", action="store_true", default=False,
                     help="run hardware-in-the-loop tests (WRITES to connected Pico/DUT)")
    parser.addoption("--hil-config", default="hil/configs/gpio_blink.json",
                     help="HIL configuration file")
    parser.addoption("--hil-port", default=None, help="Pico serial device (explicit)")
    parser.addoption("--hil-run-dir", default=None, help="directory for machine-readable run artifacts")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--hil"):
        return
    skip = pytest.mark.skip(reason="HIL not selected; pass --hil to touch hardware")
    for item in items:
        if "hil" in item.keywords:
            item.add_marker(skip)
