-- 徳島の得点を、試合ごとに一覧にする（goals と matches を JOIN）
SELECT
  substr(m.game_id, 1, 8) AS match_date,
  CASE WHEN m.home_club = '徳島ヴォルティス' THEN m.away_club ELSE m.home_club END AS opponent,
  g.scorer,
  g.minute,
  g.added_time
FROM goals AS g
JOIN matches AS m ON g.game_id = m.game_id
WHERE g.club = '徳島ヴォルティス'
ORDER BY m.game_id, g.minute, g.added_time;
