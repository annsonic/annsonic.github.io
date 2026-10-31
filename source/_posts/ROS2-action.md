---
title: ROS2 action
date: 2026-10-24 16:43:43
tags: [action]
categories: simulation 筆記
---

練習 ROS2 action，
控制小車到達指定位置和朝向（直接用 /my_robot_controller/odom 取得小車位置，沒有用 TF）。

<!-- more -->

### 環境

  - 作業系統 Ubuntu 24.04
  - ROS2 Kilted

### 專案概念

- 小車的 `/my_robot_controller/odom` 含有位置和朝向（四元數）
  - 用簡單公式 `yaw = atan2(2(wz + xy), 1 − 2(y² + z²))`
- 控制邏輯：先轉向目標，對齊後前進，到達後再修正最終朝向
  - 容許誤差（0.10 m、0.05 rad）

### 練習

前置作業跟建立 ROS2 service 一樣呢...

- 建立專案

  這是三輪小車的專案工作目錄：

  ```
  diffcar_ws
  ├── build
  ├── install
  ├── log
  └── src
      └── control_tutorial
          ├── CMakeLists.txt
          ├── config
          │   ├── controllers.yaml
          │   └── display.rviz
          ├── include
          ├── launch
          │   ├── launch.py
          │   └── action.launch.py  << 這次要新增的 launch.py
          ├── package.xml
          ├── src
          └── urdf
              └── car.xacro
  ```

  新增一個用來定義 action 資料格式的專案，我命名為 `nav_action_interface`

  `diffcar_ws/src$ ros2 pkg create --build-type ament_cmake nav_action_interface`

  以及專門放 action 定義檔的資料夾

  `diffcar_ws/src$ mkdir -p nav_action_interface/action`

  nav_action_interface 專案工作目錄：

  ```
  diffcar_ws
  ├── build
  ├── install
  ├── log
  └── src
      └── nav_action_interface/
          ├── action
          │   └── NavigateToGoal.action  << 主角
          ├── CMakeLists.txt
          ├── include
          │   └── nav_action_interface
          ├── package.xml
          └── src
  ```

  新增一個用來定義 action server 和 client 的專案，我命名為 `nav_to_goal`

  `diffcar_ws/src$ ros2 pkg create --build-type ament_python nav_to_goal`

  以及 2 個資料夾

  `diffcar_ws/src$ mkdir -p nav_to_goal/{resource,nav_to_goal}`

  還有 2 個空檔案

  `diffcar_ws/src$ touch nav_to_goal/resource/nav_to_goal`

  `diffcar_ws/src$ touch nav_to_goal/nav_to_goal/__init__.py`

  nav_to_goal 專案工作目錄：

  ```
  diffcar_ws
  ├── build
  ├── install
  ├── log
  └── src
      └── nav_to_goal/
          ├── nav_to_goal
          │   ├── __init__.py
          │   ├── nav_client.py
          │   └── nav_server.py
          ├── package.xml
          ├── resource
          │   └── nav_to_goal
          ├── scripts
          ├── setup.cfg
          └── setup.py
  ```

#### 自定義的 Action

- 編輯 `nav_action_interface/action/NavigateToGoal.action`

```
float64 x
float64 y
float64 theta
---
bool success
string message
---
float64 current_x
float64 current_y
float64 current_theta
float64 distance_remaining
float64 heading_error
```

- 編輯 `nav_action_interface/CMakeLists.txt`

加上

```
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "action/NavigateToGoal.action"
)

ament_export_dependencies(rosidl_default_runtime)
```

- 編輯 `nav_action_interface/package.xml`

加上

```
  <buildtool_depend>rosidl_default_generators</buildtool_depend>
  <exec_depend>rosidl_default_runtime</exec_depend>
  <member_of_group>rosidl_interface_packages</member_of_group>
```

#### 建立 Action Server 節點

- 編輯 `nav_to_goal/setup.py`

加上

```
    entry_points={
        'console_scripts': [
            'nav_server = nav_to_goal.nav_server:main',
        ],
    },
```

- 編輯 `nav_to_goal/package.xml`

加上

```
  <depend>rclpy</depend>
  <depend>geometry_msgs</depend>
  <depend>nav_msgs</depend>
  <depend>nav_action_interface</depend>
```

- 撰寫 `nav_to_goal/nav_to_goal/nav_server.py`

```
#!/usr/bin/env python3
import math
import time

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node

from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry

from nav_action_interface.action import NavigateToGoal


def normalize_angle(a):
    return math.atan2(math.sin(a), math.cos(a))


def yaw_from_quaternion(q):
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z),
    )


class NavServer(Node):
    def __init__(self):
        super().__init__("nav_server")
        self.cb_group = ReentrantCallbackGroup()

        self.x = self.y = self.theta = 0.0
        self.odom_received = False

        self.cmd_pub = self.create_publisher(
            TwistStamped, "/my_robot_controller/cmd_vel", 10
        )
        self.create_subscription(
            Odometry,
            "/my_robot_controller/odom",
            self.odom_callback,
            10,
            callback_group=self.cb_group,
        )

        self._server = ActionServer(
            self,
            NavigateToGoal,
            "navigate_to_goal",
            execute_callback=self.execute,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.cb_group,
        )
        self.get_logger().info("NavServer ready.")

    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        self.theta = yaw_from_quaternion(msg.pose.pose.orientation)
        self.odom_received = True

    def goal_callback(self, goal_request):
        self.get_logger().info(
            f"Goal: x={goal_request.x:.2f} y={goal_request.y:.2f} "
            f"theta={goal_request.theta:.2f}"
        )
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info("Cancel requested")
        return CancelResponse.ACCEPT

    def _publish_cmd(self, linear=0.0, angular=0.0):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.twist.linear.x = linear
        msg.twist.angular.z = angular
        self.cmd_pub.publish(msg)

    def execute(self, goal_handle):
        goal = goal_handle.request
        result = NavigateToGoal.Result()
        feedback = NavigateToGoal.Feedback()
        period = 1.0 / 20.0  # 20 Hz

        while rclpy.ok():
            if goal_handle.is_cancel_requested:
                self._publish_cmd()
                goal_handle.canceled()
                result.success = False
                result.message = "Goal canceled"
                return result

            if not self.odom_received:
                time.sleep(period)
                continue

            dx = goal.x - self.x
            dy = goal.y - self.y
            dist = math.hypot(dx, dy)
            heading_error = normalize_angle(math.atan2(dy, dx) - self.theta)
            final_theta_error = normalize_angle(goal.theta - self.theta)

            feedback.current_x = self.x
            feedback.current_y = self.y
            feedback.current_theta = self.theta
            feedback.distance_remaining = dist
            feedback.heading_error = heading_error
            goal_handle.publish_feedback(feedback)

            if dist > 0.10:
                angular = max(-1.5, min(1.5, 2.0 * heading_error))
                if abs(heading_error) < 0.35:
                    linear = max(0.0, min(0.5, 0.6 * dist))
                else:
                    linear = 0.0
                self._publish_cmd(linear, angular)
            elif abs(final_theta_error) > 0.05:
                angular = max(-1.0, min(1.0, 2.0 * final_theta_error))
                self._publish_cmd(0.0, angular)
            else:
                self._publish_cmd()
                goal_handle.succeed()
                result.success = True
                result.message = "Goal reached"
                return result

            time.sleep(period)

        self._publish_cmd()
        goal_handle.abort()
        result.success = False
        result.message = "Node stopped"
        return result


def main():
    rclpy.init()
    node = NavServer()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        # 停車：controller 的 cmd_vel_timeout 0.5 秒會讓它自己停
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
```

- 注意：
  - execute 是阻塞的迴圈,若用單執行緒,odom_callback 就收不到資料，所以用 MultiThreadedExecutor
  - ReentrantCallbackGroup 允許同一群組內的 callback 同時執行
    - execute 在 while 迴圈裡 time.sleep 時，不會擋住其他 callback，所以 odom 能持續更新、cancel 也能即時處理
  - 這裡的 callback 函數跟 python async 函數沒有關係喔
    - 平行性來自執行緒：MultiThreadedExecutor 用 thread pool 同時跑多個 callback

- 驗證 action server 節點

```
colcon build --packages-select nav_action_interface nav_to_goal
source install/setup.bash
```

[terminal-A]
執行 `ros2 run nav_to_goal nav_server`

[terminal-B]
執行 `ros2 action send_goal /navigate_to_goal nav_action_interface/action/NavigateToGoal "{x: 2.0, y: 1.0, theta: 0.0}" --feedback`

得到類似以下格式的訊息(後續略)
```
Waiting for an action server to become available...
Sending goal:
x: 2.0
y: 1.0
theta: 0.0

Goal accepted with ID: edad93ce8ceb4c65a4c6d151033e98ca
```

#### 建立 Action Client 節點

- 編輯 `nav_to_goal/setup.py`

```
    entry_points={
        'console_scripts': [
            'nav_server = nav_to_goal.nav_server:main',
            'nav_client = nav_to_goal.nav_client:main',
        ],
    },
```

- 撰寫 `nav_to_goal/nav_to_goal/nav_client.py`

```
#!/usr/bin/env python3
import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions

from nav_action_interface.action import NavigateToGoal


class NavClient(Node):
    def __init__(self):
        super().__init__("nav_client")
        self._client = ActionClient(self, NavigateToGoal, "navigate_to_goal")
        self._goal_handle = None
        self._done = False

    def send_goal(self, x, y, theta):
        self.get_logger().info("Waiting for action server...")
        self._client.wait_for_server()

        goal = NavigateToGoal.Goal()
        goal.x = x
        goal.y = y
        goal.theta = theta

        self.get_logger().info(f"Sending goal: x={x}, y={y}, theta={theta}")
        send_future = self._client.send_goal_async(
            goal, feedback_callback=self.feedback_callback
        )
        send_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        self._goal_handle = future.result()
        if not self._goal_handle.accepted:
            self.get_logger().error("Goal rejected")
            self._done = True
            return

        self.get_logger().info("Goal accepted")
        result_future = self._goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        fb = feedback_msg.feedback
        self.get_logger().info(
            f"pos=({fb.current_x:.2f}, {fb.current_y:.2f}) "
            f"theta={fb.current_theta:.2f} "
            f"dist={fb.distance_remaining:.2f} "
            f"heading_err={fb.heading_error:.2f}",
            throttle_duration_sec=1.0,
        )

    def result_callback(self, future):
        result = future.result().result
        self.get_logger().info(
            f"Result: success={result.success}, message='{result.message}'"
        )
        self._done = True

    def cancel_goal(self):
        if self._goal_handle is not None and not self._done:
            self.get_logger().info("Canceling goal...")
            future = self._goal_handle.cancel_goal_async()
            rclpy.spin_until_future_complete(self, future)


def main():
    if len(sys.argv) != 4:
        print("Usage: ros2 run nav_to_goal nav_client <x> <y> <theta>")
        return

    x, y, theta = (float(v) for v in sys.argv[1:4])

    # rclpy 不再攔截 SIGINT,當遇到 ctrl+C 時改由 Python 拋出 KeyboardInterrupt
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = NavClient()
    node.send_goal(x, y, theta)

    try:
        while rclpy.ok() and not node._done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        # Ctrl+C 時取消目標，讓小車停下來 
        node.cancel_goal()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
```

- 撰寫 `control_tutorial/launch/action.launch.py`

複製 `control_tutorial/launch/launch.py`，再添加

```
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit

... 省略

def generate_launch_description():
    ... 省略

    nav_server = Node(
        package="nav_to_goal",
        executable="nav_server",
        name="nav_server",
        output="screen",
    )

    # 在 wheel_controller_spawner 完成後才啟動 nav_server
    start_nav_server_after_controller = RegisterEventHandler(
        OnProcessExit(
            target_action=wheel_controller_spawner,
            on_exit=[nav_server],
        )
    )

    return LaunchDescription(
        [
            robot_state_publisher,
            controller_manager,
            joint_state_broadcaster_spawner,
            wheel_controller_spawner,
            start_nav_server_after_controller,
            rviz_node,
        ]
    )
```

- 驗證

```
colcon build --packages-select nav_to_goal control_tutorial
source install/setup.bash
```

[terminal-A]
執行 `ros2 launch control_tutorial action.launch.py`

會看到 Rviz 視窗，手動設定 Odometry Display 的 Topic 選 `/my_robot_controller/odom`

[terminal-B]
執行 `ros2 run nav_to_goal nav_client 2.0 1.0 0.0`

會看到 Rviz 當中的小車開始移動和自動調整轉向。

![軌跡](action.png "control the car towards the target")

附上終端機訊息紀錄：
```
[INFO] [1792834448.776422907] [nav_client]: Waiting for action server...
[INFO] [1792834449.027373030] [nav_client]: Sending goal: x=2.0, y=1.0, theta=0.0
[INFO] [1792834449.034673074] [nav_client]: Goal accepted
[INFO] [1792834449.035968295] [nav_client]: pos=(0.00, 0.00) theta=0.00 dist=2.24 heading_err=0.46
[INFO] [1792834450.066643951] [nav_client]: pos=(0.34, 0.12) theta=0.43 dist=1.88 heading_err=0.06
[INFO] [1792834451.089029778] [nav_client]: pos=(0.80, 0.36) theta=0.49 dist=1.36 heading_err=0.01
[INFO] [1792834452.093019916] [nav_client]: pos=(1.23, 0.59) theta=0.49 dist=0.87 heading_err=0.00
[INFO] [1792834453.132124734] [nav_client]: pos=(1.60, 0.79) theta=0.49 dist=0.45 heading_err=0.00
[INFO] [1792834454.199236918] [nav_client]: pos=(1.79, 0.89) theta=0.50 dist=0.24 heading_err=0.00
[INFO] [1792834455.238792853] [nav_client]: pos=(1.89, 0.94) theta=0.50 dist=0.12 heading_err=0.00
[INFO] [1792834456.270122995] [nav_client]: pos=(1.91, 0.95) theta=0.11 dist=0.10 heading_err=0.38
[INFO] [1792834456.609688228] [nav_client]: Result: success=True, message='Goal reached'
```
