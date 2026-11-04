# 設計の決定メモ（decisions.md）

決めたことを1行ずつ残す。翌日の作業はこのファイルを前提に始める。

## データベース

- 2026-10-20：保存先は CSV をやめて SQLite（data/vortis.db）に一本化する
- 2026-10-27：得点者は goals テーブルだけを正とする。matches の scorers / minutes 列は使わない（→ 2026-10-29 に列ごとなくすと変更）
- 2026-10-28：オウンゴールの club は「得点が入ったチーム」を入れる（オウンゴールした選手の所属チームではない）。club ごとの得点数が試合のスコアと一致するようにするため
- 2026-10-28：goals の外部キー（REFERENCES matches）は、接続ごとに `PRAGMA foreign_keys = ON` を実行しないとチェックされない（→ 2026-10-29 に対応済み）

## Jリーグ公式のデータで確認したこと（2026-10-28）

- オウンゴールは、最初から「得点が入ったチーム」の得点者リストに入っている（092613 で確認）。club を入れ替える処理は不要
- 0-0 の試合は、両チームとも得点者リストが空で来る（101718 で確認）
- 得点時間は "28'" や "90+6'" の形で来る。parse_score_time で minute と added_time に分ける（101719 で確認）
- チーム名に全角英字が入ることがある（横浜ＦＣ）。normalize で半角にそろえる
- 得点者リストはホーム→アウェイの順で、時間順ではない
- parse_match では、チームごとに得点者の数とスコアが一致するかを確かめ、合わなければ ValueError で止める

## データの取得元

- 2026-10-28：取得元を Jリーグ公式サイト（jleague.jp）に一本化する。vortis.jp からの取得はやめる。同じ試合が2つの番号で二重に保存されるのを防ぐため、また徳島以外の J2 チームにも広げるため
- 2026-10-28：既存の徳島の試合も Jリーグ公式から取り直す
- 2026-10-29：jleague.jp の robots.txt と利用規約を確認し、問題なしと判断（10-30 の項も参照）

## game_id

- 2026-10-27：Jリーグ公式の試合の game_id は「試合日の年 ＋ Jリーグ公式の番号」で作る方針（"2026" の決め打ちは年をまたぐと壊れるため）
- （2026-10-29 に確認済み。下の「game_id の作り方を確定」を参照）

## 未決定

- （vortis.jp 用のコードの扱いは 2026-10-30 に決定：下の項を参照）
- （既存の vortis.db の扱いは 2026-10-30 に決定：vortis_old.db として残し、Jリーグ公式から作り直した）

## 2026-10-29 game_id の作り方を確定

- URL の年は「試合日の年」（シーズンではない）。例：2026-27シーズン第24節 → /match/j2/2027/022718/
- 番号は「月日4桁＋2桁」。毎年同じ番号が出うるので、game_id = 試合日の年 ＋ 番号（例：2027022718）
- 試合日が未確定（「2/27 or 2/28」）の試合は番号が変わる可能性がある → 保存は試合終了後のみ
- 節（第◯節）は試合ページから取得できる。シーズンは URL にないので、必要なら別の列にする

## 2026-10-29 外部キーのチェックを有効にした

- save_data.py の _connect() に `PRAGMA foreign_keys = ON` を追加（SQLiteは初期設定でオフ、接続ごとに必要）
- check_fk.py で確認：PRAGMA foreign_keys = 1、存在しない game_id の goals への INSERT が「FOREIGN KEY constraint failed」で止まることを確認
## 2026-10-30 Jリーグ公式から DB を作り直した

- jleague.jp の robots.txt と利用規約は 2026-10-29 に確認済み（問題なし）。10-30 に robots.txt を再確認：`/match/*/201*`（2010〜2019年の試合ページ）は取得禁止。2020年以降の /match/j2/ は対象外で取得可
- matches テーブルの列は game_id / season / section / match_date / home_club / away_club / home_score / away_score。scorers / minutes 列はなくした（得点者は goals だけを正とする）
- save_data.py は fetch_jleague.parse_match の戻り値をそのまま保存する。昔の形（scorers 列あり）の DB を開いたら止まる
- goals の INSERT は OR IGNORE を外した。二重保存は matches 側で防ぎ、goals で重なったらエラーで止めて全部取り消す
- 取得する試合は、当面 match_list.txt に手で書く（A案）。1行1試合「年 番号」。試合が終わってから1行足して python main.py を実行する
- 古い DB は data/vortis_old.db として手元に残す（GitHub には上げない）
- 作り直した DB を確認：13試合（第1〜13節）、5勝2分6敗、goals 24件（徳島11・相手13）。match_list.txt に手で書いたスコアと一致
- SQL の文字列は '（シングルクォート）で囲む。"（ダブル）は本来、列やテーブルの名前に使う記号
- 2026-10-30：使わなくなったファイル（fetch_match.py / parse_match.py / find_vortis_schedule.py / check_fk.py / check_jleague.py / probe_keys.py / probe_match.py）は practice/ に移す（B案）。practice/ は .gitignore 済みなので GitHub からは消え、手元には残る

## 2026-11-01 ファイルの場所と勝敗の数え方を直した

- main.py / save_data.py は、実行した場所ではなく、それぞれのファイルと同じフォルダを基準に match_list.txt と data/vortis.db を探す（os.path.abspath(__file__) を使う）。別のフォルダから実行しても、そのフォルダに data/ は作られないことを確認
- queries/win_draw_lose.sql に WHERE を足し、徳島の試合だけを数える。他チーム同士の引き分けが混ざらないことを確認（今の DB では 5勝2分6敗のまま）
- test_fetch_jleague.py と save_test_html.py は、まだ実行した場所を基準に data/ を探す（リポジトリのフォルダで実行すること）

## 2026-11-02 試合番号を match.xml から集める（B案）

- jleague.jp の robots.txt を再確認：/match/ の取得禁止は `/match/*/201*`（2010〜2019年）だけで変わりなし。Sitemap は https://www.jleague.jp/sitemap.xml
- sitemap.xml は目次で、試合ページの一覧は https://www.jleague.jp/match.xml。1件ごとに試合ページのURL（大会・年・6桁の番号）と lastmod があるだけで、チーム名は載っていない
- lastmod は一覧を作り直した時刻でそろって書き換わるため、試合日には使えない
- match.xml の j2/2026 は220件（2026-11-02時点）。2月・5月は0件、8月40・11月60・12月20件。まだやっていない試合も、日程が決まった分は載っている
- まだやっていない試合（pre-game）のページにも、節・試合日・ホーム・アウェイが載っていることを確認（2026112913 第20節 いわきFC 対 北海道コンサドーレ札幌、practice/probe_pregame.py で確認）
- J2の全試合の対戦表を作る（A案）。fixtures テーブル（game_id / season / section / match_date / kickoff / home_club / away_club / game_type / checked_at）を data/vortis.db に置く
- update_fixtures.py：match.xml から j2/2026・j2/2027 の番号だけ拾う（それ以外の年は robots.txt の都合で拾わない）。対戦表にない試合と、まだ終わっていないのに試合日が過ぎた試合（延期など）だけ見に行く。2秒待つ。最後に match_list.txt と答え合わせを表示する
- fetch_jleague.py に parse_fixture を追加（試合の状態に関係なくチームを探す。得点者は取らない）。parse_match は変えていない
- 進め方：今回は対戦表まで。main.py を対戦表から選ぶ形に変えるのは、答え合わせが一致してから（A案）
- 2026-11-02 本番の実行結果：match.xml の J2（2026・2027年）は380件（38節×10試合、シーズン全部の日程が載っている）。380件すべて失敗なしで対戦表に入った。SQL で確認：全380試合、どの節も10試合、徳島は38試合
- 答え合わせで、match_list.txt に書き忘れていた第14節（2026103121 徳島ヴォルティス 対 横浜FC、10/31）が見つかった。match_list.txt に足して main.py で保存し、答え合わせは14試合で「一致しました」
- 弱点：まだ先の試合の日程が前倒しになった場合など、試合日が過ぎる前の変更は拾わない。対戦表を使い始めてから様子を見る

## 2026-11-03 今日の試合も見直す

- update_fixtures.py の見直しの条件を「試合日が今日より前」から「今日まで（今日を含む）」に変えた（B案）。試合が終わった日のうちに対戦表を post-game にできる
- 試合前に実行しても「まだ終わっていない」のまま残るだけで、次の実行でもう一度見に行く

## 2026-11-04 過去のコミットに残る HTML の扱い

- コミット 21e483f（8/31）に、保存した HTML が3つ残っている（jleague.jp 2つ、vortis.jp 1つ）
- 今のファイルからは 10/20 に外し済み（5e7f933）。.gitignore で data/*.html は除外している
- 履歴の書き直し（git filter-repo と強制プッシュ）はしない（A案）。手間と、取り返しのつかない操作の危なさを考えて判断
- 今後、取ってきたページを丸ごと保存するときは、最初から .gitignore の対象の場所に置く