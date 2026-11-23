USE imdb;

-- Query 3: Longest Careers
-- Same result as longest_careers() in mongo_queries.py:
--   people with a known birth and death year, using every principal credit
--   (any category, any title type) on titles with a known start year that
--   falls between the birth and death years (inclusive).
--   career span = last valid credit year - first valid credit year.
-- MongoDB's CAREER_MIN_SPAN shortcut is not needed here: this query computes
-- the span for every eligible person directly.

WITH eligible_people AS (
    SELECT nconst, primaryName, birthYear, deathYear
    FROM name_basics
    WHERE birthYear IS NOT NULL
      AND deathYear IS NOT NULL
)
-- NO_MERGE keeps eligible_people as a small in-memory table (about 249,000
-- rows). Without it, MySQL looks up name_basics on disk once per credit
-- (about 100 million lookups). The hint changes only the plan, not the result.
SELECT /*+ NO_MERGE(n) */
    n.nconst,
    n.primaryName,
    n.birthYear,
    n.deathYear,
    MIN(b.startYear)                    AS firstYear,
    MAX(b.startYear)                    AS lastYear,
    MAX(b.startYear) - MIN(b.startYear) AS careerSpan
FROM title_principals p
JOIN eligible_people n ON n.nconst = p.nconst
JOIN title_basics b    ON b.tconst = p.tconst
WHERE b.startYear IS NOT NULL
  AND b.startYear BETWEEN n.birthYear AND n.deathYear   -- no credits before birth or after death
GROUP BY n.nconst, n.primaryName, n.birthYear, n.deathYear
-- MongoDB sorts by span only; nconst is added only to make ties deterministic.
ORDER BY careerSpan DESC, n.nconst ASC
LIMIT 20;
