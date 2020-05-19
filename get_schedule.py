import requests, re, bs4, json, os, shutil, datetime, urllib.request
from bs4 import BeautifulSoup
from datetime import datetime as dt

def get_atcoder_schedule() :

    url = 'https://atcoder.jp/home'
    res = requests.get(url)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, "html.parser")

    contest_date = []
    contest_name = []

    # <div id="contest-table-upcoming"> の内容を取得
    for s in soup.find_all('div', id="contest-table-upcoming") :
        # <time> の内容を取得してリストに格納
        for t in s.find_all('time') :
            contest_date.append(t.contents[0])
        # <a href='/contests/~'> の内容を取得してリストに格納
        for c in s.select('a[href^="/contests"]') :
            contest_name.append(c.contents[0])

    # <time> から取得した時刻を datetime モジュールで計算可能な形に処理
    contest_date = list(map(lambda x : str(dt.strptime(x, '%Y-%m-%d %H:%M:%S+0900')), contest_date))

    return contest_name, contest_date

if __name__ == '__main__':

    name, start_date = get_atcoder_schedule()

    print (name)
    print (start_date)

    # 取得した AtCoder の開始時刻から終了時刻を計算
    end_date = list(map(lambda x : 
        str(dt.strptime(x, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(days=1, hours=1)) if dt.strptime(x, '%Y-%m-%d %H:%M:%S').hour==23 
        else str(dt.strptime(x, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=1)), start_date))

    print (end_date)