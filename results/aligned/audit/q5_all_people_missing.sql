-- Rated movies whose credited people are all missing from name_basics.
SELECT pt.tconst, b.primaryTitle, r.numVotes, COUNT(*) AS people, COUNT(n.nconst) AS named
FROM (SELECT DISTINCT p.tconst, p.nconst
      FROM title_basics b
      JOIN title_ratings r ON r.tconst = b.tconst
      JOIN title_principals p ON p.tconst = b.tconst
      WHERE b.titleType = 'movie' AND p.nconst IS NOT NULL) pt
JOIN title_basics b ON b.tconst = pt.tconst
JOIN title_ratings r ON r.tconst = pt.tconst
LEFT JOIN name_basics n ON n.nconst = pt.nconst
GROUP BY pt.tconst, b.primaryTitle, r.numVotes
HAVING COUNT(n.nconst) = 0;
