"""Read-only live monitor for MAVROS battery telemetry; never shuts down."""
import time
from .logic import Config, Protection, State


def main():
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import BatteryState

    class BatteryMonitor(Node):
        def __init__(self):
            super().__init__("rra_battery_protection_dry_run")
            self.declare_parameter("battery_topic", "/mavros_node/battery")
            self.declare_parameter("dry_run", True)
            if not self.get_parameter("dry_run").value:
                raise RuntimeError("This monitor is read-only; dry_run=false is not supported")
            self.logic = Protection(Config(emergency_enabled=False))
            self.first_sample = True
            self.create_subscription(BatteryState, self.get_parameter("battery_topic").value,
                                     self.on_battery, qos_profile_sensor_data)
            self.get_logger().warning("DRY_RUN activo: telemetría de batería de solo lectura; sin órdenes de apagado")

        def on_battery(self, msg):
            now = time.monotonic()
            voltage = float(msg.voltage)
            healthy = bool(msg.present) and voltage > 0
            if self.first_sample:
                self.first_sample = False
                self.get_logger().info(f"DRY_RUN batería recibida: {voltage:.3f} V, present={msg.present}")
            events = self.logic.update(now, voltage, healthy)
            for event in events:
                if event == "warning":
                    self.get_logger().warning(f"SIMULADO: BAT ELECTRONICA BAJA - {voltage:.3f} V")
                elif event == "shutdown":
                    self.get_logger().error(f"SIMULADO: pedir apagado companion; V={voltage:.3f} V")
                elif event in ("power_cutoff", "emergency_cutoff"):
                    self.get_logger().error(f"SIMULADO: corte candidato; V={voltage:.3f} V; GPIO sin accionar")
                elif event == "sensor_fault":
                    self.get_logger().error("Fallo persistente de lectura batería MAVROS")

    rclpy.init()
    node = BatteryMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
