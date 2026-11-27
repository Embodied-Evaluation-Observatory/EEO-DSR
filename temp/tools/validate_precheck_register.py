#!/usr/bin/env python3
"""Validate the public pre-check register: aggregate-only, no names/findings.

Allowed entry fields are exactly period_start, period_end, n_prechecks,
n_formal_entry. Any other field (organisation, submitter, dataset_id, finding,
verdict, log, input_sha256, etc.) is rejected. The register is not a record and
is not a rating.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ALLOWED = {"period_start", "period_end", "n_prechecks", "n_formal_entry"}
FORBIDDEN = {"organisation", "submitter", "dataset_id", "finding", "verdict",
             "log", "input_sha256", "record_sha256", "summary", "verdict_text"}
ROOT_ALLOWED = {"register", "entries", "allowed_fields", "forbidden", "note"}


def parse_date(value):
    try:
        return dt.date.fromisoformat(value)
    except Exception as exc:
        raise ValueError(f"period date must be YYYY-MM-DD: {value!r}") from exc


def validate(doc):
    errors = []
    if not isinstance(doc, dict):
        return ["root must be an object"]
    extra = set(doc) - ROOT_ALLOWED
    if extra:
        errors.append(f"root has disallowed keys: {sorted(extra)}")
    if doc.get("register") != "precheck-aggregate-only":
        errors.append("register must be 'precheck-aggregate-only'")
    entries = doc.get("entries")
    if not isinstance(entries, list):
        return errors + ["entries must be an array"]
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entry {i} must be an object")
            continue
        keys = set(entry)
        bad = keys - ALLOWED
        missing = ALLOWED - keys
        if bad:
            errors.append(f"entry {i} has disallowed fields: {sorted(bad)}")
        if missing:
            errors.append(f"entry {i} missing fields: {sorted(missing)}")
        if bad or missing:
            continue
        try:
            start = parse_date(entry["period_start"])
            end = parse_date(entry["period_end"])
        except ValueError as exc:
            errors.append(f"entry {i}: {exc}")
            continue
        if start > end:
            errors.append(f"entry {i}: period_start after period_end")
        n = entry["n_prechecks"]; m = entry["n_formal_entry"]
        if not isinstance(n, int) or isinstance(n, bool) or n < 0:
            errors.append(f"entry {i}: n_prechecks must be a non-negative integer")
        if not isinstance(m, int) or isinstance(m, bool) or m < 0:
            errors.append(f"entry {i}: n_formal_entry must be a non-negative integer")
        if isinstance(n, int) and isinstance(m, int) and not isinstance(n, bool) and not isinstance(m, bool) and m > n:
            errors.append(f"entry {i}: n_formal_entry cannot exceed n_prechecks")
        # free-text values are not allowed anywhere in an entry
        for key, value in entry.items():
            if key not in ("period_start", "period_end") and not isinstance(value, int):
                errors.append(f"entry {i}: {key} must be an integer")
    return errors


def self_test():
    good = {"register": "precheck-aggregate-only", "entries": [
        {"period_start": "2026-11-01", "period_end": "2026-11-30",
         "n_prechecks": 5, "n_formal_entry": 1}],
        "allowed_fields": sorted(ALLOWED), "forbidden": sorted(FORBIDDEN), "note": "x"}
    bad = json.loads(json.dumps(good))
    bad["entries"][0]["organisation"] = "an SOE"
    bad2 = json.loads(json.dumps(good))
    bad2["entries"][0]["n_formal_entry"] = 9
    assert not validate(good), validate(good)
    assert validate(bad), validate(bad)
    assert validate(bad2), validate(bad2)
    print("precheck-register self-test: ok (extra field and M>N rejected)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not args.path:
        ap.error("path is required unless --self-test")
    doc = json.loads(Path(args.path).read_text(encoding="utf-8"))
    errors = validate(doc)
    if errors:
        for e in errors: print("FAIL:", e)
        return 1
    print("precheck-register: ok")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
