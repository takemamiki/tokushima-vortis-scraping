## 次

- 試合番号を Jリーグ公式から自動で集める（B案）。match_list.txt を答え合わせに使う。sitemap.xml がヒントになるかもしれない
- 要確認：第4節の番号 082919 が vortis.jp の game 番号と同じだった。偶然か、両サイトで番号がそろっているのか
- win_draw_lose.sql の引き分けは「スコアが同じ試合」を全部数えている。徳島以外の試合を入れる前に、徳島の試合だけに絞る
- main.py / save_data.py のファイルの場所（match_list.txt、data/vortis.db）を、実行した場所ではなく main.py の隣を基準にする
- matplotlib でグラフにする（得点時間帯の分布など）

決めたこと・確認したことは docs/decisions.md に書く。
