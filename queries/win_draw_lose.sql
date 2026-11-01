-- 徳島ヴォルティスの勝ち・引き分け・負けの数
-- WHERE で徳島の試合だけに絞る（他チーム同士の引き分けを数えないため）
SELECT
    SUM(CASE WHEN (home_club = '徳島ヴォルティス' AND home_score > away_score)
              OR (away_club = '徳島ヴォルティス' AND away_score > home_score) THEN 1 ELSE 0 END) AS win,
    SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) AS draw,
    SUM(CASE WHEN (home_club = '徳島ヴォルティス' AND home_score < away_score)
              OR (away_club = '徳島ヴォルティス' AND away_score < home_score) THEN 1 ELSE 0 END) AS lose
FROM matches
WHERE home_club = '徳島ヴォルティス' OR away_club = '徳島ヴォルティス';
