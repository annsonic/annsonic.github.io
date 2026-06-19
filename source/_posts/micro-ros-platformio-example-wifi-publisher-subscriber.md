---
title: micro-ros-platformio-example-wifi-publisher-subscriber
date: 2026-06-19 18:57:51
tags: micro-ros-platformio
categories: micro-ros 筆記
---
micro-ros-platformio 在 github 上提供了兩個範例，

本篇是取材自[micro-ros_publisher/subscriber 範例](https://github.com/micro-ROS/micro_ros_platformio/tree/main/examples/ethernet_pubsub) 進行學習。

<!-- more -->

## 環境
- 作業系統 Ubuntu 24.04
- VS Code
- ESP32 (WROOM) 開發板
- micro_ros_platformio Jazzy
- micro-ROS-Agent Jazzy docker image
- ROS2 Kilted
- 家裡的 WiFi

#### 程式與操作
請見 [github 專案](https://github.com/annsonic/ros2-practice/tree/micro-ros)

## 程式筆記

#### 什麼情境需要用網路通訊？
- 較高的傳輸頻寬（Wi-Fi 或乙太網路）
  - 高頻 sensor / 高階馬達編碼器 → ESP32 → ROS2 上位機
  - ROS2 上位機 → ESP32 → 高階馬達編碼器（取得絕對角度和圈數、同步多軸控制、校正）
- 多機通訊
  - 機器人身上有多個微控制器需要同時跟 ROS 2 主機溝通

#### PlatformIO 的系統環境變數
當我決定要將程式公開在 github 專案時，想說將 WiFi 帳密寫在系統環境變數（記載在 .env 檔），搭配 PlatformIO 的 build_flags 設定，沒想到一直編譯失敗，連 AI 也訂正不了。

最後是仿效了這位前輩的[作法](https://community.platformio.org/t/inserting-and-using-environmental-variables-as-strings/14238)，
將帳密宣告在 include/secrets.h，
並且設定 .gitignore 排除該檔。

#### 五狀態連線狀態機

- 順序
  
  kConnectingWiFi → kWaitingForAgent → kCreatingEntities → kConnected ⇄ kDisconnected

  - kConnectingWiFi 連接家裡的 WiFi 分享器
  - kWaitingForAgent 尋找已經啟動的 micro-ROS Agent
  - kCreatingEntities 建立 ROS2 的節點（Node）、發布者（Publisher）、訂閱者（Subscriber）與執行器（Executor）
    - 如果其中一個節點建立失敗（例如記憶體不足），會主動呼叫 DestroyEntities() 清理資源，並退回前一個狀態重新等待。
  - kConnected 正常運作狀態。處理資料收發。
    - 偵測不到 WiFi 分享器就斷線
  - kDisconnected 處理連線中斷後的善後工作
    - 資源回收
    - 根據「WiFi 斷線」還是「Agent 斷線」來退回對應的狀態

- 最初版本程式的 WiFi 連線一直在重新連線
  - 解法：每 3 秒才 ping 一次，以及失敗消抖機制（連續 3 次 ping 失敗才判定斷線），避免瞬間網路抖動導致不必要重連。

#### 節省記憶體的措施
- ESP32 Arduino 預設關閉 C++ exceptions
  - 此時程式不可以有 try...catch 或 throw 
  - 我原先寫的程式 `std::stoi(AGENT_PORT)` 在無效輸入時會拋出例外導致程式崩潰，AI 建議我改用 `改用 atoi(AGENT_PORT)` 或 `strtoul()`
  - 啟用例外處理會增加編譯後的二進位檔大小，並在執行時佔用更多 RAM
