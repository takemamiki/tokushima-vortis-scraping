import json
import re
from datetime import datetime, timedelta, timezone

import requests

url = "https://www.jleague.jp/match/j2/2026/101015/"
headers = {"User-Agent": "Mozilla/5.0 (personal learning project)"}
res = requests.get(url, headers=headers, timeout=10)
res.encoding = "utf-8"

pattern = r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)'
chunks = re.findall(pattern, res.text)
payload = "".join(json.loads(c) for c in chunks)

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


def find_team(key):
    """得点者リストを持っているチームのデータを探す"""
    for pos, v in get_all_values(payload, key):
        if isinstance(v, dict) and "playerScoreList" in v:
            return pos, v
    return None, None


away_pos, away = find_team("awayTeam")
home_pos, home = find_team("homeTeam")

# awayTeam と homeTeam の間にある "$D…" の日付を探す
date_raw = None
for pos, v in get_all_values(payload, "date"):
    if isinstance(v, str) and v.startswith("$D") and away_pos < pos < home_pos:
        date_raw = v
        break

utc = datetime.fromisoformat(date_raw.replace("$D", "").replace("Z", "+00:00"))
jst = utc.astimezone(timezone(timedelta(hours=9)))
print("日時:", jst.strftime("%Y-%m-%d %H:%M"))

for side, team in [("ホーム", home), ("アウェイ", away)]:
    print(f"{side}: {team['name']} {team['score']}点")
    for p in team["playerScoreList"]:
        og = "（OG）" if p["ownGoal"] else ""
        print(f"  {p['scoreTime']} {p['name']}{og}")