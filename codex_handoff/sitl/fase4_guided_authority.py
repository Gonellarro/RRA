"""F4-4/F4-5 bounded ArduRover SITL checks inside an isolated WSL netns."""
import hashlib
import json
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
HOME = '-35.363261,149.165230,584,0'
GUIDED, HOLD = 15, 4
GUID_TIMEOUT = 2.0  # requested value; 4.7.2 build did not expose this parameter


def inside(folder, case):
    original = os.environ.get('RRA_ORIGINAL_NETNS')
    if not original or os.readlink('/proc/self/ns/net') == original:
        raise RuntimeError('No se ha creado un namespace de red distinto al original')
    subprocess.run(['/usr/sbin/ip', 'link', 'set', 'lo', 'up'], check=True)
    links = json.loads(subprocess.check_output(['/usr/sbin/ip', '-j', 'link']))
    if [item['ifname'] for item in links] != ['lo']:
        raise RuntimeError(f'Interfaz inesperada en namespace: {links}')
    if socket.gethostbyname('localhost') != '127.0.0.1':
        raise RuntimeError('localhost no resuelve a loopback')
    sys.path.insert(0, DEPS)
    os.environ['MAVLINK20'] = '1'
    from pymavlink import mavutil

    profile = os.path.join(folder, f'{case}.parm')
    settings = ['FS_GCS_ENABLE 0', 'FS_THR_ENABLE 0', 'RC_PROTOCOLS 0']
    if case.startswith('f4-5'):
        # Only one source ID is designated for GCS-specific filtering. This is
        # not documented as a general authorization filter for mode commands.
        settings += ['MAV_GCS_SYSID 42', 'MAV_GCS_SYSID_HI 42']
        if case == 'f4-5-guarded':
            settings.append('MAV_OPTIONS 1')
    pathlib.Path(profile).write_text(
        '# SIMULATION ONLY - never apply to physical hardware\n' + '\n'.join(settings) + '\n',
        encoding='ascii')
    combined = os.path.join(folder, 'defaults-sitl-only.parm')
    pathlib.Path(combined).write_bytes(
        pathlib.Path(BASE + '/rover-oficial-4.7.2.parm').read_bytes() +
        b'\n' + pathlib.Path(profile).read_bytes())
    cmd = [BINARY, '--model', 'rover', '--home=' + HOME,
           '--defaults=' + combined, '--serial0=udpclient:127.0.0.1:14690',
           '--serial2=udpclient:127.0.0.1:14692', '--sim-address=127.0.0.1']
    env = dict(os.environ, PYTHONPATH=DEPS, PYTHONUNBUFFERED='1')
    log_path = os.path.join(folder, 'sitl.log')
    log = open(log_path, 'w', encoding='utf-8')
    sitl = subprocess.Popen(cmd, cwd=folder, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True, env=env)
    conn = None
    events_path = os.path.join(folder, 'mavlink_events.jsonl')
    events = open(events_path, 'w', encoding='utf-8')
    armed = False
    mode = None
    speed = None
    servo3 = None
    target_stop_notice = None

    def emit(kind, **data):
        row = {'wall_time': time.time(), 'monotonic': time.monotonic(),
               'kind': kind, 'case': case, **data}
        events.write(json.dumps(row, ensure_ascii=True) + '\n')
        events.flush()
        print(json.dumps(row, ensure_ascii=True), flush=True)

    def receive(timeout=0.2):
        nonlocal armed, mode, speed, servo3, target_stop_notice
        msg = conn.recv_match(blocking=True, timeout=timeout)
        if msg is None:
            return None
        typ = msg.get_type()
        if typ == 'HEARTBEAT' and msg.get_srcSystem() == 1:
            armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
            mode = int(msg.custom_mode)
            emit('heartbeat', mode=mode, armed=armed)
        elif typ == 'VFR_HUD':
            speed = float(msg.groundspeed)
            emit('speed', groundspeed=speed)
        elif typ == 'SERVO_OUTPUT_RAW':
            servo3 = int(msg.servo3_raw)
            emit('servo_output', servo3=servo3)
        elif typ == 'STATUSTEXT':
            emit('statustext', text=msg.text)
            if msg.text.startswith('target not received last ') and 'stopping' in msg.text:
                target_stop_notice = time.monotonic()
        elif typ == 'COMMAND_ACK':
            emit('command_ack', command=int(msg.command), result=int(msg.result))
        return msg

    def wait_for(pred, seconds, label):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if sitl.poll() is not None:
                raise RuntimeError(f'SITL terminó inesperadamente: {sitl.returncode}')
            msg = receive()
            if pred(msg):
                return msg
        raise TimeoutError(f'Timeout en {label}; mode={mode}, armed={armed}, speed={speed}')

    def heartbeat(source):
        conn.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS,
                                mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                                0, 0, mavutil.mavlink.MAV_STATE_ACTIVE,
                                force_mavlink1=False)

    def set_mode_from(source, requested):
        # pymavlink connection source IDs are fixed; change its MAVLink header
        # immediately before emitting this single command.
        conn.mav.srcSystem = source
        conn.mav.set_mode_send(1, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                               requested)
        emit('mode_command_sent', source_system=source, requested_mode=requested)
        wait_for(lambda _m: mode == requested, 8, f'modo {requested} desde {source}')
        emit('mode_command_effective', source_system=source, effective_mode=mode)

    try:
        for _ in range(120):
            if sitl.poll() is not None:
                raise RuntimeError(f'SITL terminó durante el arranque: {sitl.returncode}')
            try:
                initial_sysid = 42 if case == 'f4-5-guarded' else 255
                conn = mavutil.mavlink_connection('tcp:127.0.0.1:5762',
                                                   source_system=initial_sysid,
                                                   source_component=190)
                break
            except (ConnectionError, OSError):
                time.sleep(0.25)
        if conn is None:
            raise TimeoutError('No abrió TCP loopback 5762')
        wait_for(lambda m: m is not None and m.get_type() == 'HEARTBEAT' and
                 m.get_srcSystem() == 1 and m.autopilot == mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
                 30, 'heartbeat Rover')
        if armed:
            raise RuntimeError('SITL arrancó armado')
        emit('startup', netns=os.readlink('/proc/self/ns/net'), interfaces=['lo'],
             binary_sha256=hashlib.sha256(pathlib.Path(BINARY).read_bytes()).hexdigest())

        names = ['FS_GCS_ENABLE', 'FS_THR_ENABLE', 'RC_PROTOCOLS']
        names += ['MAV_GCS_SYSID', 'MAV_GCS_SYSID_HI'] if case.startswith('f4-5') else []
        if case == 'f4-5-guarded':
            names.append('MAV_OPTIONS')
        effective = {}
        for name in names:
            conn.mav.param_request_read_send(1, 1, name.encode('ascii'), -1)
            msg = wait_for(lambda x: x is not None and x.get_type() == 'PARAM_VALUE' and
                           x.get_srcSystem() == 1 and
                           (x.param_id.decode('ascii', errors='ignore').rstrip('\x00')
                            if isinstance(x.param_id, bytes) else str(x.param_id).rstrip('\x00')) == name,
                           8, 'parámetro ' + name)
            effective[name] = float(msg.param_value)
        expect = {'FS_GCS_ENABLE': 0.0, 'FS_THR_ENABLE': 0.0, 'RC_PROTOCOLS': 0.0}
        if case.startswith('f4-5'):
            expect['MAV_GCS_SYSID'] = 42.0
            expect['MAV_GCS_SYSID_HI'] = 42.0
        if case == 'f4-5-guarded':
            expect['MAV_OPTIONS'] = 1.0
        if effective != expect:
            raise RuntimeError(f'Parámetros efectivos inesperados: {effective}, esperados {expect}')
        emit('effective_parameters', values=effective)
        wait_for(lambda m: m is not None and m.get_type() == 'GPS_RAW_INT' and m.fix_type >= 3,
                 90, 'GPS simulado')
        wait_for(lambda m: m is not None and m.get_type() == 'GLOBAL_POSITION_INT',
                 20, 'posición')
        warmup = time.monotonic() + 35
        wait_for(lambda _m: time.monotonic() >= warmup, 40, 'estabilización EKF')

        if case == 'f4-4':
            # This is the only scenario that arms; it is confined to SITL.
            conn.mav.command_long_send(1, 1, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                                       0, 1, 0, 0, 0, 0, 0, 0)
            ack = wait_for(lambda m: m is not None and m.get_type() == 'COMMAND_ACK' and
                           m.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                           15, 'ACK armado SITL')
            if ack.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
                raise RuntimeError(f'Armado SITL rechazado {ack.result}')
            wait_for(lambda _m: armed, 10, 'armed heartbeat')
            set_mode_from(255, GUIDED)
            # Low speed, north only, repeated briefly then deliberately stale.
            start = time.monotonic()
            while time.monotonic() - start < 2.5:
                conn.mav.srcSystem = 255
                conn.mav.set_position_target_local_ned_send(
                    int(time.monotonic() * 1000) & 0xffffffff, 1, 1,
                    mavutil.mavlink.MAV_FRAME_LOCAL_NED, 0x0DE7,
                    0, 0, 0, 0.35, 0, 0, 0, 0, 0, 0, 0)
                receive(0.18)
            speed_at_stop, servo_at_stop = speed, servo3
            cutoff = time.monotonic()
            emit('guided_velocity_stream_stopped', source_system=255,
                 commanded_velocity_north_mps=0.35, duration_s=2.5,
                 guid_timeout_parameter_supported=False,
                 speed_at_stop=speed_at_stop, servo3_at_stop=servo_at_stop)
            while time.monotonic() - cutoff < 6:
                receive(0.2)
            late_speed, late_servo = speed, servo3
            timeout_delay = (round(target_stop_notice - cutoff, 2)
                             if target_stop_notice is not None else None)
            emit('stale_guided_observed', elapsed_s=round(time.monotonic()-cutoff, 2),
                 groundspeed=late_speed, servo3=late_servo, mode=mode, armed=armed)
            # Safe close: HOLD, then disarm, then verify heartbeat state.
            set_mode_from(255, HOLD)
            conn.mav.command_long_send(1, 1, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                                       0, 0, 0, 0, 0, 0, 0, 0)
            wait_for(lambda _m: not armed, 10, 'desarmado seguro')
            checks = {'final_mode_hold_and_disarmed': mode == HOLD and not armed,
                      'timeout_stop_notice_around_3s': timeout_delay is not None and 2.5 <= timeout_delay <= 4.0,
                      'speed_fell_after_stream_stop': (speed_at_stop is not None and late_speed is not None and
                                                       late_speed < speed_at_stop * 0.25),
                      'motor_output_neutral_after_6s': late_servo is not None and abs(late_servo - 1500) <= 20}
            emit('scenario_passed', checks=checks,
                 speed_at_stop=speed_at_stop, speed_after_6s=late_speed,
                 servo3_at_stop=servo_at_stop, servo3_after_6s=late_servo,
                 target_stop_notice_delay_s=timeout_delay,
                 note='GUID_TIMEOUT no se expone como parámetro en este binario; se observó la respuesta predeterminada. HOLD posterior limita la ventana.')
        elif case == 'f4-5':
            # No arming; test whether two distinct MAVLink SYSIDs can alternate
            # mode requests while MAV_GCS_SYSID is set to 42.
            if armed:
                raise RuntimeError('F4-5 debe permanecer desarmado')
            set_mode_from(255, GUIDED)
            set_mode_from(42, HOLD)
            set_mode_from(255, GUIDED)
            checks = {'unauthorized_id_255_changed_mode': mode == GUIDED,
                      'designated_id_42_changed_mode_observed': True,
                      'final_mode_reflects_last_sender': mode == GUIDED,
                      'remained_disarmed': not armed}
            emit('source_arbitration_observed', sequence=[
                {'sysid': 255, 'mode': GUIDED}, {'sysid': 42, 'mode': HOLD},
                {'sysid': 255, 'mode': GUIDED}], checks=checks)
            set_mode_from(42, HOLD)
            emit('safe_end', mode=mode, armed=armed)
        else:
            # MAV_OPTIONS bit 0 is the global SYSID whitelist documented by
            # ArduPilot. Only 42 should change mode with the selected range.
            if armed:
                raise RuntimeError('F4-5 guarded debe permanecer desarmado')
            for source, requested in ((255, GUIDED), (42, GUIDED),
                                      (255, HOLD), (42, HOLD)):
                conn.mav.srcSystem = source
                conn.mav.set_mode_send(1, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                                       requested)
                emit('mode_command_sent', source_system=source,
                     requested_mode=requested, global_sysid_filter=True)
                observe_until = time.monotonic() + 1.5
                while time.monotonic() < observe_until:
                    receive(0.15)
                expected_mode = (0 if source == 255 and requested == GUIDED else
                                 GUIDED if source == 42 and requested == GUIDED else
                                 GUIDED if source == 255 else HOLD)
                observed = mode == expected_mode
                emit('mode_command_observed', source_system=source,
                     requested_mode=requested, effective_mode=mode,
                     expected_mode=expected_mode, matched=observed)
                if not observed:
                    raise RuntimeError(f'Filtro MAV_OPTIONS no produjo modo esperado: '
                                       f'source={source} requested={requested} effective={mode}')
            checks = {'unauthorized_255_ignored': True,
                      'authorized_42_changes_mode': True,
                      'last_authorized_command_holds': mode == HOLD,
                      'remained_disarmed': not armed}
            emit('source_filter_observed', filter='MAV_OPTIONS bit0',
                 allowed_sysid_range=[42, 42], checks=checks)
            emit('safe_end', mode=mode, armed=armed)
        if case.startswith('f4-5') and not all(checks.values()):
            raise RuntimeError(f'Criterio de observación fallido: {checks}')
        emit('scenario_finished', result='PASS' if all(checks.values()) else 'REVIEW', checks=checks)
    finally:
        if conn is not None:
            try:
                if armed:
                    conn.mav.srcSystem = 255
                    conn.mav.set_mode_send(1, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, HOLD)
                    time.sleep(1)
                    conn.mav.command_long_send(1, 1, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                                               0, 0, 0, 0, 0, 0, 0, 0)
                    time.sleep(2)
            except Exception as exc:
                emit('cleanup_error', error=repr(exc), mode=mode, armed=armed)
            conn.close()
        if sitl.poll() is None:
            os.killpg(sitl.pid, signal.SIGINT)
            try:
                sitl.wait(timeout=12)
            except subprocess.TimeoutExpired:
                os.killpg(sitl.pid, signal.SIGTERM)
                sitl.wait(timeout=5)
        emit('sitl_process_exit', returncode=sitl.returncode)
        events.close()
        log.close()


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--inside':
        inside(os.environ['RRA_F4_FOLDER'], sys.argv[2])
        return
    if len(sys.argv) != 2 or sys.argv[1] not in ('f4-4', 'f4-5', 'f4-5-guarded'):
        raise SystemExit('Uso: fase4_guided_authority.py f4-4|f4-5|f4-5-guarded')
    for exe in (BINARY,):
        if not os.path.isfile(exe):
            raise RuntimeError('Falta el binario ArduRover SITL')
    root = pathlib.Path.home() / 'rra-sitl' / 'fase4'
    root.mkdir(mode=0o700, exist_ok=True)
    output_root = pathlib.Path(BASE).parent / 'evidencias' / 'fase4-guided-2026-11-04' / sys.argv[1]
    output_root.mkdir(parents=True, exist_ok=True)
    folder = tempfile.mkdtemp(prefix=sys.argv[1] + '-', dir=str(output_root))
    env = dict(os.environ, RRA_ORIGINAL_NETNS=os.readlink('/proc/self/ns/net'),
               RRA_F4_FOLDER=folder)
    result = subprocess.run(['unshare', '-Urn', 'python3', os.path.abspath(__file__),
                             '--inside', sys.argv[1]], env=env, timeout=240)
    print(f'FIN {sys.argv[1]} RESULTADO={result.returncode} EVIDENCIA={folder}', flush=True)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
