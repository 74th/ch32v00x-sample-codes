import pytest
from ch32hil.watchdog import analyse_signature


def test_watchdog_signature_three_then_six():
    signal = '0' * 10 + ('1' * 7 + '0' * 7) * 3 + '0' * 60 + ('1' * 7 + '0' * 7) * 6 + '0' * 10
    result = analyse_signature(signal, 15000)
    assert len(result['high_us']) == 9 and result['gap_us'] >= 400000


@pytest.mark.parametrize('signal', ['0' * 300, ('1' * 7 + '0' * 7) * 9, 'bad'])
def test_wrong_or_incomplete_signature_rejected(signal):
    with pytest.raises(ValueError):
        analyse_signature(signal, 15000)


def test_power_loss_like_repeated_initial_signature_is_not_watchdog():
    # Two power-on signatures contain six pulses, not the 3+6 IWDG signature.
    power_cycles = '0' * 10 + ('1' * 7 + '0' * 7) * 3 + '0' * 60 + ('1' * 7 + '0' * 7) * 3 + '0' * 10
    with pytest.raises(ValueError, match='3\\+6'):
        analyse_signature(power_cycles, 15000)
