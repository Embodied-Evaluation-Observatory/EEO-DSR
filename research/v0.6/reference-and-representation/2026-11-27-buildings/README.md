# 同语料站点间偏离：TRI vs Gates（双向）

日期：2026-11-27。样本：`2026-11-27-droid-sample`，成功 1,999/2,000；指纹管线 `median → IQR → center → SVD → sign → L2`，`dims=32`，基只在 reference 侧拟合。

**口径：站点 A 相对站点 B 的分布偏离，不是买方部署参照。** TRI 183 条、Gates 149 条，均来自同一 DROID 语料；没有使用未授权买方数据，也没有合成参照。

## 1 为什么必须双向

基拟合在有偏簇结构的单侧，会把该侧的方差结构装进投影，另一侧被截掉；能量距离又依赖投影。交换拟合侧后读数差异很大：

| 表示 | 方向 | energy distance（0.9 子采样区间） | mean shift L2 |
|---|---|---|---:|
| summary | TRI→Gates | 0.032804（0.029592–0.040978） | 1.2453 |
| summary | Gates→TRI | 0.023949（0.019203–0.033377） | 1.0446 |
| traj16 | TRI→Gates | 0.075332（0.066134–0.090600） | 1.2086 |
| traj16 | Gates→TRI | 0.027926（0.025230–0.035626） | 1.1155 |

traj16 两个方向区间不重叠；summary 方向区间只是边缘重叠。**当前单侧读数不可作为唯一发布读数；若发，必须两方向并列，并写 `claim_scope: basis_fit_direction_dependent`。** 换边差异不是附录，是读数能否发的前提。

## 2 energy 点值/区间矛盾的诊断

旧输出 `energy_distance 0.032804` 落在 bootstrap 区间 `[0.033723, 0.071461]` 外。核查结果：

- 点值与区间用的是**同一批指纹数组、同一套 L2 归一化、同一个 V-statistic**；不是 `fingerprints` / `projections` 混用。
- 根因是**有放回 bootstrap 在 V-statistic 的 within-sample 项里制造重复/零距离对**，把区间整体抬高；点值本身没有用错数组，错的是区间方法。
- 改用 0.9 **无放回子采样**后，summary 点值落在 `[0.029592, 0.040978]` 内，traj16 点值落在 `[0.066134, 0.090600]` 内。旧 bootstrap 区间已撤下。

明细：`energy-diagnostic.json`。工具 `tools/reference_deviation.py` 现默认 `--interval-method subsample`，并保留 `bootstrap` 仅用于诊断，不再写入站点读数。

## 3 越界比例不进入读数

`target_outside_reference_0.5_99.5_share` 对同尺寸零基线没有区分信号，故不进入站点读数、不放进表格，也不作 headline。核对数据仍保留在 `outside-null.json` / `outside-identical-null.json`，只供内部复算；要证明站点差异，应看 energy 与 mean shift，不看这个比例。

## 4 能量距离的零假设

同一池化样本、同尺寸重排 300 次：

| 表示 | 观测 energy | null 均值（95%） | 观测在 null 分布的位置 |
|---|---:|---:|---:|
| summary | 0.032804 | 0.015889（0.011227–0.024498） | 99.67% |
| traj16 | 0.075332 | 0.016270（0.011474–0.023840） | 100% |

能量距离本身高于 null；但 summary 反向 0.023949 已贴近 null 上界 0.024498，说明方向性不只是基造成的，也可能是样本量/方向组合。见 `energy-null.json`。

## 5 文件

- `tri-to-gates-summary-reference.npz` / `target.npz`；`gates-to-tri-summary-*`。
- `*-pair.json`：两侧 building、n、dims、basis SHA256。
- `*-deviation.json`：`scope: site_to_site`、`energy_distance_interval_method: subsample`。
- `energy-diagnostic.json`、`outside-null.json`、`energy-null.json`。

## 6 边界

- 两个 building 样本量都不大（183/149）；只选了一对，不外推。
- 不做接受/拒绝判断；读数只回答“这两个站点在各自基下的分布差多少”。
- 由于换边差异，任何单方向引用都必须同时给另一方向与 `basis_fit_direction_dependent`。
- **0.9 子采样比例未做敏感性。** 0.9 是可调参数；当前只固定用 0.9，不能称“最优”或“唯一”。敏感性矩阵尚未跑。
- **主口径仍是单边基，不是合并拟合基。** traj16 两方向区间不重叠，说明被测量随基改变；下一版应把合并拟合基作主口径，两个单边作敏感性。合并基未实现前，不得把任一单边当唯一发布值。
