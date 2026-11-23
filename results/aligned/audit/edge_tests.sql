-- T2a: knownForTitles lists that repeat a title (MongoDB's $lookup matches each title once;
--      SQL JSON_TABLE yields a row per entry, so repeated entries must not change the pick).
SELECT COUNT(*) AS deceased_with_repeated_knownFor
FROM (
  SELECT n.nconst
  FROM name_basics n
  JOIN JSON_TABLE(CONCAT('["', REPLACE(n.knownForTitles, ',', '","'), '"]'), '$[*]' COLUMNS (t VARCHAR(12) PATH '$')) k
  WHERE n.deathYear IS NOT NULL AND n.knownForTitles IS NOT NULL
  GROUP BY n.nconst HAVING COUNT(*) <> COUNT(DISTINCT k.t)
) x;

-- T4: principal rows with every non-key field empty. load_mongo.py drops such rows
--     (empty entry), so MongoDB's $size would be smaller than SQL COUNT(*) for those movies.
SELECT COUNT(*) AS empty_principal_rows,
       COUNT(DISTINCT p.tconst) AS titles_affected
FROM title_principals p
WHERE p.nconst IS NULL AND p.category IS NULL AND p.job IS NULL AND p.characters IS NULL;

-- T5: rated movies whose credited people are all missing from name_basics
--     (SQL SUM gives NULL, MongoDB $sum gives 0), and rated movies with at least one missing person.
SELECT SUM(named = 0) AS movies_all_people_missing,
       SUM(named > 0 AND named < people) AS movies_some_people_missing,
       COUNT(*) AS rated_movies_with_people
FROM (
  SELECT pt.tconst, COUNT(*) AS people, COUNT(n.nconst) AS named
  FROM (SELECT DISTINCT p.tconst, p.nconst
        FROM title_basics b
        JOIN title_ratings r ON r.tconst = b.tconst
        JOIN title_principals p ON p.tconst = b.tconst
        WHERE b.titleType = 'movie' AND p.nconst IS NOT NULL) pt
  LEFT JOIN name_basics n ON n.nconst = pt.nconst
  GROUP BY pt.tconst
) m;
