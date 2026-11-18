import os
import requests
from config import RAW, TABLES, URL

os.makedirs(RAW, exist_ok=True)

for name in TABLES:
    file = TABLES[name]["file"]
    path = os.path.join(RAW, file)
    if os.path.exists(path):
        continue
    r = requests.get(URL + file, stream=True)
    f = open(path, "wb")
    for block in r.iter_content(chunk_size=1024 * 1024):
        f.write(block)
    f.close()
