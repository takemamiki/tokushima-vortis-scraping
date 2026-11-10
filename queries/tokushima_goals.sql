-- 徳島の得点を、試合ごとに一覧にする（goals と matches を JOIN）
-- オウンゴールは決めた選手名のうしろに「（OG）」を付けて区別する
-- goals には season 列がないので、matches の season で今季に絞る
SELECT
  m.match_date AS 試合日,
  CASE WHEN m.home_club = '徳島ヴォルティス' THEN m.away_club ELSE m.home_club END AS 相手,
  CASE WHEN g.is_own_goal = 1 THEN g.scorer || '（OG）' ELSE g.scorer END AS 選手,
  g.minute     AS 分,
  g.added_time AS 追加時間
FROM goals AS g
JOIN matches AS m ON g.game_id = m.game_id
WHERE m.season = '2026-27'
  AND g.club = '徳島ヴォルティス'
ORDER BY m.match_date, g.minute, g.added_time;
