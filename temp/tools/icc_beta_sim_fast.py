"""Vectorized beta-binomial coverage simulation for large cluster tables.

Same estimand and estimator as icc_beta_sim.py, but works on numpy arrays so
the cell axis (K ~ 5e4, many singletons) can be recalibrated at >=1,000
simulations. This is a calibration tool, not a corpus reading.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import dataset_driver as dd


def icc_vec(n: np.ndarray, s: np.ndarray):
    # ICC(1) in dataset_driver excludes singletons; they contribute to the
    # corpus size table but not to the variance components.
    mask = n >= 2
    n = n[mask]
    s = s[mask]
    k = n.size
    N = float(n.sum())
    if k < 2 or N <= k:
        return None
    pbar = float(s.sum()) / N
    msb = float((n * (s / n - pbar) ** 2).sum() / (k - 1))
    msw = float((s - s * s / n).sum() / (N - k))
    m0 = (N - float((n * n).sum()) / N) / (k - 1)
    den = msb + (m0 - 1.0) * msw
    if den == 0:
        return None
    return (msb - msw) / den


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, centre - half), min(1.0, centre + half)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--simulations", type=int, default=1000)
    ap.add_argument("--bootstrap-reps", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20261127)
    args = ap.parse_args()
    rows, _ = dd.read_corpus(args.input)
    clusters = dd.aggregate(rows, ("scene_id",))
    sizes = np.array([int(c["n"]) for c in clusters], dtype=np.int64)
    p_mean = sum(int(c["successes"]) for c in clusters) / sum(int(c["n"]) for c in clusters)
    rng = np.random.default_rng(args.seed)
    grid = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9]
    out = []
    for rho in grid:
        est, covers, neg, failed = [], 0, 0, 0
        for _ in range(args.simulations):
            sim_n = rng.choice(sizes, size=sizes.size, replace=True)
            if rho <= 0:
                probs = np.full(sizes.size, p_mean)
            else:
                a = p_mean * (1.0 / rho - 1.0)
                b = (1.0 - p_mean) * (1.0 / rho - 1.0)
                probs = rng.beta(a, b, size=sizes.size)
            sim_s = rng.binomial(sim_n, probs)
            point = icc_vec(sim_n, sim_s)
            if point is None or not math.isfinite(point):
                failed += 1
                continue
            est.append(point); neg += int(point < 0)
            vals = []
            for _ in range(args.bootstrap_reps):
                idx = rng.integers(0, sizes.size, sizes.size)
                r = icc_vec(sim_n[idx], sim_s[idx])
                if r is not None and math.isfinite(r):
                    vals.append(r)
            if len(vals) >= max(20, args.bootstrap_reps // 4):
                lo, hi = np.percentile(vals, [2.5, 97.5])
                covers += int(lo <= rho <= hi)
        valid = len(est)
        cov = covers / valid if valid else None
        out.append({
            "rho_true": rho,
            "simulations_requested": args.simulations,
            "simulations_valid": valid,
            "simulations_failed": failed,
            "bias_mean": (sum(est) / valid - rho) if valid else None,
            "sd": float(np.std(est)) if valid else None,
            "coverage_95": cov,
            "coverage_successes": covers,
            "coverage_wilson_95": wilson(covers, valid),
            "bootstrap_replicates_valid": valid,
            "negative_share": (neg / valid) if valid else None,
        })
    obj = {
        "input": args.input,
        "clusters": int(sizes.size),
        "episodes": int(sizes.sum()),
        "p_mean": p_mean,
        "method": "vectorized beta-binomial at known rho; cluster sizes resampled from this corpus; ICC(1); cluster bootstrap percentile; Wilson interval on coverage",
        "simulations_per_rho": args.simulations,
        "bootstrap_reps": args.bootstrap_reps,
        "grid": out,
        "note": "Coverage is conditional on an estimable point and is itself estimated from a finite simulation count; report coverage_wilson_95, not only the point.",
    }
    Path(args.out).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
