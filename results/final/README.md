# MySQL benchmark and verification evidence

Saved outputs behind the numbers in `docs/mysql.md`. All runs used the `mysql` client with `-vvv`, so each `.txt` file contains the query text, the result rows, and the timing line (`20 rows in set (...)`).

## runs/

All runs in this folder completed.

| File | What it is |
|---|---|
| `q1_base_1..3.txt`, `q1_idx_1..3.txt` | Controlled Q1 runs, `idx_ratings_score_votes` invisible (`base`) or visible (`idx`), alternated |
| `q2_base_1..2.txt`, `q2_idx_1..2.txt` | Controlled Q2 runs, same method |
| `q2_first_run.txt` ... `q5_first_run.txt` | First verified run of each query, with `idx_ratings_score_votes` visible. Q5 was only run in this configuration; its time with the index invisible (the final configuration) was not measured. |

## plans/

`EXPLAIN FORMAT=TREE` output (estimates only, nothing executed):

- `q*_final.txt`: final configuration (ratings index invisible, `deathYear` histogram present).
- `q1/q2/q5_ratings_index_invisible.txt` and `_visible.txt`: the two benchmark configurations.
- `q2/q3_before_histogram.txt` and `_after_histogram.txt`: effect of the `deathYear` histogram.

## experiments/

- `nconst_index_build.txt`: build of the tested `title_principals(nconst)` index (later dropped).
- `q2/q3_join_order_hint.sql`: scratch copies of Q2/Q3 that force the `nconst` index with `JOIN_ORDER`.
- `q2/q3_join_order_hint_explain_analyze.txt`: `EXPLAIN ANALYZE` output of **interrupted runs**. Both were cancelled (`KILL QUERY`) at about 2x the baseline time and never completed; the actual row counts show how far each run got. Their results were not compared with the original queries.

## verification/

- `*.sql` + `*.tsv`: credit exports used to recompute Q2, Q3 and Q5 outside SQL; `q4_check.sql` is the alternative Q4 formulation.
- `q5_primer_restricted.sql`: Query 5's SQL restricted to the people credited on *Primer*.
- `verify.py`: recomputes the Q2, Q3 and Q5 checks from the `.tsv` files without a database:

      python results/final/verification/verify.py
