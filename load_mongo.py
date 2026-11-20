"""Load the cleaned IMDb CSVs (output of clean.py) into MongoDB.

python load_mongo.py  - full load
python load_mongo.py --limit N  - only the first N titles and N people, for testing

There are two collections:
titles - one document per title_basics row, with its rating, crew and principals embedded
people - one document per name_basics row

Every IMDb file is sorted by its key as a string, so the four title files are merged
in a single pass instead of needing to be joined in memory.
Missing values are skipped (no nulls).
"""
import csv
import json
import os
import sys
import time
from pymongo import MongoClient
from config import CLEAN

BATCH = 5000
csv.field_size_limit(10 ** 8)


def rows(table):
    """Yield each cleaned CSV row as a dict, with empty strings removed."""
    with open(os.path.join(CLEAN, table + ".csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            yield {k: v for k, v in row.items() if v != ""}


def grouped(table, key, limit_key=None):
    """Yield (key value, [rows]) for consecutive rows with the same key. Checks the sort order."""
    prev = None
    group = []
    for row in rows(table):
        k = row[key]
        if k != prev:
            if prev is not None:
                if k < prev:
                    raise ValueError(table + " is not sorted by " + key + ": " + k + " after " + prev)
                yield prev, group
            prev = k
            group = []
        group.append(row)
    if prev is not None:
        yield prev, group


def to_list(s):
    return s.split(",")


def to_characters(s):
    try:
        value = json.loads(s)
        return value if isinstance(value, list) else [str(value)]
    except ValueError:
        return [s]


def set_if(doc, field, value):
    if value is not None and value != []:
        doc[field] = value


def title_doc(basic, rating, crew, principals):
    doc = {"_id": basic["tconst"], "type": basic.get("titleType"), "title": basic.get("primaryTitle")}
    doc = {k: v for k, v in doc.items() if v is not None}
    if "originalTitle" in basic and basic["originalTitle"] != basic.get("primaryTitle"):
        doc["originalTitle"] = basic["originalTitle"]
    if "isAdult" in basic:
        doc["isAdult"] = basic["isAdult"] == "1"
    for src, dst in (("startYear", "startYear"), ("endYear", "endYear"), ("runtimeMinutes", "runtime")):
        if src in basic:
            doc[dst] = int(basic[src])
    if "genres" in basic:
        doc["genres"] = to_list(basic["genres"])
    if rating:
        r = rating[0]
        sub = {}
        if "averageRating" in r:
            sub["average"] = float(r["averageRating"])
        if "numVotes" in r:
            sub["votes"] = int(r["numVotes"])
        set_if(doc, "rating", sub or None)
    if crew:
        c = crew[0]
        if "directors" in c:
            doc["directors"] = to_list(c["directors"])
        if "writers" in c:
            doc["writers"] = to_list(c["writers"])
    if principals:
        principals.sort(key=lambda p: int(p.get("ordering", 0)))
        cast = []
        for p in principals:
            entry = {"person": p["nconst"]} if "nconst" in p else {}
            if "category" in p:
                entry["category"] = p["category"]
            if "job" in p:
                entry["job"] = p["job"]
            if "characters" in p:
                entry["characters"] = to_characters(p["characters"])
            if entry:
                cast.append(entry)
        set_if(doc, "principals", cast)
    return doc


def person_doc(row):
    doc = {"_id": row["nconst"]}
    if "primaryName" in row:
        doc["name"] = row["primaryName"]
    if "birthYear" in row:
        doc["birthYear"] = int(row["birthYear"])
    if "deathYear" in row:
        doc["deathYear"] = int(row["deathYear"])
    if "primaryProfession" in row:
        doc["professions"] = to_list(row["primaryProfession"])
    if "knownForTitles" in row:
        doc["knownFor"] = to_list(row["knownForTitles"])
    return doc


class Side:
    """One of the secondary title tables, advanced at the same time as title_basics."""

    def __init__(self, table):
        self.table = table
        self.it = grouped(table, "tconst")
        self.cur = next(self.it, None)
        self.orphans = 0

    def take(self, tconst):
        while self.cur is not None and self.cur[0] < tconst:
            self.orphans += len(self.cur[1])
            self.cur = next(self.it, None)
        if self.cur is not None and self.cur[0] == tconst:
            group = self.cur[1]
            self.cur = next(self.it, None)
            return group
        return None

    def finish(self):
        while self.cur is not None:
            self.orphans += len(self.cur[1])
            self.cur = next(self.it, None)


def insert_all(coll, docs, label):
    start = time.time()
    batch = []
    n = 0
    for doc in docs:
        batch.append(doc)
        if len(batch) == BATCH:
            coll.insert_many(batch, ordered=False)
            n += len(batch)
            batch = []
            if n % 1000000 == 0:
                print(label, n, "docs", round(time.time() - start), "s", flush=True)
    if batch:
        coll.insert_many(batch, ordered=False)
        n += len(batch)
    print(label, n, "docs in", round(time.time() - start), "s", flush=True)
    return n


def load_titles(db, limit):
    sides = {name: Side(name) for name in ("title_ratings", "title_crew", "title_principals")}

    def docs():
        for i, (tconst, basic) in enumerate(grouped("title_basics", "tconst")):
            if limit and i >= limit:
                return
            yield title_doc(basic[0],
                            sides["title_ratings"].take(tconst),
                            sides["title_crew"].take(tconst),
                            sides["title_principals"].take(tconst))

    db.titles.drop()
    insert_all(db.titles, docs(), "titles")
    if not limit:
        for side in sides.values():
            side.finish()
            print(side.table, "rows with no matching title:", side.orphans)


def load_people(db, limit):
    def docs():
        for i, row in enumerate(rows("name_basics")):
            if limit and i >= limit:
                return
            yield person_doc(row)

    db.people.drop()
    insert_all(db.people, docs(), "people")


def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 0
    client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017"))
    db = client.imdb
    start = time.time()
    load_titles(db, limit)
    load_people(db, limit)
    print("total", round(time.time() - start), "s")


if __name__ == "__main__":
    main()
