# Contrato de integración del Computer Companion RRA

**Estado:** borrador local para coordinación con Martín. No se atribuye ninguna
decisión de arquitectura al Companion definitivo. Las líneas marcadas
*pendiente de acuerdo* son propuestas, no compromisos. Actualizado: 2026-11-08.

## Responsabilidades

### H743-WLITE con ArduRover

Responsabilidad prevista: lectura RC, estimación/telemetría del autopiloto,
control de bajo nivel de ESC/dirección, armado/modos, failsafes y protecciones
críticas. El Companion no sustituye estas funciones ni debe ser requisito para
que ArduRover mantenga sus failsafes.

Cableado reportado por el usuario, no re-inspeccionado en esta sesión: ESC
(señal) en S1 sin conductor positivo; servo dirección en S3; receptor RC en RX6;
DroneBridge ESP32 en TX7/RX7; GNSS/brújula en TX2/RX2 y SDA1/SCL1. TX1/RX1
(TELEM2/SERIAL2) ahora conecta la Orange Pi por UART5; se probó telemetría real
con MAVLink2/57600 el 2026-11-07. Firmware ArduRover 4.7.2 y SERIAL2
PROTOCOL/BAUD/OPTIONS constan de capturas de Mission Planner; aún falta export
completo de parámetros, confirmar revisión exacta de PCB y verificar signing.

### Companion provisional (`C:\RRA` / `~/rra_ws`)

- `rra_telemetry`: diagnóstico ROS 2 a partir de mensajes MAVROS; fixture
  sintético y pruebas/registro para integración.
- `rra_companion_readonly`: API fija de estado/versión/parámetro. Conservar sin
  ampliar durante la prioridad de telemetría. BATT_MONITOR puede llegar ambiguo
  por falta de correlación MAVLink; no usar para decisiones críticas.
- `rra_mavros_version_plugin`: consulta específica de versión y parámetro; se
  conserva sin refactor. MAVROS/plugin permanecen en la base de confianza.
- SITL/rosbag2: fixture para comprobar interfaces y ayudar a Martín sin placa.

### Companion definitivo de Martín

No se presume ninguna implementación ni decisión de Martín. Posibles funciones
a coordinar: integración con computador final, sensores, odometría, mapa,
obstáculos, planificación, interfaz y eventual adaptación de órdenes de
navegación a ArduRover. Alcance y autoridad quedan **pendientes de acuerdo con
Martín**. Este prototipo no implementa ni habilita órdenes físicas de motor,
dirección, armado o cambio de modo.

## Interfaces ROS 2 disponibles/propuestas

Se priorizan mensajes ROS estándar y topics que MAVROS ya publica; no se crea
un paquete de mensajes custom sin una necesidad compartida.

| Uso | Topic actual/propuesto | Tipo | Convención / estado |
|---|---|---|---|
| Estado FCU | `/mavros/state` | `mavros_msgs/msg/State` | MAVROS específico: `connected`, `armed`, `mode`; adaptador temporal. |
| Posición GNSS | `/mavros/global_position/global` | `sensor_msgs/msg/NavSatFix` | Lat/lon grados WGS84; altitud/datum debe fijarse antes de fusionar RTK/mapa. |
| Orientación/IMU | `/mavros/imu/data` | `sensor_msgs/msg/Imu` | Cuaternión y vectores ROS; comprobar montaje, calibración y `frame_id`. |
| Odómetro/velocidad | `/mavros/global_position/local` | `nav_msgs/msg/Odometry` | Velocidad m/s; MAVROS transforma posición local a ENU. Frames usuales `map`/`base_link`, sujetos a configuración. |
| Rumbo autopiloto | `/mavros/global_position/compass_hdg` | `std_msgs/msg/Float64` | Grados `[0,360)` desde norte según MAVROS; no incluye unidad/timestamp. Representación común pendiente. |
| Batería | `/mavros/battery` | `sensor_msgs/msg/BatteryState` | V y porcentaje 0–1 si conocidos. |
| Salud/diagnóstico | `/rra/telemetry/diagnostics` | `diagnostic_msgs/msg/DiagnosticArray` | Enlace, GNSS, IMU, batería, velocidad, rumbo y latido del observador. |
| Transformaciones | `/tf`, `/tf_static` | `tf2_msgs/msg/TFMessage` | MAVROS puede publicar TF; frames y autoridad única pendientes de acuerdo. |

MAVROS documenta los mensajes de [global_position](https://github.com/mavlink/mavros/blob/ros2/mavros/src/plugins/global_position.cpp), [frames](https://github.com/mavlink/mavros/blob/ros2/docs/frames.md) y [local_position](https://github.com/mavlink/mavros/blob/ros2/docs/plugins/std/local_position.md). El observador debe reutilizar esos datos, no duplicar su generación.

### Coordenadas, frames y frescura

- GNSS en grados; declarar datum de altitud antes de fusionarlo con RTK/mapa.
- Odometría en metros y m/s en el frame local que MAVROS configure; heading
  `compass_hdg` es una magnitud separada, no un ángulo ENU.
- IMU en el frame declarado por el mensaje. No aplicar transformación hasta
  inspeccionar el montaje físico y `frame_id`.
- Poses de antenas RTK, heading de doble antena, LiDAR y AS5047P sin verificar;
  transforms y tasa quedan por acordar.
- `rra_telemetry` informa edad monotónica desde recepción y
  `edad_muestra_verificada=no`; no acredita la edad de medición en el FCU.

## Dependencias de hardware

- SITL usa UDP de loopback. Para banco, UART5 Orange Pi está habilitada en
  Armbian y aparece como `/dev/ttyS5` con permiso `dialout`.
- Verificar pinout/nivel antes de conectar a GPIO; no asumir tolerancia de
  tensión de la entrada Orange Pi.
- UART FCU propuesta: TELEM2 TX1/RX1 (WLITE/SERIAL2), reportada libre. No asumir
  parámetros ni habilitar retorno antes de las comprobaciones de banco.
- LiDAR/GNSS RTK/encoder sin instalación, puerto, tasa, driver ni TF confirmados.
- El ordenador definitivo no debe depender de `/dev/ttyS5`, `/home/rra`, WSL,
  IP doméstica ni del CPU de Orange Pi.

## Responsabilidades/acuerdos pendientes con Martín

1. Distro ROS 2, plataformas ARM64/x86_64, namespacing y QoS de los topics.
2. Representación común del estado: conservar `mavros_msgs/State` como adaptador
   o normalizarlo a otro mensaje compartido.
3. Datum GNSS, frames autoritativos (`earth/map/odom/base_link/sensores`),
   convención de heading y quién publica TF.
4. Propiedad de drivers GNSS/LiDAR/encoder y enlace de SITL/rosbag con pruebas.
5. Geometría Ackermann medida (wheelbase, track, ángulo/ratio de dirección,
   radio de rueda); no inventar dimensiones ni usarlas en planificación aún.
6. Si habrá comandos de navegación, su tipo, límites, permisos y ejecutor. No se
   habilita interfaz de actuación en el Companion provisional.
7. Selección y destino de rosbag; por defecto solo datos necesarios y locales.

## Regla de sustitución

La lógica reutilizable consume mensajes estándar y parámetros externos; MAVROS,
drivers y UART son adaptadores. Martín debe revisar y acordar las interfaces
antes de portar el código. Los nombres provisionales y valores SITL no son
decisiones acordadas.

## Estado de integración física actualizado — 2026-11-07

Esta nota supersede las frases anteriores de este contrato que dicen que la Orange Pi/H743 está desconectada. Se estableció UART5 de la Orange Pi en `/dev/ttyS5:57600`; MATEK TX1→Orange Pi UART5_RX y Orange Pi UART5_TX→MATEK RX1 con GND común están conectados según el usuario. Con MAVROS se confirmó estado real conectado/HOLD/desarmado, telemetría de GPS, IMU, batería, velocidad y heading; una consulta fija BATT_MONITOR recibió `PARAM_VALUE=4` pero su correlación con la petición es ambigua. No se habilitó el plugin MAVROS estándar `param` ni el plugin `command` en la sesión de observación. La lectura física de AUTOPILOT_VERSION por el plugin local sigue sin respuesta. En 2026-11-07 se probó una rosbag física y replay de siete tópicos; el 2026-11-08 se capturó otra rosbag íntegra de todos los tópicos ROS visibles y se copió al paquete local de integración para Martín.

MATEK y ArduRover: el usuario identifica la placa instalada como H743-WLITE; Mission Planner mostró ArduRover 4.7.2 y capturas de SERIAL2 con protocolo MAVLink2, baud 57 (57600) y OPTIONS 0. La revisión exacta del PCB no está documentada con foto legible. El repositorio público `Gonellarro/RRA` en su README aún dice H743-WING V3 y menciona ROS 2 Jazzy como referencia. Son datos/documentación en discrepancia: no asumir que Martín ya eligió Jazzy ni corregir la documentación compartida sin acuerdo.

El Companion provisional sigue siendo un adaptador de datos/diagnóstico ROS y registro. No publica consignas físicas ni sustituye control, failsafes o RC de ArduRover. La edad del observador es edad de recepción local, no edad del sensor.

## Addendum — ROS 2 real del sensor HC-SR04 y rosbag — 2026-11-08

La H743-WLITE con ArduRover 4.7.2 publica `DISTANCE_SENSOR` y MAVROS `distance_sensor` lo convierte al tipo estándar `sensor_msgs/msg/Range`. En la configuración de hardware del Companion el tópico observado es `/mavros_node/rangefinder_pub`; `frame_id=hc_sr04_front`, radiación ultrasónica, límites 0,20–2,0 m y `field_of_view=0` (ángulo aún no medido). La posición configurada del sensor está a cero como placeholder y no es una medición del montaje. Una muestra ROS de 0,90 m coincide con la medida física de 90 cm que comunicó Juan; Mission Planner mostró lecturas exactas a 30 cm y 90 cm según su comprobación manual. El flujo recibido en ROS 2 está comprobado.

El paquete `ros-lyrical-mavros-extras` se instaló en la Orange Pi, `distance_sensor` se añadió a la allowlist y `rra_telemetry` se reconstruyó. Solo hay `rangefinder_pub` configurado; no se definió un subscriber ROS de distancia que transmita al FCU. Esto no convierte la UART completa en un enlace físicamente de solo lectura: los demás plugins MAVROS y la UART deben evaluarse por separado.

Se capturó rosbag2 SQLite íntegra en el Companion físico (`ros2 bag record -a`): 57,1769 s, 2.730 mensajes, 43 tópicos, incluyendo GNSS crudo/procesado, odometría, IMU, batería, estados, diagnósticos y MAVLink source/sink. `/mavros_node/rangefinder_pub` tiene 57 muestras. No se filtró ni transformó el contenido; se reconstruyó el índice `metadata.yaml` y luego se verificó `ros2 bag info`, reproducción en `ROS_DOMAIN_ID=206` aislado y una muestra Range de 0,90 m. El SHA-256 del DB3 en local coincide byte a byte con el capturado en la Orange Pi. La ubicación local preparada para revisión de Martín es `docs/companion_handoff_martin_2026-11-08/`.

MAVLink Inspector había indicado `DISTANCE_SENSOR` a 2 Hz; la rosbag mostró aproximadamente 1 mensaje Range/s (57/57,18 s). Esa discrepancia queda pendiente de comparar durante una captura sostenida simultánea. No se modificaron parámetros FCU ni se enviaron órdenes de motor, dirección, armado, modo o misión durante la captura. La captura de estado no demuestra por sí sola que el rover estuviera quieto; es una sesión de telemetría física de banco/campo.

La distribución del Companion definitivo de Martín y su namespace siguen pendientes de confirmación. El paquete usa ROS 2 Lyrical y namespace operativo `/mavros_node`; nombres ROS, frames, datum GNSS, QoS y ubicación de drivers son acuerdos por revisar. No se presentan como decisiones tomadas por Martín.

