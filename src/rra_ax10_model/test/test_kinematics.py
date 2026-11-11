import math
import unittest

from rra_ax10_model.kinematics import Ax10Geometry, integrate_pose, steering_angles, yaw_rate


class TestAx10Kinematics(unittest.TestCase):
    def test_zero_steering_is_straight(self):
        g = Ax10Geometry()
        self.assertEqual(steering_angles(0.0, g), (0.0, 0.0))
        self.assertEqual(yaw_rate(1.0, 0.0, g), 0.0)

    def test_reported_parallel_geometry(self):
        g = Ax10Geometry()
        left, right = steering_angles(math.radians(20), g)
        self.assertAlmostEqual(left, right)

    def test_ackermann_mode_has_inner_outer_difference(self):
        g = Ax10Geometry(steering_geometry="ackermann")
        left, right = steering_angles(math.radians(20), g)
        self.assertGreater(left, right)  # left wheel is inside on left turn

    def test_clamps_to_reported_steering_limit(self):
        g = Ax10Geometry()
        left, right = steering_angles(math.radians(80), g)
        self.assertAlmostEqual(left, math.radians(25))
        self.assertAlmostEqual(right, math.radians(25))

    def test_reverse_speed_reverses_yaw_rate(self):
        g = Ax10Geometry()
        self.assertLess(yaw_rate(-1.0, math.radians(10), g), 0.0)

    def test_straight_integration(self):
        g = Ax10Geometry()
        x, y, yaw, _ = integrate_pose(0, 0, 0, 1.0, 0.0, 1.0, g)
        self.assertAlmostEqual(x, 1.0)
        self.assertAlmostEqual(y, 0.0)
        self.assertAlmostEqual(yaw, 0.0)


if __name__ == "__main__":
    unittest.main()
