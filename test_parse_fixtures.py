"""
test_parse_fixture.py
保存済みの試合ページ（data/jleague_*.html）を使って、fetch_jleague.py の parse_fixture を確かめる。
終わった試合4つと、まだやっていない試合1つ（2026112913）で試す。サイトにはアクセスしない。
2026112913 のHTMLは practice/probe_pregame.py を実行したときに保存されている。
"""
import os

from fetch_jleague import extract_payload, parse_fixture

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load(year, number):
    new_path = os.path.join(BASE_DIR, "data", f"jleague_{year}{number}.html")  # 新しいファイル名
    old_path = os.path.join(BASE_DIR, "data", f"jleague_{number}.html")        # 以前のファイル名
    path = new_path if os.path.exists(new_path) else old_path
    if not os.path.exists(path):
        raise FileNotFoundError(f"{new_path} がありません")
    with open(path, encoding="utf-8") as f:
        return parse_fixture(extract_payload(f.read()), year, number)


# (年, 番号, 節, 試合日, ホーム, アウェイ, 試合の状態)
CASES = [
    ("2026", "102412", 13, "2026-10-24", "藤枝MYFC", "徳島ヴォルティス", "post-game"),
    ("2026", "092613", 8, "2026-09-26", "徳島ヴォルティス", "栃木シティ", "post-game"),
    ("2026", "101718", 11, "2026-10-17", "ベガルタ仙台", "徳島ヴォルティス", "post-game"),
    ("2026", "101719", 11, "2026-10-17", "栃木シティ", "横浜FC", "post-game"),
    ("2026", "112913", 20, "2026-11-29", "いわきFC", "北海道コンサドーレ札幌", "pre-game"),
]

for year, number, section, match_date, home, away, game_type in CASES:
    r = load(year, number)
    assert r["game_id"] == f"{year}{number}"
    assert r["season"] == "2026-27", r["season"]
    assert r["section"] == section, r["section"]
    assert r["match_date"] == match_date, r["match_date"]
    assert r["home_club"] == home, r["home_club"]
    assert r["away_club"] == away, r["away_club"]
    assert r["game_type"] == game_type, r["game_type"]
    print(f"OK: {r['game_id']} 第{r['section']}節 {r['match_date']} {r['kickoff']} "
          f"{r['home_club']} 対 {r['away_club']}（{r['game_type']}）")

print("全部OK")
