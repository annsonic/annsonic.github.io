---
title: blender-phobos-installation
date: 2026-07-22 23:27:17
tags: blender-plugin, phobos
categories: simulation 筆記
---

為了在 3D 空間中調整 URDF 檔的 link 和 joint 位置，
以及考慮到免費的軟體方案，
我選擇採用 blender 軟體和它的 phobos 外掛。
<!-- more -->

### 環境

- 作業系統 Ubuntu 24.04
- Blender [4.2](https://www.blender.org/download/lts/4-2/)
  - Python (Blender 自己建立的 Python 環境)
- phobos [2.0.2](https://github.com/dfki-ric/phobos/releases/tag/2.0.2)

### 安裝筆記

#### Blender

1. 從官網下載 tar.xz，解壓縮，將資料夾搬移到 /opt 目錄下。

  ```
  sudo mv ~/Downloads/blender-4.2.23-linux-x64/ /opt/blender-4.2.23-linux-x64/
  ```

2. 建立連結，之後就可以從終端機下指令 `blender` 來啟動 Blender 程式。

  ```
  sudo ln -s /opt/blender-4.2.23-linux-x64/blender /usr/local/bin/blender
  ```

#### phobos 外掛

1. 從 github releases 下載 zip 檔

2. 把 phobos 的程式加入到 Blender 的 Add-on 裡，從這一步驟開始就是一連串的除錯過程。

  我做了 Blender 的 Edit -> Preferences -> Add-ons -> Install from Disk. -> 選擇 phobos.zip

  但是從 Blender 的終端機訊息看到，Blender 讀取到了空的 phobos 資料夾，

  原因出在 ZIP 解開後形成了雙層資料夾結構，導致 Blender 無法正確找到 __init__.py。
  
  預期結構應為：


  ```
  ~/.config/blender/4.2/scripts/addons/phobos
   ├── __init__.py
   ├── io/
   ├── model/
   ├── utils/
  ...等其他資料夾
  install_requirements.py
  ```

  解決方法：
  
  將內層 phobos/ 資料夾中的所有檔案直接移至外層的 ~/.config/blender/4.2/scripts/addons/phobos/。
  
  完成後，Blender 的 Add-ons 清單即可正常顯示 Phobos。

2. Blender 的 Edit -> Preferences -> Add-ons 清單中的 phobos 不能被啟用，

  點擊清單中的核取方塊，

  得到錯誤訊息

  ```
  Phobos:All Phobos requirements have been installed.
  Please restart Blender to activate the Phobos add-on!
  Exception in module register(): ~/.config/blender/4.2/scripts/addons/phobos/__init__.py
  Traceback (most recent call last):
    File "~/.config/blender/4.2/scripts/modules/numpy/_core/__init__.py", line 23, in <module>
    from . import multiarray
    File "~/.config/blender/4.2/scripts/modules/numpy/_core/multiarray.py", line 10, in <module>
      from . import overrides
    File "~/.config/blender/4.2/scripts/modules/numpy/_core/overrides.py", line 7, in <module>
      from numpy._core._multiarray_umath import (
  ModuleNotFoundError: No module named 'numpy._core._multiarray_umath'
  ```
  
  由於 Phobos 自動安裝的 NumPy(舊版) 與 Blender 內建環境的 NumPy(新版) 版本衝突所致。

  我的個性是喜歡更新套件版本，不是配合用舊版本，
  
  所以先刪除 numpy 和 scipy 的資料夾，再重新安裝

  ```
  rm -r ~/.config/blender/4.2/scripts/modules/numpy

  rm -r ~/.config/blender/4.2/scripts/modules/scipy

  /opt/blender-4.2.23-linux-x64/4.2/python/bin/python3.11 ~/.config/blender/4.2/scripts/addons/phobos/install_requirements.py
  ```

3. 修復 install_requirements.py 語法錯誤

  執行上一步驟時，跳出 importlib 相關錯誤：

  ```
  Traceback (most recent call last):
    File "~/.config/blender/4.2/scripts/addons/phobos/install_requirements.py", line 85, in   check_requirements
      if importlib.util.find_spec(import_name) is None:
         ^^^^^^^^^^^^^^
  AttributeError: module 'importlib' has no attribute 'util''
    File "~/.config/blender/4.2/scripts/addons/phobos/install_requirements.py", line 89, in   check_requirements
      if not issubclass(type(loader), importlib.machinery.SourceFileLoader)
                                      ^^^^^^^^^^^^^^^^^^^
  AttributeError: module 'importlib' has no attribute 'machinery'
  ```

  解決方法： 修改 ~/.config/blender/4.2/scripts/addons/phobos/install_requirements.py 內對應的程式碼：

  | 項目 | 舊程式 | 新程式 |
  | --- | --- | --- |
  | 1 | `import importlib` | `from importlib import util, machinery` |
  | 2 | `if importlib.util.find_spec(import_name) is None:` | `if util.find_spec(import_name) is None:` |
  | 3 | `if not issubclass(type(loader), importlib.machinery.SourceFileLoader):` | `if not issubclass(type(loader), machinery.SourceFileLoader):` |


  再一次執行安裝

  ```
  /opt/blender-4.2.23-linux-x64/4.2/python/bin/python3.11 ~/.config/blender/4.2/scripts/addons/phobos/install_requirements.py
  ```

  等到終端機顯示安裝完成，開啟 Blender 的 Edit -> Preferences -> 核取啟用 Add-ons 清單中的 phobos，關閉 Blender

4. 驗證

  開啟 Blender，Blender 的畫布畫面中按 N 開啟側面板，在側面板會有一個名稱是 phobos 的標籤頁

完成！
