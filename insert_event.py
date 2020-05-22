from __future__ import print_function
import datetime
import pickle
import os, os.path
import sys
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
    url = 'https://atcoder.jp/contests'
    res = requests.get(url)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, 'html.parser')

    contest_table = soup.find('div', id='contest-table-upcoming').find('table')
    start_datetime_objs = contest_table.select('tbody tr > td:nth-child(1)')
    name_objs = contest_table.select('tbody tr > td:nth-child(2) > a')
    duration_objs = contest_table.select('tbody tr > td:nth-child(3)')

    # コンテストの名前・開始時間・制限時間の数は同じ必要がある
    if not (len(start_datetime_objs) == len(name_objs) and len(name_objs) == len(duration_objs)):
        print("Failed to retrieve all the contests info.")
        sys.exit(1)

    start_date = []
    end_date = []
    contest_name = list(map(lambda name_obj: name_obj.text, name_objs))

    for i in range(len(start_datetime_objs)):
        start_datetime = dt.strptime(start_datetime_objs[i].text, '%Y-%m-%d %H:%M:%S+0900')
        start_date.append(start_datetime.strftime('%Y-%m-%dT%H:%M:%S'))
        duration_time = duration_objs[i].text.split(':')
        duration_timedelta = datetime.timedelta(hours=int(duration_time[0]), minutes=int(duration_time[1]))
        end_datetime = start_datetime + duration_timedelta
        end_date.append(end_datetime.strftime('%Y-%m-%dT%H:%M:%S'))
    return contest_name, start_date, end_date

# google calender api を使う部分．サンプルそのまま
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

    # コンテスト名，開始時刻，終了時刻をそれぞれリスト形式で取得
    names, start_dates, end_dates = get_atcoder_schedule()
    
    # 既にカレンダーに追加しているコンテスト名を読みこむ
    scheduled = []
    with open('data/schedule.txt', mode='rt') as f:
        for d in f:
            scheduled.append(d.replace('\n', ''))
    f.close()

    # 取得した各コンテストについてループ
    for name, start, end in zip(names, start_dates, end_dates) :
        
        event['summary'] = name
        event['start']['dateTime'] = start
        event['end']['dateTime'] = end
        
        # 既にカレンダーに追加済みであればその旨を出力
        if event['summary'] in scheduled :
            print('already registered!')
        # まだカレンダーに追加していないコンテストであれば追加し，
        # 追加済みリストにコンテスト名を書き込む
        else :
            main(event)
            with open('data/schedule.txt', mode='a') as f :
                f.write(str(event['summary']))
                f.write("\n")
            f.close()
