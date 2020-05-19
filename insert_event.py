from __future__ import print_function
import datetime
import pickle
import os, os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

import requests, re, bs4, shutil
from collections import OrderedDict
from datetime import datetime as dt

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
    res = requests.get('https://atcoder.jp/home')
    res.raise_for_status()
    # 取得したhtmlをbs4で解析可能に
    soup = bs4.BeautifulSoup(res.content, "html.parser")
    # 特定のタグ<td>についてその要素を取得
    #elems = soup.select("td")
    
    elems = []
    group = soup.find_all("td")
    for g in group:
        s = delete_brackets(str(g))
        elems.append(s)
    
    contests = []
    for i in range(len(elems)):
        try :
            t = dt.strptime(elems[i], '%Y-%m-%d %H:%M:%S+0900')
            contests.append(elems[i+1].replace("◉ ", ""))
            contests.append(str(t))
        except :
            continue

    return contests


def main(event):
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

    event = service.events().insert(calendarId='s1c5d19mg7bo08h10ucio8uni8@group.calendar.google.com', body=event).execute()

    print (event['id'])


if __name__ == '__main__':

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

    contest = get_atcoder_schedule()
    
    pre_saved = []
    with open('data/schedule.txt', mode='rt') as f:
        for d in f:
            pre_saved.append(d.replace('\n', ''))
    f.close()

    ## 各コンテスト名毎にループ
    for i in range(int(len(contest)/2)) :
        ## 前回のスケジュール取得時に既にカレンダーに追加済みでなければ
        if not(contest[2*i] in pre_saved) :
            event['summary'] = contest[2*i]
            event['start']['dateTime'] = contest[2*i+1].replace(" ", "T")
            ## コンテストの終了時間を計算 : begin 
            s = str(event['start']['dateTime']).replace("T", " ")
            t = dt.strptime(s, '%Y-%m-%d %H:%M:%S')
            if (t.hour==23) :
                t = str(t + datetime.timedelta(days=1, hours=1)).replace(" ", "T")
            else :
                t = str(t + datetime.timedelta(hours=1)).replace(" ", "T")
            event['end']['dateTime'] = t
            ## コンテストの終了時間を計算 : finish

            print (event['start']['dateTime'], event['end']['dateTime'], event['summary'])

            with open('data/schedule.txt', mode='a') as f :
                f.write(str(event['summary']))
                f.write("\n")

            main(event)
