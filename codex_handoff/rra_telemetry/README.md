# Observador local de telemetría MAVROS

Paquete provisional de ROS 2 para observar estado, GPS, IMU y batería, con una
fuente sintética para integración y reproducción reproducible.
Publica un `diagnostic_msgs/DiagnosticArray` en `/rra/telemetry/diagnostics` con
un estado independiente para conexión y cada sensor. No publica comandos ni
invoca servicios.

Parámetros: `state_topic` (predeterminado `/mavros/state`), `gps_topic`
(`/mavros/global_position/global`), `imu_topic` (`/mavros/imu/data`),
`battery_topic` (`/mavros/battery`), `odometry_topic`
(`/mavros/global_position/local`), `heading_topic`
(`/mavros/global_position/compass_hdg`), `diagnostics_topic`
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

La edad expuesta (`edad_recepcion_s` o `edad_recepcion_ms`) es desde que el
observador recibió el mensaje usando reloj monotónico local. `edad_muestra_verificada=no`
deja explícito que el timestamp/origen del FCU no se ha validado. No equivale a
edad de medición del sensor.

## Interfaces provisionales

| Topic por defecto | Tipo | Productor | QoS |
|---|---|---|---|
| `/mavros/state` | `mavros_msgs/msg/State` | adaptador MAVROS | reliable, depth 10 |
| `/mavros/global_position/global` | `sensor_msgs/msg/NavSatFix` | adaptador MAVROS | perfil sensor |
| `/mavros/imu/data` | `sensor_msgs/msg/Imu` | adaptador MAVROS | perfil sensor |
| `/mavros/battery` | `sensor_msgs/msg/BatteryState` | adaptador MAVROS | perfil sensor |
| `/mavros/global_position/local` | `nav_msgs/msg/Odometry` | adaptador MAVROS | perfil sensor |
| `/mavros/global_position/compass_hdg` | `std_msgs/msg/Float64` | adaptador MAVROS | perfil sensor |
| `/rra/telemetry/diagnostics` | `diagnostic_msgs/msg/DiagnosticArray` | `state_observer` | reliable, depth 10 |

`mavros_msgs/State` es específico de MAVROS y solo representa estado de enlace,
armado y modo. Para integrar con el Companion de Martín, conviene acordar los
mensajes estándar de sensores y los diagnósticos; estos nombres y QoS son una
propuesta local, no un contrato ya acordado. Mantener el adaptador MAVROS
separable permitirá cambiar el origen del FCU sin acoplar consumidores.

### Telemetría simulada y rosbag2

`telemetry_simulator` publica datos deterministas, coherentes entre GNSS/IMU/
odometría/rumbo, y no tiene interfaz de control.
Sus topics por defecto están aislados bajo `/rra/sim/fcu/`; el modo SIMULATION,
GPS de Madrid, batería 12.4 V/75%, velocidad 0 m/s y rumbo 90° son valores
ficticios. La odometría usa ENU; la velocidad y rumbo son configurables. El
observador permite remapear topics:

```bash
ros2 run rra_telemetry telemetry_simulator
ros2 run rra_telemetry state_observer --ros-args \
  -p state_topic:=/rra/sim/fcu/state \
  -p gps_topic:=/rra/sim/fcu/global_position \
  -p imu_topic:=/rra/sim/fcu/imu \
  -p battery_topic:=/rra/sim/fcu/battery \
  -p odometry_topic:=/rra/sim/fcu/global_position/local \
  -p heading_topic:=/rra/sim/fcu/compass_hdg
ros2 topic echo /rra/telemetry/diagnostics
ros2 bag record -o /tmp/rra_telemetry_demo \
  /rra/sim/fcu/state /rra/sim/fcu/global_position \
  /rra/sim/fcu/imu /rra/sim/fcu/battery \
  /rra/sim/fcu/global_position/local /rra/sim/fcu/compass_hdg \
  /rra/telemetry/diagnostics
```

Grabar solo mientras los nodos están activos; parar rosbag con Ctrl-C y validar
con `ros2 bag info /tmp/rra_telemetry_demo`. Los bags pueden contener ubicación
y telemetría: conservarlos localmente y borrarlos manualmente cuando ya no hagan
falta. No se grabará automáticamente.

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

No se instala Nav2, SLAM ni componentes pesados. Estos topics no autorizan
actuación ni presentan la telemetría sintética como datos del rover.

## Velocidad, rumbo y salud del proceso

El diagnóstico incluye un latido de `state_observer` a 1 Hz y estados separados
para velocidad y rumbo, calculados desde `/mavros/global_position/local`
(`nav_msgs/Odometry`) y `/mavros/global_position/compass_hdg`
(`std_msgs/Float64`). No se duplica un topic de estado cinemático. La velocidad
es la magnitud del vector lineal en m/s; el rumbo MAVROS está en grados desde
norte. El `Float64` no lleva unidad ni timestamp, por lo que el significado se
debe conservar en el contrato hasta acordar un tipo común con Martín.

El simulador incluye `/rra/sim/fcu/global_position/local` y
`/rra/sim/fcu/compass_hdg`; default estacionario a 0 m/s y rumbo 90° (este), con
orientación ENU coherente. No representa la dinámica o calibración real del RRA.

## Ejecución portable y grabación limitada

El paquete instala launch, configuración YAML y grabador bajo su propio prefix
ament; no requiere rutas de usuario ni conocimiento de la Orange Pi. El modo
`mavros` solo inicia el observador y necesita que MAVROS ya esté arrancado por
separado. El modo `sim` inicia el simulador y remapea el observador a su namespace
aislado. El launch no inicia MAVROS, seriales ni interfaces de control:

```bash
ROS_DOMAIN_ID=183 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST \
  ros2 launch rra_telemetry telemetry.launch.py source:=sim
```

Para observar una fuente MAVROS ya activa, usar `source:=mavros`. Los parámetros
por defecto están en `config/observer.yaml` y `config/simulator.yaml`; se pueden
sustituir con los argumentos `observer_params:=/ruta/observer.yaml` y
`simulator_params:=/ruta/simulator.yaml`.

En otra terminal y con el mismo dominio, el grabador conserva una lista fija de
siete topics, limita cada ejecución a 300 segundos y comprueba el resultado:

```bash
bash "$(ros2 pkg prefix --share rra_telemetry)/scripts/record_telemetry.sh" \
  /tmp/rra-demo 30 sim
```

Usar el tercer argumento `mavros` para registrar los topics MAVROS. El destino
debe ser nuevo; el script no sobrescribe bolsas existentes. La duración es un
límite máximo; el envío de SIGINT cierra rosbag2 ordenadamente y se muestra
`ros2 bag info`. La duración efectiva puede ser menor por el descubrimiento y la
suscripción inicial: revisar duración, mensajes y tópicos antes de reutilizar el
bag. Las bolsas siguen siendo locales.
