import csv
from collections import defaultdict

rows = list(csv.DictReader(open("live_log.csv")))
groups = defaultdict(list)
for r in rows:
    groups[r["label"]].append(r)
for label, g in groups.items():
    n = len(g)
    allow = sum(r["decision"] == "ALLOW" for r in g)
    deny = sum(r["decision"] == "DENY" for r in g)
    avg = sum(float(r["post_seconds"]) for r in g) / n
    kind = "false rejects" if label == "live" else "false accepts"
    bad = (n - allow) if label == "live" else allow
    print(f"{label}: {n} tries | allow {allow} | deny {deny} | {kind}: {bad} | avg after capture {avg:.2f}s")