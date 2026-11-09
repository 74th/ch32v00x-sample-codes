"""HIL: CH32V006-only WCH SDK samples (not in the book): usart2, opa, tim3, tkey. Skipped on every other device.

DESTRUCTIVE: rebuilds and flashes the DUT. Run: uv run pytest --hil --hil-device ch32v006 --hil-framework wch tests/hil/wch/test_v006_only.py
Flow and judgements (shared with the ch32fun versions): tests/hil/v006_only_flow.py and ch32hil/v006_only.py.
"""
import pytest

import v006_only_flow as flow

from .common import new_run

pytestmark = [pytest.mark.hil, pytest.mark.wch]
PREFIX = "wch_"


@pytest.mark.pwm
def test_wch_tim3(request, hil_device, hil_config, hil_dut):
    flow.run_tim3(request, hil_device, hil_config, hil_dut, new_run, PREFIX)


def test_wch_usart2(request, hil_device, hil_config, hil_dut):
    flow.run_usart2(request, hil_device, hil_config, hil_dut, new_run, PREFIX)


@pytest.mark.adc
@pytest.mark.parametrize("gain", [4, 8], ids=["gain4", "gain8"])
def test_wch_opa(request, hil_device, hil_config, hil_dut, gain):
    flow.run_opa(request, hil_device, hil_config, hil_dut, new_run, PREFIX, gain)


@pytest.mark.adc
def test_wch_tkey(request, hil_device, hil_config, hil_dut):
    flow.run_tkey(request, hil_device, hil_config, hil_dut, new_run, PREFIX)
