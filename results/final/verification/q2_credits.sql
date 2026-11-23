-- All eligible rated movie credits for the 20 returned actors + control nm0005132,
-- computed without window functions: best = max rating, then max votes, then min tconst.
SELECT DISTINCT p.nconst, n.primaryName, n.deathYear, b.tconst, b.startYear, r.averageRating, r.numVotes
FROM title_principals p
JOIN title_basics b ON b.tconst = p.tconst
JOIN title_ratings r ON r.tconst = p.tconst
JOIN name_basics n ON n.nconst = p.nconst
WHERE p.nconst IN ('nm0119364','nm0893449','nm1548005','nm0454627','nm0154164','nm0004366','nm0651737','nm0878990','nm4978225','nm1563842','nm6160527','nm0707947','nm3272130','nm4470570','nm9322849','nm2665952','nm0442479','nm6481337','nm13351033','nm2897413','nm0005132')
  AND p.category IN ('actor','actress') AND b.titleType='movie' AND b.startYear IS NOT NULL;
