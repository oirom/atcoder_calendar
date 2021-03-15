# atcoder_calender
AtCoderの[公式（？）カレンダー](https://calendar.google.com/calendar/embed?src=bhjouir2tb8p5efpbcfbnh8610%40group.calendar.google.com&ctz=Asia%2FTokyo)が更新されていないことがあるのでAPIの使い方やクラウド上での定期実行などの勉強も兼ねて作ってみることにした．


**通常URL**（ブラウザでカレンダーを見る場合はこちら）: https://calendar.google.com/calendar/embed?src=s1c5d19mg7bo08h10ucio8uni8%40group.calendar.google.com&ctz=Asia%2FTokyo

**iCal形式URL**（自分のGoogleカレンダーに登録する際のURLはこちら） : https://calendar.google.com/calendar/ical/s1c5d19mg7bo08h10ucio8uni8%40group.calendar.google.com/public/basic.ics

# main.py
こちらのソースコードを少し修正したものを Google Cloud Functions にアップロードして実行しています．
定期実行には Cloud Scheduler を活用しました．

以下，main.py 内の関数ごとに解説を書いておこうと思います．
