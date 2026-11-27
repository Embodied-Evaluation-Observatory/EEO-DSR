#!/usr/bin/env python3
"""Paired continuous comparison for fixed vs full bootstrap on the cell axis.

Same paired design as icc_cell_paired.py: one full-K simulated corpus per
simulation; fixed and full percentile intervals are computed on that same point
corpus. The continuous quantities are interval width, lower endpoint and upper
endpoint. Point estimate is identical by construction.

For each difference we report:
  - mean/median paired difference and its paired bootstrap CI (median)
  - Hodges-Lehmann location estimate (median of pairwise averages)
  - Wilcoxon signed-rank p-value
This is a design comparison, not a corpus record.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
from scipy.stats import wilcoxon
import dataset_driver as dd
from icc_beta_sim_cell_fast import icc_vec, icc_from_boot_counts, interval_from_boot


def paired_ci(vals, rng, reps=2000):
    vals = np.asarray(vals)
    n = len(vals)
    out = []
    for _ in range(reps):
        out.append(float(np.median(vals[rng.integers(0, n, n)])))
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


def hodges_lehmann(vals):
    vals = np.asarray(vals)
    # median of (d_i + d_j)/2 over all ordered pairs, including i=j
    sums = vals[:, None] + vals[None, :]
    return float(np.median(sums) / 2.0)


def describe(name, fixed, full, rng):
    fixed = np.asarray(fixed); full = np.asarray(full); diff = full - fixed
    try:
        p = float(wilcoxon(full, fixed, zero_method="wilcox", alternative="two-sided").pvalue)
    except Exception:
        p = None
    return {
        "metric": name,
        "fixed_mean": float(fixed.mean()), "fixed_sd": float(fixed.std(ddof=1)),
        "full_mean": float(full.mean()), "full_sd": float(full.std(ddof=1)),
        "difference_mean": float(diff.mean()),
        "difference_median": float(np.median(diff)),
        "difference_hodges_lehmann": hodges_lehmann(diff),
        "difference_median_paired_bootstrap_95": paired_ci(diff, rng),
        "wilcoxon_signed_rank_p": p,
        "variation_ok": bool(fixed.std(ddof=1) > 0 and full.std(ddof=1) > 0),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rho", type=float, default=0.9)
    ap.add_argument("--simulations", type=int, default=300)
    ap.add_argument("--bootstrap-reps", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261130)
    args = ap.parse_args()
    rows, _ = dd.read_corpus(args.input)
    clusters = dd.aggregate(rows, ("scene_id",))
    sizes = np.array([int(c["n"]) for c in clusters], dtype=np.int64)
    succ = np.array([int(c["successes"]) for c in clusters], dtype=np.int64)
    p_mean = float(succ.sum()) / int(sizes.sum())
    K = int(sizes.size); multi = sizes >= 2
    n_multi = sizes[multi].astype(float); s_multi = succ[multi].astype(float)
    rng = np.random.default_rng(args.seed)
    wf=[]; wg=[]; lf=[]; lg=[]; uf=[]; ug=[]; point_bias=[]
    for _ in range(args.simulations):
        counts = rng.multinomial(K, np.full(K, 1.0/K))
        c_multi = counts[multi]; m_occ = int(c_multi.sum())
        if m_occ < 2: continue
        sim_n = np.repeat(n_multi, c_multi)
        probs = (rng.beta(p_mean*(1/args.rho-1), (1-p_mean)*(1/args.rho-1), size=sim_n.size)
                 if args.rho > 0 else np.full(sim_n.size, p_mean))
        sim_s = rng.binomial(sim_n.astype(np.int64), probs).astype(float)
        point = float(icc_vec(sim_n, sim_s))
        if not math.isfinite(point): continue
        boot_f = rng.multinomial(m_occ, np.full(m_occ, 1.0/m_occ), size=args.bootstrap_reps)
        rb_f = icc_from_boot_counts(boot_f, sim_n, sim_s)
        kb = rng.binomial(K, m_occ/K, size=args.bootstrap_reps)
        boot_g = rng.multinomial(kb, np.full(m_occ, 1.0/m_occ), size=args.bootstrap_reps)
        rb_g = icc_from_boot_counts(boot_g, sim_n, sim_s)
        vf = rb_f[np.isfinite(rb_f)]; vg = rb_g[np.isfinite(rb_g)]
        if len(vf) < max(20, args.bootstrap_reps//4) or len(vg) < max(20, args.bootstrap_reps//4): continue
        ivf = interval_from_boot(vf, point, None, "percentile")
        ivg = interval_from_boot(vg, point, None, "percentile")
        lf.append(ivf[0]); uf.append(ivf[1]); wf.append(ivf[1]-ivf[0])
        lg.append(ivg[0]); ug.append(ivg[1]); wg.append(ivg[1]-ivg[0])
        point_bias.append(point - args.rho)
    n=len(wf); rng2=np.random.default_rng(args.seed+9949)
    out={
      "input": args.input, "rho_true": args.rho, "simulations_valid": n,
      "bootstrap_reps": args.bootstrap_reps, "seed": args.seed,
      "design":"paired on one full-K simulated corpus per simulation; percentile intervals only",
      "point_bias": {"mean": float(np.mean(point_bias)), "sd": float(np.std(point_bias, ddof=1)),
                     "note":"identical for both modes by construction; not a method difference"},
      "metrics": [describe("interval_width", wf, wg, rng2),
                  describe("lower_endpoint", lf, lg, rng2),
                  describe("upper_endpoint", uf, ug, rng2)],
      "note":"Continuous paired comparison; widths/endpoints are percentile intervals. If a metric has near-zero variation, the test has little power."
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(out, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    raise SystemExit(main())
