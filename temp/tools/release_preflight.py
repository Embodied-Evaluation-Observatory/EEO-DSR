#!/usr/bin/env python3
"""Run the DSR release gate and write releases/<version>/preflight.json.

The record is a file, not a claim. It refuses to overwrite an existing gate record.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args):
    p = subprocess.run([sys.executable] + args, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, help="release id, e.g. v0.5")
    ap.add_argument("--w", type=float, default=0.95)
    args = ap.parse_args()

    rel_dir = os.path.join(ROOT, "releases", args.version)
    manifest_path = os.path.join(rel_dir, "manifest.json")
    out_path = os.path.join(rel_dir, "preflight.json")
    if not os.path.isfile(manifest_path):
        print(f"MISSING: releases/{args.version}/manifest.json", file=sys.stderr)
        return 2
    if os.path.exists(out_path):
        print(f"REFUSED: releases/{args.version}/preflight.json already exists. "
              f"A gate record is immutable.", file=sys.stderr)
        return 2

    manifest = json.load(open(manifest_path, encoding="utf-8"))
    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "status": "PASS" if ok else "BLOCK", "detail": detail})
        return ok

    bad = []
    for e in manifest["files"]:
        p = os.path.join(ROOT, e["file"])
        if not os.path.isfile(p):
            bad.append(f"missing:{e['file']}")
        elif os.path.getsize(p) != e["bytes"]:
            bad.append(f"size:{e['file']}")
        elif sha256(p) != e["sha256"]:
            bad.append(f"sha256:{e['file']}")
    check("manifest", not bad, "; ".join(bad))

    sums_path = os.path.join(ROOT, "SHA256SUMS")
    sum_bad = []
    listed = set()
    if not os.path.isfile(sums_path):
        sum_bad.append("SHA256SUMS missing")
    else:
        for line in open(sums_path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            digest, rel = line.split("  ", 1)
            listed.add(rel)
            p = os.path.join(ROOT, rel)
            if not os.path.isfile(p):
                sum_bad.append(f"missing:{rel}")
            elif sha256(p) != digest:
                sum_bad.append(f"sha256:{rel}")
    needed = {e["file"] for e in manifest["files"]}
    if not needed.issubset(listed):
        sum_bad.append("SHA256SUMS omits: " + ", ".join(sorted(needed - listed)))
    check("checksums", not sum_bad, "; ".join(sum_bad))

    code, out = run(["tools/validate_record.py", "--self-test"])
    check("self-test", code == 0, out.splitlines()[-1] if out else "")
    code, out = run(["tools/run_all_checks.py"])
    check("examples", code == 0, out.splitlines()[-1] if out else "")
    code, out = run(["tools/cosine_threshold_smoke.py", "--w", str(args.w)])
    check("smoke", code == 0,
          "cosine smoke ran; this is not a detector gate" if code == 0 else out[-500:])

    result = "PASS" if all(c["status"] == "PASS" for c in checks) else "BLOCK"
    record = {
        "release": args.version,
        "tag": manifest.get("tag"),
        "run_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "checks": checks,
        "result": result,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
