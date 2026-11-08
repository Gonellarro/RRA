"""Verifica la reproducción de una bolsa SITL sin publicar órdenes."""

import math
import os
import signal
import subprocess
import sys
import time

import rclpy
from diagnostic_msgs.msg import DiagnosticArray
from mavros_msgs.msg import State
from nav_msgs.msg import Odometry
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState, Imu, NavSatFix
from std_msgs.msg import Float64


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Uso: verify_bag.py RUTA_BAG')
    if os.environ.get('ROS_AUTOMATIC_DISCOVERY_RANGE') != 'LOCALHOST' or not os.environ.get('ROS_DOMAIN_ID'):
        raise RuntimeError('Configurar dominio de prueba y descubrimiento LOCALHOST')
    rclpy.init()
    node = rclpy.create_node('rra_sitl_bag_check')
    found = {key: [] for key in ('state', 'gps', 'imu', 'battery', 'odom',
                                 'heading', 'diag')}
    subs = [
        node.create_subscription(State, '/mavros/state', lambda m: found['state'].append(m), 10),
        node.create_subscription(NavSatFix, '/mavros/global_position/global', lambda m: found['gps'].append(m), qos_profile_sensor_data),
        node.create_subscription(Imu, '/mavros/imu/data', lambda m: found['imu'].append(m), qos_profile_sensor_data),
        node.create_subscription(BatteryState, '/mavros/battery', lambda m: found['battery'].append(m), qos_profile_sensor_data),
        node.create_subscription(Odometry, '/mavros/global_position/local', lambda m: found['odom'].append(m), qos_profile_sensor_data),
        node.create_subscription(Float64, '/mavros/global_position/compass_hdg', lambda m: found['heading'].append(m), qos_profile_sensor_data),
        node.create_subscription(DiagnosticArray, '/rra/telemetry/diagnostics', lambda m: found['diag'].append(m), 10),
    ]
    process = subprocess.Popen(['ros2', 'bag', 'play', sys.argv[1], '--rate', '4.0'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=True)
    try:
        end = time.monotonic() + 55
        while process.poll() is None and time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.1)
        if process.poll() is None or process.returncode != 0:
            raise RuntimeError('La reproducción falló o agotó el tiempo')
        for _ in range(10):
            rclpy.spin_once(node, timeout_sec=0.1)
        if not all(found.values()):
            raise RuntimeError('Faltan tópicos: ' + repr({k: len(v) for k, v in found.items()}))
        checks = [
            any(m.connected and not m.armed for m in found['state']),
            any(not m.connected for m in found['state']),
            any(m.status.status >= 0 and math.isfinite(m.latitude) for m in found['gps']),
            any(math.isfinite(m.orientation.w) for m in found['imu']),
            any(m.voltage > 0 and 0 <= m.percentage <= 1 for m in found['battery']),
            any(all(math.isfinite(v) for v in (m.twist.twist.linear.x,
                                               m.twist.twist.linear.y,
                                               m.twist.twist.linear.z))
                for m in found['odom']),
            any(math.isfinite(m.data) and 0 <= m.data < 360 for m in found['heading']),
            all(any(s.name == name and s.level == b'\x00'
                    for m in found['diag'] for s in m.status)
                for name in ('RRA: gps', 'RRA: imu', 'RRA: battery',
                             'RRA: speed', 'RRA: heading')),
        ]
        if not all(checks):
            raise RuntimeError('No pasaron todas las comprobaciones: ' + repr(checks))
        print('REPLAY_OK', {key: len(value) for key, value in found.items()}, flush=True)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
            process.wait(timeout=10)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
