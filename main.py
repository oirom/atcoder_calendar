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
    res = requests.get(urlparse.urljoin(ATCODER_BASE_URL, "contests/?lang=ja"))
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

def add_updated_at(event: CalendarEvent, updated_at: datetime.datetime, create: bool = False):
    if event.description:
        event.description += '\n'
    # HACK: UTC to JST
    updated_at_str: str = f"{(updated_at + datetime.timedelta(hours=9)).strftime('%Y/%m/%d %H:%M:%S')} JST"

    if create:
        event.description += f"CREATED AT: {updated_at_str}\n"
    event.description += f"UPDATED AT: {updated_at_str}"

def add_event(event: CalendarEvent, created_at: datetime.datetime):
    add_updated_at(event, created_at, create=True)
    added_event = API_SERVICE.events().insert(calendarId=CALENDAR_ID, body=event.get_as_obj()).execute()

def get_registered_events(time_from: datetime.datetime, time_to: datetime.datetime):
    registered_events = []
    
    page_token = None
    while True:
        events = API_SERVICE.events().list(
            calendarId=CALENDAR_ID,
            timeMin=f"{time_from.isoformat()}Z",
            timeMax=f"{time_to.isoformat()}Z",
            pageToken=page_token
        ).execute()
        registered_events += events['items']
        page_token = events.get('nextPageToken')
        if not page_token:
            break

    return registered_events

def delete_events(time_from: datetime.datetime, time_to: datetime.datetime):
    events_to_delete = get_registered_events(time_from, time_to)
    for event in events_to_delete:
        API_SERVICE.events().delete(
            calendarId=CALENDAR_ID,
            eventId=event['id']
        ).execute()
    print(f'{len(events_to_delete)} events have been deleted.')

def update_event(event_id: str, event_description: str, event: CalendarEvent, updated_at: datetime.datetime):
    # Googleカレンダーの説明欄からCREATED ATを抜き出してeventにつける
    description_lines = list(filter(lambda line: line != '', event_description.split('\n')))
    # descriptionにURLとUPDATED ATしかつけてなかった時の名残のreplace
    created_at_str = description_lines[1].replace('UPDATED AT: ', 'CREATED AT: ')
    if event.description:
        event.description += '\n'
    event.description += created_at_str

    # 更新時間を更新
    add_updated_at(event, updated_at)
    API_SERVICE.events().update(
        calendarId=CALENDAR_ID,
        eventId=event_id,
        body=event.get_as_obj()
    ).execute()

def main(data, context):
    upcoming_contests = get_atcoder_schedule()
    print(f"{len(upcoming_contests)} contests have been retrieved.")
    now = datetime.datetime.utcnow()
    eight_week_later = now + datetime.timedelta(weeks=8)

    if not upcoming_contests:
        print("There is no upcoming contests.")
        sys.exit()

    updated_count = 0
    inserted_count = 0

    registered_contests = get_registered_events(now, eight_week_later)
    for uc in upcoming_contests:
        already_registered = False
        for rc in registered_contests:
            if uc.summary == rc['summary']:
                updated_count += 1
                update_event(rc['id'], rc['description'], uc, now)
                already_registered = True
                break

        if already_registered:
            continue

        inserted_count += 1
        add_event(uc, now)
    
    print(f"{updated_count} contests have been updated.")
    print(f"{inserted_count} contests have been added.")

if __name__ == '__main__':
    main('', '')
