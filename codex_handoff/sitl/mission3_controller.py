"""Misión AUTO de prueba exclusivamente dentro de un namespace aislado WSL.

Envía órdenes de armado y AUTO SOLO al proceso SITL local, nunca a la Orange Pi
ni al rover físico. El endpoint no es configurable; falla si hay más de loopback.
"""

import json
import math
import os
import socket
import subprocess
import sys
import time

os.environ['MAVLINK20'] = '1'
from pymavlink import mavutil

HOME = (-35.363261, 149.165230)
POINTS = [HOME, (HOME[0] + 0.000100, HOME[1]),
          (HOME[0] + 0.000100, HOME[1] + 0.000120), HOME]


def ensure_isolated():
    original = os.environ.get('RRA_ORIGINAL_NETNS')
    if not original or os.readlink('/proc/self/ns/net') == original:
        raise RuntimeError('No existe aislamiento de red')
    links = json.loads(subprocess.check_output(['/usr/sbin/ip', '-j', 'link']))
    if [link['ifname'] for link in links] != ['lo']:
        raise RuntimeError('El namespace tiene interfaces además de loopback')
    if socket.gethostbyname('localhost') != '127.0.0.1':
        raise RuntimeError('Loopback inesperado')


def distance(a, b):
    y = (a[0] - b[0]) * 111320
    x = (a[1] - b[1]) * 111320 * math.cos(math.radians(b[0]))
    return math.hypot(x, y)


def main():
    ensure_isolated()
    log = open('mission_events.jsonl', 'w', encoding='utf-8')
    mav = mavutil.mavlink
    connection = None
    last_gcs = 0.0
    last_position = None
    reached = set()
    armed = False

    def emit(kind, **values):
        row = {'time': time.time(), 'kind': kind, **values}
        print(json.dumps(row, ensure_ascii=True), file=log, flush=True)
        print(json.dumps(row, ensure_ascii=True), flush=True)

    def tick():
        nonlocal last_gcs
        if time.monotonic() - last_gcs >= 1:
            connection.mav.heartbeat_send(mav.MAV_TYPE_GCS, mav.MAV_AUTOPILOT_INVALID,
                                          0, 0, mav.MAV_STATE_ACTIVE)
            last_gcs = time.monotonic()

    def receive(deadline, predicate):
        nonlocal last_position, armed
        while time.monotonic() < deadline:
            tick()
            msg = connection.recv_match(blocking=True, timeout=0.3)
            if msg is None:
                continue
            kind = msg.get_type()
            if kind == 'STATUSTEXT':
                emit('status', text=msg.text)
            elif kind == 'GLOBAL_POSITION_INT':
                last_position = (msg.lat / 1e7, msg.lon / 1e7)
            elif kind == 'HEARTBEAT' and msg.get_srcSystem() == 1:
                armed = bool(msg.base_mode & mav.MAV_MODE_FLAG_SAFETY_ARMED)
            elif kind == 'MISSION_ITEM_REACHED':
                reached.add(msg.seq)
                emit('mission_item_reached', seq=msg.seq, position=last_position)
            if predicate(msg):
                return msg
        raise TimeoutError('Agotado el plazo de la operación MAVLink')

    try:
        deadline = time.monotonic() + 25
        while True:
            try:
                connection = mavutil.mavlink_connection('tcp:127.0.0.1:5762',
                                                       source_system=255, source_component=190)
                break
            except (ConnectionError, OSError):
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.5)
        hb = receive(time.monotonic() + 30, lambda m: m.get_type() == 'HEARTBEAT'
                     and m.get_srcSystem() == 1 and m.autopilot == mav.MAV_AUTOPILOT_ARDUPILOTMEGA)
        if hb.type != mav.MAV_TYPE_GROUND_ROVER:
            raise RuntimeError('La fuente no corresponde a un rover SITL')
        emit('heartbeat', type=hb.type, armed=armed, mode=hb.custom_mode)
        gps = receive(time.monotonic() + 90, lambda m: m.get_type() == 'GPS_RAW_INT' and m.fix_type >= 3)
        emit('gps_ready', fix_type=gps.fix_type)
        receive(time.monotonic() + 20, lambda m: m.get_type() == 'GLOBAL_POSITION_INT')
        emit('start_position', position=last_position)

        # Permitir que las IMU y EKF simulados completen el arranque antes de
        # pedir armado, manteniendo heartbeat GCS y todas las comprobaciones.
        warmup_end = time.monotonic() + 40
        receive(warmup_end + 5, lambda m: time.monotonic() >= warmup_end)
        emit('warmup_complete')

        connection.mav.mission_count_send(1, 1, len(POINTS), mav.MAV_MISSION_TYPE_MISSION)
        uploaded = set()
        while True:
            req = receive(time.monotonic() + 20, lambda m: m.get_type() in
                          ('MISSION_REQUEST_INT', 'MISSION_REQUEST', 'MISSION_ACK'))
            if req.get_type() == 'MISSION_ACK':
                if req.type != mav.MAV_MISSION_ACCEPTED or len(uploaded) != len(POINTS):
                    raise RuntimeError(f'Misión rechazada o incompleta: {req.type}, {sorted(uploaded)}')
                emit('mission_uploaded', count=len(POINTS))
                break
            seq = req.seq
            if not 0 <= seq < len(POINTS):
                raise RuntimeError('Secuencia de misión fuera de rango')
            lat, lon = POINTS[seq]
            connection.mav.mission_item_int_send(
                1, 1, seq, mav.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
                mav.MAV_CMD_NAV_WAYPOINT, int(seq == 0), 1, 0, 0, 0, 0,
                int(round(lat * 1e7)), int(round(lon * 1e7)), 0,
                mav.MAV_MISSION_TYPE_MISSION)
            uploaded.add(seq)

        connection.mav.command_long_send(1, 1, mav.MAV_CMD_COMPONENT_ARM_DISARM,
                                         0, 1, 0, 0, 0, 0, 0, 0)
        ack = receive(time.monotonic() + 20, lambda m: m.get_type() == 'COMMAND_ACK'
                      and m.command == mav.MAV_CMD_COMPONENT_ARM_DISARM)
        emit('arm_ack', result=ack.result)
        if ack.result != mav.MAV_RESULT_ACCEPTED:
            try:
                receive(time.monotonic() + 4, lambda m: False)
            except TimeoutError:
                pass
            raise RuntimeError(f'Armado SITL rechazado: {ack.result}')
        receive(time.monotonic() + 15, lambda m: m.get_type() == 'HEARTBEAT' and armed)
        connection.mav.set_mode_send(1, mav.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 10)
        receive(time.monotonic() + 20, lambda m: m.get_type() == 'HEARTBEAT' and m.custom_mode == 10)
        emit('auto_started')
        start = time.monotonic()
        if sys.argv[1:] == ['--stop-after-first']:
            receive(start + 90, lambda m: m.get_type() == 'MISSION_ITEM_REACHED' and m.seq == 1)
            connection.mav.set_mode_send(1, mav.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 4)
            receive(time.monotonic() + 15, lambda m: m.get_type() == 'HEARTBEAT' and m.custom_mode == 4)
            connection.mav.command_long_send(1, 1, mav.MAV_CMD_COMPONENT_ARM_DISARM,
                                             0, 0, 0, 0, 0, 0, 0, 0)
            receive(time.monotonic() + 15, lambda m: m.get_type() == 'HEARTBEAT' and not armed)
            until = time.monotonic() + 5
            receive(until + 3, lambda m: time.monotonic() >= until)
            if 2 in reached or armed:
                raise RuntimeError('La misión avanzó o quedó armada después de la parada')
            emit('mid_mission_stop_verified', mode='HOLD', armed=False, reached=sorted(reached))
            return
        receive(start + 180, lambda m: m.get_type() == 'MISSION_ITEM_REACHED' and m.seq == 3)
        finish = last_position
        if finish is None or distance(finish, HOME) > 5.0:
            raise RuntimeError('Último punto demasiado lejos del destino')
        emit('mission_complete', duration_s=round(time.monotonic() - start, 2),
             reached=sorted(reached), position=finish, distance_home_m=round(distance(finish, HOME), 2))
        connection.mav.set_mode_send(1, mav.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 4)
        receive(time.monotonic() + 15, lambda m: m.get_type() == 'HEARTBEAT' and m.custom_mode == 4)
        connection.mav.command_long_send(1, 1, mav.MAV_CMD_COMPONENT_ARM_DISARM,
                                         0, 0, 0, 0, 0, 0, 0, 0)
        receive(time.monotonic() + 15, lambda m: m.get_type() == 'HEARTBEAT' and not armed)
        emit('safe_end', mode='HOLD', armed=False)
    except Exception as exc:
        emit('error', error=repr(exc), last_position=last_position, armed=armed)
        raise
    finally:
        if connection is not None:
            if armed:
                try:
                    connection.mav.set_mode_send(1, mav.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 4)
                    connection.mav.command_long_send(1, 1, mav.MAV_CMD_COMPONENT_ARM_DISARM,
                                                     0, 0, 0, 0, 0, 0, 0, 0)
                    receive(time.monotonic() + 5,
                            lambda m: m.get_type() == 'HEARTBEAT' and not armed)
                    emit('cleanup_disarmed')
                except Exception as exc:
                    emit('cleanup_error', error=repr(exc))
            connection.close()
        log.close()


if __name__ == '__main__':
    if sys.argv[1:] not in ([], ['--stop-after-first']):
        raise SystemExit('Solo se admite --stop-after-first')
    main()
