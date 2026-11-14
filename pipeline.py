import csv, glob, os
from collections import defaultdict
import core

if __name__ == "__main__":
    ref = core.load_ref()
    rows = []
    for p in sorted(glob.glob("photos/tests/*.*")):
        if not p.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        with open(p, "rb") as f:
            r = core.analyze_still(f.read(), ref)
        r["file"] = os.path.basename(p)
        r["label"] = r["file"].split("_")[0]
        rows.append(r)
        print(r["file"], r["decision"], f"{r['similarity']:.0f}", f"{r['seconds']}s", "-", r["reason"])

    if rows:
        keys = ["file", "label", "decision", "reason", "similarity", "sharpness", "seconds"]
        with open("results.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

        live = [r for r in rows if r["label"] == "live"]
        spoof = [r for r in rows if r["label"] not in ("live", "noface")]
        print("\n--- SUMMARY ---")
        if live:
            print(f"False rejection (live not allowed): {sum(r['decision'] != 'ALLOW' for r in live)}/{len(live)}")
        if spoof:
            print(f"False acceptance (spoof allowed):   {sum(r['decision'] == 'ALLOW' for r in spoof)}/{len(spoof)}")
        groups = defaultdict(list)
        for r in rows:
            groups[r["label"]].append(r)
        for label, g in groups.items():
            n = lambda d: sum(r["decision"] == d for r in g)
            avg = sum(r["seconds"] for r in g) / len(g)
            print(f"{label}: {len(g)} images | allow {n('ALLOW')} | verify {n('REQUEST_VERIFICATION')} | deny {n('DENY')} | avg {avg:.2f}s")