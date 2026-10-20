-- 徳島の得点ランキング（オウンゴールは除く）
SELECT
  scorer,
  COUNT(*) AS goals
FROM goals
WHERE club = '徳島ヴォルティス'
  AND is_own_goal = 0
GROUP BY scorer
ORDER BY goals DESC, scorer;
