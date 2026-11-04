import unittest

from rra_telemetry.status import classify_state


class StateTests(unittest.TestCase):
    def test_unknown(self):
        self.assertEqual(classify_state(False, None, 100, 5)[0], 2)

    def test_recent_disconnected(self):
        self.assertEqual(classify_state(False, 99, 100, 5)[0], 1)

    def test_recent_connected(self):
        self.assertEqual(classify_state(True, 99, 100, 5)[0], 0)

    def test_stale_even_if_last_value_connected(self):
        self.assertEqual(classify_state(True, 90, 100, 5)[0], 2)


if __name__ == '__main__':
    unittest.main()
