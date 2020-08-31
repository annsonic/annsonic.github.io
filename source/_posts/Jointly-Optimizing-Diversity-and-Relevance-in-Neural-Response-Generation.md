---
title: Jointly Optimizing Diversity and Relevance in Neural Response Generation
date: 2020-05-09 11:48:22
categories: Interested Paper
---

2019年發表於NLP四大頂會之一的NAACL-HLT，
作者來自於微軟，
有提供source code:https://github.com/golsun/SpaceFusion
<!-- more -->

## 觀點與事實
* 此文獻提出一個控制Seq2seq模型生成語意的方法
* 可以應用於做出有個性的聊天機器人、給對話加料
* 作者提出SpaceFusion模型，
  在loss函數引入新的regularization項，
  將AE模型的encoder潛在空間融入Seq2Seq模型的空間,
  可以藉由在encoder潛在空間以內插的方式，
  控制生成的句子的語氣或意見。
* 請評審評分（5分制），
  SpaceFusion模型得到句子相關性2.72分，
  變化性2.53分，
  較其他模型優。

## 背景簡介
* 已有Seq2seq模型用於聊天機器人（自然語言生成）的任務，
  但存在問題之一是容易產生無意義的句子，
  例如：I don’t know，或是OK，
  原因是訓練文本中很多這種無意義句子，
  而這些句子泛用於多種情境中。
* 句子的多樣性與對話的相關性，往往是需要折衷的。
* 前作[2]使用AE輔助Seq2Seq，
  兩者共用同一個decoder，
  ![previous work](1.jpg "AE multitask")
  Seq2Seq輸入context句子，
  學習輸出對應的hypothesis句子，
  AE負責學習其他可以配上此context的reference句子、學習出這些句子的空間分佈，
  兩者交替學習；
  ![latent space](2.jpg "latent space")
  但是將Seq2seq和AE的encoder潛在空間一起視覺化後，
  發現兩者沒有交集，
  空間中存在一個大空白區域。

## 資料集
* 作者使用Switchboard資料集和Reddit資料集，我針對Reddit資料集做介紹。
  從Reddit網站爬了2011年份的發文以及其留言，
  以發文作為context、留言作為references句子（和hypothesis句子），
  平均一句context有24句reference。
  ![dataset](3.jpg "reddit")
## 模型與方法
  1. 為了消弭空間中的空白區域，
    將Seq2Seq的encoder潛在空間與AE的encoder潛在空間拉近，
    因為句子配對有n種組合、所以距離除以n，n是batch size;
	![method 1](4.jpg "regularization ")
  2. 為求句子均勻佔據在空間中，
    不同的context彼此在Seq2seq encoder潛在空間中的距離要拉遠，
    同樣地，references句子彼此在AE encoder潛在空間中的距離要拉遠，
    而句子佔據空間中有 n*(n-1)種組合，
    所以距離除以n^2-n
	![method 2](5.jpg "regularization ")
  3. 希望能以內插的方式，控制生成的句子的語氣或意見，
    所以加入新的內插encoder潛在空間Zinterp，
    Zinterp的計算公式如下，
    decoder實際為3個不同的decoder所組成。
    發現一個疑點，
    Zinterp生成的句子yinterp_hat是需要標準答案，
    才能計算出categorical cross entropy，
    這…看code還是不清楚作者怎麼解決此問題的，
    不過看作者實驗中的u值，
    u超過0.3即取reference句子做輸出，
    可能就是這般訓練出模型的。
  4.整體的loss函數，於是Seq2seq和AE變成同時做訓練。
    ![method 3](6.jpg "regularization ")
	![model](7.jpg "model ")
## 實驗結果節錄
  ![result](8.jpg "result ")
  ![result](9.jpg "result ")
  ![result](10.jpg "result ")
  ![result](11.jpg "result ")
  ![result](12.jpg "result ")
  
## 個人感想
* 作者擅長視覺化說故事
* 將encoder潛在空間混合後，用內插法來控制生成句子的語氣或意見，
  感覺比起其他方法來得溫和，句子品質應該有比較好
* 但內插u的值域不是預期的[0, 1]、而是[0, 0.3]，
  造成內插帶來的漸變效果有限。

## 參考資料
[1] “Jointly Optimizing Diversity and Relevance in Neural Response Generation,” Xiang Gao, Sungjin Lee, Yizhe Zhang, Chris Brockett, Michel Galley, Jianfeng Gao, Bill Dolan, NAACL-HLT, 2019.
[2] “Multi-Task Learning for Speaker-Role Adaptation in Neural Conversation Models,” Yi Luan, Chris Brockett, Bill Dolan, Jianfeng Gao, Michel Galley, IJCNLP 2017.
