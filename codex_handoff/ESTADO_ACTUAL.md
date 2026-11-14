# Estado comprobado de RRA

Actualizado: 2026-11-08, hora Europe/Madrid. Revalidar lo variable al retomar.

## Estado vigente de rover físico y Companion — actualización 2026-11-08

Corrección de las descripciones anteriores: el Companion provisional sí se
conectó físicamente a la H743-WLITE el 2026-11-07. La sesión registró
UART5 `/dev/ttyS5` ↔ TELEM2/SERIAL2, MAVLink2/57600, recepción real de estado,
GPS, IMU, batería, velocidad y rumbo, más grabación/replay PASS de siete
tópicos. Una consulta fija `BATT_MONITOR` devolvió valor 4 en 54 ms, pero
`PARAM_VALUE` carece de ID de transacción y la correlación queda ambigua.
`AUTOPILOT_VERSION` continúa sin respuesta. Esto no convierte la UART en
unidireccional ni el enlace en solo lectura: el Companion transmite solicitudes.
La Orange Pi también se alimenta desde Vx medido por el usuario en 5,1 V; el
margen de corriente en picos sigue sin medirse.

Resultados de campo reportados por el usuario y recibidos en la orden del
2026-11-07 (no se adjuntó un log instrumental para esta actualización): chasis
AX10 montado con H743-WLITE y ArduRover 4.7.2; MANUAL/RC, armado/desarmado,
HOLD, dirección, tracción y fix GNSS 3D probados; misión AUTO de 3–4 waypoints
ejecutada con éxito el 2026-11-02. LOITER está **CERRADO/RESUELTO** según el
usuario; no se conoce ni se atribuye causa raíz o fecha de corrección. Una
desviación GNSS inicial cercana a 2 m se conserva como antecedente; la última
prueba comunicada dio HDOP 0,6 y error horizontal **estimado** 0,3 m. HDOP es
adimensional y 0,3 m no es error absoluto medido contra punto de referencia.
No hace falta RTK para declarar viables las primeras pruebas AUTO despejadas;
UM982/RTK dual sigue como mejora futura sin instalación confirmada.

La prueba de telemetría Companion no valida acompañamiento durante una misión
física. Tampoco están validados la parada ante obstáculo, la geocerca completa,
la precisión topográfica ni operación autónoma sin supervisión. Las pruebas
LOITER/AUTO anteriores permanecen en el historial como resultados separados.

## Fase 3: misión AUTO en simulación

El usuario autorizó la fase 3 y con ello órdenes de misión, armado, AUTO, HOLD y
desarmado **únicamente sobre SITL** dentro del namespace aislado de WSL. Se
utilizó ArduRover SITL 4.7.2, el archivo oficial de parámetros Rover para la
revisión `fb773567896014da007bca58358704d4a0d8516f` y `pymavlink` 2.4.50
instalado en una carpeta privada de WSL, sin modificar paquetes del sistema.

Dos ejecuciones del mismo triángulo simulado completaron puntos 1, 2 y 3 en
20,9 s cada una, terminaron a 0,07 m del HOME simulado y se desarmaron en HOLD.
Sus registros DataFlash tienen 1093 posiciones y 109 mensajes GPS por ejecución;
el trayecto estimado fue 36,19 m y la separación máxima 14,51 m en ambas. Una
tercera ejecución detuvo la misión en HOLD y desarmó tras el primer punto, sin
alcanzar el segundo durante cinco segundos. Todo son datos de simulación.

Los primeros intentos fallaron por acceso al namespace, acelerómetros aún
inconsistentes y filtro EKF sin estabilizar; se mantuvieron las comprobaciones
de armado y el controlador ahora espera la inicialización. Detalles, comandos,
límites y evidencia en `sitl/FASE3_MISION_SITL.md` y
`evidencias/fase3-2026-11-03/`. La Orange Pi no participó en estas misiones;
su conexión unidireccional a SITL se comprobó en pruebas anteriores. El uso
manual de una estación de control y el hardware real siguen sin validarse.

## Batería, rosbag, cierre y telemetría SITL: 2026-11-03

Se comparó el arranque anterior sin parámetros Rover con el archivo oficial
`Tools/autotest/default_params/rover.parm` de la revisión de ArduPilot 4.7.2
`fb773567896014da007bca58358704d4a0d8516f`: el archivo habilita `BATT_MONITOR 4`.
Se añadió esa única opción en `sitl/rover-battery-sim.parm` y se carga mediante
`--defaults` solo en instancias nuevas de SITL. El valor pasó de 0 V y -0,01 a
12,6 V y porcentaje 1,0 (100 %) en tres ensayos. Esto demuestra el efecto en
esta simulación, no la configuración ni el voltaje de una batería física.

El observador local `rra_telemetry` ahora publica diagnósticos independientes
para conexión, posición GPS, orientación IMU y batería. Usa la QoS de sensores
ofrecida por MAVROS y la edad local de recepción; rechaza posición sin fix o
fuera de rango, orientación ausente/no finita/no normalizada, voltaje cero,
infinito o no presente y porcentaje inválido. Si el voltaje es válido pero el
porcentaje no, conserva el voltaje y marca porcentaje desconocido. No presenta
valores de sensores caducados. Estas reglas no acreditan calibración, precisión
ni salud física. Detalles y parámetros en `rra_telemetry/README.md`.

Verificación: `colcon build --packages-select rra_telemetry`, nueve pruebas
unitarias y prueba integrada ROS con estado, sensores válidos, batería inválida
y caducidad, todas correctas. Tres ejecuciones SITL consecutivas cerraron el
grabador, el observador y MAVROS con código 0 después de detectar la pérdida de
enlace. El antiguo fallo de MAVROS al cerrar simultáneamente sigue registrado;
3/3 cierres secuenciales nuevos reducen incertidumbre, no garantizan ausencia
del fallo en todas las condiciones.

El receptor graba ahora cinco tópicos mediante rosbag SQLite. La primera bolsa
de SITL duró 61,05 s y contiene 266 mensajes: 55 estado, 51 GPS, 51 IMU,
51 batería y 58 diagnósticos. La reproducción a 4x, en dominio ROS separado y
solo local, recuperó todos esos mensajes; se verificaron conexión/desconexión,
posición y orientación finitas, batería positiva/porcentaje válido y estados
OK de los tres sensores. Script reproducible: `sitl/verify_bag.py` y copia en
`/home/rra/rra_ws/tools/verify_bag.py`. No se reprodujeron órdenes de control.

Registros y las tres bolsas se copiaron a
`C:\RRA\codex_handoff\evidencias\sitl-2026-11-03-telemetria`, fuera del
índice Git. Las carpetas `/tmp/rra-sitl-receiver-fg8mol9a`, `...-y3cjrrf2` y
`...-lpfm9a_4` también existen en la Orange Pi pero son temporales. No hay
autostart. Los procesos y puertos temporales se verificaron cerrados.

Limitaciones: son datos SITL y el enlace de prueba es unidireccional; MAVROS
genera solicitudes automáticas sin respuesta al simulador, que aparecen en sus
logs como timeouts. No demuestra MAVROS bidireccional, control, fiabilidad en
campo ni integración con la H743. El perfil MAVROS predeterminado expone
interfaces de control y sigue sin estar aprobado para conexión física.

## ArduRover SITL con Orange Pi: 2026-11-03

Se descargó el binario oficial precompilado de ArduRover SITL x86-64 4.7.2 en
WSL Ubuntu-22.04: `/home/kitttrain/rra-sitl/ardurover`, SHA-256
`f453fd8217b9d798c873e5c424e139a2a3597b52e31658f76b2c177b523391af`.
No se clonó ni modificó el repositorio de Martín, ni se instaló una toolchain.
Los binarios `stable` pueden cambiar; conservar el hash y versión observados.

El primer arranque con seriales predeterminadas abrió TCP 5762/5763; se cerró
inmediatamente. Al forzar esas salidas a UDP loopback, una auditoría de sockets
reveló un puerto UDP de entrada RC en `0.0.0.0`. Para la prueba final se usó
`unshare -Urn` con loopback dentro de un namespace temporal: ese puerto queda
dentro de la red aislada, sin modificar firewall o red persistente del PC.

El puente `sitl/sitl_local_bridge.py` envió los datagramas mediante IPC Unix
local y un canal SSH de una sola dirección al `sitl/sitl_receiver.py` de la
Orange Pi. El receptor entregó datos a MAVROS por UDP loopback, ROS dominio 179
con descubrimiento local. La prueba final pasó: 1197 datagramas; 53 mensajes
de estado conectado, 52 de GPS, 52 de IMU y 52 mensajes de batería. El estado
conectado fue `MANUAL`, desarmado. Al terminar el flujo se registraron pérdida
de diagnóstico y desconexión; MAVROS y observador terminaron con código 0.
No se enviaron órdenes de armado, movimiento o modo. MAVROS sí efectuó solicitudes
automáticas de información hacia su extremo UDP local, que el puente no lee
ni transmite de vuelta al simulador.

GPS/IMU son datos simulados, no mediciones del vehículo. La batería publicada
fue 0 V y porcentaje -0,01: dato inválido o no disponible, no batería agotada.
La salida original de SITL informó aviso de calibración de acelerómetro; no se
ha corregido ni validado en esta prueba. No se han probado ruta ni movimiento.

Fallos y correcciones conservados: el primer receptor usó QoS fiable y no recibió
GPS, IMU ni batería porque MAVROS ofrecía otra QoS; se cambió a perfil de
sensores. Tras perder enlace, el observador sufrió una carrera con SIGINT y se
corrigió su cierre con gestor de señales y `spin_once`; cuatro pruebas unitarias
y la integrada sintética volvieron a pasar. En otra repetición MAVROS terminó con
señal 11 al cerrarse al mismo tiempo que el observador; un cierre secuencial
pasó una vez, sin demostrar que el problema sea imposible de repetir.

Procedimiento: [sitl/README.md](sitl/README.md). Logs de la última prueba en
`C:\RRA\codex_handoff\evidencias\sitl-2026-11-03-final`; las salidas en
`/tmp/rra-sitl-receiver-3z4zzr4f` y el directorio WSL
`/home/kitttrain/rra-sitl/ensayo-figwth49` pueden no ser permanentes.
No se grabó un rosbag de este ensayo SITL; el rosbag anterior es sintético.
MAVROS sigue exponiendo interfaces de control y no está aprobado para conectarse
al vehículo. Las pruebas físicas siguen pendientes.

## Prueba MAVLink sintética y rosbag: 2026-11-03

Ejecutada en la Orange Pi como `rra` con `ROS_DOMAIN_ID=176` y
`ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`. El script local reproducible es
`rra_telemetry/test/mavlink_loopback_check.py` (también copiado a
`/home/rra/rra_ws/src/rra_telemetry/test/`). Emite únicamente heartbeats
MAVLink 1 sintéticos desarmados a `127.0.0.1:14680`; MAVROS escucha en ese
puerto y su extremo remoto se limita a `127.0.0.1:14681`. GCS deshabilitada.
El emisor no recibe ni ejecuta órdenes y no es ArduRover SITL.

Resultado: MAVROS reconoció el heartbeat y el observador informó conectado;
el envío sostenido durante 12 segundos no produjo pérdidas falsas. Al detener
el emisor, el observador informó primero estado caducado y después MAVROS
confirmó desconexión. No se conectó ningún vehículo ni puerto físico.

Se grabaron 54 mensajes con rosbag SQLite: 25 de `/mavros/state` y 29 de
`/rra/telemetry/diagnostics`. La reproducción devolvió 31 diagnósticos; una
repetición independiente a velocidad 2x confirmó la presencia tanto de conexión
como de pérdida de enlace. Esta prueba de reproducción adicional verificó los
criterios reforzados añadidos después al script; el script completo con esos
dos criterios nuevos aún no se ha vuelto a ejecutar de principio a fin.

Evidencia de la prueba completa en la Orange Pi:
`/tmp/rra-mavlink-check-u7bkl70m`; copia persistida en este PC bajo
`C:\RRA\codex_handoff\evidencias\rra-mavlink-check-u7bkl70m` (el SQLite y
los logs contienen únicamente la prueba sintética). `/tmp` puede borrarse con
el tiempo. La carpeta del PC está excluida mediante `.git/info/exclude`.

En ese momento no se encontró `sim_vehicle.py` ni una instalación en las rutas
comprobadas de la Orange Pi o WSL; el SITL precompilado y las pruebas posteriores
se describen en los apartados más recientes de este documento.

## Reanudación desde Codex Remoto: ROS 2

En la reanudación se localizaron `C:\RRA` y esta carpeta en el portátil
`DESKTOP-UD89C2L`; el checkout conservaba la rama y cambios locales descritos.
SSH como `rra` respondió en `192.168.1.156`, con Ubuntu Resolute ARM64,
kernel y recursos coherentes con el diagnóstico previo. Una prueba nueva con
dos procesos Python `rclpy` en dominio 172 y descubrimiento local publicó y
recibió `RRA prueba local`; ambos finalizaron correctamente. Evidencia temporal
en `/tmp/rra-roscheck-bhFTptsQ/`. No se probó hardware en esta fase.

## Reanudación: MAVROS instalado y arranque aislado

La comprobación `apt-cache policy` confirmó MAVROS 2.16.0-1 para Resolute
ARM64. La simulación de APT propuso 12 paquetes nuevos, 0 actualizados y 0
eliminados; descarga 6,7 MB y ocupación adicional aproximada 84 MB. Se ejecutó
como root, necesario para instalar: `apt-get install -y --no-install-recommends
--no-remove --no-upgrade ros-lyrical-mavros`. La instalación finalizó con
éxito; `ros2 pkg prefix mavros` y `ros2 pkg executables mavros` lo encuentran.
`dpkg --audit` no mostró incidencias, SSH siguió activo y el kernel no cambió.

El instalador proporcionado por MAVROS fue inspeccionado. La documentación
oficial indica que el geoide es obligatorio para el nodo UAS. La descarga de
`egm96-5` con `geographiclib-get-geoids -d` agotó el timeout al 95 %; se
reanudó el archivo parcial con `wget -c`, se comprobó con `bzip2 -t` y se
inspeccionó su contenido antes de extraerlo sin sobrescritura en
`/usr/share/GeographicLib`. El sistema carecía de `bzip2`; APT instaló ese
único paquete sin actualizar ni eliminar otros. `GeoidEval -n egm96-5` con
entrada `0 0` devolvió `17.1630`, comprobando que puede leer el modelo.

Prueba de arranque como `rra`: `ROS_DOMAIN_ID=173`, descubrimiento ROS local,
`ros2 run mavros mavros_node --ros-args -p
fcu_url:=udp://127.0.0.1:14680@127.0.0.1:14681 -p "gcs_url:=''"`. El nodo y
los tópicos aparecieron; cerró con SIGINT y código 0. Las advertencias sobre
timeout de versión del FCU son coherentes con no tener simulador conectado.
Registro temporal `/tmp/rra-mavros-check-edf4y7c4/mavros.log`. La primera
prueba falló al pasar `gcs_url:=` sin un valor válido; se corrigió a cadena
vacía y se repitió. No se conectó a hardware ni se recibió telemetría.

**Límite:** el arranque predeterminado expuso interfaces de control y servicios
además de telemetría. La prueba se limitó a loopback; no usar esa configuración
como sistema de solo lectura ni conectarla al vehículo. Se necesita definir y
verificar aislamiento antes de cualquier conexión física.

## Reanudación: observador ROS provisional

Creado `rra_telemetry` en `C:\RRA\codex_handoff\rra_telemetry` y copiado a
`/home/rra/rra_ws/src/rra_telemetry` en la Orange Pi. Es trabajo local sin
versionar ni publicar y separado del repositorio compartido. Compilado como
usuario `rra` con `colcon build --packages-select rra_telemetry`; el overlay
queda en `/home/rra/rra_ws/install`.

`state_observer` se suscribe a `mavros_msgs/State` y publica solo un
`diagnostic_msgs/DiagnosticArray` en `/rra/telemetry/diagnostics`. Informa sin
datos, estado caducado, desconectado o conectado; la caducidad usa el tiempo
desde la recepción, no un reloj del sensor. No envía órdenes ni usa servicios.
Los tópicos y el umbral son parámetros. No informa posición o batería todavía.

Verificación como `rra`, con ROS y overlay cargados: cuatro pruebas unitarias
con `python3 -m unittest discover -s test -p 'test_*.py' -v`; y prueba ROS
`ROS_DOMAIN_ID=174 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST python3
test/integration_check.py`: pasan los cuatro estados con publicador simulado.
La prueba reproducible está junto al paquete; log temporal
`/tmp/rra-observer-check-vd4c6m_5/observer.log`.

Con MAVROS real ejecutándose solo en loopback, pero sin simulador ni autopiloto,
el observador informó `Sin datos de MAVROS`, no `desconectado`; la expectativa
inicial de recibir un estado desconectado falló. Ambos procesos cerraron con
código 0. Logs temporales `/tmp/rra-mavros-observer-a5rh14gv/`. Esto prueba
que declara falta de datos; no acredita recepción de telemetría MAVLink.

Problemas corregidos: el correo de ejemplo `rra@localhost` no era válido en el
manifiesto ROS y colcon trató el paquete como Python genérico; se sustituyó por
`rra@example.invalid` y se reconstruyó. La primera publicación de diagnósticos
abortó porque `DiagnosticStatus.level` es un campo `byte` y requiere un valor
`bytes` de longitud uno; se corrigió el tipo y pasaron las pruebas integradas.
La hipótesis inicial de que el aborto se debía a los acentos fue incorrecta.

## Completado y verificado

- Proyecto: `C:\RRA`, Git `feature/orangepi-ros2`, base `a370189d`, remoto
  `https://github.com/Gonellarro/RRA.git`. Rama y cambios no publicados. El
  directorio de la sesión anterior era `C:\KITT2`, diferente del proyecto RRA.
- PC Windows: Git 2.53.0, Python 3.10.11, Node 26.13.0, VS Code 1.141.2 y
  Codex CLI 0.162.0-alpha.17.2 disponibles al consultar.
- Orange Pi `orangepizero2w`: Armbian Community 26.11.0-trunk.120, imagen
  nightly, Ubuntu 26.04 Resolute ARM64, kernel 6.18.60-current-sunxi64. El
  2026-11-03: 3,8 GiB RAM, 1,9 GiB swap zram y 56 GiB libres de 58 GiB en `/`.
- SSH con clave desde este usuario Windows hacia `rra@192.168.1.156` pasó;
  `rra` pertenece a sudo. Root también se verificó en la sesión anterior y no
  se deshabilitó. No se ha modificado SSH durante esta transferencia.
- Instalados ROS base Lyrical `0.13.0-3resolute.20260919.195359`,
  `python3-rosdep` 0.27.0-1 y `python3-colcon-common-extensions` 0.3.0-100.
  También se instalaron ejemplos Python. `rosdep init` y actualización como
  `rra` pasaron; `colcon list` y `ros2 bag --help` funcionaron.
- `/home/rra/rra_ws/src` existe; el `.bashrc` de `rra` carga ROS y el overlay si
  existe. Una sesión interactiva nueva mostró `ROS_DISTRO=lyrical`.
- El 2026-11-03, dos procesos ROS con `rclpy` intercambiaron un mensaje local
  y terminaron con éxito. No es prueba de MAVROS ni del rover. El script
  `C:\RRA\scripts\companion_diagnostico.sh` fue ejecutado con éxito en la
  placa, donde se copió a `/home/rra/rra_ws/tools/companion_diagnostico.sh`.
- `dpkg --audit` estaba limpio al terminar la instalación y SSH seguía activo.

## Archivos y cambios locales anteriores

`docs/diario.md` contiene una entrada añadida sin commit;
`docs/companion_orange_pi.md` y `scripts/companion_diagnostico.sh` no están
versionados todavía. Preservarlos; no asumir que existen en GitHub. El
repositorio tenía en `main` documentación de proyecto y SITL, sin paquetes
ROS RRA versionados. Estos archivos no pertenecen a este directorio de
transferencia; no copiarlos a servicios externos sin autorización.

## Pendiente y no verificado

- MAVROS, el geoide y `rra_telemetry` se han probado con SITL y rosbag; no se
  han probado conexión a la H743, sensores físicos o control físico.
- En la primera prueba, `set -u` impidió cargar el entorno ROS. Otra recibió
  mensajes pero un cierre forzado por `timeout` causó una excepción; la
  repetición con dos nodos que terminan normalmente pasó. Los logs en `/tmp`
  de la placa pueden desaparecer y no son evidencia persistente garantizada.
- `packages.ros.org` presenta certificado para otro nombre en HTTPS: los
  mantenedores indican usar HTTP con índices APT firmados. Se instaló el
  configurador oficial y APT verificó la firma; no desactivar validaciones.
- La imagen Armbian es comunitaria nightly, no una instalación Ubuntu estándar;
  compatibilidad práctica validada solo para la prueba ROS indicada.
- Una ejecución SSH no interactiva del script de diagnóstico indicó ROS «no
  cargada», aunque el paquete está instalado: esa sesión no carga `.bashrc`.
  Cargar `source /opt/ros/lyrical/setup.bash` antes de diagnosticar ROS así.
- El usuario indica que Remote ya está vinculado al portátil. Esta sesión no
  ha probado una nueva conexión móvil ni verificado la selección del checkout.
  Una copia nueva o worktree no incorpora automáticamente archivos ignorados,
  cambios sin commit, claves SSH ni el estado instalado en la Orange Pi.
- `C:\RRA` está fuera de la ruta OneDrive detectada y no es un enlace; no se
  ha auditado la existencia de otros sistemas de copia o sincronización del PC.
## Reanudación local y preparación de fase 4 — 2026-11-04

Se leyeron los documentos de continuidad, README, roadmap, diario, documentación local del companion y guías SITL. El repositorio continúa en `feature/orangepi-ros2`; siguen intactos los cambios previos `docs/diario.md`, `docs/companion_orange_pi.md` y `scripts/companion_diagnostico.sh`. No hubo cambios en Git ni sincronización externa.

El espacio libre observado en C: fue 19,17 GiB y en D: 597,58 GiB. WSL Ubuntu-22.04 está disponible; el binario SITL de ArduRover conserva el hash previamente registrado. No se ejecutaron escenarios de fallo o control de fase 4. La comprobación SSH de solo lectura a `rra@192.168.1.156` agotó el timeout; esto no determina si la Orange Pi está apagada o inaccesible por otra causa. No se cambió red ni SSH.

La fase 3 permanece completada solo en SITL. Se preparó el diseño local de fase 4 en `sitl/FASE4_DISENO.md`. F4-0 consultó los parámetros efectivos en SITL aislado, sin armar ni cambiar modos: `FS_GCS_ENABLE=0`, `FS_GCS_TIMEOUT=5`, `FS_ACTION=2` (HOLD) y `FS_OPTIONS=0`; el heartbeat mostró `armed=false`. El failsafe GCS estaba deshabilitado en el perfil oficial. F4-1 a F4-3 se probaron después con perfiles temporales de SITL y resultados PASS en los tres valores de `FS_GCS_ENABLE`; detalles, límites y hashes en `sitl/FASE4_DISENO.md` y `evidencias/fase4-gcs-2026-11-04/resumen.json`.

**Corrección de estado (2026-11-04):** el párrafo anterior quedó obsoleto tras la autorización expresa del usuario para F4-1 a F4-3 en SITL aislado. Esos ensayos sí se ejecutaron y sus resultados PASS están documentados abajo. F4-4 y F4-5 siguen pendientes; no hay conexión física ni prueba de control en el rover.
### Resultados F4-1…F4-3 — 2026-11-04

Se probaron en tres procesos SITL aislados la pérdida del heartbeat GCS durante AUTO y la reconexión. `FS_GCS_ENABLE=0` mantuvo AUTO sin evento GCS; `=1` generó `GCS Failsafe`, cambió a HOLD a los 6,0 s y permaneció HOLD tras reconectar; `=2` registró el failsafe pero `Failsafe - Continuing Auto Mode`, manteniendo AUTO. Ventana de pérdida 8,16 s. Cada cierre fue HOLD y desarmado, con comprobación explícita del heartbeat final. Los parámetros efectivos se leyeron antes de armar.

La primera pasada de los perfiles 1 y 2 se descartó porque apareció `Radio Failsafe` antes del umbral GCS. La guía oficial de operación solo GCS permitió aislar esa interferencia en SITL con `FS_THR_ENABLE=0` y `RC_PROTOCOLS=0`, perfil temporal nunca aplicado a hardware. En la repetición no apareció `Radio Failsafe`; las tres ejecuciones pasaron las comprobaciones y DataFlash registró los modos 0→10→4. El informe, JSONL, perfiles y registros DataFlash están en `evidencias/fase4-gcs-2026-11-04/`; eventos y DataFlash se compararon por SHA-256 con WSL. No se usó la Orange Pi ni hardware real.

F4-0 a F4-3 completados en simulación. Siguen pendientes F4-4 (caducidad de consignas GUIDED, aún no existe esa interfaz en el companion) y F4-5 (arbitraje entre fuentes, política aún por definir). No se considera finalizada toda la fase 4 hasta acotar y validar esos límites.


## Fase 4 SITL: F4-4 y F4-5 — 2026-11-04

El usuario autorizó continuar con ambos ensayos de fase 4. Se añadió el runner local `sitl/fase4_guided_authority.py`; su resumen reproducible está en `evidencias/fase4-guided-2026-11-04/resumen.json` y los eventos JSONL, perfiles y DataFlash en las subcarpetas de evidencia. Los casos usaron el binario ArduRover SITL 4.7.2 ya verificado y un namespace WSL distinto por ejecución con única interfaz `lo`.

F4-4 pasó para el comportamiento predeterminado observado: se envió una consigna local NED de 0,35 m/s durante 2,5 s; sin nuevas consignas, SITL informó parada a los 2,84 s, el groundspeed cayó de 0,459 a 0,024 m/s en seis segundos y SERVO3 terminó en 1500. Se seleccionó HOLD y se confirmó desarmado. El parámetro `GUID_TIMEOUT` no respondió a `PARAM_REQUEST_READ`, así que su ajuste explícito sigue sin validar. Hubo un primer intento detenido antes de armar por esta falta de respuesta y otro ensayo cuya comprobación de velocidad inicial estaba defectuosa; el runner corregido se repitió y pasó. No se aplicó el parámetro a hardware ni se amplió la duración de movimiento para sortear la discrepancia.

F4-5 tuvo dos partes desarmadas. Solo con `MAV_GCS_SYSID=42` y `MAV_GCS_SYSID_HI=42`, las solicitudes SET_MODE de SYSID 255 y 42 fueron aceptadas de forma alterna y prevaleció la última. En un segundo caso, añadiendo `MAV_OPTIONS=1`, las órdenes de 255 se ignoraron y las de 42 sí cambiaron GUIDED/HOLD. El filtro global funcionó para SET_MODE en ese SITL. Los IDs de fuente no se autenticaron criptográficamente y no se probaron otros mensajes/canales ni MAVROS.

La fase 4 está ensayada hasta F4-5 en SITL. Sigue sin definirse si el Companion tendrá interfaz de control; permanece como observador. Para cualquier futura actuación habrá que definir una puerta de control y autoridad única, y validar explícitamente su comportamiento antes de conectar hardware. Orange Pi, H743, GitHub y sincronización externa no participaron. No quedó proceso `ardurover` activo.

Seguimiento F4-5: el segundo caso añadió `MAV_OPTIONS=1`, descrito por ArduPilot para aceptar MAVLink solo desde los SYSID configurados. El ensayo desarmado comprobó que SYSID 255 no cambia modo y SYSID 42 sí. Evidencia completa en `evidencias/fase4-guided-2026-11-04/f4-5-guarded/`; esto es un filtro de IDs observado en SITL, no prueba de autenticación ni validación de hardware.

## Pausa del proyecto — 2026-11-04

El usuario ha solicitado paralizar el proyecto. Estado guardado en Git local; no continuar tareas hasta nueva solicitud. Al reanudar, revisar el estado de fase 4 y decidir si el Companion seguirá siendo solo observador o requerirá una puerta de control; no conectar MAVROS al hardware ni emitir órdenes físicas. El commit de esta pausa permanece solo en este clon.

## Reanudación y acceso SSH — 2026-11-04

El usuario reanudó el proyecto y solicitó revisar SSH y resumir el trabajo pendiente. Se intentó conexión de solo lectura desde Windows con la clave configurada de `rra`, `BatchMode=yes`, `StrictHostKeyChecking=yes` y `ConnectTimeout=8` a `rra@192.168.1.156`; agotó timeout (código SSH 255). Una comprobación posterior dio ICMP sin respuesta y TCP 22 no alcanzable. No se puede concluir que la placa esté apagada: la IP pudo cambiar o la placa/red/servicio pueden estar temporalmente inaccesibles. No se hicieron escaneos, cambios de red, SSH, claves ni instalaciones. Git local estaba en `3565aca` al reanudar; sin operaciones con GitHub.

## Reanudación: acceso SSH recuperado y diagnóstico actual — 2026-11-04

Tras la captura del router que confirma `orangepizero2w` en `192.168.1.156` (MAC `e4:33:89:2e:8d:ad`), se repitió SSH con la clave de `rra`, `BatchMode=yes` y host key previamente conocida. La autenticación por clave pasó; el host reportó `orangepizero2w`, usuario `rra`, arquitectura `aarch64`, Armbian community 26.11.0-trunk.120 Resolute y `ROS_DISTRO=lyrical`. El primer timeout no se reprodujo en la siguiente conexión. `Test-NetConnection` vio TCP/22 accesible y el servicio SSH está activo.

Diagnóstico remoto de solo lectura: `/opt/ros/lyrical` y el overlay existen; `ros2 pkg prefix mavros` devuelve `/opt/ros/lyrical`, `rra_telemetry` devuelve `/home/rra/rra_ws/install/rra_telemetry`, y `colcon list` encuentra `rra_telemetry` en `/home/rra/rra_ws/src`. Versiones consultadas por dpkg: ROS base `0.13.0-3resolute.20260919.195359`, MAVROS `2.16.0-1resolute.20260928.090531`, rosdep `0.27.0-1`, colcon `0.3.0-100`, bzip2 `1.0.8-6ubuntu0.1`. `dpkg --audit` no informó incidencias; `GeoidEval -n egm96-5` con `0 0` devolvió `17.1630`; el script de diagnóstico acabó con código 0. Raíz: 56 GiB libres de 58 GiB; RAM disponible 3,6 GiB, swap sin uso. No se instalaron paquetes, cambiaron configuraciones, modificó SSH ni ejecutaron órdenes de control.

## Reanudación: pruebas y análisis de MAVROS — 2026-11-04

El usuario pidió continuar los cuatro frentes de trabajo. Se validó SSH por clave a `rra@192.168.1.156`, el hostname `orangepizero2w`, arquitectura `aarch64`, ROS Lyrical y versiones de paquetes. El código fuente de `rra_telemetry` local coincide por SHA-256 con `/home/rra/rra_ws/src/rra_telemetry`.

Verificación en la Orange Pi, sin FCU/H743:

- `colcon build --packages-select rra_telemetry`: correcto.
- `python3 -m unittest discover -s test -p 'test_*.py' -v`: 9/9 correcto.
- `ROS_DOMAIN_ID=174 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST python3 test/integration_check.py`: correcto con mensajes simulados.
- `ROS_DOMAIN_ID=176 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST python3 test/mavlink_loopback_check.py`: correcto. Heartbeat sintético por loopback, conectado sostenido, caducidad, desconexión y rosbag reproducido. 54 mensajes (26 estado, 28 diagnóstico), 31,77 s. Evidencia local en `evidencias/readonly-validation-2026-11-04/mavlink-loopback/`.

**Resultado de seguridad importante:** se arrancó MAVROS aislado en ROS_DOMAIN_ID 191/LOCALHOST con `plugin_allowlist=[sys_status, imu, global_position]`, `plugin_denylist=["*"]` y URL FCU solo `127.0.0.1:14682/14683`. El grafo aún anunció `/mavros/set_mode`, `/mavros_router/add_endpoint`, `/mavros_router/del_endpoint`, `/mavros/sys/set_stream_rate`, `/mavros/sys/set_message_interval`, `/mavros/sys/statustext/send`, `/mavros/global_position/set_gp_origin`, `vehicle_info_get` y canales MAVLink internos. La allowlist no constituye frontera efectiva de solo lectura. La inspección de interfaces y la propuesta están en `MAVROS_READONLY_BOUNDARY.md`. No conectar MAVROS a la H743 hasta diseñar y probar una barrera adicional.

No quedó proceso `mavros_node`, ni sockets UDP de prueba. No se vieron unidades `rra`/MAVROS activas o habilitadas en systemd. Un proceso `ros2 daemon` de la CLI seguía presente tras introspeccionar el grafo; no es un servicio del companion y no se detuvo. No se activó autostart ni se modificó configuración permanente de la Orange Pi.

El README y roadmap local indican los datos de H743 pendientes, pero no hay firmware/configuración física registrada. El usuario confirma que la Orange Pi no está conectada físicamente a la placa; no se hizo prueba física. La lista requerida y el procedimiento supervisado propuesto están en `MAVROS_READONLY_BOUNDARY.md` y el inventario está en `H743_DATOS_HARDWARE.md`.

Se redactó allí una propuesta de operación continua con servicios systemd separados, journald y límites de rosbag. No se creó ni activó ninguna unidad, ni se inició grabación continua. `ros2 security` y sus herramientas de gestión de keystores/permisos están disponibles; no se generaron claves o políticas. Siguientes pasos: diseñar/probar localmente un gateway unidireccional y una política DDS con pruebas positivas y negativas; recoger del responsable la información real de H743; solo después revisar un despliegue manual. Cambios y evidencias siguen locales; no GitHub, commit ni push.

## Ensayo de gateway con permisos DDS — 2026-11-04

El usuario autorizó un ensayo de gateway unidireccional y permisos DDS. Se creó el prototipo local `codex_handoff/gateway_probe/` y se transfirió temporalmente a `/tmp` de la Orange Pi. Con ROS Lyrical, ROS_DOMAIN_ID 188, descubrimiento LOCALHOST y SROS2 `ROS_SECURITY_STRATEGY=Enforce`, se crearon identidades/permisos efímeros para productor simulado, gateway y app. No se instaló software ni se tocaron los servicios permanentes.

**PASS sintético:** la app recibió y validó estado conectado/desarmado, GPS, IMU y batería por los cuatro tópicos de salida del gateway. DDS denegó a la app crear suscriptor directo de `/mavros/state`, cliente para `/mavros/set_mode` y publicador para `/mavros/setpoint_velocity/cmd_vel`. Se comprobó que el servicio sintético SetMode estaba creado y que no recibió llamada; la fuente no recibió setpoint. Evidencia: `evidencias/readonly-validation-2026-11-04/gateway-dds-probe-pass.txt`. Los directorios de claves/políticas bajo `/tmp`, scripts de prueba remotos, procesos y puertos de ensayo se retiraron; no quedó MAVROS o gateway activo.

Esto demuestra la separación gateway+política SROS2 en nodos sintéticos y la configuración de permisos del prototipo; no valida el `mavros_node` instalado bajo SROS2, los demás servicios/endpoint del router, el flujo real FCU ni hardware. Las pruebas previas con MAVROS real mostraron que la allowlist no es suficiente. Próximo: repetir el inventario y las denegaciones con MAVROS real en loopback, sin FCU, luego mantenerlo desconectado hasta que esa prueba pase. H743 y operación continua siguen pendientes; autostart continúa desactivado/no creado. No GitHub, commit ni push.

## Recopilación documental de H743 — 2026-11-04

El usuario confirma que Orange Pi no está físicamente conectada a la H743 y que el modelo es **MATEK H743-WLITE**. Por tanto, no es posible leer firmware, parámetros ni telemetría del autopiloto mediante el companion actual. La identificación del modelo procede del usuario; no se ha contrastado con la etiqueta física ni se conoce la revisión o configuración instalada. ArduRover 4.7.2 y los parámetros citados en `sitl/FASE4_DISENO.md` son datos SITL, no del H743. Se creó `H743_DATOS_HARDWARE.md` con estos hechos, límites y lista de campos reales aún necesarios. No se consultó el autopiloto, conectó cable, ni cambió configuración. Todo sigue local.

## Identificación de modelo H743 — 2026-11-04

El usuario especifica que la placa es **MATEK H743-WLITE**. Se actualizó la identificación del diseño en `README.md`, `Roadmap_RRA_Software.md` y los documentos locales de continuidad. La etiqueta física, revisión, firmware, parámetros y cableado siguen sin comprobarse porque Orange Pi no está conectada a la placa. Sin cambios de código ni de hardware; no se sincronizó con GitHub.

## Reconciliación con el documento maestro RRA — 2026-11-04

El documento maestro recibido del usuario (revisión 1.4, fechado 2026-11-04) informa de pruebas físicas previas: H743-WLite con ArduRover 4.7.2, QUESCAN AN251/M10 y brújula, RC/actuadores y una misión AUTO elemental. Se incorpora este estado como **resultado reportado por el responsable**, no como medición obtenida por la Orange Pi ni como informe físico verificado en esta revisión. No contradice que la Orange Pi no esté conectada a la H743: son vías y pruebas distintas. La revisión física, firmware/configuración y resultados completos de failsafe siguen sin estar comprobados por el companion.

Para el companion, se confirma por los registros de esta carpeta: ROS 2 Lyrical y MAVROS 2.16.0 instalados en Orange Pi; paquete `rra_telemetry` construido y probado; SITL/MAVLink loopback y rosbag verificados; prototipo de gateway SROS2 probado primero con nodos sintéticos y después con MAVROS real. Una matriz ampliada del grafo observado denegó 69 suscripciones directas, 73 publicadores y 233 clientes de servicio desde la app; no aparecieron acciones ROS. MAVROS conserva interfaces de escritura para su propia identidad. El resultado no valida FCU/UART ni un proceso MAVROS comprometido y no autoriza conectar la H743. La nota anterior en `docs/companion_orange_pi.md` que decía “aún sin instalar” era del estado inicial del 3/11 y quedó sustituida por la actualización del 4/11.

El usuario solicita que, cuando la H743 esté físicamente conectada al companion, se inspeccione firmware/configuración mediante ROS 2/MAVROS. Es una tarea futura condicionada a esa conexión y a disponer de una frontera de solo lectura efectiva: empezar por identificar versión y leer datos, contrastarlos con la estación de control y no emitir armado, cambios de modo, parámetros ni consignas. No se realizó conexión ni inspección física en esta actualización.

## Conexionado H743 comunicado por el usuario — 2026-11-04

Se añadió el cableado declarado por el usuario a `H743_DATOS_HARDWARE.md`: señal ESC en S1 con el cable de alimentación/voltaje del ESC desconectado; servo de dirección en S3; ESP32 DroneBridge en TX7/RX7; receptor RC en RX6; GNSS QUESCAN por TX2/RX2 y brújula por DA1/CL1 (I²C1). TX1/RX1, identificado por MATEK como TELEM2/UART1/`SERIAL2`, está libre según el usuario y queda como candidato para conectar la Orange Pi. Se anotó una propuesta unidireccional inicial TX1→Orange Pi UART5_RX más masa común, sin instalarla. El retorno RX1 quedaría desconectado hasta validar el aislamiento MAVROS. Estos datos describen el cableado comunicado, no una inspección física o lectura de parámetros; no se hizo conexión ni se modificó la FCU. Todo local.

## MAVROS real con política SROS2 — 2026-11-04

En la Orange Pi, el `mavros_node` real 2.16.0 arrancó bajo SROS2 Enforce en el
dominio 197 y descubrimiento LOCALHOST. El FCU se fijó a UDP loopback
127.0.0.1:14682/14683 y recibió solo heartbeat MAVLink sintético desarmado. El
gateway recibió el estado conectado/desarmado de MAVROS y lo reexpuso como
`/rra/fcu/state`; la aplicación con identidad SROS2 distinta recibió esa
telemetría.

**PASS para la matriz parcial de 11 endpoints:** DDS impidió a la aplicación
crear suscriptor directo a `/mavros/state`, clientes para `/mavros/set_mode`,
`/mavros/cmd/arming`, `/mavros/cmd/command`, `/mavros/param/set`,
`/mavros/mission/push` y `/mavros_router/add_endpoint`, y publicadores para
`/mavros/setpoint_velocity/cmd_vel`, `/mavros/rc/override`,
`/mavros/statustext/send` y `/uas1/mavlink_source`. No se llamó ningún servicio
ni se publicó ningún mensaje de escritura. Evidencia:
`evidencias/readonly-validation-2026-11-04/mavros-sros2-real-probe-pass.txt`.

No había H743/FCU conectado. MAVROS conserva APIs de escritura para su propia
identidad y realizó solicitudes automáticas sin respuesta del emisor sintético.
La prueba no es exhaustiva y no autoriza UART bidireccional ni un servicio
permanente. El siguiente paso es ampliar la matriz con las demás interfaces de
control, parámetros, misiones, router y MAVLink del grafo. Se confirmó que no
quedaron procesos ni puertos del ensayo. Sin cambios en red, SSH, FCU, servicios,
GitHub ni remoto.

## Grafo completo MAVROS bajo SROS2 — 2026-11-04

Se tomó el inventario del grafo real de MAVROS 2.16.0 bajo ROS Lyrical: 74
Tópicos, 69 de MAVROS/MAVLink, 233 servicios incluidos los ocultos (190
servicios ROS de parámetros, conteo que se solapa con familias) y cero acciones
anunciadas. Se repitió el gateway/aplicación con SROS2 Enforce en dominio 199 y
solo loopback.

Resultado PASS: llegaron las cuatro salidas autorizadas como suscripciones; el
estado sintético conectado/desarmado llegó por `/rra/fcu/state`. DDS denegó 69
suscripciones directas y 73 publicaciones (69 tópicos MAVROS/MAVLink más las
cuatro salidas del gateway), además de los 233 clientes de servicio observados.
Se incluyeron las interfaces de lectura/escritura de parámetros, MAVROS
param pull/set, armado/modo/comandos, misiones, geofence/rallypoints, FTP,
`set_gp_origin`, intervalos, router y servicios de parámetros de nodos. No se
llamó servicio ni publicó mensaje; cero acciones estaban anunciadas para probar.
El snapshot completo está en `mavros_sros_probe/runtime_graph_inventory.txt` y
el resumen en `evidencias/readonly-validation-2026-11-04/mavros-sros2-expanded-pass.txt`.

Una prueba intermedia no arrancó el gateway por un import incorrecto durante un
ajuste de cierre; se corrigió y la repetición completa pasó sin traceback. La
comprobación final confirmó que no quedaron procesos, puertos ni directorios
remotos temporales. No se conectó hardware ni se cambió una configuración
persistente. El resultado cubre el grafo de esta instalación y no autoriza el
uso de otra identidad, el enlace bidireccional ni la conexión a H743.

## Ensayo bidireccional y consultas limitadas — 2026-11-04

**Completado en SITL aislado:** ArduRover SITL 4.7.2 en namespace de red WSL con solo loopback se conectó a MAVROS 2.16.0 mediante un túnel bidireccional por SSH stdio y sockets Unix locales. ROS_DOMAIN_ID=202 y descubrimiento LOCALHOST; UDP Pi 14680/14681 enlazado solo a 127.0.0.1. Pasaron 1.517 datagramas SITL→MAVROS y 47 MAVROS→SITL. SSH terminó con exit 0. No se usó FCU, H743, UART ni actuadores.

Se implementó un broker ROS temporal bajo identidad `/readonly_query`, aparte de `/readonly_app`, gateway y MAVROS. La aplicación dispone de tres consultas `std_srvs/Trigger`: estado, versión y parámetros. El broker consulta el estado del gateway; llama a MAVROS `VehicleInfoGet`; y para parámetros llama a `ParamPull` seguido de `GetParameters` con la lista fijada a `BATT_MONITOR`. Política separada en `mavros_sros_probe/policy_bidirectional.xml`; scripts de ensayo en `mavros_sros_probe/` y `sitl/sitl_bidirectional_bridge.py`.

**Resultado SROS2 Enforce:** la app recibió estado conectado/desarmado en MANUAL; la consulta de parámetros respondió `ParamPull success=true`, 1.253 parámetros, `BATT_MONITOR=4` (entero). DDS denegó 233/233 clientes hacia servicios MAVROS y 142 endpoints de tópicos (lectores/escritores directos de 69 tópicos y cuatro publicaciones al gateway). Se incluyen escritura de parámetros, armado, modo, misiones y comandos; no se llamó ni publicó por ellos. El inventario tenía cero acciones ROS.

**Límite de versión:** `VehicleInfoGet` respondió correctamente, pero con `available_info=1` (solo heartbeat); SITL no entregó el bit `HAVE_INFO_AUTOPILOT_VERSION` y MAVROS registró que `AUTOPILOT_VERSION` no estaba soportado. La API reporta firmware no disponible. El texto del log MAVROS `ArduRover V4.7.2 (fb773567)` no es un valor obtenido por la consulta. Resolver una fuente verificable para la versión numérica cuando se conecte una FCU o antes mediante otro ensayo SITL de lectura.

Al detener SITL, la app vio `connected=false`; una nueva solicitud limitada de parámetros obtuvo un fallo acotado por timeout (`DISCONNECT_PASS`). Se corrigió el entorno de creación de permisos SROS2 para ROS_DOMAIN_ID 202, las QoS del gateway y el túnel de retorno tras detener SITL. Evidencia resumida en `evidencias/mavros-bidirectional-sros-2026-11-04/`.

No se activó un servicio permanente; los nodos, keystore y puertos temporales se cerraron. No hubo cambios de red, SSH, hardware, GitHub ni remoto. El broker limita nombres de parámetros en su código porque SROS2 no restringe el payload de `GetParameters`; el broker bajo su enclave es un límite adicional de confianza. MAVROS mantiene capacidades de escritura en su propia identidad, por lo que no se ha probado resistencia al compromiso de MAVROS o del broker.

## Seguimiento de los puntos 1–3 — 2026-11-04

**1. Versión:** se ejecutó `sitl/sitl_autopilot_version_probe.py` en WSL con ArduRover SITL aislado en namespace de red. La solicitud MAVLink `MAV_CMD_REQUEST_MESSAGE=512`, `message_id=148` recibió ACK aceptado (`result=0`) y `AUTOPILOT_VERSION`: ArduRover 4.7.2, `custom_version_hex=6662373733353637` (`fb773567`). Esto valida la solicitud directa en SITL, pero no resuelve el endpoint ROS: `VehicleInfoGet` de MAVROS aún informa solo heartbeat (`available_info=1`), por lo que `/rra/readonly/get_version` conserva firmware como no disponible. No se habilitó el servicio genérico `/mavros/cmd/command`; integrar versión requiere ruta MAVROS especializada y restringida.

**2. Paquete local:** `rra_companion_readonly` quedó copiado en `~/rra_ws/src/rra_companion_readonly` en Orange Pi, recompilado con `colcon build --packages-select rra_companion_readonly` y disponible con los ejecutables `readonly_gateway` y `readonly_query`. Cuatro pruebas unitarias pasan. Los nodos continúan de arranque manual; no se creó ni activó autostart.

**3. Allowlist/SROS2:** se verificó que `Trigger` no recibe nombres de parámetros y que el broker construye `GetParameters` con `BATT_MONITOR` solamente; respuestas vacías/no tipadas se rechazan. La integración usando el paquete instalado pasó bajo SROS2 Enforce: 1.517 datagramas SITL→MAVROS y 47 de vuelta, `SSH_EXIT 0`; consultas de estado conectado/desarmado/MANUAL y `BATT_MONITOR=4` correctas; 233/233 clientes de servicios MAVROS y 142 endpoints directos de tópicos denegados. Tras parar SITL, la app recibió desconexión y el intento de lectura terminó en timeout acotado. No hubo solicitudes de escritura. Evidencia concisa en `evidencias/mavros-bidirectional-sros-2026-11-04/seguimiento-puntos-1-3.txt` y `version_request_result.json`.

La primera repetición del ensayo falló porque la Orange Pi conservaba la versión previa del gateway, que asignaba a `Node.publishers`, propiedad reservada de `rclpy.Node`. Se desplegó el paquete local actualizado, se reconstruyó y la repetición completa pasó. El fallo se conserva como incidencia resuelta. Al cierre se confirmó que no quedaban procesos MAVROS/gateway/broker ni sockets UDP 14680–14689; se retiraron keystores, logs y staging temporales exactos en Orange Pi y los directorios SITL de esta sesión en WSL. No conectada la H743.

## Plugin de versión MAVROS y repetición SROS2 — 2026-11-05

Se implementó en `packages/rra_mavros_version_plugin/` un plugin C++ externo para MAVROS 2.16.0. Su único servicio ROS es un `std_srvs/Trigger` sin datos de comando; envía fijo `MAV_CMD_REQUEST_MESSAGE=512` con `message_id=148` y publica `AUTOPILOT_VERSION` como JSON decodificado. Desactiva servicios de parámetros del nodo. Se compiló en la Orange Pi desde `~/rra_ws` y quedó instalado en ese overlay; no se creó autostart ni servicio persistente. El paquete `rra_companion_readonly` se recompiló con espera máxima de 3 s por el primer estado recibido para evitar un fallo de carrera al arrancar.

Ensayo integrado desde WSL Ubuntu-22.04, ArduRover SITL 4.7.2 aislado con `unshare -Urn`, túnel SSH stdio y UDP de MAVROS limitado a loopback. Bajo SROS2 Enforce y `ROS_DOMAIN_ID=202`, la app obtuvo `connected=true`, `armed=false`, `mode=MANUAL`; versión `[4,7,2]`, hash `fb773567` (`flight_sw_version=67568383`); y `BATT_MONITOR=4`, tipo entero, después de pull de 1.253 parámetros. La auditoría denegó 233/233 clientes de servicios MAVROS y 142 endpoints directos de tópicos. Al parar SITL se informó desconectado y el pull falló con timeout acotado. Transporte: 1.519 datagramas SITL→MAVROS, 48 MAVROS→SITL, `SSH_EXIT 0`. Evidencia y logs completos en `evidencias/mavros-version-plugin-sros-2026-11-05/`.

Una integración intermedia falló porque el plugin necesitaba permiso SROS2 de respuesta para `get_type_description`; al añadirlo, otra pasada llegó al plugin. Esa pasó la versión y parámetros, pero descubrió una carrera en la primera lectura de estado; se corrigió esperando hasta 3 s a recibir el primer estado. La pasada final muestra mensajes SECURITY de denegación en el log de la app, generados deliberadamente por la auditoría negativa; no impidieron crear las consultas autorizadas.

Límites: validado en SITL, no en H743/FCU/UART. El plugin solo está desplegado en el workspace de la Orange Pi y depende de la política SROS2 actual; no se ha configurado inicio automático. La protección de la allowlist de parámetro sigue residiendo en el proceso broker, porque DDS no restringe el campo `names` de `GetParameters`. MAVROS conserva sus capacidades en su identidad. Se copiaron los logs a la evidencia local y se limpiaron los archivos temporales exactos del ensayo en la Pi; no quedaron procesos ni sockets 14680/14681. No se tocó GitHub, red, SSH, H743 ni actuadores.

Dependencia de compilación: se instaló build-essential en la Orange Pi para compilar el plugin C++; la instalación apt resolvió 40 paquetes, descargó aproximadamente 70 MB y usó alrededor de 250 MB. No se actualizaron ni eliminaron paquetes existentes. El disco raíz seguía con unos 55 GB libres tras instalar.

## Repetición, timeout, reconexión y límite BATT_MONITOR — 2026-11-05

Se ejecutó SITL bajo SROS2 Enforce y se amplió el plugin MAVROS para atender solo dos lecturas fijas: `AUTOPILOT_VERSION` mediante `MAV_CMD_REQUEST_MESSAGE` 512/mensaje 148, y `BATT_MONITOR` mediante `PARAM_REQUEST_READ` con ID literal. El broker ya no importa ni llama `ParamPull` o `GetParameters` durante su operación normal, así que no provoca la descarga de la lista completa (1.253 parámetros en SITL) ni puede pedir cualquier parámetro en caché.

El plugin devuelve `request_id` en la respuesta del Trigger y el resultado publicado. El broker solo acepta el resultado con el mismo identificador y espera como máximo 8 s. Pruebas: tres llamadas de versión seguidas devolvieron `[4,7,2]`/`fb773567` con IDs 1–3; al filtrar un mensaje MAVLink 148 con el enlace activo, la consulta terminó con timeout (se descartó 1 respuesta); una solicitud inmediata tras volver a permitir respuestas también pasó; al filtrar ambos sentidos del túnel, MAVROS detectó desconexión y rechazó ambas lecturas; al restaurar el enlace reconectó y recuperó versión y `BATT_MONITOR=4`. Después se paró SITL y el servicio fijo de parámetro falló rápidamente. Marcadores `RECOVERY`, `READS_PASS`, `DISCONNECT_PASS` y `SSH_EXIT 0`.

La prueba adicional del broker con su identidad `/readonly_query` intentó crear clientes de `/mavros/param/pull` y `/mavros/param/get_parameters`: SROS2 Enforce denegó ambos. La app siguió sin poder crear 233/233 clientes de servicios MAVROS ni 142 endpoints directos de tópicos. Build colcon de `rra_mavros_version_plugin` y `rra_companion_readonly`: correcto; unittest del paquete: 4/4 OK. Evidencia/logs en `evidencias/mavros-repeat-reconnect-boundary-2026-11-05/`.

Esta medida reduce la confianza necesaria en el código Python del broker: una ejecución comprometida bajo el enclave firmado no puede leer parámetros arbitrarios usando los servicios genéricos de MAVROS. La confianza aún incluye el plugin C++ y el proceso/enclave MAVROS, que tiene acceso interno al bus UAS. MAVLink `PARAM_VALUE` no incluye un identificador de transacción: el `request_id` correlaciona las respuestas ROS del plugin con el broker, pero un paquete MAVLink antiguo que llegue físicamente durante una solicitud posterior no se distingue del valor solicitado. La prueba de pérdida filtró respuestas durante la ventana y confirmó el timeout.

Sin H743, FCU física, UART ni actuadores. No se activó autostart ni servicio permanente; se retiraron los directorios/archivos temporales del ensayo en WSL y Orange Pi tras guardar los logs. No se tocó red, SSH, GitHub ni el remoto. Orange Pi quedó sin procesos MAVROS/gateway/query y sin sockets UDP 14680/14681.

### Minimización del conjunto de plugins MAVROS — 2026-11-05

Se repitió la integración temporal con `plugin_allowlist=['sys_status','rra_readonly_version']`. MAVROS cargó solo `sys_status` (estado) y el plugin fijo del Companion. Su log confirmó `param`, `command`, `sys_time` y los demás plugins como `ignored`; en particular, el plugin estándar `param` no cargó y no se observó su descarga automática de los 1.253 parámetros. Estado, versión, BATT_MONITOR, timeout, reintento inmediato y reconexión pasaron igual. El valor de `plugin_allowlist` se pasó solo en el comando de prueba, no se guardó como configuración persistente. MAVROS documenta `plugin_allowlist` para cargar solo plugins coincidentes: https://github.com/mavlink/mavros/blob/ros2/docs/nodes.md#plugin-loading.

Corrección de alcance del contador de auditoría: los 233 servicios y 142 endpoints son nombres candidatos del inventario completo del MAVROS predeterminado que la app intentó crear y DDS denegó. Con el allowlist mínimo muchos plugins no se cargaron, así que esos números no representan interfaces activas en esta configuración recortada. Evidencia final (con el allowlist mínimo) en `evidencias/mavros-repeat-reconnect-boundary-2026-11-05/`.

## Repetición concurrente y respuesta MAVLink tardía — 2026-11-05 (repetición ampliada)

Se ejecutó el despliegue reproducible `scripts/deploy_companion_packages.ps1` desde Windows 11 hacia `rra@192.168.1.156`. Copió solo `rra_companion_readonly` y `rra_mavros_version_plugin` al workspace local `~/rra_ws/src`, compiló ambos con colcon y ejecutó la suite remota: 8/8 pruebas OK. El script no inicia nodos ni instala arranque automático.

Prueba SITL renovada bajo SROS2 Enforce, dominio 202 y UDP loopback, con MAVROS limitado a `sys_status` y `rra_readonly_version`: cuatro solicitudes simultáneas produjeron tres rechazos inmediatos (`already in progress`) y una expiración acotada; no hubo bloqueo del executor. Se filtró un `AUTOPILOT_VERSION` real de SITL, se retuvo y se reprodujo después del timeout mientras no había solicitud activa (`late_replayed=1`); la siguiente solicitud devolvió `[4,7,2]` y `fb773567`. Esta comprobación cubre replay tardío durante inactividad, no un paquete atrasado que aparezca durante una solicitud posterior.

Pasaron las tres lecturas de versión, `BATT_MONITOR=4`, caída/restauración del enlace, reconexión y detección de desconexión al parar SITL. SROS2 denegó 233/233 clientes candidatos de servicios MAVROS desde la app y 142 endpoints directos de tópicos; el broker no pudo crear clientes genéricos `ParamPull` ni `GetParameters`. Contadores del puente: 652 Pi→MAVROS, 54 MAVROS→Pi, 1 respuesta de versión retenida, 244 datagramas descartados durante la caída; SSH exit 0. Logs íntegros y resumen en `evidencias/mavros-concurrency-late-response-2026-11-05/`.

Los procesos de prueba, puertos UDP 14680/14681, keystore temporal y staging se limpiaron en la Orange Pi; el directorio temporal exacto de SITL se eliminó en WSL después de guardar el log. Sin H743, FCU física, UART, actuadores, cambios de red/SSH, GitHub o inicio automático.

## Revisión previa de UART MATEK/Orange Pi — 2026-11-05

Se cotejó la ficha H743-WLITE y el manual oficial Orange Pi Zero 2W. El fabricante asigna TX1/RX1 a USART1/TELEM2/SERIAL2; OPi coloca UART5_TX/RX en pines 11/13, GND en 14. Confirmación local por SSH: Ubuntu 26.04/kernel 6.18.60, `/dev/ttyS0`…`ttyS7`, `ttyS5` bajo `serial8250`, boot env con `overlay_prefix=sun50i-h616` pero sin overlay UART, sin alias `/dev/serial*`; esto no acredita pinmux activo en cabecera. No se cambió el arranque ni se reinició.

Se documentó el checklist previo en `UART_PRECONNECTION_CHECKLIST.md`. Hallazgos que corrigen supuestos del plan: (a) presencia de `/dev/ttyS5` no prueba el vínculo eléctrico con pines 11/13; (b) TX1 MATEK descrito como “5 V tolerant I/O” requiere verificar nivel de salida antes de conectarlo a Orange Pi; (c) cable solo TX de Matek a RX Orange Pi permite telemetría no solicitada, pero no las consultas de versión/BATT que transmite el Companion. La H743 sigue sin estar conectada y no se leyeron parámetros.

Próximo paso pendiente: identificar overlay y pinmux correcto para Armbian/kernel concreto en modo documental/solo lectura; obtener revisión física y exportación privada de parámetros desde GCS; verificar niveles eléctricos. No activar overlay, editar parámetros, cablear ni probar UART física hasta que se confirme el banco y la conexión.

Ampliación de investigación UART5 (solo lectura, 2026-11-05): DTB activo confirmado como `sun50i-h618-orangepi-zero2w.dtb`; en `/boot/armbianEnv.txt` se conserva `overlay_prefix=sun50i-h616`. El DTB tiene alias serial5, UART5 PH2/PH3 y existe overlay instalado `sun50i-h616-uart5.dtbo`, compatible H616/H618; candidato lógico `overlays=uart5`. No se activó ni reinició. Hay que validar el DT vivo y dispositivo de serie después de un cambio. La guía Armbian clasifica `armbianEnv.txt` como configuración crítica; siguiente paso operativo requiere respaldo y vía de recuperación SSH/consola preparada. Detalle en `UART_PRECONNECTION_CHECKLIST.md`.

## Diagnóstico de SSH y Wi-Fi al arranque — 2026-11-05

Con la clave desde Windows, TCP/22 conectó en 10 ms; tres sesiones SSH midieron 2,03 s (primera) y 1,21/1,22 s. La autenticación por clave fue aceptada inmediatamente. `ssh.socket` está habilitado/listening desde el boot; `ssh.service` está deshabilitado por separado pero se activa por socket, lo cual corresponde a activación bajo demanda. Arranque medido 14,352 s; socket alrededor de +6 s; wlan0/`network.target` alrededor de +7,4 s. No está activo `systemd-networkd-wait-online`. Actualmente `wlan0` tiene buen enlace (-38 dBm) y DHCP `192.168.1.156`; `eth0` está abajo. Por tanto el servicio SSH no parece ser el retraso actual; la causa probable de espera inicial es asociación Wi-Fi/DHCP o dirección dinámica, pero no se pudo probar históricamente: el usuario rra no puede leer journald/auth.log sin contraseña de sudo. Ningún cambio operativo.

Informe reproducible y recomendaciones en `SSH_DIAGNOSTIC_2026-11-05.md`. Una posible mejora sería reserva DHCP de la IP actual para MAC e4:33:89:2e:8d:ad; requiere cambio en router y no se realizó. No añadir dependencia estricta de network-online sin medir y acordar recuperación.

Corrección/ampliación del diagnóstico SSH (2026-11-05): lectura root de journal permitió fijar eventos. `ssh.socket` escucha en +12,1 s; Wi-Fi asocia en +20,1 s y DHCP asigna .156 en +22,3 s. `sshd` se activa bajo demanda en +981 s. Dos conexiones desde el portátil `.146` se cerraron por el cliente antes de autenticar; la tercera usó y aceptó la clave correcta. No hubo `Failed publickey`. Configuración efectiva: `UseDNS no`, GSSAPI desactivado y sin límites por origen. La hipótesis anterior de red/DHCP no explica esas desconexiones tardías; solo aplica si el intento ocurre dentro de los ~22 s iniciales. Para identificar la fase exacta falta el `ssh -vvv` del primer error de Codex Remote. Ver cronología completa en `SSH_DIAGNOSTIC_2026-11-05.md`.

## UART5 de Orange Pi activado — 2026-11-05

Con autorización del usuario se añadió solo `overlays=uart5` a `/boot/armbianEnv.txt` y se reinició. Antes de editar se conservó copia root-owned en la Pi y una copia local; hash original `a28921daf696c1fe31a5f8d4b4b5c3200125f9a3f1b2757499203ae797916df6`; hash posterior `00844d964c125d0e507516e559f2110010942af3cf2000c02a209aee4ca7c45f`. La Pi volvió al mismo host/IP, SSH activo, ROS Lyrical, cero unidades fallidas.

El DT vivo confirma `serial@5001400` habilitado y PH2/PH3 asignados a UART5; Linux expuso `/dev/ttyS5` (root:dialout, rra pertenece al grupo). Sin getty ni proceso tras la prueba. MAVROS 2.16 abrió `serial:///dev/ttyS5:57600` temporalmente y cargó únicamente los plugins autorizados por allowlist; dominio 204/discovery localhost, no SROS2 Enforce. Se contaron 84 bytes TX y 0 RX, pero ninguna FCU/cable estaba conectado. El baud 57600 fue solo de prueba, no se asumió como SERIAL2_BAUD real.

Se conservaron logs completos y errores corregidos en `evidencias/uart5-overlay-2026-11-05/`. Nodos temporales parados, tty libre, archivos temporales remotos retirados. No se modificaron claves, red/SSH, parámetros MATEK, servicios, autostart, GitHub ni actuadores.

Siguiente paso: leer firmware/revisión y parámetros actuales de SERIAL2 desde el GCS conectado a MATEK; confirmar voltaje TX1 vs tolerancia Orange Pi; después preparar el banco y enlazar/validar telemetría y consultas con retorno solo bajo SROS2 Enforce. La MATEK sigue físicamente desconectada.

## Pausa solicitada — 2026-11-05

El usuario no tiene ahora la MATEK H743-WLITE disponible para conectarla a Mission Planner; detiene el desarrollo temporalmente. No seguir con conexión física, lectura de parámetros SERIAL2 ni pruebas con la H743 hasta que el usuario reanude y la placa esté disponible.

Estado guardado: overlay `overlays=uart5` activo en la Orange Pi; `/dev/ttyS5` y pinmux PH2/PH3 comprobados, MAVROS abrió el dispositivo en un smoke test sin FCU. La tasa 57600 fue únicamente de prueba; baud/protocolo reales de SERIAL2 siguen desconocidos. Evidencias, respaldo y limitaciones en `evidencias/uart5-overlay-2026-11-05/`, `UART_PRECONNECTION_CHECKLIST.md` y `COMPANION_MANUAL_DEPLOYMENT.md`.

Al reanudar: conectar la H743 a Mission Planner por el medio disponible (por ejemplo DroneBridge ESP32), leer firmware/revisión y parámetros actuales de `SERIAL2` sin escribir; verificar nivel lógico de TX1; luego acordar el enlace bidireccional Matek↔OrangePi bajo el perfil SROS2 Enforce antes de cablear o iniciar MAVROS en hardware. No se creó autostart ni se conectó la H743 en esta sesión. No commit, push ni cambios a GitHub.

## Brief para revisión crítica externa — 2026-11-05

Se creó `codex_handoff/REVISION_CRITICA_EXTERNA_RRA.md` para que otro chatbot revise de forma independiente el diseño del Companion. Resume hechos SITL y UART, límites no validados en la H743, riesgos de confianza, la pausa vigente y preguntas concretas para obtener recomendaciones priorizadas. No incluye credenciales ni datos domésticos sensibles. Es un artefacto documental: no se modificó código, Orange Pi, configuración física ni GitHub.

## Fase de auditoría crítica, consultas MAVLink y telemetría ROS 2 — 2026-11-05

**Hallazgo/corrección principal:** la reproducción SITL detectó que una respuesta `PARAM_VALUE` de la consulta anterior, retenida hasta que empieza una consulta nueva, podía marcarse erróneamente como éxito de la nueva. El protocolo no tiene transaction ID. Plugin y broker ahora validan msgid/source system-component/nombre/tipo/rango, límites de concurrencia y deadline común; una respuesta candidata de `BATT_MONITOR` queda `success=false`, `ambiguous_no_mavlink_transaction_id`. Se acepta `param_index=65535` como sentinel MAVLink válido. Resultado SITL corregido, con retraso, pérdida y duplicación: `evidencias/param-value-overlap-2026-11-05/corrected/resultado.txt`. No se afirma correlación infalible.

**Límite de seguridad:** la política SROS2 filtra acceso DDS de otras identidades, no frames MAVLink; `rra` puede abrir `/dev/ttyS5` RW por `dialout`; MAVROS/plugin autorizados pueden transmitir y siguen en la base de confianza. El enlace no es físicamente de solo lectura. Ver auditoría `PHASE_REVIEW_SECURITY_AND_ROS2_2026-11-05.md` y corrección en `MAVROS_READONLY_BOUNDARY.md`.

**ROS 2:** `rra_telemetry` ampliado con edad monotónica local y declaración `edad_muestra_verificada=no`, fuente sintética bajo `/rra/sim/fcu/*` y contrato candidato basado en `sensor_msgs`/`diagnostic_msgs`. `mavros_msgs/State` queda adaptador específico; los nombres/QoS están propuestos, pendientes de coordinación con Martín. Smoke rosbag2: cinco topics, 81 mensajes/8.5 s en primera demo; benchmark conjunto: 206 mensajes/22.5 s. Contrato: `RRA_ROS2_INTERFACES.md`.

**Rendimiento corto (Orange Pi, 2026-11-05):** carga local ROS2 + MAVROS UDP loopback sin FCU + simulador/observador + rosbag: CPU ocupado 15.5% vs 0.0% reposo, MemAvailable 3627→3335 MiB, swap usado 0, temperaturas ~52.1–53.0→53.8–55.3 °C, RSS sumado ~300 MiB con páginas compartidas, latencia simulada local p50 2.158 ms / p95 3.078 ms / max 3.970 ms (n=20). Rootfs: 55 GiB libres. Muestra de 2 s, no una prueba térmica ni FCU sostenidos. Evidencia y límites en `evidencias/rra-ros2-benchmark-2026-11-05/MEDICION.md`.

**Validación de código:** 13/13 unitarias del broker, 9/9 de telemetría, compilación colcon de `rra_telemetry`, smoke de nodos/diagnósticos y rosbag2. Integración SITL de retardo/loss/duplicación pasó con 773 datagramas Pi→MAVROS, 59 de retorno, dos peticiones BATT, replay y duplicado observados. Sin H743 física, UART MAVLink, datos reales ni parámetros FCU. La primera demo detectó además que `Node.publishers` es propiedad de solo lectura en rclpy; simulador corregido para usar `self.pubs`.

**Placa:** modelo comunicado MATEK H743-WLITE; discrepancia aclarada frente a H743-WING V3. La familia comparte guía/targets, no pinout. Ver sección añadida a `UART_PRECONNECTION_CHECKLIST.md`; no se cambió placa ni ArduRover.

Orange Pi quedó sin MAVROS, simulador, observador, rosbag ni sockets del ensayo. Temporales remotos y scratch WSL de SITL retirados después de guardar logs/resúmenes localmente. Sin cambios de GitHub, commits, push, sincronización, repositorio de Martín, autostart, red o parámetros FCU.

### Próximo hito recomendado

Mantener pausada la validación física hasta disponer de la H743. Antes de eso, acordar con Martín el contrato ROS (nombres, frames, QoS y semántica) y conservar el simulador como fixture de integración. Cuando haya H743, identificar modelo/revisión y leer valores SERIALx desde GCS sin escribir; verificar niveles eléctricos y realizar recepción UART aislada. La lectura BATT por MAVLink sigue ambigua sin mitigación adicional; definirla y revisar el retorno antes de habilitar consultas físicas.

## Hito 1 — telemetría y bag SITL completados (2026-11-05)

Paquete `rra_telemetry` validado desde `/mavros/state`, GNSS, IMU, batería,
`/mavros/global_position/local` (`nav_msgs/Odometry`) y
`/mavros/global_position/compass_hdg` (`std_msgs/Float64`). El observador mantiene
un `DiagnosticArray` por fuente y latido de proceso. `telemetry_simulator` queda
separado bajo `/rra/sim/fcu/*`, configurable, estacionario por defecto y sin
publicar comandos.

En Orange Pi: `colcon build --packages-select rra_telemetry` y 11/11 unit tests
OK; smoke simulator→observer, siete estados diagnósticos OK. ArduRover SITL 4.7.2
emitió 1,249 datagramas en el bridge de prueba, MAVROS recibió todos los datos,
rosbag registró siete topics (369 mensajes/61.09 s) y pérdida de conexión quedó
en el bag. `verify_bag.py` reprodujo a 4x y comprobó State, GPS, IMU, batería,
odometría, rumbo y diagnósticos: `REPLAY_OK`. Grabación local en
`evidencias/sitl-telemetry-demo-2026-11-05/`; DB3 SHA-256
`951320a142f762c2583b4c254346e9ae07aeb1067b987c0c387a0b79ca3e16cc`.

Este primer bag es datos SITL, no datos de H743. El bridge es unidireccional
hacia MAVROS; no hay UART, H743, actuadores ni parámetros FCU. MAVROS genera
solicitudes hacia su endpoint loopback, que el bridge no reenvía. Test cerrado;
no procesos de MAVROS/observer/rosbag restantes, temporales exactos limpiados en
Pi y WSL.

Contrato principal: `CONTRATO_INTEGRACION_COMPANION.md`; componentes clasificados
en `CLASIFICACION_COMPONENTES_COMPANION.md`; plan breve de máximo cinco hitos en
`PLAN_DESARROLLO_CORTO.md`. Interfaces de rumbo/odometría siguen pendientes de
acuerdo con Martín, especialmente la semántica del `Float64` de rumbo.

**Siguiente hito recomendado:** preparar ejecución portable mediante launch y
configuración fuera del código; comprobar qué entorno x86_64/ROS puede usar
Martín antes de hacer instalaciones. H743 sigue en espera; no cambiar parámetros
ni conectar UART automáticamente.

## Hito 2 — ejecución portable en Orange Pi (2026-11-05)

`rra_telemetry` instala launch, YAML y un grabador con lista fija de siete
tópicos, límite máximo de 1–300 s y cierre SIGINT de rosbag2. `source:=sim`
arranca solamente el simulador y el observador remapeado; `source:=mavros`
arranca solo el observador y presupone MAVROS ya activo. Parámetros se pueden
sustituir por argumentos launch; no hay rutas de usuario ni configuración UART
embebidas. Código y prueba: `codex_handoff/rra_telemetry/`.

Orange Pi/ROS 2 Lyrical ARM64: `colcon build --packages-select rra_telemetry`
correcto; 11/11 unit tests; integración portable PASS. El smoke sim grabó un
MCAP local temporal de 73.5 KiB, 45 mensajes y los siete tópicos, duración
efectiva 3.005 s frente al límite solicitado de 8 s por el tiempo de arranque y
descubrimiento. El modo MAVROS inició el observador sin iniciar MAVROS/FCU.
El primer ensayo reveló que `timeout` mataba rosbag2 (137); sustituido por un
controlador local que envía SIGINT y exige finalización/metadata. Bash `-n`
correcto. La prueba eliminó su carpeta temporal; no quedan procesos ROS RRA.
No se guardaron datos sintéticos nuevos. Evidencia:
`evidencias/hito2-portable-execution-2026-11-05/RESULTADO.md`.

No hay validación x86_64: WSL Ubuntu 22.04 presente no tiene ROS 2 instalado,
y no se instaló nada. Acordar con Martín su distro/entorno antes de afirmar
portabilidad probada allí. Hito 3 sigue pendiente de disponibilidad de H743;
ningún cableado, parámetro FCU o actuador fue tocado en esta fase.

## MATEK accesible desde Mission Planner — 2026-11-07

El usuario informa que H743-WLITE está conectada a Mission Planner por TCP a
través de DroneBridge. La Orange Pi aún no se ha conectado a la controladora.
En esa fecha no se habían leído todavía los parámetros. Las capturas aportadas
después quedan registradas en la sección siguiente. La revisión física aún no se
ha confirmado; no hay enlace Orange Pi↔FCU ni parámetros escritos por esta sesión.

## Lectura de parámetros TELEM2 desde capturas GCS — 2026-11-07

Capturas aportadas por el usuario de Mission Planner 1.3.83, ArduRover V4.7.2
(build visible `fb773567`), target `MatekH743`. Se leen `SERIAL2_PROTOCOL=2`,
`SERIAL2_BAUD=57`, `SERIAL2_OPTIONS=0`; las tres celdas Value coinciden con el
default mostrado. Según la tabla oficial, para H743 TELEM2/SERIAL2 es USART1,
protocolo 2 corresponde a MAVLink2 y baud 57 a 57600. `SERIAL2_OPTIONS=0` no
activa inversión, half-duplex ni swap.

La segunda captura muestra `BRD_ALT_CONFIG=0` y `BRD_SER1_RTSCTS=2`. El último
es SERIAL1/TELEM1/UART7, donde la placa documenta CTS/RTS; no describe el flujo
de SERIAL2/TELEM2. No modificarlo. No se obtuvo volcado completo de parámetros,
no se leyeron tasas MAVLink ni firma, y la revisión física del PCB y el
nivel lógico de TX1 siguen sin verificar. La Orange Pi no está conectada a la
H743. No se hizo ninguna escritura desde esta sesión. Referencias y limitaciones:
`UART_PRECONNECTION_CHECKLIST.md` y `H743_DATOS_HARDWARE.md`.

Siguiente paso: guardar una copia local del archivo de parámetros si el usuario
quiere completar el inventario; leer sin modificar `SERIAL0_PROTOCOL` y
`SERIAL1_PROTOCOL` para asignar el índice de las tasas `MAVn_*` de TELEM2;
confirmar por foto la revisión/serigrafía y resolver el nivel eléctrico TX1↔Orange
Pi antes de planear cableado.

**Corrección de nomenclatura (ArduPilot 4.7):** las antiguas tasas `SR0_*`…
`SR9_*` se renombraron `MAV1_*`…`MAV10_*`. El canal `MAVn` se asigna según el
orden de puertos configurados con protocolo MAVLink; el `SR2_*` legado se
renombra `MAV3_*`, pero para asociarlo a TELEM2 hay que confirmar también
`SERIAL0_PROTOCOL` y `SERIAL1_PROTOCOL`. `SERIAL2_PROTOCOL=2` ya está leído.


## Tasas MAVLink MAV3 observadas — 2026-11-07

Captura adicional de Mission Planner (ArduRover 4.7.2) muestra `MAV3_ADSB=0`, `MAV3_EXTRA1/2/3=1 Hz`, `MAV3_EXT_STAT=1 Hz`, `MAV3_OPTIONS=0`, `MAV3_PARAMS=10 Hz`, `MAV3_POSITION=1 Hz`, `MAV3_RAW_CTRL=1 Hz`, `MAV3_RAW_SENS=1 Hz` y `MAV3_RC_CHAN=1 Hz`; los valores coinciden con los defaults visibles. Ya se habían observado `SERIAL0_PROTOCOL=2`, `SERIAL1_PROTOCOL=2` y `SERIAL2_PROTOCOL=2` (MAVLink2), así como `SERIAL2_BAUD=57` (57600) y `SERIAL2_OPTIONS=0`. MAV3 corresponde al antiguo SR2 según la renumeración de ArduPilot 4.7. El índice es coherente con el tercer puerto MAVLink, TELEM2/SERIAL2, pero la emisión por ese conector aún no se ha medido.

No se escribió ningún parámetro. No existe aún conexión Orange Pi↔H743 ni prueba eléctrica. Próximo paso físico-documental: obtener fotos legibles de identificación/revisión exacta de PCB y verificar el nivel de TX1 antes de cablear. Luego, si es compatible y el banco está inmovilizado, prueba UART de solo recepción TX1→pin 13/UART5_RX y GND→pin 14; dejar ambos TX sin conectar.

## Fotos físicas de la MATEK — 2026-11-07

La foto de la FCU instalada muestra una Matek H743; su serigrafía parece indicar H743-WLITE, aunque los cables y el enfoque impiden leer modelo/revisión con certeza. Las imágenes adicionales son capturas de producto y no prueban la revisión del ejemplar instalado. No se puede mapear desde las fotos qué cable actual ocupa cada pin, por lo que no se desconectó ni recomendó retirar ninguno.

El manual oficial identifica TX1/RX1 como USART1/TELEM2/SERIAL2 y califica I/O como tolerante a 5 V. Esa indicación no basta para conocer el nivel de salida TX1 ni la tolerancia del RX de Orange Pi; falta comprobar compatibilidad antes de cablear. No se añadió cable entre placas ni se midió voltaje. Próxima tarea física: foto macro legible de serigrafía/revisión de la FCU y determinación del nivel TX1; luego, solo si es compatible, prueba de banco unidireccional según `UART_PRECONNECTION_CHECKLIST.md`.

## Medición TX1 y siguiente acción — 2026-11-07

El usuario informa que, midiendo GND–TX1 con multímetro, la lectura oscila aproximadamente entre 2,9 y 3,3 V. Es indicativa de nivel cercano a 3,3 V bajo tráfico, aunque no captura picos ni constituye caracterización de laboratorio. Se decidió avanzar a una prueba funcional limitada de recepción sin retorno, sin añadir level shifter de inicio. Cableado: TX1→pin 13 UART5_RX y GND→pin 14; no unir 5V/VCC y dejar Matek RX1 y Orange Pi pin 11 UART5_TX desconectados. Hacer conexiones con placas apagadas y luego alimentarlas con sus fuentes habituales. Aún no se ha conectado; pendiente confirmación del usuario.

## Primer intento tras conexión UART RX — 2026-11-07

El usuario indica que realizó la conexión física unidireccional propuesta. Desde el portátil se intentó SSH con la clave `~/.ssh/rra_orangepi_ed25519` a `rra@192.168.1.156` (BatchMode, ConnectTimeout=8): timeout. Ping a esa IP perdió 2/2 paquetes y no hay entrada ARP. El portátil tiene IPv4 `192.168.2.2/24` (gateway `192.168.2.1`) además de una interfaz `10.30.203.91`; no tiene dirección ni ruta `192.168.1.0/24`. Por tanto no se pudo comprobar SSH ni abrir ttyS5, y no hay resultado de telemetría UART todavía. No se cambiaron configuraciones ni se transmitió por UART.

Siguiente paso: identificar la IP actual de Orange Pi en el router/red a la que está conectada, o conectar el portátil a la misma LAN, y volver a probar SSH con clave. Después hacer una escucha serial corta en ttyS5 a 57600 con TX local desconectado y registrar bytes/heartbeat.

## Orange Pi fuera de la LAN doméstica — alternativa de acceso — 2026-11-07

El usuario aclara que la Orange Pi está fuera de casa y sin acceso a su router Wi-Fi; por eso el intento de SSH a `192.168.1.156` no podía funcionar y no debe interpretarse como fallo de la Pi ni del UART. No cambiar la configuración de red/SSH de la Pi para esta prueba. Opción sencilla: habilitar hotspot del teléfono usando temporalmente el mismo SSID y contraseña de la Wi-Fi doméstica que la Orange Pi ya tiene guardados (si la configuración del teléfono lo permite), preferiblemente banda 2,4 GHz/WPA2; la Orange Pi se asociaría como si estuviera en su red conocida. Conectar también el portátil al hotspot y obtener la IP DHCP de la Pi desde la lista de clientes; luego probar SSH por clave. La comunicación cliente-a-cliente del hotspot debe estar permitida. Si esto no resulta, usar consola local/monitor/teclado para configurar temporalmente una red o revisar un adaptador USB-Ethernet; no cambiar parámetros de FCU.

La prueba UART queda pendiente; cableado reportado RX-only permanece. Todavía no hubo acceso remoto, escucha serial ni evidencia de heartbeat.

## Alternativa para configurar red fuera de casa — consola local — 2026-11-07

El usuario no recuerda la clave Wi-Fi doméstica y la Orange Pi está fuera de la LAN. Alternativa de acceso independiente de la red: consola UART0 de la Orange Pi mediante adaptador USB–TTL de 3,3 V; el manual oficial mapea pin físico 8=UART0_TX, 9=GND y 10=UART0_RX. Conexión cruzada adaptador RX→pin 8, adaptador TX→pin 10, GND→pin 9; no conectar VCC. UART0 es independiente del UART5 en pines 11/13 usado para H743. Terminal prevista 115200 8N1 según `console=ttyS0,115200` observado previamente, sujeto a validar prompt de consola. Ya en consola se puede configurar la Wi-Fi/hotspot disponible localmente y luego regresar a SSH. No se ha realizado este cableado ni se ha modificado red.

Un cable USB-C directo PC↔Orange Pi no garantiza consola ni SSH: USB0 puede actuar como device según el manual, pero el modo/gadget necesario depende de la imagen instalada; Armbian actual no ha sido probado para esta función. Otra alternativa es monitor mini-HDMI y teclado/USB host si hay adaptador disponible. Fuente pinout/USB: https://orangepi.net/wp-content/uploads/2023/10/OrangePi_Zero2w_H618_User-Manual_v1.1.pdf

## Búsqueda de nueva IP tras configurar Wi-Fi — 2026-11-07

El usuario informa que la Orange Pi ya está conectada por Wi-Fi, pero la IP no se conoce. Se comprobó `orangepizero2w.local` y se buscaron hosts SSH en las subredes locales enumeradas; sin resultado. Diagnóstico de `netsh wlan show interfaces`: interfaz Wi-Fi del portátil está **desconectada** (aunque retenga una dirección anterior en el inventario de IP), y la interfaz activa Ethernet 3 es 10.30.203.91/24. No hay aún evidencia de que el portátil y la Orange Pi compartan LAN. No se pudo determinar ni probar la IP de la Pi.

Siguiente paso: conectar el Wi-Fi del portátil a la misma red/hotspot al que se conectó Orange Pi. Después volver a consultar la lista ARP/vecinos, resolver mDNS y probar SSH por clave. Si el usuario no puede conectar el portátil a esa red, obtener la dirección DHCP de Orange Pi desde la lista de clientes del punto de acceso o desde consola local `hostname -I`.

## Orange Pi confirmada en hotspot del teléfono — 2026-11-07

La captura del teléfono muestra al cliente `orangepizero2w`, MAC `e4:33:89:2e:8d:ad`, conectado al hotspot. La MAC coincide con la Orange Pi vista anteriormente en la lista DHCP del router doméstico. La pantalla no muestra IP. La interfaz Wi-Fi del portátil sigue reportada desconectada en la última comprobación, así que todavía no se puede descubrir/SSH a la Pi desde este entorno. Próximo paso: conectar manualmente el portátil al mismo hotspot y escanear vecinos/SSH, o consultar detalles DHCP en el teléfono si muestra la IP.

## SSH restablecido y primera escucha UART física — 2026-11-07

El portátil se conectó a la Wi-Fi/hotspot `DIGIFIBRA-PyHA` (10.221.18.142/24). Un barrido local encontró MAC `e4:33:89:2e:8d:ad` en `10.221.18.8`, que responde por SSH; el nombre del host es `orangepizero2w`, usuario `rra`, sistema confirma `/dev/ttyS5` root:dialout y membresía de `rra` en dialout. La clave de host presentada coincide con la clave ed25519 ya registrada para la antigua IP 192.168.1.156 (fingerprint observado `SHA256:hiOntbIYlxJIOwf0FBNQl9HuotVuqms5TFyogqbFxwI`); se usó HostKeyAlias para verificar, sin desactivar la comprobación ni modificar known_hosts.

Se configuró localmente ttyS5 a 57600, raw, sin eco/control de flujo y se hizo lectura pasiva de seis segundos: `timeout 6s cat /dev/ttyS5 | wc -c` → **0 bytes**. `stty` confirmó 57600 8N1, `crtscts` apagado; no había proceso MAVROS/ros2 ocupando el dispositivo antes de la lectura. La lectura no transmite desde la Orange Pi. Esto demuestra que el dispositivo abre, no que el cableado o emisión de FCU funcione. No se cambió ningún parámetro de ArduPilot y no hubo comandos de control.

Próximo paso: con H743 alimentada, comprobar visualmente que Matek TX1 va a Orange Pi pin físico 13 (UART5_RX), GND a pin 14 y no se ha conectado retorno TX; repetir lectura pasiva durante 15 s. Si sigue a cero, aislar si la FCU emite por TELEM2 mediante captura/osciloscopio o revisar el baud/configuración efectiva desde GCS antes de tocar parámetros.

Repetición tras SSH: segunda escucha pasiva de 15 s a ttyS5 57600 raw devolvió también 0 bytes. No se observa recepción; sigue sin transmisión desde Orange Pi.

El usuario confirma que la conexión física sigue hecha. Tercera escucha RX pasiva de 15 s a 57600 en `/dev/ttyS5`: 0 bytes. La Orange Pi mantiene SSH en 10.221.18.8. Siguiente prueba de diagnóstico: medir con multímetro en el extremo Orange Pi entre pin físico 13 (UART5_RX, ya conectado a TX1) y pin14/GND mientras la H743 está encendida; comparar con el nivel aproximado 2,9–3,3 V que el usuario había visto en TX1. Esto permite distinguir llegada eléctrica al pin de un problema de UART/baud. No transmitir ni modificar parámetros FCU.

## Recepción MAVLink2 real en TELEM2 — 2026-11-07

Tras la petición del usuario se repitió escucha pasiva en `/dev/ttyS5` a 57600 durante 15 s: se recibieron **10.692 bytes**. Muestra inicial: `fd 09 00 00 f8 01 01 00 00 00 04 00 00 00 0a 03 01 05 03 b3 08`. Se valida como frame MAVLink2 válido: magic FD, msgid 0 HEARTBEAT, sysid 1, compid 1; payload indica MAV_TYPE_GROUND_ROVER (10), MAV_AUTOPILOT_ARDUPILOTMEGA (3), estado ACTIVE (5), versión MAVLink 3; CRC X.25 incluyendo extra 50 coincide con 0x08B3. Esto confirma que el cableado de recepción Orange Pi UART5 está entregando telemetría válida desde la H743/ArduRover. La FCU no recibió transmisión de vuelta: listener abierto solo lectura (`cat`), retorno físico RX1 desconectado. No se modificó parámetro alguno.

Siguiente hito: iniciar MAVROS de forma controlada con la URL serial 57600 y el perfil de plugins de observación existente, comprobar `/mavros/state` y telemetría básica ROS; mantener el retorno físico desconectado durante esa validación.

## MAVROS y observador RRA con telemetría real — 2026-11-07

Prueba temporal en Orange Pi, ROS 2 Lyrical, `ROS_DOMAIN_ID=205` y `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`. MAVROS abrió `serial:///dev/ttyS5:57600`; allowlist de plugins `sys_status`, `global_position`, `imu`, `local_position`. Log: `CON: Got HEARTBEAT, connected. FCU: ArduPilot`. `rra_telemetry` se lanzó con `source:=mavros` y publicó `/rra/telemetry/diagnostics`. Todos los estados publicados en esa muestra fueron nivel OK: conexión (modo HOLD, armado false, connected true, edad ~0,86 s), GPS disponible, IMU/orientación disponible, batería disponible (≈11,59 V, ≈95%), velocidad disponible (0 m/s) y rumbo disponible (≈13,7°). No se conserva la coordenada GNSS exacta en esta documentación. El campo del observador aclara `edad_muestra_verificada=no`; son edades de recepción del nodo, no validación de frescura de la medición en el sensor.

El FCU envió el texto `PreArm: Radio failsafe on`; no se cambió ningún failsafe ni se armó/movió el vehículo. MAVROS intentó solicitar AUTOPILOT_VERSION y agotó reintentos/timeout debido a que el retorno UART está físicamente desconectado; no interpretar esto como que el firmware carezca de soporte. Esta prueba no usó SROS2: dominio aislado y descubrimiento localhost para smoke test, sin afirmar seguridad DDS autenticada. Los plugins de control/params/global_position command no estaban en allowlist, pero MAVROS aún puede transmitir desde su TX local; el cable hacia Matek RX1 permaneció desconectado según configuración del ensayo.

Se cerraron MAVROS y `state_observer`; comprobación `ps -C state_observer -C mavros_node -C mavros_router` sin procesos. No se modificó FCU, red persistente ni autostart. Resultado: UART RX real, conversión a estado/batería/GPS/IMU/velocidad/rumbo ROS y diagnóstico unificado funcionales.

Próximo paso: ajustar la prueba para eliminar el timeout/reintentos de versión en escenario RX-only o documentar que es esperado; después repetir con rosbag2 corto y verificar reproducción del bag real, manteniendo el retorno desconectado.

## Rosbag de telemetría real y replay — 2026-11-07

Se grabó localmente en la Orange Pi, en `~/rra_ws/recordings/rra-h743-uart-rx-20261107-154256`, mediante `scripts/record_telemetry.sh` con fuente MAVROS y lista fija. MCAP 80,4 KiB; duración efectiva 6,88 s; 58 mensajes, siete topics: estado (16), batería/GPS/IMU/odometría/rumbo y diagnóstico (7 cada uno). La duración fue inferior a los 10 s solicitados por arranque/suscripción; suficiente para un smoke de cada topic. La bolsa puede contener coordenadas GNSS exactas y permanece en almacenamiento privado de la Orange Pi, fuera de Git/documentación compartida.

Replay en `ROS_DOMAIN_ID=206`/LOCALHOST PASS: `mavros_msgs/State` reproducido con connected=true, armed=false, HOLD; `/rra/telemetry/diagnostics` reprodujo conexión y estados disponibles de GPS, IMU, batería, velocidad y heading. Se detuvo el player antes del fin tras recibir las muestras objetivo; no quedan procesos ROS/rosbag activos.

**Incidencia:** durante un ensayo de MAVROS con cuatro plugins y al terminar captura, Bash reportó una terminación por segmentation fault tras SIGINT. El log muestra señal SIGINT y executor terminado; no hay proceso activo ni core dump localizado. Es una ocurrencia única pendiente de reproducir/aislar; no atribuirlo aún al plugin ni declarar cierre siempre limpio. Un ensayo anterior de MAVROS con `sys_status` terminó sin este reporte. En ambos casos retorno UART abierto y sin comandos FCU.

## Reproducción de cierre MAVROS — 2026-11-07

Se repitió el arranque/cierre controlado en UART real con dos allowlists, `sys_status` y `sys_status,global_position,imu,local_position`, ROS_DOMAIN_ID=205/LOCALHOST y FCU conectada solo en RX. Ambos procesos detectaron heartbeat ArduPilot, recibieron SIGINT y terminaron con `wait EXIT=0`; el segmentation fault visto al cerrar la captura anterior no se reprodujo. No se deja una incidencia de crash confirmada, sino una anomalía aislada pendiente de vigilar. No se generaron cores. `PreArm: Radio failsafe on` tampoco volvió a aparecer en estas ventanas cortas; eso no confirma que el failsafe haya desaparecido ni reemplaza la advertencia de la sesión previa.

MAVROS sigue mostrando timeouts de versión cuando inicia sin retorno; la telemetría básica funciona. No se modificaron parámetros ni se conectó el pin de transmisión del Companion.

## Reorientación inmediata: retorno MAVLink y alimentación desde H743 — 2026-11-07

El usuario solicita acelerar retorno y alimentación y aclara que la batería 2S del motor está conectada pero su interruptor limita la propulsión; acepta que, en un incidente, el servo de dirección podría moverse. Priorizar los ensayos de lectura MAVLink y alimentación integrada; no añadir revisiones de seguridad redundantes ni iniciar armado/consignas de movimiento.

**Retorno:** cable previsto Orange Pi UART5_TX, pin físico 11 → MATEK RX1/TELEM2; ya existe MATEK TX1→Orange Pi UART5_RX pin13 y GND común. Con protocolo/baud ya observados (MAVLink2, 57600), habilitar el retorno permitirá probar las consultas fijas existentes AUTOPILOT_VERSION y BATT_MONITOR mediante `rra_mavros_version_plugin`; no usar escritura de parámetros ni mensajes de control en este ensayo.

**Alimentación:** Matek H743-WLITE especifica BEC Vx seleccionable 5/6/7,2 V, 8 A continuos/10 A pico; BEC 5V general 2 A continuos/3 A máx. Orange Pi Zero 2W especifica alimentación 5 V/2 A y admite alimentar por su cabezal de 40 pines. Candidato preferente para Pi: Vx configurado/medido a 5 V, en lugar del BEC general compartido. Antes de cablear, lectura única de Vx-GND con la Matek alimentada. Si da 5 V, usar Vx→Orange Pi pin 2 o 4 (5V) y GND→pin6 (GND) con cable de potencia dedicado; apagar Orange Pi y retirar su USB-C antes de alimentar por los pines para no paralelar dos fuentes. No usar Vx si mide 6/7,2 V ni pad 4V5 (solo 500mA). Si Vx no está a 5 V, alternativa es convertidor 5V/3A o cambiar jumper de Vx conforme al manual considerando el servo.

Fuentes primarias: ficha MATEK https://www.mateksys.com/?portfolio=h743-wlite; manual Orange Pi, 5V por cabezal y pinout https://orangepi.net/wp-content/uploads/2023/10/OrangePi_Zero2w_H618_User-Manual_v1.1.pdf . Aún no se ha conectado retorno ni alimentación a la Pi.

## Orange Pi alimentada desde Vx de MATEK — 2026-11-07

El usuario informa que midió Vx=5,1 V y conectó Vx/GND a los pines de alimentación 5V/GND de Orange Pi; comunica que la Pi arranca y funciona desde la Matek. Confirmación remota después del cambio: `orangepizero2w` responde por SSH en 10.221.18.8, `/dev/ttyS5` sigue disponible y una lectura pasiva de 5 s recibió 3.591 bytes a 57600. Uptime observado ~1 min y boot_id estable entre las comprobaciones; no se aprecia reinicio durante la lectura. La UART TX1→RX5 continúa entregando telemetría. Prueba funcional breve con carga normal, no ensayo de consumo pico con movimiento de servo.

El usuario no dijo explícitamente si retiró USB-C externo al pasar a Vx; confirmar que solo quede una fuente conectada (la recomendación fue retirar USB-C al alimentar por 5V GPIO). Retorno UART de Orange Pi pin11→Matek RX1 sigue pendiente según último estado informado.

## Retorno UART físico conectado y probado — 2026-11-07

El usuario conectó el retorno UART5_TX de Orange Pi (pin físico 11) a RX1/TELEM2 de Matek; se mantuvieron la recepción TX1→UART5_RX (pin 13), baud 57600 y masa común. Con MAVROS temporal en el perfil mínimo `sys_status,rra_readonly_version`, la consulta fija `request_batt_monitor` obtuvo respuesta en 54 ms: `PARAM_VALUE` de sysid/compid 1/1, nombre `BATT_MONITOR`, tipo MAVLink 2 y valor entero 4. Esto confirma el camino de transmisión Orange Pi→FCU y el retorno FCU→Orange Pi para una consulta MAVLink. El resultado lleva `correlation_status=ambiguous_no_mavlink_transaction_id`: identifica una respuesta compatible, no prueba de forma infalible que esa trama concreta pertenezca a la solicitud recién emitida.

La consulta fija `request_autopilot_version` fue aceptada localmente, pero no se observó publicación en `/mavros/readonly_version/autopilot_version`; MAVROS agotó su solicitud de AUTOPILOT_VERSION y usó capacidades predeterminadas. El comando implementado (MAV_CMD_REQUEST_MESSAGE 512, param1=148) coincide con la especificación MAVLink y el procedimiento documentado por ArduPilot; por tanto no se cambia el código a ciegas. La versión ArduRover 4.7.2 (`fb773567`) sí se vio antes en Mission Planner, evidencia independiente de esta consulta.

Prueba sin cambios de parámetros, armado, modo ni consignas de movimiento. Se conserva la advertencia observada anteriormente `PreArm: Radio failsafe on`; no se intervino. No se usó SROS2. La solicitud BATT_MONITOR fue una lectura fija; no se abrió acceso genérico a comandos o escritura. Se detuvo el ensayo temporal de MAVROS al terminar.

**Siguiente paso práctico:** mantener el cableado como está y usar la telemetría ROS estándar más el diagnóstico/rosbag físico ya preparados. Investigar AUTOPILOT_VERSION por separado con captura de respuesta/ACK cuando resulte útil; no bloquea la integración de telemetría. No hace falta conectar nada más para continuar.

## Sesión física bidireccional: observador y rosbag — 2026-11-07

Orange Pi conectada por SSH (`orangepizero2w`, `/dev/ttyS5`, ROS 2 Lyrical). Arranque MAVROS corregido tras una primera línea de comando inválida (falló antes de abrir el UART, sin transmisión). En el arranque válido se aplicó perfil temporal de allowlist `sys_status`, `global_position`, `imu`, `local_position`, `rra_readonly_version`; los plugins `command` y `param` quedaron ignorados. Dominio ROS 205 y descubrimiento LOCALHOST. Se arrancó `rra_telemetry` con fuente MAVROS y se grabó en la propia Pi: `~/rra_ws/recordings/rra-h743-uart-duplex-20261107-1626`, MCAP 77,8 KiB, 62 mensajes, 7 tópicos (State 18; batería, rumbo, GPS, odometría local e IMU 8 cada uno; diagnósticos 4), 7,96 s efectivos. La sesión capturó datos físicos y la bolsa permanece en la Orange Pi; puede incluir ubicación GNSS, no copiar a documentación compartida.

Al cierre controlado SIGINT de MAVROS volvió a aparecer `Segmentation fault` en `ros2run` (ya es una segunda ocurrencia total, aunque no consecutiva en los ensayos anteriores). El executor informó terminación; no se observó luego proceso MAVROS/observador activo. No atribuir todavía el crash a un plugin concreto. Se mantiene como incidencia reproducible ocasional en cierre físico que requiere aislarse antes de confiar en cierres automáticos prolongados.

La reproducción se inició en domain206, pero la sesión SSH se perdió durante esa validación. El portátil informa ahora Wi-Fi 192.168.2.2, mientras la Pi se había alcanzado en la red 10.221.18.0/24; no se pudo recuperar el resultado de replay ni verificar si la Pi sigue encendida o si la dirección cambió. No afirmar que replay pasó. Reconectar el portátil a la red/hotspot de la Pi o descubrir su IP actual, inspeccionar la Pi y completar replay de la bolsa existente. La grabación y validación de metadatos sí finalizaron antes de perder el acceso.

Se observaron avisos FCU `PreArm: Check mag field (xy diff:157–159>100)` y `PreArm: Radio failsafe on`; son telemetría/diagnósticos existentes, no se modificaron parámetros ni failsafes. No se envió armado, cambio de modo ni consigna de movimiento. El test de retorno BATT_MONITOR de 54 ms se documenta en la sección previa; AUTOPILOT_VERSION sigue sin respuesta.

## Intento de reconexión tras pérdida SSH — 2026-11-07

El portátil volvió a la Wi-Fi/hotspot 10.221.18.0/24 (IP 10.221.18.142, gateway 10.221.18.248). La IP previa de Orange Pi 10.221.18.8 no responde por ICMP ni SSH. Sondeo concurrente local de la subred y vecinos ARP solo detectó el portátil y gateway; no se detectó la MAC Pi `e4:33:89:2e:8d:ad` ni otro SSH activo. Esto no determina si la Pi está apagada: también podría estar conectada a otra Wi-Fi o tener una IP/SSID distinto. Replay y consulta de sus procesos quedan en pausa hasta recuperar su IP/acceso.

## Reanudación y nueva caída de acceso — 2026-11-07

Tras el reinicio manual reportado por el usuario, la Orange Pi reapareció en `10.221.18.8` con MAC `e4:33:89:2e:8d:ad`; SSH y ROS 2 Lyrical funcionaban. No había procesos MAVROS/rosbag heredados. Al revisar la bolsa anterior (`...-1626`) tanto el MCAP como metadata.yaml estaban a 0 bytes pese a que antes `ros2 bag info` había informado 77,8 KiB; no se hallaron errores mmc/ext4 en dmesg y el rootfs tenía 55 GiB libres. Esto apunta a que aquella evidencia no sobrevivió el corte/reinicio, sin evidencia suficiente para atribuir causa.

Se volvió a iniciar MAVROS/observador y se grabó otra sesión con mismo allowlist/domain; el log reportó cierre correcto de rosbag y `ros2 bag info` identificó el bag `~/rra_ws/recordings/rra-h743-uart-duplex-20261107-1654`: MCAP 39.386 bytes y metadata.yaml 5.948 bytes en una comprobación inmediata, tras `sync`. Sin embargo, la verificación remota posterior se interrumpió al caer de nuevo SSH; no se conoce si la Pi sigue asociada ni se completó replay. Se debe revalidar tamaños y ejecutar replay antes de otra pérdida de alimentación.

Tras esa captura, el portátil seguía conectado a `DIGIFIBRA-PyHA` (10.221.18.142; hotspot gateway .248), pero la Pi volvió a desaparecer del ping/SSH y de vecinos. Estado/causa de caída de Wi-Fi aún no identificados; una posible pérdida de alimentación o asociación Wi-Fi no está confirmada. Mantener la Pi encendida y recuperar la red antes de reiniciarla de nuevo para comprobar persistencia de archivos.

## Captura física validada y replay PASS — 2026-11-07

Tras el reinicio de la Orange Pi reportado por el usuario, el hotspot mostró de nuevo `orangepizero2w` (MAC `e4:33:89:2e:8d:ad`); SSH confirmó IP `10.221.18.8`. La Pi permaneció accesible durante esta sesión de prueba. `iw dev wlan0 get power_save` informó `Power save: off`; la causa de que no se asociara en el arranque anterior queda sin determinar. No atribuir a ahorro de energía Wi-Fi.

Corrección sobre la bolsa intermedia `rra-h743-uart-duplex-20261107-1654`: su metadata contiene solo 4 mensajes, `State` conectado=false y diagnósticos/sensores sin datos. El replay de esa bolsa expuso ausencia de telemetría útil; queda descartada como evidencia funcional aunque MCAP (39.386 B) y metadata (5.948 B) sean legibles.

En el arranque actual, MAVROS sobre `serial:///dev/ttyS5:57600` publicó `/mavros/state` conectado=true, armado=false, modo HOLD. Allowlist temporal: `sys_status`, `global_position`, `imu`, `local_position`, `rra_readonly_version`; plugins `command` y `param` ignorados. `rra_telemetry` publicó un diagnóstico en el que conexión, GPS, IMU, batería, velocidad y rumbo estaban disponibles/nivel OK; el verificador omitió coordenadas.

Nueva grabación útil, con `rosbag2` en MCAP y `sync` al acabar: `~/rra_ws/recordings/rra-h743-uart-live-20261107-1700`, 71.981 B más metadata de 5.947 B. Metadata: 51 mensajes / 7 tópicos (State 16; IMU, odometría local, heading, batería y GPS 6 cada uno; diagnostics 5). Replay en ROS_DOMAIN_ID=207 y discovery LOCALHOST PASS: se recibió un mensaje de cada tipo en los siete tópicos; `/mavros/state` siguió como connected=true, armed=false, HOLD; batería presente con voltaje positivo; diagnósticos replayados indicaron conexión y cinco sensores disponibles. Subscriber usó sensor QoS best-effort; el primer verificador con QoS reliable no era compatible y fue corregido. Coordenadas GNSS no se imprimieron; la bolsa queda privada en la Pi.

Cierre controlado de este MAVROS con SIGINT PASS: executor terminó y no quedaron procesos MAVROS/observer/rosbag activos. El segmentation fault de sesiones anteriores no se reprodujo esta vez; se conserva como incidencia ocasional pendiente de aislar, sin refactorización por ahora. MAVROS aún registra timeout en la consulta de versión y usa capacidades predeterminadas. `PreArm: Radio failsafe on` se recibió por MAVLink; no se alteró failsafe ni se enviaron órdenes de movimiento o cambios de parámetros.

**Hito completado:** captura y reproducción de telemetría física H743→ROS 2 verificadas. **Siguiente paso práctico:** mantener esta lista de interfaces como base para la integración ROS del rover/modelo `base_link`; en paralelo, tratar la asociación Wi-Fi al arranque como incidencia separada con observación de logs al próximo arranque, sin más reinstalaciones. No hace falta conectar cables adicionales.

## Arranque reproducible, reconexión y AX10 — preparación local (2026-11-07)

Se añadieron localmente `rra_telemetry/launch/companion_uart.launch.py`, `config/mavros_hardware.yaml` y `scripts/start_companion_hardware.sh`. El launch inicia MAVROS + `rra_state_observer`, usa como defecto `serial:///dev/ttyS5:57600`, ROS_DOMAIN_ID 205 y discovery LOCALHOST; URL, ROS setup y overlay pueden sustituirse. La allowlist cargada contiene sys_status, global_position, imu, local_position y rra_readonly_version; command y param quedan fuera. Se declaró `mavros` como dependencia de ejecución. Sintaxis Bash (`bash -n`) y parseo Python del launch pasan localmente. No se ha compilado ni desplegado en la Pi porque la IP anterior `10.221.18.8` agotó el timeout SSH y no apareció en el escaneo local.

El procedimiento operativo se documenta en `COMPANION_UART_ARRANQUE.md`. En el último SSH remoto conocido, `~/rra_ws/src` no existía aunque sí estaban `build` e `install`; antes de copiar, comprobar de nuevo ese estado para preservar cualquier fuente que haya aparecido. No iniciar autostart/systemd.

**Reconexión física:** no ejecutada. Cuando SSH vuelva, arrancar la receta, comprobar connected=true, el usuario desconecta solo Matek TX1→Orange Pi pin13 durante 12 s y vuelve a conectar; observar false→true sin cerrar MAVROS. No se interviene el retorno ni se cambian parámetros/actuadores.

**AUTOPILOT_VERSION:** el plugin fijo transmite `MAV_CMD_REQUEST_MESSAGE` (512), param1=148. La documentación oficial de ArduPilot describe command 512 y param1 como message ID para consultar una instancia: https://software.ardupilot.org/dev/docs/mavlink-requesting-data.html . Por tanto, el formato elegido es válido; eso no identifica la causa física del timeout. El timeout `mavros.sys` que dice `command plugin service call failed` corresponde además al sondeo automático del plugin sys_status cuando el plugin genérico `command` está excluido; la consulta local fija también requiere validar que llegue AUTOPILOT_VERSION. Trigger exitoso solo confirma envío/request_id, no respuesta. La siguiente sesión suscribirá primero al tópico local, hará una sola consulta fija y registrará si llega el mensaje. No habilitar command plugin genérico ni cambiar parámetros por ahora; MAVLink ACK no está expuesto por el plugin actual.

Se añadió `AX10_MEDICIONES.md` como plantilla vacía y procedimiento. No se han medido wheelbase, vías, radios/circunferencia, ángulos de rueda ni poses. Para crear el modelo sin inventar valores, Juan debe completar medidas del chasis real y acordar con Martín el origen de base_link. GNSS principal/secundario e IMU se registran según montaje real; LiDAR y encoder quedan `NO INSTALADO` si aún no están montados.

Al terminar esta preparación no se ejecutaron pruebas físicas nuevas, no se emitió ningún comando de vehículo, no se modificó configuración ArduRover ni se escribió en GitHub. Las modificaciones locales previas del árbol se conservaron.

## Diagnóstico de pérdida de acceso Orange Pi — 2026-11-07

Tras el reinicio manual, el hotspot mostró la MAC de la Pi y el portátil confirmó `10.221.18.8` → `e4:33:89:2e:8d:ad`. SSH llegó a OpenSSH 10.2 de Ubuntu y la clave ed25519 coincidió con la registrada para `192.168.1.156`; no era un error de clave ni una IP de otro equipo. La sesión root ejecutó las consultas de diagnóstico.

Datos del arranque observado: `uptime` informó 7 min; `ssh` y `wpa_supplicant` activos; `NetworkManager` inactivo. `iw dev wlan0 get power_save` informó `off`; la interfaz aparecía `UP,LOWER_UP`, `state UP mode DORMANT`, con 0 errores y 0 paquetes descartados RX/TX en esa captura. El diario del arranque mostraba el inicio e inicialización correcta de `wpa_supplicant`, sin un evento explícito de desconexión en el fragmento disponible. Esto no demuestra que Wi-Fi permaneciera asociado antes del reinicio ni excluye una caída de alimentación.

No se pudo inspeccionar el arranque anterior: `journalctl -b -1` informó que no había diario persistente, y `last` no está instalado. `who -b` indicó arranque 19:00 mientras `uptime` decía 7 minutos a las 19:44 +01; las fuentes de hora/arranque no son coherentes y no debe usarse `who -b` como prueba de la hora exacta. El mensaje de `sunxi-wdt` solo indica watchdog habilitado, no que se haya disparado. En las líneas filtradas no apareció un aviso explícito de undervoltage ni de apagado térmico; su ausencia no descarta una caída brusca de 5 V.

Se escribió `/etc/systemd/journald.conf.d/90-rra-diagnostics.conf` con `Storage=persistent`, `SystemMaxUse=32M`, `SystemMaxFileSize=8M`, `RuntimeMaxUse=8M` y `MaxRetentionSec=7day`; se reinició `systemd-journald` y `journalctl --flush` terminó. `journalctl --list-boots` mostró el arranque actual y el uso informado fue 8 MB. `systemd-tmpfiles --create --prefix /var/log/journal` falló porque `/var/log/journal` es un symlink; su destino todavía debe comprobarse y la persistencia real se confirma cuando un siguiente reinicio deje visible el boot previo. No se tocó Wi-Fi, SSH, UART, MAVROS ni parámetros de ArduRover.

**Conclusión provisional:** no hay evidencia de que SSH inactivo active suspensión; en el arranque observado el ahorro Wi-Fi estaba desactivado. La incidencia anterior sigue sin causa confirmada: puede ser una desasociación Wi-Fi o un reinicio/corte de alimentación. Próxima observación, sin reinicio manual: comprobar `iw dev wlan0 link`, uptime y `journalctl --list-boots`; al siguiente corte, tras recuperar SSH, comparar el boot anterior y buscar mensajes de `wpa_supplicant`, kernel y undervoltage. Verificar también el destino de `/var/log/journal`.

## Arranque reproducible probado en Orange Pi — 2026-11-07

Desplegados en `/home/rra/rra_ws/src/rra_telemetry` los archivos del arranque de hardware (`companion_uart.launch.py`, `mavros_hardware.yaml`, `start_companion_hardware.sh`) y la dependencia de ejecución `mavros` en `package.xml`. Antes de actualizar se conservaron copias de los archivos reemplazados. El `setup.py` remoto ya instalaba launch/config/scripts y no se sustituyó.

`colcon build --packages-select rra_telemetry` terminó correctamente en ROS 2 Lyrical/Ubuntu 26.04. Se corrigieron dos fallos reales durante la prueba: se quitó `nounset` (`set -u`) del script porque abortaba al cargar el setup ROS por `AMENT_TRACE_SETUP_FILES` indefinida; y se renombró el nodo MAVROS a `mavros` porque publicaba en `/mavros_node/...` mientras el observador escuchaba `/mavros/...`.

Validación física: MAVROS recibió HEARTBEAT de ArduPilot por UART5 y publicó `/mavros/state`; el grafo confirmó un publicador y un suscriptor. El mensaje llegó `connected=true`, `armed=false`, `mode=HOLD`. `/rra/telemetry/diagnostics` confirmó conexión y datos recientes de GPS, IMU, batería, velocidad y rumbo; las edades de recepción observadas fueron ~0,2–0,3 s. El launch y observador se dejaron iniciados para continuar con la sesión.

Incidencias abiertas: el sondeo automático MAVROS de `AUTOPILOT_VERSION` agota timeout y cambia a capacidades por defecto; `command` sigue fuera de la allowlist, y no se habilitó. Debe probarse separadamente el servicio fijo de versión RRA. MAVROS también recibió `PreArm: Radio failsafe on`; no se alteró ningún parámetro. No se envió ninguna orden de actuación ni movimiento.

El arranque reproducible funciona con el dominio ROS 205 y `serial:///dev/ttyS5:57600`. La prueba remota confirmó la interfaz y telemetría, no el arranque autónomo tras reinicio (sigue siendo manual, sin systemd). No se tocó GitHub ni se creó commit.

## HC-SR04 conectado; prueba aún pendiente — 2026-11-08

El usuario informa que instaló el HC-SR04 siguiendo la conexión propuesta en la H743-WLITE: TRIG a S4/GPIO53, ECHO a S5/GPIO54, alimentación de 5 V y GND común; indica que los pines estaban libres y comprobó las tensiones con multímetro. La conexión y el funcionamiento aún no se han verificado desde la FCU. No hay copia local completa de parámetros físicos.

La Orange Pi volvió a estar accesible por SSH como `rra` (alias `rra-companion`, host `orangepizero2w`, IP observada `10.221.18.8`); uptime de 17 minutos, asociación Wi-Fi activa, UART5 `/dev/ttyS5` presente y `rra` en grupo `dialout`. Se inició el launch hardware de telemetría ya existente: MAVROS recibió heartbeat de ArduPilot por UART5 y el observer arrancó. `distance_sensor` no está en la allowlist actual; por tanto, esta sesión no observó el sonar en ROS. Se pararon los procesos y no quedaron MAVROS/observer activos.

El log del arranque capturó el aviso existente `PreArm: Radio failsafe on` y timeout automático de `AUTOPILOT_VERSION`; no se alteró ningún parámetro, modo, misión ni actuador. La petición actual del usuario es avanzar con pruebas del sonar. Próximo paso: guardar desde Mission Planner el archivo completo actual `.param` en `codex_handoff/evidencias/sonar-20261108/`, comparar las asignaciones de S4/S5 y los parámetros `RNGFND1_*`, y después validar solo medición del HC-SR04. No activar `PRX1_TYPE` ni `AVOID_ENABLE` en esta fase de lectura. La cámara USB y las mediciones del AX10 siguen pendientes.

## Revisión del export previo al HC-SR04 — 2026-11-08

Se encontró `codex_handoff/evidencias/sonar-20261108/H743_antes_sonar_2026-11-08.param` (19.768 bytes): 1.135 nombres únicos y sin duplicados. Estado guardado: `SERVO4_FUNCTION=0`, `SERVO5_FUNCTION=0`, `RNGFND1_TYPE=0`, `PRX1_TYPE`…`PRX5_TYPE=0`, `AVOID_ENABLE=3`, `FENCE_ENABLE=0`, `OA_TYPE=0`. El sonar conectado por el usuario aún no ha generado una lectura observada. Se prepararon archivos locales con configuración de lectura candidata y reversión mínima, pero no se aplicó ningún parámetro.

La guía oficial asigna a `AVOID_ENABLE=3` los bits de fence y proximity. Por tanto, se mantendrá `PRX*_TYPE=0` y no se tocará `AVOID_ENABLE` en la prueba de distancia. No se activará evitación ni navegación.

Después de guardar el estado, el portátil pasó a Wi-Fi `192.168.2.2`/gateway `192.168.2.1`, mientras la última IP conocida de Orange Pi era `10.221.18.8`. La conexión SSH se agotó y no se puede comprobar si la Pi conserva un launch temporal activo. La última conexión MAVROS sí confirmó heartbeat ArduPilot y luego fue cerrada antes de esta segunda sesión temporal.

## Prueba inicial del HC-SR04 en H743 — 2026-11-08

Matek H743-WLITE está conectada por Mission Planner sobre TCP. El export previo (`codex_handoff/evidencias/sonar-20261108/H743_antes_sonar_2026-11-08.param`) conserva 1.135 parámetros; valores observados antes de cambio: `SERVO4_FUNCTION=0`, `SERVO5_FUNCTION=0`, `RNGFND1_TYPE=0`, `PRX1..5_TYPE=0`, `AVOID_ENABLE=3`. El archivo del candidato omitía parámetros no reconocidos por la tabla que estaba cargada. Mission Planner confirmó escribir solamente `SERVO4_FUNCTION=-1`, `SERVO5_FUNCTION=-1` y `RNGFND1_TYPE=30`; mostró aviso de reinicio requerido. No se reinició ni se activó evitación.

Al pedir refresco, Mission Planner informó que cambió el total de parámetros y que efectuaría una descarga completa; la tabla quedó vacía en la observación final de esta sesión. Por tanto, no hay confirmación actual de `RNGFND1_STOP_PIN`, `RNGFND1_PIN`, `RNGFND1_ORIENT`, `RNGFND1_MIN` ni `RNGFND1_MAX`, y no existe todavía ninguna lectura real del HC-SR04. Mantener inmóvil el rover. Próximo paso operativo: recuperar la tabla completa, completar/leer de vuelta esos cinco parámetros (53, 54, 0, 0.2, 2.0), guardar export posterior y recién entonces reiniciar para probar medidas; dejar `PRX*` y `AVOID_ENABLE` sin cambios. No iniciar actuadores, modos ni movimiento. La Pi no está confirmada accesible por SSH en esta sesión, por lo que aún no se añadió `distance_sensor` a MAVROS.

## HC-SR04: parámetros físicos guardados — 2026-11-08

Después de reconectar y refrescar Mission Planner, se completó la configuración mínima de rango y se confirmó el mensaje “3 parameters successfully saved”: `RNGFND1_MAX` 7→2 m, `RNGFND1_PIN` -1→54, `RNGFND1_STOP_PIN` -1→53. Se mantienen `SERVO4_FUNCTION=-1`, `SERVO5_FUNCTION=-1`, `RNGFND1_TYPE=30`, `RNGFND1_MIN=0.2`, `RNGFND1_ORIENT=0`. `PRX1_TYPE`…`PRX5_TYPE` se observaron en 0 y `AVOID_ENABLE=3`, como en el export previo. Por tanto el sensor no se seleccionó como fuente de proximidad y no se activó una función de evitación nueva.

La H743 aún no se ha reiniciado después de configurar el driver y no existe lectura física validada. El próximo paso depende de dejar el rover estacionario y desarmado; reiniciar solo la controladora, reconectar Mission Planner y medir el HC-SR04 frente a un blanco plano a distancias conocidas. No moverse a prueba móvil. Cuando la lectura local funcione, verificar estado de SSH y publicar el mensaje en ROS mediante MAVROS `distance_sensor`. Trabajo y documentación permanecen en local; sin cambios en GitHub/Trello.


## Lectura física del sonar tras reinicio — 2026-11-08

Mission Planner recibió DISTANCE_SENSOR (#132) del autopiloto a 2 Hz. Muestra observada: 81 cm; min/max 20/200 cm, orientación 0 frontal, tipo 1 ultrasonido. Vehículo DISARMED con aviso PreArm Radio failsafe on; no se armó ni se enviaron órdenes. Primera recepción de medida confirmada; falta comprobar cambios frente a blancos a distancias medidas (0,50 m y 1,00 m) y validar en MAVROS. La Pi está en el hotspot según el usuario, pero el portátil no la localiza: antigua IP 10.221.18.8 y alias SSH fallan; portátil 192.168.2.2, gateway 192.168.2.1. No se alteraron redes. Consultar nueva IP en clientes del hotspot. Sin PRX/evitación ni movimiento.


## Incidente Wi-Fi/actividad tras varias horas — 2026-11-08

El usuario informa que la Orange Pi vuelve a dejar de aparecer en el hotspot al cabo de un rato. Observación física: LED rojo fijo y LED verde, que antes parpadeaba, apagado. Desde el portátil no hay SSH al alias rra-companion ni a la última IP conocida 10.221.18.8; la búsqueda local anterior no encontró otro host. No hay evidencia en esta sesión que permita decidir si cayó solo la WLAN, si Linux se bloqueó o si la tarjeta dejó de arrancar.

El manual oficial Orange Pi Zero 2W indica que el rojo permanece encendido con alimentación, el verde es controlado por software y, durante el arranque esperado, parpadea al entrar en el kernel. Rojo fijo/verde apagado puede ser compatible con Linux que no inició correctamente, pero no es diagnóstico concluyente porque el LED verde se puede desactivar. Referencia: https://orangepi.net/wp-content/uploads/2023/10/OrangePi_Zero2w_H618_User-Manual_v1.1.pdf, sección 3.5.

En el último diagnóstico remoto accesible (2026-11-05), wlan0 tenía ahorro de energía Wi-Fi apagado, enlace fuerte y sin errores/drops; esos datos son históricos y no describen el fallo presente. Posibles causas aún abiertas: cuelgue del sistema/kernel o WLAN, alimentación marginal/caída de tensión desde el rail Vx de la Matek, o problema de microSD/arranque. No cambiar configuraciones todavía.

Siguiente captura discriminante durante el fallo: comprobar en la lista del hotspot si orangepizero2w sigue conectado. Si desapareció, registrar hora/tiempo desde encendido y estado de ambos LEDs; si sigue conectado, anotar IP asignada y reintentar SSH a esa IP. Para separar cuelgue Linux de caída de Wi-Fi se necesitará una consola local (HDMI o UART debug TTL 3,3 V con adaptador USB-TTL; no conectar al UART de telemetría ni inyectar 5 V). A la vuelta de SSH, recoger journal del arranque anterior y estado de undervoltage/thermal y revisar el rail 5 V de entrada bajo carga. No se alteró red, SSH, sistema ni cableado en esta sesión.


## Reinicio recuperado, sin acceso SSH a la IP actual — 2026-11-08

El usuario informa que después de reinicializar la Orange Pi vuelve el parpadeo del LED verde y el dispositivo reaparece en la lista del hotspot. Esto confirma alimentación y asociación reportadas, pero no diagnostica el incidente previo ni confirma SSH. El portátil sigue en 192.168.2.2; el alias SSH local ra-companion aún apunta a 10.221.18.8, que no responde. No se obtuvieron logs porque la IP DHCP actual de la Pi no está identificada/accesible. No se hicieron cambios remotos.

Para continuar el análisis del arranque y undervoltage hace falta la IP asignada actualmente (detalle del cliente orangepizero2w en el hotspot/router) o acceso local a la Pi. Una vez recuperado SSH: consultar journalctl -b -1 -k y journalctl -b -1, dmesg del boot anterior, vcgencmd/estado thermal disponible en esta plataforma y contadores mmc/ext4 de errores; distinguir errores de undervoltage (si el SoC/PMIC los expone) de simples desconexiones Wi-Fi. Revisar el voltaje Vx bajo carga con multímetro solo si siguen los reinicios/cuelgues. No alterar alimentación, Wi-Fi, kernel ni microSD antes de guardar evidencia.


Reintento SSH solicitado por el usuario (2026-11-08 18:53:09): alias rra-companion sigue resolviendo a 10.221.18.8; conexión TCP/22 agotó timeout tras 3 s (OpenSSH 9.5p2, BatchMode; sin prompt de clave). No se pudieron obtener logs. Requiere IP actual alcanzable o acceso a la misma subred sin aislamiento entre clientes.


## Revisión SSH de registros de cuelgue — 2026-11-08 19:20 CET

Conectividad confirmada por SSH usando la clave local existente a rra@10.221.18.8. Sistema activo: Orange Pi Zero 2W, ARM64, kernel 6.18.60-current-sunxi64; uptime observado 29 min y carga baja.

Journald conserva cuatro boots (16:45–16:56, 18:00–18:30, 18:00–18:45 y el actual). El boot anterior al actual termina en el registro 18:45:29 durante armbian-truncate-logs, sin shutdown ordenado ni último mensaje de kernel que explique la detención. Como el usuario ya había forzado la reinicialización tras el fallo, ese corte es compatible con apagado/reinicio manual y no identifica la causa del cuelgue. No aparecen eventos OOM, panic/oops, reset de watchdog, timeouts de MMC, errores I/O ni errores EXT4 en el boot previo.

La microSD de 59.5 GiB fue detectada, mmcblk0p1 montó EXT4 y se remontó r/w; raíz ocupa 2.6 GiB y quedan 55 GiB libres. No hay evidencia actual de corrupción de sistema de archivos, aunque esto no sustituye a un chequeo offline de la tarjeta. Los mensajes repetidos sunxi-mmc ... Error applying setting, reverse things back ocurren durante la fase de pinctrl al iniciar UART/SPI/MMC, pero luego mmc inicializa, detecta la tarjeta y monta la raíz; por sí solos no demuestran fallo de la SD.

El boot previo registra una asociación Wi-Fi rechazada una vez y aceptada dos segundos después; DHCP consiguió 10.221.18.8. No hay evento posterior de pérdida de carrier ni desconexión Wi-Fi antes de que cesen los logs. Estado actual: wlan0 asociado a DIGIFIBRA-PyHA, RSSI -51 dBm, power_save=off, RX/TX errors y drops=0. Temperaturas CPU/SoC registradas 43.2–44.3 °C. No hay sensores de voltaje expuestos en /sys/class/hwmon o /sys/bus/iio en la instalación examinada, y el log no contiene evento explícito de undervoltage; por tanto no se puede confirmar ni excluir un bajón transitorio en la alimentación de 5 V mediante software.

Conclusión provisional: no se observan indicios de corrupción de kernel/microSD, sobretemperatura ni simple ahorro de energía Wi-Fi. La detención parece abrupta (cuelgue o pérdida de alimentación), pero la evidencia no distingue ambas porque el usuario reinició físicamente el sistema y el SoC no expone telemetría de voltaje. Próxima comprobación de mayor valor: medir 5 V directamente en la entrada de la Pi mientras opera desde Vx de la Matek y repetir bajo carga Wi-Fi; una prueba A/B breve con fuente USB-C regulada conocida separaría el rail Vx de un posible fallo de software. No cambiar kernel, Wi-Fi, SSH ni microSD hasta hacer esa comparación.

## ROS 2 recibe distancia del sonar — 2026-11-08

En Orange Pi, instalado `mavros-extras`, activado plugin `distance_sensor` y reconstruido `rra_telemetry`. El launch UART5 normal publica `/mavros_node/rangefinder_pub` (`sensor_msgs/msg/Range`) con `frame_id=hc_sr04_front`. Muestra real 0,90 m; coincide con medida física de 90 cm comunicada. Configurado solo flujo FCU→ROS, sin suscriptor de distancia ROS→MAVLink. Detalle reproducible en `codex_handoff/evidencias/sonar-20261108/ROS2_HC_SR04_RESULTADO.md`. El launch se dejó activo manualmente. No se enviaron órdenes ni se modificaron parámetros de la H743 durante esta fase.

## Paquete local para revisión de Martín — 2026-11-08

Preparado en `docs/companion_handoff_martin_2026-11-08/`: contrato de integración actualizado, YAML MAVROS, resultado HC-SR04 y rosbag2 física íntegra. La rosbag incluye todos los tópicos ROS visibles (43), GNSS y MAVLink source/sink tal cual, dura 57,18 s y contiene 57 muestras del sonar. `ros2 bag info` y reproducción aislada (`ROS_DOMAIN_ID=206`) comprobaron lectura del DB3 y recepción de `/mavros_node/rangefinder_pub` como `sensor_msgs/msg/Range` a 0,90 m. El hash del DB3 coincide entre Pi y PC.

El entorno de `C:\RRA` quedó con `pull.rebase=true`. Se trajo `origin/main` mediante `git pull --rebase --autostash`; Martín había actualizado de `a370189` a `66eba7a`. El checkpoint local previo se rebasó como `efcdea6`. El paquete de revisión quedó publicado en `origin/main` mediante el commit `e81d973` (incluye los commits `efcdea6`, `6ef307b` y `24ed3fd`, más las actualizaciones de Companion/telemetría). La verificación posterior confirmó `main` local y `origin/main` en `e81d973`, sin diferencias. Ver contrato, bag e instrucciones en `docs/companion_handoff_martin_2026-11-08/README.md`.


\n\n\n## Actualización 2026-11-10 — control de aceleración/frenado
Juanjo informa que `MOT_SLEWRATE` se puso a `0` y que la respuesta ahora es inmediata y satisfactoria tanto al acelerar como al frenar/soltar el gatillo. Esto confirma en la prueba práctica que la rampa de salida de ArduRover era el origen del retardo percibido. El valor anterior `100` aparece en la captura de Mission Planner; el valor actual `0` es reportado por el usuario y no se volvió a leer desde la estación en esta sesión. La emisora mostraba Rate 100/Exp 0 en CH4, sin que esa captura identifique el canal como acelerador. No se cuantificó distancia de parada. Registro detallado en `docs/diario.md` (2026-11-10).

## 2026-11-10 — modelo ROS AX10
Existe el paquete local `src/rra_ax10_model`: Xacro con `base_link` en el centro del eje trasero, ruedas/sensores; coordenadas de ficha convertidas de Y derecha a Y izquierda ROS; cinemática configurable. El modo usado por defecto es paralelo por Ackermann reportado 0°, con límite preliminar 25°, wheelbase 0,320 m y radio 0,056 m. Incluye alternativa Ackermann ideal configurable. El nodo consume consignas en `/rra/model/cmd_ackermann` y publica solo odometría y articulaciones predichas; no controla el rover; TF móvil desactivado por defecto. Seis tests Python pasan y XML bien formado. Sin ROS 2/colcon/xacro disponibles en el portátil: compilación/lanzamiento ROS pendiente. Ver `src/rra_ax10_model/README.md` y `docs/diario.md`.

## 2026-11-10 — distribución de batería del rover reportada
Dos packs HOOVO LiPo 2S (7,4 V nominal, 5200 mAh, 80C según ficha comercial, XT60), idénticos según el usuario: uno alimenta exclusivamente ESC Axial AE-2/motor; el de electrónica llega a BAT+/BAT− de H743 mediante fusible de 30 A e interruptor. La Matek tiene conectados servo MG995, PWM del ESC, GNSS/brújula, Orange Pi, HC-SR04, FS-BS8 y XIAO ESP32-S3/DroneBridge. El cable rojo BEC del ESC está desconectado; PWM mantiene masa común. El rail de alimentación de cada periférico y sus consumos siguen pendientes. AE-2 tiene corte LiPo Auto-LiPo por defecto según su guía, pendiente de verificar en este ESC. La entrada H743-WLITE está especificada para 6,8–30 V. Fusible no equivale a protección de sobredescarga. Detalles y próximos pasos en `codex_handoff/ARQUITECTURA_ALIMENTACION_BATERIAS.md`; inventario corregido (incluido receptor FS-BS8).

## 2026-11-11 — medida inicial de batería electrónica
Juanjo reporta `battery_voltage` 7,38 V en Mission Planner y 7,46 V con multímetro (diferencia 0,08 V, aprox. 1,1%); no consta si coincidieron instante y punto de medida. Corriente reportada 0,15 A habitual y picos de 0,6 A con todos los periféricos conectados y el servo moviéndose repetidamente. El usuario observa que la Orange Pi deja de responder cuando mueve el servo; una caída transitoria de Vx/5 V es plausible, pero aún no está medida y el amperaje mostrado puede no registrar picos breves. No se ajustó calibración ni umbral. Siguiente: medir tensión en la entrada de la Pi durante el movimiento del servo, manteniendo condiciones comparables. Diseño local en `codex_handoff/ARQUITECTURA_ALIMENTACION_BATERIAS.md`.

## 2026-11-11 — caída de tensión durante movimiento del servo
El usuario observa que la Orange Pi deja de responder al mover repetidamente el servo. En el multímetro la entrada de batería varió aproximadamente entre 7,5 y 6,6 V, mientras Mission Planner apenas variaba. Falta confirmar si la medición fue directamente en BAT+/BAT− de la H743; si sí, 6,6 V está por debajo de la especificación mínima de entrada (6,8 V). Próximo: comparar pack, BAT de H743 y entrada 5 V de Pi durante el mismo movimiento para localizar si la caída aparece en pack, cableado o Vx. No cambiar parámetros/cableado todavía. Diseño local actualizado.

## 2026-11-13 — protección de batería electrónica
Paquete prototipo `src/rra_battery_protection` implementado; seis pruebas de simulación pasan local y en Orange Pi. Compiló en `~/rra_ws`. Prueba temporal MAVROS por UART5 `/dev/ttyS5:57600` conectó; monitor DRY_RUN recibió batería 7,890 V y sonar 1,63 m. Launch cerrado, sin autostart.

Lectura de parámetros sin escritura: `SCR_ENABLE=0`, `BATT_MONITOR=4`, `BATT_VOLT_PIN=10`, `BATT_VOLT_MULT=11`, low/critical voltages 0, low timer 10, actions 0, SERVO12 0, RELAY1_FUNCTION 0, `RELAY_PIN` no declarado. Contrastar multiplier 11 con referencia Matek 21 midiendo los pads BAT al mismo tiempo que Mission Planner. No activar el Lua o umbrales aún. Protocolo MAVLink de apagado todavía no implementado; sin servicio systemd/Pololu. Ver `PROTECCION_BATERIA_2026-11-13.md`.

### Actualización — desarrollo de apagado Companion sin Pololu (2026-11-13)

`src/rra_battery_protection` incluye protocolo MAVLink raw Lua↔Companion y listener ROS2, con `DRY_RUN=1`, persistencia JSONL, ACK y READY con nonce. El Lua no acciona GPIO. Trece pruebas locales pasan. SSH por clave funciona; paquete compilado en Orange Pi con ROS 2 Lyrical. Unidad systemd activa como `rra`, QoS BEST_EFFORT coincidente con MAVROS y DRY_RUN confirmado. Prueba sintética completó ACK/READY y poweroff simulado. El 2026-11-14 MAVROS volvió a conectar físicamente por `/dev/ttyS5:57600`, `MY ID 1.191/TARGET 1.1`; el estado FCU fue conectado, desarmado, HOLD, batería 7,633 V. La descarga completa de parámetros solo muestra `SCR_ENABLE=0` y no declara `SCR_HEAP_SIZE`; el script Lua no se ha subido ni ejecutado. El perfil temporal con plugins param/ftp se revirtió; ambos vuelven excluidos. No se escribieron parámetros FCU, no hubo corte ni apagado real. Guía en `PROTECCION_BATERIA_2026-11-13.md`.

### Corrección — compatibilidad Lua confirmada en el firmware 4.7.2

La consulta del 2026-11-14 al servidor oficial de firmware confirma que el build reportado por la Matek (ArduRover 4.7.2, commit `fb773567896014da007bca58358704d4a0d8516f`) corresponde a `Rover/stable-4.7.2/MatekH743`. Su `features.txt` incluye `AP_SCRIPTING_ENABLED`, `AP_SDCARD_STORAGE_ENABLED` y `AP_FILESYSTEM_SYS_ENABLED`. La ausencia de `SCR_HEAP_SIZE` con `SCR_ENABLE=0` no significa que scripting no esté compilado; la documentación indica refrescar/reiniciar los parámetros tras habilitarlo. En la continuación SSH funcionó y el servicio quedó `active` con `DRY_RUN=1`; una escucha UART5 leyó 6.569 bytes/8 s y encontró framing MAVLink con origen `1/1` y msgid 0, pero MAVROS permaneció `connected=false`. SSH volvió a agotar el tiempo de espera durante la comprobación. No se cambió `SCR_ENABLE`, no se hizo pull de parámetros y no se cargó Lua. Siguiente: recuperar SSH y resolver por qué MAVROS no acepta el flujo UART5; luego guardar parámetros y habilitar `SCR_ENABLE=1`, sin GPIO ni corte.

Actualización de medida simultánea: multímetro 7,89 V y ArduPilot 7,854 V, diferencia 0,036 V (0,46%). A este nivel la calibración actual presenta buena coincidencia; no cambiar `BATT_VOLT_MULT` solo por la diferencia con la referencia de ficha. Falta precisión a otros voltajes y medir sag bajo servo.
