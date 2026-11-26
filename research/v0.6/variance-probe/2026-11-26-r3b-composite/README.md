# G1 簇键唯一性：composite 重跑

## 发现

raw `scene_id` 不是全局唯一。非缺失 scene 的 2,207 个值中：

- 9 个 scene_id 落在 >1 个 building（大小写与别名归一后仍为 9）。
- 2 个 scene_id 落在 >1 个 robot_serial。
- 典型碰撞：`4823049285` 跨 BAIR／KAIST／Gates／Penn Levine 457／Bayes - RAD Lab／Bayes - Lab 1；`4465064685` 跨 Gates／BAIR；`3827924651` 跨 Mila Staff Kitchen／Glen's office。

`scene_id` 单独不能作为全局唯一簇键。按 `scene_id|building|robot_serial` 复合键重跑。

覆盖键与精度键必须分开：

| 键 | 值 | 用途 |
|---|---|---|
| 覆盖键 `scene_id` | 2,207 个 raw scene 值 | 回答“覆盖了多少个 scene 值” |
| 精度键 `scene_id｜building｜robot_serial` | 2,220 个簇 | 回答“成功率的独立试次折算” |

9 个碰撞 id 覆盖 2,172 条 episode，占 73,413 的 2.96%。这不是可忽略的边角：撞的是 2.96% 的 episode，不是 2.96% 的 id。另有 `scene_id=-1` 的 1,382 条，占 raw metadata 74,896 的 1.85%；它属“无场景标识”，与 9 个跨 building 碰撞分开报。

两条 claim scope 不共用一个名字：覆盖用 `scene_coverage_at_raw_scene_id_not_success_rate_precision`；精度用 `success_rate_precision_at_composite_scene_key_not_training_information`。

## 逐 id 分裂表

| scene_id | episode | 占语料 | building 数 | robot_serial 数 | 分裂数 |
|---|---:|---:|---:|---:|---:|
| 4823049285 | 778 | 1.06% | 6 | 5 | 6 |
| 8969941950 | 372 | 0.51% | 2 | 1 | 2 |
| 5539130832 | 284 | 0.39% | 2 | 1 | 2 |
| 3827924651 | 272 | 0.37% | 2 | 1 | 2 |
| 4465064685 | 272 | 0.37% | 2 | 2 | 2 |
| 8372815467 | 69 | 0.09% | 2 | 1 | 2 |
| 4173062021 | 47 | 0.06% | 2 | 1 | 2 |
| 7224020122 | 40 | 0.05% | 2 | 1 | 2 |
| 8444908630 | 38 | 0.05% | 2 | 1 | 2 |

## composite 结果

| 读数 | 值 |
|---|---:|
| 簇数 K | 2,220 |
| episode 数 | 73,413 |
| 单例 | 217 |
| 有变化簇 | 1,045 |
| 零方差占比（多例分母） | 47.83% |
| ρ 点估计 | 0.284524 |
| 点 n_eff | 5,953.54 |
| deff | 12.3310 |
| ρ 条件 95% | [0.258117, 0.313981] |
| n_eff 条件 95% | [5,519.34, 6,428.41] |
| n_eff 条件相对宽 | 15.22% |
| bootstrap reps | 1,000 |

## 仍未关闭

论文 2,080 与语义去重后的 564 没有复现；raw 2,207、composite 2,220 都不是 564。G1 只完成了“检查碰撞并改复合键重跑”，没有完成“564 语义映射”。不得把 2,207 或 2,220 写成论文的 scene 数。

`nees_record: not_issued`；本目录仅为本地未审查研究产物。
