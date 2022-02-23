import json
import os
import sys
import datetime
import urllib.parse as urlparse
from datetime import datetime as dt
from typing import Final, List, Dict
from dataclasses import dataclass, InitVar, field

import requests
import bs4
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES: List[str] = ['https://www.googleapis.com/auth/calendar']

CREDENTIAL_INFO: Dict[str, str] = {}
if os.environ.get('ENV') == 'local':
    # ローカルでテスト
    # `ENV=local python3 main.py` みたいに使う
    print(f'Running in {os.environ.get("ENV")}.')
    CREDENTIAL_FILE_NAME: Final[str] = 'credential.json'
    if not os.path.exists(CREDENTIAL_FILE_NAME):
        print(f'{CREDENTIAL_FILE_NAME} does not exist.')
        exit(1)
    CREDENTIAL_INFO = json.load(open('credential.json'))
else:
    # 本番環境で実行されている
    print('Running in production.')
    CREDENTIAL_VARIABLE_NAME: Final[str] = 'CREDENTIAL_INFO'
    if CREDENTIAL_VARIABLE_NAME not in os.environ:
        print(f'{CREDENTIAL_VARIABLE_NAME} is not set.')
        print('If you meant to run this in local,')
        print(f'try `ENV=local python3 {__file__}`')
        exit(1)
    CREDENTIAL_INFO = json.loads(os.environ.get('CREDENTIAL_INFO'))

API_CREDENTIAL = service_account.Credentials.from_service_account_info(
    CREDENTIAL_INFO, scopes=SCOPES
)
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
    start_at_with_time_zone: TimeWithStrTimeZone = field(init=False)
    end_at_with_timw_zone: TimeWithStrTimeZone = field(init=False)
    id: str = ''
    url: str = ''

    def __post_init__(self, start_at, end_at):
        self.start_at_with_time_zone = TimeWithStrTimeZone(start_at)
        self.end_at_with_timw_zone = TimeWithStrTimeZone(end_at)

    def get_description(self) -> str:
        """
        :returns: Description formatted for Google Calendar
        """
        created_at_jst_str: Final[str] = utc_to_jst_str(self.created_at)
        updated_at_jst_str: Final[str] = utc_to_jst_str(self.updated_at)
        return f"created at: {created_at_jst_str}\nupdated at: {updated_at_jst_str}"

    def get_as_obj(self) -> dict:
        """
        :returns: Dictionary formatted for Google Calendar API
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
        """
        return {
            'summary': self.summary,
            'location': self.url,
            'description': self.get_description(),
            'start': self.start_at_with_time_zone.get_as_obj(),
            'end': self.end_at_with_timw_zone.get_as_obj()
        }

    @classmethod
    def parse_event(cls, event_item_obj: dict) -> "CalendarEvent":
        """
        :param event_item_obj: Object received from Google Calendar API
        :returns: CalendarEvent obtained by parsing the param
        """
        return CalendarEvent(
            summary=event_item_obj['summary'],
            created_at=parse_datetime(event_item_obj['created']),
            updated_at=parse_datetime(event_item_obj['updated']),
            start_at=parse_datetime(event_item_obj['start']['dateTime']),
            end_at=parse_datetime(event_item_obj['end']['dateTime']),
            id=event_item_obj['id']
        )

    @classmethod
    def parse_text_obj_to_calendarevent(
            cls, name_obj, start_datetime_obj, duration_obj, now: datetime.datetime
        ) -> "CalendarEvent":
        """
        :param name_obj: Object, which contains name and url of the contest, obtained from html
        :param start_datetime_obj: Object, which contains start time, obtained from html
        :param duration_obj: Object, which contains duration time (1:30 as one hour and 30 minutes), obtained from html
        :param now: The time this program started
        :returns: Parsed Calendar Event
        """
        contest_title: str = name_obj.text
        contest_url: str = urlparse.urljoin(ATCODER_BASE_URL, name_obj.attrs['href'])
        start_at: datetime.datetime = dt.strptime(start_datetime_obj.text, '%Y-%m-%d %H:%M:%S+0900')
        contest_hours, contest_minutes = map(int, duration_obj.text.split(':'))
        contest_duration: datetime.timedelta = datetime.timedelta(hours=contest_hours, minutes=contest_minutes)
        end_at: datetime.datetime = start_at + contest_duration
        return CalendarEvent(
            summary=contest_title,
            created_at=now,
            updated_at=now,
            start_at=start_at,
            end_at=end_at,
            url=contest_url
        )

    @classmethod
    def are_same_contests(cls, contest: "CalendarEvent", another_contest: "CalendarEvent") -> bool:
        return (
            contest.summary == another_contest.summary
            or
            contest.url == another_contest.url
        )

def utc_to_jst_str(time: datetime.datetime) -> str:
    """
    :returns: Time converted to JST as string
    """
    return f"{(time + datetime.timedelta(hours=9)).strftime('%Y/%m/%d %H:%M:%S')} JST"


def get_atcoder_schedule(now: datetime.datetime) -> List[CalendarEvent]:
    res = requests.get(urlparse.urljoin(ATCODER_BASE_URL, "contests/?lang=ja"))
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, 'html.parser')

    contest_table = soup.find('div', id='contest-table-upcoming').find('table')
    start_datetime_objs = contest_table.select('tbody tr > td:nth-child(1)')
    name_objs = contest_table.select('tbody tr > td:nth-child(2) > a')
    duration_objs = contest_table.select('tbody tr > td:nth-child(3)')

    # コンテストの名前・開始時間・制限時間の数は同じ必要がある
    if not len(name_objs) == len(start_datetime_objs) == len(duration_objs):
        print("Failed to retrieve all the contests info.")
        sys.exit(1)

    event_list = [
        CalendarEvent.parse_text_obj_to_calendarevent(nobj, sobj, dobj, now)
        for nobj, sobj, dobj in zip(name_objs, start_datetime_objs, duration_objs)
    ]

    return event_list

def add_event(event: CalendarEvent):
    API_SERVICE.events().insert(calendarId=CALENDAR_ID, body=event.get_as_obj()).execute()

def parse_datetime(t: str) -> datetime.datetime:
    try:
        return datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%f%z")

def get_registered_events(
        time_from: datetime.datetime, time_to: datetime.datetime
    ) -> List[CalendarEvent]:
    registered_events: List[CalendarEvent] = []

    page_token = None
    while True:
        events = API_SERVICE.events().list(
            calendarId=CALENDAR_ID,
            timeMin=f"{time_from.isoformat()}Z",
            timeMax=f"{time_to.isoformat()}Z",
            pageToken=page_token
        ).execute()
        registered_events += [
            CalendarEvent.parse_event(event_item_obj) for event_item_obj in events['items']
        ]
        page_token = events.get('nextPageToken')
        if not page_token:
            break

    return registered_events

def delete_events(time_from: datetime.datetime, time_to: datetime.datetime):
    events_to_delete = get_registered_events(time_from, time_to)
    for event in events_to_delete:
        API_SERVICE.events().delete(
            calendarId=CALENDAR_ID,
            eventId=event.id
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
    for upcoming in upcoming_contests:
        already_registered = False
        for registered in registered_contests:
            if CalendarEvent.are_same_contests(upcoming, registered):
                updated_count += 1
                update_event(registered, upcoming)
                already_registered = True
                break

        if already_registered:
            continue

        inserted_count += 1
        add_event(upcoming)

    print(f"{updated_count} contests have been updated.")
    print(f"{inserted_count} contests have been added.")

if __name__ == '__main__':
    main('', '')
