import pytest
from ch32hil.dut import CmdResult, Dut, DutError, check_flash_output, check_readback_output

GOOD = "Detected CH32V003\nImage written.\n"


@pytest.mark.parametrize("res", [
    CmdResult(0, ""),                                   # disconnected, exit 0
    CmdResult(0, "No detected chip.\n"),
    CmdResult(0, "Detected CH32V006\nImage written.\n"),  # wrong device
    CmdResult(0, "Detected CH32V003\n"),                 # no write confirmation
    CmdResult(0, GOOD + "Unknown chip\n"),
    CmdResult(1, GOOD),
])
def test_flash_false_success_rejected(res):
    with pytest.raises(DutError) as e:
        check_flash_output(res)
    assert e.value.phase == "flash"


def test_flash_ok():
    check_flash_output(CmdResult(0, GOOD))


def test_readback_requires_detection():
    with pytest.raises(DutError):
        check_readback_output(CmdResult(0, ""))


def make_dut(tmp_path, runner):
    (tmp_path / "main.bin").write_bytes(b"\x01\x02\x03")
    return Dut(tmp_path, run=runner, minichlink=tmp_path / "mc", ready_timeout=0)


def test_readback_mismatch(tmp_path):
    def runner(argv, t):
        (tmp_path / "readback.bin").write_bytes(b"\x01\x02\xff")
        return CmdResult(0, "Detected CH32V003\n")
    with pytest.raises(DutError, match="differ"):
        make_dut(tmp_path, runner).readback(tmp_path)


def test_readback_match_and_size_arg(tmp_path):
    seen = []
    def runner(argv, t):
        seen.append(argv)
        (tmp_path / "readback.bin").write_bytes(b"\x01\x02\x03")
        return CmdResult(0, "Detected CH32V003\n")
    make_dut(tmp_path, runner).readback(tmp_path)
    assert "3" in seen[0]


def test_timeout_propagates(tmp_path):
    def runner(argv, t):
        raise DutError("timeout", "slow")
    with pytest.raises(DutError):
        make_dut(tmp_path, runner).flash()


def test_missing_artifact(tmp_path):
    with pytest.raises(DutError, match="missing"):
        Dut(tmp_path, run=lambda a, t: None, ready_timeout=0).flash()


def test_uses_pinned_minichlink():
    from ch32hil.dut import MINICHLINK
    assert MINICHLINK.parts[-4:-1] == ("externals", "ch32fun", "minichlink")


@pytest.mark.parametrize('output', [
    'Detected CH32V0034\nImage written.\n',
    'Detected CH32V003\nDetected CH32V006\nImage written.\n',
    'No detected chip.\n',
])
def test_ambiguous_device_output_rejected(output):
    with pytest.raises(DutError):
        check_flash_output(CmdResult(0, output))


def test_reset_requires_detected_chip(tmp_path):
    dut = Dut(tmp_path, run=lambda args, timeout: CmdResult(0, ''), ready_timeout=0)
    with pytest.raises(DutError, match='expected only'):
        dut.reset()
    dut.run = lambda args, timeout: CmdResult(0, 'Detected CH32V003\n')
    dut.reset()


PROBE_OK = "Found WCH Link\nWCH Programmer is LinkE version 2.22\nDetected CH32V003\n"


def test_wait_ready_retries_until_detected(tmp_path):
    calls = []

    def runner(args, timeout):
        calls.append(args[-1])
        return CmdResult(0, PROBE_OK) if len(calls) == 3 else CmdResult(0, "Could not find any programmers\n")

    dut = Dut(tmp_path, run=runner, minichlink=tmp_path / "mc", ready_timeout=30, sleep=lambda s: None)
    dut.wait_ready("flash")
    assert calls == ["-i"] * 3


def test_wait_ready_times_out_with_phase(tmp_path):
    dut = Dut(tmp_path, run=lambda a, t: CmdResult(0, ""), minichlink=tmp_path / "mc",
              ready_timeout=0.05, ready_interval=0.01)
    with pytest.raises(DutError) as e:
        dut.wait_ready("flash")
    assert e.value.phase == "flash" and "not detected" in str(e.value)


def test_wait_ready_rejects_wrong_chip(tmp_path):
    out = "Found WCH Link\nDetected CH32V006\n"
    dut = Dut(tmp_path, run=lambda a, t: CmdResult(0, out), minichlink=tmp_path / "mc", ready_timeout=5)
    with pytest.raises(DutError):
        dut.wait_ready("flash")
