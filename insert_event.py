from __future__ import print_function
import datetime
import pickle
import os, os.path
import requests, re, bs4
from datetime import datetime as dt
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

event = {
    'summary': '',
    'location': '',
    'description': '',
    'start': {
        'dateTime': '2020-01-01T00:00:00',
        'timeZone': 'Japan',
    },
    'end': {
        'dateTime': '2020-01-01T01:00:00',
        'timeZone': 'Japan',
    },
}

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


def main(event):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    event = service.events().insert(calendarId='s1c5d19mg7bo08h10ucio8uni8@group.calendar.google.com', body=event).execute()

    print (event['id'])


if __name__ == '__main__':

    names, start_dates, end_dates = get_atcoder_schedule()
    
    scheduled = []
    with open('data/schedule.txt', mode='rt') as f:
        for d in f:
            scheduled.append(d.replace('\n', ''))
    f.close()

    for name, start, end in zip(names, start_dates, end_dates) :
        
        event['summary'] = name
        event['start']['dateTime'] = start
        event['end']['dateTime'] = end
        
        if event['summary'] in scheduled :
            print('already registered!')
        else :
            main(event)
            with open('data/schedule.txt', mode='a') as f :
                f.write(str(event['summary']))
                f.write("\n")
            f.close()
