USE imdb;

SELECT
    n.primaryName,
    COUNT(*) AS movieCredits
FROM title_ratings r
JOIN title_basics b
    ON r.tconst = b.tconst
JOIN title_principals p
    ON b.tconst = p.tconst
JOIN name_basics n
    ON p.nconst = n.nconst
WHERE b.titleType = 'movie'
  AND b.startYear BETWEEN 2015 AND 2025
  AND r.averageRating >= 7.0
  AND r.numVotes >= 50000
  AND p.category IN ('actor', 'actress')
GROUP BY n.nconst, n.primaryName
ORDER BY movieCredits DESC
LIMIT 20;
