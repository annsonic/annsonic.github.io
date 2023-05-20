---
title: >-
  Dynamic Knowledge Graph Construction for Zero-shot Commonsense Question
  Answering
date: 2020-09-01 19:57:24
categories: Interested Paper
---

2019年發表於ArXiv，
作者來自於艾倫人工智慧研究所，
無提供source code
不過其中運用了他們的前作COMeT[1]，
COMeT有提供source code: https://github.com/atcbosselut/comet-commonsense
和網頁互動demo: https://mosaickg.apps.allenai.org/
我讀這一篇是因為做情感分類的題目，
想知道如何利用COMeT提供的資訊來輔助分類文字的情緒，
紀錄一下自己從中學習到的。
<!-- more -->

## 觀點與事實
* 此文獻提出使用動態生成的知識圖譜來回答社交上的常識性問題，達成零樣本學習的模型
* 可以應用於社交機器人的決策，或是應答
* 作者利用COMeT模型，
  並加以計算知識圖譜的multi-hop推論。
* 在STORY Commonsense dataset上測試情緒分類，
  1-hop推論得到的F1-score = 19.3%，
  相較於直接使用COMeT的結果好1%。

## 背景簡介
* 可以將分類問題，轉化為QA問題，而且使用知識圖譜，計算multi-hop推論，選出信心值最高的答案
  ![scenario](1.png "Application")
* 前作ATOMIC[2]提出一個事件和隱含的社交常識對應的資料集，
  標註了事件主角的感受(xReact)
  ![atomic](2.png "ATOMIC dataset")
  ![atomic items](3.png "ATOMIC dataset items")
  有提供網頁以瀏覽資料集： https://homes.cs.washington.edu/~msap/atomic/
* 前作COMeT[1]使用GPT模型、訓練在ATOMIC資料集[2]，
  將ATOMIC的事件、標註類型和標註值串接成一個句子，
  所以給個起頭的句子(即事件和標註類型)，
  GPT模型會接著推論標註值來完成句子，
  所以是動態的知識圖譜。
  ![comet](4.png "COMeT")

## 模型與方法
* 升級COMeT，使用GPT-2作為骨幹，
  藉由GPT-2已讀過許多書，
  能廣泛推論不在ATOMIC資料集內的事件，
  有潛力達成Zero-shot learning
* multi-hop推論來增進推論的準確率，
  作者的認為可以由xWant、xIntent、xEffect等標註類型，
  來推論背後的主角的感受(xReact)，
  但因為知識圖譜上路徑太多，
  需要手動設定關聯性閥值以取捨路徑
  ![direct inference](5.png "CA")
  ![1-hop](6.png "CGA")

## 資料集
* 我只挑情緒分類這一個實驗來介紹
  作者使用STORY COMMONSENSE Dataset做驗證，
  它以5句構成一則小故事，
  句子有標註幾個描述情感的形容詞，
  training dataset是標註多個情感強烈程度，
  validation和testing dataset才是標註單一個情緒分類
  ![story_commonsense](7.png "story")

## 實驗結果節錄
  ![story_commonsense_exp](9.png "story exp.")

## 個人感想
* COMeT能接受的句型有限，應該是受限於ATOMIC資料集句子、偏向簡短的SVO句型
* 實驗中如何得到情緒分類的標籤...關於這點作者沒有交待清楚，
  COMeT產生的xReact不是完全照情緒分類的標籤名稱，
  像是這樣
  ![comet output](8.png "my exp.")
  我查了一下別的QA論文，
  Language Models are Unsupervised Multitask Learners這一篇當中的Natural Questions dataset驗證，
  它的QA答案是藏在context文字中，
  模型的輸出是答案在context文字中的index值；
  可是STORY COMMONSENSE Dataset的答案並不是藏在context文字裡欸，
  想像上會需要有個字典，
  將COMeT輸出的形容詞再分類
* 作者比較了supervised learning和zero-shot learning，
  GPT(supervised learning)的結果大勝COMeT(zero-shot learning)，
  我感覺因為COMeT輸出的形容詞會有分歧的狀況，
  例如退休事件、輸出了疲憊和喜悅，
  再推論單一個情緒分類標籤時會產生干擾，
  supervised learning則專心學習出一個情緒分類標籤。

  我不能冤枉COMeT不好，
  它應該適用於申論題的情況，
  能考慮到多個面向的答案。