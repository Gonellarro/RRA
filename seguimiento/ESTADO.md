---
tipo: estado
actualizado: 2026-11-08 18:37
metodologia: 1
---
# Estado

> **Instantánea histórica/superada (2026-11-08 12:45).** Conserva el punto de
> partida del seguimiento inicial de SITL y no refleja los hitos posteriores
> del Companion físico, el HC-SR04 ni el contrato de integración. Para el estado
> vigente consulta `README.md`, `docs/INVENTARIO_HARDWARE_COMPANION.md` y
> `docs/companion_handoff_martin_2026-11-08/`.

## Qué es
Software del Rover Rural Autónomo (Axial AX10 + MATEK H743-WLITE + ArduRover 4.7.2, según identificación de Juanjo y lectura de Mission Planner). Proyecto a dos: Juanjo (socio y cuñado) lleva el hardware y sube sus archivos al mismo repo de GitHub (`Gonellarro/RRA`); aquí se lleva el software. El contrato vigente de responsabilidades e interfaces está en `docs/companion_handoff_martin_2026-11-08/`. ArduRover conserva el control directo; el software externo empieza en solo lectura y todo se prueba antes en SITL.

## Dónde estamos
**Etapa 1 del roadmap, migrada a un portátil dedicado.** Todo el trabajo de software del RRA se hace ahora en el portátil; el PC principal solo guarda HQ y una copia del repo que se actualiza con `git pull`.

- Portátil (T-011, hecha): Lenovo IdeaPad 81BV, i5-8250U, 8 GiB, SSD NVMe de 256 GB, **Ubuntu 26.04 LTS**, usuario `marti`. Git, clave SSH y repo clonado en `~/Documentos/Personal/RRA`.
- ArduPilot (T-012, bloqueada): clonado en `~/Herramientas/RRA/ardupilot`. Falta la versión: será la que lleve la H743 de Juanjo, y se cargarán sus parámetros en SITL. Juanjo lo subirá a GitHub.
- Guía: `docs/instalacion_portatil.md` (qué se instala y por qué) y `docs/migracion_portatil.md` (plan y datos del equipo).
- ROS 2 será **Lyrical Luth** (no Jazzy) en la etapa 7.
- Hay cambios sin subir: `f238957` y todo lo de hoy, a la espera de que Juanjo suba lo suyo.
- Nada validado con hardware real.

## Próximos pasos
1. Cuando Juanjo suba: `git pull --rebase`, commit y `git push` en el PC principal, y `git pull` en el portátil.
2. T-012 · Compilar en el portátil la versión de ArduRover de Juanjo y pasar la verificación (con Claude Code instalado en el portátil).
3. T-013 · Flujo HQ en el portátil (Claude Code, /empezar y /cerrar, ruta de METODOLOGIA.md).
4. T-005 · Arranque y parada repetibles de SITL.
5. T-007 · Estación de control (QGroundControl en `~/Herramientas/RRA/qgc`).

## Riesgos y dudas
- La T-012 depende de que Juanjo suba la versión de firmware y el `.param` de la H743. Algunos parámetros son de hardware y habrá que revisarlos antes de cargarlos en SITL.
- Hasta hacer push, el portátil no tiene el tutorial ni el plan de migración.
- `CLAUDE.md` apunta a `/home/marti/HQ/...`, que no existe en el portátil (T-013). El código de HQ sigue sin commit ni remoto.
- El usuario se pierde con muchos comandos de golpe y con el cambio de PC: explicar primero la idea y trabajar desde el portátil.
- Idea abierta: un móvil con visión como ordenador de compañía (T-015). Necesita un puerto serie libre de la H743, que lo decide Juanjo.
- Siguen pendientes la T-009 (propuesta README/roadmap, ahora con Lyrical) y la T-008 (avisos de SITL; ModemManager probablemente explicado).
