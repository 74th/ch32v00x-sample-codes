"""Shared helpers for official WCH SDK HIL tests (reuses the fixture helpers of the Arduino tests)."""
from arduino.common import *  # noqa: F401,F403
from arduino import common as _base
from arduino.common import __all__  # noqa: F401


def new_run(hil_device, sample, **extra):
    run = _base.new_run(hil_device, sample, **extra)
    run.meta.pop("core", None)
    run.meta.pop("arduino_cli", None)
    run.meta.pop("fqbn", None)
    return run
