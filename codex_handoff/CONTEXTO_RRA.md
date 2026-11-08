# RRA: contexto para continuidad local

Actualizado: 2026-11-08. Datos vigentes y comprobaciones: [ESTADO_ACTUAL.md](ESTADO_ACTUAL.md).

La cronología que sigue conserva reportes previos. Si una frase histórica
contradice el estado vigente, usar la sección fechada 2026-11-08 de
`ESTADO_ACTUAL.md` y las últimas actualizaciones de `H743_DATOS_HARDWARE.md`.

## Objetivo y responsabilidades

Rover Rural Autónomo (RRA) desarrolla por etapas la supervisión, telemetría y
autonomía de un rover rural. El repositorio compartido es
<https://github.com/Gonellarro/RRA>; su propietario es Martín. El compañero
provisional se desarrolla en la Orange Pi de Juan. Martín desarrolla de forma
independiente el compañero definitivo; la integración y las interfaces comunes
deben coordinarse con él, sin presumir qué ha implementado fuera del repositorio.

La arquitectura prevista se basa en un chasis Axial AX10 Toyota Land Cruiser
83 1/10 y una MATEK H743-WLITE con ArduRover. El usuario identifica la placa
como H743-WLITE y ha comunicado este cableado: ESC (señal) en S1 sin su cable
positivo de alimentación; servo de dirección en S3; DroneBridge ESP32 en TX7/RX7;
receptor en RX6; GNSS por TX2/RX2 y brújula por DA1/CL1. TX1/RX1 (TELEM2) se
utiliza ahora para la Orange Pi por UART5, según la prueba física del 7/11.
El inventario
y la propuesta de cableado están en `H743_DATOS_HARDWARE.md`. La controladora conserva motor,
dirección, modos, failsafes y funciones críticas. El companion se destina a ROS 2,
diagnóstico, telemetría, registro y sensores; no controla PWM directamente.
El GNSS UM982+ RTK de doble antena y el encoder AS5047P son previstos; no se ha
comprobado aquí su instalación o conexión. UART H743–Orange Pi está validado
para telemetría física y una petición MAVLink fija; no hay volcado completo de
parámetros ni revisión exacta de PCB. La Orange Pi Zero 2W sí ha
respondido por SSH y reporta 3,8 GiB de RAM y almacenamiento raíz de 58 GiB.

## Decisiones y límites

- ROS 2 Lyrical y MAVROS 2.16.0 están instalados; la prueba ROS, SITL/loopback,
  observador y rosbag pasaron. El gateway SROS2 pasó primero con productor
  sintético y luego con el `mavros_node` real: del grafo observado, la app
  recibió estado a través del gateway y no pudo crear 69 lectores directos,
  73 publicadores ni 233 clientes de servicio. No había acciones ROS expuestas.
  Esto no demuestra aislamiento frente a un proceso MAVROS comprometido. La
  conexión física sí se validó el 7/11; el estado de campo del rover y el del
  Companion son evidencias distintas. Las pruebas de campo y su procedencia se
  detallan en `ESTADO_ACTUAL.md`.
- Priorizar interfaces ROS estándar y módulos portables al companion definitivo.
  No inventar conexiones, velocidades de puerto ni parámetros de la H743.
- Empezar por simulación y observación. MAVROS puede exponer interfaces de
  escritura: instalarlo o suscribirse a tópicos no garantiza aislamiento de
  órdenes. Diseñar y verificar cualquier límite antes de conectarlo a hardware.
- No emitir órdenes de armado, movimiento o cambio de modo ni activar motores
  o actuadores. Cualquier ensayo físico requiere procedimiento y autorización.
- Mantener separados simulación, banco y rover físico; una prueba SITL no
  demuestra seguridad o funcionamiento del vehículo real.
- El README y roadmap de Martín mantienen su flujo de simulación y aprendizaje;
  no se han encontrado paquetes propios de ROS en la revisión compartida
  `a370189d`. La configuración local del companion es trabajo adicional, no
  evidencia de un cambio de estado del trabajo independiente de Martín.

Actualización local 2026-11-05: H743 sigue desconectada. La investigación de solo lectura del Orange Pi identificó overlay UART5 candidato, no activado; ver `UART_PRECONNECTION_CHECKLIST.md`. Persisten pendientes revisión H743, nivel eléctrico, parámetros SERIAL2 y habilitación verificada de UART5.

Actualización 2026-11-05: auditoría y corrección de concurrencia MAVLink, contrato ROS2 sintético y benchmark local añadidos. Consultar `ESTADO_ACTUAL.md`, `PLAN_SIGUIENTES_PASOS.md`, `PHASE_REVIEW_SECURITY_AND_ROS2_2026-11-05.md` y `RRA_ROS2_INTERFACES.md`. Validación física permanece en pausa hasta tener la Matek H743-WLITE; el enlace Companion no es físicamente solo lectura y la respuesta MAVLink PARAM_VALUE no se correlaciona de forma infalible.

## Hito 1 funcional terminado — 2026-11-05

`rra_telemetry` consume tópicos estándar MAVROS para estado, GNSS, IMU, batería,
odometría/velocidad y rumbo; entrega `DiagnosticArray` por fuente y latido. Se
añadieron validación y remaps, y el simulador publica un conjunto sintético
coherente aislado. Orange Pi: build Lyrical y 11/11 tests OK; integración sintética
comprobó siete estados OK.

Grabación real de **SITL** (ArduRover 4.7.2; no rover físico): siete topics, 369
mensajes en 61 s; se observó conexión MANUAL/desarmado, datos sensor y pérdida de
enlace al parar el bridge. `verify_bag.py` pasó replay 4x con `REPLAY_OK`. Bag
local y manifest en `evidencias/sitl-telemetry-demo-2026-11-05/`. Sin H743/UART,
actuación, cambios a parámetros o control. La ambigüedad `PARAM_VALUE` persiste
como problema documentado y la lectura BATT no es apta para decisiones críticas.

**Siguiente paso:** hito 2 del `PLAN_DESARROLLO_CORTO.md`: simplificar ejecución
y recorder portable mediante launch/config; verificar entorno ROS x86_64 antes
de afirmar que Martín puede compilar. El contrato principal es
`CONTRATO_INTEGRACION_COMPANION.md`; responsabilidades/interfases pendientes con
Martín se mantienen explícitas.

## Hito 2 portable validado en ARM64 — 2026-11-05

Se completó launch/config YAML y grabador con allowlist de siete tópicos y límite
máximo de tiempo. Build en Orange Pi Lyrical, 11/11 pruebas unitarias e
integración sim+rosbag pasaron; se verificó además que la fuente MAVROS solo
arranca el observador y no MAVROS/FCU. La bolsa temporal de smoke fue MCAP,
73.5 KiB/45 mensajes/siete tópicos; rosbag reportó 3.005 s de datos frente al
límite de 8 s, debido al inicio/descubrimiento. El script muestra la duración
real y cierra rosbag con SIGINT. No se conserva el bag sintético temporal.

La limpieza de prueba termina los nodos; comprobación final de procesos sin
nodos RRA restantes. x86_64 no validado: WSL 22.04 carece de ROS 2; no se instaló.
Hito 3 sigue pendiente de la H743. Ver `ESTADO_ACTUAL.md`, `PLAN_SIGUIENTES_PASOS.md`
y `evidencias/hito2-portable-execution-2026-11-05/RESULTADO.md`.

Actualización 2026-11-07: el usuario informa que la H743-WLITE está accesible
desde Mission Planner por TCP mediante DroneBridge; la Orange Pi aún no está
conectada. Próxima tarea: consultar firmware y parámetros SERIAL2 sin escritura,
y después verificar revisión física/niveles eléctricos. No se pudieron leer en
esta sesión porque falló dos veces el helper de Computer Use.

Capturas Mission Planner recibidas 2026-11-07: ArduRover V4.7.2 (target visible
MatekH743), `SERIAL2_PROTOCOL=2`, `SERIAL2_BAUD=57`, `SERIAL2_OPTIONS=0`;
`BRD_SER1_RTSCTS=2` corresponde al enlace SERIAL1/TELEM1 del DroneBridge, no a
SERIAL2. No se han leído `SR2_*`, el volcado completo de parámetros, revisión
física ni nivel TX1. No se conectó Orange Pi ni se cambiaron parámetros. Ver
`H743_DATOS_HARDWARE.md` y `UART_PRECONNECTION_CHECKLIST.md`.


## Actualización de Mission Planner — 2026-11-07

Nuevas capturas confirman `SERIAL0_PROTOCOL=2`, `SERIAL1_PROTOCOL=2` y el bloque MAV3 de ArduRover 4.7.2. MAV3: ADSB 0; EXTRA1/2/3, EXT_STAT, POSITION, RAW_CTRL, RAW_SENS, RC_CHAN a 1 Hz; PARAMS a 10 Hz; OPTIONS 0. Los valores visibles coinciden con defaults. MAV3 es el nuevo nombre del antiguo SR2. Esto documenta configuración, pero no mide tráfico del TELEM2 físico. Ningún parámetro se cambió y Orange Pi sigue desconectada.

Próximo paso: antes de unir placas, confirmar por fotos la revisión serigrafiada de la H743-WLITE y resolver el nivel eléctrico de TX1. Si se confirma compatibilidad y el banco está inmovilizado, iniciar únicamente recepción UART (TX1→UART5_RX y GND común; dejar RX1 y UART5_TX desconectados). Ver `UART_PRECONNECTION_CHECKLIST.md`.

## Evidencia física preliminar H743 — 2026-11-07

Foto de instalación real: la controladora parece una Matek H743-WLITE, pero la serigrafía está parcialmente oculta/desenfocada; la revisión exacta no queda confirmada. Las demás imágenes son referencias comerciales. No desconectar los cables existentes ni inferir el pin ocupado por color o posición en la foto.

El manual MATEK H743-WLITE mapea TX1/RX1 a TELEM2/SERIAL2 y dice “5 V tolerant I/O”. Esto no especifica la tensión de salida TX1, así que la compatibilidad con Orange Pi UART5 aún debe verificarse. No conectar todavía ambas placas. Próximo paso: foto macro legible de la etiqueta/revisión de la FCU instalada y comprobar la salida TX1 antes del ensayo de recepción.

## Primer enlace real UART→MAVROS→RRA — 2026-11-07

Orange Pi localizable por Wi-Fi en 10.221.18.8. Recepción passiva MAVLink2 confirmada. Prueba temporal con MAVROS a 57600 y observer RRA: FCU connected, HOLD, disarm; datos de GPS/IMU/batería/velocidad/heading disponibles. RRA diagnósticos publicados. Registro de resultados detallado en `ESTADO_ACTUAL.md`. Se reporta `PreArm: Radio failsafe on`; no cambiar failsafe. Request de versión MAVROS agotó timeout porque no hay retorno TX conectado. Nodo temporal cerrado, sin cambios FCU y sin autostart. Siguiente paso: rosbag2 corto de telemetría real y replay local.

## Rosbag RRA físico — 2026-11-07

Grabado bag real MCAP de 6,88 s/58 mensajes/siete topics en `~/rra_ws/recordings/rra-h743-uart-rx-20261107-154256` (privado en Orange Pi, contiene posible GNSS, no trasladado a repositorio). Replay en domain206 local recuperó State y diagnostics de GPS/IMU/batería/velocidad/rumbo. Consultar `ESTADO_ACTUAL.md` para detalles. Pendiente reproducir incidencia única de segfault de MAVROS durante SIGINT; salida de versión timeoutea en RX-only y el texto FCU reporta failsafe de radio. No se tocaron parámetros ni actuadores.

## Cierre MAVROS y aviso de radio — 2026-11-07

Segmentation fault al cerrar grabación fue único; repetido dos veces cierre SIGINT exit0 con sys_status y allowlist de cuatro telemetría. Aviso previo `PreArm: Radio failsafe on` no apareció en dos ventanas cortas posteriores, sin que eso confirme su resolución. MAVROS version timeout en RX-only es esperado por retorno físico abierto. No cambiar parámetros FCU.

## Actualización de continuidad — retorno UART probado (2026-11-07)

El retorno físico ya está conectado y validado. La consulta fija de solo lectura `BATT_MONITOR` respondió por MAVLink en 54 ms con valor 4 (PARAM_VALUE, sysid/compid 1/1); la correlación con la petición se marca ambigua por limitación del protocolo. `AUTOPILOT_VERSION` no respondió a la petición MAV_CMD_REQUEST_MESSAGE 512 / id 148 aunque la solicitud MAVROS fue aceptada; la especificación MAVLink/ArduPilot sí define ese mecanismo, así que queda para diagnóstico posterior. Mission Planner ya mostró ArduRover 4.7.2 (`fb773567`) de forma independiente. Sin escritura de parámetros, armado, cambio de modo ni control de movimiento. No hace falta conectar más cables para continuar con telemetría ROS y rosbag.

## Estado y siguiente acción — sesión física de rosbag (2026-11-07)

MAVROS + observador ROS funcionaron en UART real con retorno conectado y allowlist de telemetría. Grabación MCAP local en la Pi: `~/rra_ws/recordings/rra-h743-uart-duplex-20261107-1626`, 77,8 KiB, 62 mensajes, 7 tópicos, 7,96 s. El metadata quedó comprobado; aún falta validar el replay porque se perdió SSH durante esa comprobación. No afirmar replay PASS.

MAVROS volvió a terminar con segmentation fault al SIGINT (ocurrencia repetida). Conexión no disponible en el último chequeo: portátil Wi-Fi 192.168.2.2, Orange Pi previamente en 10.221.18.8. Primer paso: poner ambos en la misma red/descubrir IP actual; comprobar si Pi sigue encendida, revisar log y procesos, reproducir el bag sin conectar H743 y recopilar un cierre controlado para aislar el crash. Después continuar con interfaces ROS de diagnóstico/estado. No se requiere cable nuevo.


Último intento SSH (2026-11-07): portátil en 10.221.18.142/gateway .248, Pi ausente del escaneo y sin SSH en IP antigua .8. Su estado físico/IP actual no está confirmado. Reanudar tras obtener la dirección actual del hotspot/router o recuperar la Pi en la misma red.


Reanudación 2026-11-07: Orange Pi reapareció en .8; bolsa anterior de 16:41 quedó 0 bytes después del reinicio. Se generó segunda captura 16:52 con MCAP 39.386 B + metadata 5.948 B tras sync, pero la conexión se perdió antes de replay y revalidación posterior. No reiniciar de nuevo hasta verificar tamaños/replay si se puede recuperar SSH. Hotspot DIGIFIBRA-PyHA en portátil activo; Pi vuelve a desaparecer.

Actualización final de la sesión física (2026-11-07): después del reinicio de la Pi, hotspot/SSH volvió (`10.221.18.8`) y se mantuvo durante la prueba. Wi-Fi power_save está `off`, así que la causa de la no asociación en el arranque previo queda abierta. La bolsa `...-1654` no sirve (4 mensajes, State desconectado/sensores vacíos). Reemplazada por `~/rra_ws/recordings/rra-h743-uart-live-20261107-1700`: 51 mensajes, siete tópicos, 71.981 B + metadata 5.947 B; replay en domain207 PASS para estado, diagnóstico y los cinco sensores con QoS compatible. Estado conectado/HOLD/desarmado; sensores disponibles. Coordenadas no impresas; bag solo en Pi. SIGINT de cierre MAVROS esta vez limpio y sin procesos restantes; segfaultes anteriores siguen como evento ocasional. MAVROS version timeout persiste. No se cambiaron parámetros/armado/modo ni se enviaron consignas físicas.
