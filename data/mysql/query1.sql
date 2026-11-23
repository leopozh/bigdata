USE imdb;

SELECT
    b.primaryTitle,
    b.startYear,
    r.averageRating,
    r.numVotes
FROM title_ratings r
JOIN title_basics b ON r.tconst = b.tconst
WHERE b.titleType = 'movie'
  AND b.startYear BETWEEN 2020 AND 2025
  AND r.numVotes >= 100000
ORDER BY r.averageRating DESC, r.numVotes DESC
LIMIT 20;
