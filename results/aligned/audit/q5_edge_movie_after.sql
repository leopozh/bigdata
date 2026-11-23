USE imdb;

-- Query 5: Most Star-Studded Cast and Crew
-- Mirrors star_studded() in mongo_queries.py:
--   fame(person)    = SUM(numVotes) over every rated title (any type) they are credited on
--   starScore(movie) = SUM(fame(person) - numVotes(movie)) over distinct people on the movie

WITH person_title AS (
    -- One row per (rated title, person), so people credited in several
    -- categories on the same title are counted once (Mongo: $setUnion).
    -- Only rated titles present in title_basics are kept, as in the Mongo
    -- titles collection; this also keeps the deduplicated set small.
    SELECT DISTINCT p.tconst, p.nconst, r.numVotes
    FROM title_principals p
    JOIN title_ratings r ON r.tconst = p.tconst
    JOIN title_basics b  ON b.tconst = p.tconst
    WHERE p.nconst IS NOT NULL AND p.tconst = 'tt43561434'
      AND r.numVotes IS NOT NULL
),
fame AS (
    -- SUM over INT returns DECIMAL in MySQL, so large totals do not overflow.
    -- Only people in name_basics get a fame value ($merge into the Mongo
    -- people collection discards unknown people).
    SELECT pt.nconst, SUM(pt.numVotes) AS fame
    FROM person_title pt
    JOIN name_basics n ON n.nconst = pt.nconst
    GROUP BY pt.nconst
)
SELECT
    b.tconst,
    b.primaryTitle,
    b.startYear,
    r.averageRating,
    r.numVotes,
    COUNT(*)                   AS creditedPeople,
    -- People without a fame row contribute NULL, which SUM ignores
    -- (same as Mongo's $sum over a missing $lookup result). If nobody on the
    -- movie has a fame value, SUM is NULL but MongoDB's $sum is 0, so COALESCE.
    COALESCE(SUM(f.fame - r.numVotes), 0) AS starScore
FROM title_basics b
JOIN title_ratings r ON r.tconst = b.tconst
JOIN person_title pt ON pt.tconst = b.tconst
LEFT JOIN fame f     ON f.nconst = pt.nconst
WHERE b.titleType = 'movie' AND b.tconst = 'tt43561434'
GROUP BY b.tconst, b.primaryTitle, b.startYear, r.averageRating, r.numVotes
ORDER BY starScore DESC, b.tconst ASC
LIMIT 20;
