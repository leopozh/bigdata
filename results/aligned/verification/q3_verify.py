"""Recompute Query 3 (MongoDB semantics) for sample people from all their raw credits."""
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8"), delimiter="\t"))
people = {}
for r in rows:
    people.setdefault(r["nconst"], []).append(r)
for nconst, rs in sorted(people.items()):
    born, died = int(rs[0]["birthYear"]), int(rs[0]["deathYear"])
    years = {int(r["startYear"]) for r in rs if r["startYear"] != "NULL"}          # $addToSet startYear
    valid = [y for y in years if born <= y <= died]                                 # $filter born..died
    cats = sorted({r["category"] for r in rs}); types = sorted({r["titleType"] for r in rs})
    print(f"{nconst:<10} credits {len(rs):>4}  unfiltered span {max(years)-min(years):>3}  "
          f"first {min(valid)} last {max(valid)} span {max(valid)-min(valid)}  "
          f"excluded years {len(years)-len(valid)}  categories {len(cats)} types {len(types)}")
