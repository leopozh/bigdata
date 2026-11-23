SELECT p.nconst, n.birthYear, n.deathYear, b.tconst, b.startYear
FROM title_principals p
JOIN title_basics b ON b.tconst = p.tconst
JOIN name_basics n ON n.nconst = p.nconst
WHERE p.nconst IN ('nm0782229','nm0001682','nm0038675','nm0001478','nm0511276')
  AND p.category IN ('actor','actress') AND b.titleType = 'movie';
