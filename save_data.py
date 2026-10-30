"""
save_data.py
fetch_jleague.py の parse_match が返した試合データを、SQLite（data/vortis.db）に保存する。

役割：1試合ぶんのデータを、matches テーブルと goals テーブルにまとめて保存すること。
    ページからデータを取り出すのは fetch_jleague.py の役目。

テーブル：
    matches … 1試合＝1行（シーズン・節・試合日・スコア）
    goals   … 1得点＝1行（得点者・得点時間・オウンゴールか）

ルール（docs/decisions.md）：
    - 得点者は goals テーブルだけを正とする（matches に scorers / minutes 列は持たない）。
    - オウンゴールの club は「得点が入ったチーム」。
    - matches と goals は1つのトランザクションでまとめて保存する（片方だけ入ることはない）。
    - チームごとの得点者の数がスコアと合わない試合は、どちらにも保存しない。
    - 同じ game_id は二重に保存しない（PRIMARY KEY と INSERT OR IGNORE）。
    - 接続ごとに PRAGMA foreign_keys = ON を実行する。
"""

import os
import sqlite3

DB_PATH = "data/vortis.db"

CREATE_MATCHES_SQL = """
CREATE TABLE IF NOT EXISTS matches (
    game_id    TEXT    PRIMARY KEY,
    season     TEXT    NOT NULL,
    section    INTEGER NOT NULL,
    match_date TEXT    NOT NULL,
    home_club  TEXT    NOT NULL,
    away_club  TEXT    NOT NULL,
    home_score INTEGER NOT NULL,
    away_score INTEGER NOT NULL
)
"""

CREATE_GOALS_SQL = """
CREATE TABLE IF NOT EXISTS goals (
    goal_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     TEXT    NOT NULL REFERENCES matches(game_id),
    club        TEXT    NOT NULL,
    scorer      TEXT    NOT NULL,
    minute      INTEGER NOT NULL,
    added_time  INTEGER NOT NULL DEFAULT 0,
    is_own_goal INTEGER NOT NULL DEFAULT 0,
    UNIQUE (game_id, club, scorer, minute, added_time)
)
"""

INSERT_MATCH_SQL = """
INSERT OR IGNORE INTO matches
    (game_id, season, section, match_date, home_club, away_club, home_score, away_score)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

INSERT_GOAL_SQL = """
INSERT INTO goals
    (game_id, club, scorer, minute, added_time, is_own_goal)
VALUES (?, ?, ?, ?, ?, ?)
"""


def _connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    """データベースに接続し、テーブルがなければ作る"""
    folder = os.path.dirname(db_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    with conn:
        conn.execute(CREATE_MATCHES_SQL)
        conn.execute(CREATE_GOALS_SQL)
    _check_new_layout(conn, db_path)
    return conn


def _check_new_layout(conn: sqlite3.Connection, db_path: str) -> None:
    """
    昔の形（vortis.jp 時代）の matches テーブルだったら止める。
    CREATE TABLE IF NOT EXISTS は、同じ名前のテーブルがあると何もしないため。
    """
    columns = {row[1] for row in conn.execute("PRAGMA table_info(matches)")}
    if "season" not in columns or "scorers" in columns:
        conn.close()
        raise RuntimeError(
            f"{db_path} は昔の形のテーブルです。"
            "vortis_old.db などに名前を変えてから、もう一度実行してください"
        )


def is_already_saved(game_id, db_path: str = DB_PATH) -> bool:
    """matches テーブルに、指定した game_id が既にあるかを確認する"""
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM matches WHERE game_id = ?", (str(game_id),)
        ).fetchone()
    finally:
        conn.close()
    return row is not None


def _check_goals(match: dict) -> None:
    """チームごとの得点者の数がスコアと合うか確かめる（合わなければ ValueError）"""
    home_goals = sum(1 for g in match["goals"] if g["club"] == match["home_club"])
    away_goals = sum(1 for g in match["goals"] if g["club"] == match["away_club"])
    other = len(match["goals"]) - home_goals - away_goals

    if other or home_goals != match["home_score"] or away_goals != match["away_score"]:
        raise ValueError(
            f"{match['game_id']}: 得点者の数がスコアと合いません"
            f"（ホーム {home_goals}/{match['home_score']}、"
            f"アウェイ {away_goals}/{match['away_score']}、どちらでもない {other}）"
        )


def save_match_data(match: dict, db_path: str = DB_PATH) -> bool:
    """
    試合データ（fetch_jleague.parse_match の戻り値）を、matches と goals にまとめて保存する。
    保存できたら True、保存済みでスキップしたら False を返す。
    得点者の数がスコアと合わない場合は ValueError（何も保存しない）。
    """
    _check_goals(match)

    conn = _connect(db_path)
    try:
        with conn:  # ここから下は「全部成功」か「全部取り消し」のどちらか
            cur = conn.execute(INSERT_MATCH_SQL, (
                str(match["game_id"]),
                match["season"],
                int(match["section"]),
                match["match_date"],
                match["home_club"],
                match["away_club"],
                int(match["home_score"]),
                int(match["away_score"]),
            ))
            if cur.rowcount == 0:
                print(f"既に保存済みのためスキップ: {match['game_id']}")
                return False

            for g in match["goals"]:
                conn.execute(INSERT_GOAL_SQL, (
                    str(match["game_id"]),
                    g["club"],
                    g["scorer"],
                    int(g["minute"]),
                    int(g["added_time"]),
                    int(g["is_own_goal"]),
                ))
    finally:
        conn.close()

    return True
