---
title: ros2_control_gazebo
date: 2026-11-06 22:11:39
tags: [ros2_control, Gazebo]
categories: simulation 筆記
---

[ros2 control 筆記](https://annsonic.github.io/2026/10/01/ros2-control-%E5%85%A5%E9%96%80%E7%B7%B4%E7%BF%92/)，從 mock controller 延伸變成控制 gazebo 環境裡的小車，部份參考[官方範例](https://github.com/ros-controls/gz_ros2_control/blob/rolling/gz_ros2_control_demos/launch/diff_drive_example.launch.py)

<!-- more -->

### 環境

- 作業系統 Ubuntu 24.04
- ROS2 Kilted
- Gazebo Ionic

### 練習

- 建立專案，我命名為 control_gazebo

  ```
  diffcar_ws/src$ ros2 pkg create --build-type ament_cmake control_gazebo
  ```

  現在專案工作目錄長相如下：
  
  ```
  diffcar_ws
  ├── build
  ├── install
  ├── log
  └── src
      └── control_gazebo
          ├── CMakeLists.txt
          ├── include
          ├── src
          └── package.xml
  ```

- 新增資料夾、編輯檔案

  ```
  diffcar_ws
  ├── build
  ├── install
  ├── log
  └── src
      └── control_gazebo
          ├── CMakeLists.txt
          ├── config                << 新增資料夾
          │   ├── controllers.yaml  << 沿用檔案
          │   └── display.rviz      << 沿用檔案
          ├── include
          ├── launch                << 新增資料夾
          │   └── launch.py         << 編輯檔案
          ├── package.xml           << 編輯檔案
          ├── src
          └── urdf                  << 新增資料夾
          │   └── car.xacro         << 編輯檔案
          └── worlds                << 新增資料夾
              └── empty.sdf         << 新增檔案
  ```

- 編輯 `urdf/car.xacro`

  參考[官方範例](https://github.com/ros-controls/gz_ros2_control/blob/rolling/gz_ros2_control_demos/urdf/test_diff_drive.xacro.urdf)

  原先的

  ```
    <ros2_control name="MockSimSystem" type="system">
      <hardware>
        <plugin>mock_components/GenericSystem</plugin>
        <param name="calculate_dynamics">true</param>
      </hardware>
  ```

  改成

  ```
    <ros2_control name="GazeboSimSystem" type="system">
      <hardware>
        <plugin>gz_ros2_control/GazeboSimSystem</plugin>
      </hardware>
  ```

  還有在 `<ros2_control>` 區塊後面新增

  ```
    <gazebo>
      <plugin filename="gz_ros2_control-system" name="gz_ros2_control::GazeboSimROS2ControlPlugin">
        <parameters>$(find control_gazebo)/config/controllers.yaml</parameters>
      </plugin>
    </gazebo>
  ```

  - `<param name="calculate_dynamics">true</param>` 是 `mock_components/GenericSystem` 專屬的參數，`gz_ros2_control/GazeboSimSystem` 不認識它
  - `gz_ros2_control-system` 是 `gz_ros2_control` 套件提供的 Gazebo Sim 系統插件，它負責在 Xacro 模型中被 Gazebo 加載，用來連接 ros2_control 框架與底層 Gazebo 物理引擎
    - 之前 mock controller 不需要 plugin，所以是在 launch.py 啟動 controller_manager 和指定 controllers.yaml 檔案路徑
    - `gz_ros2_control-system` 啟動 controller_manager
    - find 是是 xacro 的語法，用來查 install 的 share 目錄，control_gazebo 是這個專案的名稱

- 建立 empty.sdf
  - 複製[官方](https://github.com/gazebosim/gz-sim/blob/main/examples/worlds/empty.sdf) 檔案

- 沿用 config/controllers.yaml、config/display.rviz

  跟[ros2 control 筆記](https://annsonic.github.io/2026/10/01/ros2-control-%E5%85%A5%E9%96%80%E7%B7%B4%E7%BF%92/) 一樣的檔案內容。

  - controllers.yaml 跟 ros2_controller hardware plugin 無關，這正是 ros2_control 分層設計的好處

- 撰寫 `launch/launch.py` 檔案

  ```
  import os
  from launch import LaunchDescription
  from launch.actions import IncludeLaunchDescription, RegisterEventHandler
  from launch.event_handlers import OnProcessExit
  from launch.launch_description_sources import PythonLaunchDescriptionSource
  from launch.substitutions import Command
  from launch_ros.actions import Node
  from launch_ros.parameter_descriptions import ParameterValue
  from ament_index_python.packages import get_package_share_directory


  def generate_launch_description():
      pkg_description = get_package_share_directory("control_gazebo")
      pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")

      xacro_file = os.path.join(pkg_description, "urdf", "car.xacro")
      world_path = os.path.join(pkg_description, "worlds", "empty.sdf")
      rviz_config = os.path.join(pkg_description, "config", "display.rviz")

      robot_description = ParameterValue(Command(["xacro ", xacro_file]), value_type=str)
      use_sim_time = {"use_sim_time": True}

      # 啟動 Gazebo，載入世界檔
      gz_sim = IncludeLaunchDescription(
          PythonLaunchDescriptionSource(
              os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
          ),
          launch_arguments={"gz_args": f"-r {world_path}"}.items(),
      )

      # 把 Gazebo 模擬時間送進 ROS
      clock_bridge = Node(
          package="ros_gz_bridge",
          executable="parameter_bridge",
          arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
          output="screen",
      )

      robot_state_publisher = Node(
          package="robot_state_publisher",
          executable="robot_state_publisher",
          parameters=[{"robot_description": robot_description}, use_sim_time],
          output="screen",
      )

      # 從 /robot_description 把車生成進 Gazebo，gz_ros2_control 外掛隨之載入
      spawn_car = Node(
          package="ros_gz_sim",
          executable="create",
          arguments=["-topic", "robot_description", "-name", "diffcar", "-z", "0.5"],
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

      rviz_node = Node(
          package="rviz2",
          executable="rviz2",
          arguments=["-d", rviz_config],
          name="rviz2",
          parameters=[use_sim_time],
          output="screen",
      )

      return LaunchDescription(
          [
              gz_sim,
              clock_bridge,
              robot_state_publisher,
              spawn_car,
              # 依序啟動：生成車 -> joint_state_broadcaster -> 輪子控制器
              RegisterEventHandler(
                  OnProcessExit(
                      target_action=spawn_car,
                      on_exit=[joint_state_broadcaster_spawner],
                  )
              ),
              RegisterEventHandler(
                  OnProcessExit(
                      target_action=joint_state_broadcaster_spawner,
                      on_exit=[wheel_controller_spawner],
                  )
              ),
              rviz_node,
          ]
      )
  ```

  - 時鐘的同步問題
    - [文件](https://gazebosim.org/docs/latest/ros2_launch_gazebo/) 提到需要發布 clock 主題(`/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock`)給 gazebo controller manager
    - 以下是 Claude Sonnet 5.5 說的：Gazebo 的模擬時鐘可能比現實慢（電腦負載高、場景複雜，real-time factor < 1），可以比現實快，也可以暫停
    - {"use_sim_time": True} 參數讓節點改訂閱 /clock，並以此作為 ROS 時間。如此節點與 Gazebo 的時間同步
  - [教學](https://docs.ros.org/en/kilted/Tutorials/Intermediate/Launch/Using-Event-Handlers.html) 用 RegisterEventHandler on_exit 來控制啟動節點的順序：spawn_car → joint_state_broadcaster_spawner → wheel_controller_spawner
  - 為什麼需要 spawn_car 節點？
    - 情況 1：世界檔沒有車（官方範例做法）
      - 用 spawn_car 把 /robot_description 的車和外掛載入 gazebo
    - 情況 2：世界檔已含這台車
      - 不需要 spawn_car，否則會生出第二台車
      - 但世界檔內的那台車必須自己帶有 gz_ros2_control 外掛，並指向我的 controllers.yaml，且模型的 joint 名稱要與 `<ros2_control>` 一致，維護上有點麻煩
  - 為什麼沒有 ros2_control_node？
    - gz_ros2_control 外掛已經幫忙在 Gazebo 內啟動一個 controller manager，同一組硬體介面不應被兩個 controller manager 管理
    - 以後有機會再驗證：數位孿生的情境中，controller_manager 跑在實體車的 hardware interface 上，在 Gazebo 用 gz::sim::systems::JointPositionController，或直接用 ros_gz_bridge 把 joint／pose 寫進模擬

- 編輯 package.xml 檔案

  加上以下設定

  ```
  <exec_depend>ros_gz_sim</exec_depend>
  <exec_depend>ros_gz_bridge</exec_depend>
  <exec_depend>gz_ros2_control</exec_depend>
  <exec_depend>controller_manager</exec_depend>
  <exec_depend>diff_drive_controller</exec_depend>
  <exec_depend>joint_state_broadcaster</exec_depend>
  <exec_depend>robot_state_publisher</exec_depend>
  <exec_depend>rviz2</exec_depend>
  <exec_depend>xacro</exec_depend>
  ```

- 編輯 CMakeLists.txt 檔案

  加上以下設定

  ```
  install(
    DIRECTORY config launch urdf worlds
    DESTINATION share/${PROJECT_NAME}
  )
  ```

### 編譯、執行

- 回到根目錄，執行

  ```
    diffcar_ws$ colcon build --packages-select control_gazebo
    diffcar_ws$ . install/setup.sh
    diffcar_ws$ ros2 launch control_gazebo launch.py
  ```

  會看到 Gazebo 的視窗

- 用 `ros2 topic pub` 控制 Gazebo 小車

  ```
    $ ros2 topic pub /my_robot_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  "{twist: {linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.1}}}" --rate 10
  ```

  會看到 Gazebo 視窗中的小車開始前進

