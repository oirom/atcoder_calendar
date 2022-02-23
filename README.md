# atcoder_calender
AtCoderの[公式（？）カレンダー](https://calendar.google.com/calendar/embed?src=bhjouir2tb8p5efpbcfbnh8610%40group.calendar.google.com&ctz=Asia%2FTokyo)が更新されていないことがあるのでAPIの使い方やクラウド上での定期実行などの勉強も兼ねて作ってみることにした。

# 自分のGoogleカレンダーに追加する 
- [AtCoder Beginner Contest (ABC) のみ](https://calendar.google.com/calendar/embed?src=74149il1jgs77vpujlp6qrb89g%40group.calendar.google.com&ctz=Asia%2FTokyo)  
- [AtCoder の全てのコンテスト](https://calendar.google.com/calendar/embed?src=s1c5d19mg7bo08h10ucio8uni8%40group.calendar.google.com&ctz=Asia%2FTokyo)  
リンクを開いていただき、右下のプラスボタン(画像の赤丸で囲んだ部分)を押すと自分のGoogleカレンダーに追加することができます。

<img src="https://user-images.githubusercontent.com/49501934/131486820-cc17fa38-625c-4cba-9d8b-c8f2d5f89293.jpg" width="400px">

# main.py
こちらのソースコードを少し修正したものを Google Cloud Functions にアップロードして実行しています。

定期実行には Cloud Scheduler を活用しました。

# リンタの掛け方
※pylint のインストールが必要です。  
`pylint --rcfile=./pylintrc main.py`
