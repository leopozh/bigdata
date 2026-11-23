USE imdb;

-- Query 3: Longest Careers of Deceased Actors
-- Career span = last valid movie credit year - first valid movie credit year,
-- counting only acting credits released between the actor's birth and death.

SELECT
    n.nconst,
    n.primaryName,
    n.birthYear,
    n.deathYear,
    MIN(b.startYear)                    AS firstCreditYear,
    MAX(b.startYear)                    AS lastCreditYear,
    COUNT(DISTINCT b.tconst)            AS movieCount,
    MAX(b.startYear) - MIN(b.startYear) AS careerSpan
FROM name_basics n
JOIN title_principals p ON p.nconst = n.nconst
JOIN title_basics b     ON b.tconst = p.tconst
WHERE n.deathYear IS NOT NULL                  -- deceased actors only (mandatory)
  AND n.birthYear IS NOT NULL
  AND p.category IN ('actor', 'actress')
  AND b.titleType = 'movie'
  AND b.startYear IS NOT NULL
  AND b.startYear >= n.birthYear               -- no credits before birth
  AND b.startYear <= n.deathYear               -- no credits after death
  AND b.startYear <= YEAR(CURDATE())           -- no future films
GROUP BY n.nconst, n.primaryName, n.birthYear, n.deathYear
HAVING COUNT(DISTINCT b.tconst) >= 2
ORDER BY careerSpan DESC, movieCount DESC, n.nconst ASC
LIMIT 20;
