SELECT p.tconst, p.nconst, p.category, r.numVotes, (b.tconst IS NOT NULL) inBasics, (n.nconst IS NOT NULL) inNames
FROM title_principals p
LEFT JOIN title_ratings r ON r.tconst = p.tconst
LEFT JOIN title_basics b ON b.tconst = p.tconst
LEFT JOIN name_basics n ON n.nconst = p.nconst
WHERE p.nconst IN ('nm1503403','nm1503383','nm1503463','nm0881420','nm1503468','nm1503624','nm1503460','nm1508372','nm1518910','nm1439230');
