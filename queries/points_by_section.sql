-- 徳島ヴォルティスの節ごとの結果と、勝ち点の積み上げ（グラフの元データ）
WITH t AS (
    SELECT
        section,
        match_date,
        CASE WHEN home_club = '徳島ヴォルティス' THEN away_club  ELSE home_club  END AS 相手,
        CASE WHEN home_club = '徳島ヴォルティス' THEN 'H' ELSE 'A' END          AS HA,
        CASE WHEN home_club = '徳島ヴォルティス' THEN home_score ELSE away_score END AS gf,
        CASE WHEN home_club = '徳島ヴォルティス' THEN away_score ELSE home_score END AS ga
    FROM matches
    WHERE season = '2026-27'
      AND (home_club = '徳島ヴォルティス' OR away_club = '徳島ヴォルティス')
)
SELECT
    section                     AS 節,
    match_date                  AS 試合日,
    HA,
    相手,
    gf || '-' || ga             AS スコア,
    CASE WHEN gf > ga THEN 3 WHEN gf = ga THEN 1 ELSE 0 END AS 勝ち点,
    SUM(CASE WHEN gf > ga THEN 3 WHEN gf = ga THEN 1 ELSE 0 END)
        OVER (ORDER BY section) AS 累計勝ち点
FROM t
ORDER BY section;
