USE imdb;

-- Query 2: Actors Who Died Before Their Best-Known Movie
-- For each deceased actor/actress, pick their best-known credited movie
-- (highest rating, then most votes, then lowest tconst) across ALL eligible
-- movies, and only then keep those whose pick was released after they died.

WITH ranked_credits AS (
    SELECT /*+ JOIN_ORDER(n, p, b, r) */
        p.nconst,
        b.tconst,
        b.primaryTitle,
        b.startYear,
        r.averageRating,
        r.numVotes,
        -- Rank every eligible movie per actor; duplicate credits on the same
        -- movie share a tconst, so whichever copy gets rank 1 is the same movie.
        ROW_NUMBER() OVER (
            PARTITION BY p.nconst
            ORDER BY r.averageRating DESC, r.numVotes DESC, b.tconst ASC
        ) AS movieRank
    FROM title_principals p
    JOIN name_basics n   ON n.nconst = p.nconst
    JOIN title_basics b  ON b.tconst = p.tconst
    JOIN title_ratings r ON r.tconst = p.tconst
    WHERE p.category IN ('actor', 'actress')
      AND n.deathYear IS NOT NULL
      AND b.titleType = 'movie'
      AND b.startYear IS NOT NULL
      AND r.averageRating IS NOT NULL
      AND r.numVotes IS NOT NULL
)
SELECT
    n.nconst,
    n.primaryName,
    n.deathYear,
    rc.tconst,
    rc.primaryTitle,
    rc.startYear,
    rc.averageRating,
    rc.numVotes
FROM ranked_credits rc
JOIN name_basics n ON n.nconst = rc.nconst
WHERE rc.movieRank = 1               -- best-known movie chosen first ...
  AND rc.startYear > n.deathYear     -- ... then checked for posthumous release
ORDER BY rc.averageRating DESC, rc.numVotes DESC, n.nconst ASC
LIMIT 20;
