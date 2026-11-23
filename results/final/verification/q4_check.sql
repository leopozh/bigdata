SELECT tconst, COUNT(*) c, COUNT(DISTINCT nconst) distinct_people FROM title_principals WHERE tconst IN ('tt0249991','tt8108230','tt1371111','tt7528004','tt3534078') GROUP BY tconst;
SELECT pc.principalCount, COUNT(*) movies, GROUP_CONCAT(pc.tconst ORDER BY pc.tconst) ids
FROM (SELECT tconst, COUNT(*) principalCount FROM title_principals GROUP BY tconst HAVING COUNT(*) >= 44) pc
JOIN title_basics b ON b.tconst = pc.tconst WHERE b.titleType='movie'
GROUP BY pc.principalCount ORDER BY pc.principalCount DESC;
