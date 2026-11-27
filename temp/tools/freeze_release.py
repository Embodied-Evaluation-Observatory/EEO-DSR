#!/usr/bin/env python3
"""Freeze one DSR release manifest. Refuses to overwrite a release.

The manifest lists every tracked file outside `releases/` and `SHA256SUMS`, with size and sha256.
It is committed before the tag is created; the tag then points at a commit that carries the
frozen list. Corrections create a new version, never mutate this manifest.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = ("releases/", "SHA256SUMS")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked():
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    paths = [p for p in raw.decode("utf-8").split("\0") if p]
    return sorted(p for p in paths if not p.startswith(SKIP))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, help="release id, e.g. v0.5")
    ap.add_argument("--tag", required=True, help="annotated tag name, e.g. v0.5")
    ap.add_argument("--method", default="EEO-DSR-V0.5")
    args = ap.parse_args()

    rel_dir = os.path.join(ROOT, "releases", args.version)
    manifest_path = os.path.join(rel_dir, "manifest.json")
    if os.path.exists(rel_dir):
        print(f"REFUSED: {rel_dir} already exists. Releases are immutable.", file=sys.stderr)
        print("To correct a release, publish a new version and state the correction.",
              file=sys.stderr)
        return 2

    entries = []
    for rel in tracked():
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            print(f"MISSING: {rel}", file=sys.stderr)
            return 3
        entries.append({"file": rel, "bytes": os.path.getsize(p), "sha256": sha256(p)})

    os.makedirs(rel_dir)
    manifest = {
        "module": "EEO-DSR",
        "release": args.version,
        "tag": args.tag,
        "method_version": args.method,
        "frozen_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "files": entries,
        "policy": ("This manifest is committed before the tag. The tag is annotated and is "
                   "never moved; corrections are new versions."),
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"froze {args.version}: {len(entries)} files -> releases/{args.version}/manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
