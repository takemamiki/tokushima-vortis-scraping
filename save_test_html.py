import time

from fetch_jleague import fetch_match_html

for match_id in ["102412", "092613", "101718", "101719"]:
    html = fetch_match_html(match_id)
    with open(f"data/jleague_{match_id}.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("保存:", match_id)
    time.sleep(2)