USE imdb;

-- Query 2: Actors Who Died Before Their Best-Known Movie
-- Same as died_before_best_known() in mongo_queries.py:
--   candidates  = movies in the person's IMDb knownForTitles list on which
--                 they have an actor/actress credit
--   best-known  = the candidate with the most votes
--   result      = deceased people whose best-known movie came out after
--                 their death year, most-voted first

WITH known_for AS (
    -- knownForTitles is a comma-separated list; split it into one row per title.
    SELECT n.nconst, n.primaryName, n.deathYear, k.tconst
    FROM name_basics n
    JOIN JSON_TABLE(
        CONCAT('["', REPLACE(n.knownForTitles, ',', '","'), '"]'),
        '$[*]' COLUMNS (tconst VARCHAR(12) PATH '$')
    ) AS k
    WHERE n.deathYear IS NOT NULL
      AND n.knownForTitles IS NOT NULL
),
ranked AS (
    SELECT
        kf.nconst,
        kf.primaryName,
        kf.deathYear,
        b.tconst,
        b.primaryTitle,
        b.startYear,
        r.numVotes,
        -- MongoDB sorts by votes (unrated movies last) and takes the first
        -- movie per person; tconst is added only to make ties deterministic.
        ROW_NUMBER() OVER (
            PARTITION BY kf.nconst
            ORDER BY r.numVotes DESC, b.tconst ASC
        ) AS movieRank
    FROM known_for kf
    JOIN title_basics b ON b.tconst = kf.tconst
    LEFT JOIN title_ratings r ON r.tconst = b.tconst   -- unrated movies stay eligible
    WHERE b.titleType = 'movie'
      AND EXISTS (
          SELECT 1
          FROM title_principals p
          WHERE p.tconst = b.tconst
            AND p.nconst = kf.nconst
            AND p.category IN ('actor', 'actress')
      )
)
SELECT nconst, primaryName, deathYear, tconst, primaryTitle, startYear, numVotes
FROM ranked
WHERE movieRank = 1                 -- best-known movie chosen first ...
  AND startYear > deathYear         -- ... then checked for posthumous release
ORDER BY numVotes DESC, nconst ASC
LIMIT 22;
