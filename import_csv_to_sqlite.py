"""
import_csv_to_sqlite.py
matches_2026-27.csv の試合データを、SQLite（data/vortis.db）に取り込む。

役割：CSVに溜まった試合データを、データベースへ移すこと。
    game_id を PRIMARY KEY（主キー）にしているので、
    同じ試合を何回取り込んでも重複しない。

v1（A案）：scorers と minutes は CSV と同じ文字列のまま保存する。
          得点者を別テーブル（goals）に分けるのは次の段階。
"""

import csv
import sqlite3

CSV_PATH = "data/matches_2026-27.csv"
DB_PATH = "data/vortis.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS matches (
    game_id    TEXT PRIMARY KEY,
    home_club  TEXT NOT NULL,
    away_club  TEXT NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    scorers    TEXT,
    minutes    TEXT
)
"""

INSERT_SQL = """
INSERT OR IGNORE INTO matches
    (game_id, home_club, away_club, home_score, away_score, scorers, minutes)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""


def main() -> None:
    with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    conn = sqlite3.connect(DB_PATH)
    inserted = 0
    try:
        with conn:  # ブロックを抜けるときに自動でcommitされる
            conn.execute(CREATE_TABLE_SQL)
            for row in rows:
                cur = conn.execute(INSERT_SQL, (
                    row["game_id"],
                    row["home_club"],
                    row["away_club"],
                    int(row["home_score"]),
                    int(row["away_score"]),
                    row["scorers"],
                    row["minutes"],
                ))
                # 新しく追加できたら1、既にあって無視されたら0
                inserted += cur.rowcount
    finally:
        conn.close()

    print(f"CSV {len(rows)}行のうち、{inserted}行を新しく追加しました（{DB_PATH}）")


if __name__ == "__main__":
    main()
