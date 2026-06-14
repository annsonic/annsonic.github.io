---
title: micro-ros-platformio example - serial publisher
date: 2026-06-14 17:48:05
tags: micro-ros-platformio
categories: micro-ros 筆記
---
micro-ros-platformio 在 github 上提供了兩個範例，
我先從這一個 [micro-ros_publisher 範例](https://github.com/micro-ROS/micro_ros_platformio/tree/main/examples/micro-ros_publisher) 入門學習。
<!-- more -->

## 環境
- 作業系統 Ubuntu 24.04
- VS Code
- ESP32 (WROOM) 開發板
- micro_ros_platformio Jazzy
- micro-ROS-Agent Jazzy docker image
- ROS2 Kilted

#### 開啟 micro-ros-agent 容器
```
docker run --rm -it \
  --net=host \
  --device=/dev/ttyUSB0:/dev/ttyUSB0 \
  microros/micro-ros-agent:jazzy \
  serial --dev /dev/ttyUSB0 -b 115200
```
device 參數請依照你的情況填寫，可以從 platformio Home 的 Devices 的 Serial 的 Port 清單得知要填的值。

我的情況是上傳韌體時會占用 serial port /dev/ttyUSB0，所以
上傳完成後再啟動 agent，避免同時搶 /dev/ttyUSB0。

## 測試

開發板 每 1 秒發布一次 std_msgs/msg/Int32 訊息到 topic micro_ros_platformio_node_publisher，

並讓數值遞增 (0,1,2,...)。

#### 在 micro-ros-agent 容器的終端機訊息

```
1781432157.822946] info     | SessionManager.hpp | establish_session        | session established    | client_key: 0x19A8F6A1, address: 0
[1781432157.885356] info     | ProxyClient.cpp    | create_participant       | participant created    | client_key: 0x19A8F6A1, participant_id: 0x000(1)
[1781432157.902801] info     | ProxyClient.cpp    | create_topic             | topic created          | client_key: 0x19A8F6A1, topic_id: 0x000(2), participant_id: 0x000(1)
[1781432157.912677] info     | ProxyClient.cpp    | create_publisher         | publisher created      | client_key: 0x19A8F6A1, publisher_id: 0x000(3), participant_id: 0x000(1)
[1781432157.924255] info     | ProxyClient.cpp    | create_datawriter        | datawriter created     | client_key: 0x19A8F6A1, datawriter_id: 0x000(5), publisher_id: 0x000(3)

```

#### 在 ROS 2 主機上看 topic：
```
ros2 topic list
```
預期看到 /micro_ros_platformio_node_publisher topic

```
ros2 topic echo /micro_ros_platformio_node_publisher
```
會看到類似
```
data: 64
---
data: 65
---
data: 66
---
```
這樣格式的訊息。

## 程式筆記

#### 每個 micro-ROS serial 通訊專案的固定句型
全域物件
```
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
```

固定的 setup() 開頭流程
```
void setup() {
  // Configure serial transport
  Serial.begin(115200);
  set_microros_serial_transports(Serial);
  delay(2000);

  allocator = rcl_get_default_allocator();

  //create init_options
  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));
```

setup() 流程再宣告 node。

setup() 流程最後是 `rclc_executor_init(&executor, &support.context, 1, &allocator)`
在此因為只有一個 timer 所以填入 1。

- 個數：只計算需要被「監聽」或「觸發」的元件（稱為 Handles），是「被動等待通知」的元件
  - Subscriber（訂閱者）
  - Timer（計時器）
  - Server（服務端）
  - Client（用戶端）


`rclc_executor_spin_some()` 被 `void loop()` 呼叫。

#### 錯誤處理
在 micro-ROS 中，大部分的函式（例如建立節點、建立發布者）執行完後，都會回傳一個狀態碼（型態為 rcl_ret_t）。如果成功，會回傳 RCL_RET_OK（數值為 0）；如果失敗（例如記憶體不足、連線中斷），則會回傳錯誤碼。

- `RCCHECK` 致命錯誤。
- `RCSOFTCHECK` 非致命錯誤

宣告巨集，

```
#define RCCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){error_loop();}}
#define RCSOFTCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){}}
```

可以避免 setup() 充斥著大量的 if-else 判斷式。

進入 `error_loop()` 無窮迴圈的話，就表示「初始化有嚴重錯誤」。
