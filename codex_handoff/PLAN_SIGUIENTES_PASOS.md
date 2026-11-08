# Plan para la siguiente sesión

> **Plan vigente al 2026-11-08:** las notas cronológicas anteriores son
> historial. La Orange Pi ya hizo telemetría física/replay UART el 7/11; la
> integración H743 no está pendiente de primera conexión. Prioridad ahora:
> registrar el resultado de campo reportado, completar medidas AX10, validar en
> SITL el uso de HC-SR04/evitación y preparar captura de cámara UVC. No instalar
> sensores ni tocar parámetros/cableado sin autorización específica.

Fecha base: 2026-11-03. Esta transferencia es documental: no ejecutar ahora
instalaciones importantes. Comprobar el estado antes de cada acción futura.

Guardado local solicitado el 2026-11-04: consultar `GUARDADO_LOCAL.md` y el
manifiesto de la copia local antes de restaurar. Mantener la prohibición de
commit, push y sincronización externa salvo nueva instrucción del usuario.

Actualización 2026-11-04: el usuario autorizó la fase 3. Se ejecutó una misma
misión AUTO dos veces en SITL aislado y se comprobó una parada a mitad de ruta;
ambas misiones completas terminaron en HOLD y desarmadas. Detalles y límites en
`sitl/FASE3_MISION_SITL.md`. El siguiente bloque del roadmap es la etapa 4:
modos, autoridad y fallos de comunicación en simulación. Sigue pendiente validar
una estación de control manual si se desea utilizarla y no se ha conectado
hardware ni demostrado aislamiento de control en MAVROS para una conexión real.

Reanudación posterior autorizada por el usuario: pasos 1–3 comprobados de nuevo
el 2026-11-03, incluida prueba de dos nodos locales. Paso 4 en ejecución; APT
simuló 12 paquetes nuevos, cero actualizaciones y cero eliminaciones para
MAVROS, 6,7 MB de descarga y unos 84 MB adicionales de disco. La documentación
original de preparación anterior se conserva abajo como plan histórico.
MAVROS y el geoide obligatorio `egm96-5` se instalaron y se verificó arranque
aislado y cierre normal en loopback. El perfil predeterminado expone interfaces
de control, por lo que no acredita solo lectura. Sin enlace a simulador o FCU.
Siguiente: desarrollar y probar la observación local sin emitir órdenes y
preparar aislamiento verificable antes de cualquier conexión física.
Actualización de la misma sesión: se creó y compiló `rra_telemetry` como paquete
local; observación de estado, cuatro pruebas unitarias y prueba ROS con mensajes
simulados aprobadas. Junto a MAVROS aislado sin FCU informa sin datos, no
desconectado; no hay todavía prueba con heartbeat MAVLink ni con ArduRover SITL.
Siguientes tareas concretas: preparar una fuente SITL independiente y de loopback,
validar frescura y desconexión con heartbeat real simulado, registrar/reproducir
rosbag, y diseñar/verificar un perfil MAVROS que no exponga control antes de
cualquier conexión física. No suponer que una configuración de plugins por sí
sola garantiza aislamiento sin inspección y pruebas de las interfaces efectivas.

Seguimiento: heartbeat MAVLink sintético en loopback validado el 2026-11-03,
incluido envío sostenido, caducidad, desconexión y grabación/reproducción de
rosbag. No es ArduRover SITL y solo transportó heartbeat/estado. Evidencia y
límites en `ESTADO_ACTUAL.md`. La siguiente tarea es preparar ArduRover SITL en
un entorno local adecuado, verificar que la conexión se limite a loopback o a
un enlace explícitamente autorizado, y comprobar estado/posición/batería y
sus fallos. Antes de cualquier conexión física, diseñar y verificar aislamiento
de las interfaces de control de MAVROS.

Nuevo seguimiento: ArduRover SITL 4.7.2 se ejecutó en WSL con red aislada y
datos de un solo sentido por SSH hacia MAVROS en la Orange Pi. Se recibieron
estado, GPS, IMU y un mensaje de batería con valores inválidos; se verificó la
pérdida del enlace y un cierre secuencial correcto. Los detalles y fallos previos
están en `ESTADO_ACTUAL.md`. Siguiente: estudiar la configuración y validez de
la batería en SITL sin modificar hardware, registrar/reproducir un rosbag de
datos SITL y repetir la prueba de cierre para evaluar el fallo intermitente de
MAVROS. Antes de una conexión física sigue pendiente un aislamiento de control
efectivo, inspeccionado y probado.

Seguimiento posterior: los cuatro pasos solicitados se han realizado en SITL.
`BATT_MONITOR 4` en un archivo exclusivo de simulación corrigió la batería en
esa prueba; se grabó y reprodujo rosbag de cinco tópicos, pasaron 3/3 cierres
secuenciales y se ampliaron y probaron los diagnósticos de GPS, IMU y batería.
Quedan por evaluar repetibilidad más amplia, funcionamiento bidireccional solo
en simulación si se autoriza, fallos y validación de interfaces antes de usar
hardware. El fallo previo de cierre simultáneo no queda descartado por 3/3.

1. **Entorno y acceso.** En `C:\RRA`, revisar rama y cambios locales; SSH como
   `rra`, hostname, arquitectura, espacio, memoria, usuario y estado de APT.
   Aceptación: conexión y diagnóstico sin alterar red ni perder acceso root.
2. **Compatibilidad ROS.** Comprobar SO real y arquitectura; verificar
   repositorios oficiales y `apt-cache policy ros-lyrical-ros-base`. Aceptación:
   versiones y paquetes Resolute ARM64 documentados. No mezclar distros.
3. **ROS 2 nativo.** Ya instalado: revalidar entorno, `ros2` y un publicador y
   suscriptor locales con cierre normal. Solo instalar o reparar si el nuevo
   diagnóstico lo exige y está autorizado. Aceptación: intercambio reproducible
   y sesión nueva con `ROS_DISTRO=lyrical`; no instalar Docker por defecto.
4. **MAVROS.** Consultar repositorios oficiales vigentes, `apt-cache policy
   ros-lyrical-mavros`, y simular con `apt-get -s --no-install-recommends
   install ros-lyrical-mavros`; revisar cambios, tamaño y GeographicLib antes de
   instalar. No actualizar kernel o firmware. Aceptación: paquetes y datos
   requeridos instalados, versión y arranque aislado probados, fallos anotados.
5. **Workspace.** Existe `~/rra_ws/src` con `rra_telemetry`: revisar contenido y overlay antes
   de modificar; preparar dependencias y build reproducible. Aceptación:
   `colcon list` y build/pruebas del paquete real. No sobrescribir cambios locales.
6. **Diagnóstico y telemetría.** Ampliar el observador provisional con interfaces mínimas y paquetes portables
   con ROS estándar. Empezar por diagnóstico y lectura, sin órdenes de control.
   Aceptación: parámetros documentados y pruebas significativas de datos válidos,
   ausentes y obsoletos. La existencia de MAVROS no garantiza solo lectura.
7. **Comunicación.** Empezar en SITL, conexión aislada y explícita; validar
   heartbeat, estado, modo, posición, orientación y batería solo si disponibles,
   además de desconexión y datos obsoletos. Registrar y reproducir rosbag.
   Aceptación: mensajes y logs con marcas de tiempo, desconexión indicada y
   ninguna orden de movimiento, armado o modo emitida durante el ensayo.
8. **H743 futura.** Recoger de hardware firmware, conexiones reales, puertos,
   velocidades, protecciones y procedimiento de parada. Diseñar prueba primero
   inmovilizada y supervisada; no asumir conexión ni habilitar actuación.
   Aceptación: contrato de interfaz revisable y prueba física solo autorizada.
9. **Documentar.** Actualizar en local `ESTADO_ACTUAL.md` y este plan con
   comandos, versiones, resultados, fallos, límites y siguiente paso. Mantener
   separadas propuestas, software instalado y resultados realmente observados.
Actualización 2026-11-04: fase 3 sigue cerrada en SITL; F4-0 es una lectura completada, mientras que las pruebas de fallo de fase 4 siguen pendientes. Se revisaron los entornos: WSL Ubuntu-22.04 disponible, binario ArduRover con hash esperado; no había SITL activo al inicio y no queda proceso tras F4-0. SSH a la Orange Pi agotó timeout. C: mostró 19,17 GiB libres. Diseño de autoridad y matriz F4-0…F4-5 en `sitl/FASE4_DISENO.md`. F4-0…F4-3 se completaron en SITL. F4-1 probó heartbeat perdido con failsafe GCS habilitado; F4-2 verificó persistencia de HOLD al reconectar; F4-3 comparó `FS_GCS_ENABLE` 0/1/2. Los tres perfiles pasaron. Resumen y evidencia en `evidencias/fase4-gcs-2026-11-04/`; diseño y límites en `sitl/FASE4_DISENO.md`.

Nota de estado: el párrafo anterior refleja el punto previo a la autorización expresa del usuario para F4-1…F4-3 en SITL aislado y ha quedado obsoleto para esos tres ensayos; ver su actualización y evidencias inmediatamente debajo y en `sitl/FASE4_DISENO.md`. F4-4 y F4-5 continúan pendientes: concretar la interfaz y criterio de caducidad GUIDED (el companion actual es solo lectura), y definir la autoridad si hubiera dos emisores. No extrapolar perfiles temporales a hardware. Orange Pi, hardware y GitHub permanecen fuera de esos ensayos.
Actualización 2026-11-04: F4-1…F4-3 probadas y aprobadas en SITL aislado. Resultado comparativo y evidencias en `sitl/FASE4_DISENO.md` y `evidencias/fase4-gcs-2026-11-04/resumen.json`. Próximo paso es cerrar el diseño de consignas GUIDED y autoridad entre emisores para F4-4/5 antes de implementar o emitir esas consignas.


Actualización 2026-11-04: F4-4 y F4-5 ejecutadas en SITL aislado; resultados y límites en `sitl/FASE4_DISENO.md` y `evidencias/fase4-guided-2026-11-04/resumen.json`. F4-4 observó parada predeterminada de consigna de velocidad a los 2,84 s, pero no obtuvo respuesta al leer `GUID_TIMEOUT`; F4-5 mostró que SET_MODE de SYSID 255 y 42 fueron aceptados y prevaleció el último incluso con MAV_GCS_SYSID configurado a 42. Fase 4 queda ensayada en simulación. Siguiente: decidir la política/puerta de autoridad antes de desarrollar control desde Companion; mantenerlo en solo observación y no conectar MAVROS al hardware.

Ampliación de F4-5 el 2026-11-04: se ensayó además `MAV_OPTIONS=1` con rango GCS 42…42. SITL ignoró SET_MODE del SYSID 255 y aceptó GUIDED/HOLD del 42, terminando desarmado. El intento de preflight desde 255 quedó bloqueado por el filtro, así que la repetición se hizo desde el ID permitido. El filtro observado no acredita autenticación del emisor ni otras clases de MAVLink. Consultar `sitl/FASE4_DISENO.md` y el nuevo caso de `resumen.json`; el Companion sigue en solo observación hasta acordar política y diseño de control.

Pausa solicitada por el usuario el 2026-11-04: trabajo detenido después de guardar el estado y evidencias en Git local. No iniciar los pasos siguientes hasta que el usuario reanude el proyecto. Al volver, verificar este estado y revisar la decisión pendiente de autoridad/puerta de control para Companion antes de cualquier trabajo de actuación.

Reanudación 2026-11-04: acceso a `rra@192.168.1.156` agotó timeout con clave existente en modo no interactivo; ICMP y TCP/22 tampoco respondieron. Primero confirmar la IP/alcance actual de la Orange Pi y repetir la verificación SSH de solo lectura. No cambiar red, SSH, claves ni instalar componentes hasta recuperar acceso y revisar estado real.

Ampliación 2026-11-04: el router confirmó la asignación `192.168.1.156`; SSH volvió a responder con clave tras el timeout previo. Se validaron en vivo ROS Lyrical, MAVROS 2.16.0, geoide, `rra_telemetry` en el workspace y diagnóstico remoto; `dpkg --audit` limpio. Ver `ESTADO_ACTUAL.md`. Siguiente trabajo: revisar/build/pruebas del paquete si hay cambios pendientes, y preparar el diseño de una ruta MAVLink de solo lectura verificable antes de conectar FCU/H743. No cambiar puertos/servicios ni activar arranque automático sin definir y autorizar esa decisión.

## Reanudación de los cuatro pasos — 2026-11-04

1. **Build/pruebas del paquete:** completados en Orange Pi. Build correcto, 9 pruebas unitarias, prueba integrada con nodos simulados y prueba sintética MAVLink loopback correctas. 54 mensajes reproducidos desde rosbag. Detalle y evidencia en `MAVROS_READONLY_BOUNDARY.md` y `evidencias/readonly-validation-2026-11-04/mavlink-loopback/`.
2. **Límite MAVROS de solo lectura:** no aprobado. La prueba de allowlist aislada conservó servicios de modo/endpoints y otros puntos de entrada. No conectar a la H743. Siguiente: diseño de gateway unidireccional y política de permisos de ROS/DDS con prueba positiva de telemetría y negativa de cada superficie de escritura.
3. **H743:** faltan el firmware/versión y parámetros reales, puertos/cableado/baud/protocolo, equipos enlazados y procedimiento físico RC/corte. No asumir datos ni ejecutar ensayo en hardware. Recopilar lo enumerado en `MAVROS_READONLY_BOUNDARY.md`.
4. **Operación continua:** propuesta local documentada; no hay autostart. Primero debe aprobarse la frontera y la retención de logs/bags. Mantener unidades systemd deshabilitadas/no creadas hasta entonces.

El diagnóstico al final mostró que MAVROS, los puertos temporales y unidades RRA/MAVROS no permanecían activos. No se cambió red, SSH, parámetros, kernel, firmware ni servicios. `ros2 security` está disponible en Lyrical; no se generaron claves ni permisos. El siguiente paso seguro es diseñar y probar en local un gateway unidireccional junto con permisos DDS/ROS estrictos, verificando telemetría permitida y denegación de `set_mode` y canales de escritura; sin hardware. Después recoger datos reales de H743 y revisar el arranque/retención antes de activar servicios. Mantener esta carpeta fuera de GitHub.

## Resultado del ensayo DDS/gateway — 2026-11-04

Prototipo local `codex_handoff/gateway_probe/` probado en la Orange Pi con productor MAVROS simulado, gateway de cuatro tópicos fijos y tres identidades SROS2 en modo Enforce. Pasaron: telemetría state/GPS/IMU/batería por el gateway; denegación de suscripción directa a `/mavros/state`; denegación de cliente `/mavros/set_mode`; denegación del publicador de setpoints; ninguna solicitud llegó al servicio sintético y ningún setpoint llegó a la fuente. Evidencia de salida en `evidencias/readonly-validation-2026-11-04/gateway-dds-probe-pass.txt`; alcance y limitaciones en `MAVROS_READONLY_BOUNDARY.md`.

El ensayo aún no usó el `mavros_node` real ni un FCU. La lista permitida de plugins sigue sin ser una barrera adecuada. Próximo paso: iniciar MAVROS en loopback, sin FCU, con SROS2 estricto y perfil limitado; inspeccionar todos los topics/services/endpoints y repetir pruebas de denegación con la identidad de aplicación. No conectar la H743 hasta que se valide ese perfil. Se limpiaron keystore temporal, procesos y puertos; el autostart no se habilitó. Seguir en local, sin tocar GitHub.

## Recopilación H743 — 2026-11-04

El usuario confirmó que Orange Pi no tiene conexión física con H743 y especificó el modelo **MATEK H743-WLITE**. La lectura de firmware/parámetros desde Orange Pi no es posible en esta topología. El modelo ahora figura en la documentación del proyecto, pero no se ha contrastado con la etiqueta ni se conoce la revisión física o la configuración instalada. Datos reales pendientes: etiqueta/revisión, versión de firmware, exportación de parámetros, puertos y cableado, protocolo/baud, alimentación, GCS/RC y sistemas de sensores/actuadores. Recogerlos del responsable de hardware o una estación de control conectada en una tarea posterior; no inventar valores ni confundir con SITL. No se conectó ni consultó el autopiloto en esta sesión.

### Cableado comunicado — 2026-11-04

Ver `H743_DATOS_HARDWARE.md` para el inventario detallado. El usuario informa
que S1 lleva la señal ESC con su cable de voltaje desconectado, S3 lleva el
servo de dirección, TX7/RX7 conectan la ESP32 DroneBridge, RX6 lleva el receptor,
TX2/RX2 el GNSS y DA1/CL1 la brújula I²C1. TX1/RX1 (TELEM2 / `SERIAL2`) está
libre según el usuario y se considera para la Orange Pi. Antes de conectar,
comprobar los parámetros reales del puerto y terminar la prueba de aislamiento
con `mavros_node` real; no cablear ni transmitir órdenes en esta fase.

### Actualización de estado maestro — 2026-11-04

El documento maestro recibido reporta pruebas físicas iniciales de H743-WLite,
ArduRover 4.7.2, GNSS M10/brújula, RC/actuadores y misión AUTO. Son datos
reportados por el responsable y no contradicen que el companion Orange Pi aún no
tenga enlace físico a la placa. Para el companion, MAVROS 2.16.0 ya está instalado
y probado con SITL/loopback; la nota de instalación inicial en
`docs/companion_orange_pi.md` se actualizó. El ensayo SROS2 de gateway pasó con
nodos sintéticos, pero falta repetir la matriz con `mavros_node` real en loopback
y permisos estrictos. Ese es el próximo paso técnico local, sin FCU ni hardware.

Cuando el usuario conecte la H743 al companion, la tarea futura será identificar
y leer firmware/configuración por ROS 2/MAVROS en modo estrictamente de solo
lectura y contrastarlo con Mission Planner. No conectar ni enviar órdenes antes
de validar el aislamiento del MAVROS real y confirmar el estado de conexión con
el usuario; no emitir armado, cambio de modo, escritura de parámetros ni
consignas de movimiento.

## Actualización de fase companion — 2026-11-04

La siguiente tarea planificada, ejecutar MAVROS real bajo SROS2 en loopback,
quedó completada para una matriz parcial. Resultado y límites en
`MAVROS_READONLY_BOUNDARY.md`; evidencia en
`evidencias/readonly-validation-2026-11-04/mavros-sros2-real-probe-pass.txt`.

Siguiente tarea: inventariar y probar los servicios, acciones, parámetros,
endpoints del router y tópicos MAVLink/control restantes que expuso el grafo;
repetir positivos de telemetría y negativos de escritura con la aplicación bajo
SROS2 Enforce. Solo después de revisar esa cobertura, evaluar el diseño de dos
barreras: identidad DDS de aplicación restringida y cable unidireccional TX más
masa común. Mantener RX1 sin conectar; no conectar H743 ni habilitar autostart
por el resultado parcial actual.

## Matriz SROS2 del MAVROS real completada — 2026-11-04

La matriz ampliada cubrió el grafo observado: 69 tópicos MAVROS/MAVLink, 233
servicios y cero acciones anunciadas. Pasaron las suscripciones del gateway y
la entrega de estado conectado/desarmado. DDS denegó la creación de 69 lectores
directos, 73 escritores y 233 clientes de servicio desde la identidad de
aplicación. Detalles en `MAVROS_READONLY_BOUNDARY.md`, inventario y evidencia en
`mavros_sros_probe/runtime_graph_inventory.txt` y
`evidencias/readonly-validation-2026-11-04/mavros-sros2-expanded-pass.txt`.

Siguiente paso: revisar el diseño de las dos barreras antes de la conexión
física: despliegue de aplicación únicamente bajo la identidad SROS2 con
credenciales protegidas; y enlace de observación unidireccional TX1→RX de Orange
Pi más masa común, manteniendo RX1 sin cable. Consultar pinouts, niveles lógicos,
UART disponible y `SERIAL2_*` del hardware concreto antes de proponer cableado
final. No conectar la H743 ni activar un servicio permanente en esta fase.

## Continuidad tras ensayo bidireccional — 2026-11-04

La instrucción previa de preparar solo un enlace TX unidireccional queda reemplazada para SITL por el ensayo bidireccional autorizado, sin modificar la recomendación de no cablear la H743 todavía. Ver resultados completos en `MAVROS_READONLY_BOUNDARY.md` y evidencia en `evidencias/mavros-bidirectional-sros-2026-11-04/`.

1. **Versión del firmware:** solicitud directa `MAV_CMD_REQUEST_MESSAGE=512`, `message_id=148` verificada en SITL: ACK aceptado y ArduRover 4.7.2 (`fb773567`). Pendiente: exponerla mediante un endpoint MAVROS estrecho; `VehicleInfoGet` sigue sin versión y el broker reporta no disponible. No habilitar `/mavros/cmd/command` genérico.
2. **Paquete ROS local:** completado. `rra_companion_readonly` está en `~/rra_ws/src`, build correcto, cuatro pruebas unitarias pasan y ejecutables `readonly_gateway`/`readonly_query` disponibles. Sin autostart.
3. **Allowlist y denegación:** completada para la interfaz auditada. Parámetro fijado a `BATT_MONITOR`, petición `Trigger` sin nombres y fallos cerrados; integración del paquete bajo SROS2 Enforce pasó con 233 servicios y 142 endpoints de tópicos denegados, consultas positivas y pérdida de SITL/timeout acotado. Riesgo residual: el broker posee permiso de lectura genérico en `GetParameters`; el código limita el nombre pero un compromiso del broker podría eludir esa restricción. SROS2 no inspecciona ese contenido. No se concedieron permisos de escritura.
4. **Fase física aún pendiente:** cuando se vaya a conectar MATEK H743-WLITE, verificar pinout, niveles, `SERIAL2_*`, baud y tierra en la revisión concreta; preparar banco inmovilizado y revisar protección de keystore. No conectar ni emitir comandos al hardware en este paso documental.
5. Mantener fuera de GitHub y sin commit/push. Ningún nodo tiene autostart. Al retomar, comprobar procesos/puertos, y después diseñar una ruta especializada para `AUTOPILOT_VERSION`; revisar si el límite actual del broker frente a compromiso requiere implementación fuera del proceso Python antes de conectar hardware.

## Actualización del plan — 2026-11-05

Puntos 1–3 del trabajo MAVROS/SITL quedan completados en simulación: la ruta MAVROS fija para `AUTOPILOT_VERSION` entrega `[4,7,2]` y `fb773567`; el paquete `rra_companion_readonly` y el plugin `rra_mavros_version_plugin` compilan y están instalados en el workspace ROS 2 de la Orange Pi, sin autostart; el broker ofrece únicamente consultas de estado, versión y `BATT_MONITOR`, con SROS2 Enforce y denegaciones DDS verificadas (233 servicios, 142 endpoints de tópicos). Pasaron también estado de desconexión y timeout acotado tras detener SITL.

Siguiente paso de desarrollo seguro: probar repetición de varias solicitudes de versión, timeout y reconexión del FCU simulado, y revisar que el plugin no publique respuestas antiguas ni deje la petición pendiente. Después revisar endurecimiento del broker frente a compromiso (la allowlist de `GetParameters` es lógica del proceso) y documentar instalación reproducible/política de permisos. Solo tras esas tareas preparar una propuesta revisable para ensayo físico de observación: verificar pinout/voltajes/`SERIAL2_*`, resguardar keystore y mantener TX1→RX más GND, RX1 desconectado hasta revisión específica. No conectar H743 ni habilitar autostart todavía.

Evidencia de esta fase: `evidencias/mavros-version-plugin-sros-2026-11-05/`. Todo permanece local; no commit, push ni acceso de escritura a GitHub.

## Actualización del plan — repetición y frontera del broker, 2026-11-05

**Completado:** tres solicitudes de versión consecutivas; timeout inducido con la conexión FCU activa y una respuesta 148 filtrada, seguido de solicitud inmediata correcta; corte/restauración de ambos sentidos y reconexión MAVROS; lectura de versión y `BATT_MONITOR` tras reconectar; fallo rápido al parar SITL. Auditoría en el enclave del broker confirmó que SROS2 niega `ParamPull` y `GetParameters` genéricos. El broker ya no descarga la lista de parámetros ni pide nombres arbitrarios. Build de los dos paquetes y cuatro pruebas unitarias pasaron. Evidencia en `evidencias/mavros-repeat-reconnect-boundary-2026-11-05/`.

**Límite actualizado:** la allowlist `BATT_MONITOR` ya no depende de Python ni del payload `GetParameters`; la operación es un servicio Trigger fijo que transmite `PARAM_REQUEST_READ` del ID literal. El plugin y MAVROS siguen en la base de confianza. El identificador `request_id` evita confundir muestras ROS viejas de otra solicitud; MAVLink `PARAM_VALUE` no trae correlación en el protocolo, así que un mensaje MAVLink demorado que llegue durante una solicitud nueva no puede identificarse como antiguo.

**Siguientes tareas:** (1) documentar y empaquetar una instalación reproducible de los dos paquetes y la política SROS2, manteniendo el arranque manual; (2) revisar pruebas de concurrencia/solicitudes simultáneas y respuestas tardías; (3) antes de hardware, contrastar pinout, niveles, `SERIAL2_*`, UART, GND y protección de keystore para la placa concreta y preparar procedimiento de banco inmovilizado. No conectar H743, activar autostart ni controlar actuadores sin el paso de validación correspondiente. Todo local, sin commit/push.

**Comprobación adicional de reducción MAVROS — 2026-11-05:** repetición completa con `plugin_allowlist=['sys_status','rra_readonly_version']` temporal: estado y las dos lecturas fijas siguen pasando; plugins `param`, `command` y resto quedan ignorados; MAVROS ya no ejecuta su lectura automática de la lista de parámetros en este perfil. Se verificó el ID verdadero `sys_status` (el patrón `sys` no coincide). La opción está documentada por MAVROS y el comando se probó; no se aplicó a configuración persistente. Interpretar los 233/142 como intentos contra el inventario completo, no endpoints vivos bajo este perfil mínimo. Resultados y logs finales en `evidencias/mavros-repeat-reconnect-boundary-2026-11-05/`.

## Actualización — 2026-11-05, concurrencia y entrega reproducible

**Completados los tres puntos anteriores:** (1) script local de despliegue manual comprobado en el equipo; (2) consulta simultánea validada: una llamada realiza la operación, las demás fallan rápido y sin ocupar hilos del executor; timeout queda acotado; resultado viejo en ROS se asocia por `request_id`; (3) replay de una respuesta `AUTOPILOT_VERSION` después del timeout y mientras no había solicitud: se ignoró para la llamada siguiente, que devolvió versión correcta. Cuatro llamadas concurrentes: `busy=3 timeout=1`; `late_replayed=1`. Suite remota 8/8 y build de ambos paquetes OK. Integración completa y límites en `MAVROS_READONLY_BOUNDARY.md`; evidencia/logs en `evidencias/mavros-concurrency-late-response-2026-11-05/`.

**Límite abierto:** MAVLink `PARAM_VALUE` no incluye transaction ID. `request_id` protege la correlación del plugin→broker en ROS, no permite distinguir un frame físico atrasado si llega durante otra solicitud pendiente. Mantener explícito ese riesgo; antes de hardware, seleccionar mitigación/protocolo de consulta y confirmar pinout, nivel lógico, UART/baud, GND y protección de keystore de la revisión H743 concreta.

**Siguiente tarea:** inspección de la interfaz física/documentación MATEK y configuración serial prevista, sin conectar ni modificar placa. Preparar checklist de banco desarmado/inmovilizado y credenciales SROS2. No habilitar autostart, no emitir comandos de escritura y no subir cambios. La integración física requiere la conexión H743 que el usuario indicará y validación específica.

## Actualización — checklist UART previo a H743, 2026-11-05

**Completado en esta fase documental:** revisión de fuentes oficiales MATEKSYS, ArduPilot y Orange Pi; comprobación remota de solo lectura de OS/kernel, boot overlays, nodos UART, pinmux aún no acreditado, permisos y consola. Checklist: `UART_PRECONNECTION_CHECKLIST.md`.

**Siguiente paso seguro:** investigar documentación de Armbian para habilitar UART5 (PH2/PH3) en la imagen `Ubuntu 26.04 / 6.18.60-current-sunxi64`, sin tocar aún `armbianEnv.txt`; determinar cómo confirmar el pinmux y `/dev` resultante. En paralelo, cuando el usuario tenga acceso a la FCU vía GCS, recopilar revisión y exportación local privada de parámetros SERIAL2 en modo solo lectura. Revisar compatibilidad eléctrica TX1→OPi RX con nivel medido/especificación de revisión exacta. No realizar overlay, reinicio, conexión, modificación de parámetros ni fase bidireccional ahora.

Corrección técnica para el plan: el enlace inicial de sentido único (MATEK TX1 → OPi RX13 + GND) permite recibir solo las tramas que la FCU emita espontáneamente. No permite consultas de firmware o parámetros desde el Companion. Cualquier consulta de respuesta requerirá retorno UART y nueva revisión específica del límite de confianza aplicado a la Orange Pi física.

### Resultado de investigar UART5 — 2026-11-05

La comprobación documental y del DTB ya identifica un overlay candidato en esta imagen: `overlay_prefix=sun50i-h616` + `overlays=uart5` localizaría el overlay Armbian presente `sun50i-h616-uart5.dtbo`, que habilita el alias UART5/pin group PH2/PH3 del DTB H618. No está activo. `ttyS5` actual no verifica pinmux. Checklist con fuentes: `UART_PRECONNECTION_CHECKLIST.md`.

La activación implica editar `/boot/armbianEnv.txt` y reiniciar; Armbian describe el boot environment como configuración crítica. Para proceder hace falta preparar copia verificable y plan de recuperación local/consola si el Orange Pi no vuelve por SSH. No se aplica el overlay en esta fase; revisar y acordar esa operación antes de cambiar arranque. Sigue pendiente la revisión física MATEK y verificación de niveles; el enlace TX solo no soporta consultas Companion.

Antes de la operación de overlay, el inventario reportó rootfs en `mmcblk0p1` (disco `mmcblk0` de 59.5G) y cmdline `console=ttyS0,115200`, pero no se confirmó acceso físico a SD ni una consola serial de rescate. Hash leído de `armbianEnv.txt`: `a28921daf696c1fe31a5f8d4b4b5c3200125f9a3f1b2757499203ae797916df6`. Este hash no sustituye una copia. Condición previa adicional: asegurar recuperación física (SD/consola) antes de editar y reiniciar.

### SSH/arranque de Orange Pi — diagnóstico 2026-11-05

No se detectó lentitud de sshd/autenticación en la conexión actual: el socket SSH escucha temprano, el acceso de clave acepta en un intento, y TCP/22 responde en 10 ms. La Orange Pi tarda ~14,4 s en completar el arranque de sistema medido, pero no espera a `network-online`; la red Wi-Fi/DHCP podría estar lista después de que el servicio escuche. wlan0 usa DHCP y hoy recibe .156, sin reserva del router confirmada. Revisar si existe reserva para MAC `e4:33:89:2e:8d:ad`; una reserva estable es el ajuste potencial más simple, pero se debe realizar desde el router y no se cambió. Journald/auth.log no accesible al usuario `rra`, así que el motivo exacto histórico queda sin confirmar. Detalle: `SSH_DIAGNOSTIC_2026-11-05.md`.

Revisión tras ver logs SSH en frío: no añadir aún dependencia de network-online ni editar SSH. El journal muestra que tras la estabilización Wi-Fi/DHCP, los dos primeros clientes de `192.168.1.146` cerraron conexiones antes de auth y el tercero autenticó. Próxima evidencia útil: capturar verbose del primer intento en Remote y correlacionarlo con journal; sin un reboot provocado en esta sesión. Detalle en `SSH_DIAGNOSTIC_2026-11-05.md`.

## Actualización — UART5 habilitado, 2026-11-05

**Completado:** overlay Armbian UART5 activado con backup y reinicio; pinmux PH2/PH3 confirmado en runtime; `/dev/ttyS5` accesible al usuario `rra`; MAVROS abrió la URL serial temporal y plugin allowlist bajo ROS_DOMAIN_ID local. Sin FCU, comunicación física o SROS en este smoke test. Evidencia completa: `evidencias/uart5-overlay-2026-11-05/`.

**Siguiente paso:** confirmar desde GCS/revisión física MATEK valores reales `SERIAL2_PROTOCOL`, `SERIAL2_BAUD`, opciones y control de flujo; validar nivel lógico de TX1 antes de conectar a PH3/RX; disponer banco inmovilizado. Después planificar conexión bidireccional TX1→pin13, pin11→RX1 y GND, arrancando MAVROS bajo SROS2 Enforce con allowlist probada. El enlace de hardware todavía no existe; no se han enviado tramas a la H743 ni cambiado sus parámetros.

## Estado de pausa — 2026-11-05

Pausa solicitada: el usuario no dispone ahora de la H743 para leerla desde Mission Planner. No continuar el tramo dependiente del hardware. UART5 queda preparado en la Orange Pi, pero no iniciar el enlace físico ni configurar baud/puerto en la FCU con valores supuestos.

Siguiente paso al reanudar: con la H743 disponible, conectar Mission Planner por su medio habitual (ESP32 DroneBridge si está operativo), guardar copia local privada de parámetros y leer firmware/revisión, `SERIAL2_PROTOCOL`, `SERIAL2_BAUD`, opciones y RTS/CTS; no escribir parámetros. Después confirmar tensión TX1 y planificar banco/cableado bidireccional con SROS2 Enforce. Todo queda local, sin commit/push/GitHub.

## Continuidad documental — 2026-11-05

Se añadió `codex_handoff/REVISION_CRITICA_EXTERNA_RRA.md` como brief para crítica técnica independiente. La pausa por falta de H743 sigue vigente. Mientras tanto, puede compartirse este documento con otro revisor si el usuario lo decide; al retomar con hardware, continuar primero por la lectura de SERIAL2 y la comprobación eléctrica en el checklist. No se autorizan por el brief cambios de parámetros, cableado o pruebas de actuación.

## Actualización de auditoría y telemetría reutilizable — 2026-11-05

**Completado:**
1. Reproducción real en SITL del frame `PARAM_VALUE` atrasado entregado dentro de la nueva consulta. Plugin anterior lo atribuyó a la nueva solicitud. Se corrigió el estado: validar msgid/identidad/type/rango; deadline común y exclusión concurrente; registrar edad de recepción; estado explícito ambiguo y fallo conservador porque MAVLink no incluye transaction ID. Se probaron retraso, pérdida y duplicación. No se añade proxy/MCU.
2. Clarificación de seguridad por capas: SROS2 limita endpoints DDS; el usuario `rra` tiene acceso UART RW; plugin allowlist minimiza código pero MAVROS conserva capacidad de enviar; ArduRover constituye otro límite no verificado en la H743. No llamar al enlace físicamente read-only.
3. `rra_telemetry` añade simulador seguro/sintético, validación de sensores, diagnóstico con edad de recepción y fixture rosbag2; propuesta de contrato estándar documentada como pendiente de acuerdo con Martín.
4. Benchmark corto Orange Pi: 0→15.5% CPU ocupado; MemAvailable 3627→3335 MiB; swap 0; temperatura ~52–53→54–55 °C; RSS acumulado ~300 MiB (incluye shared); latencia simulada local n=20, p50 2.158 ms/p95 3.078 ms. 206 mensajes/22.5 s de bag; 55 GiB libres. No es medida sostenida ni con FCU real.
5. Discrepancia H743-WING V3 vs WLITE documentada; no inferir pinout desde una guía de familia.

**Verificación final local/remota:** `rra_companion_readonly`: 13/13; `rra_telemetry`: 9/9; package telemetry compilado por colcon; integración de nodos/diagnóstico/rosbag PASS; replay real SITL post-fix PASS. Orange Pi volvió a idle, sin nodos de la prueba. Todo local; no commit/push/GitHub ni Martín. Ver `PHASE_REVIEW_SECURITY_AND_ROS2_2026-11-05.md`, `RRA_ROS2_INTERFACES.md` y `evidencias/rra-ros2-benchmark-2026-11-05/MEDICION.md`.

**Pendiente/recomendación:** con H743 aún ausente, no cablear ni escribir parámetros. Coordinar primero el contrato ROS con Martín. Cuando haya placa: identificar revisión, leer SERIALx de forma no invasiva, verificar niveles, banco desarmado/inmovilizado y recepción unidireccional. Una consulta BATT física requiere tratar el límite de correlación MAVLink antes de usar el dato como válido. No instalar Nav2/SLAM ni más infraestructura sin necesidad concreta.

## Reorientación — contrato y primer hito funcional (2026-11-05)

La revisión de software se clasificó en `CLASIFICACION_COMPONENTES_COMPANION.md`.
Se conserva el observador, las pruebas, el simulador/rosbag y los límites de
seguridad existentes; se posponen ampliaciones de plugin C++, nuevas capas
SROS2, Nav2, LiDAR, visión y modelo físico hasta especificaciones/medidas. La
funcionalidad de telemetría usa topics MAVROS estándar y no añade APIs de control.

Contrato principal provisional con Martín en `CONTRATO_INTEGRACION_COMPANION.md`;
los agreements no conocidos están marcados pendientes. Plan de cinco hitos en
`PLAN_DESARROLLO_CORTO.md`.

**Hito 1 completado:** el observador ROS consume state/mode, GNSS, IMU, batería,
odometría (velocidad) y heading de MAVROS; publica diagnósticos de salud por
fuente y latido del proceso. Simulador aislado probado y rosbag de ArduRover SITL
4.7.2 grabado/reproducido: siete topics, 369 mensajes, 61 s; verify `REPLAY_OK`.
11/11 unit tests del paquete pasan en Orange Pi y smoke integrado de siete
estados pasa. Artefacto `evidencias/sitl-telemetry-demo-2026-11-05/RESULTADO.md`.
No hardware real, H743, UART ni actuación.

**Siguiente hito:** launch/config portable y recorder selectivo, sin hardcodear
rutas o IP de casa y sin requerir Orange Pi para la lógica. Confirmar ROS distro
x86_64 disponible para Martín antes de prometer compatibilidad comprobada. Todo
permanece local; sin commits, push, GitHub o cambios al repositorio de Martín.

## Continuidad actualizada — 2026-11-05

El hito 2 quedó implementado y validado en Orange Pi ARM64; los detalles,
resultados y límite de duración efectiva del bag constan en la sección Hito 2 de
`ESTADO_ACTUAL.md` y en `evidencias/hito2-portable-execution-2026-11-05/RESULTADO.md`.
El modo MAVROS del launch arranca solo el observador; el recorder no inicia
MAVROS ni ninguna interfaz de control.

**Siguiente trabajo útil:** validar compilación/replay del paquete en el entorno
x86_64 que Martín pueda usar, una vez confirmada su distro ROS, sin instalar una
distro por su cuenta. En paralelo no queda trabajo físico seguro que adelantar
sin la H743: al disponer de ella, empezar por identificar placa/revisión, leer
firmware y SERIALx desde GCS sin escritura y comprobar niveles eléctricos antes
de la recepción UART. No abrir actuadores ni habilitar comandos.

## Actualización de disponibilidad H743 — 2026-11-07

Mission Planner por DroneBridge/TCP: capturas aportadas muestran ArduRover
V4.7.2 y `SERIAL2_PROTOCOL=2`, `SERIAL2_BAUD=57`, `SERIAL2_OPTIONS=0`.
Interpretación, procedencia y límites en `ESTADO_ACTUAL.md`,
`UART_PRECONNECTION_CHECKLIST.md` y `H743_DATOS_HARDWARE.md`. La Orange Pi sigue
separada; no hubo escritura ni cableado.

Siguiente paso: consultar sin escribir `SR2_*` (tasas de emisión) y parámetros
MAVLink/signing pertinentes o guardar copia local privada de parámetros; después
confirmar revisión/serigrafía exacta de la placa y revisar nivel eléctrico TX1
antes de diseñar el cableado. No unir placas todavía. La automatización de
Mission Planner falló al iniciar su helper; los valores se transcribieron de
capturas del usuario.

## Actualización tras lectura MAV3 — 2026-11-07

**Lectura completada desde Mission Planner:** SERIAL0/1/2 usan MAVLink2; para TELEM2 se revisó el bloque MAV3 (nombres nuevos en ArduPilot 4.7). Tasas observadas: EXTRA1/2/3, EXT_STAT, POSITION, RAW_CTRL, RAW_SENS y RC_CHAN a 1 Hz; PARAMS a 10 Hz; ADSB=0; OPTIONS=0. Coinciden con defaults. Solo lectura desde capturas; no hubo escritura, conexión Orange Pi ni prueba de tráfico real.

**Siguiente tarea útil:** identificar físicamente modelo y revisión (fotos nítidas de ambas caras/etiqueta) y verificar con fuente fiable el nivel alto de TX1 frente a la entrada UART5_RX del Orange Pi. No conectar todavía. Si ambas comprobaciones son satisfactorias, preparar banco inerte y ensayo inicial solo recepción, TX1→pin 13 y GND→pin 14, sin conectar RX1/UART5_TX. No hay que modificar parámetros de la H743 para esta comprobación.

## Seguimiento de evidencia física — 2026-11-07

Las nuevas fotos muestran la FCU real instalada y fotos de referencia del producto. La placa parece H743-WLITE, pero la serigrafía/revisión no es legible con suficiente certeza; las imágenes comerciales no identifican el ejemplar. El manual oficial asigna TX1/RX1 a TELEM2/SERIAL2 y declara I/O tolerantes a 5 V, sin especificar en ese dato la amplitud TX de salida. Por tanto, el cableado aún no está autorizado por evidencia eléctrica suficiente.

**Siguiente paso para el usuario:** no conectar nada por ahora. Enviar una foto macro enfocada de la serigrafía/revisión en la placa instalada, procurando no retirar cables ni mover componentes. Después resolver el nivel lógico TX1 frente a la entrada UART5 del Orange Pi. No cambiar parámetros FCU.

## Decisión de avanzar a telemetría UART RX — 2026-11-07

Lectura aproximada del usuario entre GND y TX1: 2,9–3,3 V en multímetro. Se acepta avanzar con un ensayo funcional de recepción UART5 unidireccional; el valor no se presenta como medida de pico. Conectar con placas apagadas Matek TX1→Orange Pi pin 13/UART5_RX y GND común→pin 14. Mantener Matek RX1 y Orange Pi pin 11/UART5_TX desconectados; no llevar alimentación entre placas. Tras comprobar los cables, alimentar por separado y capturar heartbeat/tráfico sin modificar FCU. Si no hay recepción, diagnosticar primero sin cambiar parámetros.

## Bloqueo de red para escucha UART — 2026-11-07

Tras la conexión física reportada por el usuario, SSH a la última IP `192.168.1.156` agotó el timeout. Ping 2/2 perdido, sin ARP. El portátil está en `192.168.2.2/24` (gateway `192.168.2.1`) y no tiene ruta a `192.168.1.0/24`. No se pudo inspeccionar ttyS5 ni probar recepción. No hubo cambios ni tráfico UART originado por la Orange Pi.

**Siguiente paso:** obtener la IP DHCP actual de la Orange Pi desde el router correspondiente o poner el portátil en la misma LAN; repetir SSH con la clave existente. Con acceso, escuchar ttyS5 a 57600 durante un intervalo breve con modo raw y TX desconectado, y comprobar heartbeat MAVLink. No cambiar parámetros de la controladora para resolver una falta de red.

## Siguiente acceso de red cuando la Pi está fuera de casa — 2026-11-07

Para retomar SSH sin modificar la configuración de Orange Pi: si tiene guardadas las credenciales de la Wi-Fi doméstica, habilitar en un teléfono un hotspot temporal con el mismo SSID y contraseña, banda 2,4 GHz/WPA2; conectar también el portátil al hotspot. Revisar la lista de dispositivos conectados para conocer la IP de Orange Pi y comprobar que los clientes pueden comunicarse entre sí. Después, usar la clave SSH existente para entrar y ejecutar la escucha de UART5. Si el teléfono no permite esos ajustes o bloquea tráfico entre clientes, pasar a acceso local por consola o USB-Ethernet; no alterar la UART ni la H743 para resolver la red.

## Recuperación de acceso local sin contraseña Wi-Fi doméstica — 2026-11-07

Preferencia: USB–TTL de 3,3 V para consola UART0. Orange Pi Zero 2W: pines físicos 8 TX, 9 GND, 10 RX. Cableado: adaptador RX→pin 8, TX→pin 10 y GND→pin 9; no VCC. Consola independiente del UART5 conectado a H743 en pines 11/13. Abrir terminal 115200 8N1 (la cmdline observada usa ttyS0,115200), iniciar sesión local y configurar un hotspot temporal sin poner la clave en el chat. Luego conectar portátil al mismo hotspot, localizar IP y retomar la escucha de UART5.

USB-C directo solo si USB gadget está habilitado en la imagen; no asumir que Armbian ofrece ADB/RNDIS/serial de fábrica. Alternativa local: mini-HDMI + teclado/USB host. Referencia oficial del pinout: manual Orange Pi Zero 2W.

## Acceso SSH pendiente: unir portátil a la Wi-Fi de Orange Pi — 2026-11-07

La Orange Pi está reportada conectada a Wi-Fi, pero Windows muestra `Wi-Fi: desconectado`; el portátil no comparte actualmente esa LAN. `.local` no resuelve y no se encontraron endpoints SSH en los segmentos activos inspeccionados. Próximo paso concreto: conectar el Wi-Fi del portátil a la misma red/hotspot que la Pi y volver a descubrir IP/SSH. Alternativa: leer IP DHCP en router/hotspot o ejecutar `hostname -I` por consola UART0 local.

## Hotspot confirmado; falta IP utilizable desde portátil — 2026-11-07

El hotspot muestra `orangepizero2w` MAC `e4:33:89:2e:8d:ad`; no aparece IP en la captura. El portátil no estaba conectado por Wi-Fi. Siguiente paso del usuario: unir el portátil al mismo hotspot, después repetir descubrimiento SSH, o abrir los detalles del cliente en Android para ver su dirección DHCP.

## Estado de telemetría física tras recuperar SSH — 2026-11-07

Orange Pi localizada en `10.221.18.8`, SSH `rra` correcto con clave de host previamente registrada. `/dev/ttyS5` existe y es accesible por grupo dialout; tty configurado a 57600 8N1. Lectura serial pasiva de 6 s dio 0 bytes. No se lanzaron MAVROS ni solicitudes, no hubo TX hacia FCU y no se modificaron parámetros. La conexión física reportada aún no entrega bytes observables.

Siguiente acción: confirmar que H743 sigue encendida y verificar el cable TX1→pin 13/UART5_RX más GND→pin14, retorno desconectado; repetir escucha pasiva 15 s. Si no llegan bytes, medir/observar TX1 o contrastar emisión TELEM2 y baud efectivo desde GCS; no cambiar SERIAL2 ni rates sin diagnóstico.

Repetición tras SSH: segunda escucha pasiva de 15 s a ttyS5 57600 raw devolvió también 0 bytes. No se observa recepción; sigue sin transmisión desde Orange Pi.

El usuario confirma que la conexión física sigue hecha. Tercera escucha RX pasiva de 15 s a 57600 en `/dev/ttyS5`: 0 bytes. La Orange Pi mantiene SSH en 10.221.18.8. Siguiente prueba de diagnóstico: medir con multímetro en el extremo Orange Pi entre pin físico 13 (UART5_RX, ya conectado a TX1) y pin14/GND mientras la H743 está encendida; comparar con el nivel aproximado 2,9–3,3 V que el usuario había visto en TX1. Esto permite distinguir llegada eléctrica al pin de un problema de UART/baud. No transmitir ni modificar parámetros FCU.

## Hito UART RX completado — MAVLink2 físico recibido — 2026-11-07

Escucha pasiva 15 s en UART5 57600: 10.692 bytes. Se identificó y validó el CRC de una trama MAVLink2 HEARTBEAT (msgid 0, sysid 1, compid 1; tipo rover y autopiloto ArduPilot; estado ACTIVE). Recepción física TELEM2→Orange Pi comprobada. No se transmitió desde la Orange Pi, no se conectó retorno y no se cambiaron parámetros FCU.

**Siguiente trabajo funcional:** arrancar MAVROS con el perfil observador actual sobre `serial:///dev/ttyS5:57600`, comprobar conexión/estado y exponer telemetría ROS estándar. Mantener RX1 desconectado durante este paso; registrar tópicos y resultado.

## MAVROS físico RX + diagnóstico ROS completados — 2026-11-07

Se validó en el hardware reportado: MAVROS serial 57600 detecta heartbeat ArduPilot. Con allowlist `sys_status`, `global_position`, `imu`, `local_position`, el observador `rra_telemetry` publica diagnóstico ROS con estado HOLD/desarmado, GNSS, orientación IMU, batería (~11,59 V/~95%), velocidad 0 y rumbo (~13,7°); todos los ítems del snapshot aparecen disponibles/nivel OK, edad de recepción <1 s. Coordenadas exactas omitidas de documentación. FCU comunica `PreArm: Radio failsafe on`; no corregido ni alterado.

MAVROS agotó el request automático AUTOPILOT_VERSION por retorno desconectado; no concluir firmware no compatible. No se usó SROS2; prueba ROS_DOMAIN_ID=205/LOCALHOST solamente. Todos los nodos temporales se cerraron y se confirmó ausencia de procesos. Sin cambios de parámetros, armado o actuación.

**Siguiente hito:** demostrar registro y reproducción de telemetría física con rosbag2 corto y lista selectiva; confirmar que el observer recibe replay. A continuación, revisar forma de evitar request de versión al arrancar en RX-only. El regreso UART sigue abierto; no consultar parámetros ni iniciar operaciones bidireccionales.

## Registro/replay físico completado — 2026-11-07

MCAP local privado en Orange Pi: `~/rra_ws/recordings/rra-h743-uart-rx-20261107-154256`, 80,4 KiB, 58 msgs, 7 topics, 6,88 s efectivos (limit requested 10 s). Replay aislado domain206/LOCALHOST recuperó State connected/HOLD/disarmed y diagnostics para GPS, IMU, batería, velocidad y heading. El bag puede contener GNSS preciso y se mantiene solo local, fuera de Git.

Pendiente: investigar una terminación segmentation fault reportada una vez al cerrar MAVROS tras SIGINT con los cuatro plugins de telemetría; no hay proceso restante ni core encontrado. El retorno UART permanece desconectado; MAVROS puede intentar emitir solicitudes de capabilities/version, que timeoutean en esta configuración RX-only. Próximo hito recomendado: capturar y consultar la batería/registros del FCU no es necesario; antes de ampliar, resolver el cierre de MAVROS y el `PreArm: Radio failsafe on` con inspección de solo lectura. No cambiar failsafe ni conectar retorno en esta fase.

## Seguimiento de cierres y failsafe — 2026-11-07

Dos cierres de MAVROS con SIGINT y `wait EXIT=0` en perfiles sys_status y telemetría contradicen como reproducible el segfault único reportado en la grabación. Se mantiene como evento aislado a vigilar, no se abre refactorización por ahora. El mensaje previo `PreArm: Radio failsafe on` no se repitió en estos probes cortos; estado del failsafe sigue sin determinar, no asumir que está resuelto. MAVROS mantiene timeout de AUTOPILOT_VERSION por retorno ausente; compatible con diseño RX-only.

Siguiente tarea: conservar RX-only; preparar un arranque manual repetible mediante argumentos externos (ruta/baud) y confirmar los diagnósticos/eventos FCU en una ventana más larga. Antes de cambiar failsafe o conectar retorno, revisar Mission Planner con el receptor presente y acordar expresamente cualquier ajuste.

## Prioridad siguiente: bidireccionalidad y alimentación integrada — 2026-11-07

El usuario confirma que quiere acelerar el retorno MAVLink y alimentar Orange Pi desde Matek. Secuencia corta:
1. Con Pi alimentada externamente por ahora, añadir MATEK RX1 ← Orange Pi pin11 UART5_TX (con el sentido de retorno) manteniendo TX1→pin13, baud 57600 y masa común. Probar el plugin fijo existente para AUTOPILOT_VERSION y BATT_MONITOR, sin parámetros de escritura ni servicios de control; comunicar si se mueve el servo solo como observación, sin probarlo.
2. Medir una vez el pad Vx contra GND. Si es 5V, pasar alimentación a pin2/4 Orange Pi 5V y pin6 GND; apagar Pi y retirar USB-C antes de usar esa alimentación. Vx 8A cont./10A pico es preferible al BEC5 general 2A compartido; no usar 4V5 ni alimentar GPIO con Vx a 6/7.2V. Si no está en 5V, definir alternativa 5V/3A o jumper con datos del servo.
3. Configurar arranque manual portátil de MAVROS + observador y rosbag corto posterior con ambas direcciones habilitadas.

No instalar autostart. La prioridad es una prueba funcional corta y resultados, sin nuevas capas SROS2. No configurar armed/mode/motion en esta fase.

## Hito alimentación desde Matek validado en uso — 2026-11-07

Vx medido por usuario a 5,1 V y conectado a Orange Pi; SSH sigue disponible, ttyS5 RX recibió 3.591 bytes/5 s tras cambio, Pi arriba y sin corte durante la prueba. Esto valida arranque y recepción básica desde Vx; no carga pico servo. Continuar con retorno: conectar Orange Pi pin11 UART5_TX a Matek RX1/TELEM2, conservando TX1→Pi pin13 y masa; luego probar AUTOPILOT_VERSION y BATT_MONITOR con plugin fijo.

## Retorno UART físico conectado y probado — 2026-11-07

El usuario conectó el retorno UART5_TX de Orange Pi (pin físico 11) a RX1/TELEM2 de Matek; se mantuvieron la recepción TX1→UART5_RX (pin 13), baud 57600 y masa común. Con MAVROS temporal en el perfil mínimo `sys_status,rra_readonly_version`, la consulta fija `request_batt_monitor` obtuvo respuesta en 54 ms: `PARAM_VALUE` de sysid/compid 1/1, nombre `BATT_MONITOR`, tipo MAVLink 2 y valor entero 4. Esto confirma el camino de transmisión Orange Pi→FCU y el retorno FCU→Orange Pi para una consulta MAVLink. El resultado lleva `correlation_status=ambiguous_no_mavlink_transaction_id`: identifica una respuesta compatible, no prueba de forma infalible que esa trama concreta pertenezca a la solicitud recién emitida.

La consulta fija `request_autopilot_version` fue aceptada localmente, pero no se observó publicación en `/mavros/readonly_version/autopilot_version`; MAVROS agotó su solicitud de AUTOPILOT_VERSION y usó capacidades predeterminadas. El comando implementado (MAV_CMD_REQUEST_MESSAGE 512, param1=148) coincide con la especificación MAVLink y el procedimiento documentado por ArduPilot; por tanto no se cambia el código a ciegas. La versión ArduRover 4.7.2 (`fb773567`) sí se vio antes en Mission Planner, evidencia independiente de esta consulta.

Prueba sin cambios de parámetros, armado, modo ni consignas de movimiento. Se conserva la advertencia observada anteriormente `PreArm: Radio failsafe on`; no se intervino. No se usó SROS2. La solicitud BATT_MONITOR fue una lectura fija; no se abrió acceso genérico a comandos o escritura. Se detuvo el ensayo temporal de MAVROS al terminar.

**Siguiente paso práctico:** mantener el cableado como está y usar la telemetría ROS estándar más el diagnóstico/rosbag físico ya preparados. Investigar AUTOPILOT_VERSION por separado con captura de respuesta/ACK cuando resulte útil; no bloquea la integración de telemetría. No hace falta conectar nada más para continuar.

## Sesión física bidireccional: observador y rosbag — 2026-11-07

Orange Pi conectada por SSH (`orangepizero2w`, `/dev/ttyS5`, ROS 2 Lyrical). Arranque MAVROS corregido tras una primera línea de comando inválida (falló antes de abrir el UART, sin transmisión). En el arranque válido se aplicó perfil temporal de allowlist `sys_status`, `global_position`, `imu`, `local_position`, `rra_readonly_version`; los plugins `command` y `param` quedaron ignorados. Dominio ROS 205 y descubrimiento LOCALHOST. Se arrancó `rra_telemetry` con fuente MAVROS y se grabó en la propia Pi: `~/rra_ws/recordings/rra-h743-uart-duplex-20261107-1626`, MCAP 77,8 KiB, 62 mensajes, 7 tópicos (State 18; batería, rumbo, GPS, odometría local e IMU 8 cada uno; diagnósticos 4), 7,96 s efectivos. La sesión capturó datos físicos y la bolsa permanece en la Orange Pi; puede incluir ubicación GNSS, no copiar a documentación compartida.

Al cierre controlado SIGINT de MAVROS volvió a aparecer `Segmentation fault` en `ros2run` (ya es una segunda ocurrencia total, aunque no consecutiva en los ensayos anteriores). El executor informó terminación; no se observó luego proceso MAVROS/observador activo. No atribuir todavía el crash a un plugin concreto. Se mantiene como incidencia reproducible ocasional en cierre físico que requiere aislarse antes de confiar en cierres automáticos prolongados.

La reproducción se inició en domain206, pero la sesión SSH se perdió durante esa validación. El portátil informa ahora Wi-Fi 192.168.2.2, mientras la Pi se había alcanzado en la red 10.221.18.0/24; no se pudo recuperar el resultado de replay ni verificar si la Pi sigue encendida o si la dirección cambió. No afirmar que replay pasó. Reconectar el portátil a la red/hotspot de la Pi o descubrir su IP actual, inspeccionar la Pi y completar replay de la bolsa existente. La grabación y validación de metadatos sí finalizaron antes de perder el acceso.

Se observaron avisos FCU `PreArm: Check mag field (xy diff:157–159>100)` y `PreArm: Radio failsafe on`; son telemetría/diagnósticos existentes, no se modificaron parámetros ni failsafes. No se envió armado, cambio de modo ni consigna de movimiento. El test de retorno BATT_MONITOR de 54 ms se documenta en la sección previa; AUTOPILOT_VERSION sigue sin respuesta.

## Intento de reconexión tras pérdida SSH — 2026-11-07

El portátil volvió a la Wi-Fi/hotspot 10.221.18.0/24 (IP 10.221.18.142, gateway 10.221.18.248). La IP previa de Orange Pi 10.221.18.8 no responde por ICMP ni SSH. Sondeo concurrente local de la subred y vecinos ARP solo detectó el portátil y gateway; no se detectó la MAC Pi `e4:33:89:2e:8d:ad` ni otro SSH activo. Esto no determina si la Pi está apagada: también podría estar conectada a otra Wi-Fi o tener una IP/SSID distinto. Replay y consulta de sus procesos quedan en pausa hasta recuperar su IP/acceso.

## Reanudación y nueva caída de acceso — 2026-11-07

Tras el reinicio manual reportado por el usuario, la Orange Pi reapareció en `10.221.18.8` con MAC `e4:33:89:2e:8d:ad`; SSH y ROS 2 Lyrical funcionaban. No había procesos MAVROS/rosbag heredados. Al revisar la bolsa anterior (`...-1626`) tanto el MCAP como metadata.yaml estaban a 0 bytes pese a que antes `ros2 bag info` había informado 77,8 KiB; no se hallaron errores mmc/ext4 en dmesg y el rootfs tenía 55 GiB libres. Esto apunta a que aquella evidencia no sobrevivió el corte/reinicio, sin evidencia suficiente para atribuir causa.

Se volvió a iniciar MAVROS/observador y se grabó otra sesión con mismo allowlist/domain; el log reportó cierre correcto de rosbag y `ros2 bag info` identificó el bag `~/rra_ws/recordings/rra-h743-uart-duplex-20261107-1654`: MCAP 39.386 bytes y metadata.yaml 5.948 bytes en una comprobación inmediata, tras `sync`. Sin embargo, la verificación remota posterior se interrumpió al caer de nuevo SSH; no se conoce si la Pi sigue asociada ni se completó replay. Se debe revalidar tamaños y ejecutar replay antes de otra pérdida de alimentación.

Tras esa captura, el portátil seguía conectado a `DIGIFIBRA-PyHA` (10.221.18.142; hotspot gateway .248), pero la Pi volvió a desaparecer del ping/SSH y de vecinos. Estado/causa de caída de Wi-Fi aún no identificados; una posible pérdida de alimentación o asociación Wi-Fi no está confirmada. Mantener la Pi encendida y recuperar la red antes de reiniciarla de nuevo para comprobar persistencia de archivos.

## Captura física validada y replay PASS — 2026-11-07

Tras el reinicio de la Orange Pi reportado por el usuario, el hotspot mostró de nuevo `orangepizero2w` (MAC `e4:33:89:2e:8d:ad`); SSH confirmó IP `10.221.18.8`. La Pi permaneció accesible durante esta sesión de prueba. `iw dev wlan0 get power_save` informó `Power save: off`; la causa de que no se asociara en el arranque anterior queda sin determinar. No atribuir a ahorro de energía Wi-Fi.

Corrección sobre la bolsa intermedia `rra-h743-uart-duplex-20261107-1654`: su metadata contiene solo 4 mensajes, `State` conectado=false y diagnósticos/sensores sin datos. El replay de esa bolsa expuso ausencia de telemetría útil; queda descartada como evidencia funcional aunque MCAP (39.386 B) y metadata (5.948 B) sean legibles.

En el arranque actual, MAVROS sobre `serial:///dev/ttyS5:57600` publicó `/mavros/state` conectado=true, armado=false, modo HOLD. Allowlist temporal: `sys_status`, `global_position`, `imu`, `local_position`, `rra_readonly_version`; plugins `command` y `param` ignorados. `rra_telemetry` publicó un diagnóstico en el que conexión, GPS, IMU, batería, velocidad y rumbo estaban disponibles/nivel OK; el verificador omitió coordenadas.

Nueva grabación útil, con `rosbag2` en MCAP y `sync` al acabar: `~/rra_ws/recordings/rra-h743-uart-live-20261107-1700`, 71.981 B más metadata de 5.947 B. Metadata: 51 mensajes / 7 tópicos (State 16; IMU, odometría local, heading, batería y GPS 6 cada uno; diagnostics 5). Replay en ROS_DOMAIN_ID=207 y discovery LOCALHOST PASS: se recibió un mensaje de cada tipo en los siete tópicos; `/mavros/state` siguió como connected=true, armed=false, HOLD; batería presente con voltaje positivo; diagnósticos replayados indicaron conexión y cinco sensores disponibles. Subscriber usó sensor QoS best-effort; el primer verificador con QoS reliable no era compatible y fue corregido. Coordenadas GNSS no se imprimieron; la bolsa queda privada en la Pi.

Cierre controlado de este MAVROS con SIGINT PASS: executor terminó y no quedaron procesos MAVROS/observer/rosbag activos. El segmentation fault de sesiones anteriores no se reprodujo esta vez; se conserva como incidencia ocasional pendiente de aislar, sin refactorización por ahora. MAVROS aún registra timeout en la consulta de versión y usa capacidades predeterminadas. `PreArm: Radio failsafe on` se recibió por MAVLink; no se alteró failsafe ni se enviaron órdenes de movimiento o cambios de parámetros.

**Hito completado:** captura y reproducción de telemetría física H743→ROS 2 verificadas. **Siguiente paso práctico:** mantener esta lista de interfaces como base para la integración ROS del rover/modelo `base_link`; en paralelo, tratar la asociación Wi-Fi al arranque como incidencia separada con observación de logs al próximo arranque, sin más reinstalaciones. No hace falta conectar cables adicionales.

## Arranque reproducible, reconexión y AX10 — preparación local (2026-11-07)

Se añadieron localmente `rra_telemetry/launch/companion_uart.launch.py`, `config/mavros_hardware.yaml` y `scripts/start_companion_hardware.sh`. El launch inicia MAVROS + `rra_state_observer`, usa como defecto `serial:///dev/ttyS5:57600`, ROS_DOMAIN_ID 205 y discovery LOCALHOST; URL, ROS setup y overlay pueden sustituirse. La allowlist cargada contiene sys_status, global_position, imu, local_position y rra_readonly_version; command y param quedan fuera. Se declaró `mavros` como dependencia de ejecución. Sintaxis Bash (`bash -n`) y parseo Python del launch pasan localmente. No se ha compilado ni desplegado en la Pi porque la IP anterior `10.221.18.8` agotó el timeout SSH y no apareció en el escaneo local.

El procedimiento operativo se documenta en `COMPANION_UART_ARRANQUE.md`. En el último SSH remoto conocido, `~/rra_ws/src` no existía aunque sí estaban `build` e `install`; antes de copiar, comprobar de nuevo ese estado para preservar cualquier fuente que haya aparecido. No iniciar autostart/systemd.

**Reconexión física:** no ejecutada. Cuando SSH vuelva, arrancar la receta, comprobar connected=true, el usuario desconecta solo Matek TX1→Orange Pi pin13 durante 12 s y vuelve a conectar; observar false→true sin cerrar MAVROS. No se interviene el retorno ni se cambian parámetros/actuadores.

**AUTOPILOT_VERSION:** el plugin fijo transmite `MAV_CMD_REQUEST_MESSAGE` (512), param1=148. La documentación oficial de ArduPilot describe command 512 y param1 como message ID para consultar una instancia: https://software.ardupilot.org/dev/docs/mavlink-requesting-data.html . Por tanto, el formato elegido es válido; eso no identifica la causa física del timeout. El timeout `mavros.sys` que dice `command plugin service call failed` corresponde además al sondeo automático del plugin sys_status cuando el plugin genérico `command` está excluido; la consulta local fija también requiere validar que llegue AUTOPILOT_VERSION. Trigger exitoso solo confirma envío/request_id, no respuesta. La siguiente sesión suscribirá primero al tópico local, hará una sola consulta fija y registrará si llega el mensaje. No habilitar command plugin genérico ni cambiar parámetros por ahora; MAVLink ACK no está expuesto por el plugin actual.

Se añadió `AX10_MEDICIONES.md` como plantilla vacía y procedimiento. No se han medido wheelbase, vías, radios/circunferencia, ángulos de rueda ni poses. Para crear el modelo sin inventar valores, Juan debe completar medidas del chasis real y acordar con Martín el origen de base_link. GNSS principal/secundario e IMU se registran según montaje real; LiDAR y encoder quedan `NO INSTALADO` si aún no están montados.

Al terminar esta preparación no se ejecutaron pruebas físicas nuevas, no se emitió ningún comando de vehículo, no se modificó configuración ArduRover ni se escribió en GitHub. Las modificaciones locales previas del árbol se conservaron.

## Diagnóstico de pérdida de acceso Orange Pi — 2026-11-07

Tras el reinicio manual, el hotspot mostró la MAC de la Pi y el portátil confirmó `10.221.18.8` → `e4:33:89:2e:8d:ad`. SSH llegó a OpenSSH 10.2 de Ubuntu y la clave ed25519 coincidió con la registrada para `192.168.1.156`; no era un error de clave ni una IP de otro equipo. La sesión root ejecutó las consultas de diagnóstico.

Datos del arranque observado: `uptime` informó 7 min; `ssh` y `wpa_supplicant` activos; `NetworkManager` inactivo. `iw dev wlan0 get power_save` informó `off`; la interfaz aparecía `UP,LOWER_UP`, `state UP mode DORMANT`, con 0 errores y 0 paquetes descartados RX/TX en esa captura. El diario del arranque mostraba el inicio e inicialización correcta de `wpa_supplicant`, sin un evento explícito de desconexión en el fragmento disponible. Esto no demuestra que Wi-Fi permaneciera asociado antes del reinicio ni excluye una caída de alimentación.

No se pudo inspeccionar el arranque anterior: `journalctl -b -1` informó que no había diario persistente, y `last` no está instalado. `who -b` indicó arranque 19:00 mientras `uptime` decía 7 minutos a las 19:44 +01; las fuentes de hora/arranque no son coherentes y no debe usarse `who -b` como prueba de la hora exacta. El mensaje de `sunxi-wdt` solo indica watchdog habilitado, no que se haya disparado. En las líneas filtradas no apareció un aviso explícito de undervoltage ni de apagado térmico; su ausencia no descarta una caída brusca de 5 V.

Se escribió `/etc/systemd/journald.conf.d/90-rra-diagnostics.conf` con `Storage=persistent`, `SystemMaxUse=32M`, `SystemMaxFileSize=8M`, `RuntimeMaxUse=8M` y `MaxRetentionSec=7day`; se reinició `systemd-journald` y `journalctl --flush` terminó. `journalctl --list-boots` mostró el arranque actual y el uso informado fue 8 MB. `systemd-tmpfiles --create --prefix /var/log/journal` falló porque `/var/log/journal` es un symlink; su destino todavía debe comprobarse y la persistencia real se confirma cuando un siguiente reinicio deje visible el boot previo. No se tocó Wi-Fi, SSH, UART, MAVROS ni parámetros de ArduRover.

**Conclusión provisional:** no hay evidencia de que SSH inactivo active suspensión; en el arranque observado el ahorro Wi-Fi estaba desactivado. La incidencia anterior sigue sin causa confirmada: puede ser una desasociación Wi-Fi o un reinicio/corte de alimentación. Próxima observación, sin reinicio manual: comprobar `iw dev wlan0 link`, uptime y `journalctl --list-boots`; al siguiente corte, tras recuperar SSH, comparar el boot anterior y buscar mensajes de `wpa_supplicant`, kernel y undervoltage. Verificar también el destino de `/var/log/journal`.

## Siguiente paso después del arranque reproducible — 2026-11-07

El arranque manual con MAVROS+observador ya se compiló y validó contra la H743-WLITE. Siguiente: aprovechar que el launch permanece activo y probar una petición única al servicio de versión del plugin fijo `rra_readonly_version`, con el tópico de respuesta suscrito antes de enviar. Registrar request_id, respuesta/timeout y desconexión; no habilitar el plugin genérico `command` para silenciar el sondeo automático MAVROS.

Después, comprobar reconexión UART con MAVROS activo (interrumpir brevemente solo TX1→UART5_RX y observar false→true), sin cambiar parámetros. Si la Orange Pi vuelve a perder acceso, conservar el encendido y revisar su diario persistente antes de reiniciarla.

No crear modelo físico/cinemático AX10 hasta recibir medidas reales de wheelbase, vías, radio rodante, límites de dirección y posiciones de sensores.

## Prioridad vigente: integración física práctica — 2026-11-08

1. Documentar, como reporte del usuario, MANUAL/RC, armado/desarmado, HOLD,
   dirección/tracción y misión AUTO de 3–4 waypoints completada el 2/11; marcar
   LOITER resuelto sin inventar causa/fecha y GNSS último dato reportado HDOP
   0,6 + error estimado 0,3 m (no exactitud absoluta). Hecho en README,
   Roadmap y estado vigente.
2. Completar `AX10_MEDICIONES.md`: distancia entre ejes, vías, radio/circunferencia
   rodada, radio y diámetro de giro, ángulos de ambas ruedas, PWM centro/extremos,
   distancia de frenado/velocidad y posiciones/orientaciones de sensores.
3. HC-SR04: solo propuesta S4/GPIO53 TRIG y S5/GPIO54 ECHO. Hacer inventario y
   backup de parámetros por GCS; confirmar placa, parámetros y firmware; luego
   SITL 4.7.2. La contradicción documental sobre parada en AUTO queda abierta;
   no asumir comportamiento. Conexión/parametrización física requieren permiso.
4. Cámara: identificar UVC y puerto host disponible en Zero 2W; medir consumo
   junto con Vx/Pi; captura breve local C1. No instalar software ni conectar
   físicamente en esta fase documental.
5. Solo tras pruebas S0–S2/C0–C1 y autorización física, organizar salida
   supervisada con RC; la primera puede limitarse a detección y vídeo. No llamar
   «parada AUTO validada» hasta superar repetición de campo documentada.

Detalles en `HC_SR04_H743_INTEGRACION.md`, `CAMARA_USB_ORANGE_PI.md` y la ficha
de dimensiones `AX10_MEDICIONES.md`.

## Siguiente acción inmediata: lectura del HC-SR04 — 2026-11-08

El usuario reporta que el sonar ya está cableado y pide iniciar las pruebas. La Orange Pi está accesible y MAVROS confirma heartbeat de la H743 por UART5; hace falta capturar el estado actual de la FCU antes de activar el driver. En Mission Planner, conectado al vehículo, guardar el conjunto completo de parámetros actuales como `.param` en `codex_handoff/evidencias/sonar-20261108/` y facilitar ese archivo. Revisaremos `SERVO4_FUNCTION`, `SERVO5_FUNCTION`, `RNGFND1_*`, `PRX1_TYPE` y `AVOID_ENABLE`; no se ha modificado nada todavía.

Después, configurar únicamente lectura del rangefinder con el estado previo guardado, comprobar distancia/no-eco desde Mission Planner y añadir temporalmente el plugin MAVROS `distance_sensor` para que ROS 2 lo publique. Mantener `PRX1_TYPE`/`AVOID_ENABLE` sin cambios; la respuesta ante obstáculos y el movimiento quedan para otra fase. La cámara USB y las medidas físicas AX10 siguen pendientes.

## HC-SR04: próximo avance — actualización 2026-11-08

Export leído: `SERVO4_FUNCTION=0`, `SERVO5_FUNCTION=0`, `RNGFND1_TYPE=0`, todos los `PRX*_TYPE=0`, `AVOID_ENABLE=3`, `FENCE_ENABLE=0`. Candidatos locales de lectura y reversión están en `evidencias/sonar-20261108/`; no se han escrito a la H743. Dado que el bit de proximidad ya está incluido en `AVOID_ENABLE=3`, conservar todos los `PRX*_TYPE=0` durante esta prueba.

La prueba física aún no se ejecutó. Recuperar SSH desde una red alcanzable a la Orange Pi (última IP `10.221.18.8`; el portátil aparece ahora en `192.168.2.2`), comprobar procesos antes de iniciar otro launch y volver a consultar estado vivo. Después cargar solamente la configuración `RNGFND1` y GPIO prevista para lectura, verificar distancias con el rover quieto y publicar el mensaje a ROS usando `distance_sensor`. No habilitar evitación ni consignas. Confirmar que la lectura repetida coincide con Mission Planner antes de cerrar el hito.

## Siguiente paso — completar lectura HC-SR04 (2026-11-08)

1. En Mission Planner, recuperar la tabla completa de parámetros tras la recarga incompleta; si sigue vacía, reconectar TCP y refrescar parámetros.
2. Verificar que solo están aplicados `SERVO4_FUNCTION=-1`, `SERVO5_FUNCTION=-1`, `RNGFND1_TYPE=30`; completar `RNGFND1_STOP_PIN=53`, `RNGFND1_PIN=54`, `RNGFND1_ORIENT=0`, `RNGFND1_MIN=0.2`, `RNGFND1_MAX=2.0` y leerlos de vuelta. Exportar el estado posterior.
3. Reiniciar la H743 solo después de confirmar todos los campos. Rover inmóvil: comprobar una lectura estable con objetivo plano y anotar distancia real vs. Mission Planner. No activar PRX/evitación ni movimiento.
4. Cuando se restablezca SSH a Orange Pi, inspeccionar procesos y añadir `distance_sensor` temporalmente a MAVROS; contrastar tópico ROS con Mission Planner.
5. Documentar cinco lecturas a cada distancia de prueba; cámara USB y medidas geométricas AX10 siguen pendientes.

## HC-SR04 — parámetros ya guardados; falta validación de lectura (2026-11-08)

Mission Planner confirmó los tres cambios pendientes: `RNGFND1_MAX=2`, `RNGFND1_PIN=54` y `RNGFND1_STOP_PIN=53`. Con valores anteriores ya aplicados, queda `SERVO4_FUNCTION=-1`, `SERVO5_FUNCTION=-1`, `RNGFND1_TYPE=30`, `RNGFND1_MIN=0.2`, `RNGFND1_ORIENT=0`. `PRX1_TYPE`…`PRX5_TYPE=0`; `AVOID_ENABLE=3` sin modificar. No hubo movimiento ni se activó proximidad.

Siguiente: confirmar que el rover está estacionario y desarmado; reiniciar H743 (el usuario puede hacerlo o pedirnos que lo hagamos por Mission Planner), reconectar GCS y comprobar lectura estable con blanco plano a 0.4, 0.6 y 1.0 m. Después verificar no-eco y contrastar al menos un tópico MAVROS `distance_sensor`. Mantener medidas físicas del AX10 y cámara USB en cola.


## Hito sonar: primera telemetría física recibida (2026-11-08)

Mission Planner recibe DISTANCE_SENSOR (#132) de H743 a 2 Hz; muestra de 81 cm, límites 20–200 cm, orientación frontal y tipo ultrasonido. Falta confirmar contra distancias físicas medidas: siguiente ensayo estático con blanco plano a 0,50 m y 1,00 m y registrar cambios. Luego identificar la IP actual de la Pi desde clientes del hotspot y validar el tópico MAVROS. El portátil no alcanza la IP anterior 10.221.18.8 (actual 192.168.2.2/gateway 192.168.2.1). La H743 está DISARMED con aviso de failsafe de radio. No habilitar PRX/evitación ni movimiento.


## Diagnóstico de caídas prolongadas de Orange Pi — 2026-11-08

La Pi volvió a desaparecer del hotspot después de un intervalo. Reporte físico: LED rojo fijo, LED verde dejó de parpadear. SSH no responde en el alias ni en la IP conocida 10.221.18.8; aún no se conoce IP nueva. Esto es compatible con pérdida Wi-Fi, cuelgue de Linux, alimentación marginal o problema de microSD/arranque; el LED no discrimina por sí solo. El manual oficial dice que rojo queda encendido con alimentación y verde es programable (se espera parpadeo al entrar en kernel): https://orangepi.net/wp-content/uploads/2023/10/OrangePi_Zero2w_H618_User-Manual_v1.1.pdf, sección 3.5. Diagnóstico histórico 2026-11-05 tuvo wlan0 power_save=off y enlace fuerte. Próximo fallo: verificar si sigue en la lista de clientes del hotspot y anotar la IP; cuando vuelva SSH, recoger logs del boot anterior y revisar estado eléctrico/temperatura. Si hace falta separar cuelgue vs Wi-Fi, usar HDMI o consola UART debug 3,3 V. No cambiar red/SSH, no añadir servicios, ni tocar cableado antes de capturar estado.


## Orange Pi reaparece tras reinicio — 2026-11-08

Reporte del usuario: vuelve a parpadear LED verde y orangepizero2w aparece conectado al hotspot. No obstante, el alias local rra-companion continúa apuntando a 10.221.18.8; desde el portátil 192.168.2.2 no se alcanzó esa IP y la dirección DHCP actual no está disponible, así que no se pudieron leer logs. Próximo: obtener IP actual desde detalle de cliente hotspot/router o acceso local; entonces leer logs del boot previo y comprobar registros de kernel, almacenamiento, Wi-Fi y alimentación antes de cambiar nada.


Reintento SSH solicitado por el usuario (2026-11-08 18:53:09): alias rra-companion sigue resolviendo a 10.221.18.8; conexión TCP/22 agotó timeout tras 3 s (OpenSSH 9.5p2, BatchMode; sin prompt de clave). No se pudieron obtener logs. Requiere IP actual alcanzable o acceso a la misma subred sin aislamiento entre clientes.


## Resultado: revisión de logs Orange Pi — 2026-11-08

SSH a 10.221.18.8 verificado. Logs de cuatro arranques: el anterior al actual termina 18:45:29 sin apagado ordenado; el usuario ya había reiniciado manualmente, así que no revela causa del bloqueo. Sin OOM, panic/oops, watchdog reset, MMC timeout/I/O ni EXT4 errors. SDXC 59.5 GiB detectada y raíz EXT4 montada r/w (2.6 GiB usados, 55 GiB libres). Boot previo reconectó Wi-Fi tras un rechazo de asociación; después no hay evento de desconexión. Ahora wlan0 power_save=off, RSSI -51 dBm, cero errores/drops, temperatura 43.2–44.3 °C. No hay fuente hwmon/IIO de voltaje ni evento de undervoltage, por lo que no se puede descartar caída transitoria. Siguiente prueba recomendada: medir 5 V en la entrada de Pi bajo operación desde Matek Vx y comparar con una alimentación USB-C regulada conocida; mantener software intacto hasta separar alimentación vs. cuelgue.

## Siguiente hito práctico: validar frecuencia y registro del sonar — 2026-11-08

1. Mantener el launch Companion UART activo y observar `/mavros_node/rangefinder_pub` durante 30–60 s; comparar frecuencia/estabilidad con Mission Planner (2 Hz) y probar a 30 cm y 90 cm si el usuario mantiene esos blancos medidos.
2. Registrar una rosbag2 breve solo del tópico de distancia y reproducirla; guardar evidencia pequeña en la carpeta `evidencias/sonar-20261108`.
3. Si las lecturas y la frecuencia son coherentes, integrar el tópico en el diagnóstico/telemetría estándar del RRA y documentar los metadatos del sensor. No habilitar proximidad ni evitación todavía.

Dependencia: H743 conectada y sensor con blanco fijo. Reutilizable por Martín: tópico estándar `sensor_msgs/Range` y YAML de configuración, independiente de hardware de cómputo.

## Preparar transferencia de telemetría real a Martín — 2026-11-08

Hecho localmente: capturar todos los tópicos anunciados por el Companion por 57 s en rosbag2 SQLite, mantener los mensajes crudos completos y verificar metadata, hash Pi→PC y reproducción en dominio ROS aislado. El bundle listo está en `docs/companion_handoff_martin_2026-11-08/`. El usuario autorizó publicar el trabajo directamente en `main`. Se configuró `pull.rebase=true`, se ejecutaron pulls con rebase antes de la publicación y el push normal a `origin/main` terminó correctamente en `e81d973`; la verificación confirmó el mismo HEAD local/remoto. No se publicó `feature/orangepi-ros2`. Próximo: acordar con Martín distro ROS, namespace, QoS, frames, datum GNSS/heading y correlacionar la tasa Range (aprox. 1 Hz en ROS vs 2 Hz indicado en Mission Planner). Quedan pendientes de acuerdo con Martín: ROS distro x86_64/ARM64, namespace, QoS, frames y convención GNSS/heading; también correlacionar la tasa Range (aprox. 1 Hz en ROS vs 2 Hz visto por Mission Planner).


