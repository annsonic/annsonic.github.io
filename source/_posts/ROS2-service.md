---
title: ROS2 service
date: 2026-10-14 21:56:11
tags: [service]
categories: simulation 筆記
---

練習 ROS2 service，
延續控制上一篇的三輪小車，
加上一個決定小車車速上限的塔台。

<!-- more -->

### 環境

  - 作業系統 Ubuntu 24.04
  - ROS2 Kilted
    - [安裝 rosdep](https://docs.ros.org/en/kilted/Tutorials/Intermediate/Rosdep.html)

      `sudo apt install python3-rosdep`

      `sudo rosdep init`

### 專案概念

- 適合 ROS2 service 的情境

  ```
    這是持續更新的資料嗎？
    ├─ 是 → Topic
    └─ 否 → 這是節點的設定值嗎？
            ├─ 是 → Parameter
            └─ 否 → 我要請別的節點做一件事嗎？
                    ├─ 很快做完，且要知道結果 → Service
                    └─ 要很久、要進度或可取消 → Action
  ```

  跟 AI 討論的結果，這個專案讓 service server 擔任評估剩餘電量、決定速度上限的塔台角色。

- 用里程計模擬電量消耗
  - 三輪小車 `diff_drive_controller` 會發布 `/my_robot_controller/odom` 消息，型別是 `nav_msgs/msg/Odometry`
- 電量低時，service server「限制最高速度」或「強制降速」
  - 三輪小車 `controllers.yaml` 設定了 linear.x.max_velocity: 0.7 和 angular.z.max_velocity: 4.0，設計 service server 最高速度也要落在此範圍
  - 設計規則
  
    | 模擬電量 | 行為 |
    | -------- | ------- |
    | >= 50%	| 允許 slow / normal / fast |
    | 20%–50%	| 拒絕 fast，允許 slow / normal |
    | <= 20%	| 只允許 slow |
- 在終端機按下鍵盤按鈕，控制小車的移動和切換速度
  - 按 w/s/a/d：前進、後退、原地左轉、原地右轉
  - 按 1/2/3：低速檔位、常速檔位、高速檔位

### 練習

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
          │   └── service.launch.py  << 這次要新增的 launch.py
          ├── package.xml
          ├── src
          └── urdf
              └── car.xacro
  ```

  新增一個用來定義 service 資料格式的專案，我命名為 `set_velocity_interface`

  `diffcar_ws/src$ ros2 pkg create --build-type ament_cmake set_velocity_interface`

  以及專門放 service 定義檔的資料夾

  `diffcar_ws/src$ mkdir -p set_velocity_interface/srv`

  專門放 topic message 定義檔的資料夾

  `diffcar_ws/src$ mkdir -p set_velocity_interface/msg`

  set_velocity_interface 專案工作目錄：

  ```
  diffcar_ws
  ├── build
  ├── install
  ├── log
  └── src
      └── set_velocity_interface
          ├── CMakeLists.txt
          ├── include
          ├── msg
          │   └── SpeedProfileState.msg
          ├── package.xml
          ├── src
          └── srv
              └── SetSpeedProfile.srv    << 主角
  ```

  新增一個用來定義 service client 的專案，我命名為 `teleoperation`

  `diffcar_ws/src$ ros2 pkg create --build-type ament_python teleoperation`

  以及 3 個資料夾

  `diffcar_ws/src$ mkdir -p teleoperation/{resource,teleoperation,scripts}`

  還有 2 個空檔案

  `diffcar_ws/src$ touch teleoperation/resource/teleoperation`

  `diffcar_ws/src$ touch teleoperation/teleoperation/__init__.py`

  teleoperation 專案工作目錄：

  ```
  diffcar_ws/
  └── src/
      └── teleoperation/
          ├── package.xml
          ├── resource
          │   └── teleoperation
          ├── setup.cfg
          ├── setup.py
          └── teleoperation
              ├── __init__.py
              ├── speed_profile_server.py   << 主角 service server
              └── teleop_keyboard.py        << 主角 service client
  ```

#### 自定義的 Service

- 撰寫 service 定義檔 `set_velocity_interface/srv/SetSpeedProfile.srv`

  ```
    # range: slow, normal, fast
    string profile
    ---
    bool success
    string message
    
    string active_profile
    # 單位：m/s, 正值
    float64 linear_speed
    # 單位：m/s, 正值
    float64 angular_speed
    
    # 模擬電量 0.0 ~ 100.0，由 odom 累積里程換算
    float64 battery_percent
  ```

- 撰寫 `set_velocity_interface/msg/SpeedProfileState.msg` 定義檔

  ```
    string active_profile
    float64 linear_speed
    float64 angular_speed
    float64 battery_percent
  ```

- 修改 `set_velocity_interface/CMakeLists.txt`

  加上以下設定

  ```
    find_package(ament_cmake REQUIRED)
    find_package(rosidl_default_generators REQUIRED)
    
    rosidl_generate_interfaces(${PROJECT_NAME}
      "srv/SetSpeedProfile.srv"
      "msg/SpeedProfileState.msg"
    )
    ament_export_dependencies(rosidl_default_runtime)
  ```

- 修改 `set_velocity_interface/package.xml`

  加上以下設定

  ```
    <buildtool_depend>rosidl_default_generators</buildtool_depend>
    <exec_depend>rosidl_default_runtime</exec_depend>
    <member_of_group>rosidl_interface_packages</member_of_group>
  ```

- 驗證 set_velocity_interface 專案

  `diffcar_ws$ colcon build --packages-select set_velocity_interface`

  `diffcar_ws$ source install/setup.bash`

  `diffcar_ws$ ros2 interface show set_velocity_interface/srv/SetSpeedProfile`

  可以看到 service 資料格式。

#### 建立 Service Server 節點

- 撰寫 `teleoperation/setup.py`

  ```
    from setuptools import find_packages, setup
    
    package_name = "teleoperation"
    
    setup(
        name=package_name,
        version="0.0.1",
        packages=find_packages(exclude=["test"]),
        data_files=[
            (
                "share/ament_index/resource_index/packages",
                ["resource/" + package_name],
            ),
            (
                "share/" + package_name,
                ["package.xml"],
            ),
        ],
        install_requires=["setuptools"],
        zip_safe=True,
        maintainer="somebody",
        maintainer_email="somebody@domain",
        description="Speed profile service for mock robot teleoperation.",
        license="Apache-2.0",
        entry_points={
            "console_scripts": [
                "speed_profile_server = teleoperation.speed_profile_server:main",
                "teleop_keyboard = teleoperation.teleop_keyboard:main",
            ],
        },
    )
  ```

- 撰寫 `teleoperation/setup.cfg`

  ```
    [develop]
    script_dir=$base/lib/teleoperation
    
    [install]
    install_scripts=$base/lib/teleoperation
  ```

- 撰寫 `teleoperation/package.xml`

  ```
    <exec_depend>rclpy</exec_depend>
    <exec_depend>geometry_msgs</exec_depend>
    <exec_depend>set_velocity_interface</exec_depend>
    <exec_depend>nav_msgs</exec_depend>
    <exec_depend>std_srvs</exec_depend>
  ```

- 撰寫 `teleoperation/teleoperation/speed_profile_server.py`

  ```
    import math
    
    import rclpy
    from nav_msgs.msg import Odometry
    from rclpy.executors import ExternalShutdownException
    from rclpy.node import Node
    from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
    from std_srvs.srv import Trigger
    
    from set_velocity_interface.msg import SpeedProfileState
    from set_velocity_interface.srv import SetSpeedProfile
    
    # 由慢到快排序，index 越大越快
    PROFILE_ORDER = ["slow", "normal", "fast"]
    
    # 每個 profile 的速度大小：(m/s, rad/s)
    PROFILES = {
        "slow": (0.1, 0.3),
        "normal": (0.2, 0.6),
        "fast": (0.4, 1.0),
    }
    
    # 電量分級：(電量下限%, 此區間允許的最快 profile)，由高到低比對
    BATTERY_TIERS = [
        (50.0, "fast"),    # > 50%：全部允許
        (20.0, "normal"),  # 20% ~ 50%：最快到 normal
        (0.0, "slow"),     # < 20%：只允許 slow（含 0%，避免完全鎖死）
    ]
    
    # 單次位移小於此值視為雜訊；大於此值視為 odom 重置/跳變，都不累積
    MIN_STEP_M = 0.001
    MAX_STEP_M = 1.0
    
    
    def rank(profile: str) -> int:
        return PROFILE_ORDER.index(profile)
    
    
    class SpeedProfileServer(Node):
        def __init__(self):
            super().__init__("speed_profile_server")
    
            self.declare_parameter("odom_topic", "/my_robot_controller/odom")
            # 假設跑滿這個距離，電量歸零（練習用，設小一點比較容易測試）
            self.declare_parameter("full_range_m", 20.0)
    
            odom_topic = self.get_parameter("odom_topic").value
            self._full_range_m = float(self.get_parameter("full_range_m").value)
    
            self._active_profile = "normal"
            self._distance_m = 0.0
            self._last_xy = None
    
            self._odom_sub = self.create_subscription(
                Odometry, odom_topic, self._on_odom, 10
            )
            self._speed_srv = self.create_service(
                SetSpeedProfile, "/set_speed_profile", self._on_set_profile
            )
            self._reset_srv = self.create_service(
                Trigger, "/reset_battery", self._on_reset_battery
            )
    
            self.get_logger().info(
                f"Ready. odom_topic={odom_topic}, full_range_m={self._full_range_m}. "
                "Services: /set_speed_profile, /reset_battery"
            )
    
            # latched：後來才啟動的 client 也能立刻拿到最新狀態
            state_qos = QoSProfile(
                history=HistoryPolicy.KEEP_LAST,
                depth=1,
                reliability=ReliabilityPolicy.RELIABLE,
                durability=DurabilityPolicy.TRANSIENT_LOCAL,
            )
            self._state_pub = self.create_publisher(
                SpeedProfileState, "/speed_profile_state", state_qos
            )
            # 電量會持續變化，每秒也發一次
            self._state_timer = self.create_timer(1.0, self._publish_state)
            self._publish_state()
    
        # ---------- 電量模擬 ----------
        def _on_odom(self, msg: Odometry):
            x = msg.pose.pose.position.x
            y = msg.pose.pose.position.y
    
            if self._last_xy is not None:
                step = math.hypot(x - self._last_xy[0], y - self._last_xy[1])
                if MIN_STEP_M < step < MAX_STEP_M:
                    self._distance_m += step
            self._last_xy = (x, y)
    
            self._enforce_battery_limit()
    
        def _battery_percent(self) -> float:
            remaining = 1.0 - self._distance_m / self._full_range_m
            return max(0.0, min(100.0, 100.0 * remaining))
    
        def _max_allowed_profile(self) -> str:
            battery = self._battery_percent()
            for lower_bound, max_profile in BATTERY_TIERS:
                if battery > lower_bound:
                    return max_profile
            return "slow"  # 電量剛好 0%
    
        def _enforce_battery_limit(self):
            """電量下降導致目前 profile 超出允許範圍時，主動降速。"""
            max_profile = self._max_allowed_profile()
            if rank(self._active_profile) > rank(max_profile):
                self.get_logger().warning(
                    f"Battery {self._battery_percent():.0f}%: "
                    f"forced profile {self._active_profile} -> {max_profile}"
                )
                self._active_profile = max_profile
                self._publish_state()
    
        # ---------- Services ----------
        def _on_set_profile(self, request, response):
            requested = request.profile
    
            if requested not in PROFILES:
                response.success = False
                response.message = (
                    f"Unknown profile: {requested!r}. Expected slow, normal, or fast."
                )
                self.get_logger().warning(response.message)
            else:
                max_profile = self._max_allowed_profile()
                is_speeding_up = rank(requested) > rank(self._active_profile)
    
                # 只有「往更快」才檢查電量；降速或維持永遠允許
                if is_speeding_up and rank(requested) > rank(max_profile):
                    response.success = False
                    response.message = (
                        f"Battery low ({self._battery_percent():.0f}%): "
                        f"{requested!r} not allowed, max is {max_profile!r}."
                    )
                    self.get_logger().warning(response.message)
                else:
                    self._active_profile = requested
                    self._publish_state()
                    response.success = True
                    response.message = f"Activated profile: {self._active_profile}"
                    self.get_logger().info(response.message)
    
            # 無論成功或失敗，都回報目前實際生效的設定
            linear_speed, angular_speed = PROFILES[self._active_profile]
            response.active_profile = self._active_profile
            response.linear_speed = linear_speed
            response.angular_speed = angular_speed
            response.battery_percent = self._battery_percent()
            return response
    
        def _on_reset_battery(self, request, response):
            self._distance_m = 0.0
            self._publish_state()
            response.success = True
            response.message = "Battery recharged to 100%"
            self.get_logger().info(response.message)
            return response
    
        def _publish_state(self):
            linear_speed, angular_speed = PROFILES[self._active_profile]
            msg = SpeedProfileState()
            msg.active_profile = self._active_profile
            msg.linear_speed = linear_speed
            msg.angular_speed = angular_speed
            msg.battery_percent = self._battery_percent()
            self._state_pub.publish(msg)
    
    
    def main(args=None):
        rclpy.init(args=args)
        node = SpeedProfileServer()
    
        try:
            rclpy.spin(node)
        except (KeyboardInterrupt, ExternalShutdownException):
            pass
        finally:
            node.destroy_node()
            rclpy.try_shutdown()
    
    
    if __name__ == "__main__":
        main()
  ```

- 驗證 teleoperation 專案

  ```
  diffcar_ws$ colcon build --packages-select teleoperation
  diffcar_ws$ source install/setup.bash
  ```

  ```
  diffcar_ws$ ros2 service list -t
  diffcar_ws$ ros2 service type /set_speed_profile
  diffcar_ws$ ros2 service call /set_speed_profile set_velocity_interface/srv/SetSpeedProfile "{profile: slow}"
  ```

#### 建立 Service Client 節點

- 修改 `teleoperation/setup.py`

  console_scripts 加上 teleop_keyboard，如下

  ```
    entry_points={
        "console_scripts": [
            "speed_profile_server = teleoperation.speed_profile_server:main",
            "teleop_keyboard = teleoperation.teleop_keyboard:main",
        ],
    },
  ```

- 撰寫 `teleoperation/teleoperation/teleop_keyboard.py`

  ```
    import select
    import sys
    import termios
    import threading
    import tty
    
    import rclpy
    from geometry_msgs.msg import TwistStamped
    from rclpy.executors import ExternalShutdownException
    from rclpy.node import Node
    from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
    
    from set_velocity_interface.msg import SpeedProfileState
    from set_velocity_interface.srv import SetSpeedProfile
    
    # 停止逾時：超過這段時間沒有新的移動輸入，就自動停止
    INPUT_TIMEOUT_SEC = 0.5
    # cmd_vel 發布頻率
    PUBLISH_PERIOD_SEC = 0.1
    
    INSTRUCTIONS = """
    鍵盤控制：
      w：前進     s：後退
      a：左轉(原地)  d：右轉(原地)
      空白鍵：停止
    
      1：慢速  2：正常  3：快速
      （實際速度由 server 決定，可能因電量不足被拒絕或自動降速）
    
    Ctrl+C 離開
    """


    def get_key(settings):
        tty.setcbreak(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        key = sys.stdin.read(1) if rlist else ""
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        return key


    class TeleopKeyboard(Node):
        def __init__(self):
            super().__init__("teleop_keyboard")
    
            self._cmd_pub = self.create_publisher(
                TwistStamped, "/my_robot_controller/cmd_vel", 10
            )
            self._speed_client = self.create_client(SetSpeedProfile, "/set_speed_profile")
    
            # 速度大小完全由 server 決定；收到第一筆狀態前保持 0，車子不會動
            self._linear_speed = 0.0
            self._angular_speed = 0.0
            self._active_profile = None
            self._have_state = False
    
            state_qos = QoSProfile(
                history=HistoryPolicy.KEEP_LAST,
                depth=1,
                reliability=ReliabilityPolicy.RELIABLE,
                durability=DurabilityPolicy.TRANSIENT_LOCAL,
            )
            self._state_sub = self.create_subscription(
                SpeedProfileState, "/speed_profile_state", self._on_state, state_qos
            )
    
            # 目前方向：-1, 0, 1（代表倍率），分別給 linear / angular
            self._linear_dir = 0.0
            self._angular_dir = 0.0
    
            self._last_key_time = self.get_clock().now()
            self._lock = threading.Lock()
    
            self._timer = self.create_timer(PUBLISH_PERIOD_SEC, self._on_timer)
    
            self.get_logger().info(INSTRUCTIONS)

        # ---------- Server 狀態（唯一的速度來源） ----------
        def _on_state(self, msg: SpeedProfileState):
            with self._lock:
                changed = msg.active_profile != self._active_profile
                self._active_profile = msg.active_profile
                self._linear_speed = msg.linear_speed
                self._angular_speed = msg.angular_speed
                self._have_state = True
    
            if changed:
                self.get_logger().info(
                    f"目前 profile: {msg.active_profile} "
                    f"({msg.linear_speed} m/s, {msg.angular_speed} rad/s), "
                    f"電量 {msg.battery_percent:.0f}%"
                )

        # ---------- Service 呼叫（非阻塞） ----------
        def request_profile(self, profile: str):
            if not self._speed_client.service_is_ready():
                self.get_logger().warning("Service 尚未就緒，稍後再試")
                return
    
            request = SetSpeedProfile.Request()
            request.profile = profile
            future = self._speed_client.call_async(request)
            future.add_done_callback(self._on_profile_response)

        def _on_profile_response(self, future):
            try:
                response = future.result()
            except Exception as exc:  # noqa: BLE001
                self.get_logger().error(f"Service 呼叫失敗: {exc}")
                return
    
            # 這裡只顯示結果；速度的更新一律走 /speed_profile_state
            text = f"{response.message} (電量 {response.battery_percent:.0f}%)"
            if response.success:
                self.get_logger().info(text)
            else:
                self.get_logger().warning(text)

        # ---------- 按鍵處理 ----------
        def handle_key(self, key: str):
            if key in ("w", "s", "a", "d"):
                with self._lock:
                    if key == "w":
                        self._linear_dir, self._angular_dir = 1.0, 0.0
                    elif key == "s":
                        self._linear_dir, self._angular_dir = -1.0, 0.0
                    elif key == "a":
                        self._linear_dir, self._angular_dir = 0.0, 1.0
                    elif key == "d":
                        self._linear_dir, self._angular_dir = 0.0, -1.0
                    self._last_key_time = self.get_clock().now()
    
            elif key == " ":
                with self._lock:
                    self._linear_dir = 0.0
                    self._angular_dir = 0.0
                    self._last_key_time = self.get_clock().now()
    
            elif key == "1":
                self.request_profile("slow")
            elif key == "2":
                self.request_profile("normal")
            elif key == "3":
                self.request_profile("fast")

        # ---------- Timer：統一發布 cmd_vel + 逾時停止 ----------
        def _on_timer(self):
            now = self.get_clock().now()
    
            with self._lock:
                elapsed = (now - self._last_key_time).nanoseconds / 1e9
                if elapsed > INPUT_TIMEOUT_SEC:
                    self._linear_dir = 0.0
                    self._angular_dir = 0.0
    
                msg = TwistStamped()
                msg.header.stamp = now.to_msg()
                msg.header.frame_id = "base_link"
                if self._have_state:
                    msg.twist.linear.x = self._linear_dir * self._linear_speed
                    msg.twist.angular.z = self._angular_dir * self._angular_speed
    
            self._cmd_pub.publish(msg)


    def _spin(node):
        try:
            rclpy.spin(node)
        except ExternalShutdownException:
            pass
        except Exception as exc:  # noqa: BLE001
            node.get_logger().error(f"spin 執行緒異常終止: {exc!r}")


    def main(args=None):
        rclpy.init(args=args)
        node = TeleopKeyboard()
    
        spin_thread = threading.Thread(target=_spin, args=(node,), daemon=True)
        spin_thread.start()
    
        settings = termios.tcgetattr(sys.stdin)
        try:
            while rclpy.ok():
                key = get_key(settings)
                if key:
                    if key == "\x03":  # Ctrl+C
                        break
                    node.handle_key(key)
        except (KeyboardInterrupt, ExternalShutdownException):
            pass
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    
            stop = TwistStamped()
            stop.header.stamp = node.get_clock().now().to_msg()
            node._cmd_pub.publish(stop)
            node.destroy_node()
    
            rclpy.try_shutdown()
            spin_thread.join(timeout=1.0)
    
    
    if __name__ == "__main__":
        main()
  ```

- 驗證 teleoperation.teleop_keyboard 節點

  ```
  diffcar_ws$ colcon build --packages-select teleoperation
  diffcar_ws$ source install/setup.bash
  ```

  [terminal-A]

  `$ ros2 run teleoperation speed_profile_server --ros-args -p full_range_m:=5.0`

  [terminal-B]

  `$ ros2 run teleoperation teleop_keyboard`

  [terminal-C]

  `$ ros2 topic echo /my_robot_controller/cmd_vel`
  
  在 B 終端機按鈕控制，預期在 C 終端機看到以下格式的訊息(數值隨按鈕而不同)：

  ```
    header:
      stamp:
        sec: 1792596751
        nanosec: 786300383
      frame_id: base_link
    twist:
      linear:
        x: 0.0
        y: 0.0
        z: 0.0
      angular:
        x: 0.0
        y: 0.0
        z: 0.6
  ```

#### 練習在 Rviz 視覺化小車的移動速度

- 撰寫 `control_tutorial/launch/service.launch.py`

  以既有的 `launch.py` 為基底，加上以下設定

```
    full_range_arg = DeclareLaunchArgument(
        "full_range_m",
        default_value="10.0",
        description="Distance (m) to drain the simulated battery to 0%",
    )

    speed_profile_server = Node(
        package="teleoperation",
        executable="speed_profile_server",
        output="screen",
        parameters=[
            {
                "full_range_m": ParameterValue(
                    LaunchConfiguration("full_range_m"), value_type=float
                )
            }
        ],
    )

    return LaunchDescription(
        [
            full_range_arg,
            robot_state_publisher,
            controller_manager,
            joint_state_broadcaster_spawner,
            wheel_controller_spawner,
            rviz_node,
            speed_profile_server
        ]
    )
```

  - 註：teleop_keyboard 是互動式 CLI 工具，在「使用者親自打開的終端機」裡執行，不能被包含進入 launch.py 裡

- 驗證

  ```
    diffcar_ws$ colcon build --packages-select control_tutorial
    diffcar_ws$ source install/setup.bash
  ```

  [terminal-A]
  
  `$ ros2 launch control_tutorial service.launch.py full_range_m:=5.0`
  
  會看到 Rviz 視窗，手動設定 Odometry Display 的 Topic 選 `/my_robot_controller/odom`

  [terminal-B]

  `$ ros2 run teleoperation teleop_keyboard`

  一樣在 B 終端機用鍵盤操控小車的移動。

  ![軌跡](rviz.png "control the car to move with speed profiling")

附上終端機訊息紀錄：
```
[speed_profile_server-6] [INFO] [1792741526.466690555] [speed_profile_server]: Activated profile: fast
[speed_profile_server-6] [WARN] [1792741534.970832161] [speed_profile_server]: Battery 50%: forced profile fast -> normal
[speed_profile_server-6] [WARN] [1792741545.791433873] [speed_profile_server]: Battery 20%: forced profile normal -> slow
[speed_profile_server-6] [WARN] [1792741600.007717328] [speed_profile_server]: Battery low (0%): 'normal' not allowed, max is 'slow'.

[INFO] [1792741500.687418003] [teleop_keyboard]: 
鍵盤控制：
  w：前進     s：後退
  a：左轉(原地)  d：右轉(原地)
  空白鍵：停止

  1：慢速  2：正常  3：快速
  （實際速度由 server 決定，可能因電量不足被拒絕或自動降速）

Ctrl+C 離開

[INFO] [1792741500.760331939] [teleop_keyboard]: 目前 profile: normal (0.2 m/s, 0.6 rad/s), 電量 100%
[INFO] [1792741526.467627262] [teleop_keyboard]: 目前 profile: fast (0.4 m/s, 1.0 rad/s), 電量 87%
[INFO] [1792741526.470997588] [teleop_keyboard]: Activated profile: fast (電量 87%)
[INFO] [1792741534.971797625] [teleop_keyboard]: 目前 profile: normal (0.2 m/s, 0.6 rad/s), 電量 50%
[INFO] [1792741545.793041235] [teleop_keyboard]: 目前 profile: slow (0.1 m/s, 0.3 rad/s), 電量 20%
[WARN] [1792741600.010662495] [teleop_keyboard]: Battery low (0%): 'normal' not allowed, max is 'slow'. (電量 0%)
```
