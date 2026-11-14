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

## 2026-11-11 — lectura inicial de tensión y corriente de electrónica
- Mission Planner `battery_voltage`: 7,38 V. Multímetro reportado: 7,46 V; diferencia 0,08 V (aprox. 1,1%). No consta si fueron medidas simultáneas ni si el multímetro estaba exactamente en BAT+/BAT−.
- Corriente en Mission Planner: normalmente 0,15 A, con picos observados de 0,6 A cuando todos los periféricos estaban conectados y el servo se movía repetidamente. El usuario observa que la Orange Pi deja de responder al mover el servo; caída transitoria en Vx/5 V es una hipótesis aún no medida. La telemetría podría no capturar picos breves.
- Interpretación: lectura de tensión cercana, sin base suficiente para cambiar `BATT_VOLT_MULT` ni configurar los cortes propuestos. Repetir ambas medidas en los mismos pads y bajo Companion activo/servo moviéndose; comparar corriente con método independiente si está disponible.
- No se modificaron parámetros ni hardware. Diseño actualizado en `codex_handoff/ARQUITECTURA_ALIMENTACION_BATERIAS.md`.

## 2026-11-11 — caída de batería observada al mover servo
- Juanjo midió con multímetro una variación aproximada de 7,5 a 6,6 V entre GND y la entrada de batería mientras mueve el servo repetidamente; Mission Planner no muestra una variación comparable.
- Falta confirmar si las puntas estaban directamente en BAT+/BAT− de la H743. Si sí, el mínimo observado (6,6 V) está bajo el mínimo de entrada especificado para H743-WLITE (6,8 V). Esto hace probable una caída de alimentación relacionada con los cortes de la Orange Pi, pero la localización requiere medir también el pack, Vx y la entrada de 5 V de la Pi.
- Siguiente prueba: comparar con el mismo movimiento servo los voltajes en el conector de batería, en BAT+/BAT− de la H743 y en la entrada 5 V/GND de la Pi. Si la batería se mantiene y BAT cae, revisar cable/fusible/interruptor/conectores; si BAT se mantiene y cae la Pi, revisar Vx/distribución; si todo se mantiene, investigar masa/ruido/Wi-Fi/software.
- No se cambió cableado ni parámetros. Los valores candidatos de apagado 7,2/7,0 V quedan sin aplicar hasta corregir/entender la caída.

## 2026-11-13 — prototipo de protección de batería y prueba Pi–Matek
- Añadido `src/rra_battery_protection`: modelo Python con anillo de 20, mediana de cinco + EMA, timers monotónicos, sensor fault, histéresis y dry-run; seis pruebas pasan localmente y en Orange Pi. Simulador incluye caída de servo, descarga, lectura defectuosa y pérdida de sensor.
- El paquete se copió y compiló en `~/rra_ws` de la Orange Pi; SSH confirmado en 192.168.1.156, ROS 2 Lyrical/Python 3.14. MAVROS temporal por `/dev/ttyS5:57600` conectó a ArduPilot; observador RRA publicó. Monitor dry-run leyó 7,890 V y sonar 1,63 m. QoS se corrigió a `qos_profile_sensor_data`. Launch temporal cerrado; sin systemd/autostart instalado.
- Lectura de parámetros sin escritura: `SCR_ENABLE=0`, `SCR_HEAP_SIZE` ausente, `BATT_MONITOR=4`, `BATT_VOLT_PIN=10`, `BATT_VOLT_MULT=11`, `BATT_LOW_VOLT=0`, `BATT_CRT_VOLT=0`, `BATT_LOW_TIMER=10`, failsafes de batería 0, `SERVO12_FUNCTION=0`, `RELAY1_FUNCTION=0`, `RELAY_PIN` y `RELAY1_DEFAULT` ausentes. No se escribió ningún parámetro.
- La referencia publicada por Matek indica escala 21, distinta del 11 leído. La batería marcó 7,891 V en MAVROS; no fue medida simultáneamente con multímetro. Contrastar directamente en BAT+/BAT− antes de calibrar o activar umbrales. Lua permanece prototipo, no subido/ejecutado; protocolo de apagado aún incompleto y GPIO/Pololu no accionados. Detalle en `codex_handoff/PROTECCION_BATERIA_2026-11-13.md`.

### Medición simultánea de tensión — 2026-11-13
El usuario midió 7,89 V con multímetro y 7,854 V en ArduPilot al mismo tiempo: diferencia 0,036 V (0,46%). El ajuste actual `BATT_VOLT_MULT=11` coincide bien en este punto; no modificar por la sola diferencia respecto a la referencia de ficha 21. Pendiente comprobar otro nivel y sag bajo servo. No se cambiaron parámetros.

## 2026-11-13 — protocolo de apagado Companion sin Pololu
- Se amplió `src/rra_battery_protection`: Lua ahora prepara aviso, solicitud urgente a ≤7,2 V sostenidos durante 5 s, `COMMAND_LONG` 31000 al Companion 1/191, ACKs y READY 31001 con nonce. No contiene accionamiento GPIO, relé ni corte físico.
- Listener ROS2 usa los topics raw `/uas1/mavlink_source` y `/uas1/mavlink_sink` del router MAVROS existente; filtra origen/destino, persiste evento JSONL, responde ACK y prepara el cierre. `DRY_RUN=1` es el default; el modo real llama a `systemctl poweroff` únicamente cuando explícitamente se configura `0`.
- Se prepararon unidad systemd y script de instalación solo DRY_RUN. No se han instalado, ni se han escrito parámetros FCU. En esta sesión el SSH por lote devolvió `Permission denied (publickey,password)` y quedó una sesión interactiva esperando clave; la Pi aún no autenticada, sin despliegue de esta versión.
- Verificación local: 13 pruebas pasan y `compileall` termina. La primera ventana SSH falló porque Windows Terminal interpretó mal argumentos y buscó `bash` local; una segunda sesión SSH directa quedó autenticada por el usuario. Se creó clave dedicada `id_ed25519_rra_companion_codex`, cuya clave pública aún debe instalarse en `authorized_keys`; hasta entonces no hay acceso automatizado ni despliegue nuevo. Falta compilar/validar frames contra MAVROS/Lua del equipo; no se afirma despliegue operativo todavía. La documentación completa y pasos siguientes están en `codex_handoff/PROTECCION_BATERIA_2026-11-13.md`.

### Actualización de despliegue en Pi — 2026-11-13
- El usuario añadió la clave pública a `authorized_keys`; SSH por clave a `rra@192.168.1.156` quedó verificado. Se respaldó la versión previa fuera del workspace, en `~/rra_battery_protection.codex-backup-20261113-233152`.
- El paquete actualizado se compiló correctamente con `colcon build --symlink-install --packages-up-to rra_battery_protection` en ROS 2 Lyrical / Python 3.14.
- Prueba sintética ROS en domain 205 pasó: comando 31000 → evento JSONL con fsync → ACK → READY 31001/ACK → `DRY_RUN: poweroff simulado`. Linux siguió activo. No había MAVROS ni nodos ROS conectados durante esta prueba.
- La unidad systemd se instaló y quedó `active/enabled` con `RRA_POWER_SHUTDOWN_DRY_RUN=1`; `/etc/default/rra-power-shutdown` confirma el modo. Después se repitió el handshake a través del servicio persistente ejecutado como root. Lua no se subió ni se ejecutó y no se modificó ningún parámetro de la Matek. Este resultado valida compilación y protocolo ROS local, no la conexión física ni el comportamiento del firmware.

## 2026-11-14 — enlace MAVROS real y estado de Lua
- MAVROS se conectó a la Matek por `/dev/ttyS5:57600`; log confirmó FCU ArduPilot y `MY ID 1.191, TARGET ID 1.1`. `/mavros_node/state`: connected=true, armed=false, mode=HOLD. `/mavros_node/battery`: 7,633 V, corriente -0,2 A.
- Se detectó y corrigió en el listener una incompatibilidad QoS: MAVROS raw source publica BEST_EFFORT y el subscriber RELIABLE no recibía. El servicio ahora corre como `rra`, usa BEST_EFFORT y ROS graph confirma subscriber de `rra_power_shutdown` en `/uas1/mavlink_source`. Listener registró heartbeat físico (msgid 0, sysid/compid 1.1). Unidad sigue activa y DRY_RUN=1.
- Para inspeccionar parámetros se habilitaron temporalmente plugins `param` y `ftp`; se ejecutó pull/read solamente. Tras descargar 1150 parámetros, `SCR_ENABLE=0` y `SCR_HEAP_SIZE` no está declarado; no aparece ningún otro `SCR_*`. No se hizo ningún set ni operación FTP. Se restauró la allowlist habitual, con `param` y `ftp` excluidos.
- No se pudo ejecutar Lua en este firmware con evidencia disponible de scripting incompleto; no se subió el archivo ni se reinició/cambió la Matek. La siguiente tarea es confirmar AP_Scripting/heap y la SD `APM/scripts`. No GPIO, Pololu, apagado Linux real ni comandos de movimiento.

## 2026-11-14 — continuación de paso 1, Matek sin enlace MAVLink
- SSH volvió a estar disponible. Unidad `rra-power-shutdown.service` activa y `RRA_POWER_SHUTDOWN_DRY_RUN=1` confirmado.
- MAVROS temporal se inició en `/dev/ttyS5:57600` con plugins de lectura `sys_status`, `param`, `ftp` (luego se añadió `command` para la consulta estándar de versión; no se invocó ningún servicio de comando). El estado FCU reportó `connected=false` y no se pudo completar el pull de parámetros. Una escucha pasiva posterior de UART5 registró 6.569 bytes/8 s; un parser de framing MAVLink identificó 92 tramas/origen 1/1 durante 4 s, con msgid 0 presente. No se validó CRC de esas tramas. MAVROS no las elevó a estado conectado. La Pi volvió a agotar timeout SSH.
- No se escribió `SCR_ENABLE`, no se reinició la Matek, no se cargó Lua ni se activó ninguna salida. El build oficial exacto sí incluye AP_Scripting. El cableado transmite datos; queda depurar el framing/compatibilidad de MAVROS y recuperar la estabilidad SSH antes de leer/escribir parámetros.

## 2026-11-14 — confirmado AP_Scripting en firmware exacto
- Corrección de la interpretación del listado de parámetros: el firmware instalado se identificó como ArduRover 4.7.2 commit `fb773567896014da007bca58358704d4a0d8516f`. Se consultó el directorio oficial `Rover/stable-4.7.2/MatekH743`; `firmware-version.txt` y `git-version.txt` coinciden y `features.txt` incluye `AP_SCRIPTING_ENABLED`, `AP_SDCARD_STORAGE_ENABLED` y `AP_FILESYSTEM_SYS_ENABLED`.
- Por tanto, el build oficial exacto sí admite Lua y almacenamiento. La ausencia de `SCR_HEAP_SIZE` mientras `SCR_ENABLE=0` no prueba que scripting falte; ArduPilot documenta que los demás parámetros SCR aparecen después de habilitar scripting y refrescar/reiniciar la lista.
- No se escribió ningún parámetro ni se subió/ejecutó Lua. En esta revisión SSH a `rra@192.168.1.156` agotó tiempo de espera, así que no fue posible continuar con la controladora. Siguiente paso al recuperar MAVROS: guardar parámetros, habilitar solo `SCR_ENABLE=1`, refrescar/leer parámetros SCR y verificar almacenamiento, heap y mensajes. Mantener DRY_RUN, sin acción GPIO ni corte.
