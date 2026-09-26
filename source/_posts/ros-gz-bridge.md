---
title: ros_gz_bridge
date: 2026-09-19 15:27:10
tags: [ROS2, Gazebo]
categories: simulation 筆記
---


練習 ROS2 結合 Gazebo 做模擬。

<!-- more -->

### 環境

- 作業系統 Ubuntu 24.04
- ROS2 Kilted
- Gazebo Ionic

推薦這一堂 [YouTube 課程](https://www.youtube.com/watch?v=wOa1m8hzrgQ)，
很完整地走過安裝、製作三輪小車和模擬光達偵測障礙物，
不過因為有版權，
現在這一篇筆記是針對 Gazebo 官方文件做的筆記

- [從零建立 SDF 檔](https://gazebosim.org/docs/latest/building_robot/)
- [模擬移動行為](https://gazebosim.org/docs/latest/moving_robot/)

### 練習一：單純啟動 Gazebo GUI

- 建立專案

  Gazebo 文件推薦用 git clone 的方式，複製這個[專案樣板](https://github.com/gazebosim/ros_gz_project_template)，

  不過用另一個方式：下指令 `ros2 pkg create` 來創建專案是更自由的。

  給這個套件命名 `gz_tutorial`，專案資料夾結構：

  ```
  diffcar_ws
  └── src
      └── gz_tutorial/
          ├── CMakeLists.txt
          ├── package.xml
          ├── src/
          ├── include/
          ├── launch/                   # 手動新增
          │   └── gazebo_launch.py
          ├── config/                   # 手動新增
          │   └── keypublisher_gui.config
          └── worlds/                   # 手動新增
              └── building_robot.sdf    # 這是在上一篇筆記製作的 SDF 檔
  ```

- 撰寫 launch.py 檔案

  - 最小可執行版本，會啟動 Gazebo GUI，效果跟執行指令 `gz sim building_robot.sdf` 一樣。

  ```
    import os
    
    from ament_index_python.packages import get_package_share_directory
    from launch import LaunchDescription
    from launch.actions import IncludeLaunchDescription
    from launch.launch_description_sources import PythonLaunchDescriptionSource
    
    
    def generate_launch_description():
        pkg = get_package_share_directory('gz_tutorial')
        # 使用官方的 gz_sim.launch.py（包含 GUI）
        pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    
        gz_sim = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
            ),
            # 3. Pass arguments to Gazebo: load an empty world and run immediately (-r)
            launch_arguments={
                'gz_args': os.path.join(pkg, 'worlds', 'building_robot.sdf')
                }.items(),
        )
    
        return LaunchDescription([
            gz_sim
        ])
  ```

- 撰寫 keypublisher_gui.config

  ```
    <gui fullscreen="0">
        <plugin filename="MinimalScene" name="3D View">
            <gz-gui>
                <title>3D View</title>
                <property type="bool" key="showTitleBar">false</property>
                <property type="string" key="state">docked</property>
            </gz-gui>
            <engine>ogre2</engine>
            <scene>scene</scene>
            <ambient_light>0.4 0.4 0.4</ambient_light>
            <background_color>0.8 0.8 0.8</background_color>
            <camera_pose>-6 0 6 0 0.5 0</camera_pose>
        </plugin>
    
        <plugin filename="GzSceneManager" name="Scene Manager">
            <gz-gui><property key="resizable" type="bool">false</property>
                <property key="width" type="double">5</property>
                <property key="height" type="double">5</property>
                <property key="state" type="string">floating</property>
                <property key="showTitleBar" type="bool">false</property>
            </gz-gui>
        </plugin>
    
        <!-- 鍵盤事件發布到 /keyboard/keypress -->
        <plugin filename="KeyPublisher" name="Key Publisher"/>
    </gui>
  ```

- 編輯 CMakeLists.txt 檔案

  ```
    install(
      DIRECTORY config launch worlds
      DESTINATION share/${PROJECT_NAME}
    )
  ```

- 編輯 package.xml 檔案

  ```
    <exec_depend>ros_gz_sim</exec_depend> 
    <exec_depend>ros2launch</exec_depend>
  ```

- 編譯、執行

  ```
  diffcar_ws$ colcon build --packages-select gz_tutorial
  diffcar_ws$ . install/setup.sh
  diffcar_ws$ ros2 launch gz_tutorial gazebo_launch.py
  ```

### 練習二：Gazebo 控制小車，同時在 RViz 檢視里程計

- 專案資料夾

  ```
  diffcar_ws
  └── src
      └── gz_tutorial/
          ├── CMakeLists.txt
          ├── package.xml
          ├── src/
          ├── include/
          ├── launch/
          │   └── gazebo_launch.py
          ├── config/
          │   └── bridge.yaml         # 新增
          │   └── diff_drive.rviz            # 新增
          │   └── keypublisher_gui.config
          └── worlds/
              └── building_robot.sdf
  ```

  - ros_gz_bridge 把 Gazebo 的 `/model/vehicle_blue/odometry` 橋接到 ROS2 的 `nav_msgs/msg/Odometry`
  - RViz2 訂閱到這個 topic

- 調整 launch.py 檔案

  ```
    import os
    
    from ament_index_python.packages import get_package_share_directory
    from launch import LaunchDescription
    from launch.actions import IncludeLaunchDescription
    from launch.launch_description_sources import PythonLaunchDescriptionSource
    from launch_ros.actions import Node
    
    
    def generate_launch_description():
        pkg = get_package_share_directory("gz_tutorial")
        pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")
    
        world_path = os.path.join(pkg, "worlds", "building_robot.sdf")
        gui_config_path = os.path.join(pkg, "config", "keypublisher_gui.config")
    
        gz_sim = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
            ),
            launch_arguments={
                "gz_args": f"-r --gui-config {gui_config_path} {world_path}"
            }.items(),
        )
    
        bridge = Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            parameters=[
                {
                    "config_file": os.path.join(pkg, "config", "bridge.yaml"),
                    "qos_overrides./tf_static.publisher.durability": "transient_local",
                    "use_sim_time": True,
                }
            ],
            output="screen",
        )
    
        rviz = Node(
           package='rviz2',
           executable='rviz2',
           arguments=['-d', os.path.join(pkg, 'config', 'diff_drive.rviz')],
           parameters=[{'use_sim_time': True}],
        )
    
        return LaunchDescription(
            [
                gz_sim,
                bridge,
                rviz,
            ]
        )
  ```

- 建立 bridge.yaml
  - 從[樣板](https://github.com/gazebosim/ros_gz_project_template/blob/main/ros_gz_example_bringup/config/ros_gz_example_bridge.yaml)複製得到

- 建立 diff_drive.rviz
  - 從[樣板](https://github.com/gazebosim/ros_gz_project_template/blob/main/ros_gz_example_bringup/config/diff_drive.rviz)複製得到

- 編輯 package.xml 檔案

  ```
    <exec_depend>ros_gz_bridge</exec_depend>
    <exec_depend>rviz2</exec_depend>
  ```

- 編譯、執行

  - Step - 1: 在終端機

    ```
    diffcar_ws$ colcon build --packages-select gz_tutorial
    diffcar_ws$ . install/setup.sh
    diffcar_ws$ ros2 launch gz_tutorial gazebo_launch.py
    ```

  檢查 Topic，預期要看到

  /model/vehicle_blue/odometry

  /model/vehicle_blue/tf

  - Step - 2: 在 RViz 視窗

    - Odometry Display 的 Topic 選 /model/vehicle_blue/odometry

    - Fixed Frame 改成 odom（不是 diff_drive/odom）

- 在 Gazebo 視窗用鍵盤移動小車，Rviz 視窗會同步繪製紅色箭頭
  - 紅色箭頭就是機器人隨時間移動留下的一系列 pose（位置+方向）

  ![里程計訊息視覺化](odometry.png)
