---
title: MoveIt Path Planning
date: 2026-11-16 22:45:22
tags: [MoveIt, RViz, Gazebo]
categories: simulation 筆記
---

MoveIt Action 控制機械手臂的點到點移動。

<!-- more -->

### 環境

- 作業系統 Ubuntu 24.04
- ROS2 Kilted
- Gazebo Ionic
- Universal Robots 驅動與模擬套件


雖然有 moveit_py 這個 moveIt 提供的 python 介面，
但它會自己建立一個 move_group，
與我想要用的 ur_sim_moveit.launch.py 會重複，
所以這一篇練習不使用 moveit_py、而是呼叫現有的 `/move_action` action。

### 關於 move_group
[參考資料](https://discourse.openrobotics.org/t/moveit-2-journey-first-demonstrator-in-ros-2-planning-to-a-joint-space-goal/9301)
有三個層次
- Package(套件)：moveit_ros_move_group 是 ROS2 的套件,可以編譯、安裝的。
- Node(節點)：這個套件裡有一個可執行檔 move_group。執行它(通常用 launch file 啟動)就會產生一個執行中的 ROS2 node，名稱也叫 move_group。
- Action / Service：這個 node 運行後,對外提供一組介面,例如:
  - Action：/move_action(規劃並執行)、/execute_trajectory
  - Service：/plan_kinematic_path、/get_planning_scene、/compute_ik、/compute_fk 等


### 建立專案

我命名這個專案叫 ur5e_ptp

`arm_ws/src$ ros2 pkg create --build-type ament_python ur5e_ptp`

專案資料夾結構

```
arm_ws/src
└── ur5e_ptp
    ├── package.xml
    ├── resource
    │   └── ur5e_ptp
    ├── setup.cfg
    ├── setup.py
    └── ur5e_ptp
        ├── __init__.py
        └── ptp.py  << 我們接下來要建立的檔案
```

### 開發

- 建立 `ur5e_ptp/ur5e_ptp/ptp.py`

    ```
    import sys
    import rclpy
    from rclpy.node import Node
    from rclpy.action import ActionClient
    from moveit_msgs.action import MoveGroup
    from moveit_msgs.msg import Constraints, JointConstraint

    JOINTS = [
        "shoulder_pan_joint",
        "shoulder_lift_joint",
        "elbow_joint",
        "wrist_1_joint",
        "wrist_2_joint",
        "wrist_3_joint",
    ]

    POSES = {  # 弧度
        "A": [0.0, -1.57, 0.0, -1.57, 0.0, 0.0],
        "B": [0.8, -1.2, 1.0, -1.8, -1.57, 0.0],
    }


    class PtpNode(Node):
        def __init__(self):
            super().__init__("ur5e_ptp")
            self.client = ActionClient(self, MoveGroup, "/move_action")

        def move_to(self, joints):
            self.client.wait_for_server()
            goal = MoveGroup.Goal()
            req = goal.request
            req.group_name = "ur_manipulator"
            req.num_planning_attempts = 5
            req.allowed_planning_time = 5.0
            req.max_velocity_scaling_factor = 0.3
            req.max_acceleration_scaling_factor = 0.3
            c = Constraints()
            for name, pos in zip(JOINTS, joints):
                c.joint_constraints.append(
                    JointConstraint(
                        joint_name=name,
                        position=pos,
                        tolerance_above=0.01,
                        tolerance_below=0.01,
                        weight=1.0,
                    )
                )
            req.goal_constraints.append(c)
            goal.planning_options.plan_only = False  # False = 規劃並執行

            send = self.client.send_goal_async(goal)
            rclpy.spin_until_future_complete(self, send)
            handle = send.result()
            if not handle.accepted:
                self.get_logger().error("goal rejected")
                return False
            res = handle.get_result_async()
            rclpy.spin_until_future_complete(self, res)
            code = res.result().result.error_code.val
            self.get_logger().info(f"error_code={code} (1 = SUCCESS)")
            return code == 1


    def main():
        rclpy.init(args=sys.argv)
        node = PtpNode()
        for key in ("A", "B", "A"):
            if not node.move_to(POSES[key]):
                break
        node.destroy_node()
        rclpy.shutdown()

    ```

  - POSES 向量的關節順序和 JOINTS 宣告的順序一致
  - `move_group` action 控制關節的轉動角度，單位是 rad
    - RViz 的 MotionPlanning 面板 Joints 分頁顯示的是度(degree)
    - URDF 的關節 <limit lower upper> 也是 rad
  - 這個程式裡只有一個目標：「6 個關節同時達到這組位置(誤差各 ±0.01 rad)」
    - constraint 不規定哪個關節先動、哪個後動
    - 只要有一個關節不可達，這個目標就無法滿足，機器人完全不動
  - 補充：`/move_action` 的 request 不能直接填具名姿態。具名姿態只是 SRDF 裡存的一組關節值,要先讀出來再轉成 `JointConstraint`。


- 編輯 `ur5e_ptp/setup.py`

```
entry_points={
    'console_scripts': [
        'ptp = ur5e_ptp.ptp:main',
    ],
},
```

- 編輯 `ur5e_ptp/package.xml`

```
<exec_depend>rclpy</exec_depend>
<exec_depend>moveit_msgs</exec_depend>
<exec_depend>ur_simulation_gz</exec_depend>
```

### 編譯

```
arm_ws$ colcon build --packages-select ur5e_ptp --symlink-install
arm_ws$ source install/setup.bash
```

### 測試

- [終端機 A] 前置作業

`$ ros2 launch ur_simulation_gz ur_sim_moveit.launch.py ur_type:=ur5e`

- [終端機 B] 執行點到點的移動

`$ ros2 run ur5e_ptp ptp`

終端機輸出

```
[INFO] [1795189209.443909243] [ur5e_ptp]: error_code=1 (1 = SUCCESS)
[INFO] [1795189213.407994043] [ur5e_ptp]: error_code=1 (1 = SUCCESS)
[INFO] [1795189217.258545969] [ur5e_ptp]: error_code=1 (1 = SUCCESS)
```

在 UR5e 手臂靜止後，執行 `$ ros2 topic echo /joint_states --once`

終端機印出目前手臂的姿態

```
---
header:
  stamp:
    sec: 143
    nanosec: 844000000
  frame_id: base_link
name:
- elbow_joint
- shoulder_lift_joint
- shoulder_pan_joint
- wrist_1_joint
- wrist_2_joint
- wrist_3_joint
position:
- 0.0010963213350659064
- -1.5704286788497088
- 0.007048559812828922
- -1.5765197293739979
- -0.0015959506900845829
- -0.004129935903474681
velocity:
- -1.0340578220080499e-16
- -1.0490898107911109e-13
- -3.903737684669839e-16
- 1.0652871813843223e-13
- 9.44069041691753e-17
- -3.9063804274652725e-16
effort:
- -0.020095016791679313
- -0.0352697405346492
- -8.470329472543003e-18
- 0.006871809418104502
- -0.0023865291672471355
- -3.533018229905512e-19
---
```

差不多是姿態 A 的位置，各關節誤差都在 0.01 rad 內。
