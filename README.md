# Rover Rural Autónomo — Software

Repositorio para desarrollar y documentar el software del **Rover Rural Autónomo (RRA)**. El proyecto se realiza entre dos personas: una se ocupa principalmente del hardware del vehículo y la otra del software.

Este repositorio corresponde al trabajo de software. Las especificaciones generales del rover se mantienen en el documento maestro del proyecto y se incorporarán aquí cuando se decida la estructura definitiva del repositorio.

## Objetivo

Desarrollar, por etapas, el software necesario para supervisar y acompañar un rover rural basado en un **Axial AX10**, un autopiloto **MATEK H743-WING V3** y **ArduRover**.

La primera meta de software es aprender y validar el flujo en simulación: conectar con ArduRover SITL, observar su estado, guardar registros y ejecutar una misión sencilla. La integración con el vehículo real llegará después de que el hardware esté montado y sus conexiones y límites hayan sido medidos.

## Principios del proyecto

- **ArduRover conserva el control directo** del motor, la dirección, los modos y los failsafes configurados.
- El software externo consulta el estado y, en fases posteriores, podrá solicitar acciones mediante interfaces explícitas y supervisadas.
- La primera autonomía se plantea con misiones **AUTO** preparadas y probadas; ROS 2 y la navegación local son fases posteriores.
- Cada etapa debe producir resultados verificables antes de avanzar.
- Simulación, banco de pruebas y rover real son entornos diferentes. Un resultado en SITL no demuestra por sí solo seguridad física.
- Las decisiones se etiquetan como **propuesta**, **seleccionada**, **implementada** o **validada**. Una decisión solo se considera validada tras una prueba documentada.
- No se inventan conexiones, parámetros eléctricos, precisión ni comportamiento del hardware: se confirman con medidas y con la persona responsable del montaje.

## Estado actual

**Fase de preparación y aprendizaje.** El responsable de software conoce Linux y Git. El siguiente trabajo es preparar el entorno de desarrollo, ejecutar ArduRover SITL y aprender a inspeccionar sus estados desde una estación de control.

Todavía no se da por implementado ni validado:

- la conexión con la placa H743 real;
- el enlace de telemetría que usará el rover;
- la integración del UM982+ RTK y sus correcciones;
- la lectura del encoder AS5047P;
- los parámetros y failsafes finales del vehículo.

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
- [ROS 2 Jazzy](https://docs.ros.org/en/jazzy/)
- [Nav2](https://docs.nav2.org/)

Las versiones compatibles se comprobarán en la documentación vigente antes de instalar o fijar dependencias. El estado real de cada integración se documentará aquí o en los documentos enlazados.
