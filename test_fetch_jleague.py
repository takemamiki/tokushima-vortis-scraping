"""
test_fetch_jleague.py
保存済みの試合ページ（data/jleague_*.html）を使って、fetch_jleague.py の parse_match を確かめる。
サイトにはアクセスしない。HTMLがなければ、先に save_test_html.py を実行する。
"""
import os

from fetch_jleague import extract_payload, parse_match, parse_score_time

# 得点時間の分け方
assert parse_score_time("28'") == (28, 0)
assert parse_score_time("90+2'") == (90, 2)
assert parse_score_time("45+1'") == (45, 1)


def load(year, number):
    """保存済みのHTMLを読み込んで parse_match にかける"""
    new_path = f"data/jleague_{year}{number}.html"  # 新しいファイル名
    old_path = f"data/jleague_{number}.html"        # 以前のファイル名
    path = new_path if os.path.exists(new_path) else old_path
    if not os.path.exists(path):
        raise FileNotFoundError(f"{new_path} がありません。先に save_test_html.py を実行してください")
    with open(path, encoding="utf-8") as f:
        return parse_match(extract_payload(f.read()), year, number)


def check_common(r, year, number, match_date):
    """どの試合でも成り立つこと"""
    assert r["game_id"] == f"{year}{number}"
    assert r["match_date"] == match_date
    assert r["season"] == "2026-27"
    assert isinstance(r["section"], int) and 1 <= r["section"] <= 38
    assert isinstance(r["home_score"], int) and isinstance(r["away_score"], int)
    assert len(r["goals"]) == r["home_score"] + r["away_score"]
    print(f"OK: {r['game_id']} 第{r['section']}節 {r['home_club']} {r['home_score']}-{r['away_score']} {r['away_club']}")


# 普通の試合
r = load("2026", "102412")
check_common(r, "2026", "102412", "2026-10-24")
assert (r["home_score"], r["away_score"]) == (0, 1)

# オウンゴール：得点が入ったチーム側に入っている
r = load("2026", "092613")
check_common(r, "2026", "092613", "2026-09-26")
og = [g for g in r["goals"] if g["is_own_goal"] == 1]
assert len(og) == 1
assert og[0]["club"] == "徳島ヴォルティス"

# 0-0：得点者リストが空
r = load("2026", "101718")
check_common(r, "2026", "101718", "2026-10-17")
assert r["goals"] == []

# アディショナルタイム・全角の正規化
r = load("2026", "101719")
check_common(r, "2026", "101719", "2026-10-17")
assert r["away_club"] == "横浜FC"
assert any(g["minute"] == 90 and g["added_time"] == 6 for g in r["goals"])

print("全部OK")
