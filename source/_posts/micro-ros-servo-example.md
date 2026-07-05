---
title: micro-ros-servo-example
date: 2026-07-01 21:28:40
tags: micro-ros-platformio, servo, pca9685
categories: micro-ros 筆記
---

將 ESP32 開發板接上步進馬達驅動板 PCA9685 和 SG90 馬達，
配上改造自 [serial publisher範例](https://annsonic.github.io/2026/06/14/micro-ros-platformio-example-serial-publisher/) 的程式做控制練習。
<!-- more -->

### 環境

- 作業系統 Ubuntu 24.04
- VS Code
- ESP32 (WROOM) 開發板
- PCA9685 步進馬達驅動板
- SG90 馬達
- ICR18650-26F 鋰電池
- micro_ros_platformio Jazzy
- Micro-ROS-Agent Jazzy docker image
- ROS2 Kilted

### 硬體線路
參照[專案](https://github.com/ODraidrya/OmArm-Zero)

- PCA9685 SDA 接上 ESP32 GPIO21
- PCA9685 SCL 接上 ESP32 GPIO 22
- PCA9685 電源接上 2 顆串連的 ICR18650-26F 鋰電池


### 程式與操作

請見 [github 專案](https://github.com/annsonic/ros2-practice/tree/micro-ros-servo)

### 程式筆記

#### 初始化的步驟
原來 Micro-ROS 需要在設定 transport 完成和 Micro-ROS-Agent 的連線，再初始化硬體。


[官方](https://micro.vulcanexus.org/docs/tutorials/programming_rcl_rclc/micro-ROS/ )建議的標準邏輯是使用一個 while 迴圈不斷去 ping（握手）Agent，

直到成功才建立 ROS 2 實體。

1. WAITING_AGENT（等待 Agent 握手成功）
2. AGENT_AVAILABLE（連線成功，開始初始化 ROS 2 節點）
3. 主程式運作 / 硬體週邊啟動

我原先的初始化流程是

```
Serial.begin(115200);
delay(1000);
Wire.begin();           
pwm.begin();            
pwm.setPWMFreq(...);    
setServoAngle(...); 
delay(500);

set_microros_serial_transports(Serial); // 這裡才告訴 micro-ROS 連線方式
delay(2000);
RCCHECK(rclc_support_init(...));       // ✗ 無法連線 agent
```

程式運作會在 rclc_support_init() 這一步驟失敗。

- 執行 set_microros_serial_transports(Serial) 
  - Micro-ROS 才會正式接管 Serial，並將其格式格式化為 Micro XRCE-DDS 協定的二進位（Binary）封包。
  - 會與 Serial.println() 互相干擾

#### SG90 servo 馬達

1. 不能直接讀取馬達當前的「角度」

  - 硬體只有三條線（VCC、GND、訊號線）。訊號線只負責接收微處理器傳過去的 PWM 指令，不可回傳信號。
  - PCA9685 是一款「PWM 驅動晶片」，紀錄最後一次設定給該頻道的 PWM 訊號數值。

    [PCA9685 官方文件](https://learn.adafruit.com/16-channel-pwm-servo-driver?view=all)

    重要的函數：

    - setPWMFreq(freq)
      - SG90 servo 的規格是 50Hz
    - setPWM(channel, on, off)
      - 一個週期的波型固定由 4096 的資料點組成，函數設定高電位(on)起始在第幾個資料點、低電位(off)起始在第幾個資料點
      - [參考 dronebotworkshop 的網誌 PCA9685 Timing](https://dronebotworkshop.com/servoguide/)

2. 校正

  - 讓馬達的機械原點和脈衝值原點對齊
  - 我以為 PWM 波型控制的是「相對的」馬達轉動量，實測才發現原來是「絕對的」轉動量
    - 亦即機構初始位置並不是馬達的 0 度位置
  - 實際轉動範圍與數學計算有偏差

    SG90 的理論工作脈寬範圍通常是 1ms（0度）到 2ms（180度）。
    
    ```
    50Hz or 1/50 = 20ms (0.02 seconds)
    1ms pulse (-90 degrees): duty = 1*50 = 50 (or 1/20 = 5% DutyCycle)
    0.05 * 4096 = 205 個資料點
    ```

    理論上設定 PWM 脈衝寬度 205 時，馬達會轉到正左方，但實際卻沒有剛好到位，所以需要調整 setPWM(channel, on, off) 的設定值囉。

    這位大神 DIY 了量測角度的小工具[網誌](https://www.hackster.io/jeremy-lindsay/calibrating-my-servos-fa27ce)

  - 我給 SG90 馬達裝上旋槳，校正完畢之後，拆下旋槳、將馬達裝到機構中，結果剛才校正得到的範圍漂移了
    - 可能在拆裝過程中轉動了馬達的軸心桿，我之後都在完整機構上做校正了
