# Fase 4: diseño de pruebas de autoridad y pérdida de enlace

Estado: F4-0…F4-5 ejecutados en SITL aislado el 2026-11-04. F4-4 observó la caducidad predeterminada de velocidad GUIDED; F4-5 primero mostró ausencia de arbitraje con solo `MAV_GCS_SYSID` y después verificó el filtro global `MAV_OPTIONS` bit 0 con dos emisores. La política de autoridad para el Companion sigue sin definirse y fuera de alcance.

## Alcance y estado de entornos

- El ensayo previsto es únicamente ArduRover SITL 4.7.2 dentro de un namespace de red WSL temporal con loopback como única interfaz, siguiendo `README.md` y la verificación de aislamiento de `mission3_run.py`.
- La fase 3 está documentada por separado en `FASE3_MISION_SITL.md`. Su permiso de órdenes estaba limitado a las misiones de esa fase; este diseño no lo extiende a fase 4.
- La Orange Pi `192.168.1.156` no respondió al SSH de solo lectura del 2026-11-04 (timeout). No se intentó cambiar red, acceder por otra vía ni conectarla al ensayo. La fase 4 propuesta no necesita la Orange Pi.
- WSL `Ubuntu-22.04` está disponible. El binario local `/home/kitttrain/rra-sitl/ardurover` existe y conserva el SHA-256 registrado para 4.7.2 (`f453fd8217b9d798c873e5c424e139a2a3597b52e31658f76b2c177b523391af`). No había un proceso SITL `ardurover` activo en la comprobación inicial. Para F4-0 se inició uno dentro del namespace aislado y terminó correctamente; después se confirmó que no quedaba ningún proceso.
- El `rover-oficial-4.7.2.parm` y el overlay `rover-battery-sim.parm` no fijan los parámetros GCS. F4-0 capturó sus valores efectivos. Para separar el failsafe GCS del failsafe de throttle, las tres pruebas validadas usaron un perfil temporal solo SITL con `FS_THR_ENABLE=0` y `RC_PROTOCOLS=0`; las seis variables se leyeron de vuelta antes de iniciar misión. La documentación oficial recomienda esos valores para operación solo con GCS sin joystick/RC override; no se deben trasladar al hardware sin el diseño de control real. [Guía oficial de operación solo GCS](https://ardupilot.org/rover/docs/common-gcs-only-operation.html).

## Resultado F4-0: lectura de parámetros efectivos

Ejecución local solo de lectura el 2026-11-04. Se arrancó ArduRover SITL en namespace WSL aislado, se comprobó una sola interfaz (`lo`) y se solicitaron los cuatro parámetros por `PARAM_REQUEST_READ`. Heartbeat correspondía a Rover SITL y mostraba `armed=false`. El script no envía órdenes de armado, misión, modo ni navegación.

| Parámetro | Valor efectivo | Interpretación inicial |
|---|---:|---|
| `FS_GCS_ENABLE` | 0 | Failsafe de estación desactivado |
| `FS_GCS_TIMEOUT` | 5 s | Umbral cargado; no activa nada si el failsafe está deshabilitado |
| `FS_ACTION` | 2 | Acción configurada: HOLD, condicionada a habilitar el failsafe |
| `FS_OPTIONS` | 0 | Sin bits adicionales activos |

Por tanto, el perfil oficial no reacciona al heartbeat GCS perdido mediante el failsafe GCS: está deshabilitado. No se ha probado la pérdida de enlace ni se debe inferir que el rover se detenga en ese caso. ArduPilot indica que `FS_GCS_ENABLE=0` lo desactiva y que el valor 1 ejecuta `FS_ACTION`; cotejar la opción exacta con la versión SITL antes de preparar la matriz. [Guía oficial de failsafes Rover](https://ardupilot.org/rover/docs/rover-failsafes.html).

Captura y log persistidos en `../evidencias/fase4-parametros-2026-11-04/`. SHA-256: JSON `3799E8EBAC8B5CD1148747D7436D615C4BA306D6337D9F3DD83F0642F94B882F`; log SITL `D1F1D29A0F2EFF5EF2FE164B7F4A102B3E11FC259BE35A549B955B16E56EEF48`. Se confirmó al terminar que no quedaba un proceso `ardurover`.

Problemas de preparación y corrección: la primera invocación no encontraba `pymavlink`; el capturador ahora incorpora su ruta local WSL sin instalar dependencias. La siguiente ejecución llegó a leer parámetros pero falló al serializar porque la lista de interfaces estaba en otro ámbito; se obtuvo de nuevo dentro del proceso aislado. La ejecución final terminó con código 0. Esos dos intentos previos también cerraron SITL mediante el bloque de limpieza.
## Resultados F4-1…F4-3

Se ejecutaron tres misiones cortas, cada una en un namespace WSL distinto con única interfaz `lo`. En cada perfil se cargó la misma misión, se armó SITL, se pasó a AUTO, se cortó únicamente el heartbeat GCS tras alcanzar el waypoint 1, se observó 8,16 s y se reconectó enviando heartbeat sin reenviar misión ni modo. Las seis variables efectivas se leyeron por MAVLink antes del armado. En los tres casos el cierre registrado fue HOLD y desarmado.

| `FS_GCS_ENABLE` | Mensaje observado | Modo tras 8,16 s sin heartbeat | Tras reconectar | Resultado |
|---:|---|---|---|---|
| 0 | Sin `GCS Failsafe` | AUTO | AUTO | PASS |
| 1 | `GCS Failsafe` | HOLD, tras 6,0 s | HOLD | PASS |
| 2 | `GCS Failsafe`; `Failsafe - Continuing Auto Mode` | AUTO | AUTO | PASS |

Los DataFlash registraron modos 0 → 10 (AUTO) → 4 (HOLD al cierre) y 1090, 1092 y 1091 mensajes POS respectivamente. Waypoints 1 y 2 se alcanzaron durante la ventana de observación; el waypoint 3 no se alcanzó antes de finalizar cada ensayo. Son trayectorias y modos simulados.

**Ensayos descartados:** la primera pasada de perfiles 1 y 2 mostró `Radio Failsafe` antes del timeout GCS. No se contabilizó como resultado de GCS. La guía oficial para operación solo GCS explica que, sin joystick/RC overrides, se debe neutralizar el failsafe throttle y desactivar protocolos RC; se incorporaron `FS_THR_ENABLE=0` y `RC_PROTOCOLS=0` a perfiles temporales de SITL únicamente. La repetición validada no emitió `Radio Failsafe`. [Referencia oficial](https://ardupilot.org/rover/docs/common-gcs-only-operation.html).

Capturas, perfiles, eventos JSONL y DataFlash copiados en `../evidencias/fase4-gcs-2026-11-04/`. `resumen.json` marca PASS en todas las comprobaciones aplicables de cada perfil. El script reproducible de análisis es `fase4_summarize.py`; el lanzador está en `fase4_gcs_failsafe.py`. Las copias DataFlash y eventos coinciden por SHA-256 con sus originales WSL. No queda proceso `ardurover`.
## Matriz de autoridad propuesta

| Modo | Autoridad operativa prevista para el análisis | Papel del companion provisional | Pendiente de validar |
|---|---|---|---|
| MANUAL | Persona operadora mediante RC; comprobar qué enlace de piloto proporciona el SITL | Solo observación | Disponibilidad y respuesta de RC simulado |
| AUTO | ArduRover ejecuta la misión ya cargada; la estación supervisa | Solo observación | Qué hace el failsafe de estación al perder heartbeat |
| HOLD | ArduRover mantiene el comportamiento del modo HOLD | Solo observación | Persistencia del modo y efecto de recuperar el enlace |
| GUIDED | Fuente externa solicita navegación; no designar dos emisores simultáneos | Sin órdenes desde ROS/MAVROS | Diseñar un único emisor de prueba y límites de caducidad antes de probar |

La matriz es una política de trabajo para simulación, no una política aprobada para el rover. No se ha demostrado una separación de órdenes en MAVROS para hardware.

## Escenarios pendientes

| ID | Fallo que se inyectaría en SITL | Evidencia necesaria | Criterio de aceptación del ensayo |
|---|---|---|---|
| F4-0 | **Completado 2026-11-04:** arranque con perfil oficial y captura de parámetros efectivos | Versión/hash, cuatro parámetros y `armed=false`; ver JSON y log enlazados arriba | Completado: se conocen los valores del failsafe GCS cargado |
| F4-1 | **PASS:** perder heartbeat en AUTO con `FS_GCS_ENABLE=1` | Mensaje `GCS Failsafe`; cambió a HOLD a los 6,0 s del corte; DataFlash | HOLD observado con el resto de failsafes de entrada neutralizados solo en este perfil SITL |
| F4-2 | **PASS:** reconectar tras el failsafe GCS | Permaneció en HOLD durante 5 s de heartbeat restaurado; no se reenviaron misión ni modo | No hubo retorno automático a AUTO |
| F4-3 | **PASS:** comparar `FS_GCS_ENABLE` 0, 1 y 2 con acción HOLD | Tres ejecuciones aisladas, parámetros efectivos y DataFlash | 0: sigue AUTO sin evento GCS; 1: HOLD; 2: emite failsafe y continúa AUTO |
| F4-4 | **PASS (comportamiento predeterminado):** dejar de actualizar una consigna local NED de 0,35 m/s en GUIDED | Aviso de timeout tras 2,84 s, velocidad 0,459→0,024 m/s en seis segundos, servo 3 de 1509→1500; termina HOLD y desarmado | SITL emitió `target not received last 3secs, stopping` y detuvo la salida simulada. `PARAM_REQUEST_READ` no devolvió `GUID_TIMEOUT`; por tanto no se probó un valor configurable y el resultado aplica a la respuesta observada de este binario |
| F4-5 | **PASS:** dos pruebas desarmadas. Base: alternar GUIDED/HOLD/GUIDED desde SYSID 255/42/255 con solo `MAV_GCS_SYSID=42`; luego repetir filtrando con `MAV_OPTIONS=1` y rango 42…42 | HEARTBEAT confirma aceptación/ignorado por cada fuente; cierre HOLD y desarmado | Solo `MAV_GCS_SYSID`: 255 también cambia modo. `MAV_OPTIONS` bit 0: 255 queda ignorado y 42 cambia modo. El filtro de ID pasó en SITL; no equivale a autenticación criptográfica ni prueba todos los mensajes, canales o MAVROS |

No se marcará como probado un escenario que solo haya sido descrito, ni se afirmará que el rover se detiene automáticamente sin observarlo. Los errores de preparación, reinicios y resultados también deben quedar en logs de la ejecución.

## Precauciones de ensayo

- Antes de cada proceso: verificar que no exista un SITL previo, guardar hash de binario y parámetros, crear carpeta de evidencia nueva y comprobar aislamiento de red e interfaz única `lo`.
- Nunca aceptar un endpoint configurable ni permitir que un controlador de fase 4 se conecte a la Orange Pi o a un puerto serie. El objetivo es loopback del SITL aislado.
- Mantener activas las comprobaciones de armado de ArduPilot. No relajar EKF, GPS u otras comprobaciones para forzar un caso.
- Usar una sola variable de failsafe por ejecución, en un archivo temporal específico de SITL. No editar `rover-oficial-4.7.2.parm` ni aplicar estos valores al vehículo.
- Guardar eventos MAVLink y DataFlash; al acabar, comprobar proceso cerrado y estado final observado. Una orden de limpieza no acredita por sí sola que el simulador se haya detenido.
- F4-4 fue armado y controlado solo durante la prueba de velocidad en SITL; F4-5 permaneció desarmado. La autorización del usuario cubre estos ensayos F4-4/F4-5 en simulación, no hardware.

## Referencia técnica

La guía oficial de Rover indica que el failsafe GCS usa el heartbeat MAVLink; si nunca se ha conectado un GCS, permanece inactivo aunque se haya configurado. `FS_GCS_ENABLE=1` ejecuta `FS_ACTION`; el valor 2 omite el failsafe durante una misión AUTO. La guía también advierte que, al restablecer el enlace, puede ser necesario seleccionar de nuevo el modo y que el modo de failsafe no se revierte automáticamente. Estos detalles deben contrastarse con los parámetros y firmware SITL 4.7.2 realmente cargados antes de fijar expectativas.

- [ArduPilot Rover: Failsafes](https://ardupilot.org/rover/docs/rover-failsafes.html)
- [ArduPilot Rover: parámetros](https://ardupilot.org/rover/docs/parameters.html)
- [ArduPilot Rover: comandos MAVLink en GUIDED](https://ardupilot.org/dev/docs/mavlink-rover-commands.html)
- [ArduPilot: operación solo con GCS](https://ardupilot.org/rover/docs/common-gcs-only-operation.html)

## Resultados F4-4 y F4-5 — 2026-11-04

El runner reproducible `fase4_guided_authority.py` inicia cada caso en un namespace WSL independiente con `lo` como única interfaz. Binario SITL: SHA-256 `f453fd8217b9d798c873e5c424e139a2a3597b52e31658f76b2c177b523391af`. Evidencia local, eventos JSONL y perfiles en `../evidencias/fase4-guided-2026-11-04/`.

**F4-4:** con el rover simulado armado y en GUIDED, se enviaron durante 2,5 s consignas locales NED de 0,35 m/s Norte desde SYSID 255; después se dejaron de enviar por seis segundos. El último groundspeed al cortar fue 0,459 m/s. A los 2,84 s SITL notificó `target not received last 3secs, stopping`; a los seis segundos la velocidad era 0,024 m/s y la salida simulada de motor SERVO3 era 1500 (neutro). La ejecución terminó HOLD y desarmada. Todas las comprobaciones del comportamiento observado pasaron. Un intento previo consultó `GUID_TIMEOUT` pero no recibió `PARAM_VALUE`; el ensayo se adaptó al timeout predeterminado observable y no fijó dicho parámetro. La documentación oficial vigente describe `GUID_TIMEOUT` como configurable entre 0,1 y 5 s, así que la ajustabilidad de este binario sigue sin confirmar. La ventana limitada de observación y salida SITL no validan frenado, distancia ni seguridad física.

**F4-5:** primero, con el rover desarmado y solo `MAV_GCS_SYSID=42`, la secuencia SYSID 255→GUIDED, SYSID 42→HOLD, SYSID 255→GUIDED se reflejó completa; por sí solo este parámetro no bloqueó cambios de modo. Después se repitió con `MAV_OPTIONS=1`, manteniendo `MAV_GCS_SYSID=42` y `MAV_GCS_SYSID_HI=42`: SET_MODE desde 255 fue ignorado, desde 42 se aceptó y pudo seleccionar GUIDED y HOLD. En ambas ejecuciones el cierre fue HOLD y desarmado. `MAV_OPTIONS` bit 0 produjo el filtro de SYSID esperado en este SITL y estos mensajes. MAVLink SYSID es un identificador de origen declarado por el emisor; no se probó autenticidad criptográfica, otros tipos de mensaje ni varios canales/MAVROS. La primera preparación del caso filtrado se detuvo antes de la prueba porque consultas PARAM desde SYSID 255 quedaron bloqueadas; el runner repetido correctamente inicia como 42 y cambia SYSID solo en los pasos de ensayo.

Se conservaron dos intentos no válidos de preparación de F4-4: el primero se detuvo al no recibir el parámetro; el segundo alcanzó la limpieza HOLD/desarmado, pero el evaluador guardó por error la velocidad posterior como valor inicial. La repetición con medición corregida pasó y es la evidencia de resultado. F4-5 pasó a la primera. No hubo conexión a Orange Pi, H743 ni hardware; SITL quedó detenido.

El resultado combinado cierra los ensayos de fase 4 en simulación, no define una política de autoridad para Companion. El siguiente diseño deberá decidir si Companion se mantiene como observador o se crea una puerta de control con emisor único, lista cerrada de órdenes, tratamiento de caducidad y prueba de que el segundo emisor no puede ejercer autoridad. `MAV_OPTIONS` requiere evaluación adicional de identidad/autenticación, selección de canales y compatibilidad antes de considerar cualquier despliegue. Sin esa decisión no se habilitarán comandos MAVROS ni control del rover real.

## Siguiente paso

F4-0 a F4-5 están ensayados en SITL. Siguiente: conservar Companion en solo observación hasta decidir y diseñar —con el usuario— una política de autoridad y una posible puerta de control. El ensayo F4-5 demuestra que confiar solo en `MAV_GCS_SYSID` no impide a otro SYSID cambiar el modo en el escenario probado. No conectar MAVROS al hardware ni habilitar órdenes basándose en estas pruebas.




