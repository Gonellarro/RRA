"""ROS-only handshake smoke test; it never calls poweroff or GPIO."""
from __future__ import annotations

import sys

from .mavlink_codec import (
    CMD_COMPANION_PREPARED,
    CMD_SHUTDOWN_REQUEST,
    COMMAND_ACK_ID,
    FRAMING_OK,
    MAV_RESULT_ACCEPTED,
    decode_command_long,
    make_command_ack,
    make_command_long,
    payload_from_ros,
)


def main():
    import rclpy
    from mavros_msgs.msg import Mavlink
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy

    nonce = 12_345

    class ProtocolSmoke(Node):
        def __init__(self):
            super().__init__("rra_battery_protection_protocol_smoke")
            self.declare_parameter("source_topic", "/uas1/mavlink_source")
            self.declare_parameter("sink_topic", "/uas1/mavlink_sink")
            qos = QoSProfile(depth=100, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.pub = self.create_publisher(Mavlink, self.get_parameter("source_topic").value, qos)
            self.sub = self.create_subscription(
                Mavlink, self.get_parameter("sink_topic").value, self.on_frame, qos)
            self.fcu_sub = self.create_subscription(
                Mavlink, self.get_parameter("sink_topic").value, self.on_fcu_frame, qos)
            self.fcu_pub = self.create_publisher(
                Mavlink, self.get_parameter("source_topic").value, qos)
            self.sent = False
            self.received_ack = False
            self.received_ready = False
            self.seq = 0
            self.started = self.get_clock().now()
            self.timer = self.create_timer(0.1, self.tick)

        def tick(self):
            if not self.sent and self.pub.get_subscription_count() > 0:
                request = make_command_long(
                    self, seq=self.seq, command=CMD_SHUTDOWN_REQUEST,
                    target_system=1, target_component=191,
                    params=(float(nonce), 7.25, 7.24, 1.0, 0.0, 0.0, 0.0),
                    source_system=1, source_component=1)
                self.pub.publish(request)
                self.sent = True
                self.get_logger().info("request published to local raw topic (synthetic FCU)")
            if self.received_ack and self.received_ready:
                self.get_logger().info("PASS: receipt ACK and nonce-matched PREPARED observed")
                rclpy.shutdown()
                return
            elapsed = (self.get_clock().now() - self.started).nanoseconds / 1e9
            if elapsed > 8.0:
                self.get_logger().error(
                    f"FAIL: ack={self.received_ack}, prepared={self.received_ready}")
                rclpy.shutdown()

        def on_frame(self, msg):
            if int(msg.framing_status) != FRAMING_OK or int(msg.sysid) != 1 or int(msg.compid) != 191:
                return
            if int(msg.msgid) == COMMAND_ACK_ID:
                payload = payload_from_ros(msg)
                if len(payload) >= 3:
                    command = int.from_bytes(payload[:2], "little")
                    result = payload[2]
                    if command == CMD_SHUTDOWN_REQUEST and result == MAV_RESULT_ACCEPTED:
                        self.received_ack = True
            cmd = decode_command_long(msg)
            if (cmd is not None and cmd.command == CMD_COMPANION_PREPARED
                    and cmd.target_system == 1 and cmd.target_component == 1
                    and round(cmd.params[0]) == nonce):
                self.received_ready = True

        def on_fcu_frame(self, msg):
            # Simulate the Matek's ACK to PREPARED_TO_POWER_OFF. This is an
            # isolated ROS topic loopback; it does not reach the flight controller.
            cmd = decode_command_long(msg)
            if (cmd is None or cmd.sysid != 1 or cmd.compid != 191
                    or cmd.command != CMD_COMPANION_PREPARED
                    or cmd.target_system != 1 or cmd.target_component != 1):
                return
            ack = make_command_ack(
                self, seq=self.seq, command=CMD_COMPANION_PREPARED,
                result=MAV_RESULT_ACCEPTED, target_system=1, target_component=191,
                source_system=1, source_component=1)
            self.seq = (self.seq + 1) & 0xFF
            self.fcu_pub.publish(ack)

    rclpy.init()
    node = ProtocolSmoke()
    try:
        rclpy.spin(node)
    except Exception:
        if rclpy.ok():
            raise
    finally:
        passed = node.received_ack and node.received_ready
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
