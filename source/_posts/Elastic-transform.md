---
title: Elastic transform
date: 2022-07-09 15:01:51
tags: Interested Paper
---

## 觀點與事實
Elastic transform 對於手寫文字和醫學影像是很有用的增量技巧，
2003年論文[1]首度提出時應用於MNIST資料集，
簡單的CNN模型驗證10,000張影像達到分類準確率99.6%，
2015年的Unet[2]時應用於細胞的影像切割，
Unet模型驗證ISBI cell tracking challenge的PhC-U373資料集達到平均IoU為0.92。

<!-- more -->

## 背景簡介
隨機地移動像素造成形變，又結合線性轉換來增加變化：
(1)
線性轉換使用 Affine transformation，
它涵蓋 translation 位移、rotation 旋轉、scaling 放大縮小（包含鏡射）、shear 推移這些轉換，
線性轉換的特性是會保持兩點之間的比例，
所以原先的中心點仍然是中心點。
可以參考 [3][4]。
(2)
像素的移動量是隨機決定，
移動量再經過捲積來增加相鄰像素彼此空間上的相關性，
隨機移動的像素在畫面上看起來像雜訊，
因此需要降低隨機雜訊的平滑化濾波器，
在此捲積 kernel 採 Gaussian filter[5]。

## 方法與實驗結果
我讀的是 albumentations 的程式碼[6]。

它先進行 Affine transformation，
選定的座標點是圖片左上角、左下角和右下角，
距離邊界 1/6 邊長的3個點，
所以變數 `alpha_affine` 值應該要小於圖片尺寸的 1/6，
超過的話影像會發生鏡射。
![reflection](affine.png "Reflection by affine")

移動像素的部份，
移動量初始時值域為 [-1, 1]，
與 Gaussian filter 做捲積，
如果啟用變數 `approximate` 的話，
捲積的 kernel 大小固定為 17*17，
套用 OpenCV 的 `GaussianBlur` 函式，
計算速度快，
反之則計算 kernel 大小，
套用 scipy 的 `gaussian_filter` 函式，
kernel 大小 w 的計算公式
`w = 2 * int(truncate * sigma + 0.5) + 1`，
truncate 預設為 4。

我們可以調整變數 `sigma`，
即分佈的標準差，
若標準差小（例如sigma = 0.01），
捲積後位移向量仍然呈現隨機狀，
所以形變的影像彷彿加上很多雜訊，
看起來很粗糙；
若標準差適當（例如sigma = 4），
捲積後相鄰的位移向量會呈現方向上的漸變，
這樣可以得到彈性形變的效果，
若標準差太大（例如sigma = 16），
位移向量的變化變得平均，
彈性形變的扭曲效果便不明顯。
又，因為高斯分佈的峰值會隨標準差變大而下降，
需要搭配倍率來增幅，
倍率變數 `alpha`。 

![Small sigma](1.png "Elastic without affine, with sigma = 0.01 and alpha = 5, 34")
![Small sigma 2](2.png "Elastic without affine, with sigma = 1 and alpha = 34")
![Medium sigma](3.png "Elastic without affine, with sigma = 4 and alpha = 34")
![Large sigma](4.png "Elastic without affine, with sigma = 16 and alpha = 34")


## 程式碼
```
    import numpy as np
    import random
    import cv2
    import matplotlib.pyplot as plt


    # Magic numbers
    alpha_affine = 112 // 6 # Unit: pixels
    sigma = 4 # Unit: pixels
    alpha = 34
    border_mode = cv2.BORDER_REFLECT_101

    # Read the source image
    src = cv2.imread('6.png')
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

    # Select 3 points (array pts1) for transformation
    height, width = src.shape[:2]
    center_square = np.float32((height, width)) // 2
    square_size = min((height, width)) // 3
    pts1 = np.float32(
            [
                center_square + square_size,
                [center_square[0] + square_size, center_square[1] - square_size],
                center_square - square_size,
            ]
        )
    # Visualize and save image
    src_pts1 = src.copy()
    for i,pt in enumerate(pts1):
        cy, cx = int(pt[0]), int(pt[1])
        cv2.circle(src_pts1, (cx,cy), radius=1, color=colors[i], thickness=-1)
    cv2.imwrite('pts1.png', src_pts1)

    # Perturb 3 points to random positions
    random_state = np.random.RandomState(random.randint(0, (1 << 32) - 1))
    pts2 = pts1 + random_state.uniform(low=-alpha_affine, high=alpha_affine, size=pts1.shape).astype(
            np.float32)
    # Visualize and save image
    src_pts2 = src.copy()
    for i,pt in enumerate(pts2):
        cy, cx = int(pt[0]), int(pt[1])
        cv2.circle(src_pts2, (cx,cy), radius=1, color=colors[i], thickness=-1)
    cv2.imwrite('pts2.png', src_pts2)

    # Compute the affine transform matrix
    matrix = cv2.getAffineTransform(pts1, pts2)

    # Apply transformation
    dst_affine = cv2.warpAffine(src_pts2, matrix, (height,width))
    # Visualize and save image
    cv2.imwrite('affine.png', dst_affine)

    # Generate random displacement field in x-direction, range [-1, 1]
    dx = random_state.rand(height, width).astype(np.float32) * 2 - 1
    # Apply smoothing
    cv2.GaussianBlur(dx, (17, 17), sigma, dst=dx, borderType=border_mode)
    dx *= alpha
    # Duplicate random vector field in y-direction
    dy = dx
    # Position indices x, y
    x, y = np.meshgrid(np.arange(width), np.arange(height))
    # Purturbed position indices
    map_x = np.float32(x + dx)
    map_y = np.float32(y + dy)
    # Remap the pixels
    dst_mapped = cv2.remap(dst_affine, map_x, map_y, cv2.INTER_LINEAR)

    # Visualize the elastic transformation
    fig,ax = plt.subplots(1,1)
    ax.imshow(dst_mapped)
    # Prune the index array to reduce the arrow density
    skip=(slice(None,None,4),slice(None,None,4))
    ax.quiver(x[skip], y[skip], dx[skip], dy[skip], 
              color='orange', linewidths=(5,), headaxislength=10)
    ax.set_axis_off()
    plt.savefig('dst.png')
    plt.clf()

    # Initiate the array as the discrete Dirac delta function
    gaussian_kernel = np.zeros((17, 17))
    gaussian_kernel[8, 8] = 1
    # Apply smoothing
    cv2.GaussianBlur(gaussian_kernel, (17, 17), sigma, dst=gaussian_kernel, borderType=border_mode)
    gaussian_kernel = gaussian_kernel / gaussian_kernel.sum()
    # Visualize the kernel and save image
    plt.imshow(gaussian_kernel, cmap=plt.get_cmap('jet'), interpolation='nearest')
    plt.colorbar()
    plt.savefig('kernel.png')
```

## 參考資料
[1] Simard, Steinkraus and Platt, "Best Practices for Convolutional Neural Networks applied to Visual Document Analysis", in Proc. of the International Conference on Document Analysis and Recognition, 2003.
[2] Ronneberger, Olaf et al. "U-Net: Convolutional Networks for Biomedical Image Segmentation." MICCAI (2015).
[3] Affine transform 矩陣 [Wiki](https://en.wikipedia.org/wiki/Affine_transformation)
[4] Affine Transformation 三點轉換 [解釋](https://theailearner.com/tag/cv2-warpaffine/)
[5] Gaussian filter [解釋](https://medium.com/@bob800530/python-gaussian-filter-%E6%A6%82%E5%BF%B5%E8%88%87%E5%AF%A6%E4%BD%9C-676aac52ea17)
[6] albumentations 的[程式碼](https://albumentations.ai/docs/api_reference/augmentations/geometric/transforms/#albumentations.augmentations.geometric.transforms.ElasticTransform)