import csv
import os
import pandas as pd
from config import CHUNK, RAW, TABLES

for name in TABLES:
    path = os.path.join(RAW, TABLES[name]["file"])
    reader = pd.read_csv(path, sep="\t", dtype="string", na_values=["\\N"], keep_default_na=False, quoting=csv.QUOTE_NONE, chunksize=CHUNK, on_bad_lines="skip")
    rows = 0
    missing = 0
    for chunk in reader:
        if rows == 0:
            print(list(chunk.columns))
            print(chunk.head(3))
        rows = rows + len(chunk)
        missing = missing + chunk.isna().sum()
    print(name, rows)
    print(missing)
