"""Safety gate: HIL tests run only when explicitly selected with `--hil`."""
import pytest

from ch32hil import config, devices
from ch32hil.dut import Dut


def pytest_addoption(parser):
    parser.addoption("--hil", action="store_true", default=False,
                     help="run hardware-in-the-loop tests (WRITES to connected Pico/DUT)")
    parser.addoption("--hil-device", default=devices.DEFAULT,
                     help=f"HIL target device {sorted(devices.DEVICES)} (default {devices.DEFAULT})")
    parser.addoption("--hil-config", default=None,
                     help="HIL configuration file (default: the selected device's configuration)")
    parser.addoption("--hil-port", default=None, help="Pico serial device (explicit)")
    parser.addoption("--hil-run-dir", default=None, help="directory for machine-readable run artifacts")


def pytest_configure(config):
    try:
        devices.get(config.getoption("--hil-device"))
    except devices.DeviceError as exc:
        raise pytest.UsageError(str(exc)) from None


def pytest_collection_modifyitems(config, items):
    if config.getoption("--hil"):
        return
    skip = pytest.mark.skip(reason="HIL not selected; pass --hil to touch hardware")
    for item in items:
        if "hil" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def hil_selection(request):
    """(Device, config path, config); a dut.device/--hil-device mismatch errors before hardware access."""
    try:
        return config.select(request.config.getoption("--hil-device"),
                             request.config.getoption("--hil-config"))
    except (config.ConfigError, devices.DeviceError) as exc:
        pytest.fail(f"HIL configuration error (no hardware touched): {exc}", pytrace=False)


@pytest.fixture
def hil_device(hil_selection):
    return hil_selection[0]


@pytest.fixture
def hil_config(hil_selection):
    return hil_selection[2]


@pytest.fixture
def hil_dut(hil_device, hil_config):
    """hil_dut(sample) -> Dut for the selected device, or a reasoned skip when the sample is unavailable."""
    def make(sample):
        reason = hil_device.skip_reason(sample)
        if reason:
            pytest.skip(reason)
        print(f"HIL DEVICE: {hil_device.part} ({hil_device.name}); sample={sample}; "
              f"will BUILD, FLASH (overwrites DUT firmware) and READBACK")
        return Dut(hil_device.sample_dir(sample), target=hil_device.name)
    return make
