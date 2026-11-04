"""Evaluación conservadora de mensajes ROS; las edades miden recepción local."""

import math


def sensor_status(kind, msg, age, limit):
    if msg is None:
        return 2, 'Sin datos', {}
    if age is None or age > limit:
        return 2, 'Datos caducados', {}
    if kind == 'gps':
        if (msg.status.status < 0 or not math.isfinite(msg.latitude)
                or not math.isfinite(msg.longitude) or not -90 <= msg.latitude <= 90
                or not -180 <= msg.longitude <= 180):
            return 1, 'Posicion no valida', {}
        values = {'latitud': str(msg.latitude), 'longitud': str(msg.longitude)}
        values['altitud_m'] = str(msg.altitude) if math.isfinite(msg.altitude) else 'desconocida'
        return 0, 'Posicion disponible', values
    if kind == 'imu':
        q = msg.orientation
        xyz = (q.x, q.y, q.z, q.w)
        if (msg.orientation_covariance[0] == -1 or not all(map(math.isfinite, xyz))
                or not 0.95 <= math.sqrt(sum(v * v for v in xyz)) <= 1.05):
            return 1, 'Orientacion no valida', {}
        return 0, 'Orientacion disponible', dict(zip(('x', 'y', 'z', 'w'), map(str, xyz)))
    if kind == 'battery':
        if not msg.present or not math.isfinite(msg.voltage) or msg.voltage <= 0:
            return 1, 'Bateria no disponible', {}
        values = {'voltaje_v': str(msg.voltage)}
        if not math.isfinite(msg.percentage) or not 0 <= msg.percentage <= 1:
            values['porcentaje'] = 'desconocido'
            return 1, 'Voltaje disponible; porcentaje desconocido', values
        values['porcentaje'] = str(msg.percentage * 100)
        return 0, 'Bateria disponible', values
    raise ValueError('Tipo de sensor desconocido')
