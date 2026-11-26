#!/usr/bin/env python3
"""Full-K cell bootstrap and n_eff coverage calibration.

The fixed-size shortcut in icc_beta_sim_cell_fast.py conditions on the
multi-cluster subpopulation: the number of selected multi clusters is fixed.
This tool draws K clusters from the full corpus, then discards singletons
before ICC(1).  It measures two coverage grids:

- rho interval coverage, so the shortcut can be compared on the same seed;
- n_eff interval coverage, where the truth is the exact per-cluster n_eff at
  the known rho and the known size table.

The n_eff bootstrap keeps singleton draws as singletons (each contributes 1)
and applies the exact per-cluster sum to multi-cluster draws.  It does not
issue a corpus record.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
from statistics import NormalDist
import numpy as np
import dataset_driver as dd
from icc_beta_sim_cell_fast import icc_vec, icc_from_boot_counts, bca_acceleration, interval_from_boot, wilson

D = NormalDist()


def neff(n: np.ndarray, rho: float) -> float:
    rho = max(0.0, float(rho))
    n = np.asarray(n, dtype=float)
    return float((n / (1.0 + (n - 1.0) * rho)).sum())


def n_eff_boot(counts: np.ndarray, n_occ: np.ndarray, singletons: np.ndarray, rho: np.ndarray) -> np.ndarray:
    # counts: (B, M_occ) selected multi occurrences; n_occ repeats each
    # original cluster size for each selected occurrence.
    contrib = n_occ[None, :] / (1.0 + (n_occ[None, :] - 1.0) * np.maximum(rho, 0.0)[:, None])
    return singletons + (counts * contrib).sum(axis=1)


def run_mode(mode: str, sizes_all, successes_all, p_mean, rho, sims, B, seed, max_jack):
    K = int(sizes_all.size)
    multi = sizes_all >= 2
    n_multi = sizes_all[multi].astype(float); s_multi = successes_all[multi].astype(float)
    M = int(n_multi.size)
    rng = np.random.default_rng(seed)
    rng_jack = np.random.default_rng(seed + 104729)
    n_eff_true = neff(sizes_all.astype(float), rho)
    rows = []
    for _ in range(sims):
        if mode == "fixed":
            c_multi = rng.multinomial(M, np.full(M, 1.0 / M))
            m_occ = int(c_multi.sum())
            if m_occ < 2:
                continue
            sim_n = np.repeat(n_multi, c_multi)
            if rho <= 0:
                probs = np.full(sim_n.size, p_mean)
            else:
                a = p_mean * (1.0 / rho - 1.0); b = (1.0 - p_mean) * (1.0 / rho - 1.0)
                probs = rng.beta(a, b, size=sim_n.size)
            sim_s = rng.binomial(sim_n.astype(np.int64), probs).astype(float)
            point = float(icc_vec(sim_n, sim_s))
            if not math.isfinite(point):
                continue
            boot = rng.multinomial(m_occ, np.full(m_occ, 1.0 / m_occ), size=B)
            rb = icc_from_boot_counts(boot, sim_n, sim_s)
            singleton_draws = np.zeros(B, dtype=float)
            point_neff = float("nan")
        else:
            all_counts = rng.multinomial(K, np.full(K, 1.0 / K))
            c_multi = all_counts[multi]
            m_occ = int(c_multi.sum())
            if m_occ < 2:
                continue
            sim_n = np.repeat(n_multi, c_multi)
            if rho <= 0:
                probs = np.full(sim_n.size, p_mean)
            else:
                a = p_mean * (1.0 / rho - 1.0); b = (1.0 - p_mean) * (1.0 / rho - 1.0)
                probs = rng.beta(a, b, size=sim_n.size)
            sim_s = rng.binomial(sim_n.astype(np.int64), probs).astype(float)
            point = float(icc_vec(sim_n, sim_s))
            if not math.isfinite(point):
                continue
            # Full K bootstrap: draw K clusters from the point sample, keep
            # multi occurrences, discard singleton occurrences before ICC.
            kb = rng.binomial(K, m_occ / K, size=B)
            # Conditional on kb, the multi occurrences are multinomial over
            # the observed multi occurrence list.
            boot = rng.multinomial(kb, np.full(m_occ, 1.0 / m_occ), size=B) if np.any(kb >= 2) else np.zeros((B, m_occ), dtype=np.int64)
            rb = icc_from_boot_counts(boot, sim_n, sim_s)
            singleton_draws = (K - kb).astype(float)
            # Point n_eff includes singleton draws and multi occurrences.
            point_neff = (K - m_occ) + float((c_multi * (n_multi / (1.0 + (n_multi - 1.0) * max(0.0, point)))).sum())
        accel = bca_acceleration(sim_n, sim_s, point, rng_jack, max_jack)
        vals = rb[:B]
        vals = vals[np.isfinite(vals)]
        if len(vals) < max(20, B // 4):
            continue
        z0 = D.inv_cdf(float(np.clip(np.mean(vals < point), 1e-6, 1 - 1e-6)))
        iv_p = interval_from_boot(vals, point, accel, "percentile")
        iv_b = interval_from_boot(vals, point, accel, "bca")
        if mode == "full":
            boot_valid = boot[:B][np.isfinite(rb[:B])]
            neff_vals = n_eff_boot(boot_valid, sim_n, singleton_draws[:B][np.isfinite(rb[:B])], rb[:B][np.isfinite(rb[:B])])
            iv_neff = [float(np.percentile(neff_vals, 2.5)), float(np.percentile(neff_vals, 97.5))]
        else:
            neff_vals = None; iv_neff = None
        rows.append({"point_rho": point, "accel": accel, "z0": z0,
                     "iv_percentile": iv_p, "iv_bca": iv_b,
                     "point_neff": point_neff, "iv_neff": iv_neff,
                     "neff_values": neff_vals.size if neff_vals is not None else 0,
                     "m_occ": m_occ, "valid_boot": len(vals)})
    return rows, n_eff_true


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--simulations", type=int, default=500)
    ap.add_argument("--bootstrap-reps", type=int, default=2000)
    ap.add_argument("--rhos", default="0.3,0.9")
    ap.add_argument("--seed", type=int, default=20261130)
    ap.add_argument("--bca-jackknife", type=int, default=400)
    ap.add_argument("--modes", default="fixed,full")
    args = ap.parse_args()
    rows, _ = dd.read_corpus(args.input)
    clusters = dd.aggregate(rows, ("scene_id",))
    sizes_all = np.array([int(c["n"]) for c in clusters], dtype=np.int64)
    successes_all = np.array([int(c["successes"]) for c in clusters], dtype=np.int64)
    K = int(sizes_all.size); N = int(sizes_all.sum())
    p_mean = float(successes_all.sum()) / N
    grid = []
    for rho in [float(x) for x in args.rhos.split(",") if x.strip()]:
        cell = {"rho_true": rho, "n_eff_true": neff(sizes_all.astype(float), rho)}
        for mode in [x.strip() for x in args.modes.split(",") if x.strip()]:
            sim_rows, true_neff = run_mode(mode, sizes_all, successes_all, p_mean, rho, args.simulations, args.bootstrap_reps, args.seed, args.bca_jackknife)
            if not sim_rows:
                cell[mode] = {"simulations_valid": 0}; continue
            cov_p = sum(1 for r in sim_rows if r["iv_percentile"][0] <= rho <= r["iv_percentile"][1])
            cov_b = sum(1 for r in sim_rows if r["iv_bca"][0] <= rho <= r["iv_bca"][1])
            accels = np.array([r["accel"] for r in sim_rows]); z0s = np.array([r["z0"] for r in sim_rows])
            out = {
                "simulations_requested": args.simulations,
                "simulations_valid": len(sim_rows),
                "rho_coverage_percentile": cov_p / len(sim_rows),
                "rho_coverage_percentile_wilson": wilson(cov_p, len(sim_rows)),
                "rho_coverage_bca": cov_b / len(sim_rows),
                "rho_point_mean": float(np.mean([r["point_rho"] for r in sim_rows])),
                "rho_point_sd": float(np.std([r["point_rho"] for r in sim_rows])),
                "acceleration": {"mean": float(accels.mean()), "sd": float(accels.std()),
                                 "p025": float(np.percentile(accels, 2.5)), "p50": float(np.percentile(accels, 50)),
                                 "p975": float(np.percentile(accels, 97.5)),
                                 "min": float(accels.min()), "max": float(accels.max()),
                                 "share_abs_gt_0_1": float(np.mean(np.abs(accels) > 0.1)),
                                 "share_abs_gt_0_3": float(np.mean(np.abs(accels) > 0.3))},
                "z0": {"mean": float(z0s.mean()), "sd": float(z0s.std()),
                       "p025": float(np.percentile(z0s, 2.5)), "p50": float(np.percentile(z0s, 50)),
                       "p975": float(np.percentile(z0s, 97.5)),
                       "min": float(z0s.min()), "max": float(z0s.max())},
                "m_occ_mean": float(np.mean([r["m_occ"] for r in sim_rows])),
                "m_occ_sd": float(np.std([r["m_occ"] for r in sim_rows])),
            }
            if mode == "full":
                cov_n = sum(1 for r in sim_rows if r["iv_neff"][0] <= true_neff <= r["iv_neff"][1])
                out["n_eff_coverage_percentile"] = cov_n / len(sim_rows)
                out["n_eff_coverage_percentile_wilson"] = wilson(cov_n, len(sim_rows))
                out["n_eff_point_mean"] = float(np.mean([r["point_neff"] for r in sim_rows]))
                out["n_eff_point_bias_mean"] = out["n_eff_point_mean"] - true_neff
                out["n_eff_interval_mean_width"] = float(np.mean([r["iv_neff"][1] - r["iv_neff"][0] for r in sim_rows]))
                out["n_eff_interval_relative_width"] = out["n_eff_interval_mean_width"] / true_neff
            cell[mode] = out
        grid.append(cell)
    obj = {"input": args.input, "clusters_total": K, "episodes": N, "multi_clusters": int((sizes_all >= 2).sum()),
           "p_mean": p_mean, "bootstrap_reps": args.bootstrap_reps, "simulations_per_mode": args.simulations,
           "method": "fixed: multinomial over multi clusters only; full: Multinomial(K,1/K) over all K clusters, discard singletons before ICC; full bootstrap draws K clusters then discards singletons; n_eff uses exact per-cluster sum with singleton draws contributing 1; percentile and BCa intervals",
           "grid": grid, "seed": args.seed, "note": "research calibration, not a corpus record"}
    Path(args.out).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"clusters": K, "multi": int((sizes_all >= 2).sum()), "rhos": [g["rho_true"] for g in grid]}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
