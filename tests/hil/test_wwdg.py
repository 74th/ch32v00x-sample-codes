"""HIL: standard ch32fun wwdg (shared CH32V002/CH32V006 source; not in the book): window watchdog, three builds.

DESTRUCTIVE: rebuilds and flashes the DUT per build and re-flashes the known `blink_and_read` sample at the end of each.
Run: uv run pytest --hil --hil-device ch32v002 tests/hil/test_wwdg.py
Flow, judgement and limits: tests/hil/wwdg_flow.py and ch32hil/wwdg.py.
"""
import pytest

from wwdg_flow import run_mode

pytestmark = [pytest.mark.hil, pytest.mark.watchdog]


@pytest.mark.parametrize("mode", [0, 1, 2], ids=["mode0_feed_in_window", "mode1_feed_too_early", "mode2_no_feed"])
def test_wwdg(request, hil_device, hil_config, hil_dut, mode):
    run_mode(request, hil_device, hil_config, hil_dut, mode, "blink_and_read", "wwdg")
