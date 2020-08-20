# atcoder_calender
AtCoderの[公式（？）カレンダー](https://calendar.google.com/calendar/embed?src=bhjouir2tb8p5efpbcfbnh8610%40group.calendar.google.com&ctz=Asia%2FTokyo)が更新されていないことがあるのでAPIの使い方やクラウド上での定期実行などの勉強も兼ねて作ってみることにした．

# main.py
こちらのソースコードを少し修正したものを Google Cloud Functions にアップロードして実行しています．
定期実行には Cloud Scheduler を活用しました．

以下，main.py 内の関数ごとに解説を書いておこうと思います．

## get_atcoder_schedule()

## get_registered_event()

## add_event()

## main()
