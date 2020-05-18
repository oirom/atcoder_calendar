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


if __name__ == '__main__':
    
    elems = get_atcoder_schedule()
    print(elems)
