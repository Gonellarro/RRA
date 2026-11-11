from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    wheelbase = LaunchConfiguration("wheelbase_m")
    front_track = LaunchConfiguration("front_track_m")
    rear_track = LaunchConfiguration("rear_track_m")
    model_file = PathJoinSubstitution([
        FindPackageShare("rra_ax10_model"), "urdf", "ax10.urdf.xacro"])
    robot_description = Command([
        "xacro ", model_file,
        " wheelbase:=", wheelbase,
        " front_track:=", front_track,
        " rear_track:=", rear_track,
    ])
    return LaunchDescription([
        DeclareLaunchArgument("wheelbase_m", default_value="0.320"),
        DeclareLaunchArgument("front_track_m", default_value="0.203"),
        DeclareLaunchArgument("rear_track_m", default_value="0.203"),
        Node(package="robot_state_publisher", executable="robot_state_publisher",
             name="robot_state_publisher",
             parameters=[{"robot_description": robot_description}]),
        Node(package="rra_ax10_model", executable="ax10_kinematics",
             name="ax10_kinematics",
             parameters=[PathJoinSubstitution([
                 FindPackageShare("rra_ax10_model"), "config", "kinematics.yaml"]), {
                     "wheelbase_m": ParameterValue(wheelbase, value_type=float),
                     "front_track_m": ParameterValue(front_track, value_type=float),
                     "rear_track_m": ParameterValue(rear_track, value_type=float),
                 }]),
    ])
