"""Cálculo independiente de ROS para datos de estado recibidos por MAVROS."""


def classify_state(connected, received_at, now, stale_after):
    """Devuelve nivel y descripción; utiliza únicamente tiempo monotónico."""
    if received_at is None:
        return 2, 'Sin datos de MAVROS'
    if now - received_at > stale_after:
        return 2, 'Estado de MAVROS caducado'
    if not connected:
        return 1, 'MAVROS sin conexion al vehiculo'
    return 0, 'MAVROS conectado'
