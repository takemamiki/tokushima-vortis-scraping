SELECT
    SUM(CASE WHEN(home_club = '徳島ヴォルティス' AND home_score > away_score)
              OR (away_club = '徳島ヴォルティス' AND away_score > home_score) THEN 1 ELSE 0 END) AS win,
    SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) AS draw,
    SUM(CASE WHEN(home_club = '徳島ヴォルティス' AND home_score < away_score)
              OR (away_club = '徳島ヴォルティス' AND away_score < home_score) THEN 1 ELSE 0 END) AS lose
FROM matches;             