-- 徳島ヴォルティスの今季の得点ランキング
-- オウンゴールは「得点が入ったチーム」に記録されているが、決めたのは相手の選手なので除く
SELECT
    g.scorer       AS 選手,
    COUNT(*)       AS 得点
FROM goals AS g
JOIN matches AS m ON m.game_id = g.game_id
WHERE m.season = '2026-27'
  AND g.club = '徳島ヴォルティス'
  AND g.is_own_goal = 0
GROUP BY g.scorer
ORDER BY 得点 DESC, 選手;
