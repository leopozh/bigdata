import os
from config import CLEAN, MYSQL, TABLES

TYPES = {
    "id": "VARCHAR(12)",
    "str": "VARCHAR(255)",
    "text": "TEXT",
    "int": "INT",
    "float": "DECIMAL(3,1)",
    "bool": "TINYINT(1)",
    "list": "TEXT",
    "json": "TEXT"
}

os.makedirs(MYSQL, exist_ok=True)

schema = "CREATE DATABASE IF NOT EXISTS imdb CHARACTER SET utf8mb4;\nUSE imdb;\n\n"
load = "USE imdb;\n\n"

for name in TABLES:
    columns = TABLES[name]["columns"]
    key = TABLES[name]["key"]
    lines = []
    for col in columns:
        line = "  " + col + " " + TYPES[columns[col]]
        if col in key:
            line = line + " NOT NULL"
        lines.append(line)
    lines.append("  PRIMARY KEY (" + ", ".join(key) + ")")
    schema = schema + "DROP TABLE IF EXISTS " + name + ";\n"
    schema = schema + "CREATE TABLE " + name + " (\n" + ",\n".join(lines) + "\n);\n\n"
    path = os.path.join(CLEAN, name + ".csv")
    fields = []
    sets = []
    for col in columns:
        fields.append("@" + col)
        sets.append("  " + col + " = NULLIF(@" + col + ", '')")
    load = load + "LOAD DATA LOCAL INFILE '" + path + "'\n"
    load = load + "INTO TABLE " + name + "\n"
    load = load + "CHARACTER SET utf8mb4\n"
    load = load + "FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' ESCAPED BY ''\n"
    load = load + "LINES TERMINATED BY '\\n'\n"
    load = load + "IGNORE 1 LINES\n"
    load = load + "(" + ", ".join(fields) + ")\n"
    load = load + "SET\n" + ",\n".join(sets) + ";\n\n"

f = open(os.path.join(MYSQL, "schema.sql"), "w")
f.write(schema)
f.close()
f = open(os.path.join(MYSQL, "load.sql"), "w")
f.write(load)
f.close()
