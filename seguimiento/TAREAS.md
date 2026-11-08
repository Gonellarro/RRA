---
tipo: tareas
---
# Tareas · Rover Rural Autónomo — Software

## T-001 · Poner el proyecto al día
- estado: hecha
- importante: sí
- urgente: no
- cuando:
- vence:
- estimacion: 1h
- avance: 100%
- inicio: 2026-11-08 12:39
- fin: 2026-11-08 12:45
- depende:
- origen: humano

Alcance: leer README y código, escribir ESTADO.md y partir el trabajo pendiente en tareas.
Hecho cuando: ESTADO.md describe dónde estamos y hay al menos tres tareas con estimación.

## T-002 · .gitignore y primer commit del seguimiento HQ
- estado: hecha
- importante: sí
- urgente: sí
- cuando:
- vence:
- estimacion: 20min
- avance: 100%
- inicio: 2026-11-08 12:52
- fin: 2026-11-08 12:55
- depende: T-001
- origen: maquina

Alcance: crear `.gitignore` (tlog, parm temporales, logs voluminosos, entornos virtuales, secretos/NTRIP), hacer commit de `CLAUDE.md`, `seguimiento/` y `.gitignore`, y subirlo a GitHub para que el socio lo tenga. Configurar `pull.rebase true` en el repo.
Hecho cuando: `git status` limpio y `origin/main` contiene el seguimiento.

## T-003 · Completar el registro del entorno de desarrollo
- estado: pendiente
- importante: sí
- urgente: no
- cuando:
- vence:
- estimacion: 30min
- avance: 0%
- inicio:
- fin:
- depende: T-012
- origen: maquina

Alcance: añadir a `docs/entorno_de_desarrollo.md` lo que falta para reproducir el entorno: ruta y commit de ArduPilot (`~/src/ardupilot`, `eb8b5180a1`), venv (`~/venv-ardupilot`), versiones de MAVProxy (1.8.75) y pymavlink (2.4.50), kernel actual, y que el instalador no llegó a escribir el PATH en `~/.profile`. Entregable «lista de herramientas y versiones» de la etapa 0.
Hecho cuando: otra persona podría reconstruir el entorno leyendo solo ese documento.

## T-004 · Glosario del proyecto
- estado: pendiente
- importante: no
- urgente: no
- cuando:
- vence:
- estimacion: 45min
- avance: 0%
- inicio:
- fin:
- depende:
- origen: maquina

Alcance: `docs/glosario.md` con los términos de las etapas 0–2 (SITL, MAVLink, ArduRover, HEARTBEAT, modo, failsafe, waypoint, GNSS/RTK, fix_type, telemetría, estación de control…). Entregable de la etapa 0.
Hecho cuando: el glosario existe y cubre los términos usados en el diario y en el roadmap hasta la etapa 2.

## T-005 · Arranque y parada repetibles de SITL
- estado: pendiente
- importante: sí
- urgente: sí
- cuando:
- vence:
- estimacion: 1h30
- avance: 0%
- inicio:
- fin:
- depende: T-012
- origen: maquina

Alcance: `scripts/sitl.sh` (arrancar con/sin consola y mapa, parar, reiniciar desde cero con `-w`) y guía `docs/sitl.md` con los pasos, el puerto `tcp:127.0.0.1:5760` y cómo comprobar que funciona. Solo simulación. Entregable principal de la etapa 1.
Hecho cuando: SITL se arranca y se para tres veces seguidas con el script, siguiendo solo la guía.

## T-006 · Guardar parametría inicial y evidencia de conexión
- estado: pendiente
- importante: sí
- urgente: no
- cuando:
- vence:
- estimacion: 30min
- avance: 0%
- inicio:
- fin:
- depende: T-005
- origen: maquina

Alcance: copiar a `config/` los parámetros de partida de SITL (con fecha y commit de ArduPilot) y guardar en `logs/` un registro corto que demuestre conexión y estado. Entregables de la etapa 1.
Hecho cuando: los archivos están versionados y el diario/devlog los cita.

## T-007 · Elegir y conectar la estación de control
- estado: pendiente
- importante: sí
- urgente: no
- cuando:
- vence:
- estimacion: 1h
- avance: 0%
- inicio:
- fin:
- depende: T-005
- origen: maquina

Alcance: decidir si basta MAVProxy o se añade QGroundControl (el roadmap propone Mission Planner o QGroundControl; en Linux, QGC). Si se elige QGC, conectarlo a SITL y ver modo, posición y avisos. Registrar la decisión como «seleccionada».
Hecho cuando: hay una decisión escrita y la estación elegida muestra modo efectivo y avisos de SITL.

## T-008 · Revisar los avisos pendientes de SITL
- estado: pendiente
- importante: no
- urgente: no
- cuando:
- vence:
- estimacion: 45min
- avance: 0%
- inicio:
- fin:
- depende: T-005
- origen: maquina

Alcance: investigar los avisos del primer arranque (ModemManager, error UTF-8 al leer la lista SRTM3, `MAV Errors: 3`) y los mensajes de salud del autopiloto. Cierra el criterio de la etapa 1 «identificar los avisos del autopiloto».
Hecho cuando: cada aviso está explicado o descartado en el devlog.

## T-009 · Propuesta de cambios al README
- estado: pendiente
- importante: no
- urgente: no
- cuando:
- vence:
- estimacion: 20min
- avance: 0%
- inicio:
- fin:
- depende:
- origen: maquina

Alcance: propuesta en `seguimiento/propuestas/` para: (1) diario `docs/diario.md` vs devlog de HQ; (2) numeración de etapas 1–9 del README frente a 0–9 del roadmap; (3) sección «Uso con Codex» frente a /empezar y /cerrar; (4) cómo se coordina el repo con el socio (pull --rebase, carpetas).
Hecho cuando: la propuesta existe y el usuario la ha aceptado o descartado.

## T-010 · Programa de lectura de estado (etapa 2)
- estado: pendiente
- importante: sí
- urgente: no
- cuando:
- vence:
- estimacion: 1d
- avance: 0%
- inicio:
- fin:
- depende: T-005, T-007
- origen: maquina

Alcance: programa Python de solo lectura que se conecta a SITL y muestra conexión, modo, armado, posición, velocidad, batería y avisos; marca datos antiguos y guarda un log con hora y estado de conexión. Sin enviar órdenes. Se partirá en subtareas cuando empiece.
Hecho cuando: cumple el criterio de la etapa 2 del roadmap (no presenta como actual un dato perdido y el log permite reconstruir una desconexión).

## T-011 · Preparar el portátil (SO y base)
- estado: pendiente
- importante: sí
- urgente: sí
- cuando:
- vence:
- estimacion: 2h
- avance: 0%
- inicio:
- fin:
- depende:
- origen: maquina

Alcance: pasos 0 a 3 de `docs/migracion_portatil.md`: apuntar los datos del portátil, decidir e instalar el SO (propuesta: Ubuntu 24.04 LTS), paquetes base, git, clave SSH para GitHub y clonar RRA en `~/Documentos/Personal/RRA`.
Hecho cuando: en el portátil, `git pull` funciona en RRA y los datos del equipo y la decisión del SO están escritos.

## T-012 · ArduPilot SITL en el portátil y verificación
- estado: pendiente
- importante: sí
- urgente: sí
- cuando:
- vence:
- estimacion: 2h
- avance: 0%
- inicio:
- fin:
- depende: T-011
- origen: maquina

Alcance: pasos 4 y 5 de `docs/migracion_portatil.md`: decidir la versión de ArduPilot (mismo commit o la estable de Rover, consultándolo con el socio), instalar las dependencias, compilar SITL y pasar la lista de verificación. Solo simulación.
Hecho cuando: todas las casillas del paso 5 están marcadas y el resultado está en el devlog.

## T-013 · Flujo HQ en el portátil y sincronización con el panel
- estado: pendiente
- importante: sí
- urgente: no
- cuando:
- vence:
- estimacion: 1h
- avance: 0%
- inicio:
- fin:
- depende: T-011
- origen: maquina

Alcance: pasos 6 y 7 de `docs/migracion_portatil.md`: Claude Code, `/empezar` y `/cerrar` en el portátil, resolver la ruta de `METODOLOGIA.md` (propuesta: dar a HQ un commit y un remoto privado) y comprobar el ciclo portátil → push → pull en el PC principal → panel.
Hecho cuando: una sesión cerrada en el portátil aparece en el panel HQ del PC principal.

## T-014 · Limpiar ArduPilot del PC principal
- estado: pendiente
- importante: no
- urgente: no
- cuando:
- vence:
- estimacion: 20min
- avance: 0%
- inicio:
- fin:
- depende: T-012, T-006
- origen: maquina

Alcance: paso 9 de `docs/migracion_portatil.md`: después de confirmarlo, borrar `~/src/ardupilot` y `~/venv-ardupilot` (3,5 GB). No se tocan los paquetes de apt.
Hecho cuando: el PC principal ya no tiene ArduPilot y el portátil sigue pasando la verificación.
