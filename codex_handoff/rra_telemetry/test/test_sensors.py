import math
import unittest
from types import SimpleNamespace as N

from rra_telemetry.sensors import sensor_status


class SensorTests(unittest.TestCase):
    def gps(self, **changes):
        values = dict(status=N(status=0), latitude=12.5, longitude=-2.0, altitude=50.0)
        values.update(changes)
        return N(**values)

    def imu(self, **changes):
        values = dict(orientation=N(x=0.0, y=0.0, z=0.0, w=1.0),
                      orientation_covariance=[0.0] * 9)
        values.update(changes)
        return N(**values)

    def battery(self, **changes):
        values = dict(present=True, voltage=12.3, percentage=0.5)
        values.update(changes)
        return N(**values)

    def speed(self, **changes):
        linear = N(x=3.0, y=4.0, z=0.0)
        twist = N(twist=N(linear=linear))
        values = dict(twist=twist)
        values.update(changes)
        return N(**values)

    def test_absent_and_stale_each_sensor(self):
        for kind, msg in [('gps', self.gps()), ('imu', self.imu()), ('battery', self.battery()),
                          ('speed', self.speed()), ('heading', N(data=45.0))]:
            with self.subTest(kind=kind):
                self.assertEqual(sensor_status(kind, None, None, 5)[0], 2)
                self.assertEqual(sensor_status(kind, msg, 5.1, 5)[0], 2)
                self.assertEqual(sensor_status(kind, msg, 5.1, 5)[2]['edad_recepcion_s'], '5.100')
                self.assertEqual(sensor_status(kind, msg, 5.1, 5)[2]['edad_muestra_verificada'], 'no')

    def test_gps_valid_and_missing_fix(self):
        level, _, values = sensor_status('gps', self.gps(), 0.1234, 5)
        self.assertEqual(level, 0)
        self.assertEqual(values['edad_recepcion_s'], '0.123')
        self.assertEqual(values['edad_muestra_verificada'], 'no')
        self.assertEqual(sensor_status('gps', self.gps(status=N(status=-1)), 0, 5)[0], 1)

    def test_gps_invalid_and_unknown_altitude(self):
        self.assertEqual(sensor_status('gps', self.gps(latitude=math.nan), 0, 5)[0], 1)
        self.assertEqual(sensor_status('gps', self.gps(longitude=181), 0, 5)[0], 1)
        self.assertEqual(sensor_status('gps', self.gps(altitude=math.nan), 0, 5)[2]['altitud_m'], 'desconocida')

    def test_imu_valid_and_invalid(self):
        self.assertEqual(sensor_status('imu', self.imu(), 0, 5)[0], 0)
        self.assertEqual(sensor_status('imu', self.imu(orientation_covariance=[-1.0] + [0.0] * 8), 0, 5)[0], 1)
        self.assertEqual(sensor_status('imu', self.imu(orientation=N(x=0., y=0., z=0., w=0.)), 0, 5)[0], 1)

    def test_battery_rejects_zero_absent_nan_and_negative_percentage(self):
        self.assertEqual(sensor_status('battery', self.battery(), 0, 5)[0], 0)
        for msg in (self.battery(voltage=0), self.battery(voltage=math.nan), self.battery(present=False)):
            self.assertEqual(sensor_status('battery', msg, 0, 5)[0], 1)
            values = sensor_status('battery', msg, 0, 5)[2]
            self.assertNotIn('voltaje_v', values)
            self.assertEqual(values['edad_recepcion_s'], '0.000')
        level, _, values = sensor_status('battery', self.battery(percentage=-0.01), 0, 5)
        self.assertEqual(level, 1)
        self.assertEqual(values['porcentaje'], 'desconocido')
        self.assertIn('voltaje_v', values)

    def test_speed_magnitude_and_invalid_values(self):
        level, message, values = sensor_status('speed', self.speed(), 0.2, 5)
        self.assertEqual((level, message), (0, 'Velocidad disponible'))
        self.assertEqual(values['velocidad_m_s'], '5.000')
        self.assertEqual(sensor_status('speed', self.speed(twist=N(twist=N(
            linear=N(x=math.nan, y=0.0, z=0.0)))), 0.1, 5)[0], 1)

    def test_heading_uses_degrees_from_north_range(self):
        level, _, values = sensor_status('heading', N(data=123.456), 0.2, 5)
        self.assertEqual(level, 0)
        self.assertEqual(values['rumbo_grados_norte'], '123.46')
        for heading in (math.nan, -1.0, 360.0):
            self.assertEqual(sensor_status('heading', N(data=heading), 0.1, 5)[0], 1)


if __name__ == '__main__':
    unittest.main()
