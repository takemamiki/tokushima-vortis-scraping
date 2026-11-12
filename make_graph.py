"""
make_graph.py
queries/points_by_section.sql の結果を、節ごとの累計勝ち点の折れ線グラフにして保存する。

入力  : data/vortis.db と queries/points_by_section.sql
出力  : output/points_by_section.png
止まる: DBがない / 結果が0行 / 節の順番がおかしい
"""

import os
import sqlite3

import matplotlib
matplotlib.use("Agg")  # 画面にウィンドウを出さず、ファイルに保存するだけにする
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# main.py と同じく、このファイルがあるフォルダを基準に場所を決める
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "vortis.db")
SQL_PATH = os.path.join(BASE_DIR, "queries", "points_by_section.sql")
OUT_DIR = os.path.join(BASE_DIR, "output")
OUT_PATH = os.path.join(OUT_DIR, "points_by_section.png")

# 日本語が「□□□」にならないように、Windows に入っている游ゴシックを使う
plt.rcParams["font.family"] = "Yu Gothic"


def load_rows():
    """SQLファイルを読み込んで実行し、1行を {列名: 値} の辞書にして返す"""
    # sqlite3.connect() はファイルがないと空のDBを勝手に作るので、先に確かめる
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"DBが見つかりません: {DB_PATH}")

    with open(SQL_PATH, encoding="utf-8") as f:
        sql = f.read()

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(sql)
        names = [d[0] for d in cur.description]  # SQLで AS を付けた列名（節、累計勝ち点…）
        rows = [dict(zip(names, r)) for r in cur.fetchall()]
    finally:
        conn.close()
    return rows


def main():
    rows = load_rows()
    if not rows:
        raise SystemExit("結果が0行です。グラフは作りません（SQLの season を確認）")

    sections = [int(r["節"]) for r in rows]
    points = [r["累計勝ち点"] for r in rows]

    # 節が 1, 10, 11, 2 … のように並んでいたら、累計がずれているので止める
    if sections != sorted(sections):
        raise SystemExit(f"節の順番がおかしいです: {sections}")

    os.makedirs(OUT_DIR, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(sections, points, marker="o")
    ax.set_title(f"徳島ヴォルティス 節ごとの累計勝ち点（第{sections[-1]}節時点）")
    ax.set_xlabel("節")
    ax.set_ylabel("累計勝ち点")
    ax.set_xticks(sections)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=150)
    plt.close(fig)

    print(f"保存しました: {OUT_PATH}")
    print(f"第{sections[-1]}節時点の累計勝ち点: {points[-1]}")


if __name__ == "__main__":
    main()
