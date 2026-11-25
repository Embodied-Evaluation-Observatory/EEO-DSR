#!/usr/bin/env python3
"""Validate an EEO-DSR record, and optionally a clock observation.

Usage:
    python3 tools/validate_record.py <record.json> [...]
    python3 tools/validate_record.py --sync <observation.json> [...]
    python3 tools/validate_record.py --self-test

Exit codes: 0 valid (or self-test passed), 1 invalid (or self-test failed), 2 usage error.

The normative forms are schema/record.schema.json (eeo-dataset-review/0.5) and
schema/sync-observation.schema.json (eeo-sync-observation/0.1). This validator re-implements
them with no third-party dependency and adds the cross-field rules that carry the method:

  * thresholds -- tau, m and W -- are declared by a party, never set by EEO; the dedup metric is
    not a threshold but a method constant fixed here; each declared value must appear in its own
    sweep, and the sync sweep must show m=2, m=3 and the declared m;
  * sync is measured by EEO's own clock model: no external timing tool is cited as the source,
    and a record may claim verified sync only after a five-class fault-injection fixture passed;
  * a structurally broken time axis is a fact, and alignment is not executed in this version: the
    consequence depends on what can be established -- an excluded segment with a known extent
    leaves the rest computable, unknown extent makes NEES unestimable, an undocumented reset is
    carried as unverified and capped;
  * the pool is pass + unverified; degraded is never counted;
  * the four-step chain must close, and each step must show what it removed and why;
  * an unestimable NEES must not print a point value; its diagnostics are separate readings with
    their own bases, not parts of NEES, and the dedup count survives even when the clock does not;
  * a cap is a true upper bound: rho is taken at the low end of its interval, on the printed
    formula, with the cluster-mean definition written down;
  * a zero-failure bound uses the closed form 1 - 0.05^(1/n_ind), not 3/n;
  * EEO does not clean: dedup is an estimate, and the cross-split overlap is a separate finding;
  * a sample-tier record must not speak about the corpus it did not sample.
"""

import copy
import math
import json
import os
import sys

SCHEMA_VERSION = "eeo-dataset-review/0.5"
OBS_VERSION = "eeo-sync-observation/0.1"
METHOD_VERSION = "EEO-DSR-V0.5"

UL_VERSION = "EEO-DUL-2"
UL_EN = ("This review reports a statistical-usability reading at the episode level. It does not "
         "speak to task-difficulty match, label correctness, asset valuation, or a purchase "
         "recommendation.")
UL_ZH = ("本核验只给出该数据集在 episode 层面的统计可用性读数，不说明任务难度匹配、不说明标注正确性、"
         "不构成资产估值、不构成采购建议。")

RN_VERSION = "EEO-RN-3"
RN_EN = ("No standard is cited as a basis for this record. The dimension split of YD/T 6771-2026 "
         "informed the thinking behind this module's own five dimensions; those dimensions are "
         "defined independently and form no mapping to it. Its clauses and thresholds are not "
         "cited, and nothing here asserts conformity with it or with any other standard.")
RN_ZH = ("本记录不以任何标准为判定依据。YD/T 6771—2026 的维度划分仅作为思路参考；"
         "本模块的五个维度独立定义，与该标准不构成对照关系。不引其条款与阈值，"
         "也不声明与该标准或任何其他标准相符。")

SCOPE_ZH = "本核验只核验记录时间线自洽，不认定采集时物理同步。"
SCOPE_EN = ("This review checks that the recorded timeline is self-consistent; it does not certify "
            "that the sensors were physically synchronised at capture.")

TRAJ_NOTE = "轨迹分散度不是 NEES 的替代读数：NEES 说独立证据有多少，它说这些证据的形状有多分散。"

STAGES = ("screen", "pre_purchase", "deep")
TIERS = ("T1_sample", "T2_full")
DIMS = ("DSR-D1", "DSR-D2", "DSR-D3", "DSR-D4", "DSR-D5a", "DSR-D5b")
DIM_STATUS = ("checked", "partial", "not_checkable")
DIM_REASONS = (
    "card_has_no_breakdown", "unit_conversion_absent", "licence_not_machine_readable",
    "no_recorded_clock", "clock_features_unusable", "alignment_unresolved", "split_undeclared",
    "frame_wise_split", "no_task_labels", "no_cluster_ids", "revision_unpinned",
)
SPLITS = ("workstation-object", "scene", "environment", "not declared", "frame-wise")
AXES = ("workstation-object", "scene", "environment")
LEVELS = ("workstation_object", "scene", "environment", "task", "other")
NEES_STATUS = ("computable", "interval", "upper_bound", "unestimable_zero_variance",
               "unestimable_alignment", "unestimable_other")
NEES_REASONS = {
    "unestimable_zero_variance": ("zero_variance_dominance",),
    "unestimable_alignment": ("reset_points_unlocatable",),
    "unestimable_other": ("split_not_declared", "frame_wise_split", "cluster_ids_absent",
                          "insufficient_clusters"),
}
RHO_STATUS = ("measured", "assumed", "not_measured")
RHO_EST = ("outcome_icc", "feature_dispersion")
RHO_BASIS = ("borrowed_from", "sensitivity_range", "measured_here", "not_measured")
DECLARERS = ("buyer", "supplier", "joint")
M_ORIGINS = ("buyer", "supplier", "joint", "eeo_default")
N_IND_BASIS = ("cluster_count", "dedup_count")
CHAIN_STEPS = ("raw", "sync", "dedup", "nees")
CAP_BASES = ("sample_scope", "sync_unverified", "struct_unverified")
RHO_SOURCES = ("interval_low", "sensitivity_range_low")
SYNC_REASONS = ("no_recorded_clock", "clock_features_unusable", "struct_undocumented")
ALIGN_OUTCOMES = ("not_required", "segment_excluded", "extent_unknown", "segment_unverified")
CLOCK_FEATURES = ("offset", "drift", "jitter", "gap", "reset")
FIXTURE_CLASSES = ("late_packet", "missing_frame", "clock_drift", "clock_reset", "non_monotonic")
FATAL_VIOLATIONS = ("clock_reset", "non_monotonic")
VIOLATIONS = ("late_packet", "missing_frame", "clock_drift", "clock_reset",
              "duplicate_timestamp", "non_monotonic", "stall", "out_of_order")
OBS_VERDICTS = ("pass", "degraded", "fail", "alignment_excluded", "alignment_unlocatable",
                "unverified")
DEDUP_METRIC_ID = "eeo-dedup-metric/episode-embedding-cosine-v1"
TOP_LEVEL = (
    "schema_version", "module", "dataset", "review", "dimensions", "thresholds", "neev",
    "split", "buyer_summary", "buyer_summary_use_limitation", "submitter", "objections",
    "use_limitation", "reference_note", "scope_declaration",
)


def is_sha(v):
    return isinstance(v, str) and len(v) == 64 and all(c in "0123456789abcdef" for c in v)


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _log_binom_cdf(k, n, p):
    """log P(X <= k) for X ~ Bin(n, p), stable for large n."""
    import math
    if p <= 0:
        return 0.0
    if p >= 1:
        return float("-inf") if k < n else 0.0
    terms = []
    for i in range(0, k + 1):
        lg = (math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
              + i * math.log(p) + (n - i) * math.log1p(-p))
        terms.append(lg)
    mx = max(terms)
    return mx + math.log(sum(math.exp(t - mx) for t in terms))


def upper95(failures, n, alpha=0.05):
    """Exact one-sided upper confidence bound on the failure rate."""
    if n <= 0:
        return None
    if failures == 0:
        return 1 - alpha ** (1 / n)
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if _log_binom_cdf(failures, n, mid) > math.log(alpha):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def check(rec):
    """Return a list of error strings for a record; empty means valid."""
    errs = []

    def need(cond, msg):
        if not cond:
            errs.append(msg)

    if not isinstance(rec, dict):
        return ["record is not an object"]

    for k in TOP_LEVEL:
        if k not in rec and k != "objections":
            errs.append(f"missing top-level field: {k}")
    extra = set(rec) - set(TOP_LEVEL)
    if extra:
        errs.append(f"unknown top-level fields: {sorted(extra)}")

    need(rec.get("schema_version") == SCHEMA_VERSION,
         f"schema_version must be {SCHEMA_VERSION}")
    need(rec.get("module") == "EEO-DSR", "module must be 'EEO-DSR'")

    ds = rec.get("dataset") or {}
    for k in ("dataset_id", "version", "licence", "card_url", "retrieval_date"):
        need(isinstance(ds.get(k), str) and ds.get(k), f"dataset.{k} is required")
    for k in ("card_sha256", "manifest_sha256"):
        need(is_sha(ds.get(k)), f"dataset.{k} must be a 64-hex digest")

    rv = rec.get("review") or {}
    need(rv.get("stage") in STAGES, f"review.stage must be one of {STAGES}")
    tier = rv.get("tier")
    need(tier in TIERS, f"review.tier must be one of {TIERS}")
    need(rv.get("method_version") == METHOD_VERSION,
         f"review.method_version must be {METHOD_VERSION}")
    need(isinstance(rv.get("frame"), str) and rv.get("frame"),
         "review.frame must state how the frame was drawn")
    if tier == "T1_sample":
        need(isinstance(rv.get("scope_statement"), str) and rv.get("scope_statement"),
             "T1_sample requires review.scope_statement: what was sampled and what was not")
    if rv.get("frame") == "supplier_provided":
        need(isinstance(rv.get("supplier_provided_cap"), str) and rv.get("supplier_provided_cap"),
             "supplier-provided frame requires review.supplier_provided_cap")

    dims = rec.get("dimensions")
    need(isinstance(dims, list) and len(dims) == 6, "dimensions must carry six items")
    if isinstance(dims, list):
        got = [d.get("id") for d in dims if isinstance(d, dict)]
        need(got == list(DIMS), f"dimensions must be ordered {list(DIMS)}, got {got}")
        for d in dims:
            if not isinstance(d, dict):
                errs.append("each dimension must be an object")
                continue
            need(d.get("status") in DIM_STATUS,
                 f"{d.get('id')}: status must be one of {DIM_STATUS}")
            need(isinstance(d.get("readout"), str) and d.get("readout"),
                 f"{d.get('id')}: readout is required")
            if d.get("status") == "not_checkable":
                need(d.get("reason_code") in DIM_REASONS,
                     f"{d.get('id')}: not_checkable requires a reason_code from {DIM_REASONS}")

    th = rec.get("thresholds") or {}
    need(th.get("thresholds_origin") in ("buyer_declared", "eeo_default_package"),
         "thresholds.thresholds_origin must say buyer_declared or eeo_default_package")
    need(th.get("eeo_sets_thresholds") is False,
         "thresholds.eeo_sets_thresholds must be false: tau, m and W are declared, not set")

    if th.get("thresholds_origin") == "eeo_default_package":
        ts0 = th.get("sync") or {}
        need(ts0.get("m") == 3,
             "the EEO default package fixes m=3; a buyer who wants other values must declare them "
             "as buyer_declared")
        need((th.get("dedup") or {}).get("w") == 0.95,
             "the EEO default package fixes W=0.95; other values must be buyer_declared")
        need(th.get("acceptance_use") == "not_declared_by_buyer",
             "a default-package record must state acceptance_use not_declared_by_buyer: it may "
             "inform, not decide an acceptance")
        policy = (ts0.get("pairing_policy") or "")
        need(policy in ("nearest_neighbor", "zero_order_hold"),
             "the default package needs a declared pairing policy: without it the tau coefficient "
             "cannot be derived")
        notice = th.get("default_package_notice") or {}
        need(isinstance(notice, dict) and "未获买方声明" in (notice.get("zh") or "")
             and "不得作为验收判定依据" in (notice.get("zh") or "")
             and "自行声明阈值后重跑" in (notice.get("zh") or ""),
             "the default package must print that no buyer declaration was obtained, that it may "
             "not serve as an acceptance finding, and that the accepting party must declare "
             "thresholds and rerun")
        hl = ts0.get("sensitivity_headline")
        need(isinstance(hl, str) and "从" in hl and "到" in hl,
             "a default-package record must print the sensitivity movement in the summary, e.g. "
             "'between the two tau bands the pass count moves from A to B'")

    ded_th = th.get("dedup") or {}
    if not isinstance(ded_th, dict):
        errs.append("thresholds.dedup must be an object")
        ded_th = {}
    if "metric" in ded_th:
        errs.append("thresholds.dedup.metric is not accepted: the metric is fixed by EEO in the "
                    "method (neev.dedup.metric), only W is declared")
    w = ded_th.get("w")
    need(is_num(w) and 0 < w <= 1, "thresholds.dedup.w must be in (0, 1]")
    need(ded_th.get("declared_by") in DECLARERS,
         f"thresholds.dedup.declared_by must be one of {DECLARERS}")
    need(isinstance(ded_th.get("basis"), str) and ded_th.get("basis"),
         "thresholds.dedup.basis must state who declared W and on what document")
    dsw = ded_th.get("sensitivity") or []
    if not isinstance(dsw, list) or len(dsw) < 2:
        errs.append("thresholds.dedup.sensitivity must carry at least two w values")
    else:
        ws = [e.get("w") for e in dsw if isinstance(e, dict)]
        need(len(set(ws)) == len(ws), "dedup sensitivity w values must be distinct")
        if is_num(w):
            need(w in ws, f"the declared w {w} must appear in its own sensitivity sweep")
        for e in dsw:
            need(is_num(e.get("w")) and 0 < e.get("w") <= 1,
                 "each dedup sensitivity entry needs w in (0, 1]")
            need(is_int(e.get("n_duplicate_copies")) and e.get("n_duplicate_copies") >= 0,
                 "each dedup sensitivity entry needs a non-negative integer n_duplicate_copies")

    ne = rec.get("neev") or {}
    if not isinstance(ne, dict):
        errs.append("neev must be an object")
        ne = {}
    nd = ne.get("n_declared")
    need(is_int(nd) and nd >= 1, "neev.n_declared must be a positive integer")

    sy = ne.get("sync") or {}
    if not isinstance(sy, dict):
        errs.append("neev.sync must be an object")
        sy = {}
    sstat = sy.get("status")
    need(sstat in ("verified", "unverified"), "neev.sync.status must be verified or unverified")
    csn = sy.get("scope_note") or {}
    need(isinstance(csn, dict) and csn.get("zh") == SCOPE_ZH and csn.get("en") == SCOPE_EN,
         "neev.sync.scope_note must carry the canonical sentence: the timeline is checked, "
         "physical synchronisation at capture is not certified")
    if "tool" in sy:
        need(False, "neev.sync.tool is not accepted: EEO runs its own clock model and does not cite "
                    "an external timing tool as the source")
    clk = sy.get("clock_model")
    need(isinstance(clk, dict),
         "neev.sync.clock_model is required: sync is measured by EEO's own clock model")
    if isinstance(clk, dict):
        need(clk.get("model_id") == "eeo-clock",
             "neev.sync.clock_model.model_id must be 'eeo-clock'")
        need(isinstance(clk.get("version"), str) and clk.get("version"),
             "neev.sync.clock_model.version is required")
        need(clk.get("self_implemented") is True,
             "neev.sync.clock_model.self_implemented must be true: the model runs inside EEO")
        need(clk.get("external_dependency") is False,
             "neev.sync.clock_model.external_dependency must be false: the module takes no external "
             "timing dependency")
        feats = clk.get("features")
        need(isinstance(feats, list) and len(feats) >= 3 and all(f in CLOCK_FEATURES for f in feats),
             f"neev.sync.clock_model.features must list at least three of {CLOCK_FEATURES}")

    counts = ("n_pass", "n_degraded", "n_fail", "n_alignment_excluded",
              "n_alignment_unlocatable", "n_unverified")
    cv = [sy.get(k) for k in counts]
    for name, v in zip(counts, cv):
        need(is_int(v) and v >= 0, f"neev.sync.{name} must be a non-negative integer")
    need(sy.get("degraded_policy") == "excluded_from_nees",
         "neev.sync.degraded_policy must be 'excluded_from_nees': degraded episodes stay in the "
         "corpus with zero weight and never enter NEES")
    if "degraded_ratio" in sy:
        need(False, "a weighted degraded ratio is not accepted: degraded is binary (zero weight), "
                    "so the count is reported and no ratio is computed")

    al = sy.get("alignment") or {}
    if not isinstance(al, dict):
        errs.append("neev.sync.alignment must be an object")
        al = {}
    need(al.get("executed") is False,
         "alignment is not executed in this version: sync.alignment.executed must be false, and "
         "the corpus is not re-timed")
    out = al.get("outcome")
    need(out in ALIGN_OUTCOMES, f"neev.sync.alignment.outcome must be one of {ALIGN_OUTCOMES}")
    ex, unl = sy.get("n_alignment_excluded"), sy.get("n_alignment_unlocatable")
    if out == "not_required":
        need(ex == 0 and unl == 0, "alignment not_required cannot leave episodes with a structural "
                                   "fault")
    if out == "segment_excluded":
        need(is_int(ex) and ex >= 1, "segment_excluded requires at least one excluded episode")
        need(unl == 0, "segment_excluded cannot leave an episode of unknown extent: that is "
                       "extent_unknown")
        need(isinstance(al.get("basis"), str) and al.get("basis"),
             "segment_excluded requires alignment.basis: what established the extent of the "
             "affected segment")
        need(is_int(al.get("affected_episodes")) and al.get("affected_episodes") == ex,
             "segment_excluded requires alignment.affected_episodes to equal n_alignment_excluded")
    if out == "extent_unknown":
        need(is_int(unl) and unl >= 1, "extent_unknown requires at least one episode whose extent "
                                       "cannot be established")
        need(al.get("reason_code") == "reset_points_unlocatable",
             "extent_unknown requires alignment.reason_code reset_points_unlocatable")
    if out == "segment_unverified":
        need(is_int(sy.get("n_unverified")) and sy.get("n_unverified") >= 1,
             "segment_unverified requires at least one unverified episode")

    sf = sy.get("structural_fault")
    need(isinstance(sf, dict),
         "neev.sync.structural_fault is required: structural faults are recorded by type, not as "
         "one class")
    if isinstance(sf, dict):
        ftype = sf.get("type")
        rb = sf.get("range_basis")
        aff = sf.get("affected_episodes")
        nev = sf.get("n_events")
        need(ftype in ("none", "clock_reset", "non_monotonic_spike", "other"),
             "structural_fault.type must be none, clock_reset, non_monotonic_spike or other")
        need(is_int(nev) and nev >= 0,
             "structural_fault.n_events must count the abnormal timestamps, separately from the "
             "episodes they affect: one event can affect 0, 1 or 2 episodes")
        need(rb in ("none", "segment_from_reset_point", "spike_containing_episodes",
                    "spike_crossing_no_internal_break", "unlocatable"),
             "structural_fault.range_basis must say how the affected range was established")
        if ftype == "none":
            need(rb == "none" and nev == 0, "no structural fault means no events and range_basis none")
            need(aff == 0 and out == "not_required" and ex == 0 and unl == 0,
                 "no structural fault means affected_episodes 0, outcome not_required and both "
                 "structural counts 0")
        if ftype in ("clock_reset", "non_monotonic_spike"):
            need(is_int(nev) and nev >= 1, f"{ftype} requires at least one abnormal timestamp")
            need(sstat != "unverified",
                 "a measured structural fault cannot be carried as unverified: it is an identified "
                 "defect, routed by whether its extent can be established")
        if ftype == "clock_reset":
            need(rb in ("segment_from_reset_point", "unlocatable"),
                 "a clock reset shifts the whole segment after the reset point: range_basis must be "
                 "segment_from_reset_point or unlocatable")
        if ftype == "non_monotonic_spike":
            need(rb in ("spike_containing_episodes", "spike_crossing_no_internal_break"),
                 "a non-monotonic spike is not a segment fault: range_basis must be "
                 "spike_containing_episodes, or spike_crossing_no_internal_break when the "
                 "abnormal pair crosses an episode boundary")
            need(is_int(aff) and aff in (0, 1, 2),
                 "a spike can affect 0, 1 or 2 episodes: 0 when the abnormal pair crosses a "
                 "boundary with both sides internally monotone, 1 when it lands inside an episode, "
                 "2 when the abnormal timestamp was used to cut the boundary")
            if is_int(nev) and is_int(aff):
                need(aff <= 2 * nev,
                     "affected_episodes cannot exceed twice the number of abnormal timestamps")
            if aff == 0:
                need(rb == "spike_crossing_no_internal_break"
                     and sf.get("stream_continuity_finding") is True,
                     "a spike that breaks no internal pairing excludes nothing: range_basis "
                     "spike_crossing_no_internal_break and stream_continuity_finding true")
                need(out == "not_required" and ex == 0 and unl == 0,
                     "a spike with no affected episode leaves no structural exclusion")
            else:
                need(rb == "spike_containing_episodes" and out == "segment_excluded"
                     and is_int(ex) and ex == aff,
                     "affected spike episodes leave the pool: outcome segment_excluded and "
                     "n_alignment_excluded equal to affected_episodes")
        if rb == "unlocatable":
            need(out == "extent_unknown" and is_int(unl) and unl >= 1 and aff is None,
                 "unlocatable range makes the extent unknown: outcome extent_unknown, at least one "
                 "unlocatable episode, and affected_episodes null rather than a guess")
        if rb == "segment_from_reset_point":
            need(out == "segment_excluded" and is_int(ex) and ex >= 1 and aff == ex,
                 "an excluded segment requires outcome segment_excluded and affected_episodes equal "
                 "to n_alignment_excluded")

    scf = sy.get("stream_continuity_findings")
    need(isinstance(scf, dict),
         "neev.sync.stream_continuity_findings is required: a spike that breaks no internal "
         "pairing leaves a trace, not just a zero")
    if isinstance(scf, dict):
        cnt = scf.get("count")
        need(is_int(cnt) and cnt >= 0,
             "stream_continuity_findings.count must be a non-negative integer")
        bnd = scf.get("boundaries")
        if is_int(cnt) and cnt == 0:
            need(bnd is None, "with no continuity finding, boundaries must be null")
        if is_int(cnt) and cnt > 0:
            need(isinstance(bnd, list) and len(bnd) == cnt,
                 "stream_continuity_findings.boundaries must list one entry per finding, so a third "
                 "party can recheck the boundary")
            if isinstance(bnd, list):
                for b in bnd:
                    need(isinstance(b, dict)
                         and isinstance(b.get("left_episode_id"), str)
                         and isinstance(b.get("right_episode_id"), str),
                         "each continuity boundary needs left_episode_id and right_episode_id")
        need(isinstance(scf.get("basis"), str) and scf.get("basis"),
             "stream_continuity_findings.basis must say how the pairing was judged")
        need("不进 NEES" in (scf.get("note") or ""),
             "stream_continuity_findings.note must say it does not enter NEES or any dimension "
             "reading")
        if isinstance(sf, dict) and sf.get("range_basis") == "spike_crossing_no_internal_break":
            need(is_int(cnt) and cnt >= 1,
                 "a spike crossing a boundary with no internal break requires at least one "
                 "continuity finding")

    ar = al.get("rule")
    need(isinstance(ar, dict),
         "neev.sync.alignment.rule is required: where the rule lives, whether it changed, and "
         "whether it belongs to a recomputable class are three different facts")
    if isinstance(ar, dict):
        rt = ar.get("rule_type")
        need(rt in ("none", "reset_to_zero", "custom_documented"),
             "alignment.rule.rule_type must be none, reset_to_zero or custom_documented")
        src, rh, app = ar.get("source"), ar.get("rule_hash"), ar.get("applicable")
        if rt == "none":
            need(src is None and rh is None and app is False,
                 "rule_type none means no rule: source and rule_hash must be null and applicable "
                 "false")
        if rt == "reset_to_zero":
            need(src is None and rh is None and app is True,
                 "reset_to_zero is the method's built-in rule: no source or hash, applicable true")
            need(isinstance(ar.get("reset_point_episode_id"), str)
                 and ar.get("reset_point_episode_id"),
                 "reset_to_zero requires the reset point episode id")
            need(isinstance(ar.get("reset_point_timestamp"), str)
                 and ar.get("reset_point_timestamp"),
                 "reset_to_zero requires the reset point timestamp")
        if rt == "custom_documented":
            need(isinstance(src, str) and src,
                 "custom_documented requires source: the card field path or document reference")
            need(is_sha(rh), "custom_documented requires rule_hash: the sha256 of the rule text")
            need(app is True,
                 "custom_documented requires applicable true: a rule marked inapplicable cannot "
                 "support recomputation")

    if sstat == "verified":
        need(sy.get("n_unverified") == 0, "verified sync cannot leave episodes unverified")
        need(is_sha(clk.get("observation_sha256")) if isinstance(clk, dict) else False,
             "verified sync requires clock_model.observation_sha256: the counts must trace to the "
             "observation they were taken from")
        if isinstance(clk, dict):
            sc = clk.get("self_check")
            need(isinstance(sc, dict),
                 "verified sync requires clock_model.self_check: known-ground-truth injection must "
                 "have passed before sync can be called verified")
            if isinstance(sc, dict):
                need(is_int(sc.get("n_cases")) and sc.get("n_cases") >= 8,
                     "clock_model.self_check.n_cases must be at least 8 injected cases")
                need(sc.get("n_passed") == sc.get("n_cases"),
                     "clock_model.self_check must have passed every injected case")
                need(isinstance(sc.get("fixture_id"), str) and sc.get("fixture_id"),
                     "clock_model.self_check.fixture_id is required")
                need(isinstance(sc.get("runner"), str) and sc.get("runner"),
                     "clock_model.self_check.runner is required: the fixture is an executable "
                     "driver under tools/, not a written note")
                cov = sc.get("coverage")
                need(isinstance(cov, list) and len(set(cov)) == len(cov)
                     and all(c in FIXTURE_CLASSES for c in cov),
                     f"clock_model.self_check.coverage must use only {FIXTURE_CLASSES}")
                need(isinstance(cov, list) and set(FIXTURE_CLASSES) <= set(cov),
                     "clock_model.self_check.coverage must cover all five injected fault classes: "
                     "late packets, missing frames, drift, reset and non-monotonic")
                need(isinstance(sc.get("run_date"), str),
                     "clock_model.self_check.run_date is required")
        ts = th.get("sync")
        need(isinstance(ts, dict),
             "verified sync requires thresholds.sync (tau and m are not EEO's to set)")
        if isinstance(ts, dict):
            tau = ts.get("tau_ms")
            m = ts.get("m")
            need(is_num(tau) and tau > 0, "thresholds.sync.tau_ms must be a positive number")
            need(is_num(m) and m > 1, "thresholds.sync.m must be greater than 1")
            need(ts.get("declared_by") in DECLARERS,
                 f"thresholds.sync.declared_by must be one of {DECLARERS}")
            need(ts.get("m_origin") in M_ORIGINS,
                 f"thresholds.sync.m_origin must be one of {M_ORIGINS}")
            need(ts.get("m_origin") != "eeo_default" or (is_num(m) and abs(m - 3) < 1e-9),
                 "m_origin 'eeo_default' means m is EEO's default of 3 and says so; a different "
                 "m must be attributed to a party")
            need(isinstance(ts.get("basis"), str) and ts.get("basis"),
                 "thresholds.sync.basis must state who declared tau and m, and on what document")
            rule = ts.get("tau_rule")
            policy = ts.get("pairing_policy")
            factor = ts.get("tau_factor")
            pb = ts.get("period_basis")
            need(rule in ("derived_from_pairing_policy", "declared_convention"),
                 "thresholds.sync.tau_rule must be derived_from_pairing_policy or "
                 "declared_convention")
            need(policy in ("nearest_neighbor", "zero_order_hold", "unknown"),
                 "thresholds.sync.pairing_policy must say how samples are paired")
            expected_factor = {"nearest_neighbor": 0.5, "zero_order_hold": 1.0}.get(policy)
            if expected_factor is not None:
                need(rule == "derived_from_pairing_policy",
                     f"pairing policy {policy} derives tau, it does not pick a constant")
                need(is_num(factor) and abs(factor - expected_factor) < 1e-9,
                     f"pairing policy {policy} implies tau_factor {expected_factor}: a nearest "
                     f"neighbour can be at most half a period away, a zero-order hold at most a "
                     f"full period")
            else:
                need(rule == "declared_convention",
                     "an unknown pairing policy cannot derive tau: the record falls back to an "
                     "explicit convention")
                need(isinstance(ts.get("tau_convention_note"), str)
                     and ts.get("tau_convention_note"),
                     "an unknown pairing policy requires tau_convention_note: what convention was "
                     "used and why it is an explicit choice")
                need(is_num(factor) and factor > 0,
                     "a declared convention still needs tau_factor")
            need(pb in ("sampled_stream", "shortest_stream"),
                 "thresholds.sync.period_basis must be sampled_stream (the stream being sampled "
                 "sets the period) or shortest_stream (the strict end, used when the pairing "
                 "direction is unknown)")
            direction = ts.get("pairing_direction")
            need(direction in ("camera_frames_to_state_samples",
                               "state_samples_to_camera_frames", "bidirectional", "unknown"),
                 "thresholds.sync.pairing_direction must say which stream is paired to which")
            if pb == "sampled_stream":
                need(direction != "unknown",
                     "sampled_stream requires a known pairing direction: the sampled stream is "
                     "the one whose period applies")
                period = ts.get("sampled_stream_period_ms")
            else:
                need(direction == "unknown"
                     or (isinstance(ts.get("tau_convention_note"), str)
                         and "取最严" in ts.get("tau_convention_note", "")),
                     "shortest_stream is the strict end: with a known direction it must say it is "
                     "chosen as the strictest pairing")
                period = ts.get("shortest_stream_period_ms")
            need(is_num(period) and period > 0,
                 f"period_basis {pb} requires its period in ms")
            need(ts.get("tau_scope") == "global_simplified",
                 "tau_scope must be global_simplified: one tau for all pairs is a simplification")
            note = ts.get("global_tau_note") or ""
            need(isinstance(note, str) and note
                 and "偏低" in note and "取最严" in note,
                 "global_tau_note must print the direction of the bias: taking the strictest pair "
                 "can over-exclude and push NEES low; per-pair tau is the ideal form")
            if is_num(period) and is_num(factor) and is_num(tau):
                need(abs(tau - factor * period) <= max(1e-6, 1e-6 * tau),
                     f"tau {tau} does not recompute: tau_factor {factor} x period {period} = "
                     f"{factor * period}")
            tsen = ts.get("sensitivity") or []
            if not isinstance(tsen, list) or len(tsen) < 2:
                errs.append("thresholds.sync.sensitivity must carry at least two (tau, m) pairs")
            else:
                pairs = [(e.get("tau_ms"), e.get("w"), e.get("m")) for e in tsen
                         if isinstance(e, dict)]
                need(len(set(pairs)) == len(pairs),
                     "sync sensitivity (tau, w, m) combinations must be distinct")
                ms = [e.get("m") for e in tsen if isinstance(e, dict)]
                need(any(is_num(x) and abs(x - 2) < 1e-9 for x in ms),
                     "sync sensitivity must show m=2 as one of its bands")
                need(any(is_num(x) and abs(x - 3) < 1e-9 for x in ms),
                     "sync sensitivity must show m=3 as one of its bands")
                if is_num(m):
                    need(any(is_num(x) and abs(x - m) < 1e-9 for x in ms),
                         f"sync sensitivity must contain the declared m {m}, in addition to m=2 "
                         f"and m=3")
                    need(any(p[0] == tau and p[2] == m for p in pairs if is_num(p[0])),
                         f"the declared (tau, m) = ({tau}, {m}) must appear in its own sensitivity "
                         f"sweep")
                for e in tsen:
                    need(is_int(e.get("n_fail")) and is_int(e.get("n_degraded")),
                         "each sync sensitivity entry needs integer n_fail and n_degraded")
                    need(is_num(e.get("w")) and 0 < e.get("w") <= 1,
                         "each sync sensitivity entry needs w in (0, 1]: tau and W are swept in "
                         "the same table")
                ws = [e.get("w") for e in tsen if isinstance(e, dict)]
                if th.get("thresholds_origin") == "eeo_default_package":
                    need(len(set(ws)) >= 2,
                         "a default-package record must sweep W as well as tau: at least two w "
                         "values, including 0.95")
                    need(any(is_num(x) and abs(x - 0.95) < 1e-9 for x in ws),
                         "a default-package record must include the default W=0.95 in its sweep")
    if sstat == "unverified":
        need(sy.get("reason_code") in SYNC_REASONS,
             f"unverified sync requires a reason_code from {SYNC_REASONS}")
        need(all(v == 0 for v in cv[:3]) and all(v == 0 for v in cv[3:5]),
             "unverified sync cannot classify episodes: pass, degraded, fail and the two structural "
             "classes must be 0")
        if is_int(nd):
            need(sy.get("n_unverified") == nd,
                 "unverified sync must carry every episode as n_unverified")

    de = ne.get("dedup") or {}
    if not isinstance(de, dict):
        errs.append("neev.dedup must be an object")
        de = {}
    need(de.get("executed") is False,
         "neev.dedup.executed must be false: EEO estimates duplicates, it does not clean the corpus")
    mt = de.get("metric") or {}
    METRICS = ("embedding_cosine", "perceptual_hash", "exact_byte")
    need(isinstance(mt, dict) and isinstance(mt.get("id"), str) and mt.get("id"),
         "neev.dedup.metric.id is required: one id per named metric")
    need(isinstance(mt, dict) and isinstance(mt.get("defined_in"), str) and mt.get("defined_in"),
         "neev.dedup.metric must point at where the metric is defined (defined_in)")
    fam = mt.get("family") if isinstance(mt, dict) else None
    need(fam in METRICS,
         "neev.dedup.metric.family must be one of embedding_cosine / perceptual_hash / exact_byte: "
         "one enum, no synonyms, or records cannot be compared")
    bind = mt.get("threshold_binding") if isinstance(mt, dict) else None
    need(isinstance(bind, dict),
         "neev.dedup.metric.threshold_binding must be an object binding the metric and W")
    status = de.get("calibration_status")
    need(status in ("not_established", "established"),
         "neev.dedup.calibration_status must be not_established or established: no detector "
         "means no calibration claim")
    if isinstance(bind, dict):
        need(bind.get("metric") == fam,
             "metric.threshold_binding.metric must equal metric.family")
        wdecl = (th.get("dedup") or {}).get("w")
        need(is_num(bind.get("w")) and bind.get("w") == wdecl,
             "metric.threshold_binding.w must equal thresholds.dedup.w: W is bound to its metric")
        if status == "not_established":
            need(bind.get("calibration_fixture_id") is None,
                 "metric.threshold_binding.calibration_fixture_id must be null while "
                 "calibration_status is not_established")
        elif status == "established":
            need(isinstance(bind.get("calibration_fixture_id"), str)
                 and bind.get("calibration_fixture_id"),
                 "metric.threshold_binding.calibration_fixture_id is required when a real "
                 "calibration exists")
    cal = de.get("calibration")
    if status == "not_established":
        need(cal is None,
             "neev.dedup.calibration must be null while calibration_status is not_established: "
             "the cosine smoke test is not a detector gate")
    if status == "established":
        need(isinstance(cal, dict),
             "neev.dedup.calibration is required when calibration_status is established: the "
             "detector is EEO's own measurement and carries a known-truth gate")
    if status == "established" and isinstance(cal, dict):
        need(isinstance(cal.get("fixture_id"), str) and cal.get("fixture_id"),
             "dedup.calibration.fixture_id is required")
        need(isinstance(cal.get("fixture_version"), str) and cal.get("fixture_version"),
             "dedup.calibration.fixture_version is required")
        need(isinstance(cal.get("runner"), str) and cal.get("runner"),
             "dedup.calibration.runner is required: the calibration is an executable driver")
        if isinstance(cal.get("runner"), str):
            import os as _os
            _p = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                               cal.get("runner"))
            need(_os.path.isfile(_p),
                 f"dedup.calibration.runner {cal.get('runner')} must exist: a gate that cannot be "
                 f"run is not a gate")
        need(cal.get("executed") is True,
             "dedup.calibration.executed must be true: a runner that exists but was never run is "
             "not evidence")
        npos = cal.get("n_positive_pairs")
        nneg = cal.get("n_negative_pairs")
        need(is_int(npos) and npos >= 59,
             "dedup.calibration needs at least 59 known duplicate pairs: 0/59 gives a 95% upper "
             "bound just under 5%; 20 pairs cannot support a 5% claim")
        need(is_int(nneg) and nneg >= 59,
             "dedup.calibration needs at least 59 known distinct pairs, for the same reason")
        def _cp(k, n):
            if k >= n:
                return 1.0
            def cdf(p):
                return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))
            lo, hi = 0.0, 1.0
            for _ in range(60):
                mid = (lo + hi) / 2
                if cdf(mid) > 0.05:
                    lo = mid
                else:
                    hi = mid
            return (lo + hi) / 2
        for side, n in (("merge", npos), ("split", nneg)):
            k = cal.get(f"n_false_{side}")
            need(is_int(k) and is_int(n) and 0 <= k <= n,
                 f"dedup.calibration.n_false_{side} must be the observed count")
            rate = cal.get(f"false_{side}_rate")
            need(is_num(rate) and abs(rate - (k / n if is_int(n) and n else -1)) < 1e-6,
                 f"dedup.calibration.false_{side}_rate must equal n_false_{side}/n")
            ub = cal.get(f"upper95_false_{side}_rate")
            need(is_num(ub) and is_int(k) and is_int(n) and abs(ub - _cp(k, n)) < 5e-4,
                 f"upper95_false_{side}_rate must be the exact Clopper-Pearson upper bound")
            need(is_num(ub) and ub <= 0.05,
                 f"upper95_false_{side}_rate must be at most 0.05: the point rate is not the "
                 f"evidence")
        need(isinstance(cal.get("fixture_hash"), str) and len(cal.get("fixture_hash")) == 64,
             "dedup.calibration.fixture_hash is required")
        need(isinstance(cal.get("result_hash"), str) and len(cal.get("result_hash")) == 64,
             "dedup.calibration.result_hash is required")
        need(cal.get("passed") is True, "dedup.calibration.passed must be true before a dedup "
                                        "count is used")
        need(isinstance(cal.get("run_date"), str) and len(cal.get("run_date")) == 10,
             "dedup.calibration.run_date is required")
        if isinstance(bind, dict):
            need(bind.get("calibration_fixture_id") == cal.get("fixture_id"),
                 "threshold_binding.calibration_fixture_id must equal calibration.fixture_id")
    for k in ("n_duplicate_copies", "n_exact_copies", "n_cross_split_copies", "n_distinct_est"):
        need(is_int(de.get(k)) and de.get(k) >= 0,
             f"neev.dedup.{k} must be a non-negative integer")
    need(is_num(de.get("leakage_rate")) and de.get("leakage_rate") in (0, 1)
         or (is_num(de.get("leakage_rate")) and 0 <= de.get("leakage_rate") <= 1),
         "neev.dedup.leakage_rate must be in [0, 1]")

    pool_in = None
    if all(is_int(v) for v in cv):
        need(sum(cv) == nd,
             f"sync states do not close: pass {cv[0]} + degraded {cv[1]} + fail {cv[2]} + "
             f"alignment-excluded {cv[3]} + alignment-unlocatable {cv[4]} + unverified {cv[5]} "
             f"!= declared {nd}")
        pool_in = cv[0] + cv[5]
        dup = de.get("n_duplicate_copies")
        exact = de.get("n_exact_copies")
        if is_int(dup):
            need(dup <= pool_in, f"duplicates {dup} exceed the eligible pool {pool_in}")
        if is_int(dup) and is_int(exact):
            need(exact <= dup, f"exact copies {exact} exceed all duplicate copies {dup}")
        cross = de.get("n_cross_split_copies")
        if is_int(dup) and is_int(cross):
            need(cross <= dup, f"cross-split copies {cross} exceed all duplicate copies {dup}")
        dist = de.get("n_distinct_est")
        if is_int(dist):
            need(dist == pool_in - (dup if is_int(dup) else 0),
                 f"n_distinct_est {dist} does not recompute from pool {pool_in} minus "
                 f"duplicates {dup}")

    ch = ne.get("chain")
    if not isinstance(ch, dict):
        errs.append("neev.chain must be an object with sync_filtered, sync_unverified, "
                    "dedup_count and nees: four chain fields, with null rather than omission")
        ch = {}
    for k in ("sync_filtered", "sync_unverified", "dedup_count", "nees"):
        need(k in ch, f"neev.chain.{k} is required; use null rather than omitting it")
        v = ch.get(k)
        need(v is None or is_num(v), f"neev.chain.{k} must be a number or null")
    if all(is_int(v) for v in cv):

        need(is_num(ch.get("sync_unverified")) and ch.get("sync_unverified") == cv[5],
             f"chain.sync_unverified must be the unverified share {cv[5]} of the pool, so the "
             f"reader can see what inside sync_filtered was not measured")
        need(is_num(ch.get("sync_filtered")) and ch.get("sync_filtered") == cv[0] + cv[5],
             f"chain.sync_filtered must equal n_pass + n_unverified = {cv[0] + cv[5]}")
        if is_num(ch.get("sync_unverified")) and is_num(ch.get("sync_filtered")):
            need(ch.get("sync_unverified") <= ch.get("sync_filtered"),
                 "chain.sync_unverified cannot exceed chain.sync_filtered: the unverified share is "
                 "a part of the pool, not a separate count")
    dv = de.get("n_distinct_est")
    if is_int(dv):
        need(is_num(ch.get("dedup_count")) and ch.get("dedup_count") == dv,
             "chain.dedup_count must equal n_distinct_est")
    nsv = (ne.get("nees") or {}).get("value")
    nss = (ne.get("nees") or {}).get("status")
    if ch.get("nees") is None:
        need(nss not in ("computable", "interval", "upper_bound"),
             "chain.nees may be null only when NEES has no value")
    elif is_num(ch.get("nees")):
        need(is_num(nsv) and abs(ch.get("nees") - nsv) < 1e-9,
             "chain.nees must carry the NEES value when one is printed")

    cl = ne.get("cluster") or {}
    if not isinstance(cl, dict):
        errs.append("neev.cluster must be an object")
        cl = {}
    need(cl.get("axis") in AXES, f"neev.cluster.axis must be one of {AXES}")
    need(cl.get("level") in LEVELS, f"neev.cluster.level must be one of {LEVELS}")
    k_cnt = cl.get("count")
    need(is_int(k_cnt) and k_cnt >= 1, "neev.cluster.count must be a positive integer")
    ms = cl.get("mean_size")
    need(is_num(ms) and ms >= 1, "neev.cluster.mean_size must be >= 1")
    dist_est = de.get("n_distinct_est")
    if is_int(k_cnt) and is_int(dist_est) and is_num(ms):
        expect = dist_est / k_cnt
        need(abs(expect - ms) <= max(0.02, 0.01 * expect),
             f"neev.cluster.mean_size {ms} does not recompute: {dist_est}/{k_cnt} = {expect:.4f}")

    rho = ne.get("rho") or {}
    if not isinstance(rho, dict):
        errs.append("neev.rho must be an object")
        rho = {}
    rs = rho.get("status")
    need(rs in RHO_STATUS, f"neev.rho.status must be one of {RHO_STATUS}")
    need(rho.get("estimator") in RHO_EST, f"neev.rho.estimator must be one of {RHO_EST}")
    rv_val = rho.get("value")
    if rs in ("measured", "assumed"):
        need(is_num(rv_val) and 0 <= rv_val <= 1,
             "measured/assumed rho requires a value in [0, 1]")
    rb = rho.get("basis")
    need(isinstance(rb, dict) and rb.get("kind") in RHO_BASIS,
         f"neev.rho.basis must be an object whose kind is one of {RHO_BASIS}")
    if isinstance(rb, dict):
        kind = rb.get("kind")
        if rs == "assumed":
            need(kind in ("borrowed_from", "sensitivity_range"),
                 "assumed rho must state a typed basis: borrowed_from (a corpus id) or "
                 "sensitivity_range (a range, no point claim)")
        if kind == "borrowed_from":
            need(isinstance(rb.get("corpus_id"), str) and rb.get("corpus_id"),
                 "rho basis borrowed_from requires corpus_id")
        if kind == "sensitivity_range":
            rng = rb.get("range")
            need(isinstance(rng, list) and len(rng) == 2 and all(is_num(x) for x in rng)
                 and rng[0] <= rng[1],
                 "rho basis sensitivity_range requires a [low, high] range")
            if isinstance(rng, list) and len(rng) == 2 and isinstance(rho.get("interval"), list):
                need(rho.get("interval") == rng,
                     "rho.interval must equal the sensitivity range it is read from")
        if rs == "not_measured":
            need(kind == "not_measured", "not_measured rho must carry basis.kind not_measured")
        if rs == "measured":
            need(kind == "measured_here", "measured rho must carry basis.kind measured_here")
            need(isinstance(rho.get("interval"), list) and len(rho.get("interval")) == 2,
                 "measured rho must carry its interval")
    iv_r = rho.get("interval")
    if isinstance(iv_r, list) and len(iv_r) == 2 and all(is_num(x) for x in iv_r):
        need(iv_r[0] <= iv_r[1], "rho.interval must be [low, high]")
        if is_num(rv_val):
            need(iv_r[0] <= rv_val <= iv_r[1], "rho.value must lie inside rho.interval")

    ns = ne.get("nees") or {}
    if not isinstance(ns, dict):
        errs.append("neev.nees must be an object")
        ns = {}
    nst = ns.get("status")
    need(nst in NEES_STATUS, f"neev.nees.status must be one of {NEES_STATUS}")
    need(ns.get("unit") == "episode",
         "neev.nees.unit must be 'episode' (the counted unit is an episode, not a sample)")
    need(ns.get("basis") == "post_dedup_estimate",
         "neev.nees.basis must be 'post_dedup_estimate': it reports what dedup would leave, "
         "it does not report an edited corpus")
    need(ns.get("cleaning") == "not_performed",
         "neev.nees.cleaning must be 'not_performed': EEO does not edit the corpus")
    iv = ns.get("interval")
    if iv is not None:
        need(isinstance(iv, list) and len(iv) == 2 and is_num(iv[0]) and is_num(iv[1])
             and iv[0] <= iv[1], "neev.nees.interval must be [low, high] with low <= high")

    cap = ns.get("cap") or {}
    need(isinstance(cap, dict), "neev.nees.cap must be an object")
    if not isinstance(cap, dict):
        cap = {}
    bases = cap.get("bases")
    need(isinstance(bases, list) and all(b in CAP_BASES for b in bases),
         f"neev.nees.cap.bases must be a subset of {CAP_BASES}")
    if tier == "T1_sample":
        need("sample_scope" in (bases or []),
             "T1_sample must cap the reading with basis sample_scope")
    if tier == "T2_full":
        need("sample_scope" not in (bases or []),
             "T2_full is the full reading and must not carry a sample_scope cap")
    if sstat == "unverified":
        need("sync_unverified" in (bases or []),
             "unverified sync must cap the reading with basis sync_unverified")
        need(cap.get("direction") == "upper_bound",
             "unverified sync must set the cap direction to upper_bound")

    cap_value = cap.get("value")
    if cap.get("applied") is True:
        need(is_num(cap_value) and cap_value >= 0,
             "an applied cap requires cap.value: the bound is the number the buyer reads")
        need(isinstance(cap.get("formula"), str) and cap.get("formula"),
             "an applied cap requires cap.formula so the bound can be recomputed")
        need(is_num(cap.get("rho")) and 0 <= cap.get("rho") <= 1,
             "an applied cap requires cap.rho, the rho used in the bound")
        need(isinstance(cap.get("basis_note"), str) and cap.get("basis_note"),
             "an applied cap requires cap.basis_note")
        need(isinstance(cap.get("buyer_note"), str)
             and "上界" in cap.get("buyer_note", "")
             and "不是估计值" in cap.get("buyer_note", ""),
             "an applied cap requires buyer_note saying the bound is an upper bound, not an "
             "estimate")
        need(isinstance(iv_r, list) and len(iv_r) == 2,
             "a cap needs rho.interval: the low end of an interval is what makes the bound an "
             "upper bound; with no interval the reading is unestimable, not capped")
        need(cap.get("rho_source") in RHO_SOURCES,
             f"an applied cap must state rho_source from {RHO_SOURCES}: a true upper bound takes "
             f"rho at the low end of its interval")
        need(cap.get("mean_size_def") == "mean_cluster_size = n_dedup / n_clusters",
             "an applied cap must print mean_size_def: the cluster mean is n_dedup/n_clusters at "
             "the declared cluster.level, not any other average")
        need(cap.get("direction") == "upper_bound",
             "an applied cap must state direction upper_bound")
        low = None
        if isinstance(iv_r, list) and len(iv_r) == 2 and is_num(iv_r[0]):
            low = iv_r[0]
        if low is not None and is_num(cap.get("rho")):
            need(abs(cap.get("rho") - low) < 1e-9,
                 "cap.rho must be the low end of rho.interval: an upper bound at the point or "
                 "mid estimate is not an upper bound")
        if is_num(cap_value) and is_int(dist_est) and is_int(k_cnt) and is_num(cap.get("rho")):
            expect = dist_est / (1 + (dist_est / k_cnt - 1) * cap.get("rho"))
            need(abs(cap_value - expect) <= max(0.005, 0.005 * expect),
                 f"cap.value {cap_value} does not recompute: n_dedup/(1+(mean_cluster_size-1)*rho) "
                 f"= {expect:.3f}")
    else:
        need(cap.get("direction") is None, "a cap that is not applied must not state a direction")
        need(cap.get("value") is None, "a cap that is not applied must not print a bound")

    val = ns.get("value")
    if nst == "computable":
        need(is_num(val), "computable NEES requires a point value")
        need(iv is not None, "computable NEES requires an interval")
        need(rs in ("measured", "assumed") and is_num(rv_val),
             "computable NEES requires rho.status measured or assumed with a value")
        if is_num(val):
            need(is_int(dist_est) and val <= dist_est,
                 f"NEES {val} exceeds the deduplicated pool {dist_est}")
            if isinstance(iv, list) and len(iv) == 2:
                need(iv[0] <= val <= iv[1], "NEES point value must lie inside its interval")
    if nst == "interval":
        need(iv is not None, "interval-status NEES requires an interval")
        need(val is None, "interval-status NEES must not print a point value")
    if nst == "upper_bound":
        need(cap.get("applied") is True, "upper_bound status requires an applied cap")
        need(is_num(val) and is_num(cap_value) and abs(val - cap_value) < 1e-9,
             "upper_bound status requires nees.value to equal cap.value: the bound is the reading")
        need(iv is None, "upper_bound status must not carry an interval: an upper bound is not a "
                         "confidence interval")
    if nst in ("unestimable_zero_variance", "unestimable_alignment", "unestimable_other"):
        need(val is None, f"{nst} must not print a value")
        need(ns.get("reason_code") in NEES_REASONS[nst],
             f"{nst} requires a reason_code from {NEES_REASONS[nst]}")
        need(isinstance(ns.get("reason_detail"), str) and ns.get("reason_detail"),
             f"{nst} requires a reason_detail")
    if nst == "unestimable_alignment":
        need(is_int(unl) and unl >= 1 and al.get("outcome") == "extent_unknown",
             "unestimable_alignment requires episodes whose extent is unknown: "
             "n_alignment_unlocatable >= 1 and alignment.outcome extent_unknown")
    if is_int(unl) and unl > 0:
        need(nst == "unestimable_alignment" and al.get("outcome") == "extent_unknown",
             f"{unl} episodes have a structural fault whose extent is unknown: NEES must be "
             f"unestimable_alignment with alignment.outcome extent_unknown")

    dg = ne.get("diagnostics")
    need(isinstance(dg, dict),
         "neev.diagnostics is required: separate readings carry their own bases")
    if isinstance(dg, dict):
        zv = dg.get("zero_variance_share") or {}
        ndiag = dg.get("n_dedup") or {}
        zstat = zv.get("status")
        need(zstat in ("computed", "not_computable_due_to_alignment"),
             "diagnostics.zero_variance_share.status must be computed or "
             "not_computable_due_to_alignment")
        if zstat == "computed":
            need(is_num(zv.get("value")) and 0 <= zv.get("value") <= 1,
                 "diagnostics.zero_variance_share.value must be in [0, 1] when computed")
        else:
            need(zv.get("value") is None,
                 "diagnostics.zero_variance_share must not carry a value when the time axis is "
                 "broken")
            need(nst == "unestimable_alignment",
                 "zero_variance_share is not computable only when NEES is unestimable_alignment")
        if nst == "unestimable_alignment":
            need(zstat == "not_computable_due_to_alignment",
                 "an alignment-blocked reading cannot print zero_variance_share: the variance "
                 "reading depends on the time axis and is not computable")
        need(isinstance(zv.get("basis"), str) and zv.get("basis"),
             "diagnostics.zero_variance_share.basis must state the level it was taken at")
        need(is_int(ndiag.get("value")) and ndiag.get("value") >= 0,
             "diagnostics.n_dedup.value must be a non-negative integer")
        need(ndiag.get("value") == dist_est,
             "diagnostics.n_dedup.value must equal n_distinct_est")
        need(isinstance(ndiag.get("basis"), str) and ndiag.get("basis"),
             "diagnostics.n_dedup.basis must state how the count was reached")
        if nst == "unestimable_zero_variance":
            need(zstat == "computed" and is_num(zv.get("value")) and zv.get("value") >= 0.9,
                 "unestimable_zero_variance requires zero_variance_share computed at >= 0.90")
        if zstat == "computed" and is_num(zv.get("value")) and zv.get("value") >= 0.9:
            need(nst != "computable" and nst != "interval" and nst != "upper_bound",
                 "zero-variance dominance forbids a point or capped NEES: no reading where rho "
                 "cannot be identified")

    fo = ne.get("failure_observations")
    if fo is None:
        need(nst == "unestimable_alignment",
             "failure_observations may be omitted only when NEES is unestimable_alignment")
    else:
        if not isinstance(fo, dict):
            errs.append("neev.failure_observations must be an object or null")
            fo = {}
        fails = fo.get("failures")
        need(is_int(fails) and fails >= 0,
             "failure_observations.failures must be a non-negative integer")
        need(is_int(fo.get("n")) and fo.get("n") >= 1, "failure_observations.n must be positive")
        n_ind = fo.get("n_ind")
        need(is_int(n_ind) and n_ind >= 1, "failure_observations.n_ind must be a positive integer")
        need(fo.get("n_ind_basis") in N_IND_BASIS,
             f"failure_observations.n_ind_basis must be one of {N_IND_BASIS}")
        need(isinstance(fo.get("basis"), str) and fo.get("basis"),
             "failure_observations.basis must state what n_ind counts and where the two ends come "
             "from")
        need(is_num(fo.get("upper95_by_cluster")) and 0 <= fo.get("upper95_by_cluster") <= 1,
             "failure_observations.upper95_by_cluster must be in [0, 1]")
        need(is_num(fo.get("upper95_by_dedup")) and 0 <= fo.get("upper95_by_dedup") <= 1,
             "failure_observations.upper95_by_dedup must be in [0, 1]")
        need(isinstance(fo.get("decision_note"), str) and fo.get("decision_note"),
             "failure_observations.decision_note must say what the bound rules out, in buyer terms")
        if is_int(dist_est) and is_int(fo.get("n")):
            need(fo.get("n") <= dist_est,
                 "failure_observations.n cannot exceed the deduplicated count: outcomes are a "
                 "subset of the pool")
        if fo.get("n_ind_basis") == "dedup_count" and is_int(dist_est):
            need(n_ind == dist_est,
                 "n_ind_basis dedup_count requires n_ind to equal n_distinct_est")
            need("偏窄" in fo.get("basis", ""),
                 "n_ind_basis dedup_count must note that residual clustering is not removed and the "
                 "bound is narrow")
        if fo.get("n_ind_basis") == "cluster_count" and is_int(k_cnt):
            need(n_ind == k_cnt,
                 "n_ind_basis cluster_count requires n_ind to equal the cluster count")
        if is_int(fails) and is_int(k_cnt):
            p = upper95(fails, k_cnt)
            need(is_num(fo.get("upper95_by_cluster"))
                 and abs(fo.get("upper95_by_cluster") - p) <= max(0.0025, 0.05 * p),
                 f"upper95_by_cluster {fo.get('upper95_by_cluster')} does not recompute from "
                 f"{fails} failures over {k_cnt} clusters ({p:.4f})")
        if is_int(fails) and is_int(dist_est):
            p = upper95(fails, dist_est)
            need(is_num(fo.get("upper95_by_dedup"))
                 and abs(fo.get("upper95_by_dedup") - p) <= max(0.0025, 0.05 * p),
                 f"upper95_by_dedup {fo.get('upper95_by_dedup')} does not recompute from "
                 f"{fails} failures over {dist_est} episodes ({p:.4f})")
        if is_int(fails) and fails == 0:
            budget = fo.get("cluster_budget")
            need(isinstance(budget, list) and len(budget) >= 1,
                 "a zero-failure observation must print the cluster budget: how many independent "
                 "clusters a target failure rate would need")
            targets = [0.1, 0.05, 0.01]
            if isinstance(budget, list):
                rates = [e.get("target_rate") for e in budget if isinstance(e, dict)]
                need(set(targets) <= set(rates),
                     "cluster_budget must cover 10%, 5% and 1% target rates")
                for e in budget:
                    if not isinstance(e, dict):
                        continue
                    rate = e.get("target_rate")
                    need(rate in targets, "cluster_budget target_rate must be 0.10, 0.05 or 0.01")
                    if rate in targets:
                        need(e.get("clusters_required") == math.ceil(math.log(0.05) / math.log(1 - rate)),
                             f"clusters_required for {rate} must be "
                             f"ceil(ln(0.05)/ln(1-target)) = "
                             f"{math.ceil(math.log(0.05) / math.log(1 - rate))}")
        elif is_int(fails):
            need(fo.get("cluster_budget") is None,
                 "the cluster budget assumes zero failures; with observed failures print the "
                 "failure-rate interval instead")

    tr = ne.get("trajectory_diversity_signal")
    need(isinstance(tr, dict),
         "neev.trajectory_diversity_signal is required: the diversity reading travels with NEES")
    if isinstance(tr, dict):
        tstat = tr.get("status")
        need(tstat in ("computed", "insufficient_sample", "not_computed",
                       "not_computable_mixed_embodiment", "not_computable"),
             "trajectory_diversity_signal.status must be computed, insufficient_sample, "
             "not_computed, not_computable_mixed_embodiment or not_computable")
        need(tr.get("pool") == "post_dedup",
             "trajectory_diversity_signal.pool must be post_dedup: diversity is measured on the "
             "clean pool, never upstream")
        need(is_int(tr.get("n_dedup")) and tr.get("n_dedup") == dist_est,
             "trajectory_diversity_signal.n_dedup must equal n_distinct_est")
        need(tr.get("dim_rule") == "participation_ratio",
             "the primary diversity reading is the participation ratio: deterministic, no cutoff. "
             "A variance cutoff introduces an adjustable X and is not accepted as the main rule; "
             "spectral entropy may travel only as a supplementary T2 reading")
        need(tr.get("embodiment_scope") in ("single", "mixed", "unknown"),
             "trajectory_diversity_signal.embodiment_scope must be single, mixed or unknown")
        scope = tr.get("embodiment_scope")
        emb = tr.get("embodiment") or {}
        st = tr.get("stratification") or {}
        need(isinstance(st, dict),
             "trajectory_diversity_signal.stratification is required: task variety can masquerade "
             "as policy variety, so the unit of stratification must be stated")
        if isinstance(st, dict):
            mode = st.get("mode")
            need(mode in ("stratified", "pooled"),
                 "stratification.mode must be stratified or pooled")
            need(st.get("unit") in ("task", "scene", "dataset"),
                 "stratification.unit must be task, scene or dataset")
            tc = st.get("task_count")
            need(is_int(tc) and tc >= 1, "stratification.task_count must be a positive integer")
            need(is_int(st.get("n_strata")) and st.get("n_strata") >= 1,
                 "stratification.n_strata must be a positive integer")
            if is_int(tc) and tc > 1:
                need(mode == "stratified",
                     "a corpus with more than one task must report diversity per stratum: a pooled "
                     "value would let task variety pass as policy variety")
            if mode == "pooled":
                need(tc == 1,
                     "pooled diversity is allowed only for a single-task corpus")
                need(st.get("per_stratum") is None,
                     "pooled diversity must not carry per_stratum entries")
            if mode == "stratified":
                ps = st.get("per_stratum")
                need(isinstance(ps, list) and len(ps) == st.get("n_strata"),
                     "stratified diversity requires per_stratum entries, one per stratum")
                if isinstance(ps, list) and is_int(tr.get("n_dedup")):
                    ids = [e.get("stratum_id") for e in ps if isinstance(e, dict)]
                    need(len(set(ids)) == len(ids), "per_stratum stratum_id values must be distinct")
                    tot = sum(e.get("n_dedup") for e in ps
                              if isinstance(e, dict) and is_int(e.get("n_dedup")))
                    need(tot == tr.get("n_dedup"),
                         f"per_stratum n_dedup sums to {tot}, not the pool {tr.get('n_dedup')}")
                    vals = []
                    n_ins = 0
                    for e in ps:
                        if not isinstance(e, dict):
                            continue
                        n_e = e.get("n_dedup")
                        need(is_int(n_e) and n_e >= 0, "each stratum needs a non-negative n_dedup")
                        if is_int(n_e) and n_e >= 50:
                            need(e.get("status") == "computed" and is_num(e.get("effective_dim")),
                                 "a stratum with n_dedup >= 50 is computed and carries its "
                                 "effective_dim")
                            if is_num(e.get("effective_dim")):
                                vals.append(e.get("effective_dim"))
                        else:
                            n_ins += 1
                            need(e.get("status") == "insufficient_sample"
                                 and e.get("effective_dim") is None,
                                 "a stratum below 50 is insufficient_sample and prints no "
                                 "effective_dim: the floor is per stratum, not per pool")
                    summ = tr.get("stratum_summary")
                    need(isinstance(summ, dict),
                         "a stratified reading requires stratum_summary: how many strata were "
                         "computable and where the computable ones lie")
                    if isinstance(summ, dict):
                        need(summ.get("n_strata") == len(ps),
                             "stratum_summary.n_strata must equal the number of strata")
                        need(summ.get("n_computed") == len(vals),
                             f"stratum_summary.n_computed must be {len(vals)}")
                        need(summ.get("n_insufficient") == n_ins,
                             f"stratum_summary.n_insufficient must be {n_ins}")
                        if vals:
                            vals_sorted = sorted(vals)
                            n_v = len(vals_sorted)
                            med = (vals_sorted[n_v // 2] if n_v % 2
                                   else (vals_sorted[n_v // 2 - 1] + vals_sorted[n_v // 2]) / 2)
                            need(is_num(summ.get("median"))
                                 and abs(summ.get("median") - med) <= max(0.02, 0.01 * med),
                                 f"stratum_summary.median must be {med:.3f} over computed strata")
                            need(is_num(summ.get("min")) and abs(summ.get("min") - vals_sorted[0]) < 1e-6,
                                 "stratum_summary.min must be the lowest computed stratum value")
                            need(is_num(summ.get("max")) and abs(summ.get("max") - vals_sorted[-1]) < 1e-6,
                                 "stratum_summary.max must be the highest computed stratum value")
                        else:
                            need(summ.get("median") is None and summ.get("min") is None
                                 and summ.get("max") is None,
                                 "with no computable stratum the summary carries no numbers")
            if is_int(tc) and tc > 1:
                need(tr.get("effective_dim") is None,
                     "a multi-task corpus must not publish a bare pooled dimension: report per "
                     "stratum, or a pooled_total with its between_task_share")
                need(is_num(tr.get("pooled_total")) and is_num(tr.get("between_task_share"))
                     and 0 <= tr.get("between_task_share") <= 1,
                     "a multi-task corpus that prints a pooled_total must also print "
                     "between_task_share: the share of it that is task difference rather than "
                     "policy difference")
            else:
                need(tr.get("pooled_total") is None and tr.get("between_task_share") is None,
                     "a single-task corpus has no between-task share: leave pooled_total and "
                     "between_task_share null")
        if scope == "mixed":
            need(tstat == "not_computable_mixed_embodiment",
                 "a corpus that mixes embodiments cannot carry a diversity value: status must be "
                 "not_computable_mixed_embodiment")
        if scope == "unknown":
            need(tstat in ("not_computed", "not_computable"),
                 "an unknown embodiment scope cannot carry a computed value")
        if tstat == "computed":
            need(scope == "single",
                 "a computed value requires a single embodiment (embodiment_scope single)")
            need(is_int(tr.get("n_dedup")) and tr.get("n_dedup") >= 50,
                 "computed trajectory diversity requires n_dedup >= 50: below that the dimension "
                 "count is unstable (status insufficient_sample)")
            need(is_num(tr.get("effective_dim")) or is_int(st.get("task_count"))
                 and st.get("task_count") > 1,
                 "computed trajectory diversity requires effective_dim from the participation ratio")
            se = tr.get("spectral_entropy")
            if se is not None:
                need(isinstance(se, dict) and is_num(se.get("value")) and se.get("role") == "supplementary",
                     "spectral entropy may only travel as a supplementary reading, never mixed into "
                     "the primary dimension count")
            need(emb.get("mode") == "within",
                 "trajectory diversity across embodiments is not recommended: mixed bases give "
                 "uninterpretable dimensions (basis must read 'computed within embodiment: <id>')")
            need(isinstance(emb.get("embodiment_id"), str) and emb.get("embodiment_id"),
                 "computed trajectory diversity requires the embodiment id it was computed within")
            need(tr.get("basis", "").startswith("computed within embodiment:"),
                 "computed trajectory diversity basis must read 'computed within embodiment: <id>'")
        if tstat == "insufficient_sample":
            need(is_int(tr.get("n_dedup")) and tr.get("n_dedup") < 50,
                 "insufficient_sample is for n_dedup < 50")
        need("增加做法变化" in (tr.get("decision_supports") or ""),
             "trajectory_diversity_signal.decision_supports must name the decision it supports: "
             "whether to ask the supplier for more practice variation within a task")
        need("训出更好的策略" in (tr.get("decision_does_not_support") or ""),
             "trajectory_diversity_signal.decision_does_not_support must say it does not answer "
             "whether this corpus trains a better policy")
        note = tr.get("note") or ""
        need("不是 NEES 的替代" in note,
             "trajectory_diversity_signal.note must say it is not a substitute for NEES")
        need("不可跨语料直接比较" in note,
             "trajectory_diversity_signal.note must say a within-embodiment value cannot be "
             "compared across corpora")

    sp = rec.get("split")
    need(sp in SPLITS, f"split must be one of {SPLITS}")
    if sp in AXES:
        need(sp == cl.get("axis"), "split and cluster.axis must agree")
    if sp == "frame-wise":
        need(nst == "unestimable_other" and ns.get("reason_code") == "frame_wise_split",
             "frame-wise split forbids a NEES point value: reason frame_wise_split")
    if sp == "not declared":
        need(nst == "unestimable_other" and ns.get("reason_code") == "split_not_declared",
             "an undeclared split forbids a NEES point value: reason split_not_declared")

    bs = rec.get("buyer_summary")
    if not isinstance(bs, list) or not 3 <= len(bs) <= 5:
        errs.append("buyer_summary must have three to five lines: one reading and two premises, "
                    "plus a stream-continuity line when findings exist")
    else:
        need(all(isinstance(x, str) and x for x in bs),
             "each buyer_summary line must be a non-empty string")
        if tier == "T1_sample":
            joined = " ".join(bs)
            need("抽到" in joined or "抽样" in joined or "sampled" in joined,
                 "T1_sample buyer_summary must speak of what was sampled")
            need("这份数据集" not in joined and "this dataset" not in joined,
                 "T1_sample buyer_summary must not speak about the whole corpus")
            need(any("上界" in x or "upper bound" in x for x in bs),
                 "T1_sample buyer_summary must say the reading is an upper bound")
        joined = " ".join(bs)
        scf = ((ne.get("sync") or {}).get("stream_continuity_findings") or {})
        cnt = scf.get("count")
        need(is_int(cnt) and any("流连续性发现" in x and str(cnt) in x for x in bs),
             "buyer_summary must carry a line naming the stream-continuity finding count, so a "
             "summary reader sees it without opening the technical section")
        if nst in ("unestimable_zero_variance", "unestimable_alignment", "unestimable_other"):
            joined = " ".join(bs)
            need("无法" in joined or "不可计算" in joined or "not computable" in joined,
                 "an unestimable reading must say so in the buyer summary")

    tc_b = (tr.get("stratification") or {}).get("task_count") if isinstance(tr, dict) else None
    if is_int(tc_b) and tc_b > 1 and isinstance(tr, dict) and tr.get("status") == "computed":
        joined = " ".join(bs) if isinstance(bs, list) else ""
        need("层内中位数" in joined,
             "a multi-task summary must lead with the within-stratum median and range, not a bare "
             "pooled dimension")

    sd = rec.get("scope_declaration")
    need(isinstance(sd, dict),
         "scope_declaration is required: what this version does not assess must be declared, not "
         "dropped silently")
    if isinstance(sd, dict):
        for key, label in (("label_consistency", "label consistency"),
                           ("card_index_crosscheck", "card-versus-index crosscheck")):
            v = sd.get(key) or {}
            need(isinstance(v, dict) and v.get("status") == "not_assessed",
                 f"scope_declaration.{key}.status must be not_assessed: this version gives no "
                 f"reading for {label}")
            need(isinstance(v.get("reason"), str) and v.get("reason"),
                 f"scope_declaration.{key}.reason must say why it is out of scope and when it "
                 f"returns")
        note = sd.get("dimension_code_note") or ""
        need("DSR-D" in note and "不是" in note and "crosswalk" in note,
             "scope_declaration.dimension_code_note must use the DSR- prefix and say the codes are "
             "local, not a crosswalk: a prefix removes the clash instead of declaring it away")

    ul = rec.get("use_limitation") or {}
    need(ul.get("text_version") == UL_VERSION, f"use_limitation.text_version must be {UL_VERSION}")
    need(ul.get("zh") == UL_ZH and ul.get("en") == UL_EN,
         "use_limitation must carry the canonical sentence EEO-DUL-2 verbatim")
    hdr = rec.get("buyer_summary_use_limitation") or {}
    need(hdr.get("text_version") == UL_VERSION and hdr.get("zh") == UL_ZH
         and hdr.get("en") == UL_EN,
         "buyer_summary_use_limitation must repeat EEO-DUL-2 verbatim at the head of the summary "
         "page")
    rn = rec.get("reference_note") or {}
    need(rn.get("text_version") == RN_VERSION,
         f"reference_note.text_version must be {RN_VERSION}")
    need(rn.get("zh") == RN_ZH and rn.get("en") == RN_EN,
         "reference_note must carry the canonical sentence EEO-RN-3 verbatim")

    return errs


def check_observation(doc):
    """Return a list of error strings for a clock observation produced by EEO's own model."""
    errs = []

    def need(cond, msg):
        if not cond:
            errs.append(msg)

    if not isinstance(doc, dict):
        return ["clock observation is not an object"]
    need(doc.get("contract_version") == OBS_VERSION, f"contract_version must be {OBS_VERSION}")
    if "tool" in doc:
        need(False, "an observation must not name an external tool: the producer is EEO's clock model")
    prod = doc.get("producer") or {}
    need(isinstance(prod, dict), "producer is required")
    need(prod.get("model_id") == "eeo-clock", "producer.model_id must be 'eeo-clock'")
    need(isinstance(prod.get("model_version"), str) and prod.get("model_version"),
         "producer.model_version is required: a reading is only as traceable as the version behind it")
    need(prod.get("self_implemented") is True, "producer.self_implemented must be true")
    need(prod.get("external_dependency") is False,
         "producer.external_dependency must be false: EEO takes no external timing dependency")
    tau = doc.get("tolerance_ms")
    need(is_num(tau) and tau > 0, "tolerance_ms must be a positive number")
    mm = doc.get("degraded_band_multiplier")
    need(is_num(mm) and mm > 1,
         "degraded_band_multiplier must be > 1: it is the top of the band and must match the "
         "record's declared m")

    streams = doc.get("streams")
    need(isinstance(streams, list) and len(streams) >= 1, "streams must list at least one stream")
    for s in streams if isinstance(streams, list) else []:
        need(isinstance(s.get("name"), str) and s.get("name"), "each stream needs a name")
        need(s.get("role") in ("primary", "secondary", "state", "tactile", "audio", "other"),
             "each stream needs a known role")
        need(is_num(s.get("median_skew_ms")), "each stream needs median_skew_ms")
        need(is_num(s.get("p95_skew_ms")) and s.get("p95_skew_ms") >= 0,
             "each stream needs a non-negative p95_skew_ms")
        need(is_num(s.get("missing_rate")) and 0 <= s.get("missing_rate") <= 1,
             "each stream needs missing_rate in [0, 1]")

    eps = doc.get("episodes")
    need(isinstance(eps, list) and len(eps) >= 1, "episodes must list at least one episode")
    for e in eps if isinstance(eps, list) else []:
        need(isinstance(e.get("episode_id"), str) and e.get("episode_id"),
             "each episode needs an id")
        vd = e.get("verdict")
        need(vd in OBS_VERDICTS, f"each episode needs a verdict from {OBS_VERDICTS}")
        need(is_num(e.get("worst_skew_ms")) and e.get("worst_skew_ms") >= 0,
             "each episode needs a non-negative worst_skew_ms")
        fatal = False
        for v in e.get("violations") or []:
            need(v.get("type") in VIOLATIONS, "each violation needs a known type")
            need(is_int(v.get("count")) and v.get("count") >= 1,
                 "each violation needs a positive count")
            if v.get("type") in FATAL_VIOLATIONS:
                fatal = True
        if fatal:
            need(vd in ("alignment_excluded", "alignment_unlocatable", "unverified"),
                 f"episode {e.get('episode_id')}: a clock reset or non-monotonic timestamp is a "
                 f"structural fault and cannot be pass, degraded or fail")
        if is_num(tau) and is_num(mm) and is_num(e.get("worst_skew_ms")):
            w = e.get("worst_skew_ms")
            if vd == "pass":
                need(w <= tau, f"episode {e.get('episode_id')}: pass with worst skew above tau {tau}")
            if vd == "degraded":
                need(tau < w <= mm * tau,
                     f"episode {e.get('episode_id')}: degraded outside its band ({tau}, {mm * tau}]")
            if vd == "fail":
                need(w > mm * tau,
                     f"episode {e.get('episode_id')}: fail must sit above the degraded band "
                     f"{mm * tau}")

    return errs


def run_self_test(example_dir):
    names = ("record-example", "record-example-unestimable", "record-example-degraded",
             "record-example-alignment-segment", "record-example-alignment-unlocatable",
             "record-example-default-package", "record-example-multitask")
    docs = {}
    for name in names:
        with open(os.path.join(example_dir, name + ".json"), encoding="utf-8") as fh:
            docs[name] = json.load(fh)
    with open(os.path.join(example_dir, "sync-observation-example.json"), encoding="utf-8") as fh:
        obs_base = json.load(fh)

    base = docs["record-example"]
    gate = copy.deepcopy(base)
    gate["neev"]["dedup"]["calibration_status"] = "established"
    gate["neev"]["dedup"]["metric"]["threshold_binding"]["calibration_fixture_id"] = "dedup-calib-synthetic"
    gate["neev"]["dedup"]["calibration"] = {
        "fixture_id": "dedup-calib-synthetic",
        "fixture_version": "0.1",
        "fixture_hash": "9cdd7d4ad826a44c5bad35f4e0f766819c058a7324b16294386f94574dea6bbc",
        "runner": "tools/validate_record.py",
        "executed": True,
        "n_positive_pairs": 59,
        "n_negative_pairs": 59,
        "n_false_merge": 0,
        "n_false_split": 0,
        "false_merge_rate": 0.0,
        "false_split_rate": 0.0,
        "upper95_false_merge_rate": 0.049508,
        "upper95_false_split_rate": 0.049508,
        "passed": True,
        "result_hash": "f72752b4d6e922ca88e09d59a5a82148789cc41afe39b457145f247673ea9dd7",
        "run_date": "2026-11-25",
    }
    unest = docs["record-example-unestimable"]
    degraded = docs["record-example-degraded"]
    seg = docs["record-example-alignment-segment"]
    unl = docs["record-example-alignment-unlocatable"]

    for name, doc in docs.items():
        errs = check(doc)
        if errs:
            print(f"self-test: the shipped example {name} is not valid: {errs[0]}")
            return 1
    if check_observation(obs_base):
        print(f"self-test: the shipped observation is not valid: {check_observation(obs_base)[0]}")
        return 1

    cases = []

    def case(name, src, mutate, expect):
        rec = copy.deepcopy(src)
        mutate(rec)
        cases.append((name, rec, expect))

    def setp(path, value):
        def mutate(rec):
            cur = rec
            for key in path[:-1]:
                cur = cur[key]
            cur[path[-1]] = value
        return mutate

    def delp(path):
        def mutate(rec):
            cur = rec
            for key in path[:-1]:
                cur = cur[key]
            cur.pop(path[-1], None)
        return mutate

    # thresholds
    case("thresholds set by EEO", base, setp(["thresholds", "eeo_sets_thresholds"], True),
         "must be false")
    case("m missing", base, delp(["thresholds", "sync", "m"]), "m must be greater than 1")
    case("declared m absent from its sweep", base, setp(["thresholds", "sync", "m"], 2.5),
         "must appear in its own sensitivity sweep")
    case("sensitivity without m=2", base,
         setp(["thresholds", "sync", "sensitivity"],
              [{"tau_ms": 40, "w": 0.95, "m": 3, "n_fail": 96, "n_degraded": 74},
               {"tau_ms": 60, "w": 0.95, "m": 3, "n_fail": 41, "n_degraded": 38}]), "m=2")
    case("declared m=4 outside the sweep", base,
         lambda r: r["thresholds"]["sync"].update({"m": 4, "m_origin": "buyer"}),
         "must contain the declared m")
    case("m from EEO but not equal to its default", base,
         lambda r: r["thresholds"]["sync"].update({"m": 4, "m_origin": "eeo_default"}),
         "must be attributed to a party")
    case("metric smuggled into thresholds", base,
         lambda r: r["thresholds"]["dedup"].update({"metric": "cosine_frame_pooled"}),
         "metric is fixed by EEO")
    case("dedup w missing", base, delp(["thresholds", "dedup", "w"]), "w must be in (0, 1]")
    case("declared w absent from its sweep", base,
         setp(["thresholds", "dedup", "w"], 0.93), "must appear in its own sensitivity sweep")
    case("single dedup threshold", base,
         setp(["thresholds", "dedup", "sensitivity"], [{"w": 0.95, "n_duplicate_copies": 61}]),
         "at least two w values")
    case("tau undeclared on verified sync", base, delp(["thresholds", "sync"]),
         "requires thresholds.sync")

    # the clock model is EEO's own, and it must have passed its own fixture
    case("external timing tool cited as the source", base,
         lambda r: r["neev"]["sync"].update({"tool": {"name": "some-timing-cli"}}),
         "does not cite an external timing tool")
    case("clock model declared external", base,
         setp(["neev", "sync", "clock_model", "external_dependency"], True),
         "no external timing dependency")
    case("verified sync without an observation hash", base,
         delp(["neev", "sync", "clock_model", "observation_sha256"]), "observation_sha256")
    case("verified sync without a fixture run", base,
         delp(["neev", "sync", "clock_model", "self_check"]), "known-ground-truth")
    case("fixture run not fully passed", base,
         setp(["neev", "sync", "clock_model", "self_check", "n_passed"], 9),
         "passed every injected case")
    case("fixture with too few cases", base,
         setp(["neev", "sync", "clock_model", "self_check", "n_cases"], 4), "at least 8")
    case("fixture without a runner", base,
         delp(["neev", "sync", "clock_model", "self_check", "runner"]), "runner is required")
    case("fixture covering only late packets", base,
         lambda r: r["neev"]["sync"]["clock_model"]["self_check"].update(
             {"coverage": ["late_packet"]}), "all five injected fault classes")
    case("scope note dropped", base, delp(["neev", "sync", "scope_note"]), "scope_note")

    # counts, binary degraded, chain
    case("sync states do not close", base, setp(["neev", "sync", "n_pass"], 1031),
         "sync states do not close")
    case("degraded weighted instead of excluded", base,
         setp(["neev", "sync", "degraded_policy"], "weighted"), "degraded_policy")
    case("weighted degraded ratio reintroduced", base,
         lambda r: r["neev"]["sync"].update({"degraded_ratio": 0.061}), "weighted degraded ratio")
    case("chain does not close", base, setp(["neev", "chain", "dedup_count"], 1000),
         "chain.dedup_count must equal")
    case("chain field omitted", base, delp(["neev", "chain", "sync_filtered"]),
         "is required; use null rather than omitting")
    case("chain hides the unverified share", base,
         delp(["neev", "chain", "sync_unverified"]), "sync_unverified is required")
    case("chain unverified share does not match", base,
         setp(["neev", "chain", "sync_unverified"], 5), "must be the unverified share")
    case("dedup executed on the corpus", base, setp(["neev", "dedup", "executed"], True),
         "does not clean the corpus")
    case("dedup metric removed", base, delp(["neev", "dedup", "metric"]), "metric.id is required")
    case("distinct count does not recompute", base, setp(["neev", "dedup", "n_distinct_est"], 960),
         "does not recompute")
    case("exact copies exceed all copies", base,
         setp(["neev", "dedup", "n_exact_copies"], 70), "exceed all duplicate copies")
    case("cross-split exceeds all duplicates", base,
         setp(["neev", "dedup", "n_cross_split_copies"], 70), "exceed all duplicate copies")

    # structural faults: alignment is not executed, and the consequence is graded
    case("alignment executed anyway", seg, setp(["neev", "sync", "alignment", "executed"], True),
         "alignment is not executed")
    case("excluded segment without its extent", seg,
         delp(["neev", "sync", "alignment", "affected_episodes"]), "affected_episodes")
    case("segment outcome without excluded episodes", seg,
         setp(["neev", "sync", "n_alignment_excluded"], 0), "segment_excluded requires")
    case("unknown extent still prints a number", unl,
         lambda r: r["neev"]["nees"].update({"status": "computable"}), "must be unestimable_alignment")
    case("unknown extent without its reason", unl,
         delp(["neev", "sync", "alignment", "reason_code"]), "reason_code reset_points_unlocatable")
    case("alignment counted as fail only", unl,
         lambda r: (r["neev"]["sync"].update({"n_alignment_unlocatable": 0, "n_fail": 30}),
                    r["neev"]["sync"]["alignment"].update({"outcome": "not_required"}),
                    r["neev"]["nees"].update({"status": "unestimable_alignment"})),
         "requires episodes whose extent is unknown")
    case("unestimated alignment with a point value", unl,
         setp(["neev", "nees", "value"], 210.0), "must not print a value")
    case("unestimated alignment without diagnostics", unl, delp(["neev", "diagnostics"]),
         "diagnostics is required")
    case("alignment case hides the dedup count", unl,
         setp(["neev", "diagnostics", "n_dedup", "value"], None), "must equal n_distinct_est")
    case("alignment case still prints zero variance", unl,
         lambda r: r["neev"]["diagnostics"]["zero_variance_share"].update(
             {"status": "computed", "value": 0.91}), "cannot print zero_variance_share")

    # unverified sync is a state, not a skip, and its cap must be a true bound
    case("unverified sync without a cap", degraded,
         setp(["neev", "nees", "cap"], {"applied": False, "bases": []}), "must cap the reading")
    case("unverified sync classified as pass", degraded, setp(["neev", "sync", "n_pass"], 150),
         "must be 0")
    case("cap value does not recompute", degraded,
         lambda r: (r["neev"]["nees"]["cap"].update({"value": 25.0}),
                    r["neev"]["nees"].update({"value": 25.0})), "does not recompute")
    case("cap at the point estimate instead of the low end", degraded,
         lambda r: (r["neev"]["nees"]["cap"].update({"rho": 0.30, "rho_source": "interval_low"}),
                    r["neev"]["nees"].update({"value": 18.3})), "must be the low end")
    case("cap without rho_source", degraded,
         delp(["neev", "nees", "cap", "rho_source"]), "rho_source")
    case("cap without the cluster-mean definition", degraded,
         delp(["neev", "nees", "cap", "mean_size_def"]), "mean_size_def")
    case("upper bound with an interval", degraded,
         setp(["neev", "nees", "interval"], [14.0, 24.0]), "must not carry an interval")

    # NEES and its boundary
    case("NEES exceeds pool", base, setp(["neev", "nees", "value"], 1000.0),
         "exceeds the deduplicated pool")
    case("point value outside interval", base, setp(["neev", "nees", "interval"], [200.0, 260.0]),
         "inside its interval")
    case("computable on unmeasured rho", base,
         lambda r: (r["neev"]["rho"].update({"status": "not_measured"}),
                    r["neev"]["rho"].pop("value", None),
                    r["neev"]["rho"].update({"basis": {"kind": "not_measured"}})),
         "measured or assumed")
    case("assumed rho without a typed basis", degraded,
         lambda r: r["neev"]["rho"].update({"basis": {"note": "同族语料"}}), "typed basis")
    case("borrowed rho without a corpus id", degraded,
         lambda r: r["neev"]["rho"].update({"basis": {"kind": "borrowed_from"}}), "requires corpus_id")
    case("sensitivity range without a range", degraded,
         lambda r: r["neev"]["rho"].update({"basis": {"kind": "sensitivity_range"}}),
         "requires a [low, high] range")
    case("measured rho without an interval", base,
         delp(["neev", "rho", "interval"]), "must carry its interval")
    case("not computable prints a value", unest, setp(["neev", "nees", "value"], 200.0),
         "must not print a value")
    case("zero-variance dominance with a capped value", unest,
         lambda r: r["neev"]["nees"].update({"status": "upper_bound", "value": 20.0}),
         "forbids a point or capped NEES")
    case("frame-wise split with a point value", base, setp(["split"], "frame-wise"),
         "frame-wise split forbids")
    case("split and axis disagree", base, setp(["split"], "environment"), "must agree")

    # diagnostics, zero-failure bound
    case("n_dedup does not match the count", base,
         setp(["neev", "diagnostics", "n_dedup", "value"], 960), "must equal n_distinct_est")
    case("diagnostics without a basis", base,
         delp(["neev", "diagnostics", "n_dedup", "basis"]), "must state how the count was reached")
    case("n_ind below the observed outcomes", base,
         lambda r: r["neev"]["failure_observations"].update({"n": 1200}),
         "cannot exceed the deduplicated count")
    case("dedup n_ind disagrees with the count", base,
         lambda r: r["neev"]["failure_observations"].update({"n": 500, "n_ind": 900}),
         "requires n_ind to equal n_distinct_est")
    case("cluster-count n_ind disagrees with clusters", base,
         lambda r: r["neev"]["failure_observations"].update({"n_ind_basis": "cluster_count"}),
         "to equal the cluster count")
    case("zero-failure bound off the closed form", degraded,
         setp(["neev", "failure_observations", "upper95_by_cluster"], 0.2), "does not recompute")
    case("cluster budget off the closed form", degraded,
         lambda r: r["neev"]["failure_observations"]["cluster_budget"][0].update(
             {"clusters_required": 12}), "clusters_required")
    case("zero-failure budget dropped", degraded,
         delp(["neev", "failure_observations", "cluster_budget"]), "cluster budget")
    case("decision note dropped", degraded,
         delp(["neev", "failure_observations", "decision_note"]), "decision_note")

    # trajectory diversity signal
    case("trajectory signal missing", base, delp(["neev", "trajectory_diversity_signal"]),
         "trajectory_diversity_signal is required")
    case("trajectory computed across embodiments", base,
         lambda r: r["neev"]["trajectory_diversity_signal"].update(
             {"embodiment": {"mode": "across"}, "basis": "computed across embodiments"}),
         "across embodiments is not recommended")
    case("trajectory computed upstream of dedup", base,
         setp(["neev", "trajectory_diversity_signal", "pool"], "raw"), "must be post_dedup")
    case("trajectory signal as a NEES substitute", base,
         setp(["neev", "trajectory_diversity_signal", "note"], "一个补充读数"), "not a substitute")

    # structural faults are typed, and the range follows the type
    case("clock reset recorded as a spike", seg,
         lambda r: r["neev"]["sync"]["structural_fault"].update(
             {"range_basis": "spike_containing_episodes"}),
         "a clock reset shifts the whole segment")
    case("non-monotonic spike treated as a segment", seg,
         lambda r: r["neev"]["sync"]["structural_fault"].update(
             {"type": "non_monotonic_spike", "range_basis": "segment_from_reset_point"}),
         "not a segment fault")
    case("unlocatable range with a guessed extent", unl,
         lambda r: r["neev"]["sync"]["structural_fault"].update({"affected_episodes": 5}),
         "affected_episodes null rather than a guess")

    # alignment rule provenance: where it lives, whether it changed, whether it is a rule
    case("documented rule without provenance", base,
         lambda r: r["neev"]["sync"]["alignment"].update(
             {"rule": {"rule_type": "custom_documented", "source": None, "rule_hash": None,
                       "applicable": True}}), "requires source")
    case("built-in rule without a reset point", base,
         lambda r: r["neev"]["sync"]["alignment"].update(
             {"rule": {"rule_type": "reset_to_zero", "source": None, "rule_hash": None,
                       "applicable": True}}), "reset point episode id")
    case("rule marked inapplicable yet used", base,
         lambda r: r["neev"]["sync"]["alignment"].update(
             {"rule": {"rule_type": "custom_documented", "source": "card.alignment",
                       "rule_hash": "0" * 60 + "1a2b3c4d", "applicable": False}}),
         "applicable true")

    # trajectory diversity: no threshold, but a counting rule and a sample floor
    case("insufficient sample still computed", base,
         lambda r: r["neev"]["trajectory_diversity_signal"].update({"status": "insufficient_sample"}),
         "insufficient_sample is for n_dedup < 50")
    case("mixed embodiment carrying a value", base,
         lambda r: r["neev"]["trajectory_diversity_signal"].update(
             {"embodiment_scope": "mixed"}), "not_computable_mixed_embodiment")
    case("variance cutoff as the main rule", base,
         lambda r: r["neev"]["trajectory_diversity_signal"].update({"dim_rule": "variance_cutoff"}),
         "participation ratio")
    case("spectral entropy presented as the main rule", base,
         lambda r: r["neev"]["trajectory_diversity_signal"].update(
             {"dim_rule": "spectral_entropy"}, ), "participation ratio")
    case("trajectory value presented as cross-corpus comparable", base,
         lambda r: r["neev"]["trajectory_diversity_signal"].update(
             {"note": "轨迹分散度不是 NEES 的替代读数。"}), "cannot be compared across corpora")

    # caps and thresholds origin
    case("cap without a buyer note", degraded,
         delp(["neev", "nees", "cap", "buyer_note"]), "buyer_note")
    case("default package without its acceptance boundary", base,
         lambda r: r["thresholds"].update({"thresholds_origin": "eeo_default_package"}),
         "acceptance_use not_declared_by_buyer")
    case("thresholds origin missing", base, delp(["thresholds", "thresholds_origin"]),
         "thresholds_origin must say")
    case("summary header without the limitation text", base,
         delp(["buyer_summary_use_limitation"]), "buyer_summary_use_limitation")

    # tier and wording
    case("sample tier without a scope statement", degraded, delp(["review", "scope_statement"]),
         "requires review.scope_statement")
    case("sample tier speaking for the corpus", degraded,
         setp(["buyer_summary"], ["这份数据集净有效为 18.3。", "前提一：同步未核验。", "前提二：共 6 簇。"]),
         "must not speak about the whole corpus")
    case("sample tier without a cap basis", degraded,
         lambda r: r["neev"]["nees"]["cap"].update({"bases": ["sync_unverified"]}),
         "must cap the reading with basis sample_scope")
    case("full tier carrying a sample cap", base,
         lambda r: r["neev"]["nees"]["cap"].update({"bases": ["sample_scope"]}),
         "must not carry a sample_scope cap")

    # unit, canonical text
    case("unit is a sample", base, setp(["neev", "nees", "unit"], "sample"), "must be 'episode'")
    case("use limitation rewritten", base,
         setp(["use_limitation", "zh"], "本核验结论可作为采购依据。"), "canonical sentence")
    case("reference note dropped", base,
         setp(["reference_note", "zh"], "本记录符合 YD/T 6771—2026。"), "canonical sentence")
    case("buyer summary without a continuity line", base,
         lambda r: r["buyer_summary"].pop(), "stream-continuity")
    case("six lines in the buyer summary", base,
         setp(["buyer_summary"], ["a", "b", "c", "d", "e", "f"]), "three to five")
    case("unknown top-level field", base, setp(["score"], 88), "unknown top-level fields")

    case("multi-task corpus published pooled", base,
         lambda r: r["neev"]["trajectory_diversity_signal"]["stratification"].update(
             {"task_count": 3, "mode": "pooled"}), "per stratum")
    case("stratified reading without per-stratum entries", base,
         lambda r: r["neev"]["trajectory_diversity_signal"]["stratification"].update(
             {"mode": "stratified", "n_strata": 2, "task_count": 2, "per_stratum": None}),
         "per_stratum entries")
    case("effective dimension dropped", base,
         delp(["neev", "trajectory_diversity_signal", "effective_dim"]), "effective_dim")
    case("spectral entropy mixed into the main count", base,
         lambda r: r["neev"]["trajectory_diversity_signal"].update(
             {"spectral_entropy": {"value": 5.2, "role": "primary"}}), "supplementary")

    # structural fault typing, spike extent and the unverified boundary
    case("identified fault carried as unverified", seg,
         setp(["neev", "sync", "status"], "unverified"), "an identified defect")
    case("structural fault without its event count", seg,
         delp(["neev", "sync", "structural_fault", "n_events"]), "n_events")
    case("spike crossing a boundary counted as an affected episode", seg,
         lambda r: r["neev"]["sync"]["structural_fault"].update(
             {"type": "non_monotonic_spike", "n_events": 1, "affected_episodes": 0,
              "range_basis": "spike_containing_episodes", "stream_continuity_finding": False}),
         "spike_crossing_no_internal_break")
    case("spike affects more than two episodes", seg,
         lambda r: r["neev"]["sync"]["structural_fault"].update(
             {"type": "non_monotonic_spike", "n_events": 1, "affected_episodes": 3,
              "range_basis": "spike_containing_episodes"}), "0, 1 or 2 episodes")

    # tau rule and default package
    case("tau off its declared period", base,
         lambda r: r["thresholds"]["sync"].update({"sampled_stream_period_ms": 33.0}),
         "does not recompute")
    case("unknown pairing policy without a convention", base,
         lambda r: r["thresholds"]["sync"].update(
             {"pairing_policy": "unknown", "tau_rule": "derived_from_pairing_policy"}),
         "explicit convention")
    case("pairing policy contradicted by its factor", base,
         lambda r: r["thresholds"]["sync"].update(
             {"pairing_policy": "zero_order_hold"}),
         "implies tau_factor 1.0")
    case("default package without its notice", base,
         lambda r: r["thresholds"].update(
             {"thresholds_origin": "eeo_default_package",
              "sync": {"tau_ms": 2, "tau_rule": "half_shortest_stream_period", "tau_ratio": 0.5,
                       "shortest_stream_period_ms": 4, "m": 3, "declared_by": "buyer",
                       "basis": "default", "m_origin": "eeo_default",
                       "sensitivity": [{"tau_ms": 2, "w": 0.95, "m": 3, "n_fail": 0,
                                        "n_degraded": 0},
                                       {"tau_ms": 4, "w": 0.90, "m": 3, "n_fail": 0,
                                        "n_degraded": 0}]},
              "dedup": {"w": 0.95, "declared_by": "buyer", "basis": "default",
                        "sensitivity": [{"w": 0.95, "n_duplicate_copies": 1},
                                        {"w": 0.90, "n_duplicate_copies": 2}]}}),
         "no buyer declaration was obtained")

    mt = docs["record-example-multitask"]
    case("multi-task pooled dimension printed bare", mt,
         setp(["neev", "trajectory_diversity_signal", "effective_dim"], 7.0),
         "bare pooled dimension")
    case("multi-task total without its between-task share", mt,
         delp(["neev", "trajectory_diversity_signal", "between_task_share"]),
         "must also print between_task_share")
    case("stratum below the floor still prints a dimension", mt,
         lambda r: r["neev"]["trajectory_diversity_signal"]["stratification"]["per_stratum"][0].update(
             {"n_dedup": 30}), "per stratum")
    case("stratum median does not recompute", mt,
         setp(["neev", "trajectory_diversity_signal", "stratum_summary", "median"], 7.0),
         "stratum_summary.median")
    case("multi-task summary falls back to a bare total", mt,
         setp(["buyer_summary"], ["总结论 7.0。", "前提一：同步已核验。", "前提二：三任务。"]),
         "within-stratum median")
    case("default package notice omits the acceptance bar", base,
         lambda r: (r["thresholds"].update({"thresholds_origin": "eeo_default_package",
                                            "acceptance_use": "not_declared_by_buyer"}),
                    r["thresholds"]["sync"].update({"pairing_policy": "nearest_neighbor"}),
                    r["thresholds"].update({"default_package_notice": {"zh": "默认套餐。", "en": "x"}})),
         "may not serve as an acceptance finding")
    case("default package without a sensitivity headline", base,
         lambda r: (r["thresholds"].update({"thresholds_origin": "eeo_default_package",
                                            "acceptance_use": "not_declared_by_buyer"}),
                    r["thresholds"]["sync"].update({"pairing_policy": "nearest_neighbor"}),
                    r["thresholds"].update({"default_package_notice": {
                        "zh": "本次采用默认套餐，未获买方声明，不得作为验收判定依据；"
                              "验收方须自行声明阈值后重跑。", "en": "x"}})),
         "sensitivity movement in the summary")

    case("chain unverified exceeds the pool", base,
         lambda r: r["neev"]["chain"].update({"sync_unverified": 1300}),
         "cannot exceed chain.sync_filtered")
    case("calibration status missing", base,
         delp(["neev", "dedup", "calibration_status"]), "calibration_status")
    case("unestablished calibration claims an object", base,
         lambda r: (r["neev"]["dedup"].update({"calibration_status": "not_established"}),
                    r["neev"]["dedup"].update({"calibration": gate["neev"]["dedup"]["calibration"]})),
         "must be null while calibration_status is not_established")
    case("established calibration missing", gate,
         setp(["neev", "dedup", "calibration"], None),
         "calibration is required when calibration_status is established")
    case("binding names a fixture without a calibration", base,
         setp(["neev", "dedup", "metric", "threshold_binding", "calibration_fixture_id"],
              "dedup-calib-synthetic"), "must be null while")
    case("calibration below the positive-pair floor", gate,
         setp(["neev", "dedup", "calibration", "n_positive_pairs"], 20),
         "at least 59 known duplicate pairs")
    case("calibration merging distinct episodes", gate,
         lambda r: r["neev"]["dedup"]["calibration"].update(
             {"n_false_merge": 12, "false_merge_rate": 0.2}),
         "false_merge_rate must equal")
    case("calibration upper bound above five percent", gate,
         lambda r: r["neev"]["dedup"]["calibration"].update(
             {"n_false_merge": 1, "false_merge_rate": 0.016949,
              "upper95_false_merge_rate": 0.08}),
         "upper95_false_merge_rate")
    case("calibration not actually executed", gate,
         setp(["neev", "dedup", "calibration", "executed"], False), "executed must be true")
    case("calibration fixture hash missing", gate,
         delp(["neev", "dedup", "calibration", "fixture_hash"]), "fixture_hash is required")
    case("threshold binding disagrees with family", base,
         setp(["neev", "dedup", "metric", "threshold_binding", "metric"], "perceptual_hash"),
         "must equal metric.family")
    case("threshold binding W drifts from thresholds", base,
         setp(["neev", "dedup", "metric", "threshold_binding", "w"], 0.97),
         "must equal thresholds.dedup.w")
    case("chain filtered not an equation", base,
         lambda r: (r["neev"]["chain"].update({"sync_filtered": 1035}),
                    r["neev"]["sync"].update({"n_pass": 1025, "n_unverified": 5})),
         "must equal n_pass + n_unverified")
    case("dimension code without its prefix", base,
         lambda r: (r["dimensions"][0].update({"id": "D1"}),
                    r["scope_declaration"].update({"dimension_code_note": "D1–D5b 局部代号，不是 crosswalk。"})),
         "DSR- prefix")
    case("global tau note hides its bias", base,
         lambda r: r["thresholds"]["sync"].update({"global_tau_note": "全局 τ 是简化。"}),
         "direction of the bias")
    case("calibration not passed", gate,
         setp(["neev", "dedup", "calibration", "passed"], False), "passed must be true")
    case("metric family unnamed", base,
         delp(["neev", "dedup", "metric", "family"]), "family")
    case("stream continuity count without boundaries", base,
         lambda r: r["neev"]["sync"]["stream_continuity_findings"].update(
             {"count": 2, "boundaries": None}), "one entry per finding")
    case("continuity note claims a NEES effect", base,
         setp(["neev", "sync", "stream_continuity_findings", "note"], "计入 NEES"),
         "does not enter NEES")
    case("scope declaration dropped", base, delp(["scope_declaration"]),
         "scope_declaration is required")
    case("label consistency quietly assumed", base,
         lambda r: r["scope_declaration"]["label_consistency"].update({"status": "checked"}),
         "must be not_assessed")
    case("dimension codes reused as a crosswalk", base,
         lambda r: r["scope_declaration"].update({"dimension_code_note": "与 YD/T 6771 一一对应。"}),
         "not a crosswalk")
    case("decision mapping dropped", base,
         delp(["neev", "trajectory_diversity_signal", "decision_supports"]),
         "decision_supports must name the decision")
    case("decision overreach", base,
         lambda r: r["neev"]["trajectory_diversity_signal"].update(
             {"decision_does_not_support": "可用于判断策略优劣。"}), "does not answer")
    case("spike crossing leaves no continuity trace", seg,
         lambda r: (r["neev"]["sync"]["structural_fault"].update(
             {"type": "non_monotonic_spike", "n_events": 1, "affected_episodes": 0,
              "range_basis": "spike_crossing_no_internal_break", "stream_continuity_finding": True}),
                    r["neev"]["sync"].update({"n_alignment_excluded": 0, "n_pass": 440}),
                    r["neev"]["sync"]["alignment"].update({"outcome": "not_required"})),
         "at least one continuity finding")

    obs_cases = []

    def scase(name, mutate, expect):
        doc = copy.deepcopy(obs_base)
        mutate(doc)
        obs_cases.append((name, doc, expect))

    scase("model version dropped", lambda d: d["producer"].pop("model_version"),
          "model_version is required")
    scase("producer declares an external dependency",
          lambda d: d["producer"].update({"external_dependency": True}),
          "no external timing dependency")
    scase("observation names an external tool",
          lambda d: d.update({"tool": {"name": "some-timing-cli"}}),
          "must not name an external tool")
    scase("degraded below the band",
          lambda d: d["episodes"][2].update({"verdict": "degraded", "worst_skew_ms": 31.0}),
          "degraded outside its band")
    scase("pass above tolerance",
          lambda d: d["episodes"][0].update({"worst_skew_ms": 99.0}), "above tau")
    scase("fail on a non-fatal episode inside the band",
          lambda d: d["episodes"][1].update({"verdict": "fail", "worst_skew_ms": 12.0}),
          "fail must sit above the degraded band")
    scase("clock reset carried as pass",
          lambda d: d["episodes"][2].update({"verdict": "pass", "worst_skew_ms": 20.0,
                                             "violations": [{"type": "clock_reset", "count": 1}]}),
          "structural fault")
    scase("unknown violation type",
          lambda d: d["episodes"][2]["violations"][0].update({"type": "mystery"}),
          "known type")

    failed = 0
    for name, rec, expect in cases:
        errs = check(rec)
        if not errs:
            failed += 1
            print(f"  FAIL {name}: accepted, should have been rejected")
        elif not any(expect in e for e in errs):
            failed += 1
            print(f"  FAIL {name}: rejected for the wrong reason: {errs[0]}")
        else:
            print(f"  ok   {name}")
    for name, doc, expect in obs_cases:
        errs = check_observation(doc)
        if not errs:
            failed += 1
            print(f"  FAIL {name}: accepted, should have been rejected")
        elif not any(expect in e for e in errs):
            failed += 1
            print(f"  FAIL {name}: rejected for the wrong reason: {errs[0]}")
        else:
            print(f"  ok   {name}")

    total = len(cases) + len(obs_cases)
    if failed:
        print(f"self-test: {total - failed}/{total} mutations rejected as intended")
        return 1
    print(f"self-test: {total}/{total} mutations rejected as intended")
    return 0


def main(argv):
    if len(argv) < 2:
        print("usage: validate_record.py <record.json> [...] | --sync <observation.json> [...] | "
              "--self-test", file=sys.stderr)
        return 2
    paths = argv[1:]
    mode = "record"
    if paths[0] == "--self-test":
        return run_self_test(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) +
                             "/schema/examples")
    if paths[0] == "--sync":
        mode = "sync"
        paths = paths[1:]
    if not paths:
        print("usage error: --sync needs at least one file", file=sys.stderr)
        return 2

    bad = 0
    for path in paths:
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"{path}: cannot read: {exc}", file=sys.stderr)
            bad += 1
            continue
        errs = check_observation(doc) if mode == "sync" else check(doc)
        if errs:
            bad += 1
            print(f"{path}: invalid", file=sys.stderr)
            for e in errs:
                print(f"  - {e}", file=sys.stderr)
        else:
            print(f"{path}: ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
