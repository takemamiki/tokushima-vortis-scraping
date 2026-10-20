"""
build_goals_table.py
matches テーブルの scorers / minutes を分解して、goals テーブル（1得点＝1行）を作る。

役割：1つのマスに詰め込まれていた得点者と得点時間を、
    SQLで集計・JOINしやすい形に並べ直すこと。

前提（2026/10/19 に確認）：
    scorers / minutes は「ホームの得点 → アウェイの得点」の順に並んでいる。
    先頭から home_score 個がホームチームの得点、残りがアウェイチームの得点。

ルール：
    - club は「得点が入ったチーム」。オウンゴールも、得をしたチームの得点として数える。
    - 90'+2 のようなアディショナルタイムは、minute=90 / added_time=2 に分ける。
    - 件数が合わない試合（得点者の数 ≠ スコアの合計）は、取り込まずに警告を出す。
"""

import ast
import re
import sqlite3

DB_PATH = "data/vortis.db"
OWN_GOAL = "オウンゴール"

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

INSERT_GOAL_SQL = """
INSERT OR IGNORE INTO goals
    (game_id, club, scorer, minute, added_time, is_own_goal)
VALUES (?, ?, ?, ?, ?, ?)
"""

# 「90'+2」→ (90, 2)、「15'」→ (15, 0)
MINUTE_PATTERN = re.compile(r"(\d+)'(?:\+(\d+))?")


def parse_minute(text: str) -> tuple[int, int]:
    """得点時間の文字列を (分, アディショナルタイム) に分ける"""
    m = MINUTE_PATTERN.fullmatch(text.strip())
    if m is None:
        raise ValueError(f"得点時間の形式が読めません: {text!r}")
    return int(m.group(1)), int(m.group(2) or 0)


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    inserted = 0
    skipped_games = []
    try:
        with conn:
            conn.execute(CREATE_GOALS_SQL)
            rows = conn.execute(
                "SELECT game_id, home_club, away_club, home_score, away_score, scorers, minutes "
                "FROM matches"
            ).fetchall()

            for game_id, home_club, away_club, home_score, away_score, scorers_text, minutes_text in rows:
                scorers = ast.literal_eval(scorers_text)  # "['A', 'B']" → ['A', 'B']
                minutes = ast.literal_eval(minutes_text)

                total = home_score + away_score
                if not (len(scorers) == len(minutes) == total):
                    skipped_games.append(game_id)
                    print(f"【警告】件数が合わないためスキップ: {game_id} "
                          f"（スコア合計{total}、得点者{len(scorers)}、得点時間{len(minutes)}）")
                    continue

                for i, (scorer, minute_text) in enumerate(zip(scorers, minutes)):
                    club = home_club if i < home_score else away_club
                    minute, added_time = parse_minute(minute_text)
                    is_own_goal = 1 if scorer == OWN_GOAL else 0
                    cur = conn.execute(INSERT_GOAL_SQL, (
                        game_id, club, scorer, minute, added_time, is_own_goal,
                    ))
                    inserted += cur.rowcount
    finally:
        conn.close()

    print(f"{len(rows)}試合を確認し、{inserted}件の得点を新しく追加しました（{DB_PATH}）")
    if skipped_games:
        print(f"スキップした試合: {', '.join(skipped_games)}")


if __name__ == "__main__":
    main()
