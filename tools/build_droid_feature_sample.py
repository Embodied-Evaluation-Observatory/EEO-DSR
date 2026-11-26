#!/usr/bin/env python3
"""Build a stratified DROID state/action feature sample from public HDF5.

This is a real-corpus sampling tool, not a record issuer. It reads the
public DROID metadata object list, samples episodes, downloads trajectory.h5
for each sampled episode, extracts two fixed representations, and discards
the HDF5 bytes. The sample is for representation sensitivity and hard-
negative calibration; it does not issue a dedup count or an ICR interval.

Representations:
  summary: per-signal mean/std/min/max/first/last/mean-abs-delta
  traj16:  16 equal-time points for each signal, flattened

Signals: observation joint positions (7), joint velocities (7), gripper
position (1), action joint position (7), action joint velocity (7).
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, re, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import numpy as np
import h5py

PAT = re.compile(r"metadata_(.*)\.json$")
SIGS = [
    "observation/robot_state/joint_positions",
    "observation/robot_state/joint_velocities",
    "observation/robot_state/gripper_position",
    "action/joint_position",
    "action/joint_velocity",
]


def object_url(name: str) -> str:
    return ("https://storage.googleapis.com/download/storage/v1/b/gresearch/o/"
            + urllib.parse.quote(name, safe="") + "?alt=media")


def fetch(url: str, tries: int = 4) -> bytes:
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def stats(x: np.ndarray) -> np.ndarray:
    d = np.diff(x, axis=0)
    return np.concatenate([x.mean(0), x.std(0), x.min(0), x.max(0), x[0], x[-1], np.abs(d).mean(0)])


def resample(x: np.ndarray, k: int = 16) -> np.ndarray:
    if x.shape[0] == 1:
        return np.repeat(x, k, axis=0)
    pos = np.linspace(0, x.shape[0] - 1, k)
    lo = np.floor(pos).astype(int); hi = np.ceil(pos).astype(int)
    w = (pos - lo)[:, None]
    return x[lo] * (1 - w) + x[hi] * w


def extract(buf: bytes):
    with h5py.File(io.BytesIO(buf), "r") as f:
        arrs = [np.asarray(f[k], dtype=float) for k in SIGS]
    n = min(a.shape[0] for a in arrs)
    arrs = [a[:n] for a in arrs]
    arrs = [a.reshape(n, -1) if a.ndim == 1 else a for a in arrs]
    if n < 4:
        raise ValueError("trajectory shorter than 4")
    summary = np.concatenate([stats(a) for a in arrs])
    traj = np.concatenate([resample(a).reshape(-1) for a in arrs])
    return summary.astype(np.float32), traj.astype(np.float32), n


def one(row, obj):
    meta = json.loads(fetch(object_url(obj["name"])))
    if str(meta.get("uuid")) != row["uuid"]:
        raise ValueError("uuid mismatch")
    base = obj["name"].rsplit("/", 1)[0]
    lab = base.split("/")[3]
    h5 = "robotics/droid_raw/1.0.1/" + lab + "/" + meta["hdf5_path"]
    buf = fetch(object_url(h5))
    summary, traj, n = extract(buf)
    return {"uuid": row["uuid"], "scene_id": row["scene_id"], "building": row["building"],
            "current_task": row["current_task"], "lab": row["lab"], "outcome": row["success"],
            "trajectory_length_meta": meta.get("trajectory_length"), "n": n,
            "h5_sha256": hashlib.sha256(buf).hexdigest(), "summary": summary, "traj": traj}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-meta", required=True)
    ap.add_argument("--metadata-objects", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seed", type=int, default=20261130)
    args = ap.parse_args()
    rows = list(csv.DictReader(open(args.raw_meta, newline="")))
    objs = {PAT.search(o["name"]).group(1): o for o in json.load(open(args.metadata_objects)) if PAT.search(o["name"])}
    rows = [r for r in rows if r["uuid"] in objs]
    # Reproducible uniform sample; group labels are retained for post-stratified pairs.
    rng = np.random.default_rng(args.seed)
    idx = rng.choice(len(rows), size=min(args.n, len(rows)), replace=False)
    sample = [rows[int(i)] for i in idx]
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    results, failures = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut = {ex.submit(one, r, objs[r["uuid"]]): r["uuid"] for r in sample}
        for i, f in enumerate(as_completed(fut), 1):
            try:
                results.append(f.result())
            except Exception as e:
                failures.append({"uuid": fut[f], "error": str(e)[:160]})
            if i % 100 == 0:
                print(json.dumps({"done": i, "ok": len(results), "fail": len(failures)}), flush=True)
    results.sort(key=lambda r: r["uuid"])
    ids = np.array([r["uuid"] for r in results], dtype=object)
    summary = np.vstack([r["summary"] for r in results])
    traj = np.vstack([r["traj"] for r in results])
    scene = np.array([r["scene_id"] for r in results], dtype=object)
    np.savez_compressed(out / "features_summary.npz", episode_id=ids, features=summary, cluster_id=scene)
    np.savez_compressed(out / "features_traj16.npz", episode_id=ids, features=traj, cluster_id=scene)
    with open(out / "sample_meta.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["uuid", "scene_id", "building", "current_task", "lab", "outcome", "trajectory_length_meta", "n", "h5_sha256"])
        for r in results: w.writerow([r["uuid"], r["scene_id"], r["building"], r["current_task"], r["lab"], r["outcome"], r["trajectory_length_meta"], r["n"], r["h5_sha256"]])
    manifest = {"requested": args.n, "ok": len(results), "failed": len(failures), "seed": args.seed,
                "raw_meta_sha256": hashlib.sha256(Path(args.raw_meta).read_bytes()).hexdigest(),
                "metadata_objects_sha256": hashlib.sha256(Path(args.metadata_objects).read_bytes()).hexdigest(),
                "representations": {"summary_dims": int(summary.shape[1]), "traj16_dims": int(traj.shape[1])},
                "failures": failures[:50]}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": len(results), "failed": len(failures), "summary_dims": summary.shape[1], "traj_dims": traj.shape[1]}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
