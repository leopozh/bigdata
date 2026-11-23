"""Recompute the MySQL verification checks from the saved credit exports (no database needed).

python results/final/verification/verify.py

Each *.tsv file was exported with the matching *.sql file in this folder.
"""
import csv
import os
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))


def read(name):
    with open(os.path.join(HERE, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def by_person(rows):
    people = {}
    for r in rows:
        people.setdefault(r["nconst"], []).append(r)
    return people


def q2():
    """Best-known movie (rating, votes, tconst) per actor, then the posthumous check."""
    print("Query 2: best-known movie per actor")
    for nconst, rows in sorted(by_person(read("q2_credits.tsv")).items()):
        best = min(rows, key=lambda r: (-Decimal(r["averageRating"]), -int(r["numVotes"]), r["tconst"]))
        death = int(rows[0]["deathYear"])
        posthumous = int(best["startYear"]) > death
        print(f"  {nconst:<11} {rows[0]['primaryName'][:22]:<22} died {death}  best {best['tconst']} "
              f"({best['startYear']}, {best['averageRating']})  {'posthumous' if posthumous else 'NOT posthumous'}")


def q3():
    """Career span using only credits between birth and death, not in the future."""
    print("Query 3: career spans from unfiltered credits")
    for nconst, rows in sorted(by_person(read("q3_credits.tsv")).items()):
        birth, death = int(rows[0]["birthYear"]), int(rows[0]["deathYear"])
        years = {r["tconst"]: int(r["startYear"]) for r in rows if r["startYear"] != "NULL"}
        valid = [y for y in years.values() if birth <= y <= death and y <= 2026]
        print(f"  {nconst:<10} movies {len(valid):>3}  first {min(valid)}  last {max(valid)}  "
              f"span {max(valid) - min(valid)}  (excluded: {len(years) - len(valid)})")


def q5(file, movie):
    """fame = votes over distinct rated titles; score = sum(fame - movie votes) over distinct people."""
    rows = read(file)
    movie_votes = next(int(r["numVotes"]) for r in rows if r["tconst"] == movie)
    pairs = {(r["tconst"], r["nconst"]): int(r["numVotes"]) for r in rows
             if r["numVotes"] != "NULL" and r["inBasics"] == "1" and r["nconst"] != "NULL"}
    named = {r["nconst"] for r in rows if r["inNames"] == "1"}
    fame = {}
    for (_, nconst), votes in pairs.items():
        if nconst in named:
            fame[nconst] = fame.get(nconst, 0) + votes
    people = {r["nconst"] for r in rows if r["tconst"] == movie and r["nconst"] != "NULL"}
    score = sum(fame[p] - movie_votes for p in people if p in fame)
    print(f"Query 5: {movie}  credit rows {sum(r['tconst'] == movie for r in rows)}  "
          f"distinct people {len(people)}  starScore {score}")


if __name__ == "__main__":
    q2()
    q3()
    q5("q5_primer_credits.tsv", "tt0390384")
    q5("q5_batman_begins_credits.tsv", "tt0372784")
