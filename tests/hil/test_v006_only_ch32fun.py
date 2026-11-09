"""HIL: CH32V006-only standard ch32fun samples (not in the book): usart2, opa, tim3, tkey. Skipped on every other device.

DESTRUCTIVE: rebuilds and flashes the DUT. Run: uv run pytest --hil --hil-device ch32v006 tests/hil/test_v006_only_ch32fun.py
Same behaviour and judgements as the WCH SDK versions (tests/hil/wch/test_v006_only.py); flow: tests/hil/v006_only_flow.py.
"""
import pytest

import v006_only_flow as flow
from arduino.common import new_run

pytestmark = [pytest.mark.hil]


@pytest.mark.pwm
def test_tim3(request, hil_device, hil_config, hil_dut):
    flow.run_tim3(request, hil_device, hil_config, hil_dut, new_run, "")


def test_usart2(request, hil_device, hil_config, hil_dut):
    flow.run_usart2(request, hil_device, hil_config, hil_dut, new_run, "")


@pytest.mark.adc
@pytest.mark.parametrize("gain", [4, 8], ids=["gain4", "gain8"])
def test_opa(request, hil_device, hil_config, hil_dut, gain):
    flow.run_opa(request, hil_device, hil_config, hil_dut, new_run, "", gain)


@pytest.mark.adc
def test_tkey(request, hil_device, hil_config, hil_dut):
    flow.run_tkey(request, hil_device, hil_config, hil_dut, new_run, "")
