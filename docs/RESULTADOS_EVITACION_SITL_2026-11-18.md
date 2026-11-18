# Ensayo de parada nativa en ArduRover SITL 4.7.2

Fecha: 18-11-2026. **Solo simulación**; no se modificó la Matek ni se enviaron órdenes al rover físico. Ejecutado con binario SITL oficial SHA-256 `f453fd8217b9d798c873e5c424e139a2a3597b52e31658f76b2c177b523391af`, dentro de un namespace de red WSL con únicamente loopback. Las posiciones y la misión son sintéticas.

## Método y límites

Se inyectaron mensajes MAVLink `DISTANCE_SENSOR` a 10 Hz al backend virtual `RNGFND1_TYPE=10`, con distancia fija 1,80 m y después 0,40 m; se dejó de enviar para simular pérdida de ese flujo. La H743 real usa HC-SR04 `RNGFND1_TYPE=30`, no se simularon electrónica, ecos, tasa real ni driver HC-SR04. La distancia inyectada es independiente del movimiento del rover simulado; no representa una pared geométrica y no permite calcular distancia real de frenado o colisión. El reporte `sensor` de `events.jsonl` conserva la última lectura observada: durante la etapa de pérdida puede mostrar 39 aunque ya no lleguen nuevas.

Configuración experimental leída de vuelta en SITL: `PRX1_TYPE=4`, `AVOID_ENABLE=2`, `AVOID_MARGIN=1 m`, `AVOID_BACKUP_SPD=0`, `OA_TYPE=0`, `FS_GCS_ENABLE=0`, `FS_THR_ENABLE=0`, `ARMING_CHECK=0`, rango 0,2–2 m. No son recomendaciones de valores reales. La lectura de 0,40 m apareció como 39 cm por conversión interna. Se mantuvo una estación de control simulada activa; el companion simulado era otra identidad MAVLink, no una ejecución real de ROS/MAVROS. Al perderlo se interrumpió su heartbeat y, en GUIDED, las consignas de velocidad; el sensor simulado siguió enviando. No se probó la pérdida de una conexión física UART ni el failsafe de estación GCS.

La distancia de frenada que Juan ya comunicó en la ficha del AX10, **30–40 mm** después de poner `MOT_SLEWRATE=0`, es una observación real disponible. Debe conservarse como tal; velocidad, superficie, pendiente y repeticiones no se registraron, por lo que esta simulación no permite extrapolarla a otras condiciones ni fijar por sí sola el margen de detección.

## Resultados observados

| Modo | Obstáculo virtual frontal | Flujo de sensor interrumpido |
|---|---|---|
| MANUAL | Continuó avanzando con la orden RC, como describe la documentación. | Continuó avanzando. |
| STEERING | Desde ~0,47 m/s pasó a ~0,03 m/s y throttle 1500 durante el obstáculo. | Pasó a ~0,48 m/s al mantenerse la orden RC; se reanudó el avance. |
| ACRO | Desde ~0,47 m/s pasó a ~0,03 m/s y throttle 1500. | Volvió a ~0,47 m/s al mantenerse la orden RC. |
| SIMPLE | Desde ~0,50 m/s pasó a ~0,03 m/s y throttle 1500. | Volvió a ~0,51 m/s al mantenerse la orden RC. |
| GUIDED, consigna de velocidad | Desde ~0,47 m/s pasó a ~0,03 m/s y throttle 1500. | Volvió a ~0,48 m/s al mantenerse la consigna. |
| AUTO, misión alojada | Desde ~0,22 m/s pasó a ~0,03 m/s y throttle 1500, con `OA_TYPE=0` en esta prueba. | Reanudó la misión y aceleró; los valores de velocidad SITL no son los del AX10 real. |
| RTL | Desde ~0,20 m/s pasó a ~0,04 m/s y throttle 1500. | Reanudó el movimiento hacia casa. |
| SMART_RTL | Alcanzó ~0,04 m/s y throttle 1500 tras una transición oscilatoria. | Reanudó el movimiento por la ruta almacenada. |
| HOLD | Permaneció prácticamente parado; ya estaba parado al presentar el obstáculo. | No probado separadamente; no demuestra frenado en marcha. |
| LOITER | Se activó desde RTL en movimiento y presentó una respuesta oscilatoria antes de reducirse la velocidad. | No probado; ensayo no aislado y no concluyente para evitación. |

Las velocidades residuales son lecturas de `VFR_HUD.groundspeed` de la simulación; no se afirman medidas físicas ni tiempos de parada certificados. Una ejecución por caso no demuestra fiabilidad estadística. En STEERING, ACRO, SIMPLE, GUIDED, AUTO, RTL y SMART_RTL, al desaparecer el flujo, la respuesta observada no mantuvo la parada mientras seguía activa una orden o misión. La fuente/identidad era un sensor MAVLink simulado: hay que comprobar por separado qué ocurre con fallos del HC-SR04 y su driver físico.

En GUIDED al detenerse la emisión de las consignas del companion, manteniendo estación y sensor simulados, SITL emitió `target not received last 3secs, stopping` y se detuvo; siguió en GUIDED y armado. Esto no es una prueba genérica de todos los tipos de consigna ni del failsafe físico del companion. En AUTO, tras dejar de emitir el heartbeat del companion, la misión permaneció en el autopiloto y continuó; `FS_GCS_ENABLE=0` y la estación simulada seguía enviando heartbeat. No prueba pérdida total de comunicaciones.

## Conclusión y desarrollo pendiente

La evitación simple nativa mostró una reacción de parada en las situaciones anteriores, incluso en AUTO y RTL con `OA_TYPE=0`; esto matiza la lectura de la documentación general y no garantiza lo que ocurrirá en todos los casos. **La pérdida del flujo de proximidad permitió continuar** en la configuración simulada. Conviene diseñar y probar una política explícita de sensor ausente o inválido (por ejemplo, limitar o parar en modos autónomos), sin tratar la ausencia de eco como espacio despejado. No activar la protección en la Matek hasta decidir esa política y repetir los ensayos físicos acordados.

Quedan por evaluar pérdida de sensor físico/ausencia de eco real, datos congelados o inválidos, recuperación, fuente de proximidad compartida, pérdida conjunta de UART/GCS, distintas consignas y control de velocidad, y pruebas repetidas con una pared geométrica. FOLLOW y otros modos especiales no se han ensayado. La prueba LOITER no separó adecuadamente su propio frenado de la reacción al obstáculo.

## Reproducir y evidencias

`scripts/sitl/evitacion_sitl.py` comprueba hash y ejecuta dentro de `unshare -Urn` solo con loopback. En WSL: `python3 /mnt/c/RRA/scripts/sitl/evitacion_sitl.py` (MANUAL/STEERING/ACRO/GUIDED/HOLD); `RRA_TEST_CASE=auto python3 /mnt/c/RRA/scripts/sitl/evitacion_sitl.py` (AUTO/RTL/LOITER); `RRA_TEST_CASE=extra python3 /mnt/c/RRA/scripts/sitl/evitacion_sitl.py` (SIMPLE/SMART_RTL). Se versionan parámetros, eventos y log del firmware en [`evidencias/evitacion-sitl-20261118/`](evidencias/evitacion-sitl-20261118/); las copias locales completas, incluidos los DataFlash, están en `codex_handoff/evidencias/evitacion-sitl-20261118/`. Ejecuciones: `prueba-jvo2ik8f`, `prueba-krz9te8j` y `prueba-x4_ot22b`. El primero usó el campo de tipo de sensor MAVLink 0; los otros 1 (ultrasonido). En todos el backend fue MAVLink simulado.

Referencia: [evitación simple de ArduPilot](https://ardupilot.org/rover/docs/common-simple-object-avoidance.html).
