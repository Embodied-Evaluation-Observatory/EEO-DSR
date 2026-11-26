#!/usr/bin/env python3
"""Buyer-reference distribution deviation for episode fingerprints.

Inputs are two `.npz` files from `feature_representation.py`:
  reference.npz  buyer/reference population
  target.npz     dataset population

The readout compares the two fingerprint distributions. It does not rank a
dataset, does not set an acceptance threshold, and does not convert deviation
into a price or a go/no-go. A buyer supplies the reference population; EEO
reports where the target sits relative to it.

Metrics are descriptive:
- standardized mean-shift vector (per dimension) and its L2 norm
- energy distance (unbiased estimator) with a bootstrap interval
- maximum per-dimension Kolmogorov-Smirnov statistic
- share of target points outside the reference 0.5-99.5% per-dimension range
- nearest-reference cosine distance, summarized by quantiles

No metric has a built-in pass line. `reference_n` and `target_n` are printed
because a deviation computed from a small reference is a weak readout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

NOTICE = ("Descriptive readout only. No threshold, no ranking, no acceptance decision. "
          "The reference population is buyer-supplied; EEO does not own or choose it.")


def _load(path: str, matrix: str = "fingerprints"):
    z = np.load(path, allow_pickle=True)
    if matrix not in z:
        raise ValueError(f"{path}: missing {matrix}")
    return np.asarray(z[matrix], dtype=float)


def _check(x: np.ndarray, name: str):
    if x.ndim != 2 or x.shape[0] < 2 or x.shape[1] < 1:
        raise ValueError(f"{name}: need a 2-D matrix with at least two rows")
    if not np.isfinite(x).all():
        raise ValueError(f"{name}: non-finite fingerprints")


def _pairwise_l2(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # Chunked to avoid a full NxM allocation for large corpora.
    out = np.empty((a.shape[0], b.shape[0]), dtype=float)
    for i in range(0, a.shape[0], 512):
        aa = a[i:i + 512]
        out[i:i + 512] = np.sqrt(((aa[:, None, :] - b[None, :, :]) ** 2).sum(axis=2))
    return out


def energy_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Biased (V-statistic) energy distance; nonnegative, diagonal included.

    The unbiased estimator can be negative on small samples; this descriptive
    readout uses the V-statistic so a negative number does not appear. It is
    not a test statistic and no p-value is attached.
    """
    xy = _pairwise_l2(a, b).mean()
    xx = _pairwise_l2(a, a).mean()
    yy = _pairwise_l2(b, b).mean()
    return float(max(0.0, 2.0 * xy - xx - yy))


def ks_stat(a: np.ndarray, b: np.ndarray) -> float:
    vals = np.sort(np.concatenate([a, b]))
    ca = np.searchsorted(np.sort(a), vals, side="right") / a.size
    cb = np.searchsorted(np.sort(b), vals, side="right") / b.size
    return float(np.max(np.abs(ca - cb)))


def _bootstrap_energy(a: np.ndarray, b: np.ndarray, reps: int, seed: int):
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(reps):
        ai = rng.integers(0, a.shape[0], a.shape[0])
        bi = rng.integers(0, b.shape[0], b.shape[0])
        vals.append(energy_distance(a[ai], b[bi]))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def compare(reference: np.ndarray, target: np.ndarray, reps: int = 200, seed: int = 20261129):
    if reference.shape[1] != target.shape[1]:
        raise ValueError("reference and target fingerprint dimensions differ")
    pooled_sd = np.sqrt((reference.var(axis=0, ddof=1) + target.var(axis=0, ddof=1)) / 2.0)
    pooled_sd = np.where(pooled_sd > 0, pooled_sd, 1.0)
    mean_shift = (target.mean(axis=0) - reference.mean(axis=0)) / pooled_sd
    ref_lo, ref_hi = np.percentile(reference, [0.5, 99.5], axis=0)
    outside = (target < ref_lo) | (target > ref_hi)
    nearest = _pairwise_l2(target, reference).min(axis=1)
    ks = [ks_stat(reference[:, j], target[:, j]) for j in range(reference.shape[1])]
    return {
        "reference_n": int(reference.shape[0]),
        "target_n": int(target.shape[0]),
        "dims": int(reference.shape[1]),
        "mean_shift_l2": float(np.linalg.norm(mean_shift)),
        "mean_shift_max_abs_z": float(np.max(np.abs(mean_shift))),
        "mean_shift_per_dim": [float(v) for v in mean_shift],
        "energy_distance": energy_distance(reference, target),
        "energy_distance_bootstrap_95": _bootstrap_energy(reference, target, reps, seed),
        "ks_max": float(max(ks)),
        "ks_per_dim": [float(v) for v in ks],
        "target_outside_reference_0.5_99.5_share": float(outside.any(axis=1).mean()),
        "target_outside_reference_per_dim_share": [float(v) for v in outside.mean(axis=0)],
        "nearest_reference_distance_median": float(np.median(nearest)),
        "nearest_reference_distance_p95": float(np.percentile(nearest, 95)),
        "notice": NOTICE,
    }


def run(reference_path: str, target_path: str, out: str, reps: int, matrix: str = "fingerprints"):
    ref = _load(reference_path, matrix); tgt = _load(target_path, matrix)
    _check(ref, "reference"); _check(tgt, "target")
    result = compare(ref, tgt, reps=reps)
    result["matrix"] = matrix
    result["reference_input"] = str(reference_path)
    result["target_input"] = str(target_path)
    result["reference_sha256"] = hashlib.sha256(Path(reference_path).read_bytes()).hexdigest()
    result["target_sha256"] = hashlib.sha256(Path(target_path).read_bytes()).hexdigest()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("reference_n", "target_n", "mean_shift_l2",
                                             "energy_distance", "ks_max",
                                             "target_outside_reference_0.5_99.5_share")},
                     ensure_ascii=False))
    return 0


def self_test() -> None:
    rng = np.random.default_rng(20261129)
    ref = rng.normal(size=(200, 8)); ref /= np.linalg.norm(ref, axis=1, keepdims=True)
    shifted = ref[:120] + rng.normal(scale=0.05, size=(120, 8))
    shifted /= np.linalg.norm(shifted, axis=1, keepdims=True)
    a = compare(ref, ref, reps=50)
    b = compare(ref, shifted, reps=50)
    assert a["mean_shift_l2"] < 1e-9, a["mean_shift_l2"]
    assert b["mean_shift_l2"] > a["mean_shift_l2"]
    assert a["energy_distance"] < 0.05, a["energy_distance"]
    assert b["energy_distance"] > a["energy_distance"]
    print(json.dumps({"identical_mean_shift": a["mean_shift_l2"],
                      "shifted_mean_shift": b["mean_shift_l2"],
                      "identical_energy": a["energy_distance"],
                      "shifted_energy": b["energy_distance"]}, ensure_ascii=False))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reference")
    ap.add_argument("--target")
    ap.add_argument("--out")
    ap.add_argument("--bootstrap-reps", type=int, default=200)
    ap.add_argument("--matrix", default="fingerprints", choices=("fingerprints", "projections"))
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not (args.reference and args.target and args.out):
        raise SystemExit("--reference, --target and --out are required unless --self-test")
    return run(args.reference, args.target, args.out, args.bootstrap_reps, args.matrix)


if __name__ == "__main__":
    raise SystemExit(main())
