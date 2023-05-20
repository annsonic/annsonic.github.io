---
title: Decoupling Representation and Classifier for Long-Tailed Recognition
date: 2020-09-22 18:34:39
categories: Interested Paper
---

2020年發表於ICLR，
作者來自於Facebook AI，
有提供source code
https://github.com/facebookresearch/classifier-balancing
我讀這一篇是因為碰到長尾分佈下的分類問題，
試過給loss加權重、但沒幫助，
而這篇建議的re-sampling技巧我試過覺得有用，
在此紀錄一下自己從中學習到的。
<!-- more -->

## 觀點與事實
* 此文獻建議以2階段的取樣方式來處理長尾分佈下的分類問題
  ![method](0.png "2 stage learning")
* (第一階段)學習好的圖片特徵，
  以 instance-balanced sampling 方式採樣，
  一起訓練捲積層和分類器。
* (第二階段)學習分類，
  固定捲積層不動，
  以 class-balanced sampling 方式採樣、重新訓練分類器，
  或是 τ-normalized 將分類器的權重做正規化、τ是超參數，
  或是 Learnable weight scaling。
* 在ImageNet-LT資料集上得到的top-1準確度53.3%(SOTA)，
  Places-LT上得到top-1準確度37.9%
  iNaturalist上得到top-1準確度72.5%。

## 背景簡介
* 長尾分佈如下圖，
  現實中往往有稀有的類別，
  難以採集到均衡的資料
  ![long tailed](1.png "Imbalanced dataset")
* 當數據的分佈極不平衡時，
  會造成分類器學習到的是"數據的分佈機率"、偏好佔多數的種類。
* 資料平衡的可能方法:
    * Oversample the minority class.
    * Undersample the majority class.
    * Synthesize new minority classes.
  但是有過擬合、欠擬合的副作用。
  [1] [Oversampling and undersampling, Synthesizing new examples: SMOTE](https://www.svds.com/learning-imbalanced-classes/)
* 可以依類別給予不同的loss權重
  [1] [Adjusting class weights](https://www.svds.com/learning-imbalanced-classes/)
  
## 方法
* 取樣方式，比較重要的
  * Instance-balanced sampling
    每個資料點都一樣的機率被選中
  * Class-balanced sampling
    先公平地選擇類別，然後在該類別再公平地選擇資料點
  ![sampling](3.png "Sampling strategies")
* 第二階段的分類器訓練方式
  * Classifier Re-training (cRT)
    以 class-balanced sampling 方式採樣重新訓練分類器
  * τ-normalized
    將第一階段的分類器的權重做正規化，
	τ是超參數，作者經由cross validation做選擇
  * Learnable weight scaling (LWS)
    將正規化的係數也透過模型學習，
	但我不清楚作者用什麼模型來學習
  ![classifier type](4.png "Classifier strategies")

## 實驗結果節錄
  下圖是作者繪出分類器的權值L2範數對於各類資料的分佈，
  橫軸由左至右，是多數類別至少數類別，
  黑色虛線表示資料筆數，
  藍色線是normal training分類器的權值L2，
  可以看到稀有類別的權值比較小，
  影響其logit也小，
  softmax結果便會偏向佔多數的類別勝出。
  
  而綠色線是cRT得到分類器的權值L2，
  它犧牲多數類別的權值，
  稀有類別的權值比較高。
  
  τ-norm(黃線) 和 LWS(棕線)表現差不多，
  他們對權重的平衡比較折衷。
  
  ![long tailed issue](2.png "Imbalanced dataset issue")
* 與前作的分類準確度比較
  ![imagenet-lt](5.png "imagenet-lt exp.")
  ![iNaturalist](6.png "iNaturalist exp.")

## 個人感想
* 容易搭配，
  因為只須改變sampling方式和調整fully connect layer，
  可以與不同的backbone架構搭配。
* Class-balanced sampling是最簡便的，
  只是應該會影響batch size的選擇...
  例如batch size會是類別數目的倍數，
  又，等效訓練batch數變多(拉長訓練時間)
* 我用在我的文字情緒分類問題上，有效，
  獻醜了，
  我的資料筆數：230, 210, 150, 60, 60, 50 ... 12，
  是長尾分佈，
  feature extrator是拿別人pre-trained好，
  我只訓練fully connect layer。
  這是Instance-balanced sampling得到的混搖矩陣
  ![ib](7.png "ib exp.")
  這是Class-balanced sampling得到的混搖矩陣
  ![cb](8.png "ib exp.")
  兩者準確率沒差，
  但Class-balanced sampling的precision較均衡、f1-score高了10%。

## 參考資料
[1] 資料不平衡時的訓練技巧 https://www.svds.com/learning-imbalanced-classes/
[2] 論文心得 https://zhuanlan.zhihu.com/p/158638078
[3] 論文心得 https://blog.csdn.net/shanglianlm/article/details/105973699