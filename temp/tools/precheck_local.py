#!/usr/bin/env python3
"""Local pre-check log: tool log + input hash, never a record.

This script runs on the submitter's machine. It does not upload input files,
does not contact EEO-DSR, and does not create a record, record hash, summary,
finding, verdict, or letterhead. Its only output is a JSON log carrying the
machine marker `pre_check_not_a_record`. The official schema rejects any
document carrying that marker; removing the marker still fails because the log
has none of the required record fields.

Typical use:
  python3 tools/precheck_local.py \
    --input sample_manifest.csv --tool screen_cards.py \
    --command 'python3 tools/screen_cards.py --source checks/cards-source.csv' \
    --exit-code 0 --out precheck-log.json

The local `screen_cards.py` run may write its own local output directory. That
directory is not a record and must not be uploaded as one.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys

MARKER = "pre_check_not_a_record"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_log(inputs, tool, command, exit_code):
    records = []
    for path in inputs:
        p = Path(path)
        if not p.is_file():
            raise SystemExit(f"input is not a file: {path}")
        records.append({"path": str(p), "bytes": p.stat().st_size, "sha256": sha256_file(str(p))})
    return {
        MARKER: True,
        "tool": tool,
        "run_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "inputs": records,
        "command": command,
        "tool_exit_code": int(exit_code),
        "notice": ("Local pre-check log only. Not a record. No schema, no record hash, "
                   "no summary, no finding, no verdict, no letterhead. EEO-DSR does not "
                   "receive the input files."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", action="append", default=[],
                    help="local input file; repeat for multiple files")
    ap.add_argument("--tool", default="screen_cards.py")
    ap.add_argument("--command", default="")
    ap.add_argument("--exit-code", type=int, default=0)
    ap.add_argument("--out")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        import subprocess, tempfile
        with tempfile.TemporaryDirectory() as td:
            sample = Path(td) / "sample.csv"
            sample.write_text("dataset_id,url\nexample,https://example.com\n", encoding="utf-8")
            log = Path(td) / "precheck.json"
            payload = build_log([str(sample)], "screen_cards.py", "self-test", 0)
            log.write_text(json.dumps(payload), encoding="utf-8")
            validator = Path(__file__).with_name("validate_record.py")
            marked = subprocess.run([sys.executable, str(validator), str(log)],
                                    capture_output=True, text=True).returncode
            payload.pop(MARKER)
            log.write_text(json.dumps(payload), encoding="utf-8")
            stripped = subprocess.run([sys.executable, str(validator), str(log)],
                                      capture_output=True, text=True).returncode
            assert marked != 0 and stripped != 0, (marked, stripped)
        print("precheck_local self-test: ok (marker rejected; stripped log still rejected)")
        return 0
    if not args.input or not args.out:
        ap.error("--input and --out are required unless --self-test")
    payload = build_log(args.input, args.tool, args.command, args.exit_code)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"marker": MARKER, "out": args.out, "inputs": len(payload["inputs"])},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
