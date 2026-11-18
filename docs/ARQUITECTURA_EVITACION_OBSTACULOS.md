# Arquitectura propuesta: detección y evitación de obstáculos del RRA

Fecha: 18-11-2026. Estado: estudio y propuesta; no se han activado funciones de evitación ni modificado parámetros en el rover. Las decisiones sobre el companion definitivo se acuerdan con Martín.

## Decisión propuesta

Usar dos capas complementarias, con funciones y autoridad explícitas:

1. **Matek / ArduRover:** recibe el HC-SR04 directamente; procesa la proximidad y, tras configurarla y probarla, limita el movimiento o trata de detenerse ante un obstáculo frontal detectado en los modos compatibles. Debe funcionar sin la Orange Pi. La ruta RC, armado, actuadores y modos siguen en la Matek.
2. **Companion definitivo de Martín:** integra sensores con cobertura más amplia, geometría, mapa y odometría; decide rutas y maniobras, respeta la cinemática del AX10 y entrega objetivos o consignas a través de una interfaz acordada. Una sola capa tiene autoridad de planificación de trayectoria por modo; la Matek mantiene sus límites de bajo nivel. Acordar mecanismo, caducidad, arbitraje, reconexión y comportamiento de pérdida de enlace antes de control real.

El companion provisional se usa para telemetría, registro, evaluación y pruebas; no se implementa un segundo planificador que compita con Martín. Como alternativa futura, evaluar BendyRuler nativo si cubre el caso de uso; no activarlo junto con otro planificador sin definir prioridades, observabilidad y pruebas.

## Hechos y límites actuales

- HC-SR04 frontal conectado a la H743, con lecturas comunicadas de 0,30 y 0,90 m y medición ROS de 0,90 m. `RNGFND1_MIN=0,2`, `MAX=2,0 m` son límites configurados, no cobertura garantizada. El rango útil, el cono, latencia, actualización interna, falta de eco y comportamiento con suelo/materiales están por medir.
- `/mavros_node/rangefinder_pub` (`sensor_msgs/msg/Range`) es visible en la Orange Pi. El 18-11 se midió aproximadamente 0,998 Hz en ROS, durante unos segundos; esto **no es** la frecuencia interna de adquisición ni la latencia de parada de ArduPilot. Una observación anterior en Mission Planner fue 2 Hz.
- Marco ROS de entrada `hc_sr04_front`; el modelo AX10 usa `hc_sr04_link`. Reconciliar nombres y autoridad TF antes de integrar; la posición de ficha es aproximada y no debe aplicarse dos veces.
- El último snapshot disponible, de 15-11, indica `PRX1_TYPE=0`, `AVOID_ENABLE=3`, `AVOID_MARGIN=2`, `AVOID_BACKUP_SPD=0,75`, `OA_TYPE=0`. Son valores históricos, no una lectura actual. El bit de proximidad ya está incluido en `AVOID_ENABLE=3`: cambiar solo `PRX1_TYPE` podría activar comportamiento en modos compatibles. La marcha atrás automática configurada en aquel snapshot debe revisarse expresamente. `AVOID_MARGIN=2 m` coincide con el máximo configurado del sensor: no se propone como ajuste útil sin pruebas.
- Un solo sensor frontal mide un cono limitado; no acredita espacio libre a ambos lados, detrás o encima/debajo, ni detecta de forma fiable huecos, obstáculos finos, inclinados, blandos o absorbentes. Lectura inválida o ausencia de eco no equivalen automáticamente a espacio libre. Una cámara USB RGB simple no aporta profundidad métrica por sí sola.

## Comportamiento de ArduRover: verificar por modo

La documentación de ArduPilot presenta la evitación simple de Rover como una estrategia de parada y señala que no actúa en MANUAL. También remite la navegación AUTO/GUIDED a BendyRuler o Dijkstra, por lo que sus afirmaciones generales no bastan para garantizar un comportamiento concreto en todos los modos. En el código del commit instalado `fb773567`, `Mode::calc_throttle` aplica `adjust_speed` cuando está habilitado; la navegación por waypoint usa una ruta de control diferente. Validar el modo y la ruta exactos en SITL 4.7.2 y en campo antes de atribuirles protección. HOLD no es una prueba de frenada automática en marcha. No asumir que la pérdida de sonar obliga a detenerse: hay que comprobar el comportamiento real y decidir una política explícita.

BendyRuler considera caminos en distintos ángulos y se documenta para AUTO, GUIDED y RTL; un único eco frontal de corto alcance no demuestra que los laterales estén despejados. Para maniobrar alrededor de obstáculos se necesita cobertura lateral, del espacio barrido y del trayecto; añadir sensor apropiado y validarlo. Evitar considerar el giro automático con este sonar como solución completa.

## Parámetros candidatos, no aplicar aún

- `PRX1_TYPE=4`: usar rangefinders como fuente de proximidad, después de leer el estado actual y estudiar cómo se combinan fuentes futuras.
- `AVOID_ENABLE`: comprobar sus bits y conservar las demás fuentes; el último valor 3 ya incluye proximidad, no poner 7 por rutina.
- `AVOID_BACKUP_SPD=0`: candidato para primeras pruebas de parada sin marcha atrás automática; revisar el firmware y la intención operativa antes de aplicar.
- `AVOID_MARGIN`, desaceleración, velocidad y filtro: elegir a partir de mediciones y simulación, no copiar valores genéricos. Confirmar si la distancia de proximidad se interpreta desde el sensor o el origen del vehículo y configurar posiciones según firmware antes de calcular márgenes.
- `OA_TYPE` permanece sin cambiar; el snapshot histórico tenía 0. BendyRuler es una evaluación posterior, no parte de la primera parada.
- Preparar export completo y reversión de valores leídos justo antes de cualquier cambio. No cambiar parámetros, misiones, modos, armado o actuadores sin autorización concreta.

## Distancia y frecuencia

Estimar la distancia requerida como avance durante la latencia total + distancia de frenada medida a esa velocidad + margen por incertidumbre + corrección de geometría entre sensor y punto más adelantado del rover. La lectura es desde el sensor, no necesariamente desde el parachoques. El dato reportado de frenada de 30–40 mm no tiene velocidad/superficie normalizadas y no es suficiente para fijar un umbral o velocidad. La tasa ROS observada de 1 Hz implicaría hasta ~1 s entre muestras en esa ruta, pero no se puede extrapolar a la ruta nativa H743. Medir ambas rutas y la latencia completa de decisión y respuesta.

## Plan de desarrollo

1. **Caracterizar lectura real, sin movimiento automático:** registrar distancia real frente a placas de distintos tamaños/materiales, lateralidad, inclinación y alturas; al menos varios puntos entre 0,2 y 2 m; repetición, falsos ecos y pérdida/recuperación. Medir tasa y edad tanto en H743 como en ROS; registrar MAVLink/DataFlash/rosbag cuando sea posible. Documentar geometría del sensor, parachoques y convención ROS.
2. **SITL 4.7.2 aislado:** guardar configuración, inyectar rango por interfaz de simulación, reproducir presencia, salida de rango, ausencia, fallo, recuperación y objeto lateral; registrar modo, velocidad, salidas y estado. Probar MANUAL, STEERING y los modos AUTO/GUIDED de interés; confirmar y medir rutas de parada en vez de inferirlas. Añadir pruebas de pérdida del companion y pérdida del sensor. SITL no valida la física ni el eco real.
3. **Prueba física de percepción:** registro sin control nuevo, blanco fijo y conducción lenta controlada; medir distancia frontal, latencia y frenada en cada superficie y velocidad relevantes. Acordar una forma de intervención RC. Analizar registros antes de elegir umbrales.
4. **Prueba de parada nativa:** tras autorización expresa, exportar parámetros, seleccionar solo ajustes necesarios y preparar reversión; verificar en un modo cada vez con obstáculo adecuado, bajo control del operador. No convertir al rover en autónomo con cobertura solo frontal.
5. **Companion definitivo:** con Martín, fijar tópicos/sensores, timestamps y frescura, frames y TF, contrato de comandos, propietario del control, política ante sensor/enlace perdido y pruebas de integración. Evaluar LiDAR/cámara de profundidad conforme al terreno y presupuesto antes de rodear obstáculos; los sensores deben observar la envolvente y no solo el centro.

## Fuentes

- [Evitación simple, ArduPilot Rover](https://ardupilot.org/rover/docs/common-simple-object-avoidance.html)
- [Rangefinders y configuración de proximidad](https://ardupilot.org/rover/docs/common-rangefinder-setup.html)
- [BendyRuler para Rover](https://ardupilot.org/rover/docs/common-oa-bendyruler.html)
- [Parámetros Rover](https://ardupilot.org/rover/docs/parameters.html)
- [Código Rover del commit instalado](https://github.com/ArduPilot/ardupilot/blob/fb773567896014da007bca58358704d4a0d8516f/Rover/mode.cpp)
- [Mensajes de proximidad MAVLink](https://mavlink.io/en/messages/common.html#OBSTACLE_DISTANCE)
