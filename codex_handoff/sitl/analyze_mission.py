"""Resume un DataFlash SITL y su diario de eventos locales."""

import collections
import json
import math
import pathlib
import sys

from pymavlink import mavutil


def distance(a, b):
    y = (a[0] - b[0]) * 111320
    x = (a[1] - b[1]) * 111320 * math.cos(math.radians(b[0]))
    return math.hypot(x, y)


def analyze(folder):
    folder = pathlib.Path(folder)
    log = mavutil.mavlink_connection(str(folder / 'logs' / '00000001.BIN'))
    counts = collections.Counter()
    modes, points = [], []
    while True:
        msg = log.recv_match()
        if msg is None:
            break
        kind = msg.get_type()
        counts[kind] += 1
        if kind == 'MODE':
            modes.append({'time_us': msg.TimeUS, 'mode': msg.ModeNum})
        elif kind == 'POS' and math.isfinite(msg.Lat) and math.isfinite(msg.Lng):
            points.append((msg.Lat, msg.Lng))
    log.close()
    events = [json.loads(line) for line in (folder / 'mission_events.jsonl').read_text().splitlines()]
    done = next(event for event in events if event['kind'] == 'mission_complete')
    final = next(event for event in events if event['kind'] == 'safe_end')
    if len(points) < 2 or not all(mode in [item['mode'] for item in modes] for mode in (10, 4)):
        raise RuntimeError('Registro sin posiciones o modos AUTO/HOLD')
    return {'folder': str(folder), 'counts': {k: counts[k] for k in ('POS', 'GPS', 'MODE', 'CMD')},
            'modes': modes, 'max_distance_from_start_m': round(max(distance(p, points[0]) for p in points), 2),
            'position_path_length_m': round(sum(distance(a, b) for a, b in zip(points, points[1:])), 2),
            'mission_complete': done, 'safe_end': final}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit('Uso: analyze_mission.py CARPETA [CARPETA...]')
    print(json.dumps([analyze(folder) for folder in sys.argv[1:]], indent=2))
