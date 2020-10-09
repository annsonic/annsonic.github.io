---
title: 用RetinaNet計數血液細胞
date: 2020-10-09 21:56:20
tags:
  - Object detection
  - RetinaNet
categories: Project
---

未完
<!-- more -->

## 主題：

## 假設：

## 方法：

## 實驗限制：

## 結果:



## 溫故知新
1. image normalozation的mean和std設定值是否很重要？
   需要做image normalozation的原因跟做batch normalization的原因相似，
   batch normalization：將輸入資料調整為高斯分佈、降低Internal Covariate Shift問題，
   增進模型的學習效率

   > 註：Internal Covariate Shift 問題：
       We define Internal Covariate Shift as the change in the distribution of network activations due to the change in network parameters during training.
   > [引用自](https://machinelearning.wtf/terms/internal-covariate-shift/)
	
   image normalozation的常見算法是對training dataset的每個channel獨立計算mean和variance，
   用BN取代image normalozation不是個有效率的作法，
   因為BN的mean和variance是模型逐次學習出來的。

   我使用的RetinaNet，
   其image normalozation的mean和std設定值是由COCO資料集算出來的，
   我比較用Blood Cells資料集算出來的mean和std，
   雖然圖片的色調明暗差異大，
   但模型準確度是差異不大，
   見下圖，是重複實驗3次、取平均的結果，
   虛線是使用COCO資料集圖片的mean、var，
   實線是使用Blood Cells資料集的mean、var，
   只在血小板（小物件）的偵測表現上有較明顯的差異。
   ![Compare different image mean and std](compare.png "avg mAP")
2. 為何凍結BN層參數？
   我使用的RetinaNet，
   其pretrained Resnet的BN層參數是凍結的，
   作者說雖然因為pretrained資料集是Imagenet，
   與我們的dataset統計分佈有差異，
   可是訓練物件偵測模型的batch size很小(例如8)，
   又，有人實驗過，
   想藉由finetuning來學習新的BN，
   但模型表現反而像從頭訓練那般，
   難怪作者會選擇凍結Resnet的BN層參數。
   [參考討論](https://stackoverflow.com/questions/63016740/why-its-necessary-to-frozen-all-inner-state-of-a-batch-normalization-layer-when)

3.輸入圖檔的尺寸大小？
