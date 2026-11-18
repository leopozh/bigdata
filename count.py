import os
from config import CLEAN, MIN_ROWS, TABLES

total = 0
for name in TABLES:
    path = os.path.join(CLEAN, name + ".csv")
    n = -1
    for line in open(path, "rb"):
        n = n + 1
    print(name, n)
    total = total + n
print(total)
print(total >= MIN_ROWS)
