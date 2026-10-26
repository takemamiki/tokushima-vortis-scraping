"""
main.py
find_vortis_schedule.py → fetch_match.py → parse_match.py → save_data.py を
1本につなげて、J2の終了済み試合を自動でSQLite（data/vortis.db）に保存する。

保存済みの試合は、試合ページを取りに行かずに飛ばす（公式サイトへのアクセスを減らすため）。
"""

import time
from urllib.parse import urlparse, parse_qs

from find_vortis_schedule import fetch_schedule_page, find_finished_j2_urls
from fetch_match import fetch_match_html, WAIT_SECONDS
from parse_match import parse_match
from save_data import save_match_data, is_already_saved

def extract_game_id(url: str) -> str:
    """
    試合結果ページのURLから、game=から始まる試合IDだけを取り出す。
    """
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)
    return query.get("game", [None])[0]


if __name__ == "__main__":
    soup = fetch_schedule_page()
    urls = find_finished_j2_urls(soup)

    print(f"見つかった試合数: {len(urls)}")

    saved_count = 0
    failed_ids = []
    for url in urls:
        game_id = extract_game_id(url)

        if is_already_saved(game_id):
            print(f"保存済みのため取得しません: {game_id}")
            continue

        print(f"取得中: {game_id}")

        try:
            html = fetch_match_html(url)
            match_data = parse_match(html)
        except ValueError as e:
            print(f"スキップしました: {game_id} ({e})")
            failed_ids.append(game_id)
            time.sleep(WAIT_SECONDS)
            continue
        
        match_data["game_id"] = game_id

        if save_match_data(match_data):
            saved_count += 1

        time.sleep(WAIT_SECONDS)

    print(f"完了しました（新しく保存した試合: {saved_count}）")
    
    if failed_ids:
        print(f"スキップした試合: {failed_ids} (次回の実行でもう一度取りに行きます) ")

