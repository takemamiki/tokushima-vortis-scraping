"""
test_save_data.py
save_data.py を、使い捨てのデータベース（一時フォルダ）で確かめる。
本物の data/vortis.db には触らない。サイトにもアクセスしない。
"""
import os
import sqlite3
import tempfile

from save_data import save_match_data, is_already_saved


def make_match(game_id, home, hs, away, as_, goals, section=11):
    return {
        "game_id": game_id, "season": "2026-27", "section": section,
        "match_date": f"{game_id[:4]}-{game_id[4:6]}-{game_id[6:8]}",
        "home_club": home, "home_score": hs,
        "away_club": away, "away_score": as_,
        "goals": goals,
    }


def goal(club, scorer, minute, added=0, og=0):
    return {"club": club, "scorer": scorer, "minute": minute,
            "added_time": added, "is_own_goal": og}


tmp = tempfile.mkdtemp()
db = os.path.join(tmp, "test.db")

# 1. 普通の試合（0-1）
m = make_match("2026102412", "藤枝MYFC", 0, "徳島ヴォルティス", 1,
               [goal("徳島ヴォルティス", "選手A", 60)], section=13)
assert save_match_data(m, db) is True
assert is_already_saved("2026102412", db)

# 2. 同じ試合をもう一度 → スキップ、goals も増えない
assert save_match_data(m, db) is False

# 3. オウンゴール（得点が入ったチーム側）
m = make_match("2026092613", "徳島ヴォルティス", 3, "栃木シティ", 0, [
    goal("徳島ヴォルティス", "選手B", 10),
    goal("徳島ヴォルティス", "選手C", 30, og=1),
    goal("徳島ヴォルティス", "選手B", 80),
], section=8)
assert save_match_data(m, db) is True

# 4. 0-0
m = make_match("2026101718", "ベガルタ仙台", 0, "徳島ヴォルティス", 0, [])
assert save_match_data(m, db) is True

# 5. アディショナルタイム
m = make_match("2026101719", "栃木シティ", 1, "横浜FC", 1, [
    goal("栃木シティ", "選手D", 20),
    goal("横浜FC", "選手E", 90, added=6),
])
assert save_match_data(m, db) is True

# 6. 得点者の数が合わない → ValueError、何も保存されない
m = make_match("2026110101", "徳島ヴォルティス", 2, "相手", 0,
               [goal("徳島ヴォルティス", "選手F", 5)])
try:
    save_match_data(m, db)
    raise AssertionError("止まるはずが止まらなかった")
except ValueError as e:
    print("止まった（正しい）:", e)
assert not is_already_saved("2026110101", db)

# 中身の確認
conn = sqlite3.connect(db)
assert conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0] == 4
assert conn.execute("SELECT COUNT(*) FROM goals").fetchone()[0] == 6
assert conn.execute("SELECT COUNT(*) FROM goals WHERE is_own_goal = 1").fetchone()[0] == 1
assert conn.execute(
    "SELECT added_time FROM goals WHERE game_id = '2026101719' AND club = '横浜FC'"
).fetchone()[0] == 6
assert conn.execute(
    "SELECT section FROM matches WHERE game_id = '2026102412'"
).fetchone()[0] == 13
conn.close()

# 7. 昔の形のデータベース → 止まる
old_db = os.path.join(tmp, "old.db")
conn = sqlite3.connect(old_db)
conn.execute("CREATE TABLE matches (game_id TEXT PRIMARY KEY, scorers TEXT, minutes TEXT)")
conn.close()
try:
    is_already_saved("x", old_db)
    raise AssertionError("止まるはずが止まらなかった")
except RuntimeError as e:
    print("止まった（正しい）:", e)

print("全部OK")
