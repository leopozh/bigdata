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

The five queries are the ones agreed on by the group. They are in `data/mysql/query1.sql` through `query5.sql`. Every query ends with a final tiebreaker on the identifier (`tconst` or `nconst`), so the top 20 is deterministic.

### Query 1: Best Movie of the Decade

Highest-rated movies (`titleType = 'movie'`) released in the decade with at least 25,000 votes, ranked by rating, then votes, then `tconst`.

- The decade is set by `@decade_start` (currently 2020). The upper bound is `LEAST(@decade_start + 9, YEAR(CURDATE()))`, which excludes future release years.
- Result: 1,219 movies qualify; the top 20 is returned. The top result is *You Can See Everything* (2026, 9.0, 40,300 votes).

### Query 2: Actors Who Died Before Their Best-Known Movie

Actors and actresses whose best-known credited movie was released after the year they died.

- Eligible credits: `title_principals` rows with category `actor` or `actress`, on movies with a release year and a rating, for people with a known `deathYear`.
- A CTE ranks every eligible movie per person with `ROW_NUMBER()` (rating, then votes, then `tconst`). The best-known movie is chosen first (`movieRank = 1`) and only then checked for `startYear > deathYear`. This means an actor whose best movie came out while they were alive is excluded, even if they have other posthumous releases. For example, Heath Ledger is excluded: his best-known movie, *The Dark Knight* (2008), was released in the year he died, not after it.
- There is no minimum vote count, so the results are mostly little-known movies with few votes and high ratings. This follows the agreed definition.

### Query 3: Longest Careers of Deceased Actors

Longest acting careers, measured as last valid movie credit year minus first valid movie credit year.

- Requires `deathYear IS NOT NULL` and `birthYear IS NOT NULL`, so living actors are never included.
- Only `actor`/`actress` credits on movies count, and a credit is valid only if its release year is known, is between the birth year and the death year (inclusive), and is not in the future. These filters run before grouping, so `MIN` and `MAX` only see valid years.
- Requires at least two distinct movies. Ranked by career span, then movie count, then `nconst`.
- Top result: Francia Seguy (1914–2013), 87 years from 1917 to 2004 across 6 movies.

### Query 4: Biggest Casts of Characters

Movies with the most principal credits, counted as `COUNT(*)` over their `title_principals` rows (not names parsed from the `characters` field).

- Ranked by principal count, then `tconst`. Movies without a release year are kept (one appears in the top 20).
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
- Top result: *Batman Begins* (2005), 23 credited people, star score 314,240,153.

## Verification

Each query was run against the full database, and its results were checked independently:

| Query | Check |
|---|---|
| Q1 | All returned movies are in 2020–2026 with ≥ 25,000 votes. A separate count found exactly 19 eligible movies ranked above the 20th. No rated movies from 2027 or later exist. |
| Q2 | For all 20 actors, every eligible credit was exported and the best-known movie was recomputed in Python. All 20 picks match and are posthumous. Heath Ledger was used as a control and is correctly excluded. |
| Q3 | All 20 actors have a death year. For 5 actors, all acting movie credits were recomputed without filters in Python. Spans and counts match, and the filters visibly removed a credit after death (Mickey Rooney) and credits before birth (Ashalata Wabgaonkar). |
| Q4 | Counts match a direct `COUNT(*)` on `title_principals`. A second formulation (aggregate first, then filter movies) gave the same ranking, including a 7-way tie at 44 credits broken by `tconst`. |
| Q5 | The formula was recomputed in Python from raw credit rows. *Primer* (17 credit rows, 10 people, one person credited 8 times) gives 309,875 in both Python and SQL. *Batman Begins* (25 credit rows, 23 people) gives 314,240,153 in both. |

## Indexing and Performance

### Environment

MySQL server with the default 128 MB InnoDB buffer pool and a 1 GB TempTable memory limit. The tables take about 15 GB (`title_principals` alone is 6.4 GB), so most queries are limited by random disk reads. We did not change the server configuration.

### Final indexes

The final secondary indexes and statistics are in `data/mysql/indexes.sql`:

| Object | Columns | Status | Notes |
|---|---|---|---|
| `idx_ratings_score_votes` | `title_ratings(averageRating, numVotes)` | **Invisible** | Kept but hidden from the optimizer, because it made Q2 3.9x slower (see below) |
| `idx_episode_parent` | `title_episode(parentTconst)` | Visible | Kept from the earlier phase; none of the five queries use it |
| Histogram on `name_basics.deathYear` | 100 buckets | Active | Statistics only, not an index; improves row estimates for Q2 and Q3 |

With this configuration, none of the five queries uses a secondary index. They all use primary-key lookups.

All other lookups use the primary keys. `title_principals` is clustered on (`tconst`, `ordering`), so "all credits of a title" is a primary-key range lookup.

### Method

- Baseline and indexed runs use `ALTER TABLE ... ALTER INDEX ... INVISIBLE/VISIBLE`, so the index never has to be dropped and rebuilt. Configurations were alternated (baseline, indexed, baseline, ...), and the query results were compared between configurations.
- Times are wall-clock times reported by the `mysql` client.
- Limitation: an invisible index is ignored by the optimizer but still exists and is still maintained. The comparison shows the plan MySQL would choose without the index, but it does not recreate the original database (buffer pool, OS file cache and statistics are as they are at that moment).

### Controlled results: `idx_ratings_score_votes`

| Query | Without index (invisible) | With index (visible) | Median without | Median with | Effect |
|---|---|---|---:|---:|---|
| Q1 | 1.038 s, 0.244 s, 0.229 s | 0.287 s, 0.232 s, 0.228 s | 0.244 s | 0.232 s | 1.05x faster with index (within run-to-run noise) |
| Q2 | 82.3 s, 89.0 s | 371.0 s, 303.6 s | 85.6 s | 337.3 s | **3.9x slower with index** |

- The first Q1 run (1.038 s) was a cold-cache run.
- Q2 was run twice per configuration. Both configurations were consistent and the gap is large, so a third run was not needed. The two values in each "median" column are averaged.
- Results were identical in every run of each query. Q2 also matches the original verified run.

Based on these results, `idx_ratings_score_votes` was made invisible. Q1 loses about 5% (0.232 s to 0.244 s), and Q2 runs in about 86 s instead of about 337 s.

#### Why an index can make a query slower

The only plan difference in both queries is how `title_ratings` is read: a table scan (in `tconst` order) without the index, or a covering index scan (in `averageRating` order) with it. The optimizer gives the two plans almost the same cost (about 177,000 vs. 179,000 in Q2) and picks the index because it is smaller and contains every column it needs from `title_ratings`.

The cost model does not account for what happens after this step. In Q2, every ratings row is joined to `title_basics` and `title_principals` with primary-key lookups. InnoDB stores both tables clustered (physically ordered) by `tconst`:

- **Without the index:** ratings rows come out in `tconst` order, so consecutive lookups land on the same or neighboring pages. Each page is read from disk once and reused.
- **With the index:** ratings rows come out in rating order, so the `tconst` values jump around the whole table. Consecutive lookups hit unrelated pages, and with a 128 MB buffer pool (much smaller than the 6.4 GB `title_principals` table) most of them become separate random disk reads.

The measured times (3.9x slower) and the plans are consistent with this explanation, but the explanation itself is inferred; we did not measure page reads per configuration. In general, an index helps when it lets the database read much less data. Here the index only replaced a 60 MB scan, and the order it produced made the much larger joins slower.

### Single measured runs (Q3, Q4, Q5)

| Query | Time | Configuration when measured | Applies to final configuration? |
|---|---:|---|---|
| Q3 | 2 min 9.5 s | All indexes visible | Yes: the plan does not use `idx_ratings_score_votes`, and its structure is the same in the final configuration |
| Q4 | 32.0 s | All indexes visible | Yes: same reason |
| Q5 | 1 h 4 min 42.3 s | `idx_ratings_score_votes` visible | **No**: the final plan reads `title_ratings` with a table scan, and this plan was not timed |

Q5 takes about 65 minutes, so it was run once and not repeated. Its plan has the same difference as Q2 (index scan vs. table scan on `title_ratings`), so it may also be faster with the index invisible, but **Q5's runtime without the ratings index has not been measured**. Most of Q5's time is spent on temporary tables (about 3.7 GB) that do not fit in the 1 GB TempTable memory limit and go to disk, which the index does not affect.

### Experiment: index on `title_principals(nconst)`

Queries 2 and 3 start from people (deceased actors), so we tested an index on `title_principals(nconst)`:

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

The raw outputs behind every number in this section (run outputs with timings, `EXPLAIN` plans, the index experiments, and the verification exports) are in `results/final/`. `results/final/verification/verify.py` recomputes the Q2, Q3 and Q5 checks from the saved exports without a database.

The benchmark table in the previous version of this document was for an earlier set of queries and has been replaced.

## Running the Queries

From the project directory:

    mysql -u root -p < data/mysql/query1.sql

Replace `query1.sql` with the desired query file. Expected runtimes on our machine are listed above (Q5 takes about an hour).

To change the decade for Query 1, edit `@decade_start` at the top of `query1.sql`.

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
- **Number of runs:** Q1 has 3 runs per configuration and Q2 has 2. Q3 and Q4 have one run each. Q5 has one run, made with `idx_ratings_score_votes` visible; its runtime in the final configuration (index invisible) has not been measured.
- **Invisible indexes:** baseline runs use invisible indexes, which approximate but do not recreate an unindexed database.
- **Year precision:** IMDb only provides years. Q2 counts a movie as posthumous only if `startYear > deathYear`, so movies released in the year of death do not count. Q3 includes credits in the birth and death years.
- **Data quality:** some IMDb records have implausible years (for example, credits before birth). Q3 excludes them, but birth and death years themselves are taken as given.
- **No foreign keys:** inner joins skip credits that reference missing titles or people. Q5 handles people missing from `name_basics` in the same way as the MongoDB version.
- **Q1 decade:** the decade ends at the current year (2026 when measured), so the result can change as new movies and votes are added.
