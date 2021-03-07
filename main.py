#from __future__ import print_function
import json
import os
import sys
import datetime
import requests, bs4
import urllib.parse as urlparse
from datetime import datetime as dt
from typing import List, Dict
from dataclasses import dataclass, InitVar, field

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES: List[str] = ['https://www.googleapis.com/auth/calendar']
CREDENTIAL_INFO: Dict[str, str] = json.loads(os.environ.get('CREDENTIAL_INFO'))
# ローカルテスト用
# with open('credential.json') as f:
#     print(f"f: {f}")
#     CREDENTIAL_INFO = json.load(f)
API_CREDENTIAL = service_account.Credentials.from_service_account_info(CREDENTIAL_INFO, scopes=SCOPES)
API_SERVICE = build('calendar', 'v3', credentials=API_CREDENTIAL, cache_discovery=False)
CALENDAR_ID: str = 's1c5d19mg7bo08h10ucio8uni8@group.calendar.google.com'
ATCODER_BASE_URL: str = 'https://atcoder.jp/'
@dataclass
class TimeWithStrTimeZone:
    time: datetime.datetime
    time_zone: str = 'Japan'

    def get_as_obj(self):
        return {
            'dateTime': self.time.isoformat(timespec='seconds'),
            'timeZone': self.time_zone
        }

@dataclass
class CalendarEvent:
    summary: str
    start_at: InitVar[datetime.datetime]
    end_at: InitVar[datetime.datetime]
    start: TimeWithStrTimeZone = field(init=False)
    end: TimeWithStrTimeZone = field(init=False)
    location: str = ''
    description: str = ''

    def __post_init__(self, start_at, end_at):
        self.start = TimeWithStrTimeZone(start_at)
        self.end = TimeWithStrTimeZone(end_at)
    
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


def parse_event(name_obj, start_datetime_obj, duration_obj) -> CalendarEvent:
    contest_title = name_obj.text
    contest_url = urlparse.urljoin(ATCODER_BASE_URL, name_obj.attrs['href'])
    start_at = dt.strptime(start_datetime_obj.text, '%Y-%m-%d %H:%M:%S+0900')
    contest_hours, contest_minutes = map(int, duration_obj.text.split(':'))
    contest_duration = datetime.timedelta(hours=contest_hours, minutes=contest_minutes)
    end_at = start_at + contest_duration
    return CalendarEvent(
        summary=contest_title, start_at=start_at, end_at=end_at, description=contest_url
    )

def get_atcoder_schedule() -> List[CalendarEvent]:
    res = requests.get(urlparse.urljoin(ATCODER_BASE_URL, "contests"))
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
def add_event(event: CalendarEvent, created_at: datetime.datetime):
    if event.description:
        event.description += '\n'
    # HACK: UTC to JST
    event.description += f"UPDATED AT: {(created_at + datetime.timedelta(hours=9)).strftime('%Y/%m/%d %H:%M:%S')} JST"
    added_event = API_SERVICE.events().insert(calendarId=CALENDAR_ID, body=event.get_as_obj()).execute()
    print (added_event['id'])

def delete_contests(time_from, time_to):
    events_to_delete =  API_SERVICE.events().list(
        calendarId=CALENDAR_ID,
        timeMin=f"{time_from.isoformat()}Z",
        timeMax=f"{time_to.isoformat()}Z",
    ).execute()['items']
    for event in events_to_delete:
        API_SERVICE.events().delete(
            calendarId=CALENDAR_ID,
            eventId=event['id']
        ).execute()

def main(data, context):
    event_list = get_atcoder_schedule()
    print(f"{len(event_list)} contests have been retrieved.")
    now = datetime.datetime.utcnow()
    eight_week_later = now + datetime.timedelta(weeks=8)
    delete_contests(time_from=now, time_to=eight_week_later)

    # 取得した各コンテストについてループ
    if not event_list:
        print("There is no upcoming contests.")
        sys.exit()

    counter = 0
    for event in event_list:
        if event.start.time > eight_week_later:
            continue
        counter += 1
        add_event(event, now)
    print(f'{counter} events have been added.')

if __name__ == '__main__':
    main()
