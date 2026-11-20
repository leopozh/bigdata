"""Run the MongoDB queries and time them.

python mongo_queries.py
"""
import os
import time
from pymongo import MongoClient


def star_studded(db):
    """Which movie has the most star-studded cast and crew?

    1. Each person's fame" is the total number of imdb votes of each project they have a credit on
    2. A movie's score is the sum of the fame of everyone credited on it, subtracting the votes each
       of them got from that movie.
    """
    db.titles.aggregate([
        {"$match": {"rating.votes": {"$exists": True}, "principals": {"$exists": True}}},
        {"$project": {"_id": 0, "votes": "$rating.votes",
                      "people": {"$setUnion": ["$principals.person", []]}}},
        {"$unwind": "$people"},
        {"$group": {"_id": "$people", "fame": {"$sum": "$votes"}}},
        {"$merge": {"into": "people", "on": "_id", "whenMatched": "merge", "whenNotMatched": "discard"}},
    ], allowDiskUse=True)

    return list(db.titles.aggregate([
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
    ], allowDiskUse=True))


QUERIES = [
    ("5. Most star-studded movies", star_studded),
]


def main():
    db = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017")).imdb
    for name, query in QUERIES:
        start = time.time()
        rows = query(db)
        print(name, round(time.time() - start, 2), "s")
        for row in rows:
            print(" ", row)
        print()


if __name__ == "__main__":
    main()
