USE imdb;

-- Query 1: Best Movie of the Decade
-- Highest-rated movies released in the chosen decade with at least 25,000 votes.

-- Decade bounds: change @decade_start to evaluate a different decade.
SET @decade_start = 2020;
SET @min_votes = 25000;
-- Last year of the decade, capped at the current year to exclude future releases.
SET @decade_end = LEAST(@decade_start + 9, YEAR(CURDATE()));

SELECT
    b.tconst,
    b.primaryTitle,
    b.startYear,
    r.averageRating,
    r.numVotes
FROM title_basics b
JOIN title_ratings r ON r.tconst = b.tconst
WHERE b.titleType = 'movie'
  AND b.startYear BETWEEN @decade_start AND @decade_end
  AND r.numVotes >= @min_votes
ORDER BY r.averageRating DESC, r.numVotes DESC, b.tconst ASC
LIMIT 20;
