SELECT COUNT(*) AS fixtures_total FROM fixtures;

SELECT game_id, section, match_date, home_club, away_club, game_type
FROM fixtures
WHERE home_club LIKE '%徳島%' OR away_club LIKE '%徳島%'
ORDER BY match_date;