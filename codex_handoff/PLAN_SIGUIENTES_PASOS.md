# Plan para la siguiente sesión

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
