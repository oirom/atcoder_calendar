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

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_registered_event():
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
        print(event['summary'])

if __name__ == '__main__':
    
    reged_list = get_registered_event()

    print(reged_list)