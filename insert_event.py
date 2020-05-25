#from __future__ import print_function
import sys
import copy
import pickle
import datetime
import os, os.path
import requests, bs4
import urllib.parse as urlparse
from datetime import datetime as dt
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def get_atcoder_schedule() :
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
    
    url = 'https://atcoder.jp/contests'
    res = requests.get(url)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, 'html.parser')

    contest_table = soup.find('div', id='contest-table-upcoming').find('table')
    start_datetime_objs = contest_table.select('tbody tr > td:nth-child(1)')
    name_objs = contest_table.select('tbody tr > td:nth-child(2) > a')
    duration_objs = contest_table.select('tbody tr > td:nth-child(3)')

    # コンテストの名前・開始時間・制限時間の数は同じ必要がある
    if not (len(name_objs) == len(start_datetime_objs) == len(duration_objs)):
        print("Failed to retrieve all the contests info.")
        sys.exit(1)
    num_event = len(start_datetime_objs)
    event_list = []

    for i in range(num_event):
        tmp_event = event
        tmp_event['summary'] = name_objs[i].text
        tmp_event['description'] = urlparse.urljoin('https://atcoder.jp', name_objs[i].attrs['href'])
        start_datetime = dt.strptime(start_datetime_objs[i].text, '%Y-%m-%d %H:%M:%S+0900')
        tmp_event['start']['dateTime'] = start_datetime.strftime('%Y-%m-%dT%H:%M:%S')
        duration_time = duration_objs[i].text.split(':')
        duration_timedelta = datetime.timedelta(hours=int(duration_time[0]), minutes=int(duration_time[1]))
        end_datetime = start_datetime + duration_timedelta
        tmp_event['end']['dateTime'] = end_datetime.strftime('%Y-%m-%dT%H:%M:%S')
        event_list.append(copy.deepcopy(tmp_event))
    return event_list

# google calender api を使う部分．サンプルそのまま
def add_event(event):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
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
            print(flow)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    event = service.events().insert(calendarId='s1c5d19mg7bo08h10ucio8uni8@group.calendar.google.com', body=event).execute()

    print (event['id'])

def get_registered_event():
    SCOPES = ['https://www.googleapis.com/auth/calendar']
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

    # Call the Calendar API
    dt = datetime.date.today()
    timefrom = dt.strftime('%Y/%m/%d')
    timeto = (dt + datetime.timedelta(weeks=8)).strftime('%Y/%m/%d')
    timefrom = datetime.datetime.strptime(timefrom, '%Y/%m/%d').isoformat()+'Z'
    timeto = datetime.datetime.strptime(timeto, '%Y/%m/%d').isoformat()+'Z'
    events_result = service.events().list(calendarId='s1c5d19mg7bo08h10ucio8uni8@group.calendar.google.com',timeMin=timefrom,timeMax=timeto,singleEvents=True,orderBy='startTime').execute()
    events = events_result.get('items', [])

    registered_event = []

    for event in events:
        registered_event.append(event['summary'])
    return registered_event


def main():
    event_list = get_atcoder_schedule()
    reged_list = get_registered_event()

    # 取得した各コンテストについてループ
    for event in event_list:
        # 既にカレンダーに追加済みであればその旨を出力
        if event['summary'] in reged_list :
            print('already registered!')
        # まだカレンダーに追加していないコンテストであれば追加し，
        # 追加済みリストにコンテスト名を書き込む
        else :
            add_event(event)

if __name__ == '__main__':
    main()
