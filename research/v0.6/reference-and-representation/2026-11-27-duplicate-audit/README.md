# 重复记录审计：101 / 98 条

日期：2026-11-27。输入 `droid_raw_meta.csv`；只做字段审计，不下载 HDF5、不跑指纹、不设阈值。

## 行宇宙

- raw metadata：74,896 行，74,795 个唯一 uuid，101 条多余重复行。
- scene 有效宇宙（`scene_id` 非空且不为 `-1`）：去重前 73,511，去重后 73,413，移除 98 条。

两个数不是同一分母：101 是 raw 全部重复行；98 是其中落在 scene 有效宇宙里的重复行。不得互相替代。

## 结果

| 宇宙 | 重复组 | 字段完全一致 | 字段冲突 |
|---|---:|---:|---:|
| raw metadata，101 条 | 101 | 58 | 43 |
| scene 有效，98 条 | 98 | 57 | 41 |

字段完全一致的重复 uuid 是真实重复正例候选：同一 episode 记录出现两次。字段冲突的重复 uuid 是数据质量发现，不应当作正例；冲突主要是 `success`：

| 冲突字段组合 | raw 组数 |
|---|---:|
| `success` | 23 |
| `success`, `current_task` | 15 |
| `scene_id`, `success`, `current_task`, `robot_serial` | 4 |
| `scene_id`, `success` | 1 |

## 边界

- 这些是重复**记录**候选，不是独立重编码轨迹。同一 uuid 若指向同一 HDF5，指纹会按定义相同，不能拿它冒充独立真实重复的召回率。
- 58 条 exact 属于 `exact` 等价类（指纹相同、W 无关、构造性 FNR=0）；它不补 `re-encoded` 与 `near-take` 类的缺口。真实正例问题已改写为“三个等价类的定义缺口”，见 `../2026-11-27-equivalence-classes/README.md`。
- 43 条冲突不是普通数据质量：43 组全部涉及 `success`，同一 uuid 一败一成，等于 ρ 输入有一个未声明的 tie-break。独立读数与三规则敏感性见 `../2026-11-27-label-conflicts/README.md`；本审计不静默选边。

明细：`duplicate-audit.json`、`duplicate-records.csv`。
