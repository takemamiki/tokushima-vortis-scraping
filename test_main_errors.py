"""
test_main_errors.py
main.py の「失敗するはずのケース」のテスト（サイトにはアクセスしない）。

確かめること：
    1. 想定外のエラー（KeyError）が出ても、その試合だけ失敗にして次の試合へ進む
    2. 制約違反（IntegrityError）が出ても次へ進み、その試合は matches にも goals にも入らない
    3. 通信エラー（requests の ConnectionError）も次へ進む
    4. RuntimeError（昔の形のデータベースなど）は全体を止める

実行：python test_main_errors.py
"""

import os
import sqlite3
import tempfile

import requests

import main
import save_data
from fetch_jleague import MatchNotFinished


def make_match(game_id, goals):
    home = sum(1 for g in goals if g["club"] == "徳島")
    return {
        "game_id": game_id,
        "season": "2026-27",
        "section": 1,
        "match_date": "2026-10-24",
        "home_club": "徳島",
        "home_score": home,
        "away_club": "今治",
        "away_score": len(goals) - home,
        "goals": goals,
    }


def goal(scorer, minute, club="徳島"):
    return {"club": club, "scorer": scorer, "minute": minute,
            "added_time": 0, "is_own_goal": 0}


def setup(tmpdir, match_list, behaviors):
    """main.py の部品を、テスト用の偽物と一時的なデータベースに差し替える"""
    db = os.path.join(tmpdir, "test.db")
    main.WAIT_SECONDS = 0
    main.read_match_list = lambda: match_list
    main.is_already_saved = lambda gid: save_data.is_already_saved(gid, db)
    main.save_match_data = lambda m: save_data.save_match_data(m, db)

    def fake_fetch(year, number):
        b = behaviors[f"{year}{number}"]
        if isinstance(b, Exception):
            raise b
        return f"{year}{number}"  # html の代わりに game_id をそのまま渡す

    main.fetch_match_html = fake_fetch
    main.extract_payload = lambda html: html

    def fake_parse(payload, year, number):
        b = behaviors[payload]
        if callable(b):
            return b()
        return b

    main.parse_match = fake_parse
    return db


def count(db, sql, gid):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(sql, (gid,)).fetchone()[0]
    finally:
        conn.close()


def test_continue_after_errors():
    with tempfile.TemporaryDirectory() as tmp:
        def raise_keyerror():
            raise KeyError("scoreTime")

        def raise_not_finished():
            raise MatchNotFinished("2027022718: 試合が終わっていません（pre-game）")

        behaviors = {
            "2026000001": raise_keyerror,                                   # 想定外：KeyError
            "2026000002": make_match("2026000002",                          # 制約違反：同じ得点が2行
                                     [goal("山田", 10), goal("山田", 10)]),
            "2026000003": requests.ConnectionError("つながりません"),        # 通信エラー
            "2027022718": raise_not_finished,                               # 未開催
            "2026000005": make_match("2026000005", [goal("鈴木", 30)]),      # 普通の試合
        }
        match_list = [(gid[:4], gid[4:]) for gid in behaviors]
        db = setup(tmp, match_list, behaviors)

        main.main()  # 途中で止まらずに最後まで動くこと

        # 普通の試合だけ保存されている
        assert count(db, "SELECT COUNT(*) FROM matches WHERE game_id = ?", "2026000005") == 1
        assert count(db, "SELECT COUNT(*) FROM goals WHERE game_id = ?", "2026000005") == 1

        # 制約違反の試合は、matches にも goals にも入っていない（トランザクションで取り消し）
        assert count(db, "SELECT COUNT(*) FROM matches WHERE game_id = ?", "2026000002") == 0
        assert count(db, "SELECT COUNT(*) FROM goals WHERE game_id = ?", "2026000002") == 0

        # 失敗した試合は保存されていないので、次の実行で取りに行く対象になる
        for gid in ["2026000001", "2026000002", "2026000003"]:
            assert not save_data.is_already_saved(gid, db)
    print("OK: 想定外のエラー・制約違反・通信エラーのあとも次の試合へ進んだ")


def test_runtime_error_stops():
    with tempfile.TemporaryDirectory() as tmp:
        def raise_runtime():
            raise RuntimeError("昔の形のテーブルです")

        behaviors = {
            "2026000001": raise_runtime,
            "2026000002": make_match("2026000002", [goal("鈴木", 30)]),
        }
        match_list = [(gid[:4], gid[4:]) for gid in behaviors]
        db = setup(tmp, match_list, behaviors)

        try:
            main.main()
        except RuntimeError:
            pass
        else:
            raise AssertionError("RuntimeError で止まるはずが、最後まで動いた")

        # 止まったので、後ろの試合は保存されていない
        assert not save_data.is_already_saved("2026000002", db)
    print("OK: RuntimeError では全体が止まった")


if __name__ == "__main__":
    test_continue_after_errors()
    print("-" * 40)
    test_runtime_error_stops()
    print("-" * 40)
    print("全部のテストが通りました")
