"""Prueba GCS failsafe solo en ArduRover SITL dentro de namespace aislado WSL."""
import hashlib
import json
import math
import os
import pathlib
import signal
import socket
import subprocess
import sys
import tempfile
import time

BASE = '/mnt/c/RRA/codex_handoff/sitl'
BINARY = os.path.expanduser('~/rra-sitl/ardurover')
DEPS = os.path.expanduser('~/rra-sitl/deps-pymavlink-2.4.50')
HOME = (-35.363261, 149.165230)
POINTS = [HOME, (HOME[0] + 0.000100, HOME[1]),
          (HOME[0] + 0.000100, HOME[1] + 0.000120), HOME]
AUTO = 10
HOLD = 4
GCS_TIMEOUT_S = 5
OBSERVE_LOSS_S = 8
RECONNECT_OBSERVE_S = 5


def verify_isolation():
    original = os.environ.get('RRA_ORIGINAL_NETNS')
    if not original or os.readlink('/proc/self/ns/net') == original:
        raise RuntimeError('No se ha creado un namespace de red distinto al original')
    subprocess.run(['/usr/sbin/ip', 'link', 'set', 'lo', 'up'], check=True)
    links = json.loads(subprocess.check_output(['/usr/sbin/ip', '-j', 'link']))
    if [x['ifname'] for x in links] != ['lo']:
        raise RuntimeError(f'Interfaz inesperada en namespace: {links}')
    if socket.gethostbyname('localhost') != '127.0.0.1':
        raise RuntimeError('localhost no resuelve a loopback IPv4')
    return links


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def distance(a, b):
    y = (a[0] - b[0]) * 111320
    x = (a[1] - b[1]) * 111320 * math.cos(math.radians(b[0]))
    return math.hypot(x, y)


def inside(folder, enable):
    links = verify_isolation()
    sys.path.insert(0, DEPS)
    os.environ['MAVLINK20'] = '1'
    from pymavlink import mavutil

    official = BASE + '/rover-oficial-4.7.2.parm'
    profile = os.path.join(folder, f'fase4-gcs-enable-{enable}.parm')
    with open(profile, 'w', encoding='ascii') as f:
        f.write(f'# SITL ONLY. Never load this profile on physical hardware.\n')
        # GCS-only SITL: disable the separate RC-throttle failsafe so it cannot
        # mask the GCS heartbeat case. RC input is not part of this test.
        f.write(f'FS_GCS_ENABLE {enable}\nFS_GCS_TIMEOUT {GCS_TIMEOUT_S}\nFS_ACTION 2\nFS_OPTIONS 0\nFS_THR_ENABLE 0\nRC_PROTOCOLS 0\n')
    combined = os.path.join(folder, 'defaults-sitl-only.parm')
    pathlib.Path(combined).write_bytes(pathlib.Path(official).read_bytes() + b'\n' + pathlib.Path(profile).read_bytes())

    cmd = [BINARY, '--model', 'rover', '--home=-35.363261,149.165230,584,0',
           '--defaults=' + combined, '--serial0=udpclient:127.0.0.1:14690',
           '--serial2=udpclient:127.0.0.1:14692', '--sim-address=127.0.0.1']
    env = dict(os.environ, PYTHONPATH=DEPS, PYTHONUNBUFFERED='1')
    with open(os.path.join(folder, 'sitl.log'), 'w', encoding='utf-8') as log:
        sitl = subprocess.Popen(cmd, cwd=folder, stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True, env=env)
        conn = None
        events = open(os.path.join(folder, 'mavlink_events.jsonl'), 'w', encoding='utf-8')
        armed = False
        current_mode = None
        last_position = None
        reached = set()
        latest_hb = None

        def emit(kind, **data):
            event = {'wall_time': time.time(), 'monotonic': time.monotonic(), 'kind': kind, **data}
            events.write(json.dumps(event, ensure_ascii=True) + '\n')
            events.flush()
            print(json.dumps(event, ensure_ascii=True), flush=True)

        def heartbeat():
            conn.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS,
                                    mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                                    0, 0, mavutil.mavlink.MAV_STATE_ACTIVE)

        def read_message(timeout=0.25):
            nonlocal armed, current_mode, last_position, latest_hb
            m = conn.recv_match(blocking=True, timeout=timeout)
            if m is None:
                return None
            t = m.get_type()
            if t == 'HEARTBEAT' and m.get_srcSystem() == 1:
                latest_hb = m
                current_mode = int(m.custom_mode)
                armed = bool(m.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                emit('heartbeat', mode=current_mode, armed=armed)
            elif t == 'STATUSTEXT':
                emit('statustext', text=m.text)
            elif t == 'MISSION_ITEM_REACHED':
                reached.add(int(m.seq))
                emit('mission_item_reached', seq=int(m.seq), position=last_position)
            elif t == 'GLOBAL_POSITION_INT':
                last_position = (m.lat / 1e7, m.lon / 1e7)
            elif t == 'COMMAND_ACK':
                emit('command_ack', command=int(m.command), result=int(m.result))
            return m

        def wait_for(predicate, timeout, send_gcs=True, label='espera'):
            end = time.monotonic() + timeout
            last_sent = 0.0
            while time.monotonic() < end:
                if sitl.poll() is not None:
                    raise RuntimeError(f'SITL terminó inesperadamente: {sitl.returncode}')
                now = time.monotonic()
                if send_gcs and now - last_sent >= 0.8:
                    heartbeat()
                    last_sent = now
                m = read_message(0.2)
                if predicate(m):
                    return m
            raise TimeoutError(f'Timeout en {label}; modo={current_mode}, armed={armed}')

        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if sitl.poll() is not None:
                    raise RuntimeError(f'SITL salió durante el arranque: {sitl.returncode}')
                try:
                    conn = mavutil.mavlink_connection('tcp:127.0.0.1:5762',
                                                       source_system=255, source_component=190)
                    break
                except (ConnectionError, OSError):
                    time.sleep(0.25)
            if conn is None:
                raise TimeoutError('No abrió el TCP de loopback 5762')
            hb = wait_for(lambda m: m is not None and m.get_type() == 'HEARTBEAT'
                          and m.get_srcSystem() == 1 and m.autopilot == mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA
                          and m.type == mavutil.mavlink.MAV_TYPE_GROUND_ROVER, 30, label='heartbeat Rover')
            if armed:
                raise RuntimeError('SITL arrancó armado')
            emit('startup', mode=int(hb.custom_mode), armed=armed,
                 network_namespace=os.readlink('/proc/self/ns/net'), interfaces=[x['ifname'] for x in links],
                 enable=enable, timeout_s=GCS_TIMEOUT_S, action=2, options=0,
                 fs_thr_enable=0, rc_protocols=0)

            # Capture the parameters SITL actually accepted before the mission.
            effective = {}
            for name in ('FS_GCS_ENABLE', 'FS_GCS_TIMEOUT', 'FS_ACTION', 'FS_OPTIONS',
                         'FS_THR_ENABLE', 'RC_PROTOCOLS'):
                conn.mav.param_request_read_send(1, 1, name.encode('ascii'), -1)
                end = time.monotonic() + 8
                while time.monotonic() < end:
                    msg = read_message(0.25)
                    if msg is None or msg.get_type() != 'PARAM_VALUE' or msg.get_srcSystem() != 1:
                        continue
                    param_id = msg.param_id.decode('ascii', errors='ignore').rstrip('\x00') \
                        if isinstance(msg.param_id, bytes) else str(msg.param_id).rstrip('\x00')
                    if param_id == name:
                        effective[name] = float(msg.param_value)
                        break
                if name not in effective:
                    raise RuntimeError(f'No se leyó el parámetro efectivo {name}')
            emit('effective_parameters', values=effective)
            expected = {'FS_GCS_ENABLE': float(enable), 'FS_GCS_TIMEOUT': float(GCS_TIMEOUT_S),
                        'FS_ACTION': 2.0, 'FS_OPTIONS': 0.0, 'FS_THR_ENABLE': 0.0,
                        'RC_PROTOCOLS': 0.0}
            if effective != expected:
                raise RuntimeError(f'Parámetros efectivos distintos del perfil SITL: {effective}')

            gps = wait_for(lambda m: m is not None and m.get_type() == 'GPS_RAW_INT' and m.fix_type >= 3,
                           90, label='GPS fix simulado')
            wait_for(lambda m: m is not None and m.get_type() == 'GLOBAL_POSITION_INT', 20,
                     label='posición inicial')
            warmup_end = time.monotonic() + 40
            wait_for(lambda m: time.monotonic() >= warmup_end, 46, label='estabilización SITL')
            emit('ready', gps_fix=int(gps.fix_type))

            conn.mav.mission_count_send(1, 1, len(POINTS), mavutil.mavlink.MAV_MISSION_TYPE_MISSION)
            uploaded = set()
            while True:
                req = wait_for(lambda m: m is not None and m.get_type() in
                               ('MISSION_REQUEST_INT', 'MISSION_REQUEST', 'MISSION_ACK'),
                               20, label='carga de misión')
                if req.get_type() == 'MISSION_ACK':
                    if req.type != mavutil.mavlink.MAV_MISSION_ACCEPTED or len(uploaded) != len(POINTS):
                        raise RuntimeError(f'Misión no aceptada/completa: ACK={req.type}, items={sorted(uploaded)}')
                    emit('mission_uploaded', count=len(uploaded))
                    break
                seq = int(req.seq)
                if not 0 <= seq < len(POINTS):
                    raise RuntimeError(f'Secuencia fuera de rango: {seq}')
                lat, lon = POINTS[seq]
                conn.mav.mission_item_int_send(
                    1, 1, seq, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
                    mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, int(seq == 0), 1,
                    0, 0, 0, 0, int(round(lat * 1e7)), int(round(lon * 1e7)), 0,
                    mavutil.mavlink.MAV_MISSION_TYPE_MISSION)
                uploaded.add(seq)

            conn.mav.command_long_send(1, 1, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                                      0, 1, 0, 0, 0, 0, 0, 0)
            ack = wait_for(lambda m: m is not None and m.get_type() == 'COMMAND_ACK'
                           and m.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                           20, label='ACK de armado')
            if ack.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
                raise RuntimeError(f'Armado SITL rechazado: ACK={ack.result}')
            wait_for(lambda m: armed, 15, label='estado armado')
            conn.mav.set_mode_send(1, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, AUTO)
            wait_for(lambda m: current_mode == AUTO, 20, label='modo AUTO')
            emit('auto_started')
            wait_for(lambda m: m is not None and m.get_type() == 'MISSION_ITEM_REACHED' and m.seq == 1,
                     90, label='primer punto')

            emit('gcs_heartbeat_stopped', enable=enable, timeout_s=GCS_TIMEOUT_S)
            loss_started = time.monotonic()
            loss_deadline = loss_started + OBSERVE_LOSS_S
            while time.monotonic() < loss_deadline:
                read_message(0.2)  # Solo recibe; deliberadamente no emite heartbeat GCS.
            loss_mode = current_mode
            loss_armed = armed
            remaining = sorted(set(range(1, len(POINTS))) - reached)
            emit('gcs_loss_observed', enable=enable, duration_s=round(time.monotonic()-loss_started, 2),
                 mode=loss_mode, armed=loss_armed, reached=sorted(reached), remaining=remaining)

            # Reconectar la estación solo con heartbeat; no reenviar modos ni misión.
            reconnect_end = time.monotonic() + RECONNECT_OBSERVE_S
            last_sent = 0.0
            while time.monotonic() < reconnect_end:
                if time.monotonic() - last_sent >= 0.8:
                    heartbeat()
                    last_sent = time.monotonic()
                read_message(0.2)
            reconnect_mode = current_mode
            emit('gcs_reconnected', mode=reconnect_mode, armed=armed, reached=sorted(reached))

            expected = HOLD if enable == 1 else AUTO
            if loss_mode != expected:
                raise RuntimeError(f'Esperado modo {expected} tras pérdida; observado {loss_mode}')
            if enable == 1 and reconnect_mode != HOLD:
                raise RuntimeError(f'El failsafe debía permanecer en HOLD tras reconexión; modo {reconnect_mode}')
            if enable in (0, 2) and loss_mode != AUTO:
                raise RuntimeError(f'Con ENABLE={enable} se esperaba seguir AUTO; observado {loss_mode}')
            emit('scenario_passed', enable=enable, loss_mode=loss_mode,
                 reconnect_mode=reconnect_mode, expected_mode=expected)
        finally:
            if conn is not None:
                if armed:
                    try:
                        heartbeat()
                        conn.mav.set_mode_send(1, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, HOLD)
                        wait_for(lambda m: current_mode == HOLD, 10, label='modo HOLD de cierre')
                        conn.mav.command_long_send(1, 1, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                                                   0, 0, 0, 0, 0, 0, 0, 0)
                        wait_for(lambda m: not armed, 10, label='desarmado de cierre')
                        emit('safe_end', mode=current_mode, armed=armed)
                    except Exception as exc:
                        emit('cleanup_error', error=repr(exc), mode=current_mode, armed=armed)
                conn.close()
            events.close()
            if sitl.poll() is None:
                os.killpg(sitl.pid, signal.SIGINT)
                try:
                    sitl.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    os.killpg(sitl.pid, signal.SIGTERM)
                    sitl.wait(timeout=5)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--inside':
        enable = int(sys.argv[2])
        if enable not in (0, 1, 2):
            raise SystemExit('FS_GCS_ENABLE debe ser 0, 1 o 2')
        folder = os.environ.get('RRA_F4_FOLDER')
        if not folder:
            raise RuntimeError('Falta carpeta local de evidencia del ensayo')
        return inside(folder, enable)
    if sys.argv[1:]:
        raise SystemExit('Uso: fase4_gcs_failsafe.py [0|1|2]')
    if not os.path.isfile(BINARY) or not os.path.isdir(DEPS):
        raise RuntimeError('Falta el binario SITL o pymavlink local')
    root = pathlib.Path.home() / 'rra-sitl' / 'fase4'
    root.mkdir(mode=0o700, exist_ok=True)
    for enable in (0, 1, 2):
        folder = tempfile.mkdtemp(prefix=f'gcs-enable-{enable}-', dir=root)
        env = dict(os.environ, RRA_ORIGINAL_NETNS=os.readlink('/proc/self/ns/net'),
                   RRA_F4_FOLDER=folder)
        command = ['unshare', '-Urn', 'python3', os.path.abspath(__file__), '--inside', str(enable)]
        print(f'INICIO FS_GCS_ENABLE={enable} EVIDENCIA={folder}', flush=True)
        result = subprocess.run(command, env=env, timeout=300)
        print(f'FIN FS_GCS_ENABLE={enable} RESULTADO={result.returncode} EVIDENCIA={folder}', flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
