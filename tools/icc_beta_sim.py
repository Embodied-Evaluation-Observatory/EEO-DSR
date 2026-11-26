"""Beta-binomial bias and bootstrap-coverage simulation for ICC(1).

Cluster sizes are drawn from a real DROID native-scene size table, with
replacement. Outcomes are beta-binomial at a known rho. The script reports
bias, 95% percentile coverage, and negative-ICC share. It does not turn a
simulation into a corpus reading.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import dataset_driver as dd
from icc_bootstrap import percentile


def clusters_from_sizes(sizes: list[int], rho: float, p: float, rng: random.Random) -> list[dict]:
    if rho <= 0:
        probs = [p] * len(sizes)
    else:
        a = p * (1.0 / rho - 1.0)
        b = (1.0 - p) * (1.0 / rho - 1.0)
        probs = [rng.betavariate(a, b) for _ in sizes]
    out = []
    for i, (n, q) in enumerate(zip(sizes, probs)):
        succ = sum(1 for _ in range(n) if rng.random() < q)
        out.append({"id": f"s{i}", "n": n, "successes": succ,
                    "failures": n - succ, "rate": succ / n})
    return out


def bootstrap_interval(clusters: list[dict], rho: float, reps: int, rng: random.Random) -> tuple[float, float] | None:
    k = len(clusters)
    vals = []
    for _ in range(reps):
        sample = [clusters[rng.randrange(k)] for _ in range(k)]
        r = dd.icc1(sample)
        if r.get("status") == "computed" and math.isfinite(r["rho"]):
            vals.append(float(r["rho"]))
    if len(vals) < max(50, reps // 4):
        return None
    return percentile(vals, 0.025), percentile(vals, 0.975)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, help="native scene CSV with episode_id,scene_id,outcome")
    p.add_argument("--out", required=True)
    p.add_argument("--simulations", type=int, default=300)
    p.add_argument("--bootstrap-reps", type=int, default=200)
    p.add_argument("--seed", type=int, default=20261126)
    args = p.parse_args()

    rows, _ = dd.read_corpus(args.input)
    clusters = dd.aggregate(rows, ("scene_id",))
    sizes = [int(c["n"]) for c in clusters]
    rng = random.Random(args.seed)
    p_mean = sum(int(c["successes"]) for c in clusters) / sum(int(c["n"]) for c in clusters)
    grid = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9]
    results = []
    for rho_true in grid:
        est = []
        covers = []
        negative = 0
        for _ in range(args.simulations):
            sim_sizes = [sizes[rng.randrange(len(sizes))] for _ in range(len(sizes))]
            c = clusters_from_sizes(sim_sizes, rho_true, p_mean, rng)
            point = dd.icc1(c)
            if point.get("status") != "computed" or not math.isfinite(point["rho"]):
                continue
            rho_hat = float(point["rho"])
            est.append(rho_hat)
            negative += int(rho_hat < 0.0)
            ci = bootstrap_interval(c, rho_true, args.bootstrap_reps, rng)
            if ci is not None:
                covers.append(int(ci[0] <= rho_true <= ci[1]))
        results.append({
            "rho_true": rho_true,
            "simulations_valid": len(est),
            "bias_mean": (sum(est) / len(est) - rho_true) if est else None,
            "sd": (math.sqrt(sum((x - sum(est) / len(est)) ** 2 for x in est) / len(est))) if est else None,
            "coverage_95": (sum(covers) / len(covers)) if covers else None,
            "bootstrap_replicates_valid": len(covers),
            "negative_share": (negative / len(est)) if est else None,
        })

    obj = {
        "input": args.input,
        "clusters": len(clusters),
        "episodes": len(rows),
        "p_mean": p_mean,
        "size_table": {
            "min": min(sizes), "median": sorted(sizes)[len(sizes) // 2],
            "max": max(sizes), "mean": sum(sizes) / len(sizes),
        },
        "method": "beta-binomial at known rho; sizes resampled from DROID native scene sizes; ICC(1); cluster bootstrap percentile",
        "simulations_per_rho": args.simulations,
        "bootstrap_reps": args.bootstrap_reps,
        "grid": results,
        "note": "Coverage is conditional on an estimable point; this tests estimator behaviour, not a corpus claim.",
    }
    Path(args.out).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
