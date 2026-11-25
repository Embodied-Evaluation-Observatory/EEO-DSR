#!/usr/bin/env python3
"""Screen public dataset cards against DSR Phase 0 checks.

Reads checks/cards-source.csv (dataset_id,url), fetches each card once, stores the raw page hash,
parses a fixed structured field set into card_sha256, runs S1-S6, and writes a dated directory:
cards.csv, index.html, README.md, manifest.json and manifest.sha256.

No score, no rating, no ranking. A cell is PASS, FAIL or MISSING. FAIL prints the declared and
recomputed values. MISSING is recorded separately from FAIL, and the summary reports both
distributions rather than collapsing them into "not pass".
"""
import argparse
import csv
import datetime as dt
import email.utils
import hashlib
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPDX = {"mit", "apache-2.0", "cc-by-4.0", "cc-by-sa-4.0", "bsd-3-clause", "gpl-3.0"}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "EEO-DSR/0.4 phase0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(), r.headers.get("Last-Modified")


def parse_last_modified(value):
    if not value:
        return "not available"
    try:
        return email.utils.parsedate_to_datetime(value).date().isoformat()
    except Exception:
        return "not available"


def number(text, key):
    m = re.search(rf'"{key}"\s*:\s*(\d+)', text)
    return int(m.group(1)) if m else None


def parse(card):
    text = card.decode("utf-8", "replace")
    lic = re.search(r"^license:\s*([^\s]+)\s*$", text, re.M)
    info = {
        "total_episodes": number(text, "total_episodes"),
        "total_frames": number(text, "total_frames"),
        "total_tasks": number(text, "total_tasks"),
        "total_videos": number(text, "total_videos"),
        "scene_count": number(text, "scene_count"),
    }
    m = re.search(r'"fps"\s*:\s*([0-9.]+)', text)
    info["fps"] = float(m.group(1)) if m else None
    m = re.search(r'"codebase_version"\s*:\s*"([^"]+)"', text)
    info["version"] = m.group(1) if m else None
    m = re.search(r'"robot_type"\s*:\s*"([^"]+)"', text)
    info["robot_type"] = m.group(1) if m else None
    per_scene = {}
    m = re.search(r'"per_scene_episodes"\s*:\s*\{([^}]*)\}', text)
    if m:
        for k, v in re.findall(r'"([^"]+)"\s*:\s*(\d+)', m.group(1)):
            per_scene[k] = int(v)
    info["per_scene_episodes"] = per_scene or None
    info["scene_id"] = bool(re.search(r'"(scene_id|workstation_id|station_id)"\s*:', text))
    info["license"] = lic.group(1).lower() if lic else None
    info["has_checksum"] = bool(re.search(r'"(sha256|checksum)"\s*:', text))
    declared = {}
    for key in ("frames_per_episode", "seconds_per_episode"):
        m = re.search(rf'"{key}"\s*:\s*([0-9.]+)', text)
        if m:
            declared[key] = float(m.group(1))
    info["declared_ratios"] = declared
    return text, info


def s1(info):
    total = info.get("total_episodes")
    scenes = info.get("scene_count")
    per = info.get("per_scene_episodes")
    if total is None:
        return "MISSING", "卡片未声明 total_episodes"
    if scenes is None:
        return "MISSING", f"声明总数 {total}；卡片未声明 scene_count"
    if not per:
        return "MISSING", f"声明总数 {total}、场景数 {scenes}；卡片未给分场景计数"
    summed = sum(per.values())
    evidence = f"声明总数 {total}，场景数 {scenes}，分场景计数之和 {summed}"
    if len(per) != scenes:
        return "FAIL", evidence + "；场景个数对不上"
    if summed != total:
        return "FAIL", evidence + "；算术不平"
    return "PASS", evidence


def s2(info):
    total = info.get("total_episodes")
    fps = info.get("fps")
    frames = info.get("total_frames")
    declared = info.get("declared_ratios") or {}
    if total is None:
        return "MISSING", "卡片未声明 total_episodes"
    if fps is None:
        return "MISSING", f"声明 {total} episodes；卡片未声明 fps"
    if frames is None:
        return "MISSING", f"声明 {total} episodes、{fps} fps；未给帧数，无法算两个被比值"
    fpe = frames / total
    spe = frames / (total * fps)
    ratio = f"frames/episode={fpe:.2f}，seconds/episode={spe:.2f}"
    if not declared:
        return "MISSING", f"声明 {total} episodes、{frames} frames、{fps} fps；{ratio}；卡片未声明换算率字段"
    failures = []
    for key, value in declared.items():
        calc = fpe if key == "frames_per_episode" else spe
        if abs(value - calc) > max(1e-9, 0.01 * abs(calc)):
            failures.append(f"{key} 声明 {value}，重算 {calc:.4f}")
    if failures:
        return "FAIL", f"{ratio}；" + "；".join(failures)
    return "PASS", f"{ratio}；声明的换算率与重算一致"


def s3(info, last_modified):
    version = info.get("version")
    if version and last_modified != "not available":
        return "PASS", f"版本 {version}；页面修订日期 {last_modified}"
    return "MISSING", f"版本 {version}；页面修订日期 {last_modified}"


def s4(info):
    lic = info.get("license")
    if lic and lic in SPDX:
        return "PASS", f"license: {lic}"
    if lic:
        return "FAIL", f"声明 license: {lic}；非机器可识别标识"
    return "MISSING", "卡片无 license 字段"


def s5(info):
    if info.get("has_checksum"):
        return "PASS", "卡片声明了文件级校验和字段"
    return "MISSING", "卡片未给文件级校验和"


def s6(info):
    if info.get("scene_id"):
        return "PASS", "卡片声明了场景/工位标识"
    return "MISSING", "卡片未给场景/工位标识，无法跨表 join"


def screen(info, last_modified):
    return {"S1": s1(info), "S2": s2(info), "S3": s3(info, last_modified),
            "S4": s4(info), "S5": s5(info), "S6": s6(info)}


def structured(info, dataset_id, retrieval_date):
    fields = ["dataset_id", "version", "total_episodes", "scene_count", "per_scene_episodes",
              "total_frames", "total_tasks", "total_videos", "fps", "license", "retrieval_date"]
    payload = {"dataset_id": dataset_id, "retrieval_date": retrieval_date}
    payload.update({k: info.get(k) for k in fields if k != "dataset_id" and k != "retrieval_date"})
    return payload


def card_hash(payload):
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_bytes(canonical.encode("utf-8")), canonical


def write_cards(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dataset_id", "url", "version", "retrieval_date", "card_last_modified",
                    "page_file", "page_sha256", "card_sha256", "S1", "S2", "S3", "S4", "S5", "S6", "evidence"])
        for r in rows:
            ev = "; ".join(f"{k}: {v[1]}" for k, v in r["checks"].items())
            w.writerow([r["dataset_id"], r["url"], r["version"], r["retrieval_date"],
                        r["card_last_modified"], r["page_file"], r["page_sha256"], r["card_sha256"]] +
                       [r["checks"][f"S{i}"][0] for i in range(1, 7)] + [ev])


def write_readme(path, date, rows, summary):
    lines = [f"# Phase 0 披露度普查 {date}", "",
             summary["hard_sentence"], "",
             summary["sentence"], "",
             "本目录字段由 `tools/screen_cards.py` 自动解析自钉住的页面字节；**没有人工转录**。"
             "每张卡片的原始页面字节存在 `pages/`，其哈希（`page_sha256`）与结构化字段哈希（`card_sha256`）见 `cards.csv`。",
             "",
             "## 集合级可判率", "",
             "| 项 | 可判 (PASS+FAIL)/m | 可判率 | 判定 |",
             "|---|---:|---:|---|"]
    for k, v in summary["judgeability"].items():
        lines.append(f"| {k} | {v['judgeable']}/{summary['cards']} | {v['rate']:.0%} | {v['verdict']} |")
    lines += ["",
              "某项 100% MISSING 时判为不可判，不计入通过。全部行同构时，声明本集合上无区分信号。",
              "可判率是集合上的分布，不是对单张卡片的评级。", "",
              "## 逐项分布", "",
              "；".join(f"{k} PASS {v['PASS']} / FAIL {v['FAIL']} / MISSING {v['MISSING']}"
                       for k, v in summary["by_check"].items()), "",
              "S1 测的是分场景计数之和与声明总数；卡片没有分场景计数时，S1 记 MISSING，不是 FAIL。",
              "S2 只有在卡片声明 `frames_per_episode` 或 `seconds_per_episode` 且与重算一致时才 PASS；"
              "只给条数、帧数与 fps 不够。", "",
              "`manifest.sha256` 钉住 `manifest.json`；`manifest.json` 列出输入与三个输出文件的哈希。", ""]
    for r in rows:
        lines.append(f"- `{r['dataset_id']}`：{r['url']}  page `{r['page_sha256']}`  card `{r['card_sha256']}`")
    lines += ["", "本页只报告披露与算术，不构成核验结论，不说明语料可用性。"]
    open(path, "w", encoding="utf-8").write("\n".join(lines))

def write_html(path, date, rows, summary):
    esc = html.escape
    head = f"""<!doctype html><meta charset="utf-8"><title>Phase 0 披露度普查 {date}</title>
<style>body{{font:14px/1.5 system-ui,sans-serif;margin:32px;max-width:1200px}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccc;padding:6px;vertical-align:top}}
.pass{{color:#176b2c}}.fail{{color:#a11}}.missing{{color:#777}}code{{font-size:12px}}</style>"""
    body = [head, f"<h1>Phase 0 披露度普查 {date}</h1>",
            f"<p><b>{esc(summary['hard_sentence'])}</b></p>",
            "<p>披露度普查只报告页面上的披露与算术，不出具合格结论，不做数据集排名，不做资产估值。</p>",
            "<p>本记录不以任何标准为判定依据。披露度普查只做页面披露，不是符合性检查。</p>",
            f"<p>{esc(summary['sentence'])}</p>",
            "<p>某项 100% MISSING 时判为不可判，不计入通过；全部行同构时，本集合上无区分信号。</p>",
            "<table><tr><th>项</th><th>可判</th><th>可判率</th><th>判定</th></tr>"]
    for k, v in summary["judgeability"].items():
        body.append(f"<tr><td>{k}</td><td>{v['judgeable']}/{summary['cards']}</td>"
                    f"<td>{v['rate']:.0%}</td><td>{esc(v['verdict'])}</td></tr>")
    body += ["</table>", "<table><tr><th>卡片</th><th>S1</th><th>S2</th><th>S3</th><th>S4</th><th>S5</th><th>S6</th></tr>"]
    for r in rows:
        cells = [f"<td><a href='{esc(r['url'])}'>{esc(r['dataset_id'])}</a><br>"
                 f"<code>page {r['page_sha256'][:16]}…</code><br>"
                 f"<code>card {r['card_sha256'][:16]}…</code></td>"]
        for i in range(1, 7):
            st, ev = r["checks"][f"S{i}"]
            cells.append(f"<td class='{st.lower()}'><b>{st}</b><br>{esc(ev)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    body += ["</table>", "<p>按 dataset_id 字母序，不按失败数。</p></body>"]
    open(path, "w", encoding="utf-8").write("\n".join(body))

def self_test():
    """Exercise the S1 arithmetic and S4 licence branches without network access."""
    ok = True
    cases = [
        ("S1 balanced", s1({"total_episodes": 6, "scene_count": 3,
                            "per_scene_episodes": {"a": 1, "b": 2, "c": 3}}), "PASS"),
        ("S1 unbalanced", s1({"total_episodes": 7, "scene_count": 3,
                              "per_scene_episodes": {"a": 1, "b": 2, "c": 3}}), "FAIL"),
        ("S1 missing count", s1({"total_episodes": 6, "scene_count": 3,
                                 "per_scene_episodes": None}), "MISSING"),
        ("S2 no declared ratio", s2({"total_episodes": 10, "total_frames": 100, "fps": 10,
                                    "declared_ratios": {}}), "MISSING"),
        ("S2 declared ratio matches", s2({"total_episodes": 10, "total_frames": 100, "fps": 10,
                                         "declared_ratios": {"frames_per_episode": 10.0}}), "PASS"),
        ("S2 declared ratio drifts", s2({"total_episodes": 10, "total_frames": 100, "fps": 10,
                                        "declared_ratios": {"frames_per_episode": 11.0}}), "FAIL"),
        ("S4 known licence", s4({"license": "apache-2.0"}), "PASS"),
        ("S4 unknown licence", s4({"license": "apache"}), "FAIL"),
    ]
    for name, (status, _), expected in cases:
        if status != expected:
            ok = False
            print(f"FAIL {name}: got {status}, expected {expected}")
    print("screen_cards self-test: ok" if ok else "screen_cards self-test: FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=os.path.join(ROOT, "checks", "cards-source.csv"))
    ap.add_argument("--date", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    ap.add_argument("--out", default="")
    ap.add_argument("--self-test", action="store_true", help="run local branch tests; no network")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    if not os.path.isfile(args.source):
        print(f"MISSING source: {args.source}", file=sys.stderr)
        return 2
    outdir = args.out or os.path.join(ROOT, "checks", "dataset", args.date)
    if os.path.exists(outdir):
        print(f"REFUSED: {outdir} exists. Use a new dated directory; results are not overwritten.",
              file=sys.stderr)
        return 2

    with open(args.source, newline="", encoding="utf-8") as f:
        entries = list(csv.DictReader(f))
    if not entries:
        print("source list is empty", file=sys.stderr)
        return 2
    if not all(e.get("dataset_id") and e.get("url") for e in entries):
        print("source list needs dataset_id and url on every row", file=sys.stderr)
        return 2

    rows = []
    for e in entries:
        raw, last_modified = fetch(e["url"])
        _, info = parse(raw)
        mod = parse_last_modified(last_modified)
        payload = structured(info, e["dataset_id"], args.date)
        chash, canonical = card_hash(payload)
        page_file = os.path.join("pages", e["dataset_id"].replace("/", "__") + ".md")
        rows.append({
            "dataset_id": e["dataset_id"], "url": e["url"], "version": info.get("version"),
            "retrieval_date": args.date, "card_last_modified": mod,
            "page_file": page_file, "page_sha256": sha256_bytes(raw), "card_sha256": chash,
            "raw": raw,
            "structured_canonical": canonical, "checks": screen(info, mod),
        })
    rows.sort(key=lambda r: r["dataset_id"])

    os.makedirs(outdir)
    for r in rows:
        page_path = os.path.join(outdir, r["page_file"])
        os.makedirs(os.path.dirname(page_path), exist_ok=True)
        with open(page_path, "wb") as f:
            f.write(r["raw"])
    cards_path = os.path.join(outdir, "cards.csv")
    html_path = os.path.join(outdir, "index.html")
    readme_path = os.path.join(outdir, "README.md")
    write_cards(cards_path, rows)

    n_fail = sum(1 for r in rows if any(v[0] == "FAIL" for v in r["checks"].values()))
    n_missing = sum(1 for r in rows if any(v[0] == "MISSING" for v in r["checks"].values()))
    n_both = sum(1 for r in rows if any(v[0] == "FAIL" for v in r["checks"].values())
                 and any(v[0] == "MISSING" for v in r["checks"].values()))
    by_check = {f"S{i}": {st: sum(1 for r in rows if r["checks"][f"S{i}"][0] == st)
                          for st in ("PASS", "FAIL", "MISSING")} for i in range(1, 7)}
    judgeability = {}
    for i in range(1, 7):
        v = by_check[f"S{i}"]
        judgeable = v["PASS"] + v["FAIL"]
        rate = judgeable / len(rows) if rows else 0.0
        if judgeable == 0:
            verdict = "不可判"
        elif v["PASS"] == judgeable or v["FAIL"] == judgeable:
            verdict = "无可区分信号"
        else:
            verdict = "有区分"
        judgeability[f"S{i}"] = {"judgeable": judgeable, "rate": rate,
                                 "verdict": verdict,
                                 "discriminating": bool(v["PASS"] and v["FAIL"])}
    patterns = {tuple(r["checks"][f"S{i}"][0] for i in range(1, 7)) for r in rows}
    homogeneous = len(patterns) == 1
    hard_sentence = f"本集合 0 项 FAIL 不代表卡片自洽；S1 在 {len(rows)} 张卡上全部不可判。"
    if by_check["S1"]["MISSING"] != len(rows):
        hard_sentence = (f"本集合 0 项 FAIL 不代表卡片自洽；S1 有 "
                         f"{by_check['S1']['MISSING']} 张不可判。")
    summary = {
        "cards": len(rows),
        "at_least_one_fail": n_fail,
        "at_least_one_missing": n_missing,
        "both_fail_and_missing": n_both,
        "neither": len(rows) - n_fail - n_missing + n_both,
        "by_check": by_check,
        "judgeability": judgeability,
        "homogeneous_rows": homogeneous,
        "status_combinations": len(patterns),
        "hard_sentence": hard_sentence,
        "sentence": (f"本集合 {len(rows)} 张卡片中 {n_fail} 张至少一项 FAIL，"
                     f"{n_missing} 张至少一项 MISSING；两项都有的 {n_both} 张。"),
    }
    if homogeneous:
        summary["sentence"] += " 全部行同构，本集合上无区分信号。"
    write_readme(readme_path, args.date, rows, summary)
    write_html(html_path, args.date, rows, summary)

    outputs = {os.path.basename(p): sha256_file(p) for p in (cards_path, html_path, readme_path)}
    manifest = {
        "module": "EEO-DSR",
        "phase": "Phase 0 disclosure census",
        "date": args.date,
        "retrieval_date": args.date,
        "source": os.path.relpath(args.source, ROOT),
        "source_sha256": sha256_file(args.source),
        "tool": "tools/screen_cards.py",
        "tool_sha256": sha256_file(os.path.abspath(__file__)),
        "cards": [{
            "dataset_id": r["dataset_id"], "url": r["url"], "version": r["version"],
            "card_last_modified": r["card_last_modified"],
            "page_file": r["page_file"],
            "page_sha256": r["page_sha256"], "card_sha256": r["card_sha256"],
            "structured": json.loads(r["structured_canonical"]),
            "checks": {k: v[0] for k, v in r["checks"].items()},
        } for r in rows],
        "outputs": outputs,
        "summary": summary,
        "note": "Fields are parsed automatically from the pinned page bytes; no manual transcription.",
    }
    manifest_path = os.path.join(outdir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    mh = sha256_file(manifest_path)
    with open(os.path.join(outdir, "manifest.sha256"), "w", encoding="utf-8") as f:
        f.write(f"{mh}  manifest.json\n")
    print(summary["sentence"])
    print(f"manifest_sha256 {mh}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
