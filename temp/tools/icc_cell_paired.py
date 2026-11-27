#!/usr/bin/env python3
"""Paired fixed-vs-full cell bootstrap coverage comparison.

The previous fixed/full runs used the same seed but separate RNG paths: they
were not paired on one simulated corpus.  This rerun draws one full-K sample
per simulation, then applies both bootstrap designs to that same multi-cluster
sample.  The point ICC is identical by construction; the comparison isolates
the bootstrap design (fixed multi-only resampling vs full-K resampling with
singletons discarded), not the point estimator.

Coverage indicators are paired by simulation index.  The tool prints the
discordant counts, an exact McNemar p-value, and a paired bootstrap interval
for the coverage difference.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from statistics import NormalDist
import numpy as np
from scipy.stats import binomtest
import dataset_driver as dd
from icc_beta_sim_cell_fast import icc_vec, icc_from_boot_counts, bca_acceleration, interval_from_boot, wilson

D = NormalDist()


def neff(n, rho):
    n = np.asarray(n, dtype=float); rho = max(0.0, float(rho))
    return float((n / (1.0 + (n - 1.0) * rho)).sum())


def n_eff_boot(counts, n_occ, singletons, rho):
    contrib = n_occ[None, :] / (1.0 + (n_occ[None, :] - 1.0) * np.maximum(rho, 0.0)[:, None])
    return singletons + (counts * contrib).sum(axis=1)


def paired_ci(diff, rng, reps=2000):
    n = len(diff); vals = []
    for _ in range(reps):
        idx = rng.integers(0, n, n)
        vals.append(float(np.mean(diff[idx])))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def run(sizes_all, successes_all, p_mean, rho, sims, B, seed, max_jack):
    K = int(sizes_all.size); multi = sizes_all >= 2
    n_multi = sizes_all[multi].astype(float); s_multi = successes_all[multi].astype(float)
    M = int(n_multi.size)
    rng = np.random.default_rng(seed); rng_jack = np.random.default_rng(seed + 104729)
    rows = []
    for _ in range(sims):
        all_counts = rng.multinomial(K, np.full(K, 1.0 / K))
        c_multi = all_counts[multi]; m_occ = int(c_multi.sum())
        if m_occ < 2: continue
        sim_n = np.repeat(n_multi, c_multi)
        if rho <= 0:
            probs = np.full(sim_n.size, p_mean)
        else:
            a = p_mean * (1.0 / rho - 1.0); b = (1.0 - p_mean) * (1.0 / rho - 1.0)
            probs = rng.beta(a, b, size=sim_n.size)
        sim_s = rng.binomial(sim_n.astype(np.int64), probs).astype(float)
        point = float(icc_vec(sim_n, sim_s))
        if not math.isfinite(point): continue
        accel = bca_acceleration(sim_n, sim_s, point, rng_jack, max_jack)
        # Same point corpus: fixed bootstrap only resamples the observed multi
        # occurrences; full bootstrap draws K clusters then discards singletons.
        boot_fixed = rng.multinomial(m_occ, np.full(m_occ, 1.0 / m_occ), size=B)
        rb_fixed = icc_from_boot_counts(boot_fixed, sim_n, sim_s)
        kb = rng.binomial(K, m_occ / K, size=B)
        boot_full = rng.multinomial(kb, np.full(m_occ, 1.0 / m_occ), size=B)
        rb_full = icc_from_boot_counts(boot_full, sim_n, sim_s)
        singleton_draws = (K - kb).astype(float)
        vf = rb_fixed[np.isfinite(rb_fixed)]
        vg = rb_full[np.isfinite(rb_full)]
        if len(vf) < max(20, B // 4) or len(vg) < max(20, B // 4): continue
        zf = D.inv_cdf(float(np.clip(np.mean(vf < point), 1e-6, 1 - 1e-6)))
        zg = D.inv_cdf(float(np.clip(np.mean(vg < point), 1e-6, 1 - 1e-6)))
        ivf_p = interval_from_boot(vf, point, accel, "percentile")
        ivg_p = interval_from_boot(vg, point, accel, "percentile")
        ivf_b = interval_from_boot(vf, point, accel, "bca")
        ivg_b = interval_from_boot(vg, point, accel, "bca")
        fin = np.isfinite(rb_full)
        neff_vals = n_eff_boot(boot_full[:B][fin], sim_n, singleton_draws[:B][fin], rb_full[:B][fin])
        iv_neff = [float(np.percentile(neff_vals, 2.5)), float(np.percentile(neff_vals, 97.5))]
        rows.append({"point_rho": point, "accel": accel,
                     "fixed_p": ivf_p, "full_p": ivg_p, "fixed_bca": ivf_b, "full_bca": ivg_b,
                     "n_eff": iv_neff, "m_occ": m_occ, "z0_fixed": zf, "z0_full": zg})
    return rows, neff(sizes_all.astype(float), rho)


def cover(iv, rho): return bool(iv[0] <= rho <= iv[1])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rho", type=float, default=0.9)
    ap.add_argument("--simulations", type=int, default=300)
    ap.add_argument("--bootstrap-reps", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261130)
    ap.add_argument("--bca-jackknife", type=int, default=400)
    args = ap.parse_args()
    rows, _ = dd.read_corpus(args.input)
    clusters = dd.aggregate(rows, ("scene_id",))
    sizes = np.array([int(c["n"]) for c in clusters], dtype=np.int64)
    succ = np.array([int(c["successes"]) for c in clusters], dtype=np.int64)
    p_mean = float(succ.sum()) / int(sizes.sum())
    sim_rows, true_neff = run(sizes, succ, p_mean, args.rho, args.simulations, args.bootstrap_reps, args.seed, args.bca_jackknife)
    n = len(sim_rows)
    cov = {k: np.array([cover(r[k], args.rho) for r in sim_rows]) for k in ("fixed_p", "full_p", "fixed_bca", "full_bca")}
    neff_cov = np.array([r["n_eff"][0] <= true_neff <= r["n_eff"][1] for r in sim_rows])
    both = int(np.sum(cov["fixed_p"] & cov["full_p"]))
    only_fixed = int(np.sum(cov["fixed_p"] & ~cov["full_p"]))
    only_full = int(np.sum(~cov["fixed_p"] & cov["full_p"]))
    neither = int(np.sum(~cov["fixed_p"] & ~cov["full_p"]))
    b = only_fixed; c = only_full
    p_mcnemar = float(binomtest(min(b, c), b + c, 0.5).pvalue) if b + c > 0 else 1.0
    diff = cov["full_p"].astype(float) - cov["fixed_p"].astype(float)
    ci = paired_ci(diff, np.random.default_rng(args.seed + 991))
    acc = np.array([r["accel"] for r in sim_rows]); z0f = np.array([r["z0_fixed"] for r in sim_rows]); z0g = np.array([r["z0_full"] for r in sim_rows])
    out = {
        "input": args.input, "rho_true": args.rho, "n_eff_true": true_neff,
        "clusters_total": int(sizes.size), "episodes": int(sizes.sum()),
        "multi_clusters": int((sizes >= 2).sum()), "p_mean": p_mean,
        "simulations_requested": args.simulations, "simulations_valid": n,
        "bootstrap_reps": args.bootstrap_reps, "seed": args.seed,
        "design": "paired on one full-K simulated multi corpus per simulation; fixed and full bootstrap applied to that same point corpus",
        "coverage": {
            "fixed_percentile": float(np.mean(cov["fixed_p"])),
            "full_percentile": float(np.mean(cov["full_p"])),
            "fixed_bca": float(np.mean(cov["fixed_bca"])),
            "full_bca": float(np.mean(cov["full_bca"])),
            "n_eff_percentile": float(np.mean(neff_cov)),
            "fixed_percentile_wilson": wilson(int(cov["fixed_p"].sum()), n),
            "full_percentile_wilson": wilson(int(cov["full_p"].sum()), n),
            "n_eff_percentile_wilson": wilson(int(neff_cov.sum()), n),
        },
        "paired_2x2": {"both": both, "only_fixed": only_fixed, "only_full": only_full, "neither": neither},
        "mcnemar_exact_p": p_mcnemar,
        "coverage_difference_full_minus_fixed": float(np.mean(diff)),
        "coverage_difference_paired_bootstrap_95": ci,
        "m_occ_mean": float(np.mean([r["m_occ"] for r in sim_rows])),
        "m_occ_sd": float(np.std([r["m_occ"] for r in sim_rows])),
        "acceleration": {"mean": float(acc.mean()), "sd": float(acc.std()),
                         "p025": float(np.percentile(acc, 2.5)), "p50": float(np.percentile(acc, 50)),
                         "p975": float(np.percentile(acc, 97.5)), "min": float(acc.min()), "max": float(acc.max()),
                         "share_abs_gt_0_1": float(np.mean(np.abs(acc) > 0.1)),
                         "share_abs_gt_0_3": float(np.mean(np.abs(acc) > 0.3))},
        "z0_fixed_sd": float(z0f.std()), "z0_full_sd": float(z0g.std()),
        "note": "paired coverage comparison, not a corpus record; n_eff coverage is a separate percentile interval",
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("simulations_valid", "coverage", "paired_2x2", "mcnemar_exact_p", "coverage_difference_full_minus_fixed", "coverage_difference_paired_bootstrap_95", "m_occ_mean", "m_occ_sd")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
