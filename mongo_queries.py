"""Run the MongoDB queries and time them.

python mongo_queries.py  -  all queries
python mongo_queries.py 1 3  -  only queries 1 and 3
python mongo_queries.py --explain  -  print each query's plan instead of running it
"""
import os
import sys
import time
from pymongo import MongoClient

ACTING = ["actor", "actress"]
CAREER_MIN_SPAN = 60   # (query 3 only looks up people whose unfiltered span is at least this)
EXPLAIN = "--explain" in sys.argv


def plan_stages(node):
    """Flatten a winning plan into 'STAGE(index)' names, outermost first."""
    out = []
    while node:
        name = node.get("stage", "?")
        if node.get("indexName"):
            name += "(" + node["indexName"] + ")"
        out.append(name)
        node = node.get("inputStage") or (node.get("inputStages") or [None])[0] or node.get("queryPlan")
    return out


def find_plan(res):
    if "queryPlanner" in res:
        return res["queryPlanner"]["winningPlan"]
    for stage in res.get("stages", []):
        if "$cursor" in stage:
            return stage["$cursor"]["queryPlanner"]["winningPlan"]
    return None


def run(coll, pipeline):
    """Run an aggregation, or with --explain print its plan instead."""
    if not EXPLAIN:
        return list(coll.aggregate(pipeline, allowDiskUse=True))
    res = coll.database.command("explain", {"aggregate": coll.name, "pipeline": pipeline, "cursor": {}},
                                verbosity="queryPlanner")
    print("  " + coll.name + ": " + " <- ".join(plan_stages(find_plan(res))))
    later = [next(iter(s)) for s in res.get("stages", [])[1:]]
    if later:
        print("    then " + ", ".join(later))
    return []


def best_per_decade(db):
    """Best movie of each decade by IMDb rating, among movies with at least 25k votes."""
    return run(db.titles, [
        {"$match": {"type": "movie", "rating.votes": {"$gte": 25000}, "startYear": {"$exists": True}}},
        {"$project": {"title": 1, "startYear": 1, "rating": 1,
                      "decade": {"$subtract": ["$startYear", {"$mod": ["$startYear", 10]}]}}},
        {"$sort": {"rating.average": -1, "rating.votes": -1}},
        {"$group": {"_id": "$decade", "title": {"$first": "$title"}, "year": {"$first": "$startYear"},
                    "rating": {"$first": "$rating.average"}, "votes": {"$first": "$rating.votes"}}},
        {"$project": {"_id": 0, "decade": "$_id", "title": 1, "year": 1, "rating": 1, "votes": 1}},
        {"$sort": {"decade": 1}},
    ])


def died_before_best_known(db):
    """Actors who died before their best known movie came out.

    Best known movie: the knownFor movie with the most votes which they have an acting credit on.
    """
    return run(db.people, [
        {"$match": {"deathYear": {"$exists": True}, "knownFor": {"$exists": True}}},
        {"$lookup": {
            "from": "titles", "localField": "knownFor", "foreignField": "_id",
            "let": {"person": "$_id"},
            "pipeline": [
                {"$match": {"type": "movie"}},
                {"$project": {"title": 1, "startYear": 1, "votes": "$rating.votes",
                              "acted": {"$anyElementTrue": [{"$map": {
                                  "input": {"$ifNull": ["$principals", []]},
                                  "in": {"$and": [{"$eq": ["$$this.person", "$$person"]},
                                                  {"$in": ["$$this.category", ACTING]}]}}}]}}},
                {"$match": {"acted": True}},
            ],
            "as": "movie"}},
        {"$unwind": "$movie"},
        {"$sort": {"movie.votes": -1}},
        {"$group": {"_id": "$_id", "name": {"$first": "$name"}, "deathYear": {"$first": "$deathYear"},
                    "best": {"$first": "$movie"}}},
        {"$match": {"$expr": {"$gt": ["$best.startYear", "$deathYear"]}}},
        {"$sort": {"best.votes": -1}},
        {"$limit": 20},
        {"$project": {"_id": 0, "name": 1, "deathYear": 1, "movie": "$best.title",
                      "released": "$best.startYear", "votes": "$best.votes"}},
    ])


def longest_careers(db):
    """People with the longest careers (first to last credit).

    Only people with both a birth and death year on IMDb, and only credits of movies made between the two.
    The filtering done can only shorten a span, so only people whose unfiltered span is at least
    CAREER_MIN_SPAN are even looked up, although main() checks that the 20th result is still above that.
    """
    return run(db.titles, [
        {"$match": {"startYear": {"$exists": True}, "principals": {"$exists": True}}},
        {"$project": {"_id": 0, "startYear": 1, "people": {"$setUnion": ["$principals.person", []]}}},
        {"$unwind": "$people"},
        {"$group": {"_id": "$people", "years": {"$addToSet": "$startYear"},
                    "first": {"$min": "$startYear"}, "last": {"$max": "$startYear"}}},
        {"$match": {"$expr": {"$gte": [{"$subtract": ["$last", "$first"]}, CAREER_MIN_SPAN]}}},
        {"$lookup": {"from": "people", "localField": "_id", "foreignField": "_id", "as": "person"}},
        {"$project": {"name": {"$arrayElemAt": ["$person.name", 0]},
                      "born": {"$arrayElemAt": ["$person.birthYear", 0]},
                      "died": {"$arrayElemAt": ["$person.deathYear", 0]},
                      "years": 1}},
        {"$match": {"born": {"$exists": True}, "died": {"$exists": True}}},
        {"$project": {"name": 1, "born": 1, "died": 1, "years": {"$filter": {
            "input": "$years",
            "cond": {"$and": [{"$gte": ["$$this", "$born"]}, {"$lte": ["$$this", "$died"]}]}}}}},
        {"$project": {"_id": 0, "name": 1, "born": 1, "died": 1,
                      "first": {"$min": "$years"}, "last": {"$max": "$years"},
                      "span": {"$subtract": [{"$max": "$years"}, {"$min": "$years"}]}}},
        {"$sort": {"span": -1}},
        {"$limit": 20},
    ])


def biggest_casts(db):
    """Movies with the most principals."""
    return run(db.titles, [
        {"$match": {"type": "movie", "principals": {"$exists": True}}},
        {"$project": {"title": 1, "startYear": 1, "principals": {"$size": "$principals"}}},
        {"$sort": {"principals": -1, "_id": 1}},
        {"$limit": 20},
        {"$project": {"_id": 0}},
    ])


def star_studded(db):
    """Which movie has the most star-studded cast and crew?

    1. Each person's fame" is the total number of imdb votes of each project they have a credit on
    2. A movie's score is the sum of the fame of everyone credited on it, subtracting the votes each
       of them got from that movie.
    """
    run(db.titles, [
        {"$match": {"rating.votes": {"$exists": True}, "principals": {"$exists": True}}},
        {"$project": {"_id": 0, "votes": "$rating.votes",
                      "people": {"$setUnion": ["$principals.person", []]}}},
        {"$unwind": "$people"},
        {"$group": {"_id": "$people", "fame": {"$sum": "$votes"}}},
        {"$merge": {"into": "people", "on": "_id", "whenMatched": "merge", "whenNotMatched": "discard"}},
    ])

    return run(db.titles, [
        {"$match": {"type": "movie", "rating.votes": {"$exists": True}, "principals": {"$exists": True}}},
        {"$project": {"title": 1, "startYear": 1, "rating": 1,
                      "people": {"$setUnion": ["$principals.person", []]}}},
        {"$unwind": "$people"},
        {"$lookup": {"from": "people", "localField": "people", "foreignField": "_id",
                     "pipeline": [{"$project": {"fame": 1}}], "as": "person"}},
        {"$group": {
            "_id": "$_id",
            "title": {"$first": "$title"},
            "year": {"$first": "$startYear"},
            "rating": {"$first": "$rating"},
            "people": {"$sum": 1},
            "score": {"$sum": {"$subtract": [{"$arrayElemAt": ["$person.fame", 0]}, "$rating.votes"]}},
        }},
        {"$sort": {"score": -1}},
        {"$limit": 20},
    ])


QUERIES = [
    ("1. Best movie of each decade", best_per_decade),
    ("2. Actors who died before their best known movie", died_before_best_known),
    ("3. Longest careers", longest_careers),
    ("4. Biggest casts", biggest_casts),
    ("5. Most star-studded movies", star_studded),
]


def main():
    db = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017")).imdb
    only = [a for a in sys.argv[1:] if a.isdigit()]
    for name, query in QUERIES:
        if only and name.split(".")[0] not in only:
            continue
        start = time.time()
        if EXPLAIN:
            print(name)
        rows = query(db)
        if EXPLAIN:
            print()
            continue
        print(name, round(time.time() - start, 2), "s")
        if query is longest_careers and len(rows) == 20 and rows[-1]["span"] < CAREER_MIN_SPAN:
            print("  warning: lower CAREER_MIN_SPAN, the cutoff may have dropped real results")
        for row in rows:
            print(" ", row)
        print()


if __name__ == "__main__":
    main()
