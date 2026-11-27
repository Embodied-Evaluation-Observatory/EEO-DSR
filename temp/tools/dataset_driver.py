#!/usr/bin/env python3
"""Dataset-side arithmetic for EEO-DSR.

This module is a pipeline: it turns episode-level `(episode_id, scene_id, outcome)`
rows into cluster counts, then computes design effect, effective sample size,
zero-failure bounds, cluster budget, and the rho-low cap. It is deliberately
pure: no files, no clock, no bootstrap, no dedup, no random numbers.

The validator's "recompute by formula" path is different. It checks numbers a
record already supplies. This module computes numbers from corpus rows. Do not
use the validator as a substitute for this pipeline.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import os
from typing import Any, Iterable, Mapping, Sequence

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZERO_VARIANCE_THRESHOLD = 0.90


class ContractError(ValueError):
    """Raised when input violates a stated contract."""


def _as_outcome(value: Any, episode_id: str) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int) and value in (0, 1):
        return value
    if isinstance(value, str) and value.strip().lower() in ("0", "1", "true", "false"):
        return 1 if value.strip().lower() in ("1", "true") else 0
    raise ContractError(f"episode {episode_id!r}: outcome must be 0 or 1, got {value!r}")


def aggregate(
    rows: Iterable[Mapping[str, Any]],
    key_fields: Sequence[str] = ("scene_id",),
    episode_field: str = "episode_id",
    outcome_field: str = "outcome",
) -> list[dict[str, Any]]:
    """Aggregate episode rows into clusters.

    Each episode must appear exactly once. A cluster is the tuple of
    ``key_fields``. The result is sorted by cluster_id for stable output.
    """
    if not key_fields:
        raise ContractError("key_fields must not be empty")
    seen_episodes: set[str] = set()
    buckets: dict[str, dict[str, Any]] = {}

    for row in rows:
        if episode_field not in row:
            raise ContractError(f"missing column {episode_field!r}")
        episode_id = str(row[episode_field]).strip()
        if not episode_id:
            raise ContractError("empty episode_id")
        if episode_id in seen_episodes:
            raise ContractError(f"duplicate episode_id {episode_id!r}")
        seen_episodes.add(episode_id)

        parts = []
        for field in key_fields:
            if field not in row:
                raise ContractError(f"missing column {field!r}")
            part = str(row[field]).strip()
            if not part:
                raise ContractError(f"episode {episode_id!r}: empty {field!r}")
            parts.append(part)
        cluster_id = "||".join(parts)
        bucket = buckets.setdefault(cluster_id, {"cluster_id": cluster_id, "n": 0, "successes": 0})
        bucket["n"] += 1
        bucket["successes"] += _as_outcome(row.get(outcome_field), episode_id)

    out = []
    for cluster in buckets.values():
        n = cluster["n"]
        successes = cluster["successes"]
        rate = successes / n
        out.append({
            "cluster_id": cluster["cluster_id"],
            "n": n,
            "successes": successes,
            "failures": n - successes,
            "rate": rate,
            "zero_variance": rate in (0.0, 1.0),
            "estimable": n >= 2,
        })
    out.sort(key=lambda item: item["cluster_id"])
    return out


def summarize_clusters(clusters: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Cluster accounting with exact singleton contributions.

    Singletons contribute exactly one independent observation for any rho, so
    the rho-free n_eff interval is [K, N]. The zero-variance share is a readout,
    not a veto: constant clusters add nothing to MSW but still enter MSB, which
    pushes rho up rather than making it undefined.
    """
    if not clusters:
        raise ContractError("no clusters")
    k = len(clusters)
    n_total = sum(int(c["n"]) for c in clusters)
    singletons = [c for c in clusters if int(c["n"]) == 1]
    multi = [c for c in clusters if int(c["n"]) >= 2]
    variable = [c for c in multi if not bool(c["zero_variance"])]
    constant = [c for c in multi if bool(c["zero_variance"])]
    k_single = len(singletons)
    k_multi = len(multi)
    k_var = len(variable)
    k_const = len(constant)
    n_single = sum(int(c["n"]) for c in singletons)
    n_multi = sum(int(c["n"]) for c in multi)
    n_var = sum(int(c["n"]) for c in variable)
    n_const = sum(int(c["n"]) for c in constant)
    zero_all = sum(1 for c in clusters if bool(c["zero_variance"]))
    width = n_total - k
    return {
        "clusters": k,
        "episodes": n_total,
        "singletons": k_single,
        "singleton_episodes": n_single,
        "singleton_exact_contribution": k_single,
        "multi_clusters": k_multi,
        "multi_episodes": n_multi,
        "variable_clusters": k_var,
        "variable_episodes": n_var,
        "constant_clusters": k_const,
        "constant_episodes": n_const,
        "zero_variance_clusters_all": zero_all,
        "zero_variance_share_all": zero_all / k,
        "zero_variance_clusters_estimable": k_const,
        "zero_variance_share_estimable": (k_const / k_multi) if k_multi else None,
        "zero_variance_share": (k_const / k_multi) if k_multi else None,
        "neff_interval_low": k,
        "neff_interval_high": n_total,
        "neff_interval_width": width,
        "neff_interval_relative_width": width / n_total,
        "denominator": "all clusters; singletons contribute exactly 1",
    }


def icc1(clusters: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """One-way random-effects ICC(1) for a binary outcome.

    All clusters with n >= 2 enter, including constant clusters. Constant
    clusters contribute 0 to MSW and still enter MSB; excluding them would
    discard the strongest evidence that rho is high.
    """
    est = [c for c in clusters if int(c["n"]) >= 2]
    k = len(est)
    if k < 2:
        return {"status": "unestimable", "reason": "fewer_than_two_multi_clusters"}
    n_est = sum(int(c["n"]) for c in est)
    if n_est <= k:
        return {"status": "unestimable", "reason": "no_within_cluster_degrees_of_freedom"}
    p_bar = sum(int(c["successes"]) for c in est) / n_est

    msb_num = sum(int(c["n"]) * (float(c["rate"]) - p_bar) ** 2 for c in est)
    msb = msb_num / (k - 1)
    msw_num = sum(int(c["n"]) * float(c["rate"]) * (1.0 - float(c["rate"])) for c in est)
    msw = msw_num / (n_est - k)
    m0 = (n_est - sum(int(c["n"]) ** 2 for c in est) / n_est) / (k - 1)
    if msw == 0:
        if msb == 0:
            return {
                "status": "unestimable",
                "reason": "no_between_or_within_variance",
                "msb": msb,
                "msw": msw,
                "m0": m0,
            }
        return {
            "status": "computed",
            "estimator": "outcome_icc",
            "rho": 1.0,
            "msb": msb,
            "msw": msw,
            "m0": m0,
            "warning": "zero_within_cluster_variance; rho set to 1",
        }
    rho = (msb - msw) / (msb + (m0 - 1) * msw)
    return {
        "status": "computed",
        "estimator": "outcome_icc",
        "rho": rho,
        "msb": msb,
        "msw": msw,
        "m0": m0,
        "p_bar": p_bar,
    }


def _rho_used(rho: float) -> float:
    if not math.isfinite(rho):
        raise ContractError("rho must be finite")
    if rho > 1:
        raise ContractError("rho must be <= 1")
    return max(0.0, float(rho))


def neff_at_rho(clusters: Sequence[Mapping[str, Any]], rho: float) -> dict[str, Any]:
    """Exact per-cluster sum: sum_k n_k / (1 + (n_k - 1) * rho).

    At rho=0 this is N; at rho=1 it is K. Singletons contribute exactly 1 at
    every rho, so the interval [K, N] is strict and rho-free.
    """
    if not clusters:
        raise ContractError("no clusters")
    rho_used = _rho_used(rho)
    contributions = [
        (int(c["n"]) == 1, int(c["n"]) / (1.0 + (int(c["n"]) - 1.0) * rho_used))
        for c in clusters
    ]
    singleton = sum(value for is_single, value in contributions if is_single)
    multi = sum(value for is_single, value in contributions if not is_single)
    n_total = sum(int(c["n"]) for c in clusters)
    return {
        "n_eff": singleton + multi,
        "singleton_contribution": singleton,
        "multi_contribution": multi,
        "n_clusters": len(clusters),
        "n_dedup": n_total,
        "rho": rho,
        "rho_used": rho_used,
    }


def neff_interval(clusters: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Strict rho-free interval for the per-cluster sum."""
    low = neff_at_rho(clusters, 1.0)
    high = neff_at_rho(clusters, 0.0)
    return {
        "low": low["n_eff"],
        "high": high["n_eff"],
        "width": high["n_eff"] - low["n_eff"],
        "relative_width": (high["n_eff"] - low["n_eff"]) / high["n_eff"],
        "singleton_contribution": low["singleton_contribution"],
        "method": "per_cluster_sum; singletons exact; rho in [0,1]",
        "lower_share_of_dedup": low["n_eff"] / high["n_eff"],
    }


def design_effect(mean_cluster_size: float, rho: float) -> float:
    """mbar deff = 1 + (mbar - 1) * rho; negative rho truncates to 0.

    Only for the cap/comparison path. The exact n_eff uses per-cluster sums.
    """
    if mean_cluster_size < 1:
        raise ContractError("mean_cluster_size must be >= 1")
    rho_used = _rho_used(rho)
    return 1.0 + (float(mean_cluster_size) - 1.0) * rho_used


def mbar_effective_n(n_clusters: int, mean_cluster_size: float, rho: float) -> dict[str, Any]:
    """The old mbar approximation. Keep it only for cap/comparison.

    It assumes equal cluster size. In skewed clusters it overstates n_eff; the
    per-cluster sum is the exact diagnostic.
    """
    if n_clusters <= 0:
        raise ContractError("n_clusters must be > 0")
    n_c = n_clusters * mean_cluster_size
    deff = design_effect(mean_cluster_size, rho)
    return {
        "n_clusters": n_clusters,
        "mean_cluster_size": mean_cluster_size,
        "n_dedup": n_c,
        "rho": rho,
        "rho_used": _rho_used(rho),
        "deff": deff,
        "n_eff": n_c / deff,
        "method": "mbar_approximation",
    }


def effective_n(n_clusters: int, mean_cluster_size: float, rho: float) -> dict[str, Any]:
    """Backward-compatible alias for the mbar approximation."""
    return mbar_effective_n(n_clusters, mean_cluster_size, rho)


def n_eff_diagnostics(clusters: Sequence[Mapping[str, Any]], rho: float) -> dict[str, Any]:
    """Compare exact per-cluster n_eff with the mbar approximation at one rho."""
    exact = neff_at_rho(clusters, rho)
    n_total = exact["n_dedup"]
    k = exact["n_clusters"]
    mbar = mbar_effective_n(k, n_total / k, rho)
    return {
        **exact,
        "deff_effective": n_total / exact["n_eff"],
        "mbar_deff": mbar["deff"],
        "mbar_n_eff": mbar["n_eff"],
        "mbar_overstatement": mbar["n_eff"] / exact["n_eff"] - 1.0,
        "method": "per_cluster_sum",
        "claim_scope": "success_rate_precision_not_training_information",
    }


def upper95_zero_failure(n_ind: int) -> float:
    """Exact one-sided 95% upper bound under zero observed failures."""
    if n_ind <= 0:
        raise ContractError("n_ind must be > 0")
    return 1.0 - 0.05 ** (1.0 / n_ind)


def zero_failure_bounds(n_dedup: int, n_clusters: int) -> dict[str, Any]:
    """Print both ends: by cluster (conservative) and by dedup episode (narrow)."""
    if n_dedup <= 0 or n_clusters <= 0:
        raise ContractError("n_dedup and n_clusters must be > 0")
    if n_clusters > n_dedup:
        raise ContractError("n_clusters must be <= n_dedup")
    return {
        "upper95_by_cluster": upper95_zero_failure(n_clusters),
        "upper95_by_dedup": upper95_zero_failure(n_dedup),
        "n_ind_by_cluster": n_clusters,
        "n_ind_by_dedup": n_dedup,
        "cluster_note": "assumes all episodes in a cluster share the same outcome; conservative",
        "dedup_note": "assumes deduplicated episodes are independent; residual clustering not removed; narrow",
    }


def cluster_budget(target: float, alpha: float = 0.05) -> dict[str, Any]:
    """Clusters needed to rule out a failure rate above target at one-sided alpha."""
    if not (0 < target < 1):
        raise ContractError("target must be in (0, 1)")
    if not (0 < alpha < 1):
        raise ContractError("alpha must be in (0, 1)")
    needed = math.ceil(math.log(alpha) / math.log(1.0 - target))
    return {"target": target, "alpha": alpha, "clusters_needed": needed}


def rho_low_cap(n_dedup: int, n_clusters: int, rho_low: float | None) -> dict[str, Any]:
    """Upper bound using the lower end of a rho interval.

    bound = N_c / (1 + (mbar - 1) * rho_low), mbar = N_c / K. This is the
    mbar approximation, retained for the cap only. In skewed clusters the exact
    per-cluster sum at the same rho is lower, so this bound is looser/higher.
    Negative rho_low is truncated to 0. No interval means no bound.
    """
    if n_dedup <= 0 or n_clusters <= 0:
        raise ContractError("n_dedup and n_clusters must be > 0")
    if n_clusters > n_dedup:
        raise ContractError("n_clusters must be <= n_dedup")
    if rho_low is None:
        return {
            "status": "unestimable",
            "reason": "rho_low_not_available",
            "bound": None,
        }
    if not math.isfinite(rho_low) or rho_low > 1:
        raise ContractError("rho_low must be finite and <= 1")
    mean_size = n_dedup / n_clusters
    rho_used = max(0.0, float(rho_low))
    bound = n_dedup / (1.0 + (mean_size - 1.0) * rho_used)
    return {
        "status": "computed",
        "bound": bound,
        "n_dedup": n_dedup,
        "n_clusters": n_clusters,
        "mean_size_def": mean_size,
        "rho_low": rho_low,
        "rho_low_used": rho_used,
        "method": "mbar_approximation",
        "direction": "looser/higher bound; exact per-cluster sum at the same rho is lower",
    }


def variance_probe(rows: Iterable[Mapping[str, Any]], key_fields: Sequence[str]) -> dict[str, Any]:
    """Aggregate, summarize, and decide whether rho is identifiable."""
    clusters = aggregate(rows, key_fields=key_fields)
    summary = summarize_clusters(clusters)
    summary["clusters_detail"] = clusters
    return summary


def read_corpus(path: str) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Read a three-column episode CSV (optionally gzip-compressed)."""
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ["episode_id", "scene_id", "outcome"]:
            raise ContractError(
                "CSV must have exactly the columns episode_id,scene_id,outcome; "
                f"got {reader.fieldnames}"
            )
        rows = list(reader)
    missing = sum(1 for row in rows if not str(row.get("scene_id", "")).strip())
    usable = [row for row in rows if str(row.get("scene_id", "")).strip()]
    if not usable:
        raise ContractError("no rows with a non-empty scene_id")
    return usable, {"rows_input": len(rows), "rows_used": len(usable),
                    "excluded_missing_scene": missing}


def report(rows: Sequence[Mapping[str, Any]], key_fields: Sequence[str],
           rho_low: float | None = None,
           claim_scope: str = "success_rate_precision_not_training_information") -> dict[str, Any]:
    """Build a dataset-side report.

    - n_eff is computed by the exact per-cluster sum, not by mbar.
    - the rho-free interval [K, N] is always printed.
    - zero-variance share is a readout, not a veto.
    - a NEES record is not issued without a cluster-bootstrap rho interval.
    """
    clusters = aggregate(rows, key_fields=key_fields)
    summary = summarize_clusters(clusters)
    total_failures = sum(int(c["failures"]) for c in clusters)
    n_dedup = int(summary["episodes"])
    k = int(summary["clusters"])
    interval = neff_interval(clusters)

    icc = icc1(clusters)
    rho_point = icc.get("rho") if icc.get("status") == "computed" else None
    if rho_point is not None:
        eff = n_eff_diagnostics(clusters, rho_point)
        eff["claim_scope"] = claim_scope
        info_status = "point_estimate_without_interval"
    else:
        eff = {
            "status": "unestimable",
            "reason": icc.get("reason", "rho_unestimable"),
            "interval": interval,
            "claim_scope": claim_scope,
        }
        info_status = "interval_only_rho_point_unavailable"

    if total_failures == 0:
        zf = zero_failure_bounds(n_dedup, k)
        zf["status"] = "computed"
    else:
        zf = {
            "status": "not_applicable",
            "reason": "observed_failures",
            "failures": total_failures,
        }

    budgets = {
        "status": "computed" if total_failures == 0 else "reference_only",
        "targets": {
            str(t): cluster_budget(t)["clusters_needed"]
            for t in (0.10, 0.05, 0.01)
        },
        "formula": "ceil(ln(alpha) / ln(1 - target)), alpha=0.05",
        "note": (
            "zero-failure budget; with observed failures use a failure-rate interval, not this table"
            if total_failures else "applies because zero failures were observed"
        ),
    }

    cap = rho_low_cap(n_dedup, k, rho_low) if rho_low is not None else {
        "status": "unestimable",
        "reason": "rho_low_not_available",
        "bound": None,
    }

    return {
        "cluster_key": "||".join(key_fields),
        "claim_scope": claim_scope,
        "summary": summary,
        "information_status": info_status,
        "n_eff_interval": interval,
        "icc_point": icc,
        "effective_n_success_rate": eff,
        "zero_failure_bounds": zf,
        "cluster_budget": budgets,
        "rho_low_cap": cap,
        "nees_record": {
            "status": "not_issued",
            "reason": "no_cluster_bootstrap_rho_interval",
            "note": "effective N is for success-rate precision, not training information; a record waits for a bootstrap interval.",
        },
    }


def write_report(path: str, payload: Mapping[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


# Known-answer fixtures: inputs and expected values are both in this file so
# --self-test has no external dependency and no hidden expected constants.
def _fixture_rows_equal() -> list[dict[str, Any]]:
    rows = []
    for i in range(10):
        rows.append({"episode_id": f"a{i}", "scene_id": "A", "outcome": 0})
    for i in range(10):
        rows.append({"episode_id": f"b{i}", "scene_id": "B", "outcome": 1 if i < 5 else 0})
    for i in range(10):
        rows.append({"episode_id": f"c{i}", "scene_id": "C", "outcome": 1})
    return rows


def self_test() -> None:
    # 1. Aggregate and cluster accounting.
    clusters = aggregate(_fixture_rows_equal(), key_fields=("scene_id",))
    assert [c["cluster_id"] for c in clusters] == ["A", "B", "C"]
    assert [c["n"] for c in clusters] == [10, 10, 10]
    assert [c["successes"] for c in clusters] == [0, 5, 10]
    summary = summarize_clusters(clusters)
    assert summary["clusters"] == 3
    assert summary["variable_clusters"] == 1
    assert summary["constant_clusters"] == 2
    assert summary["zero_variance_share_estimable"] == 2 / 3

    # 1b. Zero-variance share is a readout, not a veto.
    zero_rows = []
    for c in range(10):
        for i in range(4):
            outcome = 1 if (c == 9 and i < 2) else 0
            zero_rows.append({
                "episode_id": f"z{c}-{i}", "scene_id": f"Z{c}", "outcome": outcome,
            })
    zclusters = aggregate(zero_rows, key_fields=("scene_id",))
    zsummary = summarize_clusters(zclusters)
    assert zsummary["zero_variance_share_estimable"] == 0.9
    assert zsummary["variable_clusters"] == 1
    assert zsummary["neff_interval_low"] == 10
    assert zsummary["neff_interval_high"] == 40
    assert "rho_identifiable" not in zsummary

    # 2. ICC(1) known answer: p = (0, .5, 1), n = 10 each.
    # MSB = 2.5, MSW = 2.5/27, m0 = 10, ICC = 13/18.
    icc = icc1(clusters)
    assert icc["status"] == "computed"
    assert abs(icc["rho"] - 13 / 18) < 1e-12
    assert abs(icc["msb"] - 2.5) < 1e-12
    assert abs(icc["msw"] - (2.5 / 27)) < 1e-12
    assert abs(icc["m0"] - 10.0) < 1e-12

    # 3. mbar deff/n_eff remains only as a comparison.
    eff = effective_n(3, 10.0, icc["rho"])
    assert abs(eff["deff"] - 7.5) < 1e-12
    assert abs(eff["n_eff"] - 4.0) < 1e-12
    assert eff["method"] == "mbar_approximation"

    # 4. Negative rho is truncated to 0, so deff = 1 and n_eff = N_c.
    eff_neg = effective_n(3, 10.0, -0.2)
    assert eff_neg["deff"] == 1.0
    assert eff_neg["n_eff"] == 30.0

    # 5. Unequal cluster sizes, both clusters at p = .5: n = (2, 4).
    # MSB = 0, MSW = .375, m0 = 8/3, ICC = -3/5 (truncated to 0 by deff).
    unequal = [
        {"cluster_id": "A", "n": 2, "successes": 1, "rate": 0.5, "zero_variance": False},
        {"cluster_id": "B", "n": 4, "successes": 2, "rate": 0.5, "zero_variance": False},
    ]
    icc_u = icc1(unequal)
    assert abs(icc_u["rho"] - (-3 / 5)) < 1e-12
    assert abs(icc_u["m0"] - 8 / 3) < 1e-12
    assert abs(icc_u["msw"] - 0.375) < 1e-12
    assert abs(design_effect(3, icc_u["rho"]) - 1.0) < 1e-12

    # 6. Zero-failure exact bound, both ends.
    bounds = zero_failure_bounds(240, 12)
    assert abs(bounds["upper95_by_cluster"] - (1 - 0.05 ** (1 / 12))) < 1e-15
    assert abs(bounds["upper95_by_dedup"] - (1 - 0.05 ** (1 / 240))) < 1e-15
    assert abs(bounds["upper95_by_cluster"] - 0.220922) < 5e-5
    assert abs(bounds["upper95_by_dedup"] - 0.012405) < 5e-5

    # 7. Cluster budget: 29 / 59 / 299.
    assert cluster_budget(0.10)["clusters_needed"] == 29
    assert cluster_budget(0.05)["clusters_needed"] == 59
    assert cluster_budget(0.01)["clusters_needed"] == 299

    # 8. rho-low cap: N_c=240, K=12, mbar=20, rho_low=.05 -> 240/1.95.
    cap = rho_low_cap(240, 12, 0.05)
    assert abs(cap["bound"] - (240 / 1.95)) < 1e-12
    assert abs(cap["mean_size_def"] - 20.0) < 1e-12
    assert rho_low_cap(240, 12, None)["status"] == "unestimable"
    assert abs(rho_low_cap(240, 12, -0.1)["bound"] - 240.0) < 1e-12

    # 9. Exact per-cluster sum for the equal fixture: [3, 30], rho=.5 -> 12.
    interval = neff_interval(clusters)
    assert interval["low"] == 3 and interval["high"] == 30
    assert neff_at_rho(clusters, 0)["n_eff"] == 30
    assert neff_at_rho(clusters, 1)["n_eff"] == 3
    assert abs(neff_at_rho(clusters, 0.5)["n_eff"] - 30 / 5.5) < 1e-12
    diag = n_eff_diagnostics(clusters, 0.5)
    assert abs(diag["n_eff"] - 30 / 5.5) < 1e-12
    assert diag["mbar_n_eff"] == diag["n_eff"]  # equal clusters, no skew

    # 10. Extreme skew: one 100-episode cluster plus 50 singletons.
    skew_rows = [
        {"episode_id": f"big{i}", "scene_id": "BIG", "outcome": 1 if i < 50 else 0}
        for i in range(100)
    ] + [
        {"episode_id": f"single{i}", "scene_id": f"S{i}", "outcome": 1}
        for i in range(50)
    ]
    skew_clusters = aggregate(skew_rows, key_fields=("scene_id",))
    skew_summary = summarize_clusters(skew_clusters)
    assert skew_summary["clusters"] == 51
    assert skew_summary["episodes"] == 150
    assert skew_summary["singleton_episodes"] == 50
    assert skew_summary["variable_clusters"] == 1
    assert skew_summary["neff_interval_low"] == 51
    assert skew_summary["neff_interval_high"] == 150
    skew_diag = n_eff_diagnostics(skew_clusters, 0.5)
    assert abs(skew_diag["n_eff"] - (50 + 100 / 50.5)) < 1e-12
    assert skew_diag["mbar_n_eff"] > skew_diag["n_eff"]
    assert icc1(skew_clusters)["status"] == "unestimable"

    # 11. All singletons: rho is not estimable, n_eff is exactly N for any rho.
    single_rows = [
        {"episode_id": f"s{i}", "scene_id": f"S{i}", "outcome": i % 2}
        for i in range(7)
    ]
    single_clusters = aggregate(single_rows, key_fields=("scene_id",))
    single_summary = summarize_clusters(single_clusters)
    assert single_summary["clusters"] == 7 and single_summary["episodes"] == 7
    assert single_summary["multi_clusters"] == 0
    assert single_summary["neff_interval_low"] == 7
    assert single_summary["neff_interval_high"] == 7
    assert neff_at_rho(single_clusters, 0.5)["n_eff"] == 7
    assert icc1(single_clusters)["status"] == "unestimable"

    # 12. Contract errors are errors, not silent cleanup.
    for bad in [
        lambda: aggregate([{"episode_id": "x", "scene_id": "A", "outcome": 2}]),
        lambda: aggregate([
            {"episode_id": "x", "scene_id": "A", "outcome": 1},
            {"episode_id": "x", "scene_id": "A", "outcome": 0},
        ]),
        lambda: zero_failure_bounds(10, 11),
        lambda: cluster_budget(0.0),
    ]:
        try:
            bad()
        except ContractError:
            pass
        else:
            raise AssertionError("contract violation was accepted")

    print("dataset_driver self-test: 12 groups passed")


def run_fixture(path: str) -> None:
    """Run an external known-answer fixture.

    Expected values are stored in the fixture, not recomputed from the code
    under test. This catches a formula change that silently changes an answer.
    """
    with open(path, encoding="utf-8") as f:
        fixture = json.load(f)
    rows = fixture["episodes"]
    expected = fixture["expected"]

    clusters = aggregate(rows, key_fields=("scene_id",))
    agg = expected["aggregate"]
    assert [c["cluster_id"] for c in clusters] == agg["cluster_ids"]
    assert [c["n"] for c in clusters] == agg["n"]
    assert [c["successes"] for c in clusters] == agg["successes"]
    for got, want in zip([c["rate"] for c in clusters], agg["rate"]):
        assert abs(got - want) < 1e-12

    summary = summarize_clusters(clusters)
    for key, want in agg["summary"].items():
        got = summary[key]
        if isinstance(want, float):
            assert abs(got - want) < 1e-12, (key, got, want)
        else:
            assert got == want, (key, got, want)

    icc = icc1(clusters)
    for key, want in expected["icc1"].items():
        assert abs(icc[key] - want) < 1e-12, (key, icc[key], want)

    eff = effective_n(3, 10.0, icc["rho"])
    for key, want in expected["effective_n"].items():
        assert abs(eff[key] - want) < 1e-12, (key, eff[key], want)

    ue = expected["unequal"]
    icc_u = icc1(ue["clusters"])
    for key, want in ue["expected"].items():
        if key == "deff_at_mbar3":
            got = design_effect(3, icc_u["rho"])
        else:
            got = icc_u[key]
        assert abs(got - want) < 1e-12, (key, got, want)

    zf = expected["zero_failure"]
    bounds = zero_failure_bounds(zf["n_dedup"], zf["n_clusters"])
    assert abs(bounds["upper95_by_cluster"] - zf["upper95_by_cluster"]) < 1e-12
    assert abs(bounds["upper95_by_dedup"] - zf["upper95_by_dedup"]) < 1e-12

    ne = expected["neff_exact"]
    assert neff_at_rho(clusters, 0)["n_eff"] == ne["at_rho_0"]
    assert neff_at_rho(clusters, 1)["n_eff"] == ne["at_rho_1"]
    assert abs(neff_at_rho(clusters, 0.5)["n_eff"] - ne["at_rho_0_5"]) < 1e-12
    interval = neff_interval(clusters)
    assert interval["low"] == ne["interval_low"]
    assert interval["high"] == ne["interval_high"]
    assert interval["width"] == ne["interval_width"]
    assert interval["singleton_contribution"] == ne["singleton_contribution"]

    skew = expected["extreme_skew"]
    skew_clusters = aggregate(skew["episodes"], key_fields=("scene_id",))
    skew_summary = summarize_clusters(skew_clusters)
    for key, want in skew["summary"].items():
        got = skew_summary[key]
        if isinstance(want, float):
            assert abs(got - want) < 1e-12, (key, got, want)
        else:
            assert got == want, (key, got, want)
    skew_diag = n_eff_diagnostics(skew_clusters, 0.5)
    assert abs(skew_diag["n_eff"] - skew["n_eff_at_rho_0_5"]) < 1e-12
    assert abs(skew_diag["mbar_n_eff"] - skew["mbar_at_rho_0_5"]) < 1e-12
    assert abs(skew_diag["mbar_overstatement"] - skew["mbar_overstatement"]) < 1e-12
    assert icc1(skew_clusters)["status"] == skew["icc_status"]

    single = expected["all_singleton"]
    single_clusters = aggregate(single["episodes"], key_fields=("scene_id",))
    single_summary = summarize_clusters(single_clusters)
    for key, want in single["summary"].items():
        got = single_summary[key]
        if isinstance(want, float):
            assert abs(got - want) < 1e-12, (key, got, want)
        else:
            assert got == want, (key, got, want)
    assert neff_at_rho(single_clusters, 0.5)["n_eff"] == single["n_eff_at_rho_0_5"]
    assert icc1(single_clusters)["status"] == single["icc_status"]

    cb = expected["cluster_budget"]
    got = [cluster_budget(t)["clusters_needed"] for t in cb["targets"]]
    assert got == cb["clusters_needed"], (got, cb["clusters_needed"])

    cap_e = expected["rho_low_cap"]
    cap = rho_low_cap(cap_e["n_dedup"], cap_e["n_clusters"], cap_e["rho_low"])
    assert abs(cap["bound"] - cap_e["bound"]) < 1e-12
    assert abs(cap["mean_size_def"] - cap_e["mean_size_def"]) < 1e-12

    print(f"dataset_driver fixture: {os.path.basename(path)} passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--fixture", default=os.path.join(
        ROOT, "tests", "fixtures", "dataset-driver-known-answers.json"))
    parser.add_argument("--input", help="CSV with episode_id,scene_id,outcome")
    parser.add_argument("--out")
    parser.add_argument("--label", default="")
    parser.add_argument("--rho-low", type=float, default=None)
    parser.add_argument("--source-rows", type=int, default=None)
    parser.add_argument("--cannot-cluster", type=int, default=None)
    parser.add_argument("--claim-scope", default="success_rate_precision_not_training_information")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        run_fixture(args.fixture)
        return 0
    if args.input:
        if not args.out:
            parser.error("--out is required with --input")
        rows, counts = read_corpus(args.input)
        source_rows = args.source_rows if args.source_rows is not None else counts["rows_input"]
        cannot_cluster = (
            args.cannot_cluster if args.cannot_cluster is not None
            else counts["excluded_missing_scene"]
        )
        if cannot_cluster < 0 or source_rows < counts["rows_used"] + cannot_cluster:
            raise ContractError("source_rows, cannot_cluster, and usable rows do not add up")
        payload = {
            "label": args.label,
            "input": os.path.basename(args.input),
            **counts,
            "source_rows": source_rows,
            "cannot_cluster": cannot_cluster,
            "unclusterable_share": cannot_cluster / source_rows if source_rows else None,
            **report(rows, key_fields=("scene_id",), rho_low=args.rho_low,
                     claim_scope=args.claim_scope),
        }
        write_report(args.out, payload)
        print(json.dumps({
            "clusters": payload["summary"]["clusters"],
            "episodes": payload["summary"]["episodes"],
            "variable_clusters": payload["summary"]["variable_clusters"],
            "zero_variance_share_estimable": payload["summary"]["zero_variance_share_estimable"],
            "n_eff_interval": payload["n_eff_interval"],
            "effective_n_success_rate": payload["effective_n_success_rate"],
            "rho_low_cap": payload["rho_low_cap"],
        }, ensure_ascii=False, indent=2))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
