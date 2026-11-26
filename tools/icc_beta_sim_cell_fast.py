"""Cell-axis beta-binomial coverage simulator with nested B sweep.

Same estimand and ICC(1) estimator as icc_beta_sim_fast.py, but avoids
allocating 53k singleton clusters on every bootstrap replicate. Singleton
clusters never enter ICC(1); they only affect how often a multi-episode
cluster is selected.  For a corpus with K total clusters, each multi cluster
is selected Binomial(K, 1/K) times in a cluster bootstrap, so the ICC path can
be run on those multi-cluster occurrences alone.

This is a calibration tool, not a corpus reading.  It is cell-specific only
because the singleton share makes the full-table path expensive.  It
bootstraps the multi-cluster subpopulation with a fixed number of draws, not
the full K-cluster population: point samples draw Multinomial(M, 1/M) over
the M multi clusters; bootstrap replicates draw Multinomial(M_occ, 1/M_occ)
over observed occurrences. Singletons never enter ICC(1), but their omission
means the number of selected multi clusters is fixed rather than random.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import dataset_driver as dd


def icc_vec(n: np.ndarray, s: np.ndarray):
    """ICC(1) over the last axis; returns nan if not estimable."""
    n = np.asarray(n, dtype=float); s = np.asarray(s, dtype=float)
    k = n.shape[-1]
    N = n.sum(axis=-1)
    if k < 2:
        return np.full(n.shape[:-1], np.nan)
    pbar = s.sum(axis=-1) / N
    msb = (n * (s / n - pbar[..., None]) ** 2).sum(axis=-1) / (k - 1)
    msw = (s - s * s / n).sum(axis=-1) / (N - k)
    m0 = (N - (n * n).sum(axis=-1) / N) / (k - 1)
    den = msb + (m0 - 1.0) * msw
    with np.errstate(divide="ignore", invalid="ignore"):
        rho = np.asarray((msb - msw) / den)
    return np.where(np.isfinite(rho) & (N > k) & (den != 0), rho, np.nan)


def icc_from_boot_counts(counts: np.ndarray, n: np.ndarray, s: np.ndarray):
    """ICC(1) from bootstrap selection counts, without materialising B×K arrays.

    counts: (B, K) number of times each observed cluster occurrence is selected.
    n, s:   (K,) episodes and successes of each occurrence.
    Index 0 is a prefix; returns (B,) rho with nan when not estimable.
    This is algebraically the same as icc_vec on the expanded bootstrap sample.
    """
    counts = np.asarray(counts, dtype=np.float64)
    n = np.asarray(n, dtype=np.float64); s = np.asarray(s, dtype=np.float64)
    k = counts.sum(axis=1)
    N = counts @ n
    S = counts @ s
    A = counts @ (s * s / n)
    W = counts @ (s - s * s / n)
    U = counts @ (n * n)
    with np.errstate(divide="ignore", invalid="ignore"):
        msb = (A - S * S / N) / (k - 1.0)
        msw = W / (N - k)
        m0 = (N - U / N) / (k - 1.0)
        den = msb + (m0 - 1.0) * msw
        rho = (msb - msw) / den
    good = np.isfinite(rho) & (N > k) & (den != 0) & (k >= 2)
    return np.where(good, rho, np.nan)


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
    ap.add_argument("--bootstrap-reps", default="25,100,500,2000")
    ap.add_argument("--rhos", default="0,0.05,0.1,0.2,0.3,0.5,0.7,0.9")
    ap.add_argument("--seed", type=int, default=20261128)
    args = ap.parse_args()
    Bs = sorted({int(x) for x in args.bootstrap_reps.split(",") if x.strip()})
    if min(Bs) < 20:
        raise SystemExit("B must be >= 20 for a 2.5/97.5 percentile with >=20 valid reps")
    rhos = [float(x) for x in args.rhos.split(",") if x.strip()]

    rows, _ = dd.read_corpus(args.input)
    clusters = dd.aggregate(rows, ("scene_id",))
    sizes_all = np.array([int(c["n"]) for c in clusters], dtype=np.int64)
    successes_all = np.array([int(c["successes"]) for c in clusters], dtype=np.int64)
    K_total = int(sizes_all.size)
    multi = sizes_all >= 2
    n_multi = sizes_all[multi].astype(float)
    s_multi = successes_all[multi].astype(float)
    if n_multi.size < 2:
        raise SystemExit("fewer than two multi-episode clusters")
    p_mean = float(successes_all.sum()) / float(sizes_all.sum())
    rng = np.random.default_rng(args.seed)
    Bmax = max(Bs)
    out = []
    for rho in rhos:
        est, neg, failed = [], 0, 0
        covers = {b: 0 for b in Bs}
        valid_for = {b: 0 for b in Bs}
        widths = {b: [] for b in Bs}
        for _ in range(args.simulations):
            # Each original multi cluster is selected Binomial(K, 1/K) times;
            # equivalently Multinomial over the multi clusters, then expand
            # each selected occurrence with its own beta probability.
            counts = rng.multinomial(n_multi.size, np.full(n_multi.size, 1.0 / n_multi.size))
            sim_n = np.repeat(n_multi, counts)
            if sim_n.size < 2:
                failed += 1
                continue
            if rho <= 0:
                probs = np.full(sim_n.size, p_mean)
            else:
                a = p_mean * (1.0 / rho - 1.0)
                bb = (1.0 - p_mean) * (1.0 / rho - 1.0)
                probs = rng.beta(a, bb, size=sim_n.size)
            sim_s = rng.binomial(sim_n.astype(np.int64), probs).astype(float)
            point = float(icc_vec(sim_n, sim_s))
            if not math.isfinite(point):
                failed += 1
                continue
            est.append(point); neg += int(point < 0)
            # Nested prefix bootstrap: each row is one with-replacement draw.
            M = sim_n.size
            boot_counts = rng.multinomial(M, np.full(M, 1.0 / M), size=Bmax)
            rb = icc_from_boot_counts(boot_counts, sim_n, sim_s)
            for b in Bs:
                vals = rb[:b]
                vals = vals[np.isfinite(vals)]
                if len(vals) < max(20, b // 4):
                    continue
                lo, hi = np.percentile(vals, [2.5, 97.5])
                covers[b] += int(lo <= rho <= hi)
                valid_for[b] += 1
                widths[b].append(float(hi - lo))
        valid = len(est)
        if not valid:
            out.append({"rho_true": rho, "simulations_valid": 0, "coverage_by_B": {}})
            continue
        by_b = {}
        for b in Bs:
            v = valid_for[b]
            by_b[str(b)] = {
                "coverage_95": covers[b] / v if v else None,
                "coverage_successes": covers[b],
                "coverage_wilson_95": wilson(covers[b], v),
                "mean_interval_width": float(np.mean(widths[b])) if widths[b] else None,
            }
        out.append({
            "rho_true": rho,
            "simulations_requested": args.simulations,
            "simulations_valid": valid,
            "simulations_failed": failed,
            "bias_mean": float(np.mean(est)) - rho,
            "sd": float(np.std(est)),
            "negative_share": neg / valid,
            "coverage_by_B": by_b,
            "bootstrap_replicates_valid_max_B": int(np.sum(np.isfinite(rb))) if 'rb' in locals() else None,
        })
    obj = {
        "input": args.input,
        "clusters_total": K_total,
        "episodes": int(sizes_all.sum()),
        "multi_clusters": int(n_multi.size),
        "p_mean": p_mean,
        "method": "fixed-size cluster bootstrap on the multi-cluster subpopulation; point sample Multinomial(M,1/M) over multi clusters; bootstrap Multinomial(M_occ,1/M_occ) over occurrences; nested B prefixes; ICC(1) from bootstrap counts via sufficient statistics; percentile interval; Wilson interval on coverage",
        "simulations_per_rho": args.simulations,
        "bootstrap_reps": Bs,
        "grid": out,
        "note": "Coverage is conditional on an estimable point and estimated from a finite simulation count. Nested prefixes mean B=25/100/500 use the first B of the same B=2000 stream. This is a fixed-size bootstrap of the multi-cluster subpopulation, not a full K-cluster bootstrap; singletons are excluded from ICC(1), so their omission changes the selection-count law but not the estimator.",
    }
    Path(args.out).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"clusters": K_total, "multi": int(n_multi.size), "episodes": int(sizes_all.sum()), "B": Bs}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
