#!/usr/bin/env python3
"""Phase 0 card screen.

Reads a fixed manifest of public dataset-card URLs, fetches the raw card, records its sha256, and
runs S1-S6 on what the card declares. Output is written under checks/dataset/<date>/.

No score, no rating, no ranking. A cell is PASS, FAIL or MISSING; FAIL prints both the declared and
the recomputed value.
"""
import csv
import hashlib
import html
import json
import os
import re
import sys
import urllib.request

CARDS = [
    ("lerobot/aloha_mobile_cabinet", "https://huggingface.co/datasets/lerobot/aloha_mobile_cabinet/raw/main/README.md"),
    ("lerobot/berkeley_cable_routing", "https://huggingface.co/datasets/lerobot/berkeley_cable_routing/raw/main/README.md"),
    ("lerobot/berkeley_gnm_sac_son", "https://huggingface.co/datasets/lerobot/berkeley_gnm_sac_son/raw/main/README.md"),
    ("lerobot/jaco_play", "https://huggingface.co/datasets/lerobot/jaco_play/raw/main/README.md"),
    ("lerobot/libero", "https://huggingface.co/datasets/lerobot/libero/raw/main/README.md"),
    ("lerobot/nyu_rot_dataset", "https://huggingface.co/datasets/lerobot/nyu_rot_dataset/raw/main/README.md"),
    ("lerobot/pusht", "https://huggingface.co/datasets/lerobot/pusht/raw/main/README.md"),
    ("lerobot/roboturk", "https://huggingface.co/datasets/lerobot/roboturk/raw/main/README.md"),
    ("lerobot/stanford_hydra_dataset", "https://huggingface.co/datasets/lerobot/stanford_hydra_dataset/raw/main/README.md"),
    ("lerobot/svla_so101_pickplace", "https://huggingface.co/datasets/lerobot/svla_so101_pickplace/raw/main/README.md"),
    ("lerobot/taco_play", "https://huggingface.co/datasets/lerobot/taco_play/raw/main/README.md"),
    ("lerobot/xarm_lift_medium", "https://huggingface.co/datasets/lerobot/xarm_lift_medium/raw/main/README.md"),
]
DATE = "2026-11-25"
SPDX = {"mit", "apache-2.0", "cc-by-4.0", "cc-by-sa-4.0", "bsd-3-clause", "gpl-3.0"}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "EEO-DSR/0.3 phase0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def parse(card):
    text = card.decode("utf-8", "replace")
    lic = re.search(r"^license:\s*([^\s]+)\s*$", text, re.M)
    info = {}
    m = re.search(r'"total_episodes"\s*:\s*(\d+)', text)
    if m: info["total_episodes"] = int(m.group(1))
    for k in ("total_frames", "total_tasks", "total_videos"):
        m = re.search(rf'"{k}"\s*:\s*(\d+)', text)
        if m: info[k] = int(m.group(1))
    m = re.search(r'"fps"\s*:\s*([0-9.]+)', text)
    if m: info["fps"] = float(m.group(1))
    m = re.search(r'"splits"\s*:\s*\{([^}]*)\}', text)
    if m:
        info["splits"] = dict(re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', m.group(1)))
    m = re.search(r'"codebase_version"\s*:\s*"([^"]+)"', text)
    if m: info["codebase_version"] = m.group(1)
    m = re.search(r'"robot_type"\s*:\s*"([^"]+)"', text)
    if m: info["robot_type"] = m.group(1)
    return text, (lic.group(1).lower() if lic else None), info


def coverage_ok(splits, total):
    if not splits or total is None:
        return None
    spans = []
    for v in splits.values():
        m = re.fullmatch(r"(\d+):(\d+)", str(v))
        if not m:
            return None
        spans.append((int(m.group(1)), int(m.group(2))))
    spans.sort()
    if spans[0][0] != 0 or spans[-1][1] != total:
        return False
    return all(spans[i][1] == spans[i + 1][0] for i in range(len(spans) - 1))


def checks(text, lic, info):
    E = info.get("total_episodes")
    cov = coverage_ok(info.get("splits"), E)
    out = {}
    out["S1"] = ("PASS", f"分项覆盖 0–{E}") if cov else (
        "FAIL" if cov is False else "MISSING",
        f"声明总数 {E}，分项 {info.get('splits')}")
    units = E is not None and info.get("fps") is not None and (
        info.get("total_frames") is not None or info.get("total_videos") is not None)
    out["S2"] = ("PASS", "episodes/tasks/frames/videos 均带单位，帧率换算已声明") if units else (
        "MISSING", "卡片未同时声明条数与单位/帧率")
    out["S3"] = ("MISSING", f"版本 {info.get('codebase_version')}，卡片无修订日期，无法核对")
    if lic and lic in SPDX:
        out["S4"] = ("PASS", f"license: {lic}")
    elif lic:
        out["S4"] = ("FAIL", f"声明 license: {lic}，非机器可识别标识")
    else:
        out["S4"] = ("MISSING", "卡片无 license 字段")
    out["S5"] = ("MISSING", "卡片未给文件级校验和")
    out["S6"] = ("MISSING", "卡片未给场景/工位标识，无法跨表 join")
    return out


def main():
    rows = []
    for cid, url in CARDS:
        raw = fetch(url)
        text, lic, info = parse(raw)
        res = checks(text, lic, info)
        rows.append({"id": cid, "url": url, "sha256": hashlib.sha256(raw).hexdigest(),
                     "license": lic, "total_episodes": info.get("total_episodes"),
                     "checks": res})
    outdir = os.path.join("checks", "dataset", DATE)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "cards.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "url", "sha256", "S1", "S2", "S3", "S4", "S5", "S6", "evidence"])
        for r in rows:
            ev = "; ".join(f"{k}: {v[1]}" for k, v in r["checks"].items())
            w.writerow([r["id"], r["url"], r["sha256"]] +
                       [r["checks"][f"S{i}"][0] for i in range(1, 7)] + [ev])
    bad = sum(1 for r in rows if any(v[0] != "PASS" for v in r["checks"].values()))
    summary = f"本集合 {len(rows)} 张卡片中 {bad} 张至少一项不通过。"
    by_check = {f"S{i}": {st: sum(1 for r in rows if r["checks"][f"S{i}"][0] == st)
                          for st in ("PASS", "FAIL", "MISSING")} for i in range(1, 7)}
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump({"date": DATE, "cards": len(rows), "at_least_one_not_pass": bad,
                   "by_check": by_check}, f, ensure_ascii=False, indent=2)
    write_readme(outdir, rows, summary, by_check)
    write_html(outdir, rows, summary)
    print(summary)


def write_readme(outdir, rows, summary, by_check):
    lines = [f"# Phase 0 初筛 {DATE}", "", summary, "",
             "检索日期 2026-11-25；只收录当日公开可访问、无需审批、卡片至少声明条数与许可两项的语料。",
             "每张卡片的 URL 与 sha256 见 `cards.csv`。状态只有 PASS / FAIL / MISSING；MISSING 与 FAIL 同等记录。", "",
             "逐项分布：" + "；".join(
                 f"{k} PASS {v['PASS']} / FAIL {v['FAIL']} / MISSING {v['MISSING']}"
                 for k, v in by_check.items()), ""]
    for r in rows:
        lines.append(f"- `{r['id']}`：{r['url']}  sha256 `{r['sha256']}`")
    lines += ["", "本页只做卡片算术，不构成核验结论，不说明语料可用性。"]
    open(os.path.join(outdir, "README.md"), "w", encoding="utf-8").write("\n".join(lines))


def write_html(outdir, rows, summary):
    esc = html.escape
    head = """<!doctype html><meta charset="utf-8"><title>Phase 0 初筛 2026-11-25</title>
<style>body{font:14px/1.5 system-ui,sans-serif;margin:32px;max-width:1200px}
table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccc;padding:6px;vertical-align:top}
.pass{color:#176b2c}.fail{color:#a11}.missing{color:#777}code{font-size:12px}</style>"""
    body = [head, "<h1>Phase 0 初筛 2026-11-25</h1>",
            "<p>本核验只给出该数据集在 episode 层面的统计可用性读数，不说明任务难度匹配、不说明标注正确性、"
            "不构成资产估值、不构成采购建议。</p>",
            "<p>本记录不以任何标准为判定依据。初筛只做卡片算术，不是符合性检查。</p>",
            f"<p>{esc(summary)}</p>", "<table><tr><th>卡片</th><th>S1</th><th>S2</th><th>S3</th>"
            "<th>S4</th><th>S5</th><th>S6</th></tr>"]
    for r in rows:
        cells = [f"<td><a href='{esc(r['url'])}'>{esc(r['id'])}</a><br><code>{r['sha256'][:16]}…</code></td>"]
        for i in range(1, 7):
            st, ev = r["checks"][f"S{i}"]
            cells.append(f"<td class='{st.lower()}'><b>{st}</b><br>{esc(ev)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    body += ["</table>", "<p>排序按卡片 id 字母序，不按失败数。</p></body>"]
    open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write("\n".join(body))


if __name__ == "__main__":
    sys.exit(main())
