#!/usr/bin/env python3
"""Variance probe: is rho identifiable on a real corpus?

Input: a CSV with exactly three required columns
  episode_id,scene_id,outcome

`scene_id` is the cluster key. At DROID site level it is the building; at cell
level it is `building||instruction`. The probe reports cluster success rates,
the zero-variance share as a readout, and the strict rho-free interval [K, N]
from the exact per-cluster sum. Zero-variance share is not a veto; constant
clusters enter MSB and push rho up.

No clock, fingerprint, bootstrap, or dedup enters this probe.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dataset_driver as dd


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_rows(path: str) -> tuple[list[dict[str, str]], str]:
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ["episode_id", "scene_id", "outcome"]:
            raise dd.ContractError(
                "CSV must have exactly the columns episode_id,scene_id,outcome; "
                f"got {reader.fieldnames}"
            )
        rows = list(reader)
    return rows, sha256_file(path)


def write_clusters(path: str, clusters: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow([
            "cluster_id", "n", "successes", "failures", "rate", "zero_variance", "estimable",
        ])
        for c in clusters:
            cid = str(c["cluster_id"]).replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
            writer.writerow([
                cid, c["n"], c["successes"], c["failures"],
                f"{c['rate']:.12f}", int(c["zero_variance"]), int(c["estimable"]),
            ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", default="")
    parser.add_argument("--source-rows", type=int, default=None,
                        help="rows before removing unclusterable episodes; default: input file")
    parser.add_argument("--cannot-cluster", type=int, default=None,
                        help="episodes with no cluster key; default: source-rows - usable")
    args = parser.parse_args()

    if os.path.exists(args.out):
        raise SystemExit(f"refusing to overwrite existing {args.out!r}")
    os.makedirs(args.out)

    rows, source_sha = read_rows(args.input)
    missing_scene = sum(1 for row in rows if not str(row.get("scene_id", "")).strip())
    usable = [row for row in rows if str(row.get("scene_id", "")).strip()]
    if not usable:
        raise dd.ContractError("no rows with a non-empty scene_id")
    probe = dd.variance_probe(usable, key_fields=("scene_id",))
    clusters = probe.pop("clusters_detail")
    write_clusters(os.path.join(args.out, "clusters.csv"), clusters)

    if args.source_rows is None:
        source_rows = len(rows)
        cannot_cluster = missing_scene
    else:
        source_rows = args.source_rows
        cannot_cluster = (
            args.cannot_cluster if args.cannot_cluster is not None
            else source_rows - len(usable)
        )
    if cannot_cluster < 0 or source_rows < len(usable) + cannot_cluster:
        raise dd.ContractError("source_rows, cannot_cluster, and usable rows do not add up")

    if probe["multi_clusters"] == 0:
        verdict = "all_singletons: rho not estimable; n_eff is exactly N"
    elif probe["variable_clusters"] == 0:
        verdict = "no_within_cluster_variation: rho not estimable; n_eff interval is [K,N]"
    else:
        verdict = (
            "within_cluster_variation_present: rho point estimate exists, "
            "no interval yet; zero-variance share is a readout, not a veto"
        )

    report = {
        "label": args.label,
        "input": os.path.basename(args.input),
        "input_sha256": source_sha,
        "source_rows": source_rows,
        "cannot_cluster": cannot_cluster,
        "unclusterable_share": (cannot_cluster / source_rows) if source_rows else None,
        "rows_input": len(rows),
        "rows_used": len(usable),
        "excluded_missing_scene": missing_scene,
        "cluster_key": "scene_id",
        "information_basis": {
            "variable_clusters": probe["variable_clusters"],
            "variable_episodes": probe["variable_episodes"],
            "constant_clusters": probe["constant_clusters"],
            "zero_variance_share_estimable": probe["zero_variance_share_estimable"],
            "zero_variance_role": "readout_only_not_a_veto",
            "n_eff_interval": [probe["neff_interval_low"], probe["neff_interval_high"]],
            "n_eff_interval_width": probe["neff_interval_width"],
            "n_eff_interval_relative_width": probe["neff_interval_relative_width"],
        },
        **probe,
        "verdict": verdict,
        "note": (
            "The rho-free interval [K,N] is strict for singletons and per-cluster sums. "
            "A point ICC is not a NEES reading; a NEES record waits for a cluster-bootstrap interval."
        ),
    }
    with open(os.path.join(args.out, "probe.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps({
        "label": report["label"],
        "clusters": report["clusters"],
        "episodes": report["episodes"],
        "excluded_missing_scene": report["excluded_missing_scene"],
        "multi_clusters": report["multi_clusters"],
        "variable_clusters": report["variable_clusters"],
        "zero_variance_share_estimable": report["zero_variance_share_estimable"],
        "n_eff_interval": report["information_basis"]["n_eff_interval"],
        "verdict": report["verdict"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
