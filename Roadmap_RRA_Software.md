# Roadmap de software — Rover Rural Autónomo

**Documento inicial para el responsable de software**  
**Estado:** propuesta para aprender, diseñar y validar por etapas  
**Base del proyecto:** Axial AX10 · MATEK H743-WING V3 · ArduRover · UM982+ RTK  
**Principio:** avanzar con simulación y pruebas controladas; el hardware real se integra cuando esté disponible y caracterizado.

---

## 1. Para qué sirve este roadmap

Este documento organiza el trabajo de software para una persona que todavía no conoce las herramientas ni la arquitectura del rover. No presupone experiencia previa con ArduPilot, MAVLink, ROS 2 o navegación robótica.

Cada etapa indica:

- qué aprender;
- qué construir o configurar;
- qué resultado verificable debe quedar;
- qué debe cumplirse antes de avanzar.

Es una propuesta inicial. Las versiones, interfaces y decisiones se confirmarán al probarlas y al recibir del responsable de hardware los datos reales del montaje. No hace falta empezar por ROS 2, IA, LiDAR ni brazo robótico.

## 2. Meta de la primera versión

La primera versión de software debe permitir:

1. Conectar una estación de control con ArduRover, inicialmente simulado.
2. Ver el modo, la ubicación, el estado de navegación y los avisos principales.
3. Preparar y ejecutar una misión sencilla de puntos GNSS en simulación.
4. Registrar la misión y reconstruir después qué ocurrió.
5. Detener o bloquear la operación cuando falten comunicación o datos válidos.
6. Repetir el mismo flujo con el rover real, a baja velocidad y en un entorno controlado, cuando el hardware esté listo.

El autopiloto seguirá siendo quien controle directamente el motor y la dirección. El software de nivel superior podrá planificar o solicitar movimiento, pero no sustituirá los modos, failsafes ni la recuperación RC del autopiloto.

## 3. Mapa de etapas

| Etapa | Nombre | Resultado principal |
|---|---|---|
| 0 | Preparar el entorno y aprender lo básico | Entorno de desarrollo reproducible y vocabulario común. |
| 1 | Entender ArduPilot y ArduRover | Simulación SITL funcionando y controlable desde la estación. |
| 2 | Observar y registrar | Panel/CLI de estado y registros analizables. |
| 3 | Misiones AUTO en simulación | Misión de varios puntos ejecutada y repetible en SITL. |
| 4 | Seguridad del enlace y modos | Comportamiento probado ante desconexiones, datos viejos y cambio de autoridad. |
| 5 | Integración con el hardware | Software conectado al H743 y sensores reales, primero sin conducción autónoma libre. |
| 6 | Primera patrulla real | Recorrido corto, lento, supervisado y con informe de resultados. |
| 7 | ROS 2 en laboratorio | Banco ROS 2 que lee estado y prueba interfaces sin controlar el rover real. |
| 8 | Navegación local y percepción | Evaluación de GUIDED/Nav2 y sensores, primero en simulación o en modo observación. |
| 9 | Operación mantenible | Versiones, configuración, copias y procedimientos repetibles. |

Las etapas 0–4 pueden comenzar sin el vehículo montado. Las etapas 5–6 dependen de la otra persona y de las mediciones del hardware. La etapa 7 puede avanzar en paralelo, pero no es requisito para la primera patrulla AUTO.

---

## Etapa 0 — Preparar el entorno y aprender lo básico

### Objetivo

Poder trabajar con seguridad y repetir los pasos de desarrollo sin cambiar configuraciones a ciegas.

### Aprender

- Uso básico de terminal en Linux.
- Carpetas, permisos, procesos y variables de entorno.
- Git: clonar, consultar cambios, crear commits y volver a una versión anterior.
- Diferencia entre firmware, aplicación de estación, simulador y sistema operativo.
- Conceptos de rover: autopiloto, GNSS, modo, waypoint, failsafe y telemetría.

### Hacer

- Crear un repositorio para el software del RRA.
- Crear un README con objetivo, requisitos, comandos y estado real del proyecto.
- Mantener una carpeta de notas de pruebas y decisiones.
- Elegir un entorno de desarrollo Linux. Si el equipo principal no es Linux, usar una máquina virtual o equipo Linux dedicado para las herramientas que lo requieran.
- Registrar las versiones instaladas y comandos usados.

### Entregables

- Repositorio inicial con README.
- Lista de herramientas y versiones.
- Glosario personal de términos del proyecto.

### Criterio para avanzar

Puedes explicar qué proceso se ejecuta en cada equipo y restaurar el repositorio a un estado conocido.

---

## Etapa 1 — Entender ArduPilot y ArduRover mediante SITL

**SITL** significa *Software In The Loop*: ejecutar el firmware del autopiloto en un simulador en vez de en la placa física.

### Objetivo

Aprender cómo arranca ArduRover, qué modos tiene y cómo interactúa una estación de control con él, sin riesgo para el vehículo.

### Aprender

- ArduPilot y su variante terrestre ArduRover.
- Modos MANUAL, AUTO y GUIDED, a nivel conceptual.
- Estación de control, telemetría y MAVLink.
- Qué simula SITL y qué no: no reproduce fielmente el AX10, sus ruedas, freno, radio, vibración o alimentación.

### Hacer

- Instalar y arrancar ArduRover SITL siguiendo la documentación oficial vigente.
- Conectar una estación de control compatible, por ejemplo Mission Planner o QGroundControl, según el sistema operativo y las necesidades del proyecto.
- Inspeccionar el estado del vehículo simulado y cambiar modos sin enviar órdenes de movimiento autónomo al hardware.
- Guardar los parámetros iniciales y documentar cómo reiniciar la simulación.

### Entregables

- Guía reproducible para arrancar y detener SITL.
- Captura o registro que demuestre conexión y estado.
- Copia de la configuración/parametría de partida.

### Criterio para avanzar

SITL arranca de forma repetible, la estación se conecta y puedes identificar el modo efectivo y los avisos del autopiloto.

---

## Etapa 2 — Leer estado y crear registros

### Objetivo

Construir una herramienta pequeña que observe el vehículo y guarde lo sucedido antes de intentar controlarlo desde código.

### Aprender

- MAVLink como protocolo de mensajes entre autopiloto y estación.
- Diferencia entre recibir un dato y saber que es reciente y válido.
- Marcas de tiempo, logs CSV/JSON y diagnóstico básico.
- Conceptos básicos de Python suficientes para leer una librería MAVLink y escribir archivos.

### Hacer

- Escribir un programa de solo lectura que se conecte a SITL.
- Mostrar al menos: conexión, modo, estado armado/desarmado, posición GNSS, velocidad, batería si está disponible y avisos.
- Marcar como antiguo o desconocido un dato que deja de actualizarse.
- Guardar un registro con hora, mensaje recibido y estado de conexión.
- Probar cierre normal, pérdida de SITL y reconexión.

### Entregables

- Programa de lectura con instrucciones de ejecución.
- Ejemplo de log válido y ejemplo de desconexión.
- Lista de campos disponibles y limitaciones observadas.

### Criterio para avanzar

El programa no presenta como actual una conexión o dato que ya se ha perdido y el registro permite reconstruir cuándo ocurrió una desconexión.

---

## Etapa 3 — Preparar y ejecutar misiones AUTO en SITL

### Objetivo

Aprender el flujo de una misión geográfica sencilla utilizando primero las herramientas normales de ArduPilot.

### Aprender

- HOME, waypoints, inicio y final de misión.
- Geocerca y límites geográficos.
- Requisitos de posición y rumbo para navegar.
- Diferencia entre preparar una misión y autorizar que el vehículo se mueva.

### Hacer

- Crear una misión corta de varios puntos en SITL mediante la estación de control.
- Ejecutarla y observar el progreso, las pausas y el resultado.
- Exportar o guardar la misión y registrar parámetros asociados.
- Repetirla al menos dos veces y comparar el resultado.
- Después, evaluar si conviene automatizar la carga de misiones mediante MAVLink. No es necesario programar un planificador propio.

### Entregables

- Misión de prueba versionada.
- Procedimiento de carga, validación, inicio y parada.
- Logs de dos ejecuciones y resumen de diferencias.

### Criterio para avanzar

La misión se completa en SITL de forma repetible y sabes detenerla y volver a un modo seguro desde la estación.

---

## Etapa 4 — Modos, autoridad y fallos de comunicación

### Objetivo

Definir cómo evitar que dos sistemas manden a la vez y qué debe ocurrir si una orden o enlace deja de ser válido.

### Aprender

- Autoridad de movimiento: quién tiene permiso para ordenar en cada momento.
- Diferencia entre AUTO del autopiloto y GUIDED con órdenes externas.
- Caducidad de órdenes, timeout y watchdog.
- Failsafes configurados en ArduRover y límites de las protecciones de software externo.

### Hacer

- Crear una tabla de modos permitidos y quién manda en cada uno.
- En SITL, probar pérdida de conexión de la estación, cierre del programa, orden estancada y cambio de modo.
- Verificar el comportamiento configurado por el firmware; no asumir que todos los fallos paran de la misma manera.
- Especificar que una orden antigua no se vuelva válida solo por reenviarla.
- Documentar los resultados y parámetros efectivos.

### Entregables

- Matriz de autoridad por modo.
- Tabla de fallos → respuesta esperada → respuesta observada.
- Procedimiento de parada y recuperación probado en simulación.

### Criterio para avanzar

Los casos de fallo ensayados producen una respuesta conocida y documentada. Los casos no probados quedan claramente señalados como pendientes.

---

## Etapa 5 — Integrar con el hardware real

Esta etapa comienza cuando la persona responsable del hardware entregue la información de montaje. No se deben inventar puertos, niveles eléctricos ni parámetros a partir de otra placa.

### Objetivo

Conectar el software al H743 y validar comunicación, configuración y sensores, primero con las ruedas levantadas o el vehículo inmovilizado según el ensayo.

### Información que necesitas de la persona de hardware

- Modelo exacto y revisión de la placa H743.
- Firmware y versión de ArduRover instalados.
- Archivo de parámetros y cambios efectuados.
- Asignación real de UART, USB, telemetría y receptor RC.
- Tipo de enlace entre Companion/estación y autopiloto: USB, UART, radio, Wi-Fi u otro.
- Modelo de GNSS, antenas, orientación, configuración y estado de correcciones RTK.
- ESC, servo, receptor, batería, BEC y mediciones de alimentación.
- Estado de montaje e integración del AS5047P: salida, adaptador, frecuencia, escala y sentido.
- Procedimiento físico de corte, parada y recuperación manual.

### Hacer

- Reproducir el perfil de conexión en una mesa o con el rover inmovilizado.
- Empezar en modo de solo lectura.
- Contrastar valores mostrados con la estación de control y el autopiloto.
- Confirmar modo efectivo, calidad GNSS y edad de datos; distinguir RTK fijo de otros estados si la telemetría lo proporciona.
- Guardar parámetros y configuración exactos del enlace.
- Probar pérdida y recuperación del enlace sin permitir movimiento libre.

### Entregables

- Ficha de integración real con versiones, puertos y conexiones confirmados por hardware.
- Log de telemetría real en reposo.
- Lista de discrepancias entre simulación y hardware.

### Criterio para avanzar

La conexión es estable, los datos se interpretan correctamente y la pérdida del enlace tiene una respuesta conocida. No hay discrepancias críticas sin explicar.

---

## Etapa 6 — Primera patrulla real supervisada

### Objetivo

Acompañar la primera ruta autónoma real, simple y controlada. ArduRover AUTO seguirá la misión; tu software observará, registrará y facilitará el diagnóstico.

### Hacer

- Preparar una ruta muy corta en zona controlada, sin personas, tráfico ni obstáculos no evaluados.
- Definir un observador con RC y una forma de detener la prueba.
- Confirmar geocerca, HOME, GNSS, batería, freno, velocidad baja y límites de operación.
- Empezar sin LiDAR, Nav2 ni IA como elementos necesarios para la seguridad.
- Registrar misión, modo efectivo, GNSS, telemetría, batería, eventos e intervenciones.
- Si cualquier condición de inicio falla, cancelar y registrar el motivo.

### Entregables

- Lista de comprobación previa a misión.
- Log de la prueba, resultado y desviaciones.
- Lista de cambios de software o configuración para la siguiente salida.

### Criterio para avanzar

La ruta se realiza con supervisión, se conserva el control manual y los datos permiten explicar el resultado. La distancia y precisión aceptables se fijan a partir del entorno y de mediciones, no por una cifra supuesta.

---

## Etapa 7 — ROS 2 en laboratorio

### Objetivo

Aprender ROS 2 y probar su integración con ArduPilot en una máquina Linux, manteniendo la prueba separada de la conducción real.

### Aprender

- Nodos, topics, mensajes, servicios, parámetros y transformaciones TF.
- ROS 2 Jazzy como candidato indicado en el documento maestro; confirmar compatibilidad y versiones vigentes antes de instalar.
- Puente MAVLink/ROS, inicialmente MAVROS 2 como candidato. Comparar con DDS nativo de ArduPilot solo en una prueba delimitada.
- Marcos de coordenadas: ENU/NED y ROS FLU frente a FRD, a nivel práctico.

### Hacer

- Instalar ROS 2 en Linux de laboratorio.
- Conectar ROS 2 con SITL y publicar/leer estado.
- Visualizar sensores y pose en una herramienta ROS cuando aporte valor.
- Escribir una interfaz de estado y diagnósticos, sin habilitar salida de movimiento al rover físico.
- Documentar un solo propietario para cada dato y transformación.

### Entregables

- Espacio de trabajo ROS 2 reproducible.
- Diagrama/lista de nodos, topics y marcos usados.
- Prueba SITL con logs y versiones fijadas.

### Criterio para avanzar

El flujo se reconstruye desde instrucciones, los marcos y signos están comprobados y se distingue claramente simulación de hardware.

---

## Etapa 8 — GUIDED, Nav2 y percepción local

### Objetivo

Investigar navegación local y detección de obstáculos solo cuando exista un motivo claro para superar AUTO y las mediciones del AX10 estén disponibles.

### Hacer en este orden

1. Definir qué limitación concreta de AUTO se quiere resolver.
2. Obtener geometría, radio de giro, velocidad, retardo y distancia de parada medidos por hardware.
3. Crear modelo/URDF y configuración de navegación que coincidan con el rover real.
4. Probar en SITL o reproducción de datos.
5. Ejecutar sensores en modo observación: registrar qué habría hecho el sistema, sin mandar movimiento.
6. Probar GUIDED a baja velocidad en un área cerrada, con RC disponible, límites y parada verificados.
7. Comparar con AUTO mediante rutas y condiciones similares.

### Entregables

- Informe de necesidad y beneficio frente a AUTO.
- Configuración versionada de navegación y sensores.
- Resultados de pruebas sin actuación y después controladas.

### Criterio para avanzar

Nav2 o percepción mejora una medida acordada y sus fallos tienen respuesta ensayada. Si no aporta una mejora demostrable, se mantiene AUTO.

---

## Etapa 9 — Operación mantenible

### Objetivo

Hacer que el sistema sea entendible y recuperable por cualquiera de las dos personas.

### Hacer

- Fijar versiones de firmware, ROS, dependencias, parámetros, mapas y calibraciones.
- Guardar una configuración conocida y documentar cómo volver a ella.
- Versionar misiones y mapas con datum y fecha.
- Usar nombres de logs que incluyan fecha, misión y versión.
- Registrar cambios: qué se cambió, por qué, quién lo probó y resultado.
- Preparar instrucciones de arranque, parada, recuperación y copia de registros.
- No guardar credenciales NTRIP, claves ni datos sensibles en Git; usar configuración local protegida.

### Entregables

- Manifiesto de versiones.
- Procedimientos operativos breves.
- Historial de pruebas y lista de pendientes actualizada.

### Criterio de finalización

Otra persona puede instalar o recuperar el entorno y entender qué configuración se usó en una misión concreta.

---

## 4. Cómo coordinarse entre dos personas

Como el hardware y el software se desarrollan en lugares distintos, la interfaz debe acordarse por escrito antes de depender de conexiones concretas.

### Tu responsabilidad

- SITL, aplicación/estación, lectura de telemetría y logs.
- Misiones, parámetros del lado de software y pruebas de integración.
- ROS 2 de laboratorio y futura capa de navegación.
- Documentar versiones, supuestos y errores reproducibles.

### Responsabilidad de hardware

- Montaje mecánico y eléctrico.
- Medición de motores, ESC, dirección, alimentación, GNSS y encoder.
- Asignación real de conexiones y reporte de firmware/parámetros instalados.
- Ejecución física de pruebas con el rover y medidas observadas.

### Acuerdos compartidos

- Un identificador de versión para cada configuración probada.
- No cambiar firmware, cableado o parámetros críticos sin dejar registro.
- Todo dato de hardware debe indicar cómo se midió y en qué condiciones.
- Toda prueba autónoma física tendrá un operador de recuperación RC.
- Una decisión se etiqueta como **propuesta**, **seleccionada**, **implementada** o **validada**. “Validada” requiere resultado de prueba.

### Plantilla breve para pedir o entregar una prueba

```text
ID de prueba:
Fecha y responsable:
Hardware / firmware / software:
Configuración y misión:
Condiciones del entorno:
Procedimiento:
Resultado observado:
Log o evidencia:
Problemas / diferencias:
Decisión o siguiente paso:
```

---

## 5. Orden recomendado de aprendizaje

No hace falta dominar todas las tecnologías antes de empezar. Aprende lo necesario para el siguiente resultado:

1. Linux y Git básicos.
2. Conceptos de ArduPilot, modos y SITL.
3. MAVLink y telemetría de solo lectura.
4. Python básico para automatizar lectura y logs.
5. Misiones AUTO y pruebas de fallos en SITL.
6. ROS 2 básico en laboratorio.
7. Marcos de coordenadas y transformaciones para integrar navegación.
8. Nav2 y percepción solo si las pruebas justifican esa complejidad.

---

## 6. Qué no abordar al principio

- No empezar desarrollando un autopiloto propio.
- No enviar PWM directamente al motor o al servo desde un ordenador Linux.
- No permitir que una IA decida o emita órdenes de movimiento sin supervisión convencional.
- No asumir que GNSS RTK siempre estará fijo ni que internet/NTRIP estará disponible.
- No programar la navegación local antes de medir la geometría y frenado del AX10.
- No comprar ordenador, LiDAR o brazo solo porque aparezcan como candidatos en el documento maestro.
- No tratar una simulación correcta como prueba de seguridad física.

---

## 7. Primeros pasos concretos

Para empezar, céntrate únicamente en las etapas 0 y 1:

1. Preparar Linux o un entorno Linux de laboratorio.
2. Crear el repositorio de software y documentar el entorno.
3. Instalar y arrancar ArduRover SITL siguiendo la guía oficial actual.
4. Conectar una estación de control y verificar el estado simulado.
5. Guardar instrucciones y versiones para repetirlo.
6. Después, comenzar el programa de lectura de la etapa 2.

El primer hito no es “tener ROS 2” ni “hacer que el rover vaya solo”. Es poder arrancar la simulación, conectarse, entender el estado y repetir la prueba sin depender de memoria o de una configuración desconocida.

## 8. Registro de decisiones del roadmap

| Decisión | Estado inicial | Cómo se cerrará |
|---|---|---|
| SITL para desarrollo temprano | Propuesta | Verificar instalación y conexión en el equipo de desarrollo. |
| MAVLink para enlace inicial | Propuesta del proyecto maestro | Confirmar mensajes e interfaz con firmware real. |
| AUTO como primera autonomía | Propuesta del proyecto maestro | Validar primero en SITL y después en pruebas físicas supervisadas. |
| MAVROS 2 / ROS 2 | Candidato futuro | Ensayo reproducible con versiones compatibles. |
| Ordenador embarcado | Pendiente | Elegir tras medir carga, consumo, temperatura, puertos y coste. |
| Nav2, LiDAR e IA | Posterior | Incorporar solo ante necesidad y beneficio medible. |

---

## 9. Referencias de partida

Usar documentación oficial actual y registrar fecha/versiones consultadas:

- [ArduPilot: Rover](https://ardupilot.org/rover/)
- [ArduPilot: SITL](https://ardupilot.org/dev/docs/sitl-simulator-software-in-the-loop.html)
- [ArduPilot: Rover MAVLink commands](https://ardupilot.org/dev/docs/mavlink-rover-commands.html)
- [ArduPilot: ROS 2](https://ardupilot.org/dev/docs/ros2.html)
- [MAVLink](https://mavlink.io/en/)
- [ROS 2 Jazzy](https://docs.ros.org/en/jazzy/)
- [Nav2](https://docs.nav2.org/)

Las páginas, versiones y compatibilidad pueden cambiar. Antes de instalar o fijar versiones, comprobar qué combinaciones recomienda la documentación vigente y anotar las versiones efectivamente usadas.
