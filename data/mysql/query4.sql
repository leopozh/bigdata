USE imdb;

SELECT
    b.primaryTitle,
    b.startYear,
    e.episodeCount
FROM (
    SELECT
        parentTconst,
        COUNT(*) AS episodeCount
    FROM title_episode
    WHERE parentTconst IS NOT NULL
    GROUP BY parentTconst
) e
JOIN title_basics b
    ON e.parentTconst = b.tconst
WHERE b.titleType = 'tvSeries'
  AND b.startYear BETWEEN 2000 AND 2025
ORDER BY e.episodeCount DESC
LIMIT 20;
