"""Ejecuta SITL en una red WSL aislada y transmite datos a la Orange Pi.

El único canal fuera del namespace es un socket Unix local hacia este proceso;
el proceso reenvía datagramas por stdin de SSH, nunca en sentido inverso.
"""

import os
import pathlib
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time


def stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGINT)
        try:
            process.wait(timeout=12)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)


def inside(output_path, binary, workdir):
    subprocess.run(['/usr/sbin/ip', 'link', 'set', 'lo', 'up'], check=True)
    incoming = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    incoming.bind(('127.0.0.1', 14690))
    incoming.settimeout(0.5)
    outgoing = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    cmd = [binary, '--model', 'rover', '--home=-35.363261,149.165230,584,0',
           '--defaults=/mnt/c/RRA/codex_handoff/sitl/rover-battery-sim.parm',
           '--serial0=udpclient:127.0.0.1:14690',
           '--serial1=udpclient:127.0.0.1:14691',
           '--serial2=udpclient:127.0.0.1:14692', '--sim-address=127.0.0.1']
    with open(os.path.join(workdir, 'sitl.log'), 'w', encoding='utf-8') as log:
        process = subprocess.Popen(cmd, cwd=workdir, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            while True:
                if process.poll() is not None:
                    raise RuntimeError('SITL terminó inesperadamente')
                try:
                    packet, _ = incoming.recvfrom(65535)
                except socket.timeout:
                    continue
                outgoing.sendto(packet, output_path)
        except KeyboardInterrupt:
            pass
        finally:
            stop(process)
            incoming.close()
            outgoing.close()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--inside':
        return inside(*sys.argv[2:])
    binary = os.path.expanduser('~/rra-sitl/ardurover')
    if not os.path.isfile(binary):
        raise RuntimeError('Falta ~/rra-sitl/ardurover')
    folder = tempfile.mkdtemp(prefix='ensayo-', dir=os.path.expanduser('~/rra-sitl'))
    unix_path = os.path.join(folder, 'datos.sock')
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.bind(unix_path)
    sock.settimeout(1)
    ssh = subprocess.Popen([
        '/mnt/c/Windows/System32/OpenSSH/ssh.exe', '-T',
        '-i', r'C:\Users\Juan\.ssh\rra_orangepi_ed25519',
        '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', 'rra@192.168.1.156',
        'bash -c "source /opt/ros/lyrical/setup.bash; '
        'source /home/rra/rra_ws/install/setup.bash; '
        'exec python3 -u /home/rra/rra_ws/tools/sitl_receiver.py"'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    isolated = None
    count = 0
    try:
        first = ssh.stdout.readline().decode('utf-8', errors='replace').strip()
        if first != 'READY':
            raise RuntimeError('Receptor no disponible: ' + first)
        isolated = subprocess.Popen([
            'unshare', '-Urn', 'python3', os.path.abspath(__file__), '--inside',
            unix_path, binary, folder], start_new_session=True)
        deadline = time.monotonic() + 55
        while time.monotonic() < deadline:
            if isolated.poll() is not None:
                raise RuntimeError('Proceso aislado terminó inesperadamente')
            try:
                packet = sock.recv(65535)
            except socket.timeout:
                continue
            ssh.stdin.write(struct.pack('!I', len(packet)) + packet)
            ssh.stdin.flush()
            count += 1
        stop(isolated)
        ssh.stdin.write(struct.pack('!I', 0))
        ssh.stdin.flush()
        ssh.stdin.close()
        output = ssh.stdout.read().decode('utf-8', errors='replace')
        errors = ssh.stderr.read().decode('utf-8', errors='replace')
        code = ssh.wait(timeout=25)
        print('DATAGRAMAS_SITL', count)
        print('SSH_EXIT', code)
        print(output)
        if errors:
            print('SSH_STDERR', errors)
        print('SITL_LOG', os.path.join(folder, 'sitl.log'))
        if code != 0 or count == 0:
            raise RuntimeError('Prueba SITL incompleta')
    finally:
        if isolated is not None:
            stop(isolated)
        if ssh.poll() is None:
            ssh.terminate()
            ssh.wait(timeout=10)
        sock.close()


if __name__ == '__main__':
    main()
