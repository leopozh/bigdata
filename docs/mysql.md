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
| Query 3 | 324 ms | 190 ms | 1.71x |
| Query 4 | 21.6 s | 6.24 s | 3.5x |
| Query 5 | 337 ms | 306 ms | 1.10x |

Queries 1, 2, and 4 use individual benchmark runs. Queries 3 and 5 use medians of three baseline/indexed runs. Execution times can vary due to caching and system load.

The ratings index improved the first two queries. The episode index helped Query 4 by allowing MySQL to use a covering index scan during aggregation.

Query 3 required multiple joins and grouping, which made it more expensive. Query 5 used `JSON_TABLE` to separate genres and calculate average ratings.

## Running the Queries

From the project directory:

`mysql -u root -p < data/mysql/query1.sql`

Replace `query1.sql` with the desired query file.

## Loading the data

Place the seven cleaned IMDb CSV files in `data/clean/`.

From the repository root, run:

    mysql --local-infile=1 -u root -p imdb < data/mysql/load_portable.sql

Run this only on an empty database after creating the tables with `schema.sql`. The CSV files are not included in GitHub because of their size.

## Functional Dependencies

IMDb uses unique identifiers for titles and people. The primary keys in our schema give us the following functional dependencies:

| Table | Functional dependency |
|---|---|
| `name_basics` | `nconst` determines the person's name, birth/death years, professions, and known titles |
| `title_basics` | `tconst` determines the title type, names, years, runtime, and genres |
| `title_akas` | (`titleId`, `ordering`) determines the alternate title and its region, language, and other attributes |
| `title_crew` | `tconst` determines the directors and writers |
| `title_episode` | `tconst` determines the parent series, season number, and episode number |
| `title_principals` | (`tconst`, `ordering`) determines the person, category, job, and characters |
| `title_ratings` | `tconst` determines the average rating and number of votes |

These dependencies follow from IMDb's identifiers and the primary keys used in our relational model. For example, a title has one `tconst`, but it can have multiple alternate titles and credited people. That is why `title_akas` and `title_principals` use composite primary keys.

## Normalization

Our relational model separates information about titles, people, ratings, episodes, crew, and alternate titles into seven tables. This reduces repeated data. For example, an actor's name is stored in `name_basics` instead of being repeated for every movie credit in `title_principals`. Similarly, ratings are stored separately from basic title information.

Most tables use a single identifier as their primary key, while `title_akas` and `title_principals` use composite keys to represent multiple records associated with one title. The non-key columns depend on the full primary key in each table.

However, some IMDb fields contain comma-separated lists, including `genres`, `directors`, `writers`, and `knownForTitles`. These are convenient for loading the original dataset but are not fully atomic under a strict interpretation of First Normal Form (1NF). A more normalized design would create separate tables such as `title_genres`, `title_directors`, and `title_writers`, with one value per row.

We kept these fields in their original form to preserve the dataset structure and avoid creating additional tables during loading. This is a tradeoff between normalization and implementation complexity.
