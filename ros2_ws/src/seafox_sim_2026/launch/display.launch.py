from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command
from launch_ros.parameter_descriptions import ParameterValue
from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description():

    depth_pub = ExecuteProcess(
        cmd=[
            'ros2', 'topic', 'pub', '/depth',
            'std_msgs/msg/Float32',
            '{data: 0.5}'
        ],
        output='screen'
    )

    return LaunchDescription([
        depth_pub
    ])
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_path = get_package_share_directory('seafox_sim_2026')

    urdf_file = os.path.join(pkg_path, 'urdf', 'rov.urdf')

    rviz_config = os.path.join(pkg_path, 'rviz', 'seafox.rviz')

    robot_description = ParameterValue(
        Command(['cat ', urdf_file]),
        value_type=str
    )

    return LaunchDescription([

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': robot_description
            }]
        ),

        Node(
            package='seafox_sim_2026',
            executable='depth_tf_node'
        ),

        Node(
            package='seafox_sim_2026',
            executable='force_visualizer_node'
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
            output='screen'
        ),
        ExecuteProcess(
        cmd=[
        'ros2', 'topic', 'pub',
        '--once',
        '/depth',
        'std_msgs/msg/Float32',
        '{data: 0.0}'
    ]
)

    ])