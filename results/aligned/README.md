# Evidence for the MongoDB-aligned queries

Queries 1–3 were rewritten to match the MongoDB pipelines in `mongo_queries.py`; Queries 4 and 5 were already equivalent and did not change (their evidence is in `results/final/`). All runs below completed, with the final index configuration (`idx_ratings_score_votes` invisible) unless the file name says `visible`.

## runs/

`mysql -vvv` output: query text, result rows and timing (`... rows in set (time)`). Results are identical across every run of each query.

| Files | What |
|---|---|
| `q1_run1.txt` | First run of Query 1 (cold cache) |
| `q1_invisible_1..3.txt`, `q1_visible_1..3.txt` | Query 1 with `idx_ratings_score_votes` invisible / visible, alternated |
| `q2_run1..3.txt` | Query 2, three runs |
| `q3_run1..3.txt` | Query 3, three runs |

## plans/

- `q1_final.txt` ... `q5_final.txt`: `EXPLAIN FORMAT=TREE` in the final configuration (estimates only).
- `q1_ratings_index_visible.txt`: Query 1 plan with the ratings index visible.
- `q2_explain_analyze.txt`: `EXPLAIN ANALYZE` of Query 2 with actual times per step.

## verification/

| Files | Check |
|---|---|
| `q1_check.sql`, `_output.txt` | Per-decade winner recomputed with `GROUP BY`/`MAX`; counts exact ties on rating and votes (none) |
| `q2_verify.py`, `_output.txt` | Splits `knownForTitles` in Python and recomputes the pick for 8 returned people and 3 controls (Heath Ledger, Paul Walker, James Dean) |
| `q2_ties.sql`, `_output.txt` | Counts people whose pick depends on a vote tie (none at the top-20 vote level) |
| `q3_credits.sql`, `.tsv`, `q3_verify.py`, `_output.txt` | All raw credits of 5 people, recomputed in Python with MongoDB's rules |
| `q3_spans.sql`, `_output.txt` | Number of people per career span near the top-20 cut-off |

## audit/

Edge-case checks from the final equivalence audit against `mongo_queries.py`:

| Files | Check |
|---|---|
| `edge_tests.sql`, `_output.txt` | Repeated titles in `knownForTitles` of deceased people (0); principal rows with every non-key field empty, which `load_mongo.py` would drop (0); rated movies whose credited people are all / partly missing from `name_basics` (1 / 123) |
| `q5_all_people_missing.sql`, `_output.txt` | The one such movie (`tt43561434`) |
| `q5_edge_movie_before/after.sql`, `_output.txt` | Query 5 limited to that movie: score `NULL` before the `COALESCE` fix, `0` after (MongoDB's `$sum` gives 0) |
| `q5_primer_after_fix.sql`, `_output.txt` | Control: Query 5 limited to *Primer*'s people after the fix still gives 309,875 |
| `q2_top22.sql`, `_output.txt` | Query 2 with `LIMIT 22`: first 20 rows equal the Query 2 result; the 21st has fewer votes than the 20th (no tie at the cut-off) |

The Python scripts run against the saved `.tsv` file (`q3_verify.py`) or query the database read-only (`q2_verify.py`, needs a `mysql --login-path=imdb` login).
