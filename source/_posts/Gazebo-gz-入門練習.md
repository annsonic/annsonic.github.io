---
title: Gazebo(gz) 入門練習
date: 2026-09-16 22:00:43
tags: Gazebo
categories: simulation 筆記
---

這一篇是照著官方教學走一遍，紀錄一些自己的小筆記。

<!-- more -->

### 環境

- 作業系統 Ubuntu 24.04
- ROS2 Kilted
- Gazebo Ionic
  - [官方文件的 ROS2 和 Gz 配對版本](https://gazebosim.org/docs/jetty/ros_installation/)
  - `sudo apt-get install ros-kilted-ros-gz`
  - 注意別安裝 Gazebo classic，因為新版 Gazebo (gz) 才是支援新版 Ubuntu 和 ROS2


### 操作

我是照著這兩篇教學做，

- [從零建立 SDF 檔](https://gazebosim.org/docs/latest/building_robot/)
- [模擬移動行為](https://gazebosim.org/docs/latest/moving_robot/)

類似 ROS2 官方教學的移動小烏龜範例，
不過我的目標是求大致了解 Gazebo 的特性即可，
所以沒有多花精神查找語法；
官方文件寫得很仔細，
只有在加入 Key Publisher 這一步讓我找不到按鈕。
以下是 Key Publisher 小筆記：

![視窗右上角的三個點按鈕，點擊後出現輸入框和下拉選單](keyboard_1.png)

![在輸入框進行關鍵字搜尋](keyboard_2.png)

![這是加入 Key Publisher 後的樣子](keyboard_3.png)

### Gezobo 的特點

- Gazebo 是獨立的軟體，它的資料格式和 ROS2 不同
  - 通常使用 ros_gz_sim 提供的 bridge，或是 ros2_control 的 gz_ros2_control 來作為兩者溝通的橋樑
  - ros_gz_sim 負責從 gazebo 端往 ROS2 端，發送感測器的模擬數據，不涉及控制
  - gz_ros2_control 讓 ros2_control 的程式可以控制 gazebo 世界的機器人，這樣模擬和真實機器可以共用一套控制器程式
- Gazebo 是打造虛擬世界
  - 除了機器人模型，還需要有地景等等互動物體的物理模型，進行物理特性運算
  - 相對的，ROS2 Rviz 是數據可視化工具，例如：機器人本體狀態，感測器數據視覺化：點雲、軌跡、路徑規劃結果
  - 通常會是物理描述 SDF 檔搭配機器人關節定義 xacro 檔
  - 官方提供的 SDF 檔倉庫
    - [Fuel](https://app.gazebosim.org/dashboard)
    - [github](https://github.com/gazebosim/gz-sim/tree/main/examples/worlds)
- Gazebo plugin 分成四大類型
  - System Plugin，以下列出這次學習遇到的
    - gz-sim-physics-system，(必備)計算重力、摩擦力、碰撞...
    - gz-sim-user-commands-system (必備)例如用滑鼠拖曳機器人
    - gz-sim-scene-broadcaster-system (必備)更新 3D 畫面
    - gz-sim-diff-drive-system (依機器人而變)接收速度指令，轉動輪子
    - gz-sim-triggered-publisher-system (依機器人而變)設定觸發事件和發送觸發信號
  - Sensor Plugin
  - GUI Plugin
  - Visual Plugin
- Gazebo 有自己的主題與訊息機制 (Topics and Messages)
  - 教學中訂閱的 cmd_vel 主題，這個名稱 cmd_vel 是可以自由命名的
    - 範例中機器人叫 vehicle_blue，若不宣告 plugin 的 topic 標籤，預設的 topic 名稱會是 `/model/vehicle_blue/cmd_vel`
  - 似乎藉由抄 [github](https://github.com/gazebosim/gz-sim/tree/main/examples/worlds) 範例來學習
    - 各種機器人與外掛的組合
    - 外掛提供哪些參數
- 播放鍵
  - 代表開啟物理引擎的時間推進（Unpause Physics），讓重力、摩擦力、關節力矩開始隨時間進行數值積分（Numerical Integration）運算
  - 播放的不是預先錄製好的動畫，可以用滑鼠在 Gazebo 畫面中強行拉扯或推動機器人
  - 可以暫停，進行除錯與逐幀分析（Step-by-Step）
