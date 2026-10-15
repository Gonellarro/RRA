# Diario de desarrollo — RRA Software

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
