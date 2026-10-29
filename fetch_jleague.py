import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (personal learning project)"}


class MatchNotFinished(Exception):
    """試合がまだ終わっていない（post-game ではない）ときに出すエラー"""


def fetch_match_html(year, number):
    """Jリーグ公式サイトから試合ページのHTMLを取ってくる

    year   : URL の年（＝試合日の年）。例 "2027"
    number : Jリーグ公式の6桁の番号。例 "022718"
    """
    url = f"https://www.jleague.jp/match/j2/{year}/{number}/"
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


def get_game_type(payload, game_id):
    """試合の状態（"pre-game" / "post-game" など）を取り出す

    "type": の値のうち "-game" で終わるものを探す。
    見つからない、または違う値が混ざっている場合は止める。
    """
    types = {
        v for _, v in get_all_values(payload, "type")
        if isinstance(v, str) and v.endswith("-game")
    }
    if len(types) != 1:
        raise ValueError(f"{game_id}: 試合の状態を1つに決められません（{types}）")
    return types.pop()


def get_section(payload, game_id):
    """"section": "第13節" から、数字の 13 を取り出す"""
    sections = set()
    for _, v in get_all_values(payload, "section"):
        if isinstance(v, str):
            m = re.fullmatch(r"第(\d+)節", normalize(v).strip())
            if m:
                sections.add(int(m.group(1)))
    if len(sections) != 1:
        raise ValueError(f"{game_id}: 節を1つに決められません（{sections}）")
    return sections.pop()


def season_start_from_date(match_date):
    """試合日からシーズンの開始年を計算する（仮ルール：7月以降はその年、6月以前は前の年）"""
    return match_date.year if match_date.month >= 7 else match_date.year - 1


def parse_match(payload, year, number):
    """payload から試合データを取り出して dict で返す

    試合が終わっていない場合は MatchNotFinished を出す（保存しないため）。
    """
    game_id = f"{year}{number}"

    # 1. 試合が終わっているか（post-game 以外は保存しない）
    game_type = get_game_type(payload, game_id)
    if game_type != "post-game":
        raise MatchNotFinished(f"{game_id}: 試合が終わっていません（{game_type}）")

    # 2. チームデータ
    away_pos, away = find_team(payload, "awayTeam")
    home_pos, home = find_team(payload, "homeTeam")

    if home is None or away is None:
        raise ValueError(f"{game_id}: チームデータが見つかりません")

    # 3. 試合日（awayTeam と homeTeam の間にある "$D…" の日付）
    date_raw = None
    for pos, v in get_all_values(payload, "date"):
        if isinstance(v, str) and v.startswith("$D") and away_pos < pos < home_pos:
            date_raw = v
            break

    if date_raw is None:
        raise ValueError(f"{game_id}: 試合日が見つかりません")

    utc = datetime.fromisoformat(date_raw.replace("$D", "").replace("Z", "+00:00"))
    jst = utc.astimezone(timezone(timedelta(hours=9)))

    # URL の年と試合日の年が一致するか
    if str(jst.year) != str(year):
        raise ValueError(f"{game_id}: URL の年（{year}）と試合日（{jst:%Y-%m-%d}）が合いません")

    # 4. シーズン（seasonYear と、試合日からの計算の2つで確かめる）
    years = get_all_values(payload, "seasonYear")
    if not years:
        raise ValueError(f"{game_id}: seasonYear が見つかりません")
    _, season_year = min(years, key=lambda x: abs(x[0] - away_pos))
    season_year = int(season_year)

    if season_year != season_start_from_date(jst):
        raise ValueError(
            f"{game_id}: シーズンが合いません"
            f"（seasonYear={season_year}、試合日から計算={season_start_from_date(jst)}）"
        )
    season = f"{season_year}-{(season_year + 1) % 100:02d}"

    # 5. 節
    section = get_section(payload, game_id)

    # 6. 両チームの得点を、1得点＝1件のリストにまとめる
    goals = []
    for team in [home, away]:
        club = normalize(team["name"])
        for p in team["playerScoreList"]:
            minute, added_time = parse_score_time(p["scoreTime"])
            goals.append({
                "club": club,
                "scorer": normalize(p["name"]),
                "minute": minute,
                "added_time": added_time,
                "is_own_goal": int(p["ownGoal"]),
            })

    home_club = normalize(home["name"])
    home_goals = sum(1 for g in goals if g["club"] == home_club)
    away_goals = len(goals) - home_goals
    if home_goals != int(home["score"]) or away_goals != int(away["score"]):
        raise ValueError(
            f"{game_id}: 得点者の数がスコアと合いません"
            f"（ホーム {home_goals}/{home['score']}、アウェイ {away_goals}/{away['score']}）"
        )

    return {
        "game_id": game_id,
        "season": season,
        "section": section,
        "match_date": jst.strftime("%Y-%m-%d"),
        "home_club": home_club,
        "home_score": int(home["score"]),
        "away_club": normalize(away["name"]),
        "away_score": int(away["score"]),
        "goals": goals,
    }


if __name__ == "__main__":
    import time

    # 確認用の試合（年, 番号, 内容）
    TEST_MATCHES = [
        ("2026", "102412", "普通"),
        ("2026", "092613", "OG"),
        ("2026", "101718", "0-0"),
        ("2026", "101719", "アディショナルタイム"),
        ("2027", "022718", "未開催（止まるのが正しい）"),
    ]

    for year, number, label in TEST_MATCHES:
        print(f"■ {year}/{number}（{label}）")
        try:
            html = fetch_match_html(year, number)
            payload = extract_payload(html)
            result = parse_match(payload, year, number)
            print(result)
        except MatchNotFinished as e:
            print("保存しない:", e)
        except Exception as e:
            print("エラー:", e)
        print("-" * 40)
        time.sleep(2)
