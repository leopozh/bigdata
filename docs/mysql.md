# MySQL

## Dataset

We used the IMDb dataset with 217,125,409 records across seven tables. The cleaned CSV files were loaded into MySQL.

## SQL Queries

1. Top-rated movies (2020-2025) with at least 100,000 votes.
2. Top-rated TV series (2010-2025) with at least 10,000 votes.
3. Actors with the most credits in highly rated movies (2015-2025).
4. TV series with the most episodes (2000-2025).
5. Average movie ratings by genre (2015-2025).

The queries are in `data/mysql/query1.sql` through `query5.sql`.

## Indexing and Performance

We used `EXPLAIN ANALYZE` to compare query performance before and after indexing.

Indexes added:

- `idx_ratings_score_votes` on `title_ratings(averageRating, numVotes)`
- `idx_episode_parent` on `title_episode(parentTconst)`

| Query | Before | After | Improvement |
|---|---:|---:|---:|
| Query 1 | 672 ms | 38.8 ms | 17.3x |
| Query 2 | 220 ms | 9.02 ms | 24.4x |
| Query 4 | 21.6 s | 6.24 s | 3.5x |

These are individual benchmark runs, so execution times can vary.

The ratings index improved the first two queries. The episode index helped Query 4 by allowing MySQL to use a covering index scan during aggregation.

Query 3 required multiple joins and grouping, which made it more expensive. Query 5 used `JSON_TABLE` to separate genres and calculate average ratings.

## Running the Queries

From the project directory:

`mysql -u root -p < data/mysql/query1.sql`

Replace `query1.sql` with the desired query file.
