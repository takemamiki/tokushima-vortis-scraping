-- 徳島の得点を、試合ごとに一覧にする（goals と matches を JOIN）
-- オウンゴールは決めた選手名のうしろに「（OG）」を付けて区別する
SELECT
  m.match_date,
  CASE WHEN m.home_club = '徳島ヴォルティス' THEN m.away_club ELSE m.home_club END AS opponent,
  CASE WHEN g.is_own_goal = 1 THEN g.scorer || '（OG）' ELSE g.scorer END AS scorer,
  g.minute,
  g.added_time
FROM goals AS g
JOIN matches AS m ON g.game_id = m.game_id
WHERE g.club = '徳島ヴォルティス'
ORDER BY m.match_date, g.minute, g.added_time;