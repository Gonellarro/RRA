# Estado comprobado de RRA

Actualizado: 2026-11-04, hora Europe/Madrid. Revalidar lo variable al retomar.

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
