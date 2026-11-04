# RRA: contexto para continuidad local

Actualizado: 2026-11-03. Datos de estado y comprobaciones: [ESTADO_ACTUAL.md](ESTADO_ACTUAL.md).

## Objetivo y responsabilidades

Rover Rural Autónomo (RRA) desarrolla por etapas la supervisión, telemetría y
autonomía de un rover rural. El repositorio compartido es
<https://github.com/Gonellarro/RRA>; su propietario es Martín. El compañero
provisional se desarrolla en la Orange Pi de Juan. Martín desarrolla de forma
independiente el compañero definitivo; la integración y las interfaces comunes
deben coordinarse con él, sin presumir qué ha implementado fuera del repositorio.

La arquitectura prevista se basa en un chasis Axial AX10 Toyota Land Cruiser
83 1/10 y una MATEK H743-WING V3 con ArduRover. La H743 conserva motor,
dirección, modos, failsafes y funciones críticas. El companion se destina a ROS 2,
diagnóstico, telemetría, registro y sensores; no controla PWM directamente.
El GNSS UM982+ RTK de doble antena y el encoder AS5047P son previstos; no se ha
comprobado aquí su instalación o conexión. Tampoco se ha comprobado que la H743
esté conectada a la Orange Pi ni su estado físico. La Orange Pi Zero 2W sí ha
respondido por SSH y reporta 3,8 GiB de RAM y almacenamiento raíz de 58 GiB.

## Decisiones y límites

- ROS 2 Lyrical y MAVROS están instalados; la prueba ROS y el arranque MAVROS
  en loopback pasaron. Se ha probado un enlace unidireccional con ArduRover SITL
  aislado y un observador de estado. La batería en la primera simulación fue
  inválida; con el monitor habilitado solo en SITL pasó. No se ha validado
  conexión al vehículo físico.
- Priorizar interfaces ROS estándar y módulos portables al companion definitivo.
  No inventar conexiones, velocidades de puerto ni parámetros de la H743.
- Empezar por simulación y observación. MAVROS puede exponer interfaces de
  escritura: instalarlo o suscribirse a tópicos no garantiza aislamiento de
  órdenes. Diseñar y verificar cualquier límite antes de conectarlo a hardware.
- No emitir órdenes de armado, movimiento o cambio de modo ni activar motores
  o actuadores. Cualquier ensayo físico requiere procedimiento y autorización.
- Mantener separados simulación, banco y rover físico; una prueba SITL no
  demuestra seguridad o funcionamiento del vehículo real.
- El README y roadmap de Martín mantienen su flujo de simulación y aprendizaje;
  no se han encontrado paquetes propios de ROS en la revisión compartida
  `a370189d`. La configuración local del companion es trabajo adicional, no
  evidencia de un cambio de estado del trabajo independiente de Martín.
