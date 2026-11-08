# RRA Companion: paquete de integración para revisión de Martín

Fecha de preparación: 2026-11-08. Estado: paquete publicado en la rama `main` para revisión de Martín. Contiene telemetría ROS cruda según la decisión de Juan.

## Qué incluye

- `CONTRATO_INTEGRACION_COMPANION.md`: responsabilidades, interfaces actuales y acuerdos que aún hay que tomar con Martín. Las propuestas no se presentan como decisiones suyas.
- `rosbag2_h743_raw_telemetry_2026-11-08/`: rosbag2 íntegra con la telemetría cruda anunciada en ROS durante una sesión real Orange Pi ↔ H743.
- `ROS2_HC_SR04_RESULTADO.md`: resultado de la validación del sonar hasta `/mavros_node/rangefinder_pub`.
- `mavros_hardware.yaml`: configuración de MAVROS usada en el Companion provisional.
- [`../INVENTARIO_HARDWARE_COMPANION.md`](../INVENTARIO_HARDWARE_COMPANION.md): modelos y versiones documentados del rover, sensores, Orange Pi y software.

## Captura ROS bag

La Orange Pi Zero 2W ejecutaba Ubuntu 26.04 ARM64, ROS 2 Lyrical y MAVROS conectado por UART5 (`/dev/ttyS5`, 57600 baud) a la Matek H743-WLITE con ArduRover 4.7.2. Se grabaron **todos los tópicos ROS visibles** con `ros2 bag record -a`, sin excluir ni modificar mensajes. Se incluyen posición GNSS cruda y procesada, odometría, IMU, batería, estado, diagnósticos, los mensajes de MAVROS y `/uas1/mavlink_source` y `/uas1/mavlink_sink`.

La grabación dura **57,1769 s**, contiene **2.730 mensajes** en **43 tópicos** y ocupa aproximadamente **714 KiB** según `ros2 bag info`. El tópico del sonar `/mavros_node/rangefinder_pub` (`sensor_msgs/msg/Range`) contiene **57 mensajes**; una muestra reproducida da `0,90 m`, `min_range=0,20 m`, `max_range=2,0 m`, `frame_id=hc_sr04_front`. El archivo de datos DB3 conserva los mensajes CDR exactamente como se grabaron; solo se reconstruyó `metadata.yaml` mediante `ros2 bag reindex` para recuperar el índice legible por rosbag2. El hash local coincide con el del archivo DB3 en la Orange Pi.

La medida física a 30 cm y 90 cm fue reportada por Juan como coincidente en Mission Planner. La captura presente se tomó con una lectura aproximada de 90 cm. Mission Planner había indicado `DISTANCE_SENSOR` a 2 Hz, mientras que la bag contiene 57 medidas de rango en 57,18 s (aprox. 1 Hz); esa diferencia queda pendiente de comparar con una captura más larga.

## Inspección y reproducción

En una instalación ROS 2 Lyrical con los tipos `mavros_msgs` disponibles:

```bash
ros2 bag info rosbag2_h743_raw_telemetry_2026-11-08
ROS_DOMAIN_ID=206 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST ros2 bag play rosbag2_h743_raw_telemetry_2026-11-08
```

Durante la preparación, la bag se reprodujo en un dominio DDS aislado (`ROS_DOMAIN_ID=206`) y una suscripción a `/mavros_node/rangefinder_pub` recibió un mensaje `sensor_msgs/Range` de 0,90 m. No había MAVROS conectado a la UART en ese dominio.

## Tópicos de la captura

Los nombres reflejan el namespace operativo del launch (`/mavros_node`). El contrato no obliga al Companion definitivo a conservar ese namespace; debe acordarse con Martín. Se grabaron además los tópicos de sistema y eventos que aparecen en `metadata.yaml`.

- `/mavros_node/state` — `mavros_msgs/msg/State`
- `/mavros_node/global_position/global`, `/mavros_node/global_position/raw/fix` — `sensor_msgs/msg/NavSatFix`
- `/mavros_node/global_position/local`, `/mavros_node/local_position/odom` — `nav_msgs/msg/Odometry`
- `/mavros_node/imu/data`, `/mavros_node/imu/data_raw` — `sensor_msgs/msg/Imu`
- `/mavros_node/global_position/compass_hdg` — `std_msgs/msg/Float64`
- `/mavros_node/battery` — `sensor_msgs/msg/BatteryState`
- `/mavros_node/rangefinder_pub` — `sensor_msgs/msg/Range`
- `/rra/telemetry/diagnostics` — `diagnostic_msgs/msg/DiagnosticArray`
- `/uas1/mavlink_source`, `/uas1/mavlink_sink` — `mavros_msgs/msg/Mavlink`
- `/tf`, `/tf_static`, `/diagnostics`, `/rosout`, `/parameter_events`, más el resto de tópicos MAVROS activos detallados en `metadata.yaml`.

## Límites y puntos abiertos

- Es una captura corta de telemetría real, no una validación dinámica del rover ni una bag SITL.
- La geometría Ackermann y los marcos/posiciones físicas de sensores siguen pendientes de medir; el `sensor_position` configurado a cero es provisional.
- No se enviaron órdenes de motores, dirección, armado, modo ni misión durante la captura.
- Persisten el timeout del servicio `AUTOPILOT_VERSION` y el mensaje `PreArm: Radio failsafe on` observado en el enlace.
- No se ha confirmado qué distribución ROS 2 usa Martín en x86_64; `mavros_msgs` y ROS 2 Lyrical corresponden al entorno de esta captura.
- El archivo contiene los datos tal como llegaron al Companion, incluidos datos GNSS y mensajes MAVLink. Se conserva sin anonimización por decisión de Juan.
