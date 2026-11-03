"""
update_fixtures.py
Jリーグ公式サイトの match.xml（試合ページの一覧）から J2 の試合番号を集めて、
対戦表（data/vortis.db の fixtures テーブル）を作る・新しくする。

使い方（どのフォルダから実行してもよい）：
    python update_fixtures.py        … 必要な試合を全部見に行く
    python update_fixtures.py 3      … 試しに3試合だけ見に行く

流れ：
    match.xml を1回だけ取得 → j2/2026/ と j2/2027/ の番号だけ拾う
    → 見に行く必要がある試合だけ試合ページを取得 → fixtures に保存 → 2秒待つ → 次の試合

見に行く試合：
    - 対戦表にまだない試合
    - 対戦表にあるが、まだ終わっていない（post-game 以外）のに試合日が今日まで（今日を含む）の試合
      （今日の試合、延期で日付が変わった、または終わったのにまだ反映していない試合）

ルール：
    - 2026年と2027年以外の番号は拾わない（robots.txt で 2010〜2019年の試合ページは取得禁止のため）
    - 1試合で失敗しても止まらずに次へ進み、最後に失敗した試合をまとめて表示する
    - 最後に、徳島の終わった試合を match_list.txt と見比べて表示する（答え合わせ）
"""

import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests

from fetch_jleague import HEADERS, extract_payload, fetch_match_html, parse_fixture
from main import read_match_list
from save_data import DB_PATH, _connect, load_fixtures, save_fixture

SITEMAP_URL = "https://www.jleague.jp/match.xml"
ALLOWED_YEARS = {"2026", "2027"}
WAIT_SECONDS = 2
TEAM = "徳島ヴォルティス"

URL_PATTERN = re.compile(r"https://www\.jleague\.jp/match/j2/(\d{4})/(\d{6})/")
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
JST = timezone(timedelta(hours=9))


def fetch_sitemap() -> str:
    """match.xml を取ってくる"""
    res = requests.get(SITEMAP_URL, headers=HEADERS, timeout=30)
    res.raise_for_status()
    return res.content


def read_j2_numbers(xml_bytes) -> list[tuple[str, str]]:
    """match.xml から J2 の (年, 番号) を拾う。ALLOWED_YEARS 以外の年は飛ばす"""
    root = ET.fromstring(xml_bytes)
    numbers = []
    seen = set()
    for loc in root.findall("sm:url/sm:loc", NS):
        m = URL_PATTERN.fullmatch((loc.text or "").strip())
        if m is None or m.group(1) not in ALLOWED_YEARS:
            continue
        key = (m.group(1), m.group(2))
        if key not in seen:
            seen.add(key)
            numbers.append(key)
    return sorted(numbers)


def needs_check(game_id: str, known: dict, today: str) -> bool:
    """この試合を見に行く必要があるか"""
    if game_id not in known:
        return True
    f = known[game_id]
    return f["game_type"] != "post-game" and f["match_date"] <= today


def compare_with_match_list(db_path: str = DB_PATH) -> None:
    """徳島の終わった試合（対戦表）と match_list.txt を見比べて表示する"""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT game_id, section, match_date, home_club, away_club
            FROM fixtures
            WHERE game_type = 'post-game' AND (home_club = ? OR away_club = ?)
            ORDER BY match_date
            """,
            (TEAM, TEAM),
        ).fetchall()
    finally:
        conn.close()

    from_fixtures = {r[0] for r in rows}
    from_list = {f"{y}{n}" for y, n in read_match_list()}

    print(f"\n【答え合わせ】対戦表の徳島の終わった試合: {len(from_fixtures)}、"
          f"match_list.txt: {len(from_list)}")
    for game_id, section, match_date, home, away in rows:
        mark = "" if game_id in from_list else "  ← match_list.txt にない"
        print(f"  {game_id} 第{section}節 {match_date} {home} 対 {away}{mark}")
    for game_id in sorted(from_list - from_fixtures):
        print(f"  {game_id}  ← match_list.txt にあるが、対戦表の徳島の終わった試合にない")
    if from_fixtures == from_list:
        print("  一致しました")


def main(limit=None) -> None:
    today = datetime.now(JST).strftime("%Y-%m-%d")

    print("match.xml を取得します")
    numbers = read_j2_numbers(fetch_sitemap())
    print(f"J2（{'・'.join(sorted(ALLOWED_YEARS))}年）の試合番号: {len(numbers)}")

    known = load_fixtures()
    targets = [(y, n) for y, n in numbers if needs_check(f"{y}{n}", known, today)]
    print(f"見に行く試合: {len(targets)}（対戦表にある試合: {len(known)}）")
    if limit is not None:
        targets = targets[:limit]
        print(f"試しに {len(targets)} 試合だけ見に行きます")

    new_count = 0
    updated_count = 0
    failed = []

    for i, (year, number) in enumerate(targets, start=1):
        game_id = f"{year}{number}"
        try:
            html = fetch_match_html(year, number)
            fixture = parse_fixture(extract_payload(html), year, number)
            save_fixture(fixture, datetime.now(JST).isoformat(timespec="seconds"))
            if game_id in known:
                updated_count += 1
            else:
                new_count += 1
            print(f"[{i}/{len(targets)}] {game_id} 第{fixture['section']}節 "
                  f"{fixture['match_date']} {fixture['home_club']} 対 {fixture['away_club']}"
                  f"（{fixture['game_type']}）")
        except (requests.RequestException, ValueError) as e:
            print(f"[{i}/{len(targets)}] 失敗しました: {game_id}（{e}）")
            failed.append(game_id)

        time.sleep(WAIT_SECONDS)

    print(f"\n完了しました（新しく入れた試合: {new_count}、新しくした試合: {updated_count}）")
    if failed:
        print(f"失敗した試合: {failed}（次の実行でもう一度見に行きます）")

    compare_with_match_list()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
