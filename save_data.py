"""
save_data.py
parse_match.py が抽出した試合データを、SQLite（data/vortis.db）に保存する。

役割：1試合ぶんのデータを、matches テーブルと goals テーブルにまとめて保存すること。
    HTMLからデータを取り出すのは、parse_match.pyの役目。

テーブル：
    matches … 1試合＝1行（スコアなど）
    goals   … 1得点＝1行（得点者・得点時間など）

前提（2026/10/19 に確認）：
    scorers / minutes は「ホームの得点 → アウェイの得点」の順に並んでいる。
    先頭から home_score 個がホームチームの得点、残りがアウェイチームの得点。

ルール：
    - matches と goals は1つのトランザクションでまとめて保存する（片方だけ入ることはない）。
    - 得点者の数とスコアの合計が合わない試合は、どちらにも保存せずに警告を出す。
    - 同じ game_id は二重に保存しない（PRIMARY KEY と INSERT OR IGNORE）。
    - match_date は、今は game_id の先頭8桁から作っている（暫定）。
"""

import os
import re
import sqlite3

DB_PATH = "data/vortis.db"
OWN_GOAL = "オウンゴール"

CREATE_MATCHES_SQL = """
CREATE TABLE IF NOT EXISTS matches (
    game_id    TEXT PRIMARY KEY,
    match_date TEXT,
    home_club  TEXT NOT NULL,
    away_club  TEXT NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    scorers    TEXT,
    minutes    TEXT
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
    (game_id, match_date, home_club, away_club, home_score, away_score, scorers, minutes)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

INSERT_GOAL_SQL = """
INSERT OR IGNORE INTO goals
    (game_id, club, scorer, minute, added_time, is_own_goal)
VALUES (?, ?, ?, ?, ?, ?)
"""

# 「90'+2」→ (90, 2)、「15'」→ (15, 0)
MINUTE_PATTERN = re.compile(r"(\d+)'(?:\+(\d+))?")


def _connect() -> sqlite3.Connection:
    """データベースに接続し、テーブルがなければ作る"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    with conn:
        conn.execute(CREATE_MATCHES_SQL)
        conn.execute(CREATE_GOALS_SQL)
        _add_match_date_column(conn)
    return conn


def _add_match_date_column(conn: sqlite3.Connection) -> None:
    """
    昔の matches テーブル（match_date 列がない）に列を足し、空欄を埋める。
    新しく作ったテーブルには最初から列があるので、何もしない。
    """
    columns = [row[1] for row in conn.execute("PRAGMA table_info(matches)")]
    if "match_date" not in columns:
        conn.execute("ALTER TABLE matches ADD COLUMN match_date TEXT")

    # game_id の先頭8桁「20261010」→「2026-10-10」
    conn.execute("""
        UPDATE matches
        SET match_date = substr(game_id, 1, 4) || '-' || substr(game_id, 5, 2) || '-' || substr(game_id, 7, 2)
        WHERE match_date IS NULL
    """)


def _to_match_date(game_id: str) -> str:
    """game_id の先頭8桁から日付（YYYY-MM-DD）を作る（暫定）"""
    return f"{game_id[0:4]}-{game_id[4:6]}-{game_id[6:8]}"


def _parse_minute(text: str) -> tuple[int, int]:
    """得点時間の文字列を (分, アディショナルタイム) に分ける"""
    m = MINUTE_PATTERN.fullmatch(text.strip())
    if m is None:
        raise ValueError(f"得点時間の形式が読めません: {text!r}")
    return int(m.group(1)), int(m.group(2) or 0)


def is_already_saved(game_id) -> bool:
    """matches テーブルに、指定した game_id が既にあるかを確認する"""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT 1 FROM matches WHERE game_id = ?", (str(game_id),)
        ).fetchone()
    finally:
        conn.close()
    return row is not None


def save_match_data(match_data: dict) -> bool:
    """
    試合データ（辞書）を、matches と goals にまとめて保存する。
    保存できたら True、スキップしたら False を返す。
    """
    game_id = str(match_data["game_id"])
    home_club = match_data["home_club"]
    away_club = match_data["away_club"]
    home_score = int(match_data["home_score"])
    away_score = int(match_data["away_score"])
    scorers = list(match_data["scorers"])
    minutes = list(match_data["minutes"])

    total = home_score + away_score
    if not (len(scorers) == len(minutes) == total):
        print(f"【警告】件数が合わないため保存しません: {game_id} "
              f"（スコア合計{total}、得点者{len(scorers)}、得点時間{len(minutes)}）")
        return False

    conn = _connect()
    try:
        with conn:  # ここから下は「全部成功」か「全部取り消し」のどちらか
            cur = conn.execute(INSERT_MATCH_SQL, (
                game_id,
                _to_match_date(game_id),
                home_club,
                away_club,
                home_score,
                away_score,
                str(scorers),  # 元の形も念のため残しておく
                str(minutes),
            ))
            if cur.rowcount == 0:
                print(f"既に保存済みのためスキップ: {game_id}")
                return False

            for i, (scorer, minute_text) in enumerate(zip(scorers, minutes)):
                club = home_club if i < home_score else away_club
                minute, added_time = _parse_minute(minute_text)
                is_own_goal = 1 if scorer == OWN_GOAL else 0
                conn.execute(INSERT_GOAL_SQL, (
                    game_id, club, scorer, minute, added_time, is_own_goal,
                ))
    finally:
        conn.close()

    return True


if __name__ == "__main__":
    from parse_match import match_data

    if save_match_data(match_data):
        print(f"データベースに保存しました: {DB_PATH}")
