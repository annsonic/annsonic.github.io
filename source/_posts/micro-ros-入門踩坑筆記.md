---
title: micro-ros 入門踩坑筆記
date: 2026-06-13 15:59:42
tags:
categories: micro-ros 筆記
---
## 環境
- 作業系統 Ubuntu 24.04
- VS Code
- ESP32 (WROOM) 開發板
- micro_ros_platformio Jazzy
- micro-ROS-Agent Jazzy docker image
- ROS2 kilted

<!-- more -->

## micro_ros_setup kilted 版
- 不能被 ROS2 kilted 版本編譯
    
      雖然可以正常 ros2 run micro_ros_setup create_firmware_ws.sh，
    
      但是執行 ros2 run micro_ros_setup build_firmware.sh 總是有問題，
    
      google 搜尋錯誤訊息
      
      ```
        undefined reference to `rosidl_typesupport_microxrcedds_c__get_message_type_support_handle__service_msgs__msg__ServiceEventInfo'
      ```
    
      看到當時 micro-ROS Kilted 的 CI 2026-05-16 Run #2084 也是發生同樣的錯誤，
      
      AI 說 因為 ROS2 Kilted 引入了新的服務事件訊息機制（Service Event Info），
      
      而 micro-ROS 的資料型態支援（typesupport）在 Kilted 分支上尚未完全同步或編譯失敗。
    
      看來 micro_ros_setup kilted 仍不穩定啊；
      
      如果要改用其他版本，也需要 ROS2 安裝同樣的版本，
      
      只好放棄使用了。

## micro_ros_platformio 
- PlatformIO 和 Conda 環境的 Python 不相容

      在安裝 PlatformIO 之前，我的主機安裝過 Miniconda 虛擬環境，
    
      系統預設的 Python 路徑是指向 Miniconda 內的，
    
      而 PlatformIO 在編譯 micro-ROS 程式時，
    
      會建立並依賴一個名為 penv 的內部虛擬環境來執行 Python 程式，
    
      若 Ubuntu 系統預設用 Miniconda 的 Python 的話會導致 PlatformIO 找不到應有的 python 套件。

- VS Code 每次開啟後，又重新安裝 PlatformIO extension

      解決方式：編輯 VS Code User setting JSON 檔案 ($HOME/.config/Code/User/settings.json)
    
    ```json
      {
        "platformio-ide.coreDir": "$HOME/.platformio",
        "platformio-ide.customPATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
      }
    ```

- CMake 找不到 rmw 套件的設定檔（rmwConfig.cmake 或 rmw-config.cmake）

      解決方式： 使用 micro-ros-platformio Jazzy 版本
      
      ```
        [env:esp32dev]
        platform = espressif32
        board = esp32dev
        framework = arduino
        board_microros_transport = serial
        monitor_speed = 115200
        lib_deps = https://github.com/micro-ROS/micro_ros_platformio
        board_microros_distro = jazzy
      ```
      
      只需要搭配 micro-ROS-Agent Jazzy 版本即可正常連線，
      
      主機端的 ROS2 即使是 Kilted 版本也能溝通，
      
      但要注意如果使用太複雜或新版的自訂訊息，
      
      不同版本間可能會有相容性問題。

- 虛擬開發板

      我想過，能否確認軟體套件(ROS2, micro-ros-aget, micro-ros)版本都可運作後，
    
      再花錢買 ESP32 開發板，
    
      但是 AI 教我的虛擬開發板方法都沒有成功，
    
      所以還是買了開發板，我也多慮了，硬體上沒有問題。

