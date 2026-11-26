# V0.6 原生 scene 轴复核（未审查，不提交、不推送）

日期：2026-11-26。本目录是复核草图，不是发布结果。它不替代 r2，也不签发 NEES 记录。

## 1. 先修轴：LeRobot 镜像没有原生 scene_id

DROID 论文附录 D 把 unique scene 定义为机器人工作空间的实质性变化：最初有 2,080 个 scene ID，语义去重后为 564 个 unique scenes。`lerobot/droid_1.0.1` 的 parquet 镜像只保留了 `building`、`language_instruction` 等字段，没有 `scene_id`；因此 r1/r2 的 `building` 和 `building||instruction` 都不是原生 scene 轴。

本轮从 DROID 1.0.1 的 raw metadata 重新取 `scene_id`、`success`、`building`、`current_task`、`robot_serial`、`timestamp`。

| 读数 | 值 |
|---|---:|
| raw metadata 对象 | 74,896 |
| 唯一 `uuid` | 74,795 |
| 重复 metadata 行 | 101 |
| `scene_id=-1` | 1,382 |
| 进入 scene 轴 | 73,413 |
| 非缺失 scene ID | 2,207 |

2,207 是 raw `scene_id` 的不同值，不是论文的 2,080，也不是 564。564 的语义去重需要按 robot serial、lab、building、timestamp 分组后做视觉/现场复核；本轮没有这份人工映射，不能声称复现 564。raw 的 2,207 只是“未语义去重的原生 scene 值”。

## 2. 原生 scene 轴的结果

| 读数 | building 轴 | building\|\|instruction 轴 | 原生 scene 轴 |
|---|---:|---:|---:|
| 簇数 K | 73 | 53,714 | 2,207 |
| 单例 | 1 | 47,112 | 216 |
| 有变化簇 | 65 | 93 | 1,038 |
| 零方差占比（多例分母） | 9.72% | 98.59% | 47.87% |
| ρ-free 平凡区间 | [73, 93,994] | [53,714, 93,994] | [2,207, 73,413] |
| ρ-free 区间相对宽 | 99.92% | 42.85% | 96.99% |
| ρ 条件区间（1,000 次簇 bootstrap） | [0.0563, 0.1068] | [0.6687, 0.8552] | [0.2538, 0.3069] |
| n_eff 条件区间 | [609.26, 1,137.59] | [54,373.72, 55,473.71] | [5,565.30, 6,469.14] |
| n_eff 条件区间相对宽 | 60.49% | 2.00% | 15.02% |
| 区间读数 | no_information | usable | usable |
| ρ 点估计 | 0.081593 | 0.766531 | 0.279828 |
| 点 n_eff | 791.645 | 54,853.997 | 5,990.514 |
| 点 deff | 118.732 | 1.7135 | 12.2549 |

零方差占比从 98.59% 降到 47.87%，有变化簇从 93 升到 1,038。这是轴粒度变化后的读数，不是“DROID 语料可定价”的证明。ρ-free 平凡区间仍宽 96.99%，它只说明“没有 ρ 时 n_eff 只能落在 [K,N]”，不能当作条件区间读数。原生 scene 轴的条件 n_eff 区间相对宽 15.02%，按条件读数可用；`interval_reading` 挂条件区间，ρ-free 区间另立字段。`building` 轴条件相对宽 60.49%，仍为 no_information。

`building` 轴度量站点间成功率异质性，`building||instruction` 度量文本单元粒度，原生 scene 轴才对应论文的 scene 定义。三者并列，不合并，不取最大 deff。

## 3. 93 个有变化簇不是全语料

现有 cell 轴的点 ρ=0.766531 依赖 93 个有变化簇：

| 读数 | 值 |
|---|---:|
| 有变化簇 | 93 |
| 覆盖 episode | 19,067 |
| 落在 building 数 | 49 |
| instruction 取值数 | 49，其中 45 个为空 |
| 前 10 个 building 的 episode 占比 | 69.12% |

所以 0.766531 是这 93 个簇的组内结构，不是 53,714 个簇的平均簇内相关。报告必须带这条分布，不能只印一个名义 ρ。

原生 scene 轴的 1,038 个有变化簇覆盖 58 个 building、944 个 task、51,655 条 episode；前 10 个 building 占 65.92%，前 10 个 task 占 67.76%。分布同样集中，点估计也不能当成全语料平均值。

## 4. 簇级 bootstrap

簇级 bootstrap 重采样簇，不重采样 episode；每个 replicate 计算一次 ICC(1)。

| 轴 | ρ 点 | ρ 95% percentile 区间 | n_eff 条件区间（每个 replicate 同时算 n_eff） | 相对宽 | 有效 replicate |
|---|---:|---|---:|---:|---:|
| building | 0.081593 | [0.056259, 0.106783] | [609.26, 1,137.59] | 60.49% | 1,000 |
| building\|\|instruction | 0.766531 | [0.668712, 0.855212] | [54,373.72, 55,473.71] | 2.00% | 1,000 |
| 原生 scene | 0.279828 | [0.253753, 0.306906] | [5,565.30, 6,469.14] | 15.02% | 1,000 |

区间只属于对应轴的 ICC，不是训练信息量。没有把这几个区间合并，也没有把区间宽度当成 NEES 的置信区间。n_eff 区间由每个 replicate 自己的 n_eff 取分位得到，不是把 ρ 分位代回原始簇大小。

负 ρ 的处理：`dataset_driver.icc1` 保留未截断的 `rho`；`neff_at_rho` 只在自己的求和路径里把负值截到 0，并在 `rho_used` 单独印出。当前三轴的 bootstrap 负值占比均为 0；模拟中 ρ=0 时有 59% 的负值，未被静默丢弃。

## 5. beta-binomial 偏差与覆盖率

模拟设置：簇大小从原生 scene 的 1–810 分布中重采样，结局为 beta-binomial，已知 ρ；每个网格 100 次模拟、每次 100 次簇 bootstrap。覆盖率为条件覆盖，只在点估计可算时统计。

| 真 ρ | 偏差均值 | 95% 覆盖率 | 负值占比 |
|---:|---:|---:|---:|
| 0.0 | -0.00014 | 0.88 | 59% |
| 0.05 | +0.00015 | 0.95 | 0% |
| 0.1 | -0.00031 | 0.93 | 0% |
| 0.2 | +0.00013 | 0.90 | 0% |
| 0.3 | -0.00086 | 0.92 | 0% |
| 0.5 | +0.00332 | 0.93 | 0% |
| 0.7 | -0.00098 | 0.94 | 0% |
| 0.9 | -0.00090 | 0.95 | 0% |

偏差很小，覆盖率在 0.88–0.95 之间；ρ=0 时覆盖率 0.88，低于名义 0.95，负值占 59%。这是 100/100 的粗模拟，不是最终覆盖率标定，也不能替代更大规模的重复。极端偏斜的 cell 尺寸分布本轮没有跑，不能外推。

## 6. 结论边界

- 原生 scene 轴的零方差占比为 47.87%，比 cell 轴的 98.59% 低；这支持“98.59% 主要是粒度造成的”，但不支持“DROID 整体可定价”。
- 564 个 unique scenes 没有复现；2,207 是未语义去重的 raw scene 值。
- 三轴都只是成功率估计的精度，`claim_scope` 固定为 `success_rate_precision_*_not_training_information`。
- 没有 NEES 记录，没有发布，没有打 tag，没有推送。
- 本轮没有改 Phase 0；Phase 0 的外部复核不能当作 `checks/dataset/<date>/` 的产出引用。

## 7. 文件

| 文件 | 内容 |
|---|---|
| `droid_scene.csv.gz` | 73,413 条三列原生 scene 语料 |
| `probe/probe.json` / `probe/clusters.csv` | 原生 scene 探针 |
| `driver-report.json` | 原生 scene 驱动报告 |
| `bootstrap-native.json` / `bootstrap-cell.json` / `bootstrap-site.json` | 三轴簇级 bootstrap |
| `simulation.json` | beta-binomial 偏差/覆盖模拟 |
| `variable-distribution.json` | 93 个 cell 变化簇与 1,038 个 scene 变化簇的分布 |
| `three-axis.json` | building、cell、原生 scene 三轴并列，含人话 scope |
