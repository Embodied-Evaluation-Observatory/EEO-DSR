#!/usr/bin/env python3
"""Run the full check set: validator self-test, every example, the observation, and JSON Schema."""
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAL = os.path.join(ROOT, "tools", "validate_record.py")
DRIVER = os.path.join(ROOT, "tools", "dataset_driver.py")


def run(args):
    return subprocess.run([sys.executable, VAL] + args, capture_output=True, text=True)


def main():
    failures = []

    dr = subprocess.run([sys.executable, DRIVER, "--self-test"], capture_output=True, text=True)
    for line in (dr.stdout or "").strip().splitlines():
        print(line)
    if dr.returncode != 0:
        failures.append("dataset-driver")

    st = run(["--self-test"])
    print(st.stdout.strip().splitlines()[-1] if st.stdout else "self-test: no output")
    if st.returncode != 0:
        failures.append("self-test")

    pre = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "precheck_local.py"),
                          "--self-test"], capture_output=True, text=True)
    print(pre.stdout.strip() if pre.stdout else "precheck self-test: no output")
    if pre.returncode != 0:
        failures.append("precheck-self-test")

    preg = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "validate_precheck_register.py"),
                          os.path.join(ROOT, "entry", "precheck-register.json")],
                         capture_output=True, text=True)
    print(preg.stdout.strip() if preg.stdout else "precheck-register: no output")
    if preg.returncode != 0:
        failures.append("precheck-register")

    for f in sorted(glob.glob(os.path.join(ROOT, "schema", "examples", "record-example*.json"))):
        r = run([f])
        name = os.path.basename(f)
        print(f"{name}: {'ok' if r.returncode == 0 else 'FAIL'}")
        if r.returncode != 0:
            failures.append(name)

    obs = os.path.join(ROOT, "schema", "examples", "sync-observation-example.json")
    r = run(["--sync", obs])
    print(f"sync-observation-example.json: {'ok' if r.returncode == 0 else 'FAIL'}")
    if r.returncode != 0:
        failures.append("observation")

    try:
        import jsonschema
        rs = json.load(open(os.path.join(ROOT, "schema", "record.schema.json"), encoding="utf-8"))
        osch = json.load(open(os.path.join(ROOT, "schema", "sync-observation.schema.json"),
                              encoding="utf-8"))
        for f in sorted(glob.glob(os.path.join(ROOT, "schema", "examples", "record-example*.json"))):
            jsonschema.validate(json.load(open(f, encoding="utf-8")), rs)
        jsonschema.validate(json.load(open(obs, encoding="utf-8")), osch)
        print("jsonschema: ok")
    except ImportError:
        print("jsonschema: skipped (package not installed)")
    except Exception as exc:
        print(f"jsonschema: FAIL {exc}")
        failures.append("jsonschema")

    if failures:
        print("failures: " + ", ".join(failures))
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
