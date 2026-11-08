# Rover Rural Autónomo — Software

Repositorio para desarrollar y documentar el software del **Rover Rural Autónomo (RRA)**. El proyecto se realiza entre dos personas: una se ocupa principalmente del hardware del vehículo y la otra del software.

Este repositorio corresponde al trabajo de software. Las especificaciones generales del rover se mantienen en el documento maestro del proyecto y se incorporarán aquí cuando se decida la estructura definitiva del repositorio.

## Objetivo

Desarrollar, por etapas, el software necesario para supervisar y acompañar un rover rural basado en un **Axial AX10**, un autopiloto **MATEK H743-WLITE** y **ArduRover**.

La meta del software es acompañar el rover con observación, registro y, cuando exista una frontera de autoridad comprobada, funciones superiores. El rover ya tiene pruebas físicas iniciales reportadas por su responsable; el Companion provisional también se conectó a la H743 y pasó una prueba de telemetría física y replay el 7 de noviembre de 2026. Esos hitos no equivalen a validar toda la operación en campo ni a una patrulla con el Companion.

## Principios del proyecto

- **ArduRover conserva el control directo** del motor, la dirección, los modos y los failsafes configurados.
- El software externo consulta el estado y, en fases posteriores, podrá solicitar acciones mediante interfaces explícitas y supervisadas.
- La primera autonomía se plantea con misiones **AUTO** preparadas y probadas; ROS 2 y la navegación local son fases posteriores.
- Cada etapa debe producir resultados verificables antes de avanzar.
- Simulación, banco de pruebas y rover real son entornos diferentes. Un resultado en SITL no demuestra por sí solo seguridad física.
- Las decisiones se etiquetan como **propuesta**, **seleccionada**, **implementada** o **validada**. Una decisión solo se considera validada tras una prueba documentada.
- No se inventan conexiones, parámetros eléctricos, precisión ni comportamiento del hardware: se confirman con medidas y con la persona responsable del montaje.

## Estado actual

**Rover físico, según resultados comunicados por el usuario:** MATEK H743-WLITE con ArduRover 4.7.2; MANUAL/RC, armado/desarmado, HOLD, tracción/dirección y fix GNSS 3D probados. Una misión AUTO sencilla de 3–4 waypoints se ejecutó con éxito el 2/11/2026. La incidencia LOITER se ha confirmado resuelta, sin causa raíz registrada. La última calidad GNSS comunicada fue HDOP 0,6 y error horizontal estimado 0,3 m; no es una medida absoluta topográfica. No implica validación de failsafes completos, geocerca o todas las condiciones de campo.

**Companion provisional:** Orange Pi Zero 2W (4 GB) con Armbian/Ubuntu 26.04, ROS 2 Lyrical, MAVROS 2.16.0 y `rra_telemetry`. El 7/11 se compiló e inició sobre UART5 `/dev/ttyS5` ↔ TELEM2/SERIAL2 de la H743, MAVLink2 a 57600; se recibió estado/sensores reales y un rosbag de siete tópicos superó replay. La consulta fija BATT_MONITOR recibió valor 4 con correlación MAVLink ambigua; AUTOPILOT_VERSION sigue sin respuesta. La conexión permite transmisiones de petición y no debe llamarse físicamente unidireccional ni de solo lectura. El Companion continúa en observación; no envía órdenes de movimiento. El problema de Wi-Fi/SSH de la Pi tuvo cortes sin causa confirmada.

El historial y los límites están en [`codex_handoff/ESTADO_ACTUAL.md`](codex_handoff/ESTADO_ACTUAL.md) y [`codex_handoff/MAVROS_READONLY_BOUNDARY.md`](codex_handoff/MAVROS_READONLY_BOUNDARY.md). El inventario publicado de hardware y software es [`docs/INVENTARIO_HARDWARE_COMPANION.md`](docs/INVENTARIO_HARDWARE_COMPANION.md). Las mediciones físicas pendientes del AX10 están en [`codex_handoff/AX10_MEDICIONES.md`](codex_handoff/AX10_MEDICIONES.md); los ensayos y propuestas de sensores, en las fichas HC-SR04 y cámara USB enlazadas desde el plan local.

## Roadmap

El desarrollo propuesto sigue estas etapas:

1. Preparar el entorno y repasar herramientas necesarias.
2. Ejecutar ArduRover SITL y conectarlo a una estación de control.
3. Crear una herramienta de solo lectura para observar estado y guardar logs.
4. Preparar y ejecutar misiones AUTO en SITL.
5. Probar en simulación cambios de modo y pérdida de comunicación.
6. Integrar el software con el hardware real, empezando en reposo o con el rover inmovilizado.
7. Acompañar una primera patrulla real corta, lenta y supervisada.
8. Aprender ROS 2 en laboratorio y evaluar navegación local solo si aporta una mejora demostrable.
9. Fijar versiones, procedimientos y registros para que el sistema se pueda recuperar.

El documento de trabajo detallado es [`Roadmap_RRA_Software.md`](Roadmap_RRA_Software.md). Se desarrollará una etapa cada vez; este README resume el proyecto y no reemplaza sus instrucciones de implementación.

## Coordinación entre hardware y software

Antes de integrar con la placa real, la persona responsable del hardware compartirá al menos:

- modelo y revisión exactos de la H743;
- versión de ArduRover y archivo de parámetros;
- puertos e interfaces realmente conectados;
- tipo de enlace de telemetría;
- modelos y configuración de GNSS, ESC, servo, receptor, batería y reguladores;
- estado de integración del AS5047P;
- procedimiento de parada y recuperación por RC;
- resultados de medidas y pruebas, con sus condiciones.

El software comenzará en modo de solo lectura. Las pruebas que puedan mover el rover se harán únicamente cuando exista un procedimiento físico controlado, una persona con RC disponible y una forma de detener la prueba.

## Estructura prevista

La estructura crecerá con el proyecto. No se crean todavía paquetes ROS 2 ni código de control sin haber validado antes SITL y la interfaz necesaria.

```text
.
├── README.md
├── Roadmap_RRA_Software.md
├── docs/             # decisiones, integración y procedimientos
├── config/           # configuración no secreta y versionada
├── missions/         # misiones y mapas de prueba versionados
├── logs/             # registros seleccionados, evitando datos voluminosos o sensibles
├── scripts/          # herramientas de desarrollo y operación
└── src/              # código, cuando empiece su implementación
```

La estructura puede ajustarse cuando las primeras pruebas indiquen qué componentes hacen falta. No se deben subir credenciales, contraseñas, tokens, claves ni datos de acceso a NTRIP. Los archivos de configuración local con secretos deben mantenerse fuera de Git.

## Diario de desarrollo

Mantener el diario en [`docs/diario.md`](docs/diario.md). Cada entrada debe ser breve y permitir entender qué se hizo y qué falta:

```text
## AAAA-MM-DD — título
- Objetivo:
- Cambios o acciones:
- Resultado observado:
- Evidencia/log:
- Problemas o dudas:
- Siguiente paso:
```

Registrar también las pruebas fallidas y los cambios de configuración relevantes. No describir como validado algo que solo se haya planeado o ejecutado en simulación.

## Uso con Codex en VS Code

Al comenzar una tarea, pedir a Codex que consulte este README y el roadmap. Para trabajo que continúe una etapa, debe revisar también el diario y la documentación relacionada. Al terminar una sesión de trabajo relevante, actualizar el diario con los cambios y resultados reales, sin afirmar que se ejecutó una prueba que no se haya realizado.

Una instrucción inicial útil es:

> Lee `README.md`, `Roadmap_RRA_Software.md` y `docs/diario.md` antes de proponer cambios. Estamos desarrollando el software del Rover Rural Autónomo desde cero. Respeta las etapas y sus criterios de avance; distingue propuesta, implementación y validación. No inventes conexiones ni resultados de hardware. Antes de ejecutar acciones que puedan enviar movimiento, explica el alcance y exige que la prueba se mantenga en SITL o siga el procedimiento físico documentado.

## Referencias

- [ArduPilot Rover](https://ardupilot.org/rover/)
- [ArduPilot SITL](https://ardupilot.org/dev/docs/sitl-simulator-software-in-the-loop.html)
- [Comandos MAVLink de Rover](https://ardupilot.org/dev/docs/mavlink-rover-commands.html)
- [MAVLink](https://mavlink.io/en/)
- [ROS 2 Lyrical Luth](https://docs.ros.org/en/lyrical/)
- [Nav2](https://docs.nav2.org/)

Las versiones compatibles se comprobarán en la documentación vigente antes de instalar o fijar dependencias. El estado real de cada integración se documentará aquí o en los documentos enlazados.
