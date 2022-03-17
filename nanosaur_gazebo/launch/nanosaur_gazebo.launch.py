# Copyright (C) 2022, Raffaello Bonghi <raffaello@rnext.it>
# All rights reserved
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import xacro

from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch import LaunchDescription
from launch.conditions import IfCondition


def generate_launch_description():
    package_gazebo = get_package_share_directory('nanosaur_gazebo')
    gazebo_ros_path = get_package_share_directory('gazebo_ros')

    world_file_name = LaunchConfiguration('world_file_name')
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    gazebo_gui_cmd = DeclareLaunchArgument('gui', default_value='true',
                                           description='Set to "false" to run headless.')

    gazebo_server_cmd = DeclareLaunchArgument('server', default_value='true',
                                              description='Set to "false" not to run gzserver.')

    world_file_name_cmd = DeclareLaunchArgument('world_file_name', default_value='empty_world.world',
                                                description='Load gazebo world.')

    # full  path to urdf and world file
    # world = os.path.join(package_gazebo, "worlds", world_file_name)
    xacro_path = os.path.join(package_gazebo, "urdf", "nanosaur.urdf.xacro")

    # process urdf contents because to spawn an entity in
    # gazebo we need to provide entire urdf as string on  command line
    robot_desc = xacro.process_file(xacro_path)
    xml = robot_desc.toxml()

    # Launch Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'use_sim_time': use_sim_time, 'robot_description': xml}]
    )

    # Spawn robot
    spawn_robot = Node(
        package='gazebo_ros',
        node_executable='spawn_entity.py',
        node_name='spawn_entity',
        output='screen',
        arguments=['-entity', 'nanosaur',
                   '-topic', '/robot_description',
                   '-x', '0', '-y', '0', '-z', '0'
                   ]
    )

    # start gazebo, notice we are using libgazebo_ros_factory.so instead of libgazebo_ros_init.so
    # That is because only libgazebo_ros_factory.so contains the service call to /spawn_entity
    # Reference options
    # https://github.com/ros-simulation/gazebo_ros_pkgs/blob/foxy/gazebo_ros/launch/gzserver.launch.py
    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [os.path.join(gazebo_ros_path, 'launch'), '/gzserver.launch.py']),
        launch_arguments={'world': [package_gazebo, "/worlds/", world_file_name],
                          'verbose': 'true',
                          'init': 'false'}.items(),
        condition=IfCondition(LaunchConfiguration('server'))
    )

    gazebo_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [os.path.join(gazebo_ros_path, 'launch'), '/gzclient.launch.py']),
        condition=IfCondition(LaunchConfiguration('gui'))
    )

    ld = LaunchDescription()
    ld.add_action(gazebo_gui_cmd)
    ld.add_action(gazebo_server_cmd)
    ld.add_action(world_file_name_cmd)
    ld.add_action(gazebo_server)
    ld.add_action(gazebo_gui)
    ld.add_action(robot_state_publisher_node)
    ld.add_action(spawn_robot)

    return ld
# EOF
