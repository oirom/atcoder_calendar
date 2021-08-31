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
    created_at: datetime.datetime
    updated_at: datetime.datetime
    start_at: InitVar[datetime.datetime]
    end_at: InitVar[datetime.datetime]
    start: TimeWithStrTimeZone = field(init=False)
    end: TimeWithStrTimeZone = field(init=False)
    id: str = ''
    url: str = ''

    def __post_init__(self, start_at, end_at):
        self.start = TimeWithStrTimeZone(start_at)
        self.end = TimeWithStrTimeZone(end_at)
    
    def get_description(self) -> str:
        return f"created at: {utc_to_jst_str(self.created_at)}\nupdated at: {utc_to_jst_str(self.updated_at)}"
    
    def get_as_obj(self):
        '''
        以下のような形で返す
        {
            'summary': 'ABC001',
            'location': 'https://atcoder.jp/contests/abc001',
            'description': 'created at: 2021/08/20 23:00:11 JST\nupdated at: 2021/08/28 16:34:11 JST',
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
            'location': self.url,
            'description': self.get_description(),
            'start': self.start.get_as_obj(),
            'end': self.end.get_as_obj()
        }

def utc_to_jst_str(time: datetime.datetime) -> str:
    """
    takes utc datetime.datetime and return jst in str
    """
    return f"{(time + datetime.timedelta(hours=9)).strftime('%Y/%m/%d %H:%M:%S')} JST"

def parse_text_obj_to_calendarevent(name_obj, start_datetime_obj, duration_obj, now: datetime.datetime) -> CalendarEvent:
    contest_title = name_obj.text
    contest_url = urlparse.urljoin(ATCODER_BASE_URL, name_obj.attrs['href'])
    start_at = dt.strptime(start_datetime_obj.text, '%Y-%m-%d %H:%M:%S+0900')
    contest_hours, contest_minutes = map(int, duration_obj.text.split(':'))
    contest_duration = datetime.timedelta(hours=contest_hours, minutes=contest_minutes)
    end_at = start_at + contest_duration
    return CalendarEvent(
        summary=contest_title, url=contest_url, created_at=now, updated_at=now, start_at=start_at, end_at=end_at
    )

def get_atcoder_schedule(now: datetime.datetime) -> List[CalendarEvent]:
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
        parse_text_obj_to_calendarevent(name_obj, start_datetime_obj, duration_obj, now)
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

def add_event(event: CalendarEvent):
    added_event = API_SERVICE.events().insert(calendarId=CALENDAR_ID, body=event.get_as_obj()).execute()

def parse_datetime(t: str) -> datetime.datetime:
    try:
        return datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
    except:
        return datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%f%z")

def parse_event(event_item_obj) -> CalendarEvent:
    return CalendarEvent(
        summary=event_item_obj['summary'],
        created_at=parse_datetime(event_item_obj['created']),
        updated_at=parse_datetime(event_item_obj['updated']),
        start_at=parse_datetime(event_item_obj['start']['dateTime']),
        end_at=parse_datetime(event_item_obj['end']['dateTime']),
        id=event_item_obj['id']
    )

def get_registered_events(time_from: datetime.datetime, time_to: datetime.datetime) -> List[CalendarEvent]:
    registered_events: List[CalendarEvent] = []
    
    page_token = None
    while True:
        events = API_SERVICE.events().list(
            calendarId=CALENDAR_ID,
            timeMin=f"{time_from.isoformat()}Z",
            timeMax=f"{time_to.isoformat()}Z",
            pageToken=page_token
        ).execute()
        registered_events += [parse_event(event_item_obj) for event_item_obj in events['items']]
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

def update_event(registered_event: CalendarEvent, retrieved_event: CalendarEvent) -> None:
    # created at: the time the registered event was created
    retrieved_event.created_at = registered_event.created_at
    # updated at: now
    # retrieved_event.updated_at is already "now"

    API_SERVICE.events().update(
        calendarId=CALENDAR_ID,
        eventId=registered_event.id,
        body=retrieved_event.get_as_obj()
    ).execute()

def main(data, context):
    now = datetime.datetime.utcnow()
    upcoming_contests = get_atcoder_schedule(now)
    print(f"{len(upcoming_contests)} contests have been retrieved.")
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
            if uc.summary == rc.summary:
                updated_count += 1
                update_event(rc, uc)
                already_registered = True
                break

        if already_registered:
            continue

        inserted_count += 1
        add_event(uc)
    
    print(f"{updated_count} contests have been updated.")
    print(f"{inserted_count} contests have been added.")

if __name__ == '__main__':
    main('', '')
