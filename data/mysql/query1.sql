USE imdb;

-- Query 1: Best Movie of Each Decade
-- Same as best_per_decade() in mongo_queries.py: among movies with at least
-- 25,000 votes and a known release year, the highest-rated movie of each
-- decade (ties: more votes first). One row per decade, oldest decade first.

WITH ranked AS (
    SELECT
        b.tconst,
        b.primaryTitle,
        b.startYear,
        b.startYear - MOD(b.startYear, 10) AS decade,
        r.averageRating,
        r.numVotes,
        -- MongoDB sorts by rating, then votes, and takes the first movie per
        -- decade; tconst is added only to make exact ties deterministic.
        ROW_NUMBER() OVER (
            PARTITION BY b.startYear - MOD(b.startYear, 10)
            ORDER BY r.averageRating DESC, r.numVotes DESC, b.tconst ASC
        ) AS decadeRank
    FROM title_basics b
    JOIN title_ratings r ON r.tconst = b.tconst
    WHERE b.titleType = 'movie'
      AND b.startYear IS NOT NULL
      AND r.numVotes >= 25000
)
SELECT decade, tconst, primaryTitle, startYear, averageRating, numVotes
FROM ranked
WHERE decadeRank = 1
ORDER BY decade;
