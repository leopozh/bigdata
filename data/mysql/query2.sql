USE imdb;

SELECT
    b.primaryTitle,
    b.startYear,
    r.averageRating,
    r.numVotes
FROM title_basics b
JOIN title_ratings r ON b.tconst = r.tconst
WHERE b.titleType = 'tvSeries'
  AND b.startYear BETWEEN 2010 AND 2025
  AND r.numVotes >= 10000
ORDER BY r.averageRating DESC, r.numVotes DESC
LIMIT 20;
