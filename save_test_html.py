"""
save_test_html.py
テスト用に、確認に使う4試合の試合ページを data/ に保存する（最初の1回だけ実行すればよい）。
保存したHTMLは .gitignore で GitHub には上げない。
"""
import time

from fetch_jleague import fetch_match_html

# (URL の年, Jリーグ公式の番号)
TEST_MATCHES = [
    ("2026", "102412"),
    ("2026", "092613"),
    ("2026", "101718"),
    ("2026", "101719"),
]

for year, number in TEST_MATCHES:
    html = fetch_match_html(year, number)
    with open(f"data/jleague_{year}{number}.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("保存:", year, number)
    time.sleep(2)
