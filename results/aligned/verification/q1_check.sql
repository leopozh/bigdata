-- Independent check: per decade, max rating, then max votes among those, and how many movies share both.
WITH e AS (
  SELECT b.tconst, b.startYear - MOD(b.startYear,10) AS decade, r.averageRating, r.numVotes
  FROM title_basics b JOIN title_ratings r ON r.tconst=b.tconst
  WHERE b.titleType='movie' AND b.startYear IS NOT NULL AND r.numVotes >= 25000),
top_rating AS (SELECT decade, MAX(averageRating) mr, COUNT(*) eligible FROM e GROUP BY decade),
top_votes AS (SELECT e.decade, MAX(e.numVotes) mv FROM e JOIN top_rating t ON t.decade=e.decade AND e.averageRating=t.mr GROUP BY e.decade)
SELECT t.decade, t.eligible, t.mr, v.mv,
  (SELECT COUNT(*) FROM e WHERE e.decade=t.decade AND e.averageRating=t.mr AND e.numVotes=v.mv) AS full_ties,
  (SELECT GROUP_CONCAT(tconst) FROM e WHERE e.decade=t.decade AND e.averageRating=t.mr AND e.numVotes=v.mv) AS winners,
  (SELECT COUNT(*) FROM e WHERE e.averageRating IS NULL) AS null_ratings
FROM top_rating t JOIN top_votes v ON v.decade=t.decade ORDER BY t.decade;
