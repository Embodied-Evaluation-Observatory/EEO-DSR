#!/usr/bin/env python3
"""Tie-break sensitivity for duplicate metadata records with conflicting labels.

Three rules over the same raw metadata rows:
  first  -- keep the first occurrence of each uuid (current audit behavior)
  last   -- keep the last occurrence
  drop   -- remove every row of a uuid whose occurrences conflict; exact
            duplicates still keep one row

The probe is computed on the raw-metadata universe, not the 93,994-episode
derived corpus. It is a sensitivity readout, not a replacement for the
published rho.
"""
from __future__ import annotations
import argparse, csv, json, random, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dataset_driver as dd


def q(vals, p):
    xs = sorted(vals)
    pos = (len(xs) - 1) * p
    lo = int(pos); hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def clusters_for(rows, rule):
    by = defaultdict(list)
    for i, r in enumerate(rows):
        by[r["uuid"]].append((i, r))
    chosen = []
    for uuid, items in by.items():
        first = items[0][1]
        conflict = any(any(r.get(k) != first.get(k) for k in r) for _, r in items[1:])
        if rule == "first" or (rule == "drop" and not conflict):
            chosen.append(items[0][1])
        elif rule == "last":
            chosen.append(items[-1][1])
        elif rule == "drop":
            continue
        else:
            raise ValueError(rule)
    # scene-valid, building/task-keyed cell rows
    out = []
    for i, r in enumerate(chosen):
        if not (r.get("scene_id") or "").strip() or (r.get("scene_id") or "").strip() == "-1":
            continue
        if not (r.get("building") or "").strip() or not (r.get("current_task") or "").strip():
            continue
        succ = (r.get("success") or "").strip().lower()
        if succ not in ("true", "false", "1", "0"):
            continue
        out.append({"episode_id": f"row{i}", "scene_id": f"{r['building']}||{r['current_task']}",
                    "outcome": 1 if succ in ("true", "1") else 0})
    return out, len(by), len(chosen)


def run_rule(rows, rule, reps, seed):
    usable, unique_uuid, chosen_n = clusters_for(rows, rule)
    clusters = dd.aggregate(usable, key_fields=("scene_id",))
    icc = dd.icc1(clusters)
    neff = dd.neff_at_rho(clusters, icc["rho"]) if icc.get("status") == "computed" else None
    rng = random.Random(seed)
    vals = []
    k = len(clusters)
    for _ in range(reps):
        sample = [clusters[rng.randrange(k)] for _ in range(k)]
        r = dd.icc1(sample)
        if r.get("status") == "computed":
            vals.append(float(r["rho"]))
    ci = [q(vals, 0.025), q(vals, 0.975)] if vals else None
    return {
        "rule": rule,
        "episodes": len(usable),
        "clusters": k,
        "unique_uuid": unique_uuid,
        "chosen_uuid": chosen_n,
        "rho": icc.get("rho"),
        "rho_status": icc.get("status"),
        "rho_bootstrap_95": ci,
        "bootstrap_reps": reps,
        "n_eff": neff["n_eff"] if neff else None,
        "zero_variance_share": sum(1 for c in clusters if c["zero_variance"]) / k,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-meta", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--seed", type=int, default=20261127)
    args = ap.parse_args()
    rows = list(csv.DictReader(open(args.raw_meta, newline="", encoding="utf-8")))
    fields = list(rows[0].keys())
    by = defaultdict(list)
    for i, r in enumerate(rows): by[r["uuid"]].append((i, r))
    conflict = []
    for uuid, items in by.items():
        first = items[0][1]
        diffs = [f for f in fields if any(r.get(f) != first.get(f) for _, r in items[1:])]
        if diffs:
            conflict.append({"uuid": uuid, "rows": [i for i, _ in items], "fields": diffs,
                             "success_values": [r.get("success") for _, r in items]})
    rules = {r: run_rule(rows, r, args.reps, args.seed + i) for i, r in enumerate(("first", "last", "drop"))}
    # paired difference: compare first vs each on bootstrap draws by reusing same seed
    result = {
        "date": "2026-11-27",
        "raw_meta": args.raw_meta,
        "raw_rows": len(rows),
        "raw_unique_uuid": len(by),
        "conflict_groups": len(conflict),
        "conflict_fields": sorted({f for c in conflict for f in c["fields"]}),
        "success_conflict_groups": sum(1 for c in conflict if "success" in c["fields"]),
        "success_value_patterns": sorted({tuple(c["success_values"]) for c in conflict if "success" in c["fields"]}),
        "universe": "raw metadata, scene-valid, building||current_task; not the 93,994-episode derived corpus",
        "rules": rules,
        "note": "Sensitivity only. first is the current audit tie-break; drop removes all rows of conflicting UUIDs. A same-UUID pair is not an independent re-observation.",
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({r: {k: rules[r][k] for k in ("episodes", "clusters", "rho", "rho_bootstrap_95", "n_eff")} for r in rules}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
