# Companion provisional: Orange Pi Zero 2W

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

APT ofrece `ros-lyrical-mavros` 2.16.0-1 para ARM64, aún sin instalar. MAVROS,
sensores, grabación/reproducción de rosbag y comunicación con el autopiloto
son etapas posteriores; no se ha demostrado ninguna conexión real.
