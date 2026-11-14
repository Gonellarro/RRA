# RRA: protección de batería de electrónica 2S

Paquete ROS 2 + ArduPilot Lua para alertar de tensión baja y pedir a la Orange Pi un apagado Linux ordenado. **La versión actual no acciona salidas GPIO ni corta la batería.** El nodo Companion tiene `DRY_RUN=1` por defecto. El apagado real solo ocurre si un operador cambia esa variable a `0` en systemd.

## Estado actual

- Modelo Python filtrado: 20 muestras de historial, mediana de cinco y EMA de 2 s, tiempos monotónicos, validación de lecturas, histéresis y estados enclavados.
- Trece pruebas locales de modelo, framing, payload, checksum y validación de endpoints/voltajes.
- El script Lua realiza las mediciones y el filtrado en el autopiloto, detecta aviso y umbrales de apagado, y envía `COMMAND_LONG` dirigido a `1/191` por el canal MAVLink donde recibe el heartbeat del Companion.
- La Orange Pi recibe `/uas1/mavlink_source` y publica respuestas a `/uas1/mavlink_sink` mediante los tópicos raw de MAVROS ya usados por el rover. No abre otro lector para `/dev/ttyS5`.
- Protocolo: `MAV_CMD_WAYPOINT_USER_1` (31000) solicita apagado y lleva un nonce + tensiones; el Companion persiste evento JSONL, devuelve `COMMAND_ACK`, luego envía `MAV_CMD_WAYPOINT_USER_2` (31001) como aviso `PREPARED_TO_POWER_OFF`. Lua valida origen `1/191` y nonce y confirma con `COMMAND_ACK`. En el modo actual de Pi sin Pololu, el servicio ordena `sudo -n systemctl poweroff` tras ese ACK; si no llega ACK de preparación, aplica timeout corto y solicitaría el apagado igualmente cuando `DRY_RUN=0`.
- El ACK ordinario confirma recepción/aceptación del frame. El segundo comando `PREPARED` es el ACK de aplicación de que el registro quedó persistido y el servicio está listo para iniciar el cierre. La gracia de 5 s y el fallback de 20 s pertenecen al futuro control del Pololu; no son corte físico implementado.
- Unidad systemd `rra-power-shutdown.service` instalada y habilitada en la Orange Pi con `RRA_POWER_SHUTDOWN_DRY_RUN=1`. Se ejecuta como usuario `rra` para compartir el grafo ROS con MAVROS. El apagado real usa `sudo -n systemctl poweroff` y permanece deshabilitado. MAVROS real conectó a la H743 y los endpoints raw coinciden en QoS BEST_EFFORT; el listener ya recibe heartbeats físicos.

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

El firmware reporta ArduRover 4.7.2. Una descarga completa de parámetros vía MAVROS mostró `SCR_ENABLE=0`; en la lista solo aparece ese parámetro de scripting y no aparece `SCR_HEAP_SIZE`. No se ha podido confirmar que este build exponga heap ni que incluya AP_Scripting, así que no subí ni ejecuté Lua. Para continuar hay que confirmar soporte Lua en este firmware y que exista la carpeta `APM/scripts`; después revisar módulos MAVLink y que la tabla 111 esté libre. No habilitar scripting ni cambiar parámetros hasta confirmar que el firmware está preparado.

Prueba física de enlace 2026-11-14: MAVROS conectó por `/dev/ttyS5:57600`, `MY ID 1.191`, `TARGET ID 1.1`; `/mavros_node/state` informó conectado, desarmado y HOLD, y `/mavros_node/battery` informó 7,633 V. El servicio systemd DRY_RUN está activo, con endpoint subscriber a `/uas1/mavlink_source` BEST_EFFORT, compatible con MAVROS. El perfil temporal usado para leer parámetros incluyó `param` y `ftp`, sin efectuar ningún set ni operación FTP; se restauró la allowlist original y ambos plugins vuelven a estar excluidos.

La batería se vio simultáneamente en 7,89 V multímetro y 7,854 V ArduPilot; no valida la lectura bajo transitorios. La H743 tiene un límite de entrada publicado de 6,8 V; 7,2 V deja 0,4 V nominales. Medir BAT de la controladora y 5 V de la Orange Pi con registrador/osciloscopio mientras se mueve el MG995 antes de poner umbrales reales. Los niveles deberán ajustarse al pack final, la química, tensión por celda y respuesta dinámica.

## Futuro Pololu

No hay conexión ni código de salida para el Pololu en este paquete. Antes de incorporarlo: validar carga total, polaridad/nivel de la entrada OFF y estado al arrancar, asignación GPIO libre, señal enclavada, masa común, protección contra realimentación por USB/UART y comportamiento de reinicio. Después, implementar salida de corte solo detrás de parámetro de habilitación explícito y esperar `PREPARED` o fallback de 20 s; nunca habilitarlo por cambiar solo un parámetro en Mission Planner.
