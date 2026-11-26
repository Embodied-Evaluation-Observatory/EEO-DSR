#!/usr/bin/env python3
"""Deterministic episode feature representation shared by dedup and ICR.

Input is an `.npz` with:
  episode_id  (N,) strings
  features    (N, D) finite numeric matrix
  cluster_id  (N,) strings, optional

Output is an `.npz` with the same episodes plus `fingerprints` (N, K),
L2-normalized PCA scores. The representation is method-fixed:
median impute -> IQR robust scale -> centre -> SVD -> sign fix -> L2.
No threshold is chosen here. `--dedup-threshold W` only lists candidate
pairs for a buyer-declared W; it does not decide whether two episodes are
duplicates.

This is an implementation of the shared upstream only. It does not issue a
DSR-D5a duplicate count and does not compute ICR; both need their own
calibration and record fields.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def _as_str_array(x) -> np.ndarray:
    return np.asarray([str(v) for v in np.asarray(x).reshape(-1)], dtype=object)


def _median_impute(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    med = np.nanmedian(x, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    bad = ~np.isfinite(x)
    if bad.any():
        x = x.copy()
        x[bad] = np.take(med, np.where(bad)[1])
    return x


def _robust_scale(x: np.ndarray) -> np.ndarray:
    q1, q3 = np.percentile(x, [25, 75], axis=0)
    iqr = q3 - q1
    sd = np.std(x, axis=0)
    scale = np.where(iqr > 0, iqr / 1.349, sd)
    return np.where(scale > 0, scale, 1.0)


def fit_representation(features: np.ndarray, dims: int | None = None,
                       basis: dict | None = None):
    """Fit or apply the fixed representation.

    Returns fingerprints (L2-normalized, for cosine dedup), projections
    (pre-L2, for ICR dispersion), loadings, preprocessing parameters, and
    diagnostics.  When ``basis`` is supplied, the SVD basis and medians/
    scales/means are reused rather than re-fitted: reference and target then
    live in the same coordinate space.  This is the shared-basis contract.
    """
    x = _median_impute(features)
    if x.ndim != 2:
        raise ValueError("features must be a 2-D matrix")
    if x.shape[0] < 2 or x.shape[1] < 1:
        raise ValueError("need at least two episodes and one feature")
    if basis is not None:
        med = np.asarray(basis["medians"], dtype=float)
        scales = np.asarray(basis["scales"], dtype=float)
        means = np.asarray(basis["means"], dtype=float)
        loadings = np.asarray(basis["loadings"], dtype=float)
        if med.size != x.shape[1] or scales.size != x.shape[1] or means.size != x.shape[1]:
            raise ValueError("basis preprocessing does not match input feature dimensions")
        if loadings.shape[1] != x.shape[1]:
            raise ValueError("basis loadings do not match input feature dimensions")
        x = (x - means) / scales
        projections = x @ loadings.T
        k = loadings.shape[0]
        diag = {"n_episodes": int(x.shape[0]), "input_dims": int(x.shape[1]),
                "output_dims": int(k), "basis_reused": True}
    else:
        med = np.nanmedian(features, axis=0)
        med = np.where(np.isfinite(med), med, 0.0)
        x0 = _median_impute(features)
        means = x0.mean(axis=0, keepdims=True)
        scales = _robust_scale(x0 - means)
        x = (x0 - means) / scales
        u, s, vt = np.linalg.svd(x, full_matrices=False)
        max_k = min(x.shape[1], x.shape[0] - 1, s.size)
        k = max_k if dims is None else max(1, min(int(dims), max_k))
        loadings = vt[:k].copy()
        # Deterministic sign: largest absolute loading is positive.
        for j in range(k):
            if loadings[j, np.argmax(np.abs(loadings[j]))] < 0:
                loadings[j] *= -1.0
        projections = x @ loadings.T
        ev = (s * s) / max(1.0, float(x.shape[0] - 1))
        evr = ev / ev.sum() if ev.sum() > 0 else np.zeros_like(ev)
        diag = {
            "n_episodes": int(x.shape[0]),
            "input_dims": int(x.shape[1]),
            "output_dims": int(k),
            "basis_reused": False,
            "explained_variance_ratio": [float(v) for v in evr[:k]],
            "cumulative_explained_variance": float(evr[:k].sum()),
        }
    norms = np.linalg.norm(projections, axis=1, keepdims=True)
    fingerprints = np.divide(projections, norms, out=np.zeros_like(projections), where=norms > 0)
    return fingerprints, projections, loadings, med, scales.reshape(-1), means.reshape(-1), diag


def _cosine_pairs(fingerprints: np.ndarray, threshold: float, chunk: int = 512):
    """Pairs with cosine >= threshold, excluding self and duplicate order."""
    n = fingerprints.shape[0]
    out = []
    for start in range(0, n, chunk):
        block = fingerprints[start:start + chunk] @ fingerprints.T
        rows, cols = np.where(block >= threshold)
        for i, j in zip(rows, cols):
            gi, gj = start + int(i), int(j)
            if gi < gj:
                out.append([gi, gj, float(block[i, j])])
    return out


def _load_basis(path: str):
    z = np.load(path, allow_pickle=True)
    need = ("loadings", "medians", "scales", "means")
    if any(k not in z for k in need):
        raise ValueError("basis npz must contain loadings, medians, scales, means")
    return {k: np.asarray(z[k], dtype=float) for k in need}


def run(input_path: str, out_prefix: str, dims: int | None, threshold: float | None,
        basis_path: str | None = None):
    z = np.load(input_path, allow_pickle=True)
    if "episode_id" not in z or "features" not in z:
        raise ValueError("input must contain episode_id and features")
    episode_id = _as_str_array(z["episode_id"])
    features = np.asarray(z["features"], dtype=float)
    if episode_id.size != features.shape[0]:
        raise ValueError("episode_id length does not match features rows")
    if threshold is not None and not (0.0 < threshold <= 1.0):
        raise ValueError("dedup threshold must be in (0, 1]")
    basis = _load_basis(basis_path) if basis_path else None
    fingerprints, projections, loadings, medians, scales, means, diag = fit_representation(features, dims, basis)
    cluster_id = z["cluster_id"] if "cluster_id" in z else None
    if cluster_id is not None:
        cluster_id = _as_str_array(cluster_id)
        if cluster_id.size != episode_id.size:
            raise ValueError("cluster_id length does not match episode_id")
    prefix = Path(out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "episode_id": episode_id,
        "fingerprints": fingerprints.astype(np.float32),
        "projections": projections.astype(np.float32),
        "loadings": loadings.astype(np.float32),
        "medians": medians.astype(np.float32),
        "scales": scales.astype(np.float32),
        "means": means.astype(np.float32),
    }
    if cluster_id is not None:
        payload["cluster_id"] = cluster_id
    np.savez_compressed(str(prefix) + ".npz", **payload)
    meta = {
        "input": str(input_path),
        "input_sha256": hashlib.sha256(Path(input_path).read_bytes()).hexdigest(),
        "method": "median impute; IQR robust scale; centre; SVD; sign fix; projections kept; L2 normalize for cosine",
        "representation": "episode-feature-pca-cosine-v1",
        "fingerprint_dims": diag["output_dims"],
        "basis_path": str(basis_path) if basis_path else None,
        "basis_sha256": hashlib.sha256(Path(basis_path).read_bytes()).hexdigest() if basis_path else None,
        "basis_reused": bool(diag.get("basis_reused")),
        "diagnostics": diag,
        "dedup_threshold": threshold,
        "dedup_threshold_basis": "buyer-declared; absent means no candidate list",
        "dedup_notice": "cosine candidate list is not a duplicate count; DSR-D5a still needs calibration",
        "icr_notice": "ICR uses `projections` before L2, not `fingerprints`; ICR interval is not issued here",
        "l2_notice": "fingerprints are L2-normalized for cosine dedup; projections retain amplitude for ICR dispersion",
    }
    if threshold is not None:
        pairs = _cosine_pairs(fingerprints, threshold)
        meta["dedup_candidates"] = [
            {"i": i, "j": j, "episode_id_i": episode_id[i], "episode_id_j": episode_id[j], "cosine": c}
            for i, j, c in pairs
        ]
        meta["dedup_candidate_count"] = len(pairs)
    Path(str(prefix) + ".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"out": str(prefix), "n": int(episode_id.size), "dims": diag["output_dims"],
                      "candidates": meta.get("dedup_candidate_count")}, ensure_ascii=False))
    return 0


def self_test() -> None:
    rng = np.random.default_rng(20261129)
    base = rng.normal(size=(120, 12))
    dup = base[:20] + rng.normal(scale=0.01, size=(20, 12))
    distinct = rng.normal(size=(20, 12)) + 5.0
    features = np.vstack([base, dup, distinct])
    ids = np.array([f"e{i}" for i in range(features.shape[0])], dtype=object)
    zpath = "/tmp/eeo-feature-selftest.npz"
    np.savez_compressed(zpath, episode_id=ids, features=features)
    run(zpath, "/tmp/eeo-feature-selftest", 8, 0.95)
    out = np.load("/tmp/eeo-feature-selftest.npz", allow_pickle=True)
    fps = out["fingerprints"]
    sim = fps @ fps.T
    dup_cos = np.mean([sim[i, 120 + i] for i in range(20)])
    distinct_cos = np.mean([sim[i, 140 + i] for i in range(20)])
    assert dup_cos > 0.95, dup_cos
    assert distinct_cos < 0.5, distinct_cos
    meta = json.loads(Path("/tmp/eeo-feature-selftest.json").read_text())
    assert meta["dedup_candidate_count"] >= 20
    print(json.dumps({"duplicate_cosine_mean": float(dup_cos),
                      "distinct_cosine_mean": float(distinct_cos),
                      "candidates": meta["dedup_candidate_count"]}, ensure_ascii=False))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input")
    ap.add_argument("--out-prefix")
    ap.add_argument("--dims", type=int, default=64)
    ap.add_argument("--dedup-threshold", type=float)
    ap.add_argument("--basis")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.input or not args.out_prefix:
        raise SystemExit("--input and --out-prefix are required unless --self-test")
    return run(args.input, args.out_prefix, args.dims, args.dedup_threshold, args.basis)


if __name__ == "__main__":
    raise SystemExit(main())
