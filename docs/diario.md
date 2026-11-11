# Diario de desarrollo — RRA Software

## 2026-11-08 — actualización de estado de campo y preparación de sensores
- Objetivo: incorporar el resumen de pruebas físicas reportado por el usuario y preparar integración HC-SR04 + cámara sin actuar sobre hardware.
- Cambios: actualizar README, roadmap, contexto, estado, plan y fichas locales; añadir `HC_SR04_H743_INTEGRACION.md` y `CAMARA_USB_ORANGE_PI.md`; ampliar `AX10_MEDICIONES.md` con radios/diámetros de giro, frenado y poses de sensores.
- Resultado: se registra misión AUTO de 3–4 waypoints el 2026-11-02, LOITER resuelto sin causa raíz, GNSS último reportado HDOP 0,6 y error estimado 0,3 m; se corrige como vigente la conexión Companion UART física y replay ya verificados el 2026-11-07.
- Límites: los resultados de campo proceden del usuario, no de ejecución física en esta sesión. HC-SR04/cámara no se conectaron; no se cambiaron parámetros, cableado, misión ni firmware. No se ejecutaron pruebas de hardware ni nuevas pruebas SITL en esta actualización documental.
- Siguiente paso: medir el AX10 y recopilar/exportar parámetros actuales; confirmar S4/S5 libres y el sensor/cámara reales; después validar driver HC-SR04/evitación en SITL ArduRover 4.7.2 y captura UVC sin instalar paquetes por adelantado.

Registro cronológico de decisiones, acciones y pruebas del software del Rover Rural Autónomo.

**Estado inicial:** todavía no se han ejecutado pruebas de software ni de integración desde este repositorio. Las especificaciones y el roadmap son propuestas de partida.

## Plantilla de entrada

```text
## AAAA-MM-DD — título
- Objetivo:
- Cambios o acciones:
- Resultado observado:
- Evidencia/log:
- Problemas o dudas:
- Siguiente paso:
```

## 2026-10-15 — Primer arranque de ArduRover SITL
- Objetivo: preparar el entorno de desarrollo y arrancar ArduRover SITL en Ubuntu para aprender a observar su estado y comunicarse con él mediante MAVLink.
- Cambios o acciones: se registró el entorno en `docs/entorno_de_desarrollo.md` (Ubuntu 26.04, kernel 7.0.0-38-generic, Git 2.53.0 y Python 3.14.4). Se clonó ArduPilot en `~/src/ardupilot` y se ejecutó `Tools/environment_install/install-prereqs-ubuntu.sh`. Durante esa instalación el PC se bloqueó; después no había procesos `apt-get`, `dpkg` ni el instalador activos. Se comprobó que existía `~/venv-ardupilot`, que incluía MAVProxy 1.8.75 y pymavlink 2.4.50, y que `sim_vehicle.py --help` funcionaba.
- Resultado observado: ArduRover SITL compiló correctamente («build finished successfully», 59,591 s), arrancó desde `~/src/ardupilot/Rover` y MAVProxy detectó el vehículo por TCP local `127.0.0.1:5760`. Se recibieron 1.292 parámetros; MAVProxy indicó que guardó `mav.parm` y registraba telemetría en `mav.tlog`. Se observaron las ventanas de mapa y consola, con el vehículo en `MANUAL` y desarmado (`ARM` rojo). Se cambió a `HOLD` y se volvió a `MANUAL`; el prompt reflejó el cambio tras pulsar Enter otra vez.
- Aprendizajes: MAVLink es el protocolo de comunicación; ArduRover es el autopiloto. `mode` sin argumentos enumera modos; `status` muestra mensajes MAVLink recientes. `GPS_RAW_INT` contiene datos GPS brutos y `GLOBAL_POSITION_INT` la posición estimada por el autopiloto. `HEARTBEAT` identifica el sistema y comunica su presencia, tipo, modo y estado. Los datos observados (ubicación inicial cerca de Canberra, 10 satélites, `fix_type: 6`, batería 12,6 V) pertenecen a la simulación; `fix_type: 6` no valida RTK real. No se armó el rover ni se ejecutó una misión.
- Evidencia/log: salida de arranque de SITL y consultas `mode`, `status GPS_RAW_INT`, `status GLOBAL_POSITION_INT` y `status HEARTBEAT` compartidas en la sesión. MAVProxy indicó `MAV Errors: 3` y `SYS_STATUS.errors_comm: 0` en la salida consultada.
- Problemas o dudas: MAVProxy mostró un aviso de ModemManager y falló la descarga/lectura de la lista SRTM3 por un error de decodificación UTF-8. El mapa y la conexión SITL siguieron funcionando; no se investigaron más esos avisos. El bloqueo durante la instalación no tiene causa confirmada.
- Siguiente paso: continuar la etapa 1 del roadmap, revisar mensajes de salud y avisos, y practicar el procedimiento de parada y arranque repetible de SITL. Mantener las pruebas en simulación; aún no hay validación de la H743 ni del hardware real.

## 2026-11-03 — Preparación de la Orange Pi provisional
- Objetivo: preparar ROS 2 Lyrical en la Orange Pi Zero 2W sin interferir con el desarrollo compartido.
- Cambios o acciones: rama local `feature/orangepi-ros2`; diagnóstico de Armbian comunitario Ubuntu 26.04 ARM64; acceso SSH verificado para `root` y el usuario existente `rra`; instalación de ROS base, ejemplos Python, colcon y rosdep; creación de `~/rra_ws/src` y configuración del entorno del usuario.
- Resultado observado: en una conexión nueva se cargó Lyrical; dos procesos ROS independientes publicaron y recibieron un mensaje, y finalizaron correctamente. `rosdep update`, `colcon list`, ayuda de rosbag y script de diagnóstico funcionaron. `dpkg --audit` no informó de incidencias.
- Evidencia/log: detalles, versiones y límites en `docs/companion_orange_pi.md`; salidas de pruebas en `/tmp/rra-talker-clean.log` y `/tmp/rra-listener-clean.log` de la placa, temporales.
- Problemas o dudas: el acceso automático inicial necesitó una clave SSH; la primera prueba usó una opción de shell incompatible y se corrigió; una prueba de ejemplo recibió mensajes pero produjo una excepción al terminarla forzadamente. La repetición con cierre normal pasó.
- Siguiente paso: revisar con Martín la propuesta y continuar con MAVROS y telemetría de solo lectura, empezando por simulación. No se ha validado la conexión a la H743, sensores, grabación rosbag ni el rover real.

## 2026-11-10 — Respuesta de aceleración y frenado
- Resultado de campo reportado por Juanjo: al cambiar `MOT_SLEWRATE` a `0`, la aceleración y la respuesta al soltar el acelerador/frenar pasaron a funcionar de forma inmediata y satisfactoria.
- Interpretación: confirma que la rampa de salida configurada por ArduRover era la causa práctica del retardo observado. El resultado es coherente con el valor anterior `MOT_SLEWRATE=100` mostrado en Mission Planner. No se atribuye el retardo a la curva Rate/Exp de la emisora; la captura de FS-i6S correspondía a CH4 y no demuestra por sí sola que ese canal sea el acelerador.
- Estado del parámetro: `MOT_SLEWRATE=0`, según el usuario. No se leyó de nuevo desde Mission Planner en esta sesión.
- Límite: esta observación valida la respuesta percibida en las condiciones de la prueba; no cuantifica distancia de frenado ni sustituye una medición repetible. No se cambió ningún parámetro desde esta sesión.
- Siguiente paso útil: conservar el ajuste si sigue siendo satisfactorio y, cuando se realicen las mediciones físicas del AX10, anotar superficie, velocidad inicial y distancia de parada para disponer de una referencia.

## 2026-11-10 — modelo ROS básico y cinemática inicial del AX10
- Objetivo: aprovechar las medidas disponibles en un modelo ROS reutilizable sin esperar nuevas mediciones de dirección.
- Cambios: nuevo paquete local `src/rra_ax10_model` con Xacro de marcos `base_link`, ruedas, GNSS, IMU y HC-SR04; geometría de batalla/vías/rueda en parámetros externos; biblioteca cinemática y nodo ROS 2.
- Cinemática: se usa modo `parallel` por defecto, coherente con 0° de diferencia Ackermann reportados; aplica límite preliminar de 25° y modelo bicicleta con batalla 0,320 m. Se ofrece modo `ackermann` ideal configurable, sin presentarlo como geometría física medida.
- Interfaces: entrada `ackermann_msgs/AckermannDriveStamped` en `/rra/model/cmd_ackermann`; salida de odometría predicha `nav_msgs/Odometry` en `/rra/model/predicted_odom` y articulaciones predichas en `/rra/model/joint_states`. No conecta con MAVROS ni emite órdenes al rover. TF dinámico desactivado por defecto.
- Coordenadas: URDF usa convención ROS Y izquierda; los offsets Y positivos a derecha de la ficha se convirtieron a Y negativa para GNSS e IMU. Orientaciones de sensores siguen provisionales.
- Pruebas: seis pruebas Python unitarias pasan; XML de `package.xml` y Xacro bien formado. ROS 2, `colcon`, `xacro` y lanzamiento del nodo no están disponibles en este portátil, así que falta validación nativa ROS.
- Siguiente paso: compilar y lanzar en ROS 2 Lyrical (Pi o entorno x86_64 de desarrollo), verificar `/tf_static`, articulaciones y respuesta recta/giro en el tópico de modelo; después acordar con Martín frames y namespace antes de integrar.

## 2026-11-10 — topología de baterías reportada
- Motor: pack HOOVO LiPo 2S, 7,4 V nominal, 5200 mAh, etiqueta/ficha indica 80C y XT60; alimenta solo el ESC Axial AE-2 y el motor.
- Electrónica: pack idéntico según el usuario; BAT+/BAT− de la Matek H743-WLITE a través de fusible 30 A e interruptor. La Matek alimenta servo TowerPro MG995, Companion Orange Pi, HC-SR04, GNSS/brújula, receptor FS-BS8 y XIAO ESP32-S3/DroneBridge; el rail concreto de cada carga está por identificar.
- ESC: cable rojo BEC retirado del conector de señal; queda señal PWM en S1 y referencia de masa común. Servo de dirección en S3.
- Evaluación: dos packs separan las corrientes principales de motor y electrónica. El fusible limita sobrecorriente/cortocircuito, pero no evita sobredescarga. El AE-2 admite 2S LiPo y su manual indica corte Auto-LiPo predeterminado, pero el ajuste actual debe verificarse. La H743-WLITE especifica entrada 6,8–30 V; se requiere una alarma/failsafe configurada para la batería electrónica y lectura de tensión contrastada.
- Pendiente práctico: mapear el rail de alimentación de cada módulo y medir tensión/corriente bajo carga de Companion y movimiento de servo; comprobar corte LiPo AE-2; revisar monitor y failsafe de la batería electrónica sin cambiar parámetros hasta autorizarlos.
- Referencias oficiales: manual H743-WLITE y guía de programación AE-2 enlazadas en `codex_handoff/ARQUITECTURA_ALIMENTACION_BATERIAS.md`.

## 2026-11-10 — diseño por etapas de protección de baterías
- Evaluación de la propuesta del usuario: zumbador por celdas para ambos packs; corte Auto-LiPo del AE-2 para motor; primera etapa de baja tensión en el pack electrónico para solicitar apagado limpio de Orange Pi; segunda etapa con interruptor electrónico de baja tensión, enclavado y rearme manual.
- Aclaración funcional: el failsafe de batería de ArduPilot informa/ejecuta acciones del rover, pero no apaga por sí mismo Linux. La solicitud de `poweroff` necesita un servicio local del Companion que consuma tensión MAVROS válida y reciente.
- Umbrales del usuario (7,2 V y 7,0 V) quedan como candidatos. El mínimo especificado de entrada de H743-WLITE es 6,8 V; 7,0 V ofrece solo 0,2 V de margen nominal y debe revisarse con caída de cable y sag bajo cargas reales.
- Recomendación: medir/calibrar primero la lectura H743; comprobar BATT_LOW_TIMER/failsafe y estado Auto-LiPo; medir el rail con Companion y servo; después seleccionar corte enclavado independiente del software. No se cambió hardware, se instalaron alarmas ni se modificaron parámetros.
- Diseño, secuencia y aceptación: `codex_handoff/ARQUITECTURA_ALIMENTACION_BATERIAS.md`.
