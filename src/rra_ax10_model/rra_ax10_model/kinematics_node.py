"""Odometría predicha desde consignas Ackermann; nunca emite órdenes al rover."""

import math

import rclpy
from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import Quaternion, TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster

from .kinematics import Ax10Geometry, integrate_pose, steering_angles


def yaw_quaternion(yaw: float) -> Quaternion:
    q = Quaternion()
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q


class Ax10KinematicsNode(Node):
    def __init__(self):
        super().__init__("ax10_kinematics")
        self.declare_parameter("wheelbase_m", 0.320)
        self.declare_parameter("front_track_m", 0.203)
        self.declare_parameter("rear_track_m", 0.203)
        self.declare_parameter("wheel_radius_m", 0.056)
        self.declare_parameter("max_steering_angle_deg", 25.0)
        self.declare_parameter("steering_geometry", "parallel")
        self.declare_parameter("input_topic", "/rra/model/cmd_ackermann")
        self.declare_parameter("odom_topic", "/rra/model/predicted_odom")
        self.declare_parameter("publish_tf", False)
        self.declare_parameter("command_timeout_s", 0.5)

        self.geometry = Ax10Geometry(
            wheelbase_m=float(self.get_parameter("wheelbase_m").value),
            front_track_m=float(self.get_parameter("front_track_m").value),
            rear_track_m=float(self.get_parameter("rear_track_m").value),
            wheel_radius_m=float(self.get_parameter("wheel_radius_m").value),
            max_steering_angle_rad=math.radians(
                float(self.get_parameter("max_steering_angle_deg").value)),
            steering_geometry=str(self.get_parameter("steering_geometry").value),
        )
        self.geometry.validate()
        self.input_topic = str(self.get_parameter("input_topic").value)
        self.odom_topic = str(self.get_parameter("odom_topic").value)
        self.publish_tf = bool(self.get_parameter("publish_tf").value)
        self.command_timeout_s = float(self.get_parameter("command_timeout_s").value)
        self.cmd = None
        self.last_command_time = None
        self.pose = (0.0, 0.0, 0.0)
        self.last_time = self.get_clock().now()

        self.odom_pub = self.create_publisher(Odometry, self.odom_topic, 10)
        self.joints_pub = self.create_publisher(JointState, "/rra/model/joint_states", 10)
        self.tf_broadcaster = TransformBroadcaster(self) if self.publish_tf else None
        self.create_subscription(AckermannDriveStamped, self.input_topic, self.on_command, 10)
        self.timer = self.create_timer(0.02, self.on_timer)
        self.get_logger().info(
            f"Modelo activo: geometry={self.geometry.steering_geometry}, "
            f"L={self.geometry.wheelbase_m:.3f} m; salida predicha, sin control físico")

    def on_command(self, msg: AckermannDriveStamped):
        self.cmd = msg.drive
        self.last_command_time = self.get_clock().now()

    def on_timer(self):
        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds * 1e-9
        self.last_time = now
        if self.cmd is None or dt <= 0.0 or dt > 0.2:
            return

        command_age = (now - self.last_command_time).nanoseconds * 1e-9
        speed = float(self.cmd.speed) if command_age <= self.command_timeout_s else 0.0
        steering = float(self.cmd.steering_angle)
        x, y, yaw = self.pose
        x, y, yaw, omega = integrate_pose(
            x, y, yaw, speed, steering, dt, self.geometry)
        self.pose = (x, y, yaw)
        left, right = steering_angles(steering, self.geometry)

        stamp = now.to_msg()
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = "odom_model"
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x = x
        odom.pose.pose.position.y = y
        odom.pose.pose.orientation = yaw_quaternion(yaw)
        odom.twist.twist.linear.x = speed
        odom.twist.twist.angular.z = omega
        self.odom_pub.publish(odom)

        joints = JointState()
        joints.header.stamp = stamp
        joints.name = ["front_left_steering_joint", "front_right_steering_joint",
                       "front_left_wheel_joint", "front_right_wheel_joint",
                       "rear_left_wheel_joint", "rear_right_wheel_joint"]
        wheel_rate = -speed / self.geometry.wheel_radius_m
        joints.position = [left, right, 0.0, 0.0, 0.0, 0.0]
        joints.velocity = [0.0, 0.0, wheel_rate, wheel_rate, wheel_rate, wheel_rate]
        self.joints_pub.publish(joints)

        if self.tf_broadcaster:
            transform = TransformStamped()
            transform.header.stamp = stamp
            transform.header.frame_id = "odom_model"
            transform.child_frame_id = "base_link"
            transform.transform.translation.x = x
            transform.transform.translation.y = y
            transform.transform.rotation = yaw_quaternion(yaw)
            self.tf_broadcaster.sendTransform(transform)


def main(args=None):
    rclpy.init(args=args)
    node = Ax10KinematicsNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
