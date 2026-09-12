---
title: RViz 檢視可動作的機器人
date: 2026-09-12 15:52:23
tags: [Rviz, launch.py, joint_state_publisher_gui]
categories: simulation 筆記
---

這一篇來練習撰寫 launch.py，
將 URDF 載入 RViz，
透過 joint_state_publisher_gui 控制介面調整關節角度，
以及 robot_state_publisher 輔助計算機器人元件在 3D 空間的位置，
讓 Rviz 即時更新機器人的外觀。

<!-- more -->

### 環境

- 作業系統 Ubuntu 24.04
- ROS2 Kilted
  - `sudo apt install python3-colcon-common-extensions`
  - `sudo apt install ros-kilted-joint-state-publisher-gui`
  - `sudo apt install ros-kilted-robot-state-publisher`


### URDF

上一篇筆記製作的 URDF 檔
[LinkForge 教學有現成的 URDF](https://linkforge.readthedocs.io/en/latest/tutorials/building_diff_drive.html)，
為了方便檢視元件，
所以我手動填上了 material 設定。


### 產生專案目錄

給這個專案命名 `diffcar`

```
$ mkdir -p diffcar_ws/src
$ cd diffcar_ws
diffcar_ws$ colcon build
```

現在專案工作目錄長相如下：

```
diffcar_ws
├── build
├── install
├── log
└── src
```

### 產生自訂套件的目錄

給這個套件命名 `car_description`

```
diffcar_ws$ cd src
diffcar_ws/src$ ros2 pkg create --build-type ament_cmake car_description
```

現在專案工作目錄長相如下：

```
diffcar_ws
├── build
├── install
├── log
└── src
    └── car_description
        ├── CMakeLists.txt
        ├── include
        │   └── car_description
        ├── package.xml
        └── src
```

### 新增資料夾、複製檔案

```
diffcar_ws
└── src
    └── car_description
        ├── CMakeLists.txt
        ├── include
        │   └── car_description
        ├── launch                       << 手動新增 launch 資料夾
        ├── package.xml
        ├── rviz                         << 手動新增 rviz 資料夾
        │   └── display.rviz             << 從 ROS2 官方範例複製 rviz 設定檔
        ├── src
        └── urdf                         << 手動新增 urdf 資料夾
            └── diff_drive_robot.urdf    << 這是先前製作的 URDF 檔
```

[ROS2 官方範例的 RViz 設定檔](https://github.com/ros/urdf_tutorial/blob/ros2/rviz/urdf.rviz)

注意：

- Fixed Frame: base_link
  - URDF 檔也必須宣告一樣的字串 `base_link`，作為機器人的底盤名稱
  - 作為 RViz 世界座標的座標系
- Description Topic:
  - Value: /robot_description
    - 指示 RViz 去訂閱名為 `/robot_description` 的 ROS2 Topic，以取得機器人的 URDF
    - `robot_state_publisher` 這個節點預設的話題就是 `/robot_description`

### 撰寫 launch.py 檔案

在 launch 資料夾新增 display.launch.py 檔案，
在此因為只練習 URDF 格式，不是 xacro 格式，
所以用 python 的 open 函數讀檔，
暫時犧牲 `model_arg` 所提供的彈性讀檔功能。

```
import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    car_description_dir = get_package_share_directory("car_description")

    urdf_path = os.path.join(car_description_dir, "urdf", "diff_drive_robot.urdf")

    model_arg = DeclareLaunchArgument(
        name="model",
        default_value=urdf_path,
        description="Absolute path to robot urdf file",
    )

    with open(urdf_path, 'r') as infp:
        robot_description_content = infp.read()

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description_content}],
    )

    joint_state_publisher_gui_node = Node(
        package="joint_state_publisher_gui", executable="joint_state_publisher_gui"
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=[
            "-d",
            os.path.join(car_description_dir, "rviz", "display.rviz"),
        ],
    )

    return LaunchDescription(
        [
            model_arg,
            joint_state_publisher_gui_node,
            robot_state_publisher_node,
            rviz_node,
        ]
    )
```

### 編輯 CMakeLists.txt 檔案

`diffcar_ws/src/car_description/CMakeLists.txt` 這份檔案加上以下設定

```
install(
  DIRECTORY launch urdf rviz
  DESTINATION share/${PROJECT_NAME}
)
```

### 編輯 package.xml 檔案

`diffcar_ws/src/car_description/package.xml` 這份檔案加上以下設定

```
  <exec_depend>robot_state_publisher</exec_depend>
  <exec_depend>urdf</exec_depend>
  <exec_depend>joint_state_publisher_gui</exec_depend>
  <exec_depend>rviz2</exec_depend>
  <exec_depend>ros2launch</exec_depend>
```

### 編譯、執行

回到根目錄，執行

```
diffcar_ws$ colcon build
diffcar_ws$ . install/setup.sh
diffcar_ws$ ros2 launch car_description display.launch.py
```

會看到 Rviz 視窗和 joint_state_publisher_gui 視窗，可以移動小視窗的拉桿轉動輪子。

![rviz](rviz.png "modify the joint state")

在終端機按下 ctrl + C，便可以關閉 RViz 和小視窗。
