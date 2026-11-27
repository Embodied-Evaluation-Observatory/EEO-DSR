#!/usr/bin/env python3
"""Audit duplicate metadata rows as real-positive candidates.

No fingerprints, no threshold, no synthetic copy.  A duplicate UUID with
identical fields is a real positive candidate (same episode record repeated);
a duplicate UUID with conflicting fields is a data-quality finding.  Both are
counted separately and every count carries its row universe.
"""
from __future__ import annotations
import argparse, csv, json
from collections import defaultdict
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-meta", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--csv-out")
    args = ap.parse_args()
    rows = list(csv.DictReader(open(args.raw_meta, newline="", encoding="utf-8")))
    fields = list(rows[0].keys())
    by = defaultdict(list)
    for i, r in enumerate(rows):
        by[r["uuid"]].append((i, r))
    dup_groups = {k: v for k, v in by.items() if len(v) > 1}
    exact, conflict = [], []
    for k, v in dup_groups.items():
        base = v[0][1]
        diffs = []
        for j, r in v[1:]:
            for f in fields:
                if r.get(f) != base.get(f):
                    if f not in diffs: diffs.append(f)
        if diffs:
            conflict.append({"uuid": k, "rows": [v[0][0]] + [j for j, _ in v[1:]],
                             "conflict_fields": diffs,
                             "values": {f: [r.get(f) for _, r in v] for f in diffs}})
        else:
            exact.append({"uuid": k, "rows": [v[0][0]] + [j for j, _ in v[1:]]})
    # Scene-valid universe: scene_id nonmissing and not -1.
    valid = []
    for i, r in enumerate(rows):
        s = (r.get("scene_id") or "").strip()
        if s and s != "-1":
            valid.append((i, r))
    seen = set(); removed = []
    for i, r in valid:
        if r["uuid"] in seen:
            removed.append((i, r))
        else:
            seen.add(r["uuid"])
    removed_groups = defaultdict(list)
    for i, r in removed: removed_groups[r["uuid"]].append((i, r))
    removed_exact, removed_conflict = [], []
    for k, v in removed_groups.items():
        allv = by[k]
        base = allv[0][1]
        diffs = [f for f in fields if any(r.get(f) != base.get(f) for _, r in allv[1:])]
        rec = {"uuid": k, "removed_row": v[0][0], "kept_row": allv[0][0],
               "conflict_fields": diffs}
        (removed_conflict if diffs else removed_exact).append(rec)
    out = {
        "generated": "2026-11-27",
        "raw_meta": str(args.raw_meta),
        "raw_rows": len(rows),
        "raw_unique_uuid": len(by),
        "raw_duplicate_groups": len(dup_groups),
        "raw_extra_duplicate_rows": sum(len(v) - 1 for v in dup_groups.values()),
        "raw_exact_duplicate_groups": len(exact),
        "raw_conflict_duplicate_groups": len(conflict),
        "scene_valid_before_dedup": len(valid),
        "scene_valid_after_dedup": len(seen),
        "scene_duplicate_rows_removed": len(removed),
        "scene_removed_exact_groups": len(removed_exact),
        "scene_removed_conflict_groups": len(removed_conflict),
        "real_positive_candidate_pairs": len(exact),
        "data_quality_conflict_pairs": len(conflict),
        "exact_duplicates": exact,
        "conflicts": conflict,
        "scene_removed_exact": removed_exact,
        "scene_removed_conflict": removed_conflict,
        "note": "Counts are row-universe specific: raw 74,896; scene-valid before dedup 73,511; after dedup 73,413. A same-UUID pair is a duplicate record candidate, not an independently re-encoded trajectory."
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    if args.csv_out:
        with open(args.csv_out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["uuid", "row", "kept_row", "class", "conflict_fields"])
            for x in exact: w.writerow([x["uuid"], ",".join(map(str, x["rows"])), x["rows"][0], "exact", ""])
            for x in conflict: w.writerow([x["uuid"], ",".join(map(str, x["rows"])), x["rows"][0], "conflict", ";".join(x["conflict_fields"])])
    print(json.dumps({k: out[k] for k in ("raw_rows", "raw_unique_uuid", "raw_extra_duplicate_rows",
        "raw_exact_duplicate_groups", "raw_conflict_duplicate_groups", "scene_valid_before_dedup",
        "scene_valid_after_dedup", "scene_duplicate_rows_removed", "scene_removed_exact_groups",
        "scene_removed_conflict_groups")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
