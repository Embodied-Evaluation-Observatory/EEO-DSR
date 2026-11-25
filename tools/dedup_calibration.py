#!/usr/bin/env python3
"""Deterministic calibration of the dedup detector on a synthetic known-truth set.

Positive pairs: the same episode embedding with small jitter. Negative pairs: different episodes.
The script reports the false-merge and false-split rates at the declared W. No third-party
dependency; the fixture is generated from a fixed seed, so the output is reproducible.
"""
import json
import math
import random
import sys

W = 0.95
POS = 40
NEG = 40
DIM = 32


def unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v]


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def main():
    rnd = random.Random(20261125)
    pos, neg = [], []
    for _ in range(POS):
        v = unit([rnd.gauss(0, 1) for _ in range(DIM)])
        j = unit([x + rnd.gauss(0, 0.005) for x in v])
        pos.append((v, j))
    for _ in range(NEG):
        a = unit([rnd.gauss(0, 1) for _ in range(DIM)])
        b = unit([rnd.gauss(0, 1) for _ in range(DIM)])
        neg.append((a, b))
    false_split = sum(1 for a, b in pos if cosine(a, b) < W) / POS
    false_merge = sum(1 for a, b in neg if cosine(a, b) >= W) / NEG
    out = {"W": W, "n_positive_pairs": POS, "n_negative_pairs": NEG,
           "false_merge_rate": round(false_merge, 4),
           "false_split_rate": round(false_split, 4),
           "passed": false_merge <= 0.05 and false_split <= 0.05}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
