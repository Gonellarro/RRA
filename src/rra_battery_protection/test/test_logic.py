import unittest

from rra_battery_protection.logic import Config, Protection, State


class ProtectionTests(unittest.TestCase):
    def run_values(self, values, cfg=None):
        p = Protection(cfg or Config())
        all_events = []
        for i, value in enumerate(values):
            all_events.extend(p.update(i * 0.5, value))
        return p, all_events

    def test_short_servo_dip_is_filtered(self):
        values = [7.6] * 20 + [7.1] + [7.6] * 30
        _, events = self.run_values(values)
        self.assertNotIn("shutdown", events)
        self.assertNotIn("power_cutoff", events)

    def test_sustained_low_warns_then_requests_shutdown_and_cutoff(self):
        # Hold low long enough for each independent timer to expire.
        values = [7.6] * 4 + [7.35] * 26 + [7.25] * 26 + [7.15] * 60
        p, events = self.run_values(values)
        self.assertIn("warning", events)
        self.assertIn("shutdown", events)
        self.assertIn("power_cutoff", events)
        self.assertEqual(p.state, State.POWER_CUTOFF)

    def test_single_zero_does_not_shutdown(self):
        _, events = self.run_values([7.6] * 10 + [0.0] + [7.6] * 30)
        self.assertNotIn("shutdown", events)
        self.assertNotIn("power_cutoff", events)

    def test_persistent_bad_sensor_fault_does_not_invent_low_voltage(self):
        p, events = self.run_values([None] * 10)
        self.assertIn("sensor_fault", events)
        self.assertNotIn("shutdown", events)
        self.assertNotIn("power_cutoff", events)
        self.assertEqual(p.state, State.SENSOR_FAULT)

    def test_emergency_shorter_than_deep_threshold_confirmation(self):
        cfg = Config(emergency_v=7.0, emergency_confirm_s=1.0, emergency_enabled=True)
        _, brief_events = self.run_values([7.6] * 5 + [6.9] + [7.6] * 10, cfg)
        self.assertNotIn("emergency_cutoff", brief_events)
        p, events = self.run_values([7.6] * 5 + [6.9] * 20, cfg)
        self.assertIn("emergency_cutoff", events)
        self.assertEqual(p.state, State.POWER_CUTOFF)

    def test_cutoff_is_latched_after_recovery(self):
        cfg = Config(cutoff_confirm_s=1.0, shutdown_confirm_s=1.0,
                     warning_confirm_s=1.0, cutoff_after_request_s=1.0)
        p, events = self.run_values([7.1] * 10 + [8.0] * 30, cfg)
        self.assertIn("power_cutoff", events)
        self.assertEqual(p.state, State.POWER_CUTOFF)

    def test_cutoff_waits_for_prepared_ack_and_grace(self):
        cfg = Config(cutoff_confirm_s=1.0, shutdown_confirm_s=1.0,
                     warning_confirm_s=1.0, prepared_grace_s=2.0,
                     cutoff_after_request_s=20.0)
        p = Protection(cfg)
        all_events = []
        for i in range(10):
            all_events += p.update(i * 0.5, 7.1)
        self.assertIn("shutdown", all_events)
        self.assertNotIn("power_cutoff", all_events)
        self.assertEqual(p.state, State.POWER_CUTOFF_PENDING)
        self.assertTrue(p.acknowledge_prepared(5.0))
        self.assertNotIn("power_cutoff", p.update(6.5, 7.1))
        self.assertIn("power_cutoff", p.update(7.0, 7.1))

    def test_cutoff_waits_for_fallback_if_companion_never_prepares(self):
        cfg = Config(cutoff_confirm_s=1.0, shutdown_confirm_s=1.0,
                     warning_confirm_s=1.0, cutoff_after_request_s=3.0)
        p = Protection(cfg)
        events = []
        for i in range(7):
            events += p.update(i * 0.5, 7.1)
        self.assertIn("shutdown", events)
        self.assertNotIn("power_cutoff", events)
        self.assertIn("power_cutoff", p.update(4.5, 7.1))


if __name__ == "__main__":
    unittest.main()
