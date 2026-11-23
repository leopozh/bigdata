-- All credits (any category, any type) of sample people, unfiltered.
SELECT p.nconst, n.birthYear, n.deathYear, p.category, b.titleType, b.tconst, IFNULL(b.startYear,'NULL') startYear
FROM title_principals p
JOIN title_basics b ON b.tconst = p.tconst
JOIN name_basics n ON n.nconst = p.nconst
WHERE p.nconst IN ('nm0045133','nm0728958','nm0001682','nm0454379','nm0782229');
