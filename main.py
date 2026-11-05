"""
main.py
match_list.txt に書いた試合を、Jリーグ公式サイトから順に取ってきて、
SQLite（data/vortis.db）に保存する。

流れ：
    match_list.txt を読む → 保存済みなら飛ばす → fetch_jleague.py で取得・解析
    → save_data.py で保存 → 2秒待つ → 次の試合

ルール：
    - 一覧の書き方がおかしい行があれば、サイトに1回もアクセスせずに止まる。
    - 保存済みの試合は、試合ページを取りに行かない（アクセスを減らすため）。
    - 試合が終わっていない（post-game 以外）試合は保存しない。
    - 1試合で失敗しても止まらずに次へ進み、最後に失敗した試合をまとめて表示する。
      通信エラー・データのエラー（想定内）も、それ以外のエラー（想定外）も同じく次へ進む。
      失敗した試合は何も保存されないので、次の実行でもう一度取りに行く。
    - ただし RuntimeError（昔の形のデータベースなど、全試合に関わる問題）は全体を止める。
"""

import os
import re
import time

import requests

from fetch_jleague import (
    MatchNotFinished,
    extract_payload,
    fetch_match_html,
    parse_match,
)
from save_data import is_already_saved, save_match_data

# どこから実行しても、このファイル（main.py）と同じフォルダを基準にする
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MATCH_LIST_PATH = os.path.join(BASE_DIR, "match_list.txt")
WAIT_SECONDS = 2

# 「2026 102412」の形（年4桁、半角スペース、番号6桁）
LINE_PATTERN = re.compile(r"(\d{4})\s+(\d{6})")


def read_match_list(path: str = MATCH_LIST_PATH) -> list[tuple[str, str]]:
    """
    試合の一覧を読み込んで [(年, 番号), ...] で返す。
    空行と # から始まる行は飛ばす。行の後ろの # 以降はメモとして無視する。
    書き方がおかしい行があれば ValueError（行番号つき）。
    """
    matches = []
    seen = set()
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            text = line.split("#")[0].strip()
            if not text:
                continue
            m = LINE_PATTERN.fullmatch(text)
            if m is None:
                raise ValueError(
                    f"{path} の {line_no} 行目が読めません: {line.rstrip()!r}"
                    "（「2026 102412」の形で書いてください）"
                )
            key = (m.group(1), m.group(2))
            if key in seen:
                print(f"【注意】{line_no} 行目は重複しているので飛ばします: {text}")
                continue
            seen.add(key)
            matches.append(key)
    return matches


def main() -> None:
    match_list = read_match_list()
    print(f"一覧の試合数: {len(match_list)}")

    saved_count = 0
    not_finished = []
    failed = []  # [(game_id, エラーの種類), ...]

    for year, number in match_list:
        game_id = f"{year}{number}"

        if is_already_saved(game_id):
            print(f"保存済みのため取得しません: {game_id}")
            continue

        print(f"取得中: {game_id}")
        try:
            html = fetch_match_html(year, number)
            match = parse_match(extract_payload(html), year, number)
            if save_match_data(match):
                saved_count += 1
                print(f"保存しました: {game_id} 第{match['section']}節 "
                      f"{match['home_club']} {match['home_score']}-"
                      f"{match['away_score']} {match['away_club']}")
        except MatchNotFinished as e:
            print(f"保存しません: {e}")
            not_finished.append(game_id)
        except RuntimeError:
            # 昔の形のデータベースなど、全試合に関わる問題。次へ進まず全体を止める
            raise
        except (requests.RequestException, ValueError) as e:
            # 想定内の失敗（通信エラー、データがおかしいと判断して止めたもの）
            print(f"失敗しました: {game_id}（{type(e).__name__}: {e}）")
            failed.append((game_id, type(e).__name__))
        except Exception as e:
            # 想定外の失敗（ページの形が変わった KeyError、制約違反の IntegrityError など）
            # 1試合だけの問題として記録し、次の試合へ進む
            print(f"【想定外】失敗しました: {game_id}（{type(e).__name__}: {e}）")
            failed.append((game_id, type(e).__name__))

        time.sleep(WAIT_SECONDS)

    print(f"完了しました（新しく保存した試合: {saved_count}）")
    if not_finished:
        print(f"まだ終わっていない試合: {not_finished}")
    if failed:
        print("失敗した試合（次の実行でもう一度取りに行きます）:")
        for game_id, error_type in failed:
            print(f"  {game_id}（{error_type}）")


if __name__ == "__main__":
    main()
