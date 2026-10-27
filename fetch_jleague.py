import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (personal learning project)"}


def fetch_match_html(match_id):
    """Jリーグ公式サイトから試合ページのHTMLを取ってくる"""
    url = f"https://www.jleague.jp/match/j2/2026/{match_id}/"
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    res.encoding = "utf-8"
    return res.text


def extract_payload(html):
    """self.__next_f.push の中身をつなげて1本の文字列にする"""
    pattern = r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)'
    chunks = re.findall(pattern, html)
    payload = "".join(json.loads(c) for c in chunks)
    return payload


decoder = json.JSONDecoder()


def get_all_values(text, key):
    """"key": の後ろにある値を、見つかった数だけ全部取り出す"""
    results = []
    for m in re.finditer(f'"{key}":', text):
        try:
            value, _ = decoder.raw_decode(text, m.end())
        except json.JSONDecodeError:
            continue
        results.append((m.start(), value))
    return results


def find_team(payload, key):
    """得点者リストを持っているチームのデータを探す"""
    for pos, v in get_all_values(payload, key):
        if isinstance(v, dict) and "playerScoreList" in v:
            return pos, v
    return None, None


def normalize(name):
    """全角の英数字を半角にそろえる（ＦＣ今治 → FC今治）"""
    return unicodedata.normalize("NFKC", name)

def parse_score_time(text):
    """
    得点時間を、分と追加時間に分ける。
    "28'"   → (28, 0)
    "90+2'" → (90, 2)
    """
    t = normalize(text).replace("'", "").strip()

    if "+" in t:
        minute, added = t.split("+")
        return int(minute), int(added)

    return int(t), 0

def parse_match(payload, match_id):
    """payload から日付・チーム名・スコア・得点者を取り出して dict で返す"""
    away_pos, away = find_team(payload, "awayTeam")
    home_pos, home = find_team(payload, "homeTeam")

    if home is None or away is None:
        raise ValueError(f"{match_id}: チームデータが見つかりません")

    # awayTeam と homeTeam の間にある "$D…" の日付を探す
    date_raw = None
    for pos, v in get_all_values(payload, "date"):
        if isinstance(v, str) and v.startswith("$D") and away_pos < pos < home_pos:
            date_raw = v
            break

    if date_raw is None:
        raise ValueError(f"{match_id}: 試合日が見つかりません")

    utc = datetime.fromisoformat(date_raw.replace("$D", "").replace("Z", "+00:00"))
    jst = utc.astimezone(timezone(timedelta(hours=9)))

    # 両チームの得点を、1得点＝1件のリストにまとめる
    goals = []
    for team in [home, away]:
        club = normalize(team["name"])
        for p in team["playerScoreList"]:
            goals.append({
                "club": club,
                "scorer": normalize(p["name"]),
                "minute": p["scoreTime"],
                "is_own_goal": p["ownGoal"],
            })

    return {
        "match_id": match_id,
        "match_date": jst.strftime("%Y-%m-%d"),
        "home_club": normalize(home["name"]),
        "home_score": home["score"],
        "away_club": normalize(away["name"]),
        "away_score": away["score"],
        "goals": goals,
    }


if __name__ == "__main__":
    match_id = "102412"
    html = fetch_match_html(match_id)
    payload = extract_payload(html)
    result = parse_match(payload, match_id)
    print(result)