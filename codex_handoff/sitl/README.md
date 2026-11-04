# ArduRover SITL local y receptor provisional

Prueba del 2026-11-03. El simulador oficial precompilado ArduRover 4.7.2 está
en WSL `Ubuntu-22.04`, en `/home/kitttrain/rra-sitl/ardurover`; SHA-256
`f453fd8217b9d798c873e5c424e139a2a3597b52e31658f76b2c177b523391af`.
Procedencia: [binarios oficiales para SITL x86-64](https://firmware.ardupilot.org/Rover/stable/SITL_x86_64_linux_gnu/).
La ruta `stable` puede cambiar; conservar la versión y hash de cada prueba.

`sitl_local_bridge.py` inicia SITL en un namespace de red WSL temporal con solo
loopback. Tres seriales simulados envían a puertos de loopback en ese namespace;
un socket Unix de la carpeta privada transporta solo los datagramas de la salida
principal al proceso exterior. Este los envía por stdin de SSH a
`/home/rra/rra_ws/tools/sitl_receiver.py`, en la Orange Pi. Allí un socket UDP
local los entrega a MAVROS; no se leen ni retransmiten paquetes desde MAVROS a
SITL. ROS usa dominio 179 y descubrimiento `LOCALHOST`. No se usan puertos serie
físicos, ni se conecta la H743. La ubicación es sintética y no es una ruta real.

Desde PowerShell, para repetir con los puertos de prueba libres y la Orange Pi
disponible:

```powershell
wsl -d Ubuntu-22.04 -- python3 -u /mnt/c/RRA/codex_handoff/sitl/sitl_local_bridge.py
```

El receptor debe coincidir con la copia local `sitl_receiver.py`, estar presente
en la ruta indicada y poder cargar ROS Lyrical y el overlay. La clave SSH del
usuario Windows se mantiene fuera del proyecto. La prueba abre los puertos UDP
14680 y 14681 únicamente en loopback de la Orange Pi; dentro del namespace se
utilizan 14690–14692. Cada ejecución usa una carpeta nueva bajo `~/rra-sitl`.
No programar el arranque automático ni modificar firewall/red/SSH para esto.

La prueba verifica recepción de estado, diagnóstico, GPS, IMU y mensaje de
batería, además de pérdida del flujo y cierre de procesos. Las ejecuciones desde
esta actualización cargan `rover-battery-sim.parm` como `--defaults`: contiene
`BATT_MONITOR 4` exclusivamente para SITL, de acuerdo con el `rover.parm`
oficial de la revisión `fb773567896014da007bca58358704d4a0d8516f`. Sin ese
ajuste se observó 0 V y porcentaje negativo; con él se observaron 12,6 V y
100 % simulados. Nunca aplicar este parámetro al vehículo físico sin verificar
su hardware. **La recepción de un mensaje no demuestra que su valor sea válido.** SITL no es
el rover físico y esta prueba no acredita su seguridad ni las conexiones reales.
MAVROS utiliza plugins predeterminados que exponen control dentro del dominio
local; el sentido único de este enlace de ensayo no convierte MAVROS en una
interfaz de solo lectura para uso con hardware.

La prueba graba un rosbag SQLite en el directorio temporal indicado en el
resultado remoto. Para comprobar una bolsa en la Orange Pi, con ROS y overlay
cargados y sin otros ensayos usando el dominio 181:

```bash
ROS_DOMAIN_ID=181 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST \
  python3 ~/rra_ws/tools/verify_bag.py /ruta/a/la/bolsa
```

Los scripts y parámetros locales de este directorio se conservan en
`codex_handoff`, excluido localmente de Git; no activar procesos al arrancar.
