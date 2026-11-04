"""Prueba aislada con un publicador simulado; no conecta MAVROS ni hardware."""

import os
import signal
import subprocess
import tempfile
import time

import rclpy
from diagnostic_msgs.msg import DiagnosticArray
from mavros_msgs.msg import State
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState, Imu, NavSatFix


def main():
    if os.environ.get('ROS_AUTOMATIC_DISCOVERY_RANGE') != 'LOCALHOST':
        raise RuntimeError('Configure ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST')
    if not os.environ.get('ROS_DOMAIN_ID'):
        raise RuntimeError('Configure un ROS_DOMAIN_ID de prueba aislado')
    logdir = tempfile.mkdtemp(prefix='rra-observer-check-')
    log_path = os.path.join(logdir, 'observer.log')
    with open(log_path, 'w', encoding='utf-8') as output:
        process = subprocess.Popen(
            ['ros2', 'run', 'rra_telemetry', 'state_observer', '--ros-args',
             '-p', 'stale_after_sec:=1.5'], stdout=output,
            stderr=subprocess.STDOUT, start_new_session=True)
        rclpy.init()
        node = rclpy.create_node('rra_observer_test')
        samples = []
        publisher = node.create_publisher(State, '/mavros/state', 10)
        subscription = node.create_subscription(
            DiagnosticArray, '/rra/telemetry/diagnostics',
            lambda msg: samples.extend(msg.status), 10)

        def expect(level, text, state=None):
            samples.clear()
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError('El observador terminó prematuramente')
                if state is not None:
                    publisher.publish(state)
                rclpy.spin_once(node, timeout_sec=0.25)
                if any(item.name == 'RRA: conexion MAVROS' and item.level == bytes([level]) and text in item.message
                       for item in samples):
                    print('OK:', text, flush=True)
                    return
            raise RuntimeError('No se recibió: ' + text)

        try:
            expect(2, 'Sin datos')
            simulated = State()
            simulated.connected = False
            simulated.mode = 'SIM'
            expect(1, 'sin conexion', simulated)
            simulated.connected = True
            expect(0, 'conectado', simulated)
            expect(2, 'caducado')
            gps_pub = node.create_publisher(NavSatFix, '/mavros/global_position/global', qos_profile_sensor_data)
            imu_pub = node.create_publisher(Imu, '/mavros/imu/data', qos_profile_sensor_data)
            batt_pub = node.create_publisher(BatteryState, '/mavros/battery', qos_profile_sensor_data)
            gps = NavSatFix(); gps.latitude = 12.0; gps.longitude = -2.0; gps.altitude = 30.0
            gps.status.status = 0
            imu = Imu(); imu.orientation.w = 1.0
            battery = BatteryState(); battery.present = True; battery.voltage = 12.0; battery.percentage = 0.5

            def expect_sensors(expected, publish):
                samples.clear()
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError('El observador terminó prematuramente')
                    if publish:
                        gps_pub.publish(gps); imu_pub.publish(imu); batt_pub.publish(battery)
                    rclpy.spin_once(node, timeout_sec=0.25)
                    found = {s.name: s for s in samples}
                    if all(name in found and found[name].level == bytes([level])
                           for name, level in expected.items()):
                        print('OK sensores:', expected, flush=True)
                        return
                raise RuntimeError('Diagnósticos de sensores no recibidos: ' + repr(expected))

            expect_sensors({'RRA: gps': 0, 'RRA: imu': 0, 'RRA: battery': 0}, True)
            battery.voltage = 0.0; battery.percentage = -0.01
            expect_sensors({'RRA: gps': 0, 'RRA: imu': 0, 'RRA: battery': 1}, True)
            expect_sensors({'RRA: gps': 2, 'RRA: imu': 2, 'RRA: battery': 2}, False)
            print('Prueba integrada correcta; log:', log_path, flush=True)
        finally:
            node.destroy_node()
            rclpy.shutdown()
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGINT)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=5)


if __name__ == '__main__':
    main()
