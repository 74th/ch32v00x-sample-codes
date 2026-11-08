"""HIL: official WCH SDK wwdg (not in the book; based on the official EVT EXAM/WWDG): window watchdog, three builds.

DESTRUCTIVE: rebuilds and flashes the DUT per build and re-flashes the known `blink` sample at the end of each.
Run: uv run pytest --hil --hil-framework wch tests/hil/wch/test_wwdg.py   (add --hil-device ch32v00x)
Flow, judgement and limits: tests/hil/wwdg_flow.py and ch32hil/wwdg.py.
"""
import pytest

from wwdg_flow import run_mode

pytestmark = [pytest.mark.hil, pytest.mark.wch, pytest.mark.watchdog]


@pytest.mark.parametrize("mode", [0, 1, 2], ids=["mode0_feed_in_window", "mode1_feed_too_early", "mode2_no_feed"])
def test_wch_wwdg(request, hil_device, hil_config, hil_dut, mode):
    run_mode(request, hil_device, hil_config, hil_dut, mode, "blink", "wch_wwdg")
