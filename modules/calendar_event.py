from dataclasses import InitVar, dataclass, field
import datetime

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
