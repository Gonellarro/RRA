# Inventario del rover y del Companion provisional

Actualizado: 2026-11-10. Este inventario distingue lo reportado por el usuario,
lo observado en Mission Planner y lo validado en el flujo ROS. No sustituye una
lectura nueva de la controladora ni una inspección física de las revisiones.

## Autopiloto y hardware del rover

| Elemento | Modelo/versión y estado | Evidencia / límite |
|---|---|---|
| Controladora | MATEK H743-WLITE; revisión de PCB sin confirmar | Modelo identificado por el usuario; revisión no legible en las fotos disponibles. |
| Firmware | ArduRover 4.7.2; compilación visible `fb773567` | Versión y target `MatekH743` mostrados en Mission Planner el 2026-11-07; no es una lectura nueva en esta actualización. |
| Receptor RC | FlySky FS-BS8, conectado a RX6 | Modelo y conexión comunicados por el usuario; sustituye al FS-A8S anotado por error anteriormente. |
| GNSS | QUEScan AN251 M10, conectado a TX2/RX2 | Modelo/conexión reportados por el usuario. No se ha confirmado RTK ni precisión absoluta. |
| Brújula | QMC5883L del conjunto GNSS, bus I²C SDA1/SCL1 | Identificación y conexión reportadas por el usuario. |
| Bridge GCS | Seeed XIAO ESP32-S3 con DroneBridge, conectado a TX7/RX7 | Modelo y cableado reportados por el usuario; mantiene el enlace con Mission Planner/QGroundControl. |
| Sonar frontal | HC-SR04 reportado en S4/GPIO53 TRIG y S5/GPIO54 ECHO, con 5 V y GND común | El usuario reportó mediciones a 30 y 90 cm. MAVROS recibió `sensor_msgs/msg/Range` de unos 0,90 m; la posición física y el campo de visión aún no están medidos. |
| ESC y motor | ESC Axial AE-2; motor Axial del conjunto AX10 | Modelo visible en fotos anteriores y comunicado por el usuario; el pack de motor alimenta solo el ESC/motor. |
| Servo de dirección | TowerPro MG995, señal en S3 | Modelo legible en la foto aportada anteriormente; alimentación por el rail de la Matek, según cableado reportado. |
| Batería de motor | HOOVO LiPo 2S, 7,4 V nominal, 5200 mAh, 80C, XT60 | Modelo visto en ficha comercial; el usuario informa que la batería alimenta solo ESC/motor. AE-2 debe tener activo su corte LiPo para 2S; estado real pendiente de comprobar. |
| Batería de electrónica | Mismo pack HOOVO LiPo 2S, 7,4 V nominal, 5200 mAh, 80C, XT60 | Según el usuario, idéntica a la de motor; conectada a BAT+/BAT− de H743 a través de fusible de 30 A e interruptor. |
| Distribución de energía | Batería de motor separada de batería electrónica; H743 alimenta Companion y periféricos | Distribución comunicada: servo, señal PWM ESC, GNSS/brújula, Orange Pi, HC-SR04, FS-BS8 y XIAO ESP32-S3 cuelgan de la Matek. No está mapeado todavía qué rail alimenta cada periférico ni la corriente total/picos. El cable rojo BEC del ESC está desconectado; la señal comparte masa con la controladora. El fusible no protege contra sobredescarga. |

La mención antigua a UM982+RTK describe una mejora prevista, no el GNSS instalado
identificado actualmente. No atribuir al sensor M10 prestaciones RTK.

## Companion provisional y software instalado

| Componente | Versión / detalle documentado |
|---|---|
| Ordenador | Orange Pi Zero 2W, 4 GB RAM |
| Sistema | Armbian comunitario `26.11.0-trunk.120`, Ubuntu 26.04 Resolute ARM64 |
| Kernel | `6.18.60-current-sunxi64` |
| ROS 2 | Lyrical; paquete `ros-lyrical-ros-base` `0.13.0-3resolute.20260919.195359` |
| Ejemplos ROS Python | `ros-lyrical-demo-nodes-py` `0.37.9-1resolute.20260915.091238` |
| MAVROS | 2.16.0 |
| Plugins MAVROS extra | `ros-lyrical-mavros-extras`; versión apt registrada `2.16.0-1resolute.20260928.095144`; plugin `distance_sensor` habilitado |
| Build ROS | `python3-colcon-common-extensions` `0.3.0-100` |
| Dependencias ROS | `python3-rosdep` `0.27.0-1` |
| Paquetes propios | `rra_telemetry`; `rra_companion_readonly`; `rra_mavros_version_plugin` |
| Enlace de telemetría | UART5 `/dev/ttyS5` ↔ TX1/RX1 (TELEM2/SERIAL2), MAVLink2 a 57600 baud |

Las versiones de los paquetes describen la instalación documentada, no una
consulta en vivo de dpkg realizada al publicar este inventario. La distribución
ROS 2 del Companion definitivo de Martín debe acordarse por separado.

## Verificación funcional del sonar

- En Mission Planner, el usuario reportó lecturas coincidentes con blancos a
  30 cm y 90 cm.
- MAVROS `distance_sensor` publicó en `/mavros_node/rangefinder_pub` como
  `sensor_msgs/msg/Range`; la bag contiene 57 mensajes en 57,18 s y una muestra
  reproducida de aproximadamente 0,90 m.
- El perfil configura `frame_id=hc_sr04_front`, rango 0,20–2,0 m y
  `field_of_view=0.0` como valor provisional. El montaje/ángulo no está medido.
- No se ha habilitado evitación ni se atribuye al HC-SR04 una función de parada
  automática. La tasa aproximada de 1 Hz en la bag requiere comparación sostenida
  con la indicación de 2 Hz del Inspector de Mission Planner.

Evidencia y comandos de reproducción: [resultado ROS 2 del HC-SR04](companion_handoff_martin_2026-11-08/ROS2_HC_SR04_RESULTADO.md) y [paquete rosbag2](companion_handoff_martin_2026-11-08/README.md).
