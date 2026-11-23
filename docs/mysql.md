# MySQL

## Dataset

We used the IMDb dataset with 217,125,409 records across seven tables. The cleaned CSV files were loaded into MySQL.

## Relational Schema

The schema is in `data/mysql/schema.sql`. Each IMDb file becomes one table, keyed by IMDb's own identifiers (`tconst` for titles, `nconst` for people). Row counts below are InnoDB estimates.

| Table | Primary key | Approx. rows | Contents |
|---|---|---:|---|
| `title_basics` | `tconst` | 12.1M | Title type, names, start/end year, runtime, genres |
| `title_ratings` | `tconst` | 1.7M | Average rating and number of votes |
| `title_principals` | (`tconst`, `ordering`) | 101.4M | One row per principal credit: person, category, job, characters |
| `name_basics` | `nconst` | 16.0M | Name, birth/death year, professions, known-for titles |
| `title_akas` | (`titleId`, `ordering`) | 59.6M | Alternate titles by region and language |
| `title_crew` | `tconst` | 12.8M | Directors and writers (comma-separated `nconst` lists) |
| `title_episode` | `tconst` | 9.7M | Parent series, season and episode number |

`title_ratings`, `title_principals`, `title_crew`, `title_episode` and `title_akas` reference `title_basics.tconst`; `title_principals.nconst` references `name_basics.nconst`. These relationships are not declared as foreign keys, so the queries use inner joins, which ignore any dangling references.

## SQL Queries

The five queries are in `data/mysql/query1.sql` through `query5.sql`. They answer the same questions as the MongoDB pipelines in `mongo_queries.py`, using the same eligibility rules, ranking and calculations, so the two databases can be compared directly. Where MongoDB leaves the order of exact ties unspecified, the SQL adds a final tiebreaker on the identifier (`tconst` or `nconst`); the checks below show where this can and cannot affect the results.

An earlier version of Queries 1–3 used stricter definitions (2020s only, highest-rated credit, acting credits on movies only). They were changed to match the MongoDB implementation; the earlier versions and their benchmarks remain in Git history and in `results/final/`.

### Query 1: Best Movie of Each Decade

MongoDB: `best_per_decade()`. Among movies (`titleType = 'movie'`) with a known release year and at least 25,000 votes, the highest-rated movie of each decade, with more votes winning a rating tie. One row per decade, oldest first.

- The decade is `startYear - MOD(startYear, 10)`, like MongoDB's `$subtract`/`$mod`.
- `ROW_NUMBER()` per decade ordered by rating, then votes, then `tconst` replaces MongoDB's `$sort` + `$group`/`$first`.
- Result: 12 decades (1910s–2020s), from *The Birth of a Nation* (1915) to *You Can See Everything* (2026). Every decade has a single winner on rating and votes, so the `tconst` tiebreaker never decides.

### Query 2: Actors Who Died Before Their Best-Known Movie

MongoDB: `died_before_best_known()`. For each person with a death year, the candidates are the movies in their IMDb `knownForTitles` list on which they have an `actor` or `actress` credit. The best-known movie is the candidate with the most votes. The query returns people whose best-known movie was released after their death year, most-voted first.

- `knownForTitles` is a comma-separated list, so it is split into rows with `JSON_TABLE` (MongoDB stores it as the `knownFor` array).
- The acting-credit check is an `EXISTS` subquery on `title_principals`, like MongoDB's `$anyElementTrue` over the embedded principals.
- Ratings are optional (`LEFT JOIN title_ratings`). Unrated candidates sort last, as missing values do in MongoDB's descending sort. Movies without a release year can be chosen but never pass `startYear > deathYear`.
- The best-known movie is chosen first (`movieRank = 1`) and only then checked for a posthumous release. For example, Heath Ledger is excluded because his most-voted known-for movie, *The Dark Knight* (2008), came out in the year he died.
- Result: top result is Oliver Reed (died 1999), *Gladiator* (2000, 1,896,031 votes).

### Query 3: Longest Careers

MongoDB: `longest_careers()`. People with a known birth and death year; every principal credit counts (any category and any title type) if the title's start year is known and between the birth and death years (inclusive). The career span is the last valid year minus the first valid year.

- The eligible people (about 249,000) are put in a CTE that the `NO_MERGE` hint keeps as an in-memory temporary table, so each of the roughly 100 million credits is checked with an in-memory lookup instead of a disk read. The hint changes only the plan.
- MongoDB first drops people whose unfiltered span is below `CAREER_MIN_SPAN = 60` as a speed-up. The SQL computes every eligible person's span directly, so it does not need that shortcut. The 20th span is 87, above 60, so the shortcut cannot have changed MongoDB's result.
- There is no separate future-year filter: as in MongoDB, credits are limited by the death year.
- No minimum number of credits is required (MongoDB has none); every top-20 span is at least 87 years, so each of those people has credits in at least two different years.
- Note: the docstring of `longest_careers()` says "credits of movies", but the pipeline does not filter by title type. The SQL follows the pipeline (all title types).
- Result: top result is Baby Peggy (1918–2020), 99 years from 1921 to 2020.

### Query 4: Biggest Casts of Characters

MongoDB: `biggest_casts()`. Movies with the most principal credits, counted as `COUNT(*)` over their `title_principals` rows (not names parsed from the `characters` field). This equals MongoDB's `$size` of the embedded `principals` array, which has one entry per `title_principals` row.

- Ranked by principal count, then `tconst` (MongoDB: count, then `_id`). Movies without a release year are kept (one appears in the top 20).
- Top results: *The Story of Christmas* (1994) and *Pokémon the Movie: The Power of Us* (2018), with 56 principal credits each.

### Query 5: Most Star-Studded Cast and Crew

Uses the same formula as the MongoDB `star_studded()` query:

- `fame(person) = SUM(numVotes)` over every rated title the person is credited on (any title type).
- `starScore(movie) = SUM(fame(person) - numVotes(movie))` over the distinct people credited on the movie.

Implementation details:

- The `person_title` CTE uses `SELECT DISTINCT tconst, nconst`, so a person with several credits on one title (for example, director and writer) counts once, like MongoDB's `$setUnion`. It only keeps rated titles that exist in `title_basics`, because those are the only titles used by either part of the formula.
- The `fame` CTE is grouped to one row per person before it is joined back, so vote counts are not multiplied by duplicate joins. `SUM` over `INT` returns `DECIMAL` in MySQL, so large totals do not overflow.
- People missing from `name_basics` get no fame value. They are still counted as credited people but add nothing to the score (`SUM` ignores `NULL`), which matches the MongoDB `$merge`/`$lookup` behavior.
- All principal categories are included, and only rated movies are ranked.
- If nobody credited on a movie has a fame value, `SUM` returns `NULL` but MongoDB's `$sum` returns `0`, so the score is wrapped in `COALESCE(..., 0)`. This affects exactly one rated movie (`tt43561434`, whose only credited person is missing from `name_basics`); all other scores are unchanged.
- MongoDB sorts by score only; the SQL adds `tconst` as a tiebreaker. The top 20 scores are all different, so this does not change the result.
- Top result: *Batman Begins* (2005), 23 credited people, star score 314,240,153.

## Verification

Each query was run against the full database, and its results were checked independently:

| Query | Check |
|---|---|
| Q1 | Each decade's winner was recomputed with `GROUP BY`/`MAX` instead of a window function; all 12 match. No decade has two movies tied on both rating and votes. |
| Q2 | For 8 returned people and 3 controls (Heath Ledger, Paul Walker, James Dean), `knownForTitles` was split in Python and each title looked up directly; all picks and exclusions match. Only 187 people have a vote tie on their pick, and none at the top-20 vote level (≥ 43,417 votes), so the top 20 does not depend on tie order. |
| Q3 | For 5 returned people, all raw credits (up to 6 categories and 9 title types per person) were recomputed in Python with MongoDB's rules; first year, last year and span match. The birth/death filter is active (8 of Mickey Rooney's credit years are excluded). Exactly 3 people have span 87 (the 20th place) and 17 have more, so the set of 20 people does not depend on tie order. |
| Q4 | Counts match a direct `COUNT(*)` on `title_principals`. A second formulation (aggregate first, then filter movies) gave the same ranking, including a 7-way tie at 44 credits broken by `tconst`. No principal row has all non-key fields empty, so no row is dropped by `load_mongo.py` and `COUNT(*)` equals MongoDB's `$size` for every movie. |
| Q5 | The formula was recomputed in Python from raw credit rows. *Primer* (17 credit rows, 10 people, one person credited 8 times) gives 309,875 in both Python and SQL (also after the `COALESCE` fix). *Batman Begins* (25 credit rows, 23 people) gives 314,240,153 in both. The one movie with no fame values scores 0 after the fix. |

### Equivalence with MongoDB

The MongoDB database was not available on this machine, so none of this is compared against actual MongoDB output. "Yes" means: by reading `mongo_queries.py`/`load_mongo.py` and testing the edge cases in MySQL (`results/aligned/audit/`), and assuming both databases were loaded from the same cleaned IMDb files.

| Query | Same rows (top 20)? | Same values? | Same order? | Remaining difference |
|---|---|---|---|---|
| Q1 | Yes | Yes | Yes | None found; no decade has a tie |
| Q2 | Yes | Yes | Yes | Tie order is unspecified in MongoDB, but no tie affects a pick at the top-20 vote level or the 20th/21st row |
| Q3 | Yes | Yes | **Not guaranteed** | MongoDB sorts by span only; the order of people with equal spans (2 at 89, 9 at 88, 3 at 87) can differ. The set of 20 does not, because the 21st person has span 86 |
| Q4 | Yes | Yes | Yes | None; both sort by count, then ID |
| Q5 | Yes | Yes | Yes | The 21st score was not checked (it would need another 65-minute run), so an exact tie at the 20th place cannot be ruled out |

Output columns differ in presentation only: the SQL also returns `tconst`/`nconst`, and the column names differ (for example `primaryTitle` vs. `title`).

## Indexing and Performance

### Environment

MySQL server with the default 128 MB InnoDB buffer pool and a 1 GB TempTable memory limit. The tables take about 15 GB (`title_principals` alone is 6.4 GB), so most queries are limited by random disk reads. We did not change the server configuration.

### Final indexes

The final secondary indexes and statistics are in `data/mysql/indexes.sql`:

| Object | Columns | Status | Notes |
|---|---|---|---|
| `idx_ratings_score_votes` | `title_ratings(averageRating, numVotes)` | **Invisible** | Kept but hidden from the optimizer, because it made the earlier Q2 3.9x slower (see below); for the current queries it would only be used by Q1 and Q5 |
| `idx_episode_parent` | `title_episode(parentTconst)` | Visible | Kept from the earlier phase; none of the five queries use it |
| Histogram on `name_basics.deathYear` | 100 buckets | Active | Statistics only, not an index; improves row estimates for Q2 and Q3 |

With this configuration, none of the five queries uses a secondary index. They all use primary-key lookups.

All other lookups use the primary keys. `title_principals` is clustered on (`tconst`, `ordering`), so "all credits of a title" is a primary-key range lookup.

### Method

- Baseline and indexed runs use `ALTER TABLE ... ALTER INDEX ... INVISIBLE/VISIBLE`, so the index never has to be dropped and rebuilt. Configurations were alternated (baseline, indexed, baseline, ...), and the query results were compared between configurations.
- Times are wall-clock times reported by the `mysql` client.
- Limitation: an invisible index is ignored by the optimizer but still exists and is still maintained. The comparison shows the plan MySQL would choose without the index, but it does not recreate the original database (buffer pool, OS file cache and statistics are as they are at that moment).

### Final query runtimes

Measured with the final configuration (`idx_ratings_score_votes` invisible). Evidence: `results/aligned/` (Q1–Q3) and `results/final/` (Q4, Q5).

| Query | Runs | Median | Main cost (from `EXPLAIN` / `EXPLAIN ANALYZE`) |
|---|---|---:|---|
| Q1 | 1.008 s, 0.248 s, 0.260 s (plus a first cold run of 1.338 s) | 0.26 s | Scan of `title_ratings`, primary-key lookups into `title_basics` |
| Q2 | 62.1 s, 51.3 s, 64.6 s | 62.1 s | Measured: `name_basics` scan 3.5 s; about 806,000 `title_basics`, 498,000 `title_ratings` and 498,000 `title_principals` primary-key lookups take about 53 s |
| Q3 | 218.3 s, 510.9 s, 268.3 s | 268.3 s | Reads essentially all of `title_principals` and `title_basics` (about 591,000 page reads, roughly 9 GB, in the third run) |
| Q4 | 32.0 s (one run) | — | `title_basics` scan, covering primary-key lookups into `title_principals` |
| Q5 | **Not measured** in the final configuration | — | One earlier run with the ratings index visible: 1 h 4 min 42 s (see below) |

- Results were identical in every run of each query.
- Q3's runs vary widely (218–511 s). It reads about 9 GB through a 128 MB buffer pool, so its time depends on how much of the data the operating system has cached and on other load on the machine.
- Q4's plan does not involve `idx_ratings_score_votes`, so its earlier timing applies to the final configuration.

Index decisions for the current queries:

- Q1 with `idx_ratings_score_votes` visible: 0.255 s, 0.237 s, 0.236 s (median 0.237 s), about 0.02 s faster. The index stays invisible because of the earlier Q2 result and because its effect on Q5 is unknown.
- Q2: about 92% of the measured time is primary-key lookups. An index on `name_basics(deathYear)` could only remove the 3.5 s scan (about 6%), so none was added.
- Q3 has to read every credit of every eligible person, so no index can reduce the amount of data read. The `NO_MERGE` hint was used instead (see Query 3).
- No new indexes were created.

### Earlier experiments (previous query definitions)

The experiments below were run before Queries 1–3 were aligned with MongoDB. They used the earlier versions of those queries, which are kept in Git history; the times do not apply to the current Q1–Q3.

#### Controlled results: `idx_ratings_score_votes`

| Query | Without index (invisible) | With index (visible) | Median without | Median with | Effect |
|---|---|---|---:|---:|---|
| Q1 | 1.038 s, 0.244 s, 0.229 s | 0.287 s, 0.232 s, 0.228 s | 0.244 s | 0.232 s | 1.05x faster with index (within run-to-run noise) |
| Q2 | 82.3 s, 89.0 s | 371.0 s, 303.6 s | 85.6 s | 337.3 s | **3.9x slower with index** |

- The first Q1 run (1.038 s) was a cold-cache run.
- Q2 was run twice per configuration. Both configurations were consistent and the gap is large, so a third run was not needed. The two values in each "median" column are averaged.
- Results were identical in every run of each query. Q2 also matches the original verified run.

Based on these results, `idx_ratings_score_votes` was made invisible. Q1 loses about 5% (0.232 s to 0.244 s), and Q2 runs in about 86 s instead of about 337 s.

##### Why an index can make a query slower

The only plan difference in both queries is how `title_ratings` is read: a table scan (in `tconst` order) without the index, or a covering index scan (in `averageRating` order) with it. The optimizer gives the two plans almost the same cost (about 177,000 vs. 179,000 in Q2) and picks the index because it is smaller and contains every column it needs from `title_ratings`.

The cost model does not account for what happens after this step. In Q2, every ratings row is joined to `title_basics` and `title_principals` with primary-key lookups. InnoDB stores both tables clustered (physically ordered) by `tconst`:

- **Without the index:** ratings rows come out in `tconst` order, so consecutive lookups land on the same or neighboring pages. Each page is read from disk once and reused.
- **With the index:** ratings rows come out in rating order, so the `tconst` values jump around the whole table. Consecutive lookups hit unrelated pages, and with a 128 MB buffer pool (much smaller than the 6.4 GB `title_principals` table) most of them become separate random disk reads.

The measured times (3.9x slower) and the plans are consistent with this explanation, but the explanation itself is inferred; we did not measure page reads per configuration. In general, an index helps when it lets the database read much less data. Here the index only replaced a 60 MB scan, and the order it produced made the much larger joins slower.

#### Single measured runs (Q3, Q4, Q5)

| Query | Time | Configuration when measured | Applies to final configuration? |
|---|---:|---|---|
| Q3 (earlier version) | 2 min 9.5 s | All indexes visible | No: Query 3 has changed since |
| Q4 | 32.0 s | All indexes visible | Yes: the plan does not use `idx_ratings_score_votes` |
| Q5 | 1 h 4 min 42.3 s | `idx_ratings_score_votes` visible | **No**: the final plan reads `title_ratings` with a table scan, and this plan was not timed |

Q5 takes about 65 minutes, so it was run once and not repeated. Its plan has the same difference as Q2 (index scan vs. table scan on `title_ratings`), so it may also be faster with the index invisible, but **Q5's runtime without the ratings index has not been measured**. Most of Q5's time is spent on temporary tables (about 3.7 GB) that do not fit in the 1 GB TempTable memory limit and go to disk, which the index does not affect.

#### Experiment: index on `title_principals(nconst)`

The earlier Queries 2 and 3 started from people (deceased actors), so we tested an index on `title_principals(nconst)`:

- Build: 3 min 17 s, 3.46 GB.
- The optimizer did not use it for any of the five queries.
- Adding the `deathYear` histogram corrected the optimizer's estimate of how many people have a death year (from a default guess to about 1.75%; the true value is 1.68%), but the plans still did not use the index.
- Forcing the index with `JOIN_ORDER` hints (scratch copies only, measured with `EXPLAIN ANALYZE` and stopped at about 2x the baseline, so neither run completed):

| Query | Baseline (original plan) | Hinted plan (`nconst` index) | Progress when stopped |
|---|---:|---:|---|
| Q2 | 6 min 16 s | stopped at 756 s | 172,000 of 266,000 deceased people processed |
| Q3 | 2 min 10 s | stopped at 274 s | 51,700 of 249,000 people processed |

The optimizer expected 17 credits per person; the actual average was 60–79. Each credit also needs a random lookup into the 6.4 GB clustered table to check `category`. The index was therefore dropped. The histogram was kept because it gives more accurate row estimates.

### Saved evidence

The raw outputs behind every number in this section are saved in the repository:

- `results/aligned/`: the current Queries 1–3 (runs, plans, `EXPLAIN ANALYZE` of Q2, and verification checks).
- `results/final/`: Queries 4 and 5, and the earlier experiments (earlier Q1–Q3 runs, the `nconst` index experiment, and `verify.py`, which recomputes the earlier Q2/Q3 checks and the Q5 checks offline).

The benchmark table in the previous version of this document was for an earlier set of queries and has been replaced.

## Running the Queries

From the project directory:

    mysql -u root -p < data/mysql/query1.sql

Replace `query1.sql` with the desired query file. Expected runtimes on our machine are listed above (Q5 takes about an hour).
## Loading the Data

Place the seven cleaned IMDb CSV files in `data/clean/`.

Create the database and tables:

    mysql -u root -p < data/mysql/schema.sql

> **Warning:** `schema.sql` runs `DROP TABLE IF EXISTS` before creating each table. Running it on a loaded database deletes all seven tables and their data (about 217 million rows), and reloading takes a long time. Only run it to set up an empty database.

From the repository root, load the data:

    mysql --local-infile=1 -u root -p imdb < data/mysql/load_portable.sql

Run this only once, on the empty tables created by `schema.sql`. The CSV files are not included in GitHub because of their size.

Then create the secondary indexes and the histogram once:

    mysql -u root -p < data/mysql/indexes.sql

`indexes.sql` is a one-time setup script. It creates both indexes, makes `idx_ratings_score_votes` invisible, and builds the histogram. `CREATE INDEX` fails if the index already exists, so do not run it again on a database that already has these indexes (the `ALTER INDEX` and `ANALYZE TABLE ... UPDATE HISTOGRAM` statements can be re-run safely on their own).

## Functional Dependencies

IMDb uses unique identifiers for titles and people. The primary keys in our schema give us the following functional dependencies:

| Table | Functional dependency |
|---|---|
| `name_basics` | `nconst` → `primaryName`, `birthYear`, `deathYear`, `primaryProfession`, `knownForTitles` |
| `title_basics` | `tconst` → `titleType`, `primaryTitle`, `originalTitle`, `isAdult`, `startYear`, `endYear`, `runtimeMinutes`, `genres` |
| `title_ratings` | `tconst` → `averageRating`, `numVotes` |
| `title_crew` | `tconst` → `directors`, `writers` |
| `title_episode` | `tconst` → `parentTconst`, `seasonNumber`, `episodeNumber` |
| `title_principals` | (`tconst`, `ordering`) → `nconst`, `category`, `job`, `characters` |
| `title_akas` | (`titleId`, `ordering`) → `title`, `region`, `language`, `types`, `attributes`, `isOriginalTitle` |

These dependencies follow from IMDb's identifiers and the primary keys used in our relational model. For example, a title has one `tconst`, but it can have multiple alternate titles and credited people. That is why `title_akas` and `title_principals` use composite primary keys.

`title_principals` does not have the dependency (`tconst`, `nconst`) → `category`: the same person can have several credits on one title (for example *Primer*, where one person has 8 credits). This is why `ordering` is part of the key, and why Query 5 removes duplicate (`tconst`, `nconst`) pairs.

## Normalization

Our relational model separates information about titles, people, ratings, episodes, crew, and alternate titles into seven tables. This reduces repeated data. For example, an actor's name is stored in `name_basics` instead of being repeated for every movie credit in `title_principals`. Similarly, ratings are stored separately from basic title information.

In every table, the only determinant of the non-key columns is the full primary key: the single-column keys cannot have partial dependencies, and in the two composite-key tables each attribute describes one credit or one alternate title, not `tconst` alone. There are no dependencies between non-key columns, so apart from the list-valued columns below, the tables are in Third Normal Form (3NF).

However, some IMDb fields contain lists, including `genres`, `directors`, `writers`, `knownForTitles`, `primaryProfession`, `types`, `attributes`, and `characters` (stored as JSON text). These are convenient for loading the original dataset but are not fully atomic under a strict interpretation of First Normal Form (1NF). A more normalized design would create separate tables such as `title_genres`, `title_directors`, and `title_writers`, with one value per row.

There is also some redundancy between tables: directors and writers appear both in `title_crew` and as `director`/`writer` credits in `title_principals`, and `knownForTitles` is derived from a person's credits.

We kept these fields in their original form to preserve the dataset structure and avoid creating additional tables during loading. This is a tradeoff between normalization and implementation complexity. None of the five queries depends on the list-valued columns.

## Limitations and Assumptions

- **Server memory:** all timings come from one machine with the default 128 MB buffer pool. Q2, Q3 and Q5 are limited by disk reads and would behave differently with more memory.
- **Number of runs:** Q1 has 3 runs per configuration, Q2 and Q3 have 3 runs each, and Q4 has one run. Q5 has one run, made with `idx_ratings_score_votes` visible; its runtime in the final configuration (index invisible) has not been measured.
- **MongoDB comparison:** the MongoDB database was not available on this machine, so the equivalence with `mongo_queries.py` is based on reading the pipelines and on the checks above, not on comparing actual MongoDB output. Where MongoDB leaves tie order unspecified, its row order (but, per the checks above, not its set of top-20 rows) can differ from MySQL's.
- **Invisible indexes:** baseline runs use invisible indexes, which approximate but do not recreate an unindexed database.
- **Year precision:** IMDb only provides years. Q2 counts a movie as posthumous only if `startYear > deathYear`, so movies released in the year of death do not count. Q3 includes credits in the birth and death years.
- **Data quality:** some IMDb records have implausible years (for example, credits before birth). Q3 excludes them, but birth and death years themselves are taken as given.
- **No foreign keys:** inner joins skip credits that reference missing titles or people. Q5 handles people missing from `name_basics` in the same way as the MongoDB version.
- **Changing data:** results depend on the IMDb snapshot (for example, the 2020s winner in Q1 can change as new movies and votes are added).
