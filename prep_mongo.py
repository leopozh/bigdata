import gzip
import json
import os
import pandas as pd
from config import CHUNK, CLEAN, MONGO, TABLES

os.makedirs(MONGO, exist_ok=True)

def parse_json(value):
    if pd.isna(value):
        return None
    return json.loads(value)

def convert_chunk(chunk, columns):
    for col in columns:
        kind = columns[col]
        s = chunk[col]
        if kind == "int":
            s = s.astype("Int64")
        if kind == "float":
            s = s.astype("Float64")
        if kind == "bool":
            s = s.astype("Int64").astype("boolean")
        if kind == "list":
            s = s.str.split(",")
        if kind == "json":
            s = s.map(parse_json)
        chunk[col] = s
    chunk = chunk.astype(object)
    chunk = chunk.where(chunk.notna(), None)
    return chunk

script = ""

for name in TABLES:
    columns = TABLES[name]["columns"]
    src = os.path.join(CLEAN, name + ".csv")
    out = os.path.join(MONGO, name + ".json.gz")
    reader = pd.read_csv(src, dtype="string", na_values=[""], keep_default_na=False, chunksize=CHUNK)
    f = gzip.open(out, "wt", encoding="utf-8", compresslevel=1)
    for chunk in reader:
        chunk = convert_chunk(chunk, columns)
        f.write(chunk.to_json(orient="records", lines=True, force_ascii=False))
    f.close()
    script = script + 'gunzip -c "' + out + '" | mongoimport --db imdb --collection ' + name + " --type json --drop\n"

f = open(os.path.join(MONGO, "import.sh"), "w")
f.write(script)
f.close()
