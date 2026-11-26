"""Cluster bootstrap for the one-way ICC(1) on a binary outcome.

Resamples clusters, not episodes. Positive and negative ICC values are kept
as estimated; the n_eff path clips only for its own sum and reports the clip
separately in the driver report.

This is a research helper. It does not issue a NEES record.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dataset_driver as dd


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def percentile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("empty values")
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def resample_icc(clusters: list[dict], rng: random.Random, k: int) -> dict:
    sample = [clusters[rng.randrange(k)] for _ in range(k)]
    return dd.icc1(sample)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--label", required=True)
    p.add_argument("--replicates", type=int, default=1000)
    p.add_argument("--seed", type=int, default=20261126)
    p.add_argument("--source-rows", type=int)
    p.add_argument("--cannot-cluster", type=int, default=0)
    args = p.parse_args()

    rows, input_sha = dd.read_corpus(args.input)
    clusters = dd.aggregate(rows, ("scene_id",))
    point = dd.icc1(clusters)
    k = len(clusters)
    if point.get("status") != "computed":
        raise dd.ContractError(f"point ICC not computable: {point}")
    rng = random.Random(args.seed)
    reps = []
    n_eff_reps = []
    for _ in range(args.replicates):
        sample = [clusters[rng.randrange(k)] for _ in range(k)]
        r = dd.icc1(sample)
        if r.get("status") == "computed":
            rho = float(r["rho"])
            reps.append(rho)
            n_eff_reps.append(dd.neff_at_rho(sample, rho)["n_eff"])
    reps_all = list(reps)
    reps = [x for x in reps if math.isfinite(x)]
    if not reps:
        raise dd.ContractError("no valid bootstrap replicates")
    result = {
        "label": args.label,
        "input": args.input,
        "input_sha256": input_sha,
        "source_rows": args.source_rows,
        "cannot_cluster": args.cannot_cluster,
        "rows_used": len(rows),
        "clusters": k,
        "method": "cluster bootstrap; resample K clusters with replacement; ICC(1) per replicate",
        "replicates_requested": args.replicates,
        "replicates_valid": len(reps),
        "point": {
            "rho_unclipped": point["rho"],
            "rho_zero_clipped": max(0.0, point["rho"]),
            "msb": point["msb"],
            "msw": point["msw"],
            "m0": point["m0"],
            "p_bar": point.get("p_bar"),
        },
        "interval_95": {
            "low": percentile(reps, 0.025),
            "high": percentile(reps, 0.975),
            "method": "percentile",
        },
        "n_eff_interval": {
            "low": min(percentile(n_eff_reps, 0.025), percentile(n_eff_reps, 0.975)),
            "high": max(percentile(n_eff_reps, 0.025), percentile(n_eff_reps, 0.975)),
            "method": "per replicate n_eff at its rho, then percentile",
            "relative_width": (max(percentile(n_eff_reps, 0.025), percentile(n_eff_reps, 0.975)) - min(percentile(n_eff_reps, 0.025), percentile(n_eff_reps, 0.975))) / ((max(percentile(n_eff_reps, 0.025), percentile(n_eff_reps, 0.975)) + min(percentile(n_eff_reps, 0.025), percentile(n_eff_reps, 0.975))) / 2),
        },
        "distribution": {
            "min": min(reps),
            "p025": percentile(reps, 0.025),
            "median": percentile(reps, 0.5),
            "p975": percentile(reps, 0.975),
            "max": max(reps),
            "negative_share": sum(1 for x in reps_all if x < 0.0) / len(reps_all),
            "below_zero_clipped_to_zero": sum(1 for x in reps_all if x < 0.0),
        },
        "nees_record": {
            "status": "not_issued",
            "reason": "bootstrap interval is a diagnostic; record needs the full gate",
        },
        "note": "The interval is for the ICC on this axis, not for training information.",
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "label": args.label, "clusters": k, "rho": point["rho"],
        "interval": result["interval_95"], "valid": len(reps),
        "negative_share": result["distribution"]["negative_share"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
