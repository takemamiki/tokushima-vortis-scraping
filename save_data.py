"""
save_data.py
parse_match.py が抽出した試合データを、CSVファイルに追記する。

役割：データをCSVに書き込み、蓄積していくこと。
    HTMLからデータを取り出すのは、parse_match.pyの役目。
"""

import csv
import os

CSV_PATH = "data/matches_2026-27.csv"

FIELDNAMES = ["game_id", "home_club", "away_club", "home_score", "away_score", "scorers", "minutes"]

def save_match_data(match_data: dict) -> None:
    """
    試合データ（辞書）を1行、CSVファイルに追記する。
    既に同じgame_idが保存済みの場合はスキップする。
    ファイルが存在しない場合は、見出し行も一緒に書き込む。
    """

    file_exists = os.path.exists(CSV_PATH) and os.path.getsize(CSV_PATH) > 0

    if file_exists and _is_already_saved(match_data["game_id"]):
        print(f"既に保存済みのためスキップ: {match_data['game_id']}")
        return

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)

        if not file_exists:
            writer.writeheader()

        writer.writerow(match_data)


def _is_already_saved(game_id) -> bool:
    """CSVに、指定したgame_idが既に存在するかを確認する"""
    with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["game_id"] == str(game_id):
                return True
    return False


if __name__ == "__main__":
    from parse_match import match_data

    save_match_data(match_data)
    print(f"CSVに保存しました: {CSV_PATH}")

