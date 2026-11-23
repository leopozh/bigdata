USE imdb;

SELECT
    g.genre,
    COUNT(*) AS movieCount,
    ROUND(AVG(r.averageRating), 2) AS avgRating,
    SUM(r.numVotes) AS totalVotes
FROM title_ratings r
JOIN title_basics b
    ON r.tconst = b.tconst
JOIN JSON_TABLE(
    CONCAT(
        '["',
        REPLACE(b.genres, ',', '","'),
        '"]'
    ),
    '$[*]' COLUMNS (
        genre VARCHAR(50) PATH '$'
    )
) AS g
WHERE b.titleType = 'movie'
  AND b.startYear BETWEEN 2015 AND 2025
  AND r.numVotes >= 10000
  AND b.genres IS NOT NULL
  AND b.genres <> ''
GROUP BY g.genre
HAVING COUNT(*) >= 50
ORDER BY avgRating DESC, movieCount DESC;
