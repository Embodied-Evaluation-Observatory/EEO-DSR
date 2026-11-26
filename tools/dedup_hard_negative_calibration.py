#!/usr/bin/env python3
"""Hard-negative calibration for the shared fingerprint representation.

This tool uses real DROID state/action features.  It does not issue a DSR-D5a
duplicate count.  Positive pairs are controlled re-encodings of a real
trajectory (time shift for traj16, small re-encode noise for summary); negative
pairs are real distinct episodes with the same task or the same scene but a
different task.  W is a research placeholder unless a buyer declares it.
"""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path
import numpy as np
from scipy.stats import beta
from feature_representation import fit_representation

SIGS = 29
K = 16


def cp_upper(k: int, n: int, alpha: float = 0.05) -> float:
    if n == 0: return float("nan")
    if k >= n: return 1.0
    return float(beta.ppf(1 - alpha, k + 1, n - k))


def load_meta(path: str):
    return list(csv.DictReader(open(path, newline="")), )


def make_copies(x: np.ndarray, kind: str, rng, noise_frac: float = 0.02) -> np.ndarray:
    sd = np.std(x, axis=0, keepdims=True)
    sd = np.where(sd > 0, sd, 1.0)
    if kind == "traj_shift":
        y = x.reshape(x.shape[0], K, SIGS)
        y = np.roll(y, 1, axis=1)
        y = y.reshape(x.shape[0], -1)
        return y + rng.normal(scale=noise_frac, size=y.shape) * sd
    return x + rng.normal(scale=noise_frac, size=x.shape) * sd


def pairs_from_labels(meta, labels, rng, n_pairs):
    groups = {}
    for i, v in enumerate(labels):
        groups.setdefault(v, []).append(i)
    out = []
    keys = [k for k, v in groups.items() if len(v) >= 2]
    rng.shuffle(keys)
    for k in keys:
        js = groups[k]
        if len(js) < 2: continue
        i, j = rng.choice(js, 2, replace=False)
        out.append((int(i), int(j)))
        if len(out) >= n_pairs: break
    return out


def cos_pairs(fp, pairs):
    return np.array([float(np.dot(fp[i], fp[j])) for i, j in pairs])


def calibrate(rep_name, x, meta, dims, seed, n_pos_base, n_neg_each, thresholds):
    rng = np.random.default_rng(seed)
    base_ids = np.arange(x.shape[0])
    # Fit on the real episodes only; copies are transformed by the same basis.
    fp0, proj0, load, med, scale, mean, diag = fit_representation(x, dims, None)
    basis = {"loadings": load, "medians": med, "scales": scale, "means": mean}
    pos_bases = rng.choice(base_ids, size=min(n_pos_base, len(base_ids)), replace=False)
    positive_rows, positive_pairs = [], []
    for i in pos_bases:
        # Controlled re-encodes: 0.5% and 2% feature noise.  A 1-of-16 time
        # shift is kept as a separate sensitivity, not as a positive class,
        # because it moves resampled boundaries and changes content.
        for q in (0.005, 0.02):
            c = make_copies(x[i:i+1], "reencode", rng, q)
            positive_rows.append(c[0]); positive_pairs.append((len(positive_rows)-1, i, f"reencode_{q}"))
    # Build copy matrix and apply the original basis.
    copy_x = np.vstack(positive_rows)
    fp_copy, _, _, _, _, _, _ = fit_representation(copy_x, dims, basis)
    # Pair copy index -> original index; copy fingerprints and originals share basis.
    pos_cos = []
    for cidx, oi, kind in positive_pairs:
        pos_cos.append(float(np.dot(fp_copy[cidx], fp0[oi])))
    # Negative pairs from real labels.
    task_labels = [r["current_task"] for r in meta]
    scene_labels = [r["scene_id"] for r in meta]
    neg_task = pairs_from_labels(meta, task_labels, rng, n_neg_each)
    # Same scene, different task: build scene groups and pick differing tasks.
    by_scene = {}
    for i, s in enumerate(scene_labels): by_scene.setdefault(s, []).append(i)
    neg_scene = []
    scene_keys = [s for s, js in by_scene.items() if len({task_labels[j] for j in js}) >= 2]
    rng.shuffle(scene_keys)
    for s in scene_keys:
        js = by_scene[s]
        for _ in range(4):
            i, j = rng.choice(js, 2, replace=False)
            if task_labels[i] != task_labels[j]:
                neg_scene.append((int(i), int(j))); break
        if len(neg_scene) >= n_neg_each: break
    neg_pairs = neg_task + neg_scene
    pos_cos = np.asarray(pos_cos, dtype=float)
    neg_cos = cos_pairs(fp0, neg_pairs)
    if rep_name == "traj16":
        shift_x = make_copies(x, "traj_shift", rng, 0.0)
        fp_shift, _, _, _, _, _, _ = fit_representation(shift_x, dims, basis)
        result_shift = float(np.mean([np.dot(fp0[i], fp_shift[i]) for i in range(len(x))]))
    else:
        result_shift = None
    pos_types = [p[2] for p in positive_pairs]
    by_type = {}
    for typ in sorted(set(pos_types)):
        v = pos_cos[[i for i, t in enumerate(pos_types) if t == typ]]
        by_type[typ] = {"n": len(v), "mean": float(np.mean(v)),
            "quantiles": [float(np.percentile(v, q)) for q in (0, 5, 50, 95, 100)]}
    result = {"representation": rep_name, "dims": int(diag["output_dims"]),
              "n_positive": len(pos_cos), "n_negative": len(neg_cos),
              "positive_by_copy_type": by_type,
              "positive_cosine_mean": float(np.mean(pos_cos)), "positive_cosine_min": float(np.min(pos_cos)),
              "negative_cosine_mean": float(np.mean(neg_cos)), "negative_cosine_max": float(np.max(neg_cos)),
              "positive_cosine_quantiles": [float(np.percentile(pos_cos, q)) for q in (0, 5, 50, 95, 100)],
              "negative_cosine_quantiles": [float(np.percentile(neg_cos, q)) for q in (0, 5, 50, 95, 100)],
              "time_shift_sensitivity_mean_cosine": result_shift,
              "thresholds": []}
    for w in thresholds:
        fpr = int(np.sum(neg_cos >= w)); fnr = int(np.sum(pos_cos < w))
        rec = {"w": float(w), "false_positive": fpr, "false_negative": fnr,
            "fpr": fpr / len(neg_cos), "fnr": fnr / len(pos_cos),
            "fpr_upper95": cp_upper(fpr, len(neg_cos)), "fnr_upper95": cp_upper(fnr, len(pos_cos)),
            "by_copy_type": {}}
        for typ in sorted(set(pos_types)):
            v = pos_cos[[i for i, t in enumerate(pos_types) if t == typ]]
            k = int(np.sum(v < w))
            rec["by_copy_type"][typ] = {"n": len(v), "false_negative": k, "fnr": k / len(v),
                                        "fnr_upper95": cp_upper(k, len(v))}
        result["thresholds"].append(rec)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--traj", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dims", type=int, default=32)
    ap.add_argument("--seed", type=int, default=20261130)
    ap.add_argument("--positive-bases", type=int, default=150)
    ap.add_argument("--negative-each", type=int, default=150)
    ap.add_argument("--thresholds", default="0.90,0.95,0.99")
    args = ap.parse_args()
    meta = list(csv.DictReader(open(args.meta, newline="")))
    thresholds = [float(x) for x in args.thresholds.split(",") if x.strip()]
    zs = np.load(args.summary, allow_pickle=True); zt = np.load(args.traj, allow_pickle=True)
    ids_s = np.asarray(zs["episode_id"]).astype(str); ids_t = np.asarray(zt["episode_id"]).astype(str)
    if not np.array_equal(ids_s, ids_t): raise SystemExit("summary/traj episode ids differ")
    if len(meta) != len(ids_s): raise SystemExit("meta rows do not match npz rows")
    if any(meta[i]["uuid"] != ids_s[i] for i in range(len(ids_s))): raise SystemExit("meta uuid order differs")
    res = {"summary": calibrate("summary", zs["features"].astype(float), meta, args.dims, args.seed, args.positive_bases, args.negative_each, thresholds),
           "traj16": calibrate("traj16", zt["features"].astype(float), meta, args.dims, args.seed + 1, args.positive_bases, args.negative_each, thresholds),
           "w_notice": "W is a research placeholder unless a buyer declares it; this is not a DSR-D5a duplicate count or a D5b leak count.",
           "n_floor": "at least 59 pairs per class; exact Clopper-Pearson one-sided upper bounds"}
    Path(args.out).write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: {kk: v[kk] for kk in ("n_positive", "n_negative", "positive_cosine_mean", "negative_cosine_mean")} for k, v in res.items() if isinstance(v, dict) and "n_positive" in v}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
