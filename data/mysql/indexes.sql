USE imdb;

-- Secondary indexes and statistics used by the five MySQL queries.
-- Primary keys are defined in schema.sql. See docs/mysql.md for the benchmarks.

-- Covering index on (averageRating, numVotes). It is kept but made INVISIBLE:
-- when visible, the optimizer uses it for Queries 1, 2 and 5, which made
-- Query 1 about 5% faster but Query 2 about 3.9x slower (see docs/mysql.md).
-- An invisible index is still maintained and can be re-enabled with
-- ALTER TABLE title_ratings ALTER INDEX idx_ratings_score_votes VISIBLE;
CREATE INDEX idx_ratings_score_votes
ON title_ratings(averageRating, numVotes);

ALTER TABLE title_ratings ALTER INDEX idx_ratings_score_votes INVISIBLE;

-- Kept from the earlier project phase (episode lookups by parent series).
-- None of the five final queries use it.
CREATE INDEX idx_episode_parent
ON title_episode(parentTconst);

-- Histogram (statistics only, not an index) so the optimizer knows that only
-- about 1.7% of people have a recorded deathYear (Queries 2 and 3).
ANALYZE TABLE name_basics UPDATE HISTOGRAM ON deathYear WITH 100 BUCKETS;

-- Tested and removed: an index on title_principals(nconst) was built and
-- evaluated, but the optimizer did not use it for any of the five queries,
-- and forcing it made Queries 2 and 3 slower (see docs/mysql.md).
