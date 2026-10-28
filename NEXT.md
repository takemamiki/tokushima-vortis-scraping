## 次

- 確認に使った4試合（102412 普通／092613 OG／101718 0-0／101719 アディショナルタイム）を test_fetch_jleague.py に入れる
- fetch_jleague.py の home_score / away_score を int() でそろえる（未対応なら）
- jleague.jp の robots.txt と利用規約を確認する
- matches テーブルの構造を確認する
- game_id を「試合日の年 ＋ Jリーグ公式の番号」で作る。その前に、URL の年がシーズンを表すのか、番号がシーズンをまたいで重ならないかを確かめる
- section（節）列を足すか決める
- save_data.py で `PRAGMA foreign_keys = ON` を実行しているか確認する
- 既存の vortis.db をどうするか決める（vortis_old.db に名前を変えて残し、Jリーグ公式から作り直す案）

決めたこと・確認したことは docs/decisions.md に書く。
