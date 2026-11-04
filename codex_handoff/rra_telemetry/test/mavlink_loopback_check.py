"""Prueba local: heartbeat MAVLink sintético, observador y rosbag.

No es ArduRover SITL. Únicamente emite HEARTBEAT desarmado por loopback y no
procesa ni ejecuta órdenes MAVLink. Nunca acepta direcciones configurables.
"""

import os
import signal
import socket
import struct
import subprocess
import tempfile
import time

import rclpy
from diagnostic_msgs.msg import DiagnosticArray


def crc_x25(data):
    crc = 0xFFFF
    for value in data:
        tmp = value ^ (crc & 0xFF)
        tmp = (tmp ^ (tmp << 4)) & 0xFF
        crc = ((crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xFFFF
    return crc


def heartbeat(sequence):
    # MAVLink 1: HEARTBEAT message 0, CRC_EXTRA 50; system/component 1/1.
    # Ground rover (10), ArduPilot (3), flags 0 (desarmado), ACTIVE (4).
    payload = struct.pack('<IBBBBB', 0, 10, 3, 0, 4, 3)
    header = struct.pack('<BBBBB', len(payload), sequence & 0xFF, 1, 1, 0)
    checksum = crc_x25(header + payload + bytes([50]))
    return b'\xfe' + header + payload + struct.pack('<H', checksum)


def main():
    if os.environ.get('ROS_AUTOMATIC_DISCOVERY_RANGE') != 'LOCALHOST':
        raise RuntimeError('Configurar ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST')
    if not os.environ.get('ROS_DOMAIN_ID'):
        raise RuntimeError('Configurar un ROS_DOMAIN_ID aislado')

    folder = tempfile.mkdtemp(prefix='rra-mavlink-check-')
    bag_path = os.path.join(folder, 'bag')
    processes = []
    streams = []

    def start(name, args):
        stream = open(os.path.join(folder, name + '.log'), 'w', encoding='utf-8')
        streams.append(stream)
        process = subprocess.Popen(args, stdout=stream, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        processes.append((name, process))
        return process

    def stop(process):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=5)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', 14681))
    rclpy.init()
    node = rclpy.create_node('rra_mavlink_loopback_check')
    samples = []
    subscriber = node.create_subscription(
        DiagnosticArray, '/rra/telemetry/diagnostics',
        lambda msg: samples.append(msg.status[0]), 10)
    try:
        mavros = start('mavros', [
            'ros2', 'run', 'mavros', 'mavros_node', '--ros-args',
            '-p', 'fcu_url:=udp://127.0.0.1:14680@127.0.0.1:14681',
            '-p', "gcs_url:=''"])
        observer = start('observer', ['ros2', 'run', 'rra_telemetry', 'state_observer'])
        recorder = start('record', [
            'ros2', 'bag', 'record', '-s', 'sqlite3', '-o', bag_path,
            '--topics', '/mavros/state', '/rra/telemetry/diagnostics'])

        # Esperar a que los tres procesos arranquen y el bag descubra los tópicos.
        time.sleep(12)
        for name, process in processes:
            if process.poll() is not None:
                raise RuntimeError(f'{name} terminó antes de la prueba')

        sequence = 0
        deadline = time.monotonic() + 25
        next_send = 0.0
        while time.monotonic() < deadline:
            now = time.monotonic()
            if now >= next_send:
                sock.sendto(heartbeat(sequence), ('127.0.0.1', 14680))
                sequence += 1
                next_send = now + 0.5
            rclpy.spin_once(node, timeout_sec=0.1)
            if any(s.level == b'\x00' and s.message == 'MAVROS conectado'
                   for s in samples):
                print('OK: heartbeat simulado recibido; observador conectado', flush=True)
                break
        else:
            raise RuntimeError('Sin diagnóstico conectado: ' + repr(
                [(s.level, s.message) for s in samples[-5:]]))

        # Mantener el heartbeat más tiempo que el umbral para detectar falsos
        # caducados mientras el emisor sigue activo.
        samples.clear()
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            now = time.monotonic()
            if now >= next_send:
                sock.sendto(heartbeat(sequence), ('127.0.0.1', 14680))
                sequence += 1
                next_send = now + 0.5
            rclpy.spin_once(node, timeout_sec=0.1)
        if not samples or any(s.level != b'\x00' for s in samples):
            raise RuntimeError('Falso estado de pérdida durante heartbeat: ' + repr(
                [(s.level, s.message) for s in samples]))
        print('OK: heartbeat sostenido sin pérdida falsa', flush=True)

        samples.clear()
        deadline = time.monotonic() + 35
        observed_loss = False
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.2)
            if not observed_loss and any(s.level == b'\x02' for s in samples):
                observed_loss = True
                print('OK: datos caducados tras parar heartbeat', flush=True)
            if any(s.level == b'\x01' and 'sin conexion' in s.message for s in samples):
                print('OK: MAVROS confirmó desconexión', flush=True)
                break
        else:
            raise RuntimeError('No se recibió desconexión explícita: ' + repr(
                [(s.level, s.message) for s in samples[-10:]]))
        time.sleep(2)

        stop(recorder)
        if recorder.returncode != 0:
            raise RuntimeError('rosbag record terminó con código ' + str(recorder.returncode))
        stop(observer)
        stop(mavros)
        info = subprocess.run(['ros2', 'bag', 'info', bag_path], capture_output=True,
                              text=True, timeout=30, check=True)
        print('BAG INFO:\n' + info.stdout, flush=True)
        samples.clear()
        playback = start('play', ['ros2', 'bag', 'play', bag_path])
        deadline = time.monotonic() + 45
        while playback.poll() is None and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.2)
        if playback.poll() is None:
            raise RuntimeError('rosbag play no terminó en el plazo')
        if playback.returncode != 0:
            raise RuntimeError('rosbag play terminó con código ' + str(playback.returncode))
        if not any(s.level == b'\x00' and s.message == 'MAVROS conectado'
                   for s in samples):
            raise RuntimeError('La reproducción no entregó el estado conectado')
        if not any(s.level != b'\x00' for s in samples):
            raise RuntimeError('La reproducción no entregó un estado sin conexión')
        print('OK: rosbag reproducido; diagnósticos recibidos:', len(samples), flush=True)
        print('RESULTADO CORRECTO. Evidencia local:', folder, flush=True)
    finally:
        for _, process in reversed(processes):
            stop(process)
        for stream in streams:
            stream.close()
        node.destroy_node()
        rclpy.shutdown()
        sock.close()
        print('Registros locales:', folder, flush=True)


if __name__ == '__main__':
    main()
