-- 徳島ヴォルティスの今季の勝敗と勝ち点
-- 勝ち＝3点、引き分け＝1点、負け＝0点
WITH t AS (
    SELECT
        CASE WHEN home_club = '徳島ヴォルティス' THEN home_score ELSE away_score END AS gf,
        CASE WHEN home_club = '徳島ヴォルティス' THEN away_score ELSE home_score END AS ga
    FROM matches
    WHERE season = '2026-27'
      AND (home_club = '徳島ヴォルティス' OR away_club = '徳島ヴォルティス')
)
SELECT
    COUNT(*)                                   AS 試合,
    SUM(gf > ga)                               AS 勝,
    SUM(gf = ga)                               AS 分,
    SUM(gf < ga)                               AS 敗,
    SUM(gf)                                    AS 得点,
    SUM(ga)                                    AS 失点,
    SUM(gf) - SUM(ga)                          AS 得失点差,
    SUM(CASE WHEN gf > ga THEN 3 WHEN gf = ga THEN 1 ELSE 0 END) AS 勝ち点
FROM t;
