# Companion provisional: Orange Pi Zero 2W

> Estado vigente a 2026-11-08: Orange Pi conectada a la H743-WLITE por UART5↔TELEM2 a 57600 MAVLink2. El 7/11 se probaron telemetría física, grabación rosbag de siete tópicos y replay. La receta manual se compiló y se ejecutó; no hay autostart. Ver `codex_handoff/ESTADO_ACTUAL.md` para el resultado y los límites.

Estado: ROS 2 base instalado y comunicación local básica verificada.
Registro inicial: 2026-11-03.

## Alcance y coordinación

El desarrollo se prepara en la rama local `feature/orangepi-ros2`, basada en
`main` en la revisión `a370189dbffdc9a48d3162033019e116f620823f`. La rama
todavía no está publicada. El repositorio compartido contiene documentación y
un ensayo SITL, sin paquetes ROS 2 propios en la revisión consultada.

Propuesta: mantener el software portable en paquetes independientes, usar
mensajes estándar cuando sea posible y conservar configuraciones distintas para
simulación y hardware. ArduRover mantiene el control crítico. Las primeras
pruebas del companion se limitan a diagnóstico, lectura y simulación; no se
configuran órdenes de armado, movimiento o cambio de modo.

## Acceso y diagnóstico

El 2026-11-03 se verificó acceso SSH a `orangepizero2w` como `root` y `rra`
mediante una clave dedicada del PC, sin contraseñas en el proyecto. `rra` ya
existía y pertenece al grupo sudo; su acceso con clave se probó. No se ha
desactivado root ni modificado la configuración del servidor SSH.

Diagnóstico previo a instalar: Armbian comunitario 26.11.0-trunk.120, imagen
nightly, Ubuntu 26.04 Resolute ARM64, kernel 6.18.60-current-sunxi64. Memoria
3,8 GiB, zram 1,9 GiB y 56 GiB libres en raíz; temperaturas 45,9–47,3 °C y
carga 0,00 al consultar. Wi-Fi y ruta predeterminada disponibles, DNS resuelve,
SSH activo y zona horaria Europe/Madrid con NTP sincronizado. APT mostró fuentes
Resolute de Ubuntu y Armbian; `dpkg --audit` no devolvió incidencias.

## Compatibilidad e instalación

Se instaló el configurador oficial `ros2-apt-source` 1.3.0~resolute tras
verificar el SHA-256 publicado en su release. `apt-get update` aceptó el índice
firmado para Resolute ARM64. El servidor de paquetes usa HTTP según sus
[mantenedores](https://github.com/ros-infrastructure/rosdistro/issues/195);
APT verifica las firmas y no se ha desactivado la verificación TLS.

La simulación con `apt-get -s --no-install-recommends install` indicó 401
paquetes nuevos, cero actualizaciones y cero eliminaciones para ROS base,
ejemplos Python, colcon y rosdep. Instalados con `apt-get install -y --no-remove
--no-upgrade --no-install-recommends ros-lyrical-ros-base
ros-lyrical-demo-nodes-py python3-colcon-common-extensions python3-rosdep`.
Versiones: ROS base `0.13.0-3resolute.20260919.195359`, ejemplos Python
`0.37.9-1resolute.20260915.091238`, colcon-common-extensions `0.3.0-100` y
rosdep `0.27.0-1`. Se ejecutaron `rosdep init` como root y `rosdep update
--rosdistro lyrical` como `rra`.

El usuario `rra` tiene `/home/rra/rra_ws/src`; su `.bashrc` carga ROS Lyrical
y el workspace cuando existe su instalación. Una nueva conexión y `bash -ic
env` mostraron `ROS_DISTRO=lyrical`. `colcon list` funciona con workspace vacío
y `ros2 bag --help` se ejecutó; no se han probado grabación ni reproducción.

Prueba de comunicación: dos procesos Python con `rclpy` y `std_msgs/String`,
en dominio ROS 172 con descubrimiento local, publicaron y recibieron «RRA prueba
local», ambos con salida correcta. No hay comunicación con el autopiloto.
La primera versión del guion de prueba usó `set -u` y falló al cargar el
entorno ROS antes de iniciar nodos; se corrigió. Una prueba posterior con los
ejemplos de ROS recibió mensajes, pero su cierre forzado por `timeout` produjo
una excepción de apagado; se repitió con dos procesos que terminan normalmente.
`dpkg --audit` no mostró incidencias tras la instalación; SSH siguió activo y el
kernel siguió siendo 6.18.60-current-sunxi64.

El script [`companion_diagnostico.sh`](../scripts/companion_diagnostico.sh) se
probó en la placa y se copió a `/home/rra/rra_ws/tools/`; se ejecuta con
`bash ~/rra_ws/tools/companion_diagnostico.sh` desde la sesión de `rra`.

### Actualización — 2026-11-04

La nota anterior reflejaba el estado del 3 de noviembre y quedó obsoleta: MAVROS
se instaló después. La conexión ROS local se verificó con mensajes de prueba;
MAVROS 2.16.0 arrancó aislado y el flujo MAVLink de SITL/loopback se probó en la
Orange Pi. El gateway también se probó primero con nodos sintéticos y luego con
MAVROS real bajo SROS2 Enforce. El detalle, comandos y evidencias están en
[`../codex_handoff/ESTADO_ACTUAL.md`](../codex_handoff/ESTADO_ACTUAL.md) y
[`../codex_handoff/MAVROS_READONLY_BOUNDARY.md`](../codex_handoff/MAVROS_READONLY_BOUNDARY.md).

El 2026-11-04 se completó además un ensayo bidireccional de ArduRover SITL 4.7.2
con MAVROS 2.16.0 por un túnel SSH de prueba: 1.517 datagramas llegaron a MAVROS
y 47 volvieron a SITL. SITL estaba aislado en un namespace WSL con loopback y los
puertos Orange Pi 14680/14681 solo enlazaron a 127.0.0.1. No se conectó la MATEK
H743-WLITE ni se emitieron órdenes de actuación.

La aplicación usa SROS2 Enforce y un broker de consultas de identidad separada.
El broker expone tres servicios `Trigger` fijos para estado, versión y lectura
del parámetro `BATT_MONITOR`; la app no pudo crear clientes para 233/233
servicios MAVROS ni lectores/escritores directos en los tópicos MAVROS/MAVLink.
Se denegaron 142 endpoints de tópicos. El estado leído fue conectado,
desarmado, MANUAL; `ParamPull` recibió 1.253 parámetros y `BATT_MONITOR` valió 4.
Tras detener SITL, se observó desconexión y el broker devolvió fallo acotado al
intentar otra lectura.

La consulta de vehículo respondió solo con `available_info=1` (heartbeat): SITL
no entregó `AUTOPILOT_VERSION`, así que la API marca el firmware como no
disponible aunque el log de MAVROS identifica ArduRover V4.7.2. La versión
numérica todavía no se obtiene por la interfaz. SROS2 controla endpoints, no el
contenido de una solicitud; el broker restringe los nombres de parámetros en su
código. El proceso MAVROS conserva permisos propios para sus interfaces de
escritura. Esto no valida un enlace físico ni resistencia a compromiso de MAVROS
o del broker. Evidencia y scripts locales en
[`../codex_handoff/evidencias/mavros-bidirectional-sros-2026-11-04/`](../codex_handoff/evidencias/mavros-bidirectional-sros-2026-11-04/)
y `../codex_handoff/mavros_sros_probe/`. No se conectó H743 ni se habilitó
arranque automático.

### Verificación de continuidad — 2026-11-04

Se instaló localmente en el workspace de Orange Pi el paquete ROS
`rra_companion_readonly`; build y cuatro pruebas unitarias correctas. Ensayo
SITL bidireccional bajo SROS2 Enforce correcto: consultas de estado y
`BATT_MONITOR=4`, 233 servicios MAVROS y 142 endpoints directos denegados,
desconexión y timeout limitado al detener SITL. La versión numérica se obtuvo
por MAVLink directo en SITL (`REQUEST_MESSAGE 512/148`, ArduRover 4.7.2,
`fb773567`), pero la API ROS todavía informa versión no disponible. La consulta
está pendiente de una ruta MAVROS dedicada; no habilitar `cmd/command` genérico.
No se conectó H743 ni se activó autostart. Evidencia detallada en
[`../codex_handoff/evidencias/mavros-bidirectional-sros-2026-11-04/seguimiento-puntos-1-3.txt`](../codex_handoff/evidencias/mavros-bidirectional-sros-2026-11-04/seguimiento-puntos-1-3.txt).
