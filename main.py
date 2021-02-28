#from __future__ import print_function
import sys
import copy
import datetime
import requests, bs4
import urllib.parse as urlparse
from datetime import datetime as dt
from typing import Final, List, Any, Dict
from dataclasses import dataclass


from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES: Final[List[str]] = ['https://www.googleapis.com/auth/calendar']
API_CRED_FILE_PATH: Final[str] = "./ServiceAccount.json"
API_CREDENTIAL: Final[Any] = service_account.Credentials.from_service_account_file(API_CRED_FILE_PATH, scopes=SCOPES)
API_SERVICE: Final[Any] = build('calendar', 'v3', credentials=API_CREDENTIAL)
CALENDAR_ID: Final[Any] = 's1c5d19mg7bo08h10ucio8uni8@group.calendar.google.com'
ATCODER_BASE_URL: Final[str] = 'https://atcoder.jp/'

@dataclass
class TimeWithStrTimeZone:
    time: datetime.datetime
    time_zone: str = 'Japan'

    def get_as_obj(self):
        self.time.tzinfo = None
        return {
            'dateTime': self.time.isoformat(timespec='seconds'),
            'timeZone': self.time_zone
        }

@dataclass
class AtCoderContest:
    summary: str
    start: TimeWithStrTimeZone
    end: TimeWithStrTimeZone
    location: str = ''
    description: str = ''
    
    def get_as_obj(self):
        '''
        以下のような形で返す
        {
            'summary': 'ABC001',
            'location': '',
            'description': 'https://atcoder.jp/contests/abc001',
            'start': {
                'dateTime': '2020-01-01T00:00:00',
                'timeZone': 'Japan',
            },
            'end': {
                'dateTime': '2020-01-01T01:00:00',
                'timeZone': 'Japan',
            }
        }
        '''
        return {
            'summary': self.summary,
            'location': self.location,
            'description': self.description,
            'start': self.start.get_as_obj(),
            'end': self.end.get_as_obj()
        }


def parse_event(name_obj, start_datetime_obj, duration_obj):
    summary = name_obj.text
    description = urlparse.urljoin(ATCODER_BASE_URL, name_obj.attrs['href'])
    start_datetime = dt.strptime(start_datetime_obj.text, '%Y-%m-%d %H:%M:%S+0900')
    duration_time = duration_obj.text.split(':')
    duration_timedelta = datetime.timedelta(hours=int(duration_time[0]), minutes=int(duration_time[1]))
    end_datetime = start_datetime + duration_timedelta
    return AtCoderContest(
        summary=summary, start=TimeWithStrTimeZone(start_datetime), end=TimeWithStrTimeZone(end_datetime), description=description
    ).get_as_obj()

def get_atcoder_schedule() :
    res = requests.get(urlparse.join(ATCODER_BASE_URL, "contests"))
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

    event_list = [
        parse_event(name_obj, start_datetime_obj, duration_obj)
        for name_obj, start_datetime_obj, duration_obj in zip(name_objs, start_datetime_objs, duration_objs)
    ]

    return event_list

# google calender api を使う部分．サンプルそのまま
def add_event(event):
    event = API_SERVICE.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    print (event['id'])

def delete_contests(time_from, time_to):
    API_SERVICE.events().list(
        calendarId=CALENDAR_ID,
        timeMin=f"{time_from.isoformat()}Z",
        timeMax=f"{time_to.isoformat()}Z",
    ).delete().execute()

def get_registered_event(time_from, time_to):
    # Call the Calendar API
    events_result = API_SERVICE.events().list(
        calendarId=CALENDAR_ID,
        timeMin=f"{time_from.isoformat()}Z",
        timeMax=f"{time_to.isoformat()}Z",
    ).execute()
    events = events_result.get('items', [])
    return [event['summary'] for event in events]

def main():
    event_list = get_atcoder_schedule()
    print(event_list)
    now = datetime.datetime.utcnow()
    eight_week_later = now + datetime.timedelta(weeks=8)
    delete_contests(time_from=now, time_to=eight_week_later)

    # 取得した各コンテストについてループ
    if not event_list:
        print("There is no unregistered upcoming contests.")
        sys.exit()

    for event in event_list:
        # TODO: eight_week_later以降のコンテストがあったらスキップ
        add_event(event)

if __name__ == '__main__':
    main()
