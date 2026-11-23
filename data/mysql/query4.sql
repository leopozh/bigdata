USE imdb;

-- Query 4: Biggest Casts of Characters
-- Movies with the most principal credits, counted as rows in title_principals
-- (not names parsed from the characters field).

SELECT
    b.tconst,
    b.primaryTitle,
    b.startYear,
    COUNT(*) AS principalCount
FROM title_basics b
JOIN title_principals p ON p.tconst = b.tconst
WHERE b.titleType = 'movie'
GROUP BY b.tconst, b.primaryTitle, b.startYear
ORDER BY principalCount DESC, b.tconst ASC
LIMIT 20;
