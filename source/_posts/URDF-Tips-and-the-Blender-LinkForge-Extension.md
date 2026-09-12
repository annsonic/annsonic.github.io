---
title: URDF Tips and the Blender LinkForge Extension
date: 2026-09-01 23:19:07
tags: [blender, phobos, LinkForge]
categories: simulation 筆記
---

在 Blender 組合好 3D 物件了，
接下來要用 Blender 外掛套件 LinkForge 設定 URDF 了，
來學習 URDF 的概念和 LinkForge 的操作。

<!-- more -->

### 環境

- 作業系統 Ubuntu 24.04
- Blender [4.2](https://www.blender.org/download/lts/4-2/)
  - Python (Blender 自己建立的 Python 環境)
  - LinkForge [1.5.1](https://github.com/arounamounchili/linkforge/releases/tag/v1.5.1)
    - 從 1.5.0 版開始支援一個 link 可以由多個網格物件所組成
  - phobos [2.0.2](https://github.com/dfki-ric/phobos/releases/tag/2.0.2)


### URDF

格式介紹請見 [link](https://wiki.ros.org/urdf/XML/link) 和 [joint](https://wiki.ros.org/urdf/XML/joint)

- 用 link 和 joint 展開成為一個樹狀結構
- link：用來定義形狀、物理性質
  - dummy base link
    - 機器人的底盤中心通常會懸空有一點高度，如果直接把底盤當作 z = 0 的地面，底盤以下的零件就像是陷進地底
    - 解法：先設一個虛擬 link 固定在 z = 0，從這個虛擬 link 向上算一段距離，連接到機器人的實體底盤
  - visual origin
    - 通常在本段 link 網格的中心點
    - 建議保持是本地座標的 (0, 0, 0)
- joint：定義「父 Link (上一段)」到「子 Link (下一段)」原點的相對位置與角度。
  - origin 通常在上一段 link 末端
  - 當旋轉軸不在 link 中心線上時，直接調整 Joint 的 origin 的 XYZ 偏移量
    - 例如門軸通常裝在門的邊緣，不在門的正中心，調整讓 3D 門板物件的 origin 位於門板邊緣
- 相對座標系
  - 前一個 joint 為原點，計算相對座標
  - 子 link 的原點與座標軸，完全跟隨連接它的 joint
- joint 和 link 各自有原點和 xyz 座標軸
  - 遇到轉折處，是改變 joint 的旋轉角度 (rpy)，來改變下一段 link 的方向
  - 盡量統一一個方向的旋轉軸，例如都是以 z 軸作為 joint 的旋轉軸，方便計算


### 跟著 LinkForge 的教學製作 URDF

LinkForge 的官方文件有一篇 GUI 入門[教學](https://linkforge.readthedocs.io/en/latest/tutorials/building_diff_drive.html)，這個例子很單純，一個 link 只有一個網格形狀，URDF link origin 和 URDF link visual origin 都在預設的局部原點，而 URDF joint origin 都在下一段 link 的(Blender object)網格原點。

#### 操作
補充一些細節：

- LinkForge GUI 面板沒有提供設定 link origin, link visual origin, link collision origin, joint origin 的地方
  - 在綁定給 link 之前，先將網格物件的 origin 設定好，它將成為 joint origin
    - 例如這個範例中，左輪的圓柱體 origin 在 (0, 0.175, 0) 座標
  - 綁定 link 之後，在 Blender 大綱可以看到新的階層
    - link
      - *_visual 名稱的物件
      - *_collision 名稱的物件
- 在 Blender 大綱點選 link 物件，在 Blender 右下角面板 Object data property 的 Empty → Display As 選 Arrows，會在 link origin 顯示局部座標軸
- LinkForge link collision 點選 Auto-Generate 之後，才能再選 type
- LinkForge joint axis 要看的是局部座標軸
  - 範例 left_wheel_joint 的旋轉軸要選 Y(這是全域的 Y)，我後來用 rviz 驗證實發現這是錯誤的
  - URDF 其實是看局部 (Local) 座標系的，所以 left_wheel_joint 應該選擇局部的 Z 軸做旋轉
- LinkForge Validate & Export 雖然勾選 export meshes，mesh format OBJ，但是此範例只有輸出 URDF 檔而已
  - 可能因為此範例是 URDF 本身看得懂的幾何圖形，不需要輸出成為網格

![畫好 3D 物件](01_assembly.png "3D meshes")
![建立 base_link](02_base_link.png "base_link")
![建立 left_wheel link](03_left_wheel.png "left_wheel")
![建立 right_wheel link](04_right_wheel.png "right_wheel")
![建立 left_wheel_joint](05_left_wheel_joint.png "left_wheel_joint")
![建立 right_wheel_joint](06_right_wheel_joint.png "right_wheel_joint")
![建立 lidar_link_joint](07_lidar_link_joint.png "lidar_link_joint")
![建立 sensor](08_sensor.png "set sensor attribute")
![匯出 URDF](09_export.png "export")

#### 用 Blender phobos 做驗證

如果不想要打包成為 ROS2 專案的話，可以簡單地用 Blender phobos 套件來檢查機器人關節的活動狀態。

開啟新的 Blender 視窗，在 Phobos 面板點擊 Import Robot Model，選取 URDF 檔。

在 Blender 大綱面板點選其中一個 joint，會看到一個類似螺絲釘的網格物件被選取，按下快捷鍵 R 和方向(x, y 或 z)，移動滑鼠，可以看到關節帶動 link 旋轉的效果。

  - 附圖是 left_wheel_joint 在 URDF 設定繞 Z 軸旋轉的結果
    - 這在 Blender phobos 會看到符合預期的螺絲釘方向（平行圓柱體的中軸線）
    - 只是在 Blender 檢視輪子旋轉效果要按下 R 和方向 y，不是 z，我也會感到腦袋錯亂

![用 phobos 讀取 URDF 檔](10_phobos.png "import by phobos")

