SELECT p.tconst, p.nconst, p.category, r.numVotes, (b.tconst IS NOT NULL) inBasics, (n.nconst IS NOT NULL) inNames
FROM title_principals p
LEFT JOIN title_ratings r ON r.tconst = p.tconst
LEFT JOIN title_basics b ON b.tconst = p.tconst
LEFT JOIN name_basics n ON n.nconst = p.nconst
WHERE p.nconst IN ('nm0000198','nm0000288','nm0000323','nm0000442','nm0000553','nm0001877','nm0002892','nm0004170','nm0005017','nm0006133','nm0189769','nm0275286','nm0290581','nm0614165','nm0634240','nm0660667','nm0730070','nm0746273','nm0809059','nm0843514','nm0858799','nm0913822','nm0929489') OR p.tconst = 'tt0372784';
