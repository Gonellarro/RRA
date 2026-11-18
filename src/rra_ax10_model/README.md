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
- La transformación móvil `odom_model → base_link` está desactivada por
  defecto para que la odometría modelada no compita con otras fuentes. El
  `robot_state_publisher` sí publica las transformaciones internas del modelo;
  ejecútalo en un dominio aislado hasta acordar los frames con Martín.

El nodo no publica comandos, no se conecta a MAVROS y no acciona el rover. La
integración con odometría real requiere una fuente real de velocidad/rueda y un
acuerdo de frames con Martín.

## Pruebas locales sin ROS

La biblioteca matemática es Python puro y sus pruebas se ejecutan con:

```bash
python -m unittest discover -s test -v
```

## Validación en la Orange Pi — 18-11-2026

El paquete se compiló en ROS 2 Lyrical con `colcon` en el workspace aislado
`~/rra_ax10_test_ws`; las seis pruebas matemáticas pasaron. En el dominio ROS
206, el launch publicó odometría y articulaciones para consignas simuladas,
con transformaciones de dirección y giro de ruedas; al dejar de enviar consignas
la velocidad predicha volvió a cero. Con 0,2 m/s y 0,3 rad se observaron
0,1933 rad/s y un radio predicho de 1,034 m, como corresponde a la ecuación.
La prueba no está conectada al autopiloto y no mueve el vehículo. Las
dependencias instaladas fueron `ros-lyrical-ackermann-msgs` y
`ros-lyrical-xacro`.

Para repetirla, en dos terminales de la Pi, cargar ROS y el workspace aislado
y usar `ROS_DOMAIN_ID=206` y `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` en ambas.
En la primera: `ros2 launch rra_ax10_model model.launch.py`. En la segunda:
`python3 ~/rra_ax10_test_ws/src/rra_ax10_model/scripts/ros_smoke_check.py`.
La prueba solo publica consignas a los tópicos locales del modelo.

## Contraste preliminar con la ficha física

Con batalla 0,320 m y dirección virtual de 25°, el modelo bicicleta predice
un radio de 0,686 m desde el centro del eje trasero. La ficha reporta 0,920 m
en cada sentido: la predicción es aproximadamente un 25 % menor. En sentido
inverso, un radio de 0,920 m implica un ángulo virtual efectivo de unos 19,2°
en este modelo. No es una medición del ángulo de cada rueda. La ficha no indica
cómo se determinó el centro de la trayectoria ni incluye repeticiones, y el
deslizamiento también influye; se conserva el límite de 25° hasta contrastar
el radio y el tope en ambos sentidos. No se infiere un PWM a partir del radio.

Para refinarlo, conducir a velocidad baja y dirección fija por cada lado,
marcar la trayectoria del centro del eje trasero y medir el diámetro de su
círculo, repetir y anotar la superficie y el mando utilizado. El radio es la
mitad de ese diámetro; el diámetro exterior de la carrocería no es equivalente.
