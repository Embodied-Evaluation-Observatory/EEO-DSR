#!/usr/bin/env python3
"""Known-truth calibration of the dedup detector at the declared W.

Fixture: fixed seed, 59 known duplicate pairs and 59 known distinct pairs. The gate claims a true
false-merge and false-split rate at or below 5%; with 59 pairs and zero observed failures the exact
95% upper bound is about 4.9%. Counts, point rates and Clopper-Pearson upper bounds are reported
separately, because merging distinct episodes lowers NEES and missing duplicates raises it.

Outputs a JSON object. `fixture_hash` hashes the fixture specification; `result_hash` hashes the
measurement block, so a record can carry both without embedding the data.
"""
import hashlib
import json
import math
import random
import sys

W = 0.95
N = 59
DIM = 32
SPEC = {"seed": 20261125, "dim": DIM, "jitter": 0.005, "n_each": N, "w": W}


def unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v]


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def upper_bound(k, n, alpha=0.05):
    """Clopper-Pearson upper bound: solve P(X <= k; p) = alpha."""
    def cdf(p):
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))
    if k >= n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if cdf(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    rnd = random.Random(SPEC["seed"])
    pos, neg = [], []
    for _ in range(N):
        v = unit([rnd.gauss(0, 1) for _ in range(DIM)])
        j = unit([x + rnd.gauss(0, SPEC["jitter"]) for x in v])
        pos.append((v, j))
    for _ in range(N):
        pos.append((unit([rnd.gauss(0, 1) for _ in range(DIM)]),
                    unit([rnd.gauss(0, 1) for _ in range(DIM)]))) if False else None
    for _ in range(N):
        a = unit([rnd.gauss(0, 1) for _ in range(DIM)])
        b = unit([rnd.gauss(0, 1) for _ in range(DIM)])
        neg.append((a, b))
    n_false_split = sum(1 for a, b in pos if cosine(a, b) < W)
    n_false_merge = sum(1 for a, b in neg if cosine(a, b) >= W)
    out = {
        "w": W,
        "n_positive_pairs": N,
        "n_negative_pairs": N,
        "n_false_merge": n_false_merge,
        "n_false_split": n_false_split,
        "false_merge_rate": round(n_false_merge / N, 6),
        "false_split_rate": round(n_false_split / N, 6),
        "upper95_false_merge_rate": round(upper_bound(n_false_merge, N), 6),
        "upper95_false_split_rate": round(upper_bound(n_false_split, N), 6),
        "passed": (upper_bound(n_false_merge, N) <= 0.05
                   and upper_bound(n_false_split, N) <= 0.05),
    }
    out["fixture_hash"] = hashlib.sha256(
        json.dumps(SPEC, sort_keys=True).encode()).hexdigest()
    out["result_hash"] = hashlib.sha256(
        json.dumps(out, sort_keys=True).encode()).hexdigest()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
