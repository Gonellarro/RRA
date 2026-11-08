"""Publica diagnóstico de conexión; no dispone de acciones de control."""

import signal
import time

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from mavros_msgs.msg import State
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import BatteryState, Imu, NavSatFix
from std_msgs.msg import Float64

from rra_telemetry.sensors import sensor_status
from rra_telemetry.status import classify_state


class StateObserver(Node):
    def __init__(self):
        super().__init__('rra_state_observer')
        self.declare_parameter('state_topic', '/mavros/state')
        self.declare_parameter('diagnostics_topic', '/rra/telemetry/diagnostics')
        self.declare_parameter('stale_after_sec', 5.0)
        self.declare_parameter('gps_topic', '/mavros/global_position/global')
        self.declare_parameter('imu_topic', '/mavros/imu/data')
        self.declare_parameter('battery_topic', '/mavros/battery')
        self.declare_parameter('odometry_topic', '/mavros/global_position/local')
        self.declare_parameter('heading_topic', '/mavros/global_position/compass_hdg')
        state_topic = self.get_parameter('state_topic').value
        diagnostics_topic = self.get_parameter('diagnostics_topic').value
        self.stale_after = float(self.get_parameter('stale_after_sec').value)
        if self.stale_after <= 0:
            raise ValueError('stale_after_sec debe ser positivo')
        self.received_at = None
        self.state = None
        self.sensors = {kind: (None, None) for kind in ('gps', 'imu', 'battery', 'speed', 'heading')}
        self.publisher = self.create_publisher(DiagnosticArray, diagnostics_topic, 10)
        self.subscription = self.create_subscription(State, state_topic, self.on_state, 10)
        self.sensor_subscriptions = []
        for kind, msg_type, param in (('gps', NavSatFix, 'gps_topic'),
                                      ('imu', Imu, 'imu_topic'),
                                      ('battery', BatteryState, 'battery_topic'),
                                      ('speed', Odometry, 'odometry_topic'),
                                      ('heading', Float64, 'heading_topic')):
            self.sensor_subscriptions.append(self.create_subscription(
                msg_type, self.get_parameter(param).value,
                lambda msg, key=kind: self.on_sensor(key, msg), qos_profile_sensor_data))
        self.timer = self.create_timer(1.0, self.report)

    def on_state(self, message):
        self.state = message
        self.received_at = time.monotonic()

    def on_sensor(self, kind, message):
        self.sensors[kind] = (message, time.monotonic())

    def report(self):
        now = time.monotonic()
        connected = self.state.connected if self.state is not None else False
        level, message = classify_state(connected, self.received_at, now, self.stale_after)
        status = DiagnosticStatus()
        status.name = 'RRA: conexion MAVROS'
        status.hardware_id = 'mavros'
        # diagnostic_msgs/DiagnosticStatus.level es byte, representado como bytes
        # de longitud uno por los mensajes Python de ROS 2.
        status.level = bytes([level])
        status.message = message
        if self.state is not None and level != 2:
            mode = self.state.mode.encode('ascii', errors='replace').decode('ascii')
            age_ms = max(0, int((now - self.received_at) * 1000))
            status.values = [KeyValue(key='modo', value=mode),
                             KeyValue(key='armado', value=str(self.state.armed)),
                             KeyValue(key='conectado', value=str(self.state.connected)),
                             KeyValue(key='edad_recepcion_ms', value=str(age_ms)),
                             KeyValue(key='edad_muestra_verificada', value='no')]
        result = DiagnosticArray()
        result.header.stamp = self.get_clock().now().to_msg()
        result.status = [status]
        companion = DiagnosticStatus()
        companion.name = 'RRA: Companion telemetry'
        companion.hardware_id = 'rra_companion'
        companion.level = b'\x00'
        companion.message = 'Observador activo'
        companion.values = [KeyValue(key='publicacion_hz', value='1')]
        result.status.append(companion)
        for kind in ('gps', 'imu', 'battery', 'speed', 'heading'):
            msg, received = self.sensors[kind]
            age = None if received is None else now - received
            level, description, values = sensor_status(kind, msg, age, self.stale_after)
            item = DiagnosticStatus()
            item.name = 'RRA: ' + kind
            item.hardware_id = 'mavros'
            item.level = bytes([level])
            item.message = description
            item.values = [KeyValue(key=k, value=v) for k, v in values.items()]
            result.status.append(item)
        self.publisher.publish(result)


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = None
    stopped = False

    def request_stop(_signum, _frame):
        nonlocal stopped
        stopped = True

    previous_int = signal.signal(signal.SIGINT, request_stop)
    previous_term = signal.signal(signal.SIGTERM, request_stop)
    try:
        node = StateObserver()
        while not stopped and rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.2)
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        signal.signal(signal.SIGINT, previous_int)
        signal.signal(signal.SIGTERM, previous_term)
