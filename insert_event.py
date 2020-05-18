from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

import requests, re, bs4

def delete_brackets(s):
    """
    括弧と括弧内文字列を削除
    """
    """ brackets to zenkaku """
    table = {
        "(": "（",
        ")": "）",
        "<": "＜",
        ">": "＞",
        "{": "｛",
        "}": "｝",
        "[": "［",
        "]": "］"
    }
    for key in table.keys():
        s = s.replace(key, table[key])
    """ delete zenkaku_brackets """
    l = ['（[^（|^）]*）', '【[^【|^】]*】', '＜[^＜|^＞]*＞', '［[^［|^］]*］',
            '「[^「|^」]*」', '｛[^｛|^｝]*｝', '〔[^〔|^〕]*〕', '〈[^〈|^〉]*〉']
    for l_ in l:
        s = re.sub(l_, "", s)
    """ recursive processing """
    return delete_brackets(s) if sum([1 if re.search(l_, s) else 0 for l_ in l]) > 0 else s

def get_atcoder_schedule() :
    # atcoderのコンテストスケジュールをまとめたサイトのhtmlを取得
    res = requests.get('https://competitiveprogramming.info/atcoder/contests')
    res.raise_for_status()
    # 取得したhtmlをbs4で解析可能に
    soup = bs4.BeautifulSoup(res.content, "html.parser")
    # 特定のタグ<td>についてその要素を取得
    #elems = soup.select("td")
    
    elems = []
    group = soup.find_all("td")
    for g in group:
        s = str(g.contents[0])
        s = delete_brackets(s)
        elems.append(s)

    for i in range((int(len(elems)/3))):
        s = elems[3*i].replace(" ", "T")[0:19]
        elems[3*i] = s

    return elems

def main(event):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    event = service.events().insert(calendarId='uc6houuit9g1eg16nt0u6v8uoo@group.calendar.google.com', body=event).execute()

    print (event['id'])


if __name__ == '__main__':

    event = {
        'summary': '予定の名前',
        #'location': 'Shibuya Office',
        'description': '予定の説明',
        'start': {
            'dateTime': '2020-05-19T09:00:00',
            'timeZone': 'Japan',
        },
        'end': {
            'dateTime': '2020-05-19T17:00:00',
            'timeZone': 'Japan',
        },
    }

    elems = get_atcoder_schedule()

    for i in range(3):
        event['start']['dateTime'] = str(elems[3*i])
        event['description'] = str(elems[3*i+1])
        event['summary'] = str(elems[3*i+2])

        tmp_time = str(elems[3*i])
        new_time = str(int(tmp_time[11:13])+1)[0:2]
        end_time = list(elems[3*i])
        end_time[11] = new_time[0]
        end_time[12] = new_time[1]
        
        event['end']['dateTime'] = "".join(end_time)

        print(event['summary'])
        print(event['description'])
        print(event['start']['dateTime'])
        print(event['end']['dateTime'])

        main(event)


    #main()