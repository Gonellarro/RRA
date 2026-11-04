# Observador local de telemetría MAVROS

Paquete provisional de ROS 2 para observar estado, GPS, IMU y batería de MAVROS.
Publica un `diagnostic_msgs/DiagnosticArray` en `/rra/telemetry/diagnostics` con
un estado independiente para conexión y cada sensor. No publica comandos ni
invoca servicios.

Parámetros: `state_topic` (predeterminado `/mavros/state`), `gps_topic`
(`/mavros/global_position/global`), `imu_topic` (`/mavros/imu/data`),
`battery_topic` (`/mavros/battery`), `diagnostics_topic`
(`/rra/telemetry/diagnostics`) y `stale_after_sec` (5 s).
Solo se muestran modo y armado cuando el último estado aún es reciente. La edad
se calcula con tiempo monotónico; el mensaje ROS no suministra un tiempo de
medición del autopiloto. Esto mide la antigüedad de la recepción, no demuestra
que una medición del autopiloto sea reciente o correcta.

El GPS necesita fix y coordenadas finitas dentro de sus rangos; si la altitud
no es finita se indica desconocida. La orientación necesita una estimación no
marcada como ausente y un cuaternión finito con norma 0,95–1,05. La batería
requiere presencia y voltaje finito positivo; un porcentaje no finito o fuera
del rango 0–1 se informa como desconocido, sin descartar el voltaje válido.
Cada sensor se marca como ausente, caducado o inválido sin mostrar valores
obsoletos. Estas comprobaciones son de formato y edad de recepción, no prueban
la exactitud, calibración, salud del sensor ni la seguridad del vehículo.

Tras compilar en `~/rra_ws`: `source ~/rra_ws/install/setup.bash` y
`ros2 run rra_telemetry state_observer`. Para observar el diagnóstico:
`ros2 topic echo /rra/telemetry/diagnostics`. La fuente predeterminada de
MAVROS expone controles: este observador no convierte MAVROS en solo lectura.
No conectarlo a hardware sin aislamiento y procedimiento verificados.

Pruebas en la Orange Pi con el entorno y el overlay cargados:

```bash
cd ~/rra_ws/src/rra_telemetry
python3 -m unittest discover -s test -p 'test_*.py' -v
ROS_DOMAIN_ID=174 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST python3 test/integration_check.py
```

La segunda prueba crea un publicador simulado, no arranca MAVROS y limita el
descubrimiento a la propia máquina. Evita usar simultáneamente el dominio 174
para otro ensayo. La prueba solo cubre el campo de estado, no posición, batería,
orientación, enlace real ni aislamiento de las interfaces de control de MAVROS.

La prueba adicional siguiente arranca MAVROS y un emisor de heartbeat sintético
exclusivamente en `127.0.0.1`, comprueba la pérdida de enlace y graba y
reproduce un rosbag. No es ArduRover SITL y no controla ningún hardware. Utiliza
los puertos locales UDP 14680 y 14681; no debe ejecutarse si están ocupados.

```bash
ROS_DOMAIN_ID=176 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST python3 test/mavlink_loopback_check.py
```
