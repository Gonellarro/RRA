# RRA: protección de batería de electrónica 2S

Paquete ROS 2 + ArduPilot Lua para alertar de tensión baja, pedir un apagado Linux ordenado y controlar el OFF del Pololu. Los valores predeterminados del código son corte deshabilitado y `DRY_RUN=1`.

**Rover RRA, estado confirmado el 18-11-2026:** Pololu OFF conectado a S12/GPIO61; `RBP_CUT_EN=1`, `RBP_CUT_GRACE=12`, `RBP_CUT_WAIT=25` y servicio permanente de la Pi `RRA_POWER_SHUTDOWN_DRY_RUN=0`. Con tensión simulada se comprobó el apagado de Linux y el corte físico; tras esperar, el usuario encendió el sistema a la primera. Los [registros seleccionados de la prueba](../../docs/evidencias/pololu-20261118/) se comparten en el repositorio. No se ha provocado una descarga real. Los umbrales son 7,4 V/10 s (aviso), 7,3 V/10 s (solicitud) y 7,2 V/5 s (crítico). Mantener avisador por celda. Las secciones de ensayos con fechas anteriores son historial y no reflejan necesariamente los parámetros actuales.

## Estado actual

**Reintentos corregidos:** el campo MAVLink `confirmation` queda limitado a 255 y el Lua sigue reintentando hasta recibir ACK. Una prueba local ejecuta el Lua con más de 255 envíos simulados y un ACK tardío; la desconexión física prolongada sigue pendiente.

- Modelo Python filtrado: 20 muestras de historial, mediana de cinco y EMA de 2 s, tiempos monotónicos, validación de lecturas, histéresis y estados enclavados.
- Veintitrés pruebas locales con lupa disponible: modelo, Lua, corte, framing, payload, checksum y validación de endpoints/voltajes. Las pruebas Lua se omiten si falta lupa.
- El script Lua realiza las mediciones y el filtrado en el autopiloto, detecta aviso y umbrales de apagado, y envía `COMMAND_LONG` dirigido a `1/191` por el canal MAVLink donde recibe el heartbeat del Companion.
- La Orange Pi recibe `/uas1/mavlink_source` y publica respuestas a `/uas1/mavlink_sink` mediante los tópicos raw de MAVROS ya usados por el rover. No abre otro lector para `/dev/ttyS5`.
- Protocolo: `MAV_CMD_WAYPOINT_USER_1` (31000) solicita apagado y lleva un nonce + tensiones; el Companion persiste evento JSONL, devuelve `COMMAND_ACK`, luego envía `MAV_CMD_WAYPOINT_USER_2` (31001) como aviso `PREPARED_TO_POWER_OFF`. Lua valida origen `1/191` y nonce y confirma con `COMMAND_ACK`. En modo real, el servicio ordena `sudo -n systemctl poweroff` tras ese ACK; si no llega ACK de preparación, aplica timeout corto y solicitaría el apagado igualmente cuando `DRY_RUN=0`.
- El ACK ordinario confirma recepción/aceptación del frame. `PREPARED` indica que el registro quedó persistido y el servicio está listo para iniciar el cierre; no demuestra que Linux haya terminado. `PREPARED.param2` indica 0 en DRY_RUN y 1 en modo real. El Lua bloquea el corte si recibe explícitamente el estado de simulación. En el RRA se esperan 12 segundos desde PREPARED real o un máximo de 25 segundos desde la condición crítica, lo que ocurra antes; el corte físico está habilitado.
- Unidad systemd `rra-power-shutdown.service` instalada y habilitada en la Orange Pi con `RRA_POWER_SHUTDOWN_DRY_RUN=0`. Se ejecuta como usuario `rra` para compartir el grafo ROS con MAVROS. El apagado real usa `sudo -n systemctl poweroff`. MAVROS real conectó a la H743 y los endpoints raw coinciden en QoS BEST_EFFORT; el listener ya recibe heartbeats físicos.
- `rra-mavros.service` está habilitado para UART5/57600. Se verificaron arranque tras reinicio y recuperación ante un proceso MAVROS detenido; el receptor solicita recuperación tras 120 s sin tramas válidas de la FCU. Una prueba posterior con origen Lua y voltaje simulado confirmó apagado Linux y corte Pololu; el servicio habitual quedó en modo real.

## Umbrales iniciales

| Nivel | Condición filtrada sostenida | Respuesta en esta fase |
|---|---:|---|
| Preventivo | ≤7,4 V durante 10 s | `STATUSTEXT` WARNING para Mission Planner/QGC |
| Apagado ordenado | ≤7,3 V durante 10 s | Solicitud MAVLink al Companion |
| Apagado urgente | ≤7,2 V durante 5 s | Solicita cierre inmediatamente, sin esperar los 10 s anteriores |
| Emergencia profunda | ≤7,0 V durante 1 s instantáneo | Deshabilitada por defecto; requiere revisión/validación |

Mediana-5 + EMA 2 s mitigan caídas breves; además cada condición requiere permanencia. Histéresis inicial: 0,10 V y 3 s de recuperación. Una lectura inválida o cero aislado no significa batería descargada; la pérdida persistente genera `SENSOR_FAULT` y **no** inventa un voltaje.

Una caída rápida bajo 7,2 V durante 5 s no puede esperar a que transcurran 10 s de 7,3 V: Lua manda la solicitud urgente al completar esos 5 s. La Pi no se apaga por una frase STATUSTEXT; solo responde al `COMMAND_LONG` validado por IDs, destino, nonce y tensiones plausibles.

## Protocol frame contract

- FCU system/component: `1/1`; Companion: `1/191` (MAVROS informó `MY ID 1.191, TARGET ID 1.1`). Revalidar en el enlace activo antes de instalar.
- Request `COMMAND_LONG`: command 31000, target `1/191`, `param1=nonce` (24-bit entero exacto en float), `param2=tensión filtrada V`, `param3=tensión instantánea V`, `param4=1` versión.
- Companion `COMMAND_ACK` a la petición: se envía después de escribir y `fsync` del evento.
- READY `COMMAND_LONG`: command 31001 a `1/1`, `param1=nonce`, `param2=0` en simulación y `param2=1` en modo real.
- FCU `COMMAND_ACK` del READY: solo se acepta si source `1/191` y nonce coincide con la solicitud pendiente.
- Reintentos son idempotentes durante la vida del proceso: los nonces repetidos reciben ACK pero no duplican la acción. Se rechazan emisores/destinos no esperados y voltajes fuera de 5–9 V.
- Modo por defecto `RRA_POWER_SHUTDOWN_DRY_RUN=1`: persiste/loguea y simula ACK, READY y apagado; nunca invoca `systemctl poweroff`.

## Pruebas locales

Desde la raíz de `C:\RRA` en PowerShell:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src\rra_battery_protection).Path
python -m compileall -q .\src\rra_battery_protection
python -m unittest discover -s .\src\rra_battery_protection\test -v
python .\src\rra_battery_protection\scripts\simulate_voltage.py all
```

No hace falta ROS para estas pruebas y no se conecta con el rover.

Prueba ROS aislada disponible en la Orange Pi (solo con overlay fuente):

```bash
bash ~/rra_ws/src/rra_battery_protection/scripts/test_protocol_on_pi.sh
```

Esta prueba inyecta mensajes MAVLink sintéticos a través de los topics ROS locales, verifica ACK, nonce, READY y evento JSONL, y exige `DRY_RUN=1`. No inicia MAVROS ni contacta con la Matek.

La prueba anterior en DRY_RUN es histórica: en la Pi del RRA el servicio permanente se dejó con `DRY_RUN=0` tras la prueba física autorizada.

## Instalación inicial en Pi: solo simulación

Para una instalación nueva requiere el paquete copiado a `~/rra_ws/src/rra_battery_protection`, ROS 2 Lyrical, workspace `~/rra_ws` y MAVROS en dominio ROS 205 con los dos tópicos `/uas1/mavlink_*`. Ejecutar como usuario `rra`:

```bash
bash ~/rra_ws/src/rra_battery_protection/scripts/install_dry_run_on_pi.sh
```

El script compila, verifica topics, instala la unidad, crea `/etc/default/rra-power-shutdown` con `DRY_RUN=1` y habilita el observador. En esta Pi, la unidad ya está instalada y habilitada en modo real; este instalador es para una instalación nueva en simulación. Para revisar:

```bash
sudo systemctl status rra-power-shutdown --no-pager
sudo journalctl -u rra-power-shutdown -f
```

Parada/reversión de esta unidad:

```bash
sudo systemctl disable --now rra-power-shutdown.service
sudo rm /etc/systemd/system/rra-power-shutdown.service /etc/default/rra-power-shutdown
sudo systemctl daemon-reload
```

Para una instalación nueva, validar el montaje antes de activar modo real. En el RRA actual el Pololu está instalado y la activación real fue autorizada y probada con tensión simulada.

## ArduPilot y límites antes de cargar Lua

El firmware reportado es ArduRover 4.7.2, commit `fb773567`. La lista oficial `Rover/stable-4.7.2/MatekH743/features.txt` confirma `AP_SCRIPTING_ENABLED`, `AP_SDCARD_STORAGE_ENABLED` y filesystem; este build incluye scripting. La lectura anterior mostró `SCR_ENABLE=0` y no incluyó `SCR_HEAP_SIZE`, coherente con la documentación: hay que habilitar scripting y refrescar/reiniciar la lista para ver los demás parámetros `SCR_*`. El 15 de noviembre, MAVROS conectó correctamente en UART5 a 57600 (`connected=true`, desarmado, HOLD), y el servicio MAVROS completó un pull de 1150 parámetros (`success=true`). La exportación local del snapshot falló cuando SSH volvió a agotar el tiempo de espera; no se escribió ningún parámetro y no se cargó Lua. El servicio de protección se confirmó activo en `DRY_RUN=1` antes de esta interrupción. Próximo paso al recuperar SSH: guardar snapshot de parámetros, comprobar `SCR_ENABLE`, habilitarlo si sigue en 0, refrescar parámetros `SCR_*` y revisar heap/SD; sin GPIO ni corte.

Prueba física de enlace 2026-11-14: MAVROS conectó por `/dev/ttyS5:57600`, `MY ID 1.191`, `TARGET ID 1.1`; `/mavros_node/state` informó conectado, desarmado y HOLD, y `/mavros_node/battery` informó 7,633 V. El servicio systemd DRY_RUN está activo, con endpoint subscriber a `/uas1/mavlink_source` BEST_EFFORT, compatible con MAVROS. El perfil temporal usado para leer parámetros incluyó `param` y `ftp`, sin efectuar ningún set ni operación FTP; se restauró la allowlist original y ambos plugins vuelven a estar excluidos.

La batería se vio simultáneamente en 7,89 V multímetro y 7,854 V ArduPilot; no valida la lectura bajo transitorios. La H743 tiene un límite de entrada publicado de 6,8 V; 7,2 V deja 0,4 V nominales. Medir BAT de la controladora y 5 V de la Orange Pi con registrador/osciloscopio mientras se mueve el MG995 antes de poner umbrales reales. Los niveles deberán ajustarse al pack final, la química, tensión por celda y respuesta dinámica.

## Historial del Pololu y la salida S12 (2026-11-18, anterior a la activación)

El Pololu está en la alimentación de electrónica. El usuario conectó su entrada OFF al pad S12 y después retiró ese cable para probar el GPIO. La Matek confirmó `SERVO12_FUNCTION=-1`, `RELAY1_FUNCTION=1`, `RELAY1_PIN=61`, `RELAY1_DEFAULT=0`, `RELAY1_INVERTED=0`. Sonar en GPIO54. El Lua está desplegado con `RBP_CUT_EN=0`, `RBP_CUT_WAIT=20`, `RBP_CUT_GRACE=5` y `RBP_EMERGEN=0`. El protocolo simulado 7,1 V confirmó solicitud y PREPARED de DRY_RUN, y el Lua informó bloqueo de corte; no se ha aplicado señal a OFF ni validado el corte físico.

Para completar: medir S12 respecto a GND en reposo y durante el pulso con OFF desconectado; verificar masa común, pin físico y ausencia de realimentación; probar Pololu y enclavamiento con carga de prueba; revisar retardo de apagado de Linux y alimentación bajo carga. `RBP_CUT_EN=1` se lee al arrancar y habilita corte después de reiniciar la FCU; antes de ponerlo a 1 deben completarse las pruebas y dejar el Companion en modo real. Una ausencia de PREPARED causa el corte tras el plazo de respaldo, aun sin confirmación del Companion. Los 5 s desde PREPARED son una gracia, no confirman que Linux haya terminado. La desconexión física requiere pruebas de campo y no sustituye el avisador por celda.

Actualización 2026-11-15: snapshot previo de 1150 parámetros guardado en `codex_handoff/evidencias/battery-protection-2026-11-15/matek-params-pre-scripting.yaml`; `SCR_ENABLE` seguía en 0. Por MAVFTP se abrieron en lectura `@SYS/uarts.txt` y `@PARAM/param.pck`, pero MAVROS devolvió `Incorrect list entry` y errno 34 al listar `/`, `/APM` y `/APM/scripts`. Esto no permite determinar el contenido de la tarjeta ni concluir que esté ausente. El script no se ha instalado ni ejecutado. El servicio de apagado continúa en DRY_RUN y la sesión temporal MAVROS se cerró.

Actualización posterior 2026-11-15: el cliente oficial pymavlink MAVFTP listó correctamente la tarjeta; `/APM` contenía `LOGS` y `STRG_BAK`, sin carpeta `scripts`, y `@ROMFS/scripts` no existía. Se activó `SCR_ENABLE=1` (confirmado), con `SCR_HEAP_SIZE=204800` y `SCR_DIR_DISABLE=0`. Se instalaron el monitor Lua y los cuatro módulos MAVLink del commit exacto `fb773567896014da007bca58358704d4a0d8516f`. Tras reiniciar la FCU desarmada, apareció `RRA: monitor bateria Lua iniciado; sin corte fisico`; `RBP_WARN_V=7.4`, `RBP_SHUT_V=7.3`, `RBP_EMERGEN=0`. No se observaron errores Lua en los 25 s de captura. El Companion permanece en DRY_RUN. No se ha validado aún una transición por baja tensión ni el protocolo completo Lua-Companion; no hay control GPIO en el Lua. MAVROS no quedó arrancado automáticamente. Para retirar el monitor: desactivar `SCR_ENABLE` y reiniciar, o retirar el script de `/APM/scripts` mediante MAVFTP y reiniciar scripting.

Prueba adicional de la misma sesión: el launch habitual de MAVROS, iniciado temporalmente, publicó conexión real `connected=true`, FCU desarmada y batería 7,885 V; los tópicos `/uas1/mavlink_source` y `/uas1/mavlink_sink` estaban presentes y el servicio seguía activo en DRY_RUN. Esto no demuestra todavía un intercambio de solicitud/ACK desde Lua. El launch temporal termina por timeout y no instala arranque automático.

Corrección posterior 2026-11-15: se adaptó `mavlink:send_chan` a los tres argumentos definidos en el binding del firmware instalado. Los temporizadores pendientes ahora se reinician cuando la lectura filtrada supera el umbral o una muestra es inválida; la recuperación del aviso usa histéresis durante tres segundos. Las 15 pruebas locales pasan. Se subió el Lua corregido y su CRC MAVFTP `56e97992` coincide con el archivo local (CRC de ArduPilot). Tras reiniciar la FCU desarmada, se recibió el mensaje de inicio y no se observaron errores Lua durante 20 s. El intercambio de apagado desde el Lua queda por comprobar en modo simulado.

Prueba física de protocolo en DRY_RUN 2026-11-15: variante temporal del Lua con una sola inyección simulada de 7,1 V, activada por `SCR_USER1=987`, que el propio Lua restableció a 0 antes de simular. El primer intento no obtuvo ACK: el servicio estaba activo, pero su proceso ROS no estaba recibiendo tráfico; al reiniciarlo se verificó recepción MAVLink real. Segundo y tercer intentos: la FCU emitió solicitud real, el servicio registró los valores simulados (nonce 13018 y 13521, registros del 15 de noviembre a las 21:33 y 21:35 UTC, respectivamente), y la FCU informó haber recibido el ACK. El servicio agotó su plazo de 3 s esperando ACK de PREPARED y simuló el apagado por timeout; la confirmación de preparación no quedó validada. Se restauró el Lua normal con CRC MAVFTP `56e97992`, `SCR_USER1=0`, reinicio de FCU y mensaje de inicio normal. El servicio permanece DRY_RUN, sin GPIO. El JSONL contiene eventos de prueba, no descargas reales. El launch MAVROS usado era temporal y no quedó instalado como servicio de arranque. La disponibilidad continua del servicio ROS tras reconexiones queda por investigar.

Prueba física completa 2026-11-15 22:52 CET: corregida la construcción MAVLink 2 del Companion para recortar ceros finales antes de calcular el CRC; también se admite la recepción de COMMAND_LONG con el byte final omitido. El código corregido fue compilado y desplegado en la Pi. Con una inyección temporal de 7,1 V en Lua, nonce 13518, se observó solicitud Lua, registro y ACK en Companion, mensaje `TEST RX cmd=31001`, confirmación de preparación desde la Matek y `DRY_RUN: poweroff simulado`. La tensión de 7,1 V era simulada; el evento JSONL de las 21:52 UTC es de prueba. El Lua normal se restauró (CRC MAVFTP `56e97992`), SCR_USER1 volvió a 0 y la FCU reinició mostrando inicio normal. La unidad continúa DRY_RUN; MAVROS era temporal y no arranca automáticamente. Queda pendiente investigar la pérdida anterior de recepción ROS y verificar reconexión continuada antes de activar el apagado real o el Pololu.

### Arranque automático de MAVROS y recuperación (15-11-2026)

La Pi tiene habilitados `rra-mavros.service` y `rra-power-shutdown.service`. MAVROS usa UART5 a 57600 y `/etc/rra/mavros_hardware.yaml` (copia versionada en `config/mavros_hardware.yaml`), el perfil ROS 205 y la lista de plugins existente; el servicio de batería está en DRY_RUN. Estas unidades no arrancan el observador `rra_telemetry`. El servicio de batería ya no espera a Wi-Fi o `network-online.target`; `PartOf` propaga el reinicio de MAVROS.

Se verificaron un reinicio manual de MAVROS, la terminación de su proceso y un reinicio completo de la Pi: systemd arrancó los servicios y el receptor recibió tramas FCU. En otro reinicio ambos servicios arrancaron pero UART dio tramas anómalas sin heartbeat; un reinicio de MAVROS recuperó el enlace. Por ello el receptor reinicia MAVROS y su propio servicio cuando no recibe tramas válidas de FCU 1.1 durante 120 s, salvo durante una solicitud de apagado pendiente. Si la FCU está apagada se repetirá la recuperación cada 120 s; la ausencia de tramas no identifica por sí sola la causa. El 15 de noviembre se redujo temporalmente el temporizador ROS a 5 s: la ausencia de tramas provocó reinicio de ambos servicios, heartbeat y recepción restaurados; tras reiniciar volvió al valor 120 s. La evidencia no prueba estabilidad frente a un corte de alimentación de la Pi ni la reconexión de UART bajo todas las condiciones.

Instalación para esta Pi: copiar `config/mavros_hardware.yaml` a `/etc/rra/mavros_hardware.yaml`, instalar `rra-mavros.service` y `rra-power-shutdown.service` en `/etc/systemd/system/`, ejecutar `systemctl daemon-reload` y habilitar ambas unidades. Requiere el overlay `~/rra_ws/install`, MAVROS, los plugins del perfil y el UART configurado. Mantener `/etc/default/rra-power-shutdown` con `RRA_POWER_SHUTDOWN_DRY_RUN=1`. La recuperación usa `sudo -n systemctl --no-block restart rra-mavros.service`; depende de la autorización sudo existente para `rra`.

Para revertir el arranque automático: `sudo systemctl disable --now rra-mavros.service` detiene también el receptor por `PartOf`; restaurar la unidad anterior desde `/etc/systemd/system/rra-power-shutdown.service.pre-mavros.bak`, ejecutar `sudo systemctl daemon-reload` y arrancar la unidad anterior si se desea. Esto no modifica parámetros de la Matek.


### Reintento al recuperar el Companion (15-11-2026)

El Lua ya no considera confirmado un apagado tras cinco intentos sin ACK. Mantiene el nonce y reintenta cada segundo durante los primeros cinco envíos y cada cinco segundos después, hasta recibir ACK; la ausencia se anuncia una sola vez. Solo acepta un ACK después de haber enviado la solicitud. Se garantiza que el nonce no sea cero.

Prueba en hardware con tensión simulada 7,1 V y DRY_RUN: el receptor estuvo detenido desde antes de la petición de las 23:10:03 CET; a las 23:10:08 la Matek indicó que continuaba reintentando. Tras arrancar el receptor, a las 23:10:47 recibió el nonce 12520; a las 23:10:48 Matek y Companion completaron recepción y PREPARED y a las 23:10:50 el Companion simuló el apagado. No era una descarga real. Se restauró el Lua de lectura real, CRC MAVFTP `2800f50f` coincidente con el archivo local, SCR_USER1=0; se reinició la FCU y se arrancaron los servicios MAVROS y receptor, que recuperaron heartbeat y tramas reales. El JSONL de las 22:10 UTC contiene el evento simulado. La recuperación tardía se probó con el receptor detenido, no con todos los posibles tipos de desconexión de UART o caída de alimentación.

### Ensayo de apagado real Linux iniciado (15-11-2026)

Por autorización expresa se inició un receptor temporal en modo real y ROS_DOMAIN_ID=206 con tópicos `/rra_real_shutdown_test/source` y `/rra_real_shutdown_test/sink`, aislados del MAVROS físico. Se inyectó una solicitud ROS sintética de 7,25/7,24 V y se simuló la respuesta de la FCU; no se modificaron umbrales ni se descargó batería. El listener registró en `/home/rra/rra_ws/logs/power-real-test-20261115.jsonl` el nonce 12345, `dry_run=false`; el test informó ACK y PREPARED y el listener confirmó PREPARED simulado. Después del plazo de 8 s SSH dejó de responder. Esto es compatible con apagado, pero falta reiniciar la Pi y recuperar el log persistente `/home/rra/rra_ws/logs/power-real-test-20261115.log` y el nuevo boot_id para verificar el resultado. El servicio permanente conservó `/etc/default/rra-power-shutdown` con `RRA_POWER_SHUTDOWN_DRY_RUN=1`. El texto `Matek confirmó` de este ensayo se refiere a la respuesta sintética, no a una Matek física. Boot previo: `184c50e0-5e06-4b67-95e8-c009835a4f8b`.

Resultado del ensayo real: el registro persistente recoge `Solicitado apagado ordenado Linux nonce=12345`; el journal del arranque anterior muestra `Finished systemd-poweroff.service - System Power Off` y `Shutting down`. Tras reconectar la alimentación, el boot_id cambió a `d4a1b830-abc4-4db4-be19-5fd03f969c27` y arrancaron automáticamente MAVROS y el receptor, con heartbeat de la FCU y tramas reales. El servicio permanente sigue con `RRA_POWER_SHUTDOWN_DRY_RUN=1`; el receptor temporal real no se ha instalado como servicio ni persiste tras reiniciar. La petición y el PREPARED de esta prueba fueron sintéticos y aislados; previamente el intercambio Lua–Companion se comprobó en DRY_RUN. No se ha hecho aún una prueba de apagado real originada por el Lua físico. Evidencias en `codex_handoff/evidencias/battery-protection-2026-11-15/` (archivos `power-real-test-20261115.*`, `rra-real-poweroff-journal.txt` y `rra-after-poweroff-journal.txt`).

### Corrección del contador y apagado real solicitado por la Matek (2026-11-18)

El contador de reintentos se satura en 255, manteniendo reintentos cada cinco segundos. Con lupa se ejecutó el Lua real en un entorno simulado durante 330 iteraciones de 5 s; hubo más de 255 envíos sin desbordamiento y se aceptó un ACK tardío. Pasaron las 17 pruebas locales. No se ha mantenido la desconexión física durante ese intervalo.

Por autorización del usuario se usó una variante temporal de una sola activación mediante `SCR_USER1`; simuló una lectura de 7,1 V en Lua y puso el disparador persistentemente a cero. El Lua de la Matek envió la petición real por MAVROS a un receptor temporal en modo real, que registró nonce 24470; hubo ACK, PREPARED confirmado y se ordenó `systemctl poweroff`. El journal del arranque anterior confirmó `systemd-poweroff.service` y `poweroff.target`; el usuario reconectó alimentación y la Pi arrancó de nuevo. La tensión era simulada, el intercambio y el apagado fueron reales. Las evidencias locales están en `codex_handoff/evidencias/battery-protection-2026-11-18/`.

Se subió el Lua definitivo de lectura real y se comprobó CRC local y MAVFTP `55f6e123`, `SCR_USER1=0` y mensaje de inicio normal tras reiniciar la FCU. MAVROS y el receptor se reactivaron; heartbeat y tramas de FCU confirmados. El servicio permanente sigue en `DRY_RUN=1`; no se activó GPIO ni el control OFF del Pololu. La prueba no equivale a validar corte físico ni a ensayar una descarga real.

### Prueba física Pololu iniciada (2026-11-18, pendiente de comprobar)

El usuario reconectó OFF a S12, omitió la medición de nivel alto y autorizó la prueba conjunta real. Se preparó una variante Lua temporal de un solo disparo: `SCR_USER1` se restablece persistentemente a 0 antes de activar una tensión simulada de 7,1 V; activa el corte solo durante ese arranque, sin cambiar `RBP_CUT_EN=0`. Para el ensayo se ajustaron solo en la variante temporal una gracia de 12 s desde PREPARED y un plazo de respaldo de 25 s desde la condición crítica. La variante pasó una prueba local del pulso y la gracia. El receptor temporal se ejecutó en modo real; el servicio permanente conserva DRY_RUN=1.

Al iniciar, la Matek informó `RRA TEST: 7.1V; corte real una vez` y `corte habilitado`. MAVROS recibió heartbeat y la Matek anunció solicitud a 7,10 V. Posteriormente SSH dejó de responder. Falta recuperar la alimentación y revisar `/home/rra/rra_ws/logs/power-pololu-realtest-20261118.log`, `power-pololu-realtest-20261118.jsonl`, `mavros-pololu-realtest-20261118.log` y journal previo, así como la observación del Pololu. No se puede afirmar todavía que Linux terminara antes del corte ni que OFF funcionara. Tras restablecer energía, restaurar el Lua normal desde el repositorio, verificar CRC y `SCR_USER1=0`, reiniciar la Matek y confirmar `RBP_CUT_EN=0` y servicios en DRY_RUN. La variante actual no reactivará el ensayo al reiniciar si el disparador se restableció correctamente.

Resultado de la prueba física comunicado por el usuario: se apagó toda la electrónica, pero al reactivar el Pololu el sistema volvió a apagarse una vez; tras una segunda reactivación quedó funcionando. La causa del segundo apagado no está determinada; una señal OFF aún activa, una alimentación residual o un transitorio son hipótesis que requieren comprobación. La secuencia del primer ensayo sí quedó registrada: solicitud Lua 20:42:59–20:43:01, PREPARED 20:43:02, orden Linux 20:43:04 y `poweroff.target` 20:43:07 CET. El tiempo real del pulso OFF no quedó registrado por la Pi, ya apagada; la desconexión la reporta el usuario.

Tras recuperar SSH se leyeron `SCR_USER1=0`, `RBP_CUT_EN=0`, relé inicial e inversión a 0 y FCU desarmada. Se restauró el Lua normal en SD (CRC MAVFTP `7d2daa60`) y se recargó scripting con `MAV_CMD_SCRIPTING/STOP_AND_RESTART`, sin reiniciar FCU ni accionar el relé; el mensaje confirmó `corte deshabilitado`. Los servicios MAVROS y receptor se dejaron activos y el receptor en DRY_RUN=1. Las evidencias de esta prueba están en `codex_handoff/evidencias/pololu-s12-2026-11-18/`. No activar el corte automático hasta investigar y resolver el segundo apagado, verificar los estados en arranque y comprobar el cableado definitivo.

Investigación posterior: el usuario desconectó S12 de OFF. Con el cable desconectado se reinició la FCU y se confirmó `SCR_USER1=0`, `RBP_CUT_EN=0`, relé inicial no invertido y `RELAY_STATUS` bajo. Una orden temporal de ciclo de relé fue aceptada y RELAY_STATUS indicó 0 → 1 → 0; al finalizar seguía bajo. Esta lectura verifica el estado lógico informado por la FCU, no mide la tensión física ni explica por sí sola el segundo corte. Permanecen por comprobar el tiempo antes de reactivar Pololu y posibles fuentes USB o realimentación. OFF sigue desconectado; los dos servicios se reactivaron en DRY_RUN.

## Activación real de protección 2S — 18-11-2026

- Segunda prueba física con tensión simulada de 7,1 V y S12 conectado a OFF: la Matek envió la solicitud, el Companion confirmó PREPARED y systemd alcanzó `poweroff.target` a las 22:00:25; el usuario confirmó que el sistema volvió a encender a la primera tras esperar. Registros `codex_handoff/evidencias/pololu-s12-2026-11-18/power-pololu-repeat-20261118.*`. La tensión inyectada es simulada, no una descarga real.
- Se restauró el Lua normal por MAVFTP, CRC `7d2daa60`, y `SCR_USER1=0`. `RBP_CUT_EN=1`, `RBP_CUT_GRACE=12`, `RBP_CUT_WAIT=25`, `RBP_EMERGEN=0`; el script confirmó inicio con corte habilitado. Umbrales y confirmaciones leídos: aviso 7,4 V/10 s, apagado 7,3 V/10 s, crítico 7,2 V/5 s. Valor de batería observado antes de habilitar: 7,841 V.
- Relay: `SERVO12_FUNCTION=-1`, `RELAY1_FUNCTION=1`, `RELAY1_PIN=61`, `RELAY1_DEFAULT=0`, `RELAY1_INVERTED=0`. En la Orange Pi, `/etc/default/rra-power-shutdown` tiene `RRA_POWER_SHUTDOWN_DRY_RUN=0`; `rra-mavros.service` y `rra-power-shutdown.service` quedaron activos y habilitados, con recepción MAVLink real. Copia anterior de configuración: `/etc/default/rra-power-shutdown.before-real-20261118`.
- El corte sucede tras 12 s de PREPARED real o al cumplirse 25 s desde la confirmación crítica, lo que ocurra antes. PREPARED confirma preparación, no que Linux haya terminado; el límite puede cortar antes de acabar el cierre. Si no existe telemetría válida no se inventa tensión ni se garantiza protección. Solo se mide tensión total: mantener el avisador por celda. No se ha probado un ciclo de descarga real ni el funcionamiento bajo fallo de comunicación en esta activación permanente.
- En la primera prueba hubo un segundo corte al reencender cuya causa no se investigó a petición del usuario; en la segunda, después de esperar unos 15 s, el usuario confirmó arranque estable a la primera. Queda pendiente caracterizar ese comportamiento si reaparece y validar estabilidad con movimientos del servo y tensión de alimentación.
