# MongoDB model

Run `python load_mongo.py` after `clean.py`. It loads into database `imdb`. Missing values are skipped (no nulls).

## titles

Each document is based off a single title. So rating, crew and principals are embedded into that document, as each belongs to exactly one title.

```
{
  _id: "tt0111161",
  type: "movie",
  title: "The Shawshank Redemption",
  isAdult: false,
  startYear: 1994,
  runtime: 142,
  genres: ["Drama"],
  rating: { average: 9.3, votes: 3100000 },
  directors: ["nm0001104"],
  writers: ["nm0000175", "nm0001104"],
  principals: [
    { person: "nm0000209", category: "actor", characters: ["Andy Dufresne"] },
    { person: "nm0001104", category: "director" }
  ]
}
```

People are stored by an ID only. Names come from `people` with `$lookup`.

## people

```
{
  _id: "nm0000209",
  name: "Tim Robbins",
  birthYear: 1958,
  professions: ["actor", "producer", "director"],
  knownFor: ["tt0111161", "tt0118799"]
}
```

## Compared with the relational model

Five tables become just two collections. Ratings, crew and principals move inside `titles`, so most queries no longer need to a join, and the comma-separated list columns become actual arrays.
