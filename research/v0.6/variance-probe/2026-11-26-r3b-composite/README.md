# G1 簇键唯一性：composite 重跑

## 发现

raw `scene_id` 不是全局唯一。非缺失 scene 的 2,207 个值中：

- 9 个 scene_id 落在 >1 个 building（大小写与别名归一后仍为 9）。
- 2 个 scene_id 落在 >1 个 robot_serial。
- 典型碰撞：`4823049285` 跨 BAIR／KAIST／Gates／Penn Levine 457／Bayes - RAD Lab／Bayes - Lab 1；`4465064685` 跨 Gates／BAIR；`3827924651` 跨 Mila Staff Kitchen／Glen's office。

`scene_id` 单独不能作为全局唯一簇键。按 `scene_id|building|robot_serial` 复合键重跑。

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
