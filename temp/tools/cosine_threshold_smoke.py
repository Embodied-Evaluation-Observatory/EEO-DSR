#!/usr/bin/env python3
"""Smoke test for the cosine threshold helper, not a detector calibration.

The dedup detector does not exist yet. This script only exercises cosine arithmetic on synthetic
vectors: a "duplicate" is a random unit vector with small jitter, a "distinct" pair is two
independent random vectors. That construction cannot fail at W=0.95 in 32 dimensions, and it says
nothing about the method's episode-embedding-cosine-v1 distribution. It therefore carries no
false-merge or false-split gate and must not be cited as calibration evidence.

A real gate waits for the detector: hard negatives (same task/different episode, same scene/
different task, time-shifted and re-encoded copies), W passed on the command line, at least 59
pairs per class, and both exact one-sided bounds printed.

Output is a JSON object. Exit code is 0 when the helper runs; it is not a pass/fail gate.
"""
import argparse
import hashlib
import json
import math
import random
import sys


DIM = 32


def unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v]


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def upper_bound(k, n, alpha=0.05):
    """Clopper-Pearson one-sided upper bound, printed for scale only."""
    if k >= n:
        return 1.0

    def cdf(p):
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))

    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if cdf(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=float, default=0.95,
                    help="threshold passed through to the helper; not a declared calibration W")
    ap.add_argument("--pairs", type=int, default=59)
    ap.add_argument("--seed", type=int, default=20261125)
    args = ap.parse_args()
    if args.pairs < 1:
        print("--pairs must be at least 1", file=sys.stderr)
        return 2

    rnd = random.Random(args.seed)
    pos, neg = [], []
    for _ in range(args.pairs):
        v = unit([rnd.gauss(0, 1) for _ in range(DIM)])
        j = unit([x + rnd.gauss(0, 0.005) for x in v])
        pos.append((v, j))
    for _ in range(args.pairs):
        neg.append((unit([rnd.gauss(0, 1) for _ in range(DIM)]),
                    unit([rnd.gauss(0, 1) for _ in range(DIM)])))

    n_false_split = sum(1 for a, b in pos if cosine(a, b) < args.w)
    n_false_merge = sum(1 for a, b in neg if cosine(a, b) >= args.w)
    out = {
        "kind": "cosine_threshold_smoke_test",
        "detector_implemented": False,
        "gate": False,
        "may_be_cited_as_calibration": False,
        "w": args.w,
        "seed": args.seed,
        "dim": DIM,
        "n_positive_pairs": args.pairs,
        "n_negative_pairs": args.pairs,
        "n_false_merge": n_false_merge,
        "n_false_split": n_false_split,
        "false_merge_rate": round(n_false_merge / args.pairs, 6),
        "false_split_rate": round(n_false_split / args.pairs, 6),
        "illustrative_upper95_false_merge_rate": round(upper_bound(n_false_merge, args.pairs), 6),
        "illustrative_upper95_false_split_rate": round(upper_bound(n_false_split, args.pairs), 6),
        "note_zh": "这是余弦阈值 helper 的冒烟测试，不是去重检测器标定，不能作为误判率证据。",
    }
    spec = {k: out[k] for k in ("w", "seed", "dim", "n_positive_pairs", "n_negative_pairs")}
    out["fixture_hash"] = hashlib.sha256(
        json.dumps(spec, sort_keys=True).encode()).hexdigest()
    out["result_hash"] = hashlib.sha256(
        json.dumps(out, sort_keys=True).encode()).hexdigest()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
