"""Evaluación conservadora de mensajes ROS; las edades miden recepción local."""

import math


def sensor_status(kind, msg, age, limit):
    age_values = {}
    if age is not None and math.isfinite(age) and age >= 0:
        age_values['edad_recepcion_s'] = f'{age:.3f}'
    age_values['edad_muestra_verificada'] = 'no'
    if msg is None:
        return 2, 'Sin datos', age_values
    if age is None or age > limit:
        return 2, 'Datos caducados', age_values
    if kind == 'gps':
        if (msg.status.status < 0 or not math.isfinite(msg.latitude)
                or not math.isfinite(msg.longitude) or not -90 <= msg.latitude <= 90
                or not -180 <= msg.longitude <= 180):
            return 1, 'Posicion no valida', age_values
        values = {'latitud': str(msg.latitude), 'longitud': str(msg.longitude)}
        values['altitud_m'] = str(msg.altitude) if math.isfinite(msg.altitude) else 'desconocida'
        values.update(age_values)
        return 0, 'Posicion disponible', values
    if kind == 'imu':
        q = msg.orientation
        xyz = (q.x, q.y, q.z, q.w)
        if (msg.orientation_covariance[0] == -1 or not all(map(math.isfinite, xyz))
                or not 0.95 <= math.sqrt(sum(v * v for v in xyz)) <= 1.05):
            return 1, 'Orientacion no valida', age_values
        values = dict(zip(('x', 'y', 'z', 'w'), map(str, xyz)))
        values.update(age_values)
        return 0, 'Orientacion disponible', values
    if kind == 'battery':
        if not msg.present or not math.isfinite(msg.voltage) or msg.voltage <= 0:
            return 1, 'Bateria no disponible', age_values
        values = {'voltaje_v': str(msg.voltage)}
        if not math.isfinite(msg.percentage) or not 0 <= msg.percentage <= 1:
            values['porcentaje'] = 'desconocido'
            values.update(age_values)
            return 1, 'Voltaje disponible; porcentaje desconocido', values
        values['porcentaje'] = str(msg.percentage * 100)
        values.update(age_values)
        return 0, 'Bateria disponible', values
    if kind == 'speed':
        linear = msg.twist.twist.linear
        xyz = (linear.x, linear.y, linear.z)
        if not all(map(math.isfinite, xyz)):
            return 1, 'Velocidad no valida', age_values
        speed = math.sqrt(sum(value * value for value in xyz))
        values = {'velocidad_m_s': f'{speed:.3f}'}
        values.update(age_values)
        return 0, 'Velocidad disponible', values
    if kind == 'heading':
        heading = msg.data
        if not math.isfinite(heading) or not 0 <= heading < 360:
            return 1, 'Rumbo no valido', age_values
        values = {'rumbo_grados_norte': f'{heading:.2f}'}
        values.update(age_values)
        return 0, 'Rumbo disponible', values
    raise ValueError('Tipo de sensor desconocido')
