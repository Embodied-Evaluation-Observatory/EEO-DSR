#!/usr/bin/env python3
"""Prepare a same-corpus building-A vs building-B reference deviation.

The SVD/preprocessing basis is fitted once on building A and applied to both
sides.  The output is explicitly a site-to-site distribution deviation, not a
buyer-deployment deviation.
"""
from __future__ import annotations
import argparse, csv, json, hashlib
from pathlib import Path
import numpy as np
from feature_representation import fit_representation


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--features", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--reference-building", required=True)
    ap.add_argument("--target-building", required=True)
    ap.add_argument("--out-prefix", required=True)
    ap.add_argument("--dims", type=int, default=16)
    args = ap.parse_args()
    z = np.load(args.features, allow_pickle=True)
    ids = np.asarray(z["episode_id"]).astype(str); x = np.asarray(z["features"], dtype=float)
    meta = list(csv.DictReader(open(args.meta, newline="", encoding="utf-8")))
    if len(meta) != len(ids): raise SystemExit("meta rows do not match features")
    if any(meta[i]["uuid"] != ids[i] for i in range(len(ids))): raise SystemExit("meta uuid order differs")
    ref_idx = [i for i, r in enumerate(meta) if r["building"] == args.reference_building]
    tgt_idx = [i for i, r in enumerate(meta) if r["building"] == args.target_building]
    if len(ref_idx) < 3 or len(tgt_idx) < 3: raise SystemExit("both buildings need at least 3 episodes")
    if args.reference_building == args.target_building: raise SystemExit("reference and target building are the same")
    ref_x, tgt_x = x[ref_idx], x[tgt_idx]
    # Fit only on reference; apply the same basis to target.
    fp_ref, proj_ref, load, med, scale, mean, diag = fit_representation(ref_x, args.dims, None)
    basis = {"loadings": load, "medians": med, "scales": scale, "means": mean}
    fp_tgt, proj_tgt, _, _, _, _, diag_t = fit_representation(tgt_x, args.dims, basis)
    np.savez(args.out_prefix + "-reference.npz", episode_id=np.asarray(ids)[ref_idx],
             fingerprints=fp_ref, projections=proj_ref)
    np.savez(args.out_prefix + "-target.npz", episode_id=np.asarray(ids)[tgt_idx],
             fingerprints=fp_tgt, projections=proj_tgt)
    # Same basis hash from the reference npz payload, for reproducibility.
    basis_bytes = np.concatenate([load.ravel(), med.ravel(), scale.ravel(), mean.ravel()])
    pair = {
        "reference_building": args.reference_building,
        "target_building": args.target_building,
        "reference_n": len(ref_idx), "target_n": len(tgt_idx),
        "dims": int(diag["output_dims"]), "basis_fit_side": "reference",
        "basis_sha256": hashlib.sha256(basis_bytes.tobytes()).hexdigest(),
        "matrix_for_deviation": "fingerprints",
        "claim_scope": "basis_fit_direction_dependent",
        "swap_side_note": "Read with the opposite-direction pair; single-side readout is not publishable alone.",
        "note": "Same-corpus site-to-site distribution deviation. This is not a buyer deployment reference and not an acceptance decision.",
    }
    Path(args.out_prefix + "-pair.json").write_text(json.dumps(pair, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(pair, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
