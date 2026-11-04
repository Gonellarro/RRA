"""Arranca una misión AUTO solo en un namespace de red WSL aislado."""

import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import time

BASE = '/mnt/c/RRA/codex_handoff/sitl'
BINARY = os.path.expanduser('~/rra-sitl/ardurover')
DEPS = os.path.expanduser('~/rra-sitl/deps-pymavlink-2.4.50')


def inside(folder, scenario):
    subprocess.run(['/usr/sbin/ip', 'link', 'set', 'lo', 'up'], check=True)
    original = os.environ.get('RRA_ORIGINAL_NETNS')
    if not original or os.readlink('/proc/self/ns/net') == original:
        raise RuntimeError('No se ha creado aislamiento de red')
    cmd = [BINARY, '--model', 'rover', '--home=-35.363261,149.165230,584,0',
           '--defaults=' + BASE + '/rover-oficial-4.7.2.parm',
           '--serial0=udpclient:127.0.0.1:14690',
           '--serial2=udpclient:127.0.0.1:14692', '--sim-address=127.0.0.1']
    env = dict(os.environ, PYTHONPATH=DEPS, PYTHONUNBUFFERED='1')
    with open(os.path.join(folder, 'sitl.log'), 'w', encoding='utf-8') as log:
        sitl = subprocess.Popen(cmd, cwd=folder, stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True)
        try:
            args = ['python3', BASE + '/mission3_controller.py']
            if scenario == 'stop':
                args.append('--stop-after-first')
            controller = subprocess.run(args,
                                        cwd=folder, env=env, timeout=300)
            if controller.returncode != 0:
                raise RuntimeError(f'El controlador terminó con código {controller.returncode}')
        finally:
            if sitl.poll() is None:
                os.killpg(sitl.pid, signal.SIGINT)
                try:
                    sitl.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    os.killpg(sitl.pid, signal.SIGTERM)
                    sitl.wait(timeout=5)


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--inside':
        if sys.argv[3] not in ('complete', 'stop'):
            raise SystemExit('Escenario inválido')
        return inside(sys.argv[2], sys.argv[3])
    if sys.argv[1:] not in ([], ['--stop-after-first']):
        raise SystemExit('Solo se admite --stop-after-first')
    scenario = 'stop' if sys.argv[1:] else 'complete'
    if not os.path.isfile(BINARY) or not os.path.isdir(DEPS):
        raise RuntimeError('Faltan el binario SITL o las dependencias locales')
    parent = pathlib.Path.home() / 'rra-sitl' / 'misiones'
    parent.mkdir(mode=0o700, exist_ok=True)
    folder = tempfile.mkdtemp(prefix='fase3-', dir=parent)
    print('EVIDENCIA_SITL', folder, flush=True)
    env = dict(os.environ, RRA_ORIGINAL_NETNS=os.readlink('/proc/self/ns/net'))
    result = subprocess.run(['unshare', '-Urn', 'python3', os.path.abspath(__file__),
                             '--inside', folder, scenario], env=env)
    print('RESULTADO', result.returncode, 'EVIDENCIA_SITL', folder, flush=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
