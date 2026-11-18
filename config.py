import os

URL = "https://datasets.imdbws.com/"
HOME = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HOME, "data", "raw")
CLEAN = os.path.join(HOME, "data", "clean")
MYSQL = os.path.join(HOME, "data", "mysql")
MONGO = os.path.join(HOME, "data", "mongo")
MIN_ROWS = 50000000
CHUNK = 1000000

TABLES = {
    "name_basics": {
        "file": "name.basics.tsv.gz",
        "key": ["nconst"],
        "columns": {
            "nconst": "id",
            "primaryName": "str",
            "birthYear": "int",
            "deathYear": "int",
            "primaryProfession": "list",
            "knownForTitles": "list",
        },
    },
    "title_akas": {
        "file": "title.akas.tsv.gz",
        "key": ["titleId", "ordering"],
        "columns": {
            "titleId": "id",
            "ordering": "int",
            "title": "text",
            "region": "str",
            "language": "str",
            "types": "list",
            "attributes": "list",
            "isOriginalTitle": "bool",
        },
    },
    "title_basics": {
        "file": "title.basics.tsv.gz",
        "key": ["tconst"],
        "columns": {
            "tconst": "id",
            "titleType": "str",
            "primaryTitle": "text",
            "originalTitle": "text",
            "isAdult": "bool",
            "startYear": "int",
            "endYear": "int",
            "runtimeMinutes": "int",
            "genres": "list",
        },
    },
    "title_crew": {
        "file": "title.crew.tsv.gz",
        "key": ["tconst"],
        "columns": {
            "tconst": "id",
            "directors": "list",
            "writers": "list",
        },
    },
    "title_episode": {
        "file": "title.episode.tsv.gz",
        "key": ["tconst"],
        "columns": {
            "tconst": "id",
            "parentTconst": "id",
            "seasonNumber": "int",
            "episodeNumber": "int",
        },
    },
    "title_principals": {
        "file": "title.principals.tsv.gz",
        "key": ["tconst", "ordering"],
        "columns": {
            "tconst": "id",
            "ordering": "int",
            "nconst": "id",
            "category": "str",
            "job": "text",
            "characters": "json",
        },
    },
    "title_ratings": {
        "file": "title.ratings.tsv.gz",
        "key": ["tconst"],
        "columns": {
            "tconst": "id",
            "averageRating": "float",
            "numVotes": "int",
        },
    },
}
