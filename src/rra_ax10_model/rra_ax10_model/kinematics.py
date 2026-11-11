"""Cinemática plana para el AX10; no controla el autopiloto ni el vehículo."""

from dataclasses import dataclass
import math
from typing import Tuple


@dataclass(frozen=True)
class Ax10Geometry:
    wheelbase_m: float = 0.320
    front_track_m: float = 0.203
    rear_track_m: float = 0.203
    wheel_radius_m: float = 0.056
    max_steering_angle_rad: float = math.radians(25.0)
    steering_geometry: str = "parallel"

    def validate(self) -> None:
        if self.wheelbase_m <= 0 or self.front_track_m <= 0 or self.rear_track_m <= 0:
            raise ValueError("wheelbase y vías deben ser positivas")
        if self.wheel_radius_m <= 0:
            raise ValueError("el radio de rueda debe ser positivo")
        if not 0 < self.max_steering_angle_rad < math.pi / 2:
            raise ValueError("el límite de dirección debe estar entre 0 y 90 grados")
        if self.steering_geometry not in ("parallel", "ackermann"):
            raise ValueError("steering_geometry debe ser 'parallel' o 'ackermann'")


def steering_angles(steering_angle_rad: float, geometry: Ax10Geometry) -> Tuple[float, float]:
    """Devuelve ángulos de rueda delantera (izquierda, derecha), radianes.

    `steering_angle_rad` es el ángulo virtual del eje delantero, positivo a la
    izquierda ROS. El valor medido de diferencia Ackermann es 0°, así que el
    modo inicial `parallel` aplica el mismo ángulo a ambas ruedas. El modo
    `ackermann` calcula la geometría ideal usando batalla y vía delantera.
    """
    geometry.validate()
    delta = max(-geometry.max_steering_angle_rad,
                min(geometry.max_steering_angle_rad, steering_angle_rad))
    if geometry.steering_geometry == "parallel" or abs(delta) < 1e-12:
        return delta, delta

    radius = geometry.wheelbase_m / math.tan(abs(delta))
    half_track = geometry.front_track_m / 2.0
    inner = math.atan2(geometry.wheelbase_m, radius - half_track)
    outer = math.atan2(geometry.wheelbase_m, radius + half_track)
    if delta > 0:  # giro a izquierda: rueda izquierda interior
        return inner, outer
    return -outer, -inner


def yaw_rate(speed_mps: float, steering_angle_rad: float, geometry: Ax10Geometry) -> float:
    """Velocidad angular del modelo bicicleta, positiva en giro a izquierda."""
    geometry.validate()
    delta = max(-geometry.max_steering_angle_rad,
                min(geometry.max_steering_angle_rad, steering_angle_rad))
    return speed_mps * math.tan(delta) / geometry.wheelbase_m


def integrate_pose(x: float, y: float, yaw: float, speed_mps: float,
                   steering_angle_rad: float, dt: float,
                   geometry: Ax10Geometry) -> Tuple[float, float, float, float]:
    """Integra un paso simple y devuelve x, y, yaw y yaw_rate del modelo."""
    if dt < 0:
        raise ValueError("dt no puede ser negativo")
    omega = yaw_rate(speed_mps, steering_angle_rad, geometry)
    x += speed_mps * math.cos(yaw) * dt
    y += speed_mps * math.sin(yaw) * dt
    yaw = math.atan2(math.sin(yaw + omega * dt), math.cos(yaw + omega * dt))
    return x, y, yaw, omega
