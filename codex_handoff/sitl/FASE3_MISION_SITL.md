# Fase 3: misión AUTO en ArduRover SITL

Registro: recorridos completos el 2026-11-03; prueba de parada el 2026-11-04,
hora de España. Todo está en este portátil, dentro de `codex_handoff` y WSL.

## Alcance

ArduRover SITL 4.7.2 precompilado corre en Ubuntu 22.04 de WSL dentro de un
namespace de red temporal con loopback como única interfaz. `mission3_run.py`
arranca el ejecutable y `mission3_controller.py` verifica el aislamiento antes
de conectar con `tcp:127.0.0.1:5762`. No usa SSH, ni la Orange Pi, ni puertos
serie físicos; las órdenes de armado, modo y misión se envían solo a SITL.
No conectar este controlador al rover real. La ubicación Canberra y la ruta
son simuladas y no son una misión para ejecutar físicamente.

Se cargan los parámetros oficiales de Rover para la revisión
`fb773567896014da007bca58358704d4a0d8516f` mediante
`rover-oficial-4.7.2.parm`. No desactivar comprobaciones de armado. Al inicio
se esperan fix GPS y 40 segundos adicionales de estabilización de sensores;
el controlador envía un heartbeat GCS mientras espera.

## Ruta y procedimiento

La misión fija está descrita en `mission3-solo-sitl.waypoints` (QGC WPL 110).
Se verificó que su secuencia, frame y coordenadas coinciden con las que envía
el controlador; el controlador no lee ese archivo, usa su propia lista fija.
Punto 0 es HOME y hay tres puntos de navegación: norte, este y retorno a HOME.

Desde PowerShell, con WSL y las dependencias locales preparadas:

```powershell
wsl -d Ubuntu-22.04 -- python3 -u /mnt/c/RRA/codex_handoff/sitl/mission3_run.py
```

La ejecución crea una carpeta nueva en `/home/kitttrain/rra-sitl/misiones/`,
registra eventos MAVLink y DataFlash, espera el armado y AUTO, y al completar
los puntos cambia a HOLD y desarma. Si hay fallo con el simulador armado, el
controlador intenta HOLD/desarmado antes de cerrarlo. No se debe asumir que
ese intento tiene éxito sin verificar su registro.

Para probar la parada en el primer punto, siempre en el mismo aislamiento:

```powershell
wsl -d Ubuntu-22.04 -- python3 -u /mnt/c/RRA/codex_handoff/sitl/mission3_run.py --stop-after-first
```

Esta prueba solicita HOLD y desarmado tras el primer punto y observa cinco
segundos que no se alcance el segundo. Para una interrupción humana, Ctrl+C
detiene el proceso de prueba; verificar que el simulador haya terminado. El
resultado de un cierre abrupto no equivale a una parada física controlada.

## Evidencia y resultados

- Dos recorridos completos: carpetas `fase3-wfafzpff` y `fase3-fcjlt7ru`.
  Ambos alcanzaron los puntos 1, 2 y 3; duración AUTO 20,9 s, distancia final
  al HOME simulado 0,07 m y cierre `HOLD`, desarmado.
- DataFlash de cada uno: 1093 mensajes POS, 109 GPS, tres MODE y cuatro CMD.
  El recorrido estimado a partir de posiciones POS fue 36,19 m y la separación
  máxima del punto inicial 14,51 m en ambos. Son resultados de simulación y no
  son una medida de precisión real. Se generó `resumen.json` analizando las
  copias de ambos registros.
- Prueba de parada: `fase3-k1d05hqw`, primer punto alcanzado, HOLD y desarmado;
  no alcanzó el segundo durante cinco segundos.
- Se conserva también la evidencia de intentos fallidos: una comprobación de
  aislamiento no pudo leer `/proc/1/ns/net`; se corrigió comparando el espacio
  de red original. Un primer armado fue rechazado por acelerómetros aún
  inconsistentes. Tras esperar 20 s, el armado pasó pero AUTO fue rechazado por
  el EKF; al esperar 40 s y conservar las comprobaciones, ambas ejecuciones
  completaron la misión. No se aplicaron esos ajustes al hardware real.

Evidencia copiada y local:
`C:\RRA\codex_handoff\evidencias\fase3-2026-11-03`. Las copias DataFlash de
los dos recorridos se compararon por SHA-256 con sus originales. La carpeta
está excluida mediante `.git/info/exclude` y no debe publicarse por accidente.

La fase demuestra una misión y parada en SITL con este controlador. Falta que
el usuario practique el mismo flujo con una estación de control si desea usarla
manualmente; no se ha conectado la Orange Pi durante estos recorridos ni se ha
validado el comportamiento de ningún componente físico.
