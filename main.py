#from __future__ import print_function
import sys
import copy
import datetime
import requests, bs4
import urllib.parse as urlparse
from datetime import datetime as dt
from typing import Final, List, Any


from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES: Final[List[str]] = ['https://www.googleapis.com/auth/calendar']
API_CRED_FILE_PATH: Final[str] = "./ServiceAccount.json"
API_CREDENTIAL:Final[Any] = service_account.Credentials.from_service_account_file(API_CRED_FILE_PATH, scopes=SCOPES)
API_SERVICE = build('calendar', 'v3', credentials=API_CREDENTIAL)

def get_atcoder_schedule() :
    EVENT_TEMPLATE: Final[dict[str, str]] = {
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
    
    url: Final[str] = 'https://atcoder.jp/'
    res = requests.get(urlparse.join(url, "contests"))
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
        tmp_event = copy.deepcopy(EVENT_TEMPLATE)
        tmp_event['summary'] = name_objs[i].text
        tmp_event['description'] = urlparse.urljoin(url, name_objs[i].attrs['href'])
        start_datetime = dt.strptime(start_datetime_objs[i].text, '%Y-%m-%d %H:%M:%S+0900')
        tmp_event['start']['dateTime'] = start_datetime.strftime('%Y-%m-%dT%H:%M:%S')
        duration_time = duration_objs[i].text.split(':')
        duration_timedelta = datetime.timedelta(hours=int(duration_time[0]), minutes=int(duration_time[1]))
        end_datetime = start_datetime + duration_timedelta
        tmp_event['end']['dateTime'] = end_datetime.strftime('%Y-%m-%dT%H:%M:%S')
        event_list.append(tmp_event)
    return event_list

# google calender api を使う部分．サンプルそのまま
def add_event(event):
    event = API_SERVICE.events().insert(calendarId='s1c5d19mg7bo08h10ucio8uni8@group.calendar.google.com', body=event).execute()
    print (event['id'])

def get_registered_event():
    # Call the Calendar API
    dt = datetime.date.today()
    timefrom = dt.strftime('%Y/%m/%d')
    timeto = (dt + datetime.timedelta(weeks=8)).strftime('%Y/%m/%d')
    timefrom = datetime.datetime.strptime(timefrom, '%Y/%m/%d').isoformat()+'Z'
    timeto = datetime.datetime.strptime(timeto, '%Y/%m/%d').isoformat()+'Z'
    events_result = API_SERVICE.events().list(calendarId='s1c5d19mg7bo08h10ucio8uni8@group.calendar.google.com',timeMin=timefrom,timeMax=timeto,singleEvents=True,orderBy='startTime').execute()
    events = events_result.get('items', [])
    return [event['summary'] for event in events]

def main():
    event_list = get_atcoder_schedule()
    print(event_list)
    reged_list = get_registered_event()
    print(reged_list)

    # 取得した各コンテストについてループ
    if not event_list:
        print("There is no unregistered upcoming contests.")
        sys.exit()

    for event in event_list:
        # 既にカレンダーに追加済みであればその旨を出力
        if event['summary'] in reged_list :
            print('already registered!')
            continue
        # まだカレンダーに追加していないコンテストであれば追加し，
        # 追加済みリストにコンテスト名を書き込む
        add_event(event)

if __name__ == '__main__':
    main()
