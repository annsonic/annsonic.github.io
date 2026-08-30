---
title: blender-編輯 3D 物件常用操作
date: 2026-08-19 22:21:19
tags: blender
categories: simulation 筆記
---


Blender 外掛套件 phobos 或是 linkforge 都能夠將 3D 物件設定成為 URDF 的 link、設定 joint、 collision 和匯出 URDF 檔，
不過前提是 3D 物件已經組合好，
所以我需要學習一些入門級的 blender 操作。
<!-- more -->

### 環境

- 作業系統 Ubuntu 24.04
- Blender [4.2](https://www.blender.org/download/lts/4-2/)
  - Python (Blender 自己建立的 Python 環境)

### 操作

以下是我在 Youtube 找到的教學片段，他們都是有在畫面中標注滑鼠按鍵和快捷鍵，幫助初學者照做練習的，感謝這些創作者的教學！

#### 切換視角、切換模式

[youtube](https://www.youtube.com/watch?v=H-UTd09M6vM)

- 因為我的筆電沒有數字小鍵盤，我是點擊工作區右上角的導航器來切換視角
  - 紅色 X 軸，導航器標示 X 端為正向
  - 綠色 Y 軸，導航器標示 Y 端為正向
  - 藍色 Z 軸，向上為正向

  ![navigation](01_viewport.png "the navigation tool")

- 物件模式和編輯模式
  - 我粗淺理解是編輯模式可以改變物件的點線面，物件模式可以改變物件的平移、旋轉、縮放和原點位置
  - 移動物件要限定三軸方向移動才準確（快捷鍵 `G`，然後再按鍵 X、Y 或 Z）
  - `按鈕 N` 叫出來的 Item transform 面板和螢幕右側 object properties 的 transform 是一樣的功能，都是輸入數字來做微調位置、角度、尺寸

  ![transform](02_transform.png "transform panels")

#### 插入 STL 檔案
- Menu ‣ File ‣ Import ‣ Stl (.stl)
  - 比例設為千分之一(亦即單位為 meter)，穿出螢幕向人的方向設為 X 軸，往上的方向設為 Z 軸。

  ![STL](03_import_stl.png "import STL for URDF")

#### 建立網格物件

[youtube](https://www.youtube.com/watch?v=Hc0Iu-jpIFU)

- 快捷鍵 `shift 鍵加上 A 鍵`
- 要注意畫面左下角的「Add ...」 面板
  - 只有在物件剛出生時才會出現，控制物件的形體結構，點擊畫面空白處便關閉此面板，物件的形體結構便固定了
  - object properties 的 transform 面板不能改變物件的形體結構

    ![add](04_add_mesh.png "add a new mesh")

#### 選取

[youtube](https://www.youtube.com/watch?v=zkupB5S3sUQ)

- 一邊壓著 shift 鍵、一邊用滑鼠左鍵點選，最後被選取的物件的外框線是銘黃色
- 例如選取 STL 物件的螺絲孔，在編輯模式點選「Edit Mode」右側的圖示「Edge」 後，再進行矩形框選
  - 如圖，因為是三角形網格，所以不能套用 Edge Loops 的選擇功能

  ![selection](05_edge_selection.png "select edge")
- 如何快速隱藏其他物件？
  
  [youtube](https://www.youtube.com/watch?v=vIV-BOLeU70)

  - 選取一個物件，按下快捷鍵 `shift + H`，會將其他未被選取的物件隱藏；要恢復顯示的話，按下快捷鍵 `alt + H`

#### 設定 3D cursor 位置

[youtube](https://www.youtube.com/watch?v=INoQczIMFkQ)
- 畫面上的紅白虛線十字，初始位置在世界座標的原點
- 它不是世界座標的原點
  - 概念上類似木匠的圖釘，用圖釘標示出要放置新物件的位置，或是搬移物件的目的地
  - 影片的 6:37 ~ 8:06 時間示範了用 3D cursor 輔助定位做的機械手臂
- 改變 3D cursor 位置：1.在編輯模式做選取，2. 按下 `shift + S`，3. 選單選擇「cursor to selected」

  ![3D cursor](06_cursor_to_selected.png "move the 3D cursor")

#### 設定物件的原點

[youtube](https://www.youtube.com/watch?v=h5DtfL3mnCM)

- 我粗淺理解 Blender 的物件原點相當於 pivot，旋轉軸
  - 前面介紹的平移、旋轉、縮放都是相對於物件原點來做計算
  - Blender 物件的橘色小圓點來表示物件的原點
  - 對於可以旋轉的物件，我想像 Blender 物件原點等於 URDF joint origin 的視覺化
- 改變原點位置需要三步驟：1.在編輯模式做選取，2. `shift + S` 選單選擇「cursor to selected」，3. 在物件模式，滑鼠右鍵選擇「set origin」的「origin to 3D cursor」
  - 在我的 mearm 機械手臂案例中，旋轉軸在零件的螺絲孔中心點

    ![origin](07_origin_to_cursor.png "move the roigin")

#### 父子化

[youtube](https://www.youtube.com/watch?v=5oclP4hQndc)

- 子元件會跟著父元件做一樣的平移、旋轉、縮放轉換
  - 影片的 3:02 ~ 3:56 時間示範了用父子化做的機械手臂
- 步驟：1. `shift + 滑鼠左鍵`選取子元件，2. `shift + 滑鼠左鍵`選取父元件，3. 按下快捷鍵 `ctrl + P`，4. 選擇 keep transform

  ![parent](08_parenting.png "create the parent relationship")

- 如何取消？
  - 選取所有父子化後的元件，按下快捷鍵 `alt + P`

#### 套用所有轉換

[youtube](https://www.youtube.com/watch?v=OpMSpbBiWg4)

- 如果每次變動物件都自動 Apply Transform 會頻繁修改網格的頂點數據
  - 這對大型模型來說計算成本很高
- 如果物件進行了旋轉和改變 origin 位置等等動作，但沒有執行 Apply Transform，會造成以下影響
  - 物件的旋轉、位置、縮放資訊仍然存在於 Transform Properties 中
  - 導致視覺位置和實際數據不同步
  - 當匯出 URDF 和 STL、OBJ 時，匯出的數據跟 Blender 所見不同，亦即組合好的零件位置錯位了
- 如何檢查？
  - 選中物件 → 按 `N` → 看 Item 標籤的 Transform 區域
    - 做過 Apply Transform 的話，Scale (1.0, 1.0, 1.0), Rotation (0, 0, 0)
- 套用轉換
  - 步驟：選取物件，按下快捷鍵 `ctrl + A`，選擇 all transforms
- 如何取消？
  - 在關閉檔案之前，可以利用歷史 undo 復原
- 沒有做過 apply transform，想歸零
  
  [youtube](https://www.youtube.com/watch?v=4DXo-UElW38)

#### 測量長度

[youtube](https://www.youtube.com/watch?v=tlgu1dvHnDI)

- 單一邊線的長度
  - 步驟：點選「Edit Mode」右側的圖示「Edge」 ，點選目標邊線，畫面右上角「Overlay」選取「Measurement」「Edge Length」
