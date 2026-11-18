import csv
import os
import pandas as pd
from config import CHUNK, CLEAN, RAW, TABLES

os.makedirs(CLEAN, exist_ok=True)

def clean_chunk(chunk, columns):
    for col in columns:
        kind = columns[col]
        s = chunk[col].str.strip().replace("", pd.NA)
        if kind == "int" or kind == "bool":
            s = pd.to_numeric(s, errors="coerce").astype("Int64")
        if kind == "float":
            s = pd.to_numeric(s, errors="coerce").astype("Float64")
        if kind == "list":
            s = s.str.replace("\x02", ",", regex=False)
        chunk[col] = s
    return chunk

for name in TABLES:
    columns = TABLES[name]["columns"]
    key = TABLES[name]["key"]
    src = os.path.join(RAW, TABLES[name]["file"])
    out = os.path.join(CLEAN, name + ".csv")
    reader = pd.read_csv(src, sep="\t", dtype="string", na_values=["\\N"], keep_default_na=False, quoting=csv.QUOTE_NONE, chunksize=CHUNK, on_bad_lines="skip")
    total = 0
    kept = 0
    prev = None
    first = True
    for chunk in reader:
        total = total + len(chunk)
        chunk = clean_chunk(chunk[list(columns)], columns)
        chunk = chunk.dropna(subset=key)
        chunk = chunk.drop_duplicates(subset=key)
        if prev is not None:
            chunk = chunk[~(chunk[key] == prev).all(axis=1)]
        if len(chunk) > 0:
            prev = chunk[key].iloc[-1].tolist()
        if first:
            chunk.to_csv(out, index=False, lineterminator="\n")
            first = False
        else:
            chunk.to_csv(out, mode="a", header=False, index=False, lineterminator="\n")
        kept = kept + len(chunk)
    print(name, total, kept)
