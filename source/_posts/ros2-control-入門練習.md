---
title: ros2_control-入門練習
date: 2026-10-01 21:29:22
tags: [ros2_control]
categories: simulation 筆記
---

練習 ros2_control mock 元件來控制虛擬的三輪小車。

<!-- more -->

### 環境

- 作業系統 Ubuntu 24.04
- ROS2 Kilted

  `sudo apt install ros-kilted-ros2-control ros-kilted-ros2-controllers`

### 練習

- 建立專案

  ```
  diffcar_ws/src$ ros2 pkg create --build-type ament_cmake control_tutorial
  ```

  現在專案工作目錄長相如下：
  
  ```
  diffcar_ws
  ├── build
  ├── install
  ├── log
  └── src
      └── control_tutorial
          ├── CMakeLists.txt
          ├── include
          ├── package.xml
          └── src
  ```

- 新增資料夾、編輯檔案

  ```
  diffcar_ws
  ├── build
  ├── install
  ├── log
  └── src
      └── control_tutorial
          ├── CMakeLists.txt
          ├── config                << 新增資料夾
          │   ├── controllers.yaml  << 編輯檔案
          │   └── display.rviz      << 編輯檔案
          ├── include
          ├── launch                << 新增資料夾
          │   └── launch.py         << 編輯檔案
          ├── package.xml           << 編輯檔案
          ├── src
          └── urdf                  << 新增資料夾
              └── car.xacro         << 編輯檔案
  ```

- 製作 Xacro

  - `urdf/car.xacro` 的內容

    根據 [Gazebo 官方文件 - 從零建立 SDF 檔](https://github.com/gazebosim/docs/blob/master/jetty/tutorials/building_robot/building_robot.sdf) ，請 AI 生成的 Xacro 檔案。

    ```
      <?xml version="1.0"?>
      
      <robot xmlns:xacro="http://ros.org/wiki/xacro" name="vehicle_blue">
        <!-- Properties -->
        <xacro:property name="blue" value="0 0 1 1" />
        <xacro:property name="red" value="1 0 0 1" />
        <xacro:property name="green" value="0 1 0 1" />
        <xacro:property name="wheel_radius" value="0.4" />
        <xacro:property name="wheel_length" value="0.2" />
        <!-- Materials -->
        <material name="blue">
          <color rgba="${blue}" />
        </material>
        <material name="red">
          <color rgba="${red}" />
        </material>
        <material name="green">
          <color rgba="${green}" />
        </material>
        <!-- Links -->
        <link name="caster">
          <inertial>
            <mass value="1" />
            <inertia ixx="0.016" ixy="0" ixz="0" iyy="0.016" iyz="0" izz="0.016" />
          </inertial>
          <visual>
            <origin xyz="0 0 0" rpy="0 0 0" />
            <geometry>
              <sphere radius="0.2" />
            </geometry>
            <material name="green" />
          </visual>
          <collision>
            <origin xyz="0 0 0" rpy="0 0 0" />
            <geometry>
              <sphere radius="0.2" />
            </geometry>
          </collision>
        </link>
        <link name="chassis">
          <inertial>
            <mass value="1.14395" />
            <inertia ixx="0.119161" ixy="0" ixz="0" iyy="0.405149" iyz="0" izz="0.476646" />
          </inertial>
          <visual>
            <geometry>
              <box size="2 1 0.5" />
            </geometry>
            <material name="blue" />
          </visual>
          <collision>
            <geometry>
              <box size="2 1 0.5" />
            </geometry>
          </collision>
        </link>
        <link name="left_wheel">
          <inertial>
            <mass value="1" />
            <inertia ixx="0.043333" ixy="0" ixz="0" iyy="0.043333" iyz="0" izz="0.08" />
          </inertial>
          <visual>
            <origin xyz="0 0 0" rpy="0 0 0" />
            <geometry>
              <cylinder radius="${wheel_radius}" length="${wheel_length}" />
            </geometry>
            <material name="red" />
          </visual>
          <collision>
            <origin xyz="0 0 0" rpy="0 0 0" />
            <geometry>
              <cylinder radius="${wheel_radius}" length="${wheel_length}" />
            </geometry>
          </collision>
        </link>
        <link name="right_wheel">
          <inertial>
            <mass value="1" />
            <inertia ixx="0.043333" ixy="0" ixz="0" iyy="0.043333" iyz="0" izz="0.08" />
          </inertial>
          <visual>
            <origin xyz="0 0 0" rpy="0 0 0" />
            <geometry>
              <cylinder radius="${wheel_radius}" length="${wheel_length}" />
            </geometry>
            <material name="red" />
          </visual>
          <collision>
            <origin xyz="0 0 0" rpy="0 0 0" />
            <geometry>
              <cylinder radius="${wheel_radius}" length="${wheel_length}" />
            </geometry>
          </collision>
        </link>
        <link name="base_link"></link>
        <!-- Joints -->
        <joint name="caster_wheel" type="fixed">
          <origin xyz="0.8 0 -0.2" rpy="0 0 0" />
          <parent link="chassis" />
          <child link="caster" />
        </joint>
        <joint name="left_wheel_joint" type="continuous">
          <origin xyz="-0.5 0.6 0" rpy="-1.5707 0 0" />
          <parent link="chassis" />
          <child link="left_wheel" />
          <axis xyz="0 0 1" />
          <limit effort="10" velocity="10" />
        </joint>
        <joint name="right_wheel_joint" type="continuous">
          <origin xyz="-0.5 -0.6 0" rpy="-1.5707 0 0" />
          <parent link="chassis" />
          <child link="right_wheel" />
          <axis xyz="0 0 1" />
          <limit effort="10" velocity="10" />
        </joint>
        <joint name="base_link_to_chassis" type="fixed">
          <origin xyz="0.5 0 0.4" rpy="0 0 0" />
          <parent link="base_link" />
          <child link="chassis" />
        </joint>
        <!-- ROS 2 Control -->
        <ros2_control name="MockSimSystem" type="system">
          <hardware>
            <plugin>mock_components/GenericSystem</plugin>
            <param name="calculate_dynamics">true</param>
          </hardware>
          <joint name="left_wheel_joint">
            <command_interface name="velocity" />
            <state_interface name="position" />
            <state_interface name="velocity" />
            <param name="min">-10</param>
            <param name="max">10</param>
          </joint>
          <joint name="right_wheel_joint">
            <command_interface name="velocity" />
            <state_interface name="position" />
            <state_interface name="velocity" />
            <param name="min">-10</param>
            <param name="max">10</param>
          </joint>
        </ros2_control>
      </robot>
    ```

    - 本來的 SDF 宣告 `<joint name='caster_wheel' type='ball'>`，因為 URDF 不支援 ball 型態，我先用 `<joint name="caster_wheel" type="fixed">` 代替，等之後練習 ros2_control 控制 gazebo 再來想辦法 
    - name="MockSimSystem" 給這個硬體元件一個我們可讀的識別名稱，方便在 log 訊息辨識，這個名稱不會被controller 的 YAML 或 launch.py 檔引用
    - `mock_components/GenericSystem` 只負責測試 controller 是否正確送出 command，需要 `<param name="calculate_dynamics">true</param>` 計算動力學積分，讓 `robot_state_publisher` 的 `/joint_states` topic 可以看到位置的變化數據
    - `base_link` 是機器人基座投影到地表的點，會隨著輪子轉動而移動，所以不是世界座標

- 建立 config/controllers.yaml

    ```
      controller_manager:
        ros__parameters:
          update_rate: 50 # Hz
      
          joint_state_broadcaster:
            type: joint_state_broadcaster/JointStateBroadcaster
      
          my_robot_controller:
            type: diff_drive_controller/DiffDriveController
      
      
      my_robot_controller:
        ros__parameters:
          left_wheel_names: ['left_wheel_joint']
          right_wheel_names: ['right_wheel_joint']
      
          wheel_separation: 1.2
          wheel_radius: 0.4
      
          publish_rate: 50.0
          base_frame_id: base_link
          enable_odom_tf: true
      
          cmd_vel_timeout: 0.5
      
          linear.x.has_velocity_limits: true
          linear.x.max_velocity: 0.7
          linear.x.min_velocity: -0.7
      
          angular.z.has_velocity_limits: true
          angular.z.max_velocity: 4.0
          angular.z.min_velocity: -4.0
    ```

    - 設定 `type: joint_state_broadcaster/JointStateBroadcaster` 以及 `type: diff_drive_controller/DiffDriveController` 是因為我們要控制差動驅動的三輪小車
      - `joint_state_broadcaster` 會發布 topic `/joint_states`，負責接上 `car.xacro` 宣告的 ros2_control joint 們
      - `diff_drive_controller` 根據輪速算 odometry 並發布 TF
    - `controller_manager.ros__parameters ` 區塊內的 `my_robot_controller` 名稱是自訂的
      - `launch.py` 的 spawner 用這個名字去呼叫 /controller_manager 的 service
    - 第二個 `my_robot_controller` 區塊下的 `ros__parameters` 是要按照 `diff_drive_controller` 文件來填寫
      - 注意到 joint 名稱(`left_wheel_joint`) 和在 `car.xacro` 宣告的一樣
      - 這裡是簡化的範例，很多參數省略不做設定
    - `wheel_separation: 1.2` 和 `wheel_radius: 0.4` 要符合 `car.xacro` 輪子的間距和尺寸
    - `base_frame_id: base_link` 是讓 `diff_drive_controller` 將計算出來的里程串接到 base_frame_id 指定的那個 frame 上，亦即額外發佈一條 odom -> base_link 的 TF
    - `cmd_vel_timeout: 0.5` 在 timeout 之後，車子自動煞車，速度降為 0


- 建立 `config/display.rviz`

  複製 [ROS2 官方範例的 RViz 設定檔](https://github.com/ros/urdf_tutorial/blob/ros2/rviz/urdf.rviz)

  注意：

  - Fixed Frame: odom
    - 配合 `diff_drive_controller` 自動建立的 TF，此時的 TF 根節點已經是 odom

  - Description Topic:

    Value: /robot_description
    
    - 指示 RViz 去訂閱名為 `/robot_description` 的 ROS2 Topic，以取得機器人的 URDF
    - `robot_state_publisher` 這個節點預設的話題就是 `/robot_description`

- 撰寫 `launch/launch.py` 檔案

  ```
    import os
    from launch import LaunchDescription
    from launch.actions import DeclareLaunchArgument
    from launch_ros.actions import Node
    from launch_ros.parameter_descriptions import ParameterValue
    from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
    from ament_index_python.packages import get_package_share_directory
    
    
    def generate_launch_description():
        pkg_description = get_package_share_directory("control_tutorial")
        xacro_file = os.path.join(pkg_description, "urdf", "car.xacro")
    
        robot_description = ParameterValue(Command(["xacro ", xacro_file]), value_type=str)
    
        robot_state_publisher = Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[{"robot_description": robot_description}],
        )
    
        controller_manager = Node(
            package="controller_manager",
            executable="ros2_control_node",
            parameters=[
                {"robot_description": robot_description},
                os.path.join(
                    pkg_description,
                    "config",
                    "controllers.yaml",
                ),
            ],
            output="screen",
        )
    
        joint_state_broadcaster_spawner = Node(
            package="controller_manager",
            executable="spawner",
            arguments=[
                "joint_state_broadcaster",
                "--controller-manager",
                "/controller_manager",
            ],
        )
    
        wheel_controller_spawner = Node(
            package="controller_manager",
            executable="spawner",
            arguments=[
                "my_robot_controller",
                "--controller-manager",
                "/controller_manager",
            ],
        )
    
        rviz_config = os.path.join(pkg_description, "config", "display.rviz")
        rviz_node = Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", rviz_config],
            name="rviz2",
            output="screen",
        )
    
        return LaunchDescription(
            [
                robot_state_publisher,
                controller_manager,
                joint_state_broadcaster_spawner,
                wheel_controller_spawner,
                rviz_node,
            ]
        )
  ```

  - 呼叫 controller_manager 的 service，把 `controllers.yaml` 宣告的控制器載入（load）並啟用（activate），後續發布 topic 才有反應
    - `joint_state_broadcaster_spawner` 對應 `joint_state_broadcaster`
    - `wheel_controller_spawner` 對應 `diff_drive_controller`

- 編輯 package.xml 檔案

  加上以下設定
    
    ```
      <exec_depend>xacro</exec_depend>
      <exec_depend>ros2launch</exec_depend>
      <exec_depend>ros2_control</exec_depend>
      <exec_depend>ros2_controllers</exec_depend>
      <exec_depend>controller_manager</exec_depend>
      <exec_depend>robot_state_publisher</exec_depend>
    ```
    
- 編輯 CMakeLists.txt 檔案
    
  ```
    install(
      DIRECTORY config launch urdf
      DESTINATION share/${PROJECT_NAME}
    )
  ```

### 編譯、執行

- 回到根目錄，執行

  ```
    diffcar_ws$ colcon build --packages-select control_tutorial
    diffcar_ws$ . install/setup.sh
    diffcar_ws$ ros2 launch control_tutorial launch.py
  ```

  會看到 Rviz 視窗，已設定好
  
  - RobotModel
  - TF，看到輪子上的座標軸
  
  ![顯示 odom](add_odom.png "add the odom")
  
  手動設定 Odometry Display 的 Topic 選 `/my_robot_controller/odom`

- 用 `ros2 topic pub` 控制 mock 小車

  ```
    $ ros2 topic pub /my_robot_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  "{twist: {linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.1}}}" --rate 10
  ```

  RViz 看到左右輪子的座標軸持續旋轉，以及紅色箭頭形成的軌跡。

  ![軌跡](odometry.png "control the car to move")

  - rate 10 是配合 `cmd_vel_timeout: 0.5`，要在 timeout 之前持續發布信息

- 檢查 topic 數值

  ```
    $ ros2 topic echo /joint_states
  ```

- 在終端機按下 ctrl + C，便可以關閉 RViz 和小視窗。
