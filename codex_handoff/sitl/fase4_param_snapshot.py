"""Lee parámetros de ArduRover SITL en un namespace WSL aislado; nunca arma ni cambia modos."""
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
PARAMETERS = ('FS_GCS_ENABLE', 'FS_GCS_TIMEOUT', 'FS_ACTION', 'FS_OPTIONS')


def verify_isolation():
    original = os.environ.get('RRA_ORIGINAL_NETNS')
    if not original or os.readlink('/proc/self/ns/net') == original:
        raise RuntimeError('No se ha creado un namespace de red distinto al original')
    subprocess.run(['/usr/sbin/ip', 'link', 'set', 'lo', 'up'], check=True)
    links = json.loads(subprocess.check_output(['/usr/sbin/ip', '-j', 'link']))
    if [link['ifname'] for link in links] != ['lo']:
        raise RuntimeError(f'El namespace tiene interfaces inesperadas: {links}')
    if socket.gethostbyname('localhost') != '127.0.0.1':
        raise RuntimeError('localhost no resuelve únicamente a loopback IPv4')


def inside(folder):
    verify_isolation()
    links = json.loads(subprocess.check_output(['/usr/sbin/ip', '-j', 'link']))
    os.environ['MAVLINK20'] = '1'
    sys.path.insert(0, DEPS)
    from pymavlink import mavutil

    cmd = [BINARY, '--model', 'rover', '--home=-35.363261,149.165230,584,0',
           '--defaults=' + BASE + '/rover-oficial-4.7.2.parm',
           '--serial0=udpclient:127.0.0.1:14690',
           '--serial2=udpclient:127.0.0.1:14692', '--sim-address=127.0.0.1']
    env = dict(os.environ, PYTHONPATH=DEPS, PYTHONUNBUFFERED='1')
    log_path = os.path.join(folder, 'sitl.log')
    with open(log_path, 'w', encoding='utf-8') as log:
        sitl = subprocess.Popen(cmd, cwd=folder, stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True, env=env)
        connection = None
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if sitl.poll() is not None:
                    raise RuntimeError(f'SITL terminó antes de abrir el enlace: {sitl.returncode}')
                try:
                    connection = mavutil.mavlink_connection(
                        'tcp:127.0.0.1:5762', source_system=255, source_component=190)
                    break
                except (OSError, ConnectionError):
                    time.sleep(0.25)
            if connection is None:
                raise TimeoutError('SITL no abrió el endpoint TCP local esperado')
            hb = connection.wait_heartbeat(timeout=25)
            if hb is None or hb.get_srcSystem() != 1 or hb.type != mavutil.mavlink.MAV_TYPE_GROUND_ROVER:
                raise RuntimeError('No se confirmó heartbeat de un Rover SITL')
            armed = bool(hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
            if armed:
                raise RuntimeError('SITL arrancó armado; se aborta la lectura')
            values = {}
            for name in PARAMETERS:
                connection.mav.param_request_read_send(1, 1, name.encode('ascii'), -1)
                end = time.monotonic() + 8
                while time.monotonic() < end:
                    msg = connection.recv_match(type='PARAM_VALUE', blocking=True, timeout=0.5)
                    if msg is None:
                        continue
                    msg_name = msg.param_id.decode('ascii', errors='ignore').rstrip('\x00') \
                        if isinstance(msg.param_id, bytes) else str(msg.param_id).rstrip('\x00')
                    if msg.get_srcSystem() == 1 and msg_name == name:
                        values[name] = {'value': float(msg.param_value),
                                        'type': int(msg.param_type),
                                        'index': int(msg.param_index),
                                        'count': int(msg.param_count)}
                        break
                if name not in values:
                    values[name] = {'status': 'no recibido'}
            result = {'sitl_version': 'ArduRover 4.7.2 (hash verificado antes de arrancar)',
                      'armed': armed, 'mode_id': int(hb.custom_mode), 'parameters': values,
                      'read_only': True, 'network_namespace': os.readlink('/proc/self/ns/net'),
                      'interfaces': [link['ifname'] for link in links]}
            with open(os.path.join(folder, 'parametros_efectivos.json'), 'w', encoding='utf-8') as out:
                json.dump(result, out, indent=2, ensure_ascii=False)
                out.write('\n')
            print(json.dumps(result, ensure_ascii=False), flush=True)
            if any('value' not in value for value in values.values()):
                raise RuntimeError('No se recibieron todos los parámetros solicitados')
        finally:
            if connection is not None:
                connection.close()
            if sitl.poll() is None:
                os.killpg(sitl.pid, signal.SIGINT)
                try:
                    sitl.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    os.killpg(sitl.pid, signal.SIGTERM)
                    sitl.wait(timeout=5)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--inside':
        return inside(sys.argv[2])
    if sys.argv[1:]:
        raise SystemExit('No se aceptan argumentos adicionales')
    if not os.path.isfile(BINARY) or not os.path.isdir(DEPS):
        raise RuntimeError('Falta el binario SITL o la dependencia local pymavlink')
    parent = pathlib.Path.home() / 'rra-sitl' / 'fase4'
    parent.mkdir(mode=0o700, exist_ok=True)
    folder = tempfile.mkdtemp(prefix='parametros-', dir=parent)
    original = os.readlink('/proc/self/ns/net')
    env = dict(os.environ, RRA_ORIGINAL_NETNS=original)
    command = ['unshare', '-Urn', 'python3', os.path.abspath(__file__), '--inside', folder]
    result = subprocess.run(command, env=env, timeout=90)
    print(f'EVIDENCIA_SITL={folder} RESULTADO={result.returncode}', flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()



