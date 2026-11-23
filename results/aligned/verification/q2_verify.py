"""Recompute Query 2 for sample people: split knownForTitles in Python, look up each title by PK."""
import subprocess, sys
M = ["/usr/local/mysql/bin/mysql", "--login-path=imdb", "imdb", "-B", "-N", "-e"]
def q(sql):
    out = subprocess.run(M + [sql], capture_output=True, text=True, check=True).stdout
    return [line.split("\t") for line in out.splitlines()]
people = sys.argv[1:]
for nconst in people:
    name, death, known = q(f"SELECT primaryName, deathYear, knownForTitles FROM name_basics WHERE nconst='{nconst}'")[0]
    cands = []
    for t in dict.fromkeys(known.split(",")) if known != "NULL" else []:
        row = q(f"""SELECT b.titleType, b.startYear, IFNULL(r.numVotes,'NULL'),
                   (SELECT COUNT(*) FROM title_principals p WHERE p.tconst=b.tconst AND p.nconst='{nconst}' AND p.category IN ('actor','actress'))
                   FROM title_basics b LEFT JOIN title_ratings r ON r.tconst=b.tconst WHERE b.tconst='{t}'""")
        if row and row[0][0] == "movie" and int(row[0][3]) > 0:
            votes = None if row[0][2] == "NULL" else int(row[0][2])
            cands.append((t, row[0][1], votes))
    # most votes first, unrated last, tconst as final tiebreak
    cands.sort(key=lambda c: (c[2] is None, -(c[2] or 0), c[0]))
    best = cands[0] if cands else None
    post = best is not None and best[1] != "NULL" and death != "NULL" and int(best[1]) > int(death)
    print(f"{nconst:<10} {name[:20]:<20} died {death:<5} candidates {len(cands)} best {best} -> {'POSTHUMOUS' if post else 'excluded'}")
