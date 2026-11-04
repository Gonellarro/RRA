"""Resume y valida evidencia de F4-1…F4-3; no interactúa con el SITL."""
import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path.home() / 'rra-sitl' / 'deps-pymavlink-2.4.50'))
from pymavlink import mavutil

EXPECTED = {0: 10, 1: 4, 2: 10}


def summarize(folder):
    folder = pathlib.Path(folder)
    events = [json.loads(line) for line in (folder / 'mavlink_events.jsonl').read_text(encoding='utf-8').splitlines()]
    first = lambda kind: next((event for event in events if event.get('kind') == kind), None)
    param = first('effective_parameters')
    loss = first('gcs_loss_observed')
    reconnect = first('gcs_reconnected')
    passed = first('scenario_passed')
    safe = first('safe_end')
    stop = first('gcs_heartbeat_stopped')
    statuses = [event.get('text', '') for event in events if event.get('kind') == 'statustext']

    df = mavutil.mavlink_connection(str(folder / 'logs' / '00000001.BIN'))
    counts = collections.Counter()
    modes = []
    while True:
        msg = df.recv_match()
        if msg is None:
            break
        kind = msg.get_type()
        counts[kind] += 1
        if kind == 'MODE':
            mode = int(msg.ModeNum)
            if not modes or modes[-1] != mode:
                modes.append(mode)
    df.close()

    enable = int(folder.name.split('enable-')[-1])
    params = param['values'] if param else {}
    expected_params = {'FS_GCS_ENABLE': float(enable), 'FS_GCS_TIMEOUT': 5.0,
                       'FS_ACTION': 2.0, 'FS_OPTIONS': 0.0,
                       'FS_THR_ENABLE': 0.0, 'RC_PROTOCOLS': 0.0}
    gcs_failsafe = 'GCS Failsafe' in statuses
    radio_failsafe = 'Radio Failsafe' in statuses
    continued_auto = 'Failsafe - Continuing Auto Mode' in statuses
    gcs_time = next((e['monotonic'] for e in events
                     if e.get('kind') == 'statustext' and e.get('text') == 'GCS Failsafe'), None)
    delay = round(gcs_time - stop['monotonic'], 2) if gcs_time is not None and stop else None

    checks = {
        'loopback_only': bool(first('startup') and first('startup').get('interfaces') == ['lo']),
        'parameters_match': params == expected_params,
        'gcs_timeout_event_expected': (enable == 0 and not gcs_failsafe) or (enable in (1, 2) and gcs_failsafe),
        'no_radio_failsafe': not radio_failsafe,
        'mode_after_loss_expected': bool(loss and loss.get('mode') == EXPECTED[enable]),
        'mode_after_reconnect_expected': bool(reconnect and reconnect.get('mode') == EXPECTED[enable]),
        'passed_event': passed is not None,
        'safe_end_hold_disarmed': bool(safe and safe.get('mode') == 4 and safe.get('armed') is False),
        'dataflash_has_auto_hold': 10 in modes and 4 in modes,
    }
    if enable == 2:
        checks['continue_auto_message'] = continued_auto
    if enable == 1:
        checks['gcs_failsafe_delay_approx_5s'] = delay is not None and 4.5 <= delay <= 7.0

    return {'case': enable, 'effective_parameters': params,
            'time_to_gcs_failsafe_s': delay,
            'gcs_failsafe_message': gcs_failsafe,
            'continue_auto_message': continued_auto,
            'radio_failsafe_message': radio_failsafe,
            'mode_after_heartbeat_loss': loss.get('mode') if loss else None,
            'mode_after_reconnect': reconnect.get('mode') if reconnect else None,
            'waypoints_reached_before_and_during_loss': loss.get('reached') if loss else None,
            'safe_end': safe,
            'dataflash_message_counts': {k: counts[k] for k in ('MODE', 'POS', 'GPS', 'CMD')},
            'dataflash_mode_sequence': modes,
            'checks': checks, 'result': 'PASS' if all(checks.values()) else 'REVIEW'}


if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise SystemExit('Uso: fase4_summarize.py salida.json carpeta_enable0 [carpeta_enable1 carpeta_enable2]')
    output = pathlib.Path(sys.argv[1])
    results = [summarize(path) for path in sys.argv[2:]]
    payload = {'date': '2026-11-04', 'scope': 'ArduRover 4.7.2 SITL only; isolated WSL loopback',
               'results': results, 'overall': 'PASS' if all(x['result'] == 'PASS' for x in results) else 'REVIEW'}
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(payload, indent=2, ensure_ascii=False))
