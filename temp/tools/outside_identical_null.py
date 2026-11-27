#!/usr/bin/env python3
"""Identical-side outside-rate null: split one site's own fingerprints in half.

For each site and representation, repeatedly split its rows into two halves,
fit the 0.5-99.5% per-dimension range on one half, and measure the share of the
other half outside that range. This is the zero baseline for a same-site
comparison, not a site-to-site comparison.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np


def one(matrix, reps, rng):
    n = matrix.shape[0]
    vals = []
    for _ in range(reps):
        idx = rng.permutation(n)
        a = matrix[idx[: n // 2]]
        b = matrix[idx[n // 2:]]
        lo, hi = np.percentile(a, [0.5, 99.5], axis=0)
        vals.append(float(((b < lo) | (b > hi)).any(axis=1).mean()))
    return vals


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--buildings", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--seed", type=int, default=20261127)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    out = {"reps": args.reps, "seed": args.seed, "note": "same-site split-half null; not a site-to-site reading"}
    for rep in ("summary", "traj16"):
        out[rep] = {}
        for site in ("tri", "gates"):
            if site == "tri":
                p = Path(args.buildings) / f"tri-to-gates-{rep}-reference.npz"
            else:
                p = Path(args.buildings) / f"gates-to-tri-{rep}-reference.npz"
            arr = np.load(p)["fingerprints"]
            vals = np.array(one(arr, args.reps, rng))
            out[rep][site] = {"n": int(arr.shape[0]), "mean": float(vals.mean()),
                              "p025": float(np.percentile(vals, 2.5)),
                              "p975": float(np.percentile(vals, 97.5))}
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    raise SystemExit(main())
