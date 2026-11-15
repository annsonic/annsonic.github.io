---
title: MoveIt Getting Started
date: 2026-11-14 13:58:20
tags: [MoveIt, RViz, Gazebo]
categories: simulation 筆記
---

安裝環境和執行現成的 MoveIt 範例程式。

<!-- more -->

### 環境

- 作業系統 Ubuntu 24.04
- ROS2 Kilted
- Gazebo Ionic
- Universal Robots 驅動與模擬套件
    ```
    $ sudo apt install ros-kilted-moveit
    $ sudo apt install ros-kilted-ur
    $ sudo apt install ros-kilted-ur-simulation-gz
    ```

### 啟動

`$ ros2 launch ur_simulation_gz ur_sim_moveit.launch.py ur_type:=ur5e`


### 認識 RViz GUI

![MoveIt](gui.png "MoveIt with ur5e")

- planning group 
  - 是「一組要一起規劃的關節（或連桿）」
  - 定義在 MoveIt config 的 SRDF 裡。規劃器只會移動這些關節
  - 機械手臂常見分成兩個 planning group：手肘手腕一組、夾爪自己一組

- Goal State
  - `<random valid>`
    - 隨機產生一組「無碰撞（Collision-free）」且符合運動學的合法目標位置（Goal State）
  - Named States（具名姿態）
    - 定義在 SRDF 的 `<group_state>`，給姿態命名在 Python 控制時很實用
  - state 對應哪一隻手臂
    - 可以在 RViz 的左側 Displays 面板展開 MotionPlanning 樹狀圖查看對應的顏色
      - Planning Request：Query Start State 與 Query Goal State 核取方塊
      - 我的例子中，草綠色是初始狀態、橘色是目標狀態、紅色是發生了碰撞

- 互動標記（interactive marker）
  - 左鍵拖曳：旋轉視角
  - 右鍵：縮放
  - 一次只動一個軸：滑鼠在箭頭上會換符號、箭頭是沿單軸平移，滑鼠在圓環上是另一個符號、圓環是繞單軸旋轉
  - 在 Displays → MotionPlanning → Planning Request 裡有 Interactive Marker Size 設定

- workspace
  - 規劃路徑用的工作空間邊界(只會在此範圍內做計算)
  - 不是手臂實際可達範圍!!
  - 用來限制浮動或平面虛擬關節的取樣範圍
  - 在 RViz 的左側 Displays 面板展開 MotionPlanning 樹狀圖查看工作範圍
    - Planning Request：show workspace，會畫出海軍藍色方塊
    - 畫出工作範圍的缺點：海軍藍色方塊圖層會妨礙點選互動標記
  - 在 MotionPlanning 面板的 Context 分頁裡，有 Workspace 的 Center 和 Size 欄位，可以調整

- OMPL 是通用的取樣式規劃器，結果可能繞路、不平滑。需要換的情境：
  - 畫圖：直線／平滑路徑，用 Pilz Industrial Motion Planner
  - 想要軌跡更平滑或最佳化：CHOMP 或 STOMP
  - 只是自由空間移動、避障：OMPL 就夠用

- Joints 分頁直接調每個關節角度，最精準也最不會超出工作區

- Execute 執行的是「最近一次 Plan 產生的軌跡」，然後該軌跡失效，不能重複執行，需要重新 Plan

- Gazebo 按下暫停後 RViz 的手臂也不動
  - ros2_control 在 Gazebo 裡由模擬時鐘驅動，暫停後模擬時間不前進，controller 不會更新，RViz 看到的手臂狀態來自 /joint_states，也就跟著停住

### 手動進行規劃路徑

[Rviz 官方教學](https://docs.ros.org/en/kinetic/api/moveit_tutorials/html/doc/quickstart_in_rviz/quickstart_in_rviz_tutorial.html)

- 在 RViz 的 MotionPlanning 面板選 Planning 分頁
- 拖曳手臂末端的互動標記（interactive marker）到新位置
  - 不需要花時間用互動標記去指導機械手臂抓取物件，在 3D 空間中很難用肉眼看準位置，放置互動標記的位置難以精確
- 按 Plan，觀察規劃軌跡動畫
- 按 Execute，確認 Gazebo 裡的手臂也跟著動

### 確認 MoveIt 的 action

另開終端機執行：

`$ ros2 action list`

終端機印出
```
/execute_trajectory
/joint_trajectory_controller/follow_joint_trajectory
/move_action
/scaled_joint_trajectory_controller/follow_joint_trajectory
/sequence_move_group
```

- /execute_trajectory 為執行軌跡 action
- /move_action：MoveIt 的規劃 action
- /scaled_joint_trajectory_controller/follow_joint_trajectory：實際執行軌跡的 action

繼續執行

`$ ros2 control list_controllers`

終端機印出
```
scaled_joint_trajectory_controller ur_controllers/ScaledJointTrajectoryController  active
joint_state_broadcaster            joint_state_broadcaster/JointStateBroadcaster   active
```

- scaled_joint_trajectory_controller 負責執行軌跡

在 MoveIt 按一次 Execute，接著終端機執行

`$ ros2 topic echo /joint_states --once`

終端機印出

```
header:
  stamp:
    sec: 230
    nanosec: 506000000
  frame_id: base_link
name:
- elbow_joint
- shoulder_lift_joint
- shoulder_pan_joint
- wrist_1_joint
- wrist_2_joint
- wrist_3_joint
position:
- 3.061531835299185e-15
- -1.5699999999999965
- 6.847049869711555e-22
- -1.56999999999999
- -5.068582043810573e-15
- 1.4536457371886133e-21
velocity:
- -4.0657581468206416e-20
- -8.950368793553612e-14
- 1.3552527156068805e-20
- -9.422947448364805e-14
- -2.710505431213761e-20
- 0.0
effort:
- -0.017572432177420723
- -0.05044093661208997
- -1.6940658945086007e-18
- -0.0029038103866075985
- 0.0008923555566335767
- 9.510277373872623e-20
---
```

這是模擬時間（230秒）當下各個關節的狀態值
- name 是以字母做關節名稱的排序，不是動力鏈的順序
- position：關節角度（弧度）。
- velocity：關節角速度。log 中的值接近零，表示手臂靜止。
- effort：關節力矩，主要是重力補償等造成的小值。
