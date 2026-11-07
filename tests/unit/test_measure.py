import unittest
from unittest.mock import patch
import io
import sys
from types import SimpleNamespace
import measure  # hardware/pico-tester/measure.py (pythonpath in pyproject)


def response(samples):
    return 'PICO_GPIO_V1 10000 ' + samples


class Tests(unittest.TestCase):
    def test_discovery_waits_for_device(self):
        pico = SimpleNamespace(device='/dev/example', vid=0x2e8a, pid=0x000a)
        with patch.object(measure.list_ports, 'comports', side_effect=[[], [pico]]), patch.object(measure.time, 'sleep'):
            self.assertEqual(measure.discover(1), '/dev/example')

    def test_discovery_timeout(self):
        with patch.object(measure.list_ports, 'comports', return_value=[]):
            with self.assertRaises(TimeoutError):
                measure.discover(0)

    def test_matching_pattern(self):
        self.assertTrue(measure.analyse(response('0' * 50 + '1' * 50 + '0' * 50 + '1' * 50 + '0' * 50 + '1' * 50))[0])

    def test_constant_and_wrong_period(self):
        self.assertFalse(measure.analyse(response('0' * 300))[0])
        self.assertFalse(measure.analyse(response('01' * 150))[0])

    def test_bad_frame(self):
        with self.assertRaises(ValueError):
            measure.analyse(response('0' * 299))

    def test_timeout(self):
        class EmptyDevice:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def reset_input_buffer(self): pass
            def write(self, data): pass
            def read(self, count): return b''
        with patch.object(sys, 'argv', ['measure.py', '--port', 'fake', '--timeout', '0.001']), \
             patch.object(measure.serial, 'Serial', return_value=EmptyDevice()), \
             patch('sys.stderr', new_callable=io.StringIO):
            self.assertEqual(measure.main(), 2)


if __name__ == '__main__':
    unittest.main()


def test_exit_codes_for_received_frames(capsys):
    class Device:
        def __init__(self, line): self.line = line
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def reset_input_buffer(self): pass
        def write(self, data): assert data == b's'
        def read(self, count): return self.line

    cases = [
        (response('0' * 50 + '1' * 50 + '0' * 50 + '1' * 50 + '0' * 50 + '1' * 50), 0),
        (response('0' * 300), 1),
        ('NOT_A_FRAME', 3),
    ]
    for line, expected in cases:
        with patch.object(sys, 'argv', ['measure.py', '--port', 'fake']), \
             patch.object(measure.serial, 'Serial', return_value=Device((line + '\n').encode())):
            assert measure.main() == expected
    capsys.readouterr()
