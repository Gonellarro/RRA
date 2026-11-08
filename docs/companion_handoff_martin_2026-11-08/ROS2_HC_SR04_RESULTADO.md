# Evidencia de recepción ROS 2 del HC-SR04 — 2026-11-08

- Orange Pi Zero 2W, Ubuntu 26.04 ARM64, ROS 2 Lyrical.
- Enlace UART5 `/dev/ttyS5` a 57600; MAVROS identifica FCU ArduPilot.
- Paquete instalado en la Pi: `ros-lyrical-mavros-extras` (versión apt candidata 2.16.0-1resolute.20260928.095144). El plugin MAVROS `distance_sensor` vive en `mavros_extras`.
- Paquete local `rra_telemetry` reconstruido correctamente con `colcon build --packages-select rra_telemetry`; el YAML instalado coincide con el fuente.
- Tópico: `/mavros_node/rangefinder_pub`, tipo `sensor_msgs/msg/Range`, publicador MAVROS `distance_sensor`.
- Muestra en arranque normal: `frame_id=hc_sr04_front`, `radiation_type=0` (ultrasonido), `min_range=0.2 m`, `max_range=2.0 m`, `range=0.899999976 m`.
- La medida coincide con el blanco de 90 cm comunicado por el usuario y con la prueba previa de Mission Planner. Esto valida paso DISTANCE_SENSOR H743 → MAVLink → plugin MAVROS → ROS 2.
- Mission Planner había mostrado DISTANCE_SENSOR a 2 Hz. Una observación corta de `ros2 topic hz` dio intervalos de aproximadamente 1 s; no se considera aún una medida representativa ni se concluye pérdida sistemática. Comparar más tiempo y simultáneamente antes de declarar la tasa.
- Configuración únicamente de `rangefinder_pub`: no se configura suscriptor ROS→MAVLink para distancia. No se enviaron comandos, no se cambiaron parámetros/modo/armado ni actuadores.
- MAVROS y observer del launch normal quedaron en ejecución al terminar. Launch manual, sin afirmar servicio/autostart.
- Persisten en log: timeout de `AUTOPILOT_VERSION` (el FCU vuelve a capacidades por defecto) y `PreArm: Radio failsafe on`; no impidieron recibir distancia.

Comprobación reproducible en Pi:
```bash
source /opt/ros/lyrical/setup.bash
source ~/rra_ws/install/setup.bash
ROS_DOMAIN_ID=205 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST ros2 topic echo /mavros_node/rangefinder_pub sensor_msgs/msg/Range
```

Configuración fuente archivada junto a esta evidencia: `mavros_hardware.yaml`.
