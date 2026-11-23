// Indexes for mongo_queries.py  -  mongosh imdb mongo_indexes.js
// Lookups by _id use the default _id index.

// Query 1. Partial: only titles with 25k+ votes, so no other query uses it.
db.titles.createIndex({type: 1, "rating.votes": -1},
                      {partialFilterExpression: {"rating.votes": {$gte: 25000}}})

// Queries 2-5: no index needed. Their filters match too many documents, so I found that an index
// means random fetches instead of just one sequential scan. Tried ones were slower:
// 2: 158 -> 248 s, 4: 21 -> 80 s, 5: 912 -> 1681 s.
// So they were not included
