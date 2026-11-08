"""Recibe datagramas SITL en stdin y los entrega a MAVROS solo por loopback.

Protocolo de stdin: longitud uint32 big endian, seguida del datagrama; longitud
cero termina. El socket UDP no lee ni reenvía paquetes desde MAVROS. No utilizar
con una fuente física. Todos los subprocesos se cierran al terminar.
"""

import json
import os
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time

import rclpy
from diagnostic_msgs.msg import DiagnosticArray
from mavros_msgs.msg import State
from nav_msgs.msg import Odometry
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState, Imu, NavSatFix
from std_msgs.msg import Float64


def main():
    os.environ['ROS_DOMAIN_ID'] = '179'
    os.environ['ROS_AUTOMATIC_DISCOVERY_RANGE'] = 'LOCALHOST'
    folder = tempfile.mkdtemp(prefix='rra-sitl-receiver-')
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(('127.0.0.1', 14681))
    finished = threading.Event()
    errors = []
    counts = {'datagrams': 0, 'state': 0, 'connected': 0, 'gps': 0,
              'imu': 0, 'battery': 0, 'odometry': 0, 'heading': 0,
              'diagnostic_connected': 0, 'diagnostic_speed_heading': 0,
              'disconnected_after_connection': 0, 'diagnostic_loss': 0}
    messages = {}

    def read_exact(size):
        chunks = []
        while size:
            chunk = sys.stdin.buffer.read(size)
            if not chunk:
                return None
            chunks.append(chunk)
            size -= len(chunk)
        return b''.join(chunks)

    def relay():
        try:
            while True:
                header = read_exact(4)
                if header is None:
                    break
                size = struct.unpack('!I', header)[0]
                if size == 0:
                    break
                if size > 65507:
                    raise ValueError('Datagrama demasiado grande')
                packet = read_exact(size)
                if packet is None:
                    raise ValueError('Datagrama incompleto')
                udp.sendto(packet, ('127.0.0.1', 14680))
                counts['datagrams'] += 1
        except Exception as exc:
            errors.append(str(exc))
        finally:
            finished.set()

    logs = []
    procs = []
    recorder = None

    def start(name, cmd):
        log = open(os.path.join(folder, name + '.log'), 'w', encoding='utf-8')
        logs.append(log)
        p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                             start_new_session=True)
        procs.append(p)

    rclpy.init()
    node = rclpy.create_node('rra_sitl_receive_check')

    def state(m):
        counts['state'] += 1
        if m.connected:
            counts['connected'] += 1
            messages['connected_state'] = {'connected': m.connected, 'armed': m.armed,
                                           'mode': m.mode}
        elif counts['connected']:
            counts['disconnected_after_connection'] += 1
        messages['state'] = {'connected': m.connected, 'armed': m.armed, 'mode': m.mode}

    def gps(m):
        counts['gps'] += 1
        messages['gps'] = {'status': m.status.status, 'latitude': m.latitude,
                           'longitude': m.longitude, 'altitude': m.altitude}

    def imu(m):
        counts['imu'] += 1
        messages['imu'] = {'orientation_w': m.orientation.w}

    def battery(m):
        counts['battery'] += 1
        messages['battery'] = {'voltage': m.voltage, 'percentage': m.percentage}

    def odometry(m):
        counts['odometry'] += 1
        velocity = m.twist.twist.linear
        messages['odometry'] = {'frame_id': m.header.frame_id,
                                'child_frame_id': m.child_frame_id,
                                'velocity_enu_m_s': [velocity.x, velocity.y, velocity.z]}

    def heading(m):
        counts['heading'] += 1
        messages['heading'] = {'degrees_from_north': m.data}

    def diagnostic(m):
        connected = any(s.level == b'\x00' and s.message == 'MAVROS conectado'
                        for s in m.status)
        if connected:
            counts['diagnostic_connected'] += 1
        elif counts['diagnostic_connected']:
            counts['diagnostic_loss'] += 1
        names = {s.name: s.level for s in m.status}
        if names.get('RRA: speed') == b'\x00' and names.get('RRA: heading') == b'\x00':
            counts['diagnostic_speed_heading'] += 1

    subscriptions = [
        node.create_subscription(State, '/mavros/state', state, 10),
        node.create_subscription(NavSatFix, '/mavros/global_position/global', gps, qos_profile_sensor_data),
        node.create_subscription(Imu, '/mavros/imu/data', imu, qos_profile_sensor_data),
        node.create_subscription(BatteryState, '/mavros/battery', battery, qos_profile_sensor_data),
        node.create_subscription(Odometry, '/mavros/global_position/local', odometry,
                                 qos_profile_sensor_data),
        node.create_subscription(Float64, '/mavros/global_position/compass_hdg', heading,
                                 qos_profile_sensor_data),
        node.create_subscription(DiagnosticArray, '/rra/telemetry/diagnostics', diagnostic, 10),
    ]
    try:
        start('mavros', ['/opt/ros/lyrical/lib/mavros/mavros_node', '--ros-args',
                         '-p', 'fcu_url:=udp://127.0.0.1:14680@127.0.0.1:14681',
                         '-p', "gcs_url:=''"])
        start('observer', ['/home/rra/rra_ws/install/rra_telemetry/lib/rra_telemetry/state_observer'])
        record_log = open(os.path.join(folder, 'record.log'), 'w', encoding='utf-8')
        logs.append(record_log)
        recorder = subprocess.Popen([
            'ros2', 'bag', 'record', '-s', 'sqlite3', '-o', os.path.join(folder, 'bag'),
            '--topics', '/mavros/state', '/mavros/global_position/global',
            '/mavros/imu/data', '/mavros/battery', '/mavros/global_position/local',
            '/mavros/global_position/compass_hdg', '/rra/telemetry/diagnostics'],
            stdout=record_log, stderr=subprocess.STDOUT, start_new_session=True)
        threading.Thread(target=relay, daemon=True).start()
        print('READY', flush=True)
        deadline = time.monotonic() + 90
        while not finished.is_set() and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.2)
            if recorder.poll() is not None or any(p.poll() is not None for p in procs):
                errors.append('Un proceso ROS terminó antes de tiempo')
                break
        # Mantener MAVROS activo para observar la caducidad y desconexión.
        end = time.monotonic() + 25
        while time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.2)
            if counts['disconnected_after_connection'] and counts['diagnostic_loss']:
                break
    finally:
        if recorder is not None and recorder.poll() is None:
            os.killpg(recorder.pid, signal.SIGINT)
            try:
                recorder.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(recorder.pid, signal.SIGTERM)
                recorder.wait(timeout=5)
        for p in reversed(procs):
            if p.poll() is None:
                os.killpg(p.pid, signal.SIGINT)
            try:
                p.wait(timeout=12)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGTERM)
                p.wait(timeout=5)
        for log in logs:
            log.close()
        node.destroy_node()
        rclpy.shutdown()
        udp.close()
    result = {'counts': counts, 'samples': messages, 'errors': errors,
              'log_dir': folder, 'exit_codes': [p.returncode for p in procs],
              'record_exit': None if recorder is None else recorder.returncode}
    if recorder is not None and recorder.returncode == 0:
        info = subprocess.run(['ros2', 'bag', 'info', os.path.join(folder, 'bag')],
                              capture_output=True, text=True, timeout=30)
        result['bag_info_exit'] = info.returncode
        print('BAG_INFO\n' + info.stdout, flush=True)
    print('RESULT ' + json.dumps(result, allow_nan=True), flush=True)
    if errors or recorder is None or recorder.returncode != 0 or any(p.returncode != 0 for p in procs) or not all(counts[key] for key in
                         ('connected', 'diagnostic_connected', 'gps', 'imu', 'battery',
                          'odometry', 'heading', 'diagnostic_speed_heading',
                          'disconnected_after_connection', 'diagnostic_loss')):
        sys.exit(1)


if __name__ == '__main__':
    main()
