# Modelo ROS 2 preliminar del AX10

Paquete portable `rra_ax10_model`: marco URDF/Xacro del chasis y sensores, más
una cinemática plana basada en `ackermann_msgs/AckermannDriveStamped`.

## Datos y supuestos

- Origen `base_link`: centro del eje trasero; X hacia delante, Y izquierda ROS,
  Z arriba.
- Batalla 0,320 m; vías delantera/trasera 0,203 m; radio de rodadura 0,056 m.
- La ficha del usuario usa Y positiva a la derecha. GNSS e IMU se convierten a
  Y ROS = -0,058 m; HC-SR04 está centrado (Y=0).
- `steering_geometry=parallel` usa la diferencia Ackermann medida de 0°:
  ambas ruedas delanteras reciben el mismo ángulo. `ackermann` ofrece una
  geometría ideal configurable, pero no es la geometría observada actualmente.
- Límite de dirección 25° según la ficha; no está calibrado como ángulo medido
  desde el centro de las ruedas ni derivado de PWM real.
- El Xacro solo representa marcos y ejes; no se inventan dimensiones de
  carrocería, neumáticos ni altura de los ejes respecto de `base_link`.
- Los RPY de GNSS, IMU y sonar están a cero por falta de medidas de orientación;
  deben considerarse provisionales.

## Uso ROS 2

Tras compilar el workspace con ROS 2 y sus dependencias:

```bash
ros2 launch rra_ax10_model model.launch.py
```

El nodo de cinemática recibe `ackermann_msgs/msg/AckermannDriveStamped` en
`/rra/model/cmd_ackermann` y publica:

- `/rra/model/predicted_odom` (`nav_msgs/msg/Odometry`): odometría **predicha a
  partir de la consigna**, no medida ni fusionada con MAVROS/encoders.
- `/rra/model/joint_states` (`sensor_msgs/msg/JointState`): dirección paralela,
  giro ideal Ackermann si se configura, y velocidades de ruedas predichas.
- `/tf` está desactivado por defecto para que la odometría modelada no compita
  con la autoridad de TF del autopiloto. `publish_tf` se puede activar en
  entornos de simulación aislados.

El nodo no publica comandos, no se conecta a MAVROS y no acciona el rover. La
integración con odometría real requiere una fuente real de velocidad/rueda y un
acuerdo de frames con Martín.

## Pruebas locales sin ROS

La biblioteca matemática es Python puro y sus pruebas se ejecutan con:

```bash
python -m unittest discover -s test -v
```

Este portátil no tiene ROS 2 instalado; colcon, xacro y el lanzamiento ROS
quedan pendientes de validarse en un entorno ROS 2 compatible.
