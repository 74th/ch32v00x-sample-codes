"""Shared helpers for official WCH SDK HIL tests (reuses the fixture helpers of the Arduino tests)."""
from arduino.common import *  # noqa: F401,F403
from arduino import common as _base
from arduino.common import __all__  # noqa: F401

SDK = "openwch/ch32v003 4e1b7437ada5d3ae8831a6f4b811a6320e4e23c7; WCH GCC 15.2.0"


def new_run(hil_device, sample, **extra):
    run = _base.new_run(hil_device, sample, **extra)
    run.meta.pop("core", None)
    run.meta.pop("arduino_cli", None)
    run.meta["sdk"] = SDK
    return run
