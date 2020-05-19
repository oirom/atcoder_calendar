import requests, bs4, os, datetime
from datetime import datetime as dt

def get_atcoder_schedule() :

    url = 'https://atcoder.jp/home'
    res = requests.get(url)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, "html.parser")

    start_date = []
    end_date = []
    contest_name = []

    # <div id="contest-table-upcoming"> の内容を取得
    for s in soup.find_all('div', id="contest-table-upcoming") :
        # <time> の内容を取得してリストに格納
        for t in s.find_all('time') :
            start_date.append(t.contents[0])
        # <a href='/contests/~'> の内容を取得してリストに格納
        for c in s.select('a[href^="/contests"]') :
            contest_name.append(c.contents[0])

    # <time> から取得した時刻を datetime モジュールで計算可能な形に処理
    start_date = list(map(lambda x : str(dt.strptime(x, '%Y-%m-%d %H:%M:%S+0900')), start_date))

    # 取得した AtCoder の開始時刻をもとに終了時刻を計算
    # 計算の際には日付の変更などに気を付ける必要あり
    end_date = list(map(lambda x : 
        str(dt.strptime(x, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(days=1, hours=1)) if dt.strptime(x, '%Y-%m-%d %H:%M:%S').hour==23 
        else str(dt.strptime(x, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=1)), start_date))
    
    # 日時データを google calender api で利用可能な形に整形（日付と時刻の間に T を入れるだけ）
    start_date = list(map(lambda x : x.replace(" ", "T"), start_date))
    end_date = list(map(lambda x : x.replace(" ", "T"), end_date))

    return contest_name, start_date, end_date

if __name__ == '__main__':

    names, start_dates, end_dates = get_atcoder_schedule()

    for start, end, name in zip(start_dates, end_dates, names) :
        print(start, end, name)
