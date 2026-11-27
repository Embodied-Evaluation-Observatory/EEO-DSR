# 同一 episode 两条记录的标签一致性

日期：2026-11-27。输入：`droid_raw_meta.csv` 的重复 UUID 组。见 `../2026-11-27-duplicate-audit/`。

## 读数

- 43 组字段冲突；**43 组全部涉及 `success`**。`success` 只在 23 组；其余是 `success` 与 `current_task`、`scene_id`、`robot_serial` 的组合。
- 43 组里 success 值都是同一组 `False` / `True` 对；没有一组是两个相同 success 但其他字段冲突。
- 这不是“两个评分人对同一 episode 的标注一致性”（D2），而是“同一 episode 的两条记录彼此是否一致”。口径更窄，不能叫标注一致性抽检。

## tie-break 敏感性

当前审计的 tie-break 是 **取首条**。同一 raw metadata 子集上（73,413 行、2,432 个 `building||current_task` 簇）：

| 规则 | episodes | clusters | ρ | ρ bootstrap 95% | n_eff |
|---|---:|---:|---:|---|---:|
| first | 73,413 | 2,432 | 0.191737 | 0.163587–0.217835 | 6,082.826 |
| last | 73,413 | 2,432 | 0.191548 | 0.163731–0.215563 | 6,086.621 |
| drop | 73,372 | 2,432 | 0.191820 | 0.166061–0.217792 | 6,080.981 |

三个 ρ 的极差 <0.0003，bootstrap 区间全部重叠；`n_eff` 极差约 5.6（相对约 0.09%）。43/73,413≈0.059%，数值影响可忽略；敏感性要证明的是规则选择不改变结论方向，而不是看数值挪多少。因此 tie-break 规则不改变这一子集上 ρ 的方向。

**边界**：该子集不是已发布的 93,994-episode 派生语料；2,432 个 `building||current_task` 簇与全语的 53,714 个 cell 也不同。上表的 ρ 只用于 tie-break 敏感性，不能替换 published ρ。三种规则下标签数值影响可忽略，但“规则不敏感”的结论只在这个子集上成立。

## 文件

- `label-conflict-readout.json`：冲突组、字段组合、success 模式、三规则读数。
- `tie-break-sensitivity.json`：工具原始输出（含 200 次 cluster bootstrap）。
