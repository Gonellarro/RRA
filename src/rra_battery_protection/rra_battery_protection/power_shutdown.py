"""MAVROS raw-message receiver for the RRA orderly Pi shutdown protocol.

DRY_RUN is enabled unless explicitly disabled by the service environment.
This node never opens the FCU UART; it uses the existing MAVROS UAS topics.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from .mavlink_codec import (
    CMD_COMPANION_PREPARED,
    CMD_SHUTDOWN_REQUEST,
    COMMAND_ACK_ID,
    FRAMING_OK,
    MAV_RESULT_ACCEPTED,
    MAV_RESULT_DENIED,
    decode_command_long,
    has_expected_endpoints,
    make_command_ack,
    make_command_long,
    shutdown_values_valid,
)


def main():
    import rclpy
    from mavros_msgs.msg import Mavlink
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy

    class RraPowerShutdown(Node):
        def __init__(self):
            super().__init__("rra_power_shutdown")
            self.declare_parameter("mavlink_source_topic", "/uas1/mavlink_source")
            self.declare_parameter("mavlink_sink_topic", "/uas1/mavlink_sink")
            self.declare_parameter("fcu_system_id", 1)
            self.declare_parameter("fcu_component_id", 1)
            self.declare_parameter("companion_system_id", 1)
            self.declare_parameter("companion_component_id", 191)
            self.declare_parameter(
                "event_log", str(Path.home() / ".local/state/rra/battery-protection.jsonl"))
            self.declare_parameter("prepare_ack_timeout_s", 3.0)
            self.declare_parameter("poweroff_after_prepare_s", 2.0)

            self.dry_run = os.environ.get("RRA_POWER_SHUTDOWN_DRY_RUN", "1") != "0"
            self.event_log = Path(str(self.get_parameter("event_log").value))
            # MAVROS raw source/sink use BEST_EFFORT. A RELIABLE reader is
            # incompatible with that publisher and silently gets no frames.
            qos = QoSProfile(depth=100, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.publisher = self.create_publisher(
                Mavlink, str(self.get_parameter("mavlink_sink_topic").value), qos)
            self.subscription = self.create_subscription(
                Mavlink, str(self.get_parameter("mavlink_source_topic").value),
                self.on_frame, qos)
            self.seq = 0
            self.pending_nonce = None
            self.request_received_at = None
            self.last_prepare_sent_at = 0.0
            self.prepare_acknowledged = False
            self.poweroff_due = None
            self.completed_nonces = deque(maxlen=32)
            self.raw_rx_frames = 0
            self.raw_rx_reported = False
            self.timer = self.create_timer(0.1, self.on_tick)
            mode = "DRY_RUN: no se apagará Linux" if self.dry_run else "MODO REAL: apagado ordenado habilitado"
            self.get_logger().warning(
                f"{mode}; source={self.get_parameter('mavlink_source_topic').value}; "
                f"sink={self.get_parameter('mavlink_sink_topic').value}")

        def next_seq(self):
            self.seq = (self.seq + 1) & 0xFF
            return self.seq

        def publish_ack(self, command, result, target_system, target_component):
            self.publisher.publish(make_command_ack(
                self, seq=self.next_seq(), command=command, result=result,
                target_system=target_system, target_component=target_component))

        def publish_prepared(self, nonce):
            params = (float(nonce), 1.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            self.publisher.publish(make_command_long(
                self, seq=self.next_seq(), command=CMD_COMPANION_PREPARED,
                target_system=int(self.get_parameter("fcu_system_id").value),
                target_component=int(self.get_parameter("fcu_component_id").value),
                params=params))

        def persist_event(self, nonce, filtered_v, instant_v):
            record = {
                "event": "low_voltage_shutdown_requested",
                "utc": datetime.now(timezone.utc).isoformat(),
                "nonce": nonce,
                "filtered_voltage_v": filtered_v,
                "instant_voltage_v": instant_v,
                "dry_run": self.dry_run,
                "source": "MAVLink COMMAND_LONG 31000 via MAVROS raw topic",
            }
            self.event_log.parent.mkdir(parents=True, exist_ok=True)
            with self.event_log.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, separators=(",", ":")) + "\n")
                stream.flush()
                os.fsync(stream.fileno())

        def on_frame(self, msg):
            if int(msg.framing_status) == FRAMING_OK:
                self.raw_rx_frames += 1
                if not self.raw_rx_reported:
                    self.raw_rx_reported = True
                    self.get_logger().info(
                        f"MAVLink raw recibido desde MAVROS; primer msgid={int(msg.msgid)}, "
                        f"origen={int(msg.sysid)}.{int(msg.compid)}")
            cmd = decode_command_long(msg)
            if cmd is None or cmd.command != CMD_SHUTDOWN_REQUEST:
                if int(msg.framing_status) == FRAMING_OK and int(msg.msgid) == COMMAND_ACK_ID:
                    self.on_ack(msg)
                return

            fcu_sys = int(self.get_parameter("fcu_system_id").value)
            fcu_comp = int(self.get_parameter("fcu_component_id").value)
            own_sys = int(self.get_parameter("companion_system_id").value)
            own_comp = int(self.get_parameter("companion_component_id").value)
            if not has_expected_endpoints(
                    cmd, fcu_system=fcu_sys, fcu_component=fcu_comp,
                    companion_system=own_sys, companion_component=own_comp):
                return
            nonce_f, filtered_v, instant_v = cmd.params[:3]
            if not shutdown_values_valid(cmd):
                self.publish_ack(cmd.command, MAV_RESULT_DENIED, cmd.sysid, cmd.compid)
                self.get_logger().error("Orden rechazada: nonce/tensiones inválidos")
                return

            nonce = int(round(nonce_f))
            if nonce in self.completed_nonces:
                self.publish_ack(cmd.command, MAV_RESULT_ACCEPTED, cmd.sysid, cmd.compid)
                return
            if self.pending_nonce is not None and nonce != self.pending_nonce:
                self.publish_ack(cmd.command, MAV_RESULT_DENIED, cmd.sysid, cmd.compid)
                return
            if self.pending_nonce is None:
                try:
                    self.persist_event(nonce, filtered_v, instant_v)
                except OSError as exc:
                    self.publish_ack(cmd.command, MAV_RESULT_DENIED, cmd.sysid, cmd.compid)
                    self.get_logger().error(f"No se pudo persistir el evento; orden rechazada: {exc}")
                    return
                self.pending_nonce = nonce
                self.request_received_at = time.monotonic()
                self.prepare_acknowledged = False
                self.last_prepare_sent_at = 0.0
                self.get_logger().error(
                    f"Petición válida nonce={nonce}: filtrada={filtered_v:.3f} V "
                    f"instantánea={instant_v:.3f} V")
            # ACK only after durable logging. Repeated requests are idempotent.
            self.publish_ack(cmd.command, MAV_RESULT_ACCEPTED, cmd.sysid, cmd.compid)

        def on_ack(self, msg):
            # ACK of the second phase means the FCU Lua script received READY.
            if self.pending_nonce is None or self.prepare_acknowledged:
                return
            if (int(msg.sysid) != int(self.get_parameter("fcu_system_id").value)
                    or int(msg.compid) != int(self.get_parameter("fcu_component_id").value)):
                return
            data = b"".join(int(w).to_bytes(8, "little") for w in msg.payload64)[:int(msg.len)]
            if len(data) < 3:
                return
            command, result = int.from_bytes(data[:2], "little"), data[2]
            if command == CMD_COMPANION_PREPARED and result == MAV_RESULT_ACCEPTED:
                self.prepare_acknowledged = True
                self.poweroff_due = time.monotonic() + float(
                    self.get_parameter("poweroff_after_prepare_s").value)
                self.get_logger().info("Matek confirmó PREPARED_TO_POWER_OFF")

        def on_tick(self):
            if self.pending_nonce is None:
                return
            now = time.monotonic()
            if self.poweroff_due is not None:
                if now >= self.poweroff_due:
                    self.execute_poweroff()
                return
            if now - self.last_prepare_sent_at >= 1.0:
                # Idempotent READY command; repeat until FCU acknowledges or the
                # bounded fallback expires. This never actuates any GPIO.
                self.publish_prepared(self.pending_nonce)
                self.last_prepare_sent_at = now
            timeout = float(self.get_parameter("prepare_ack_timeout_s").value)
            # At this stage there is no Pololu to wait for. Give MAVROS a short
            # bounded window, then still shut the Pi down cleanly if FCU vanished.
            if self.request_received_at is not None and now - self.request_received_at >= timeout:
                if self.dry_run:
                    self.get_logger().warning("DRY_RUN: ejecutaría systemctl poweroff (sin ejecutar)")
                    self.completed_nonces.append(self.pending_nonce)
                    self.pending_nonce = None
                else:
                    self.get_logger().fatal("Sin ACK de preparación; apagado Linux por timeout de respaldo")
                    self.poweroff_due = now + 1.0

        def execute_poweroff(self):
            nonce = self.pending_nonce
            if self.dry_run:
                self.get_logger().warning(f"DRY_RUN: poweroff simulado nonce={nonce}")
                self.completed_nonces.append(nonce)
                self.pending_nonce = None
                self.poweroff_due = None
                return
            try:
                os.sync()
                subprocess.Popen(
                    ["/usr/bin/sudo", "-n", "/usr/bin/systemctl", "poweroff"],
                    close_fds=True)
                self.completed_nonces.append(nonce)
                self.pending_nonce = None
                self.poweroff_due = None
                self.get_logger().fatal(f"Solicitado apagado ordenado Linux nonce={nonce}")
            except Exception as exc:
                self.get_logger().fatal(f"Fallo al solicitar systemctl poweroff: {exc}")
                self.pending_nonce = None
                self.poweroff_due = None

    rclpy.init()
    node = RraPowerShutdown()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception:
        # rclpy may invalidate its wait set while handling SIGINT/SIGTERM.
        # Suppress only that shutdown path; propagate runtime faults normally.
        if rclpy.ok():
            raise
    finally:
        node.destroy_node()
        rclpy.shutdown()

