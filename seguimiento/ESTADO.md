---
tipo: estado
actualizado: 2026-11-08 12:45
metodologia: 1
---
# Estado

> **Instantánea histórica/superada (2026-11-08 12:45).** Conserva el punto de
> partida del seguimiento inicial de SITL y no refleja los hitos posteriores
> del Companion físico, el HC-SR04 ni el contrato de integración. Para el estado
> vigente consulta `README.md`, `docs/INVENTARIO_HARDWARE_COMPANION.md` y
> `docs/companion_handoff_martin_2026-11-08/`.

## Qué es
Software del Rover Rural Autónomo (Axial AX10 + MATEK H743-WLITE + ArduRover 4.7.2, según identificación del usuario y lectura mostrada por Mission Planner). Proyecto a dos; consultar el contrato vigente para responsabilidades e interfaces. La presente instantánea describe el seguimiento inicial del software/SITL.

## Dónde estamos
**Final de la etapa 0 y en plena etapa 1 del roadmap** (`Roadmap_RRA_Software.md`).

- Etapa 0: repo y README hechos; entorno registrado en `docs/entorno_de_desarrollo.md` pero incompleto (faltan ArduPilot, MAVProxy y pymavlink). Falta el glosario.
- Etapa 1: ArduRover SITL compilado y funcionando (primer arranque el 2026-10-15, ver `docs/diario.md`). Revisado el 2026-11-08 tras un borrado accidental de carpetas: `~/src/ardupilot`, el binario `build/sitl/bin/ardurover` y `~/venv-ardupilot` están intactos, y SITL responde con HEARTBEAT por `tcp:127.0.0.1:5760`. Faltan los entregables: guía/script de arranque y parada, copia de parámetros, evidencia de conexión y decisión sobre la estación de control.
- Se arranca a mano: `source ~/venv-ardupilot/bin/activate`, `cd ~/src/ardupilot/Rover`, `../Tools/autotest/sim_vehicle.py -v Rover --console --map -w`.
- Nada validado con hardware real. El seguimiento HQ se añadió el 2026-11-08.

## Próximos pasos
1. T-002 · `.gitignore` y primer commit del seguimiento HQ.
2. T-005 · Arranque y parada repetibles de SITL (desbloquea T-006, T-007, T-008 y T-010).
3. T-003 · Completar el registro del entorno.
4. T-007 · Elegir y conectar la estación de control.
5. Después: T-010, programa de lectura de estado (etapa 2).

## Riesgos y dudas
- El socio sube cambios al mismo repo cuando lo considera: hay que hacer `git pull --rebase` antes de empezar y antes de subir.
- Hay dos diarios: `docs/diario.md` (del README) y `seguimiento/devlog/` (HQ). Pendiente de decidir (T-009).
- El instalador de ArduPilot se interrumpió (bloqueo del PC): no escribió el PATH en `~/.profile`. SITL funciona igualmente, pero el entorno no queda configurado solo.
- Los avisos del primer arranque (ModemManager, SRTM3, `MAV Errors: 3`) siguen sin explicar (T-008).
- Fuera del proyecto: el código de HQ (`/home/marti/HQ`) no tiene ningún commit ni copia remota.
