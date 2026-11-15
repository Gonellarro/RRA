# RRA: protección de batería de electrónica 2S

Paquete ROS 2 + ArduPilot Lua para alertar de tensión baja y pedir a la Orange Pi un apagado Linux ordenado. **La versión actual no acciona salidas GPIO ni corta la batería.** El nodo Companion tiene `DRY_RUN=1` por defecto. El apagado real solo ocurre si un operador cambia esa variable a `0` en systemd.

## Estado actual

**Pendiente antes de activar el apagado real:** limitar el campo MAVLink `confirmation` del reintento Lua a 255 y validar una desconexión prolongada. El contador puede superar el rango de ese campo y provocar un error de codificación que detenga el script. La prueba de reconexión realizada duró algo más de 40 segundos y no cubre ese caso.

- Modelo Python filtrado: 20 muestras de historial, mediana de cinco y EMA de 2 s, tiempos monotónicos, validación de lecturas, histéresis y estados enclavados.
- Dieciséis pruebas locales de modelo, framing, payload, checksum y validación de endpoints/voltajes.
- El script Lua realiza las mediciones y el filtrado en el autopiloto, detecta aviso y umbrales de apagado, y envía `COMMAND_LONG` dirigido a `1/191` por el canal MAVLink donde recibe el heartbeat del Companion.
- La Orange Pi recibe `/uas1/mavlink_source` y publica respuestas a `/uas1/mavlink_sink` mediante los tópicos raw de MAVROS ya usados por el rover. No abre otro lector para `/dev/ttyS5`.
- Protocolo: `MAV_CMD_WAYPOINT_USER_1` (31000) solicita apagado y lleva un nonce + tensiones; el Companion persiste evento JSONL, devuelve `COMMAND_ACK`, luego envía `MAV_CMD_WAYPOINT_USER_2` (31001) como aviso `PREPARED_TO_POWER_OFF`. Lua valida origen `1/191` y nonce y confirma con `COMMAND_ACK`. En el modo actual de Pi sin Pololu, el servicio ordena `sudo -n systemctl poweroff` tras ese ACK; si no llega ACK de preparación, aplica timeout corto y solicitaría el apagado igualmente cuando `DRY_RUN=0`.
- El ACK ordinario confirma recepción/aceptación del frame. El segundo comando `PREPARED` es el ACK de aplicación de que el registro quedó persistido y el servicio está listo para iniciar el cierre. La gracia de 5 s y el fallback de 20 s pertenecen al futuro control del Pololu; no son corte físico implementado.
- Unidad systemd `rra-power-shutdown.service` instalada y habilitada en la Orange Pi con `RRA_POWER_SHUTDOWN_DRY_RUN=1`. Se ejecuta como usuario `rra` para compartir el grafo ROS con MAVROS. El apagado real usa `sudo -n systemctl poweroff` y permanece deshabilitado. MAVROS real conectó a la H743 y los endpoints raw coinciden en QoS BEST_EFFORT; el listener ya recibe heartbeats físicos.
- `rra-mavros.service` está habilitado para UART5/57600. Se verificaron arranque tras reinicio y recuperación ante un proceso MAVROS detenido; el receptor solicita recuperación tras 120 s sin tramas válidas de la FCU. Una prueba real de apagado Linux con origen sintético aislado terminó en `System Power Off`; el servicio habitual sigue en DRY_RUN.

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
- READY `COMMAND_LONG`: command 31001 a `1/1`, `param1=nonce`, `param2=1` versión.
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

En la Pi del RRA ya se instaló y habilitó la unidad con `DRY_RUN=1`; el journal confirma el handshake y `poweroff` simulado. La unidad está activa aunque MAVROS no esté arrancado; cuando comparta domain/topics podrá recibir sus mensajes.

## Instalación inicial en Pi: solo simulación

Para una instalación nueva requiere el paquete copiado a `~/rra_ws/src/rra_battery_protection`, ROS 2 Lyrical, workspace `~/rra_ws` y MAVROS en dominio ROS 205 con los dos tópicos `/uas1/mavlink_*`. Ejecutar como usuario `rra`:

```bash
bash ~/rra_ws/src/rra_battery_protection/scripts/install_dry_run_on_pi.sh
```

El script compila, verifica topics, instala la unidad, crea `/etc/default/rra-power-shutdown` con `DRY_RUN=1` y habilita el observador. En esta Pi, la unidad ya está instalada y habilitada en DRY_RUN; se verificó activa. Para revisar:

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

No cambiar `DRY_RUN=0` hasta comprobar en banco y aprobar específicamente el apagado real. Sin Pololu, la orden apaga la Pi, pero la Matek y periféricos continúan conectados a la batería hasta que alguien los apague o se descargue el pack.

## ArduPilot y límites antes de cargar Lua

El firmware reportado es ArduRover 4.7.2, commit `fb773567`. La lista oficial `Rover/stable-4.7.2/MatekH743/features.txt` confirma `AP_SCRIPTING_ENABLED`, `AP_SDCARD_STORAGE_ENABLED` y filesystem; este build incluye scripting. La lectura anterior mostró `SCR_ENABLE=0` y no incluyó `SCR_HEAP_SIZE`, coherente con la documentación: hay que habilitar scripting y refrescar/reiniciar la lista para ver los demás parámetros `SCR_*`. El 15 de noviembre, MAVROS conectó correctamente en UART5 a 57600 (`connected=true`, desarmado, HOLD), y el servicio MAVROS completó un pull de 1150 parámetros (`success=true`). La exportación local del snapshot falló cuando SSH volvió a agotar el tiempo de espera; no se escribió ningún parámetro y no se cargó Lua. El servicio de protección se confirmó activo en `DRY_RUN=1` antes de esta interrupción. Próximo paso al recuperar SSH: guardar snapshot de parámetros, comprobar `SCR_ENABLE`, habilitarlo si sigue en 0, refrescar parámetros `SCR_*` y revisar heap/SD; sin GPIO ni corte.

Prueba física de enlace 2026-11-14: MAVROS conectó por `/dev/ttyS5:57600`, `MY ID 1.191`, `TARGET ID 1.1`; `/mavros_node/state` informó conectado, desarmado y HOLD, y `/mavros_node/battery` informó 7,633 V. El servicio systemd DRY_RUN está activo, con endpoint subscriber a `/uas1/mavlink_source` BEST_EFFORT, compatible con MAVROS. El perfil temporal usado para leer parámetros incluyó `param` y `ftp`, sin efectuar ningún set ni operación FTP; se restauró la allowlist original y ambos plugins vuelven a estar excluidos.

La batería se vio simultáneamente en 7,89 V multímetro y 7,854 V ArduPilot; no valida la lectura bajo transitorios. La H743 tiene un límite de entrada publicado de 6,8 V; 7,2 V deja 0,4 V nominales. Medir BAT de la controladora y 5 V de la Orange Pi con registrador/osciloscopio mientras se mueve el MG995 antes de poner umbrales reales. Los niveles deberán ajustarse al pack final, la química, tensión por celda y respuesta dinámica.

## Futuro Pololu

No hay conexión ni código de salida para el Pololu en este paquete. Antes de incorporarlo: validar carga total, polaridad/nivel de la entrada OFF y estado al arrancar, asignación GPIO libre, señal enclavada, masa común, protección contra realimentación por USB/UART y comportamiento de reinicio. Después, implementar salida de corte solo detrás de parámetro de habilitación explícito y esperar `PREPARED` o fallback de 20 s; nunca habilitarlo por cambiar solo un parámetro en Mission Planner.

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
