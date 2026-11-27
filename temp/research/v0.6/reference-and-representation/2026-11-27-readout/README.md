# 2026-11-27 研究读数汇总

本页只汇总当日新跑出的读数；每项指向可复算文件。 复盘落实清单见 `../../2026-11-27-recap/`；Phase 1 最小可签发集见 `../../../MINIMAL-SIGNABLE.md`。版本线仍为 V0.6.5（`2ac1caf`），本页不改变发布状态。

## 1. 全 K 配对对照：旧 +0.023 撤回，旧差值区间也撤回

`../variance-probe/2026-11-27-cell-paired/paired-rho090.json`、`continuous.json`

300 次模拟，B=2,000，ρ=0.900；每次先抽一份全 K 语料，fixed 与 full 在同一份语料上做。

| 模式 | ρ percentile | ρ BCa | n_eff |
|---|---:|---:|---:|
| fixed | 0.833 | 0.817 | — |
| full | 0.827 | 0.813 | 0.820 |

配对 2×2：both 248 / only fixed 2 / only full 0 / neither 50；McNemar 精确 p=0.5；full−fixed = −0.0067。**旧区间 `[−0.0167, 0.0000]` 是 c=0 强制上界 0 的统计假象，不读作“方向偏负、接近显著”；诚实表述只用 2/300 不一致和 p=0.5。**

二值覆盖率 298/300 = 99.3% 只说明“覆盖/不覆盖”的判定几乎一致，不等于连续读数等价。连续量配对比较（宽度/下端点/上端点，Hodges–Lehmann + Wilcoxon）：

| 连续量 | full−fixed HL | 中位数差配对 bootstrap 95% | Wilcoxon p |
|---|---:|---:|---:|
| 区间宽度 | +0.000167 | [−0.000137, +0.000565] | 0.348 |
| 下端点 | −0.000184 | [−0.000539, +0.000147] | 0.246 |
| 上端点 | −0.000014 | [−0.000133, +0.000088] | 0.800 |

差值都在 0 附近，量级约为宽度均值的 0.2%；宽度有实际变异（sd≈0.058），不是“无变异导致无功效”。但“未检出差异”不等于“等价”；要证明等价需预设等效界并做 equivalence test，本轮不做。

结论：配对后没有“full 抬高 coverage”的证据；旧 `fixed 0.827 / full 0.850` 是未配对的两条 RNG 路径，+0.023 不能引用。两者都仍远低于名义 0.95。

## 2. 同语料站点间偏离：双向读数，单侧不能发布

`../2026-11-27-buildings/`

参照 TRI n=183，目标 Gates n=149；指纹 `dims=32`，基只在 reference 侧拟合。口径是“站点 A 相对站点 B 的分布偏离”，不是买方部署参照。

| 表示 | 方向 | energy（0.9 子采样 95%） | mean shift L2 | KS max |
|---|---|---|---:|---:|
| summary | TRI→Gates | 0.032804 (0.029592–0.040978) | 1.2453 | 0.2337 |
| summary | Gates→TRI | 0.023949 (0.019203–0.033377) | 1.0446 | 0.2488 |
| traj16 | TRI→Gates | 0.075332 (0.066134–0.090600) | 1.2086 | 0.3237 |
| traj16 | Gates→TRI | 0.027926 (0.025230–0.035626) | 1.1155 | 0.2374 |

**换边差异很大**，尤其 traj16 两个方向区间不重叠。因此单侧 TRI 拟合读数不能作为唯一发布值；若发，必须两方向并列，并写 `claim_scope: basis_fit_direction_dependent`（偏离读数依赖基拟合方向），同时注明 Gates 的方差结构可能在 TRI 基下被截掉。

### energy 点值/区间矛盾

旧输出点值 0.032804 落在旧 bootstrap 区间 `[0.033723, 0.071461]` 外。复算确认点值与区间用的是**同一批 `fingerprints`、同一套 L2 归一化、同一个 V-statistic**，不是 `fingerprints`/`projections` 混用。根因是有放回 bootstrap 在 V-statistic 的 within-sample 项制造重复/零距离对，抬高区间。改用 0.9 无放回子采样后点值均落入区间（见上表）。旧 bootstrap 区间不再用于站点读数；明细 `energy-diagnostic.json`。

### 越界比例不进入读数

`target_outside_reference_0.5_99.5_share` 对同尺寸零基线没有区分信号，故从读数和表格中撤下，不作 headline，也不作为站点差异证据。核对数据仍在 `outside-null.json` / `outside-identical-null.json`，只供内部复算。

### energy 的零基线

同池同尺寸置换 300 次的 energy null：summary 0.015889（0.011227–0.024498），观测 0.032804 位于 99.67 分位；traj16 0.016270（0.011474–0.023840），观测 0.075332 位于 100 分位。energy 高于同分布零基线，但 summary 反向 0.023949 已贴近 null 上界，仍说明方向依赖。

## 3. 注入偏移标定

`../2026-11-27-reference/calibration.json`

合成 200 条 8 维单位向量，前 120 条加 `N(0, 0.05)` 后单位化：identical mean shift 0.0 / energy 0.0；shifted 0.1028678214 / 0.0042879333。只证明比较器对已知偏移有响应，不证明真实语料上的分辨力；文件标 `eeo_synthetic: true`。

## 4. FPR/FNR-vs-W 曲线与目标类

`../2026-11-27-fpr-fnr-curve/`

样本 1,999/2,000（1 条 HTTP 404），`dims=32`，硬负例 246，正例 300 对（150 对 0.5% 重编码 + 150 对 2% 重编码）。W 从 0.70 到 0.99。

W=0.90：summary FPR 2/246=0.0081、0.5% 副本 FNR 5/150=0.0333、2% 副本 FNR 96/150=0.6400；traj16 FPR 0/246、0.5% FNR 0/150、2% FNR 60/150=0.4000。W=0.70 时 summary FPR 0.187/FNR 0.163，traj16 0.041/0.043；W=0.99 时 summary FNR 0.717、traj16 0.587。

`0/150` 与 `2/246` 的 Clopper–Pearson 上界分别为 1.98% 与 2.54%，是上界不是工作点。0.5% 副本 summary 中位余弦约 0.981、2% 约 0.810；traj16 约 0.995/0.935，**不是合成自测的 0.99997 级**；这是 `re-encoded` 类分布，不代表 `near-take`。

traj16 在全网格上支配 summary，且本管线两者都投影到 `dims=32`，输出维度相同；差异来自 464 维时序点 vs 203 维摘要统计的输入表示。**不能直接说“表示选择比 W 选择更重要”或“维度越高越好”**，需同维度/同信息量消融；当前只能说“本网格 traj16 的 FPR/FNR 全面优于 summary，2% 副本 FNR 仍 0.40”。

## 5. 43 组 success 冲突：首个真实标签一致性读数

`../2026-11-27-label-conflicts/label-conflict-readout.json`、`tie-break-sensitivity.json`

raw 74,896 行 / 74,795 唯一 uuid；43 组字段冲突全部涉及 `success`：23 组仅 `success`，15 组 `success+current_task`，4 组 `scene_id+success+current_task+robot_serial`，1 组 `scene_id+success`。43 组的 success 模式均为 `[False, True]`，即同一 episode 两条记录一败一成。三条轴的全部 ρ 都建在 success 上，所以这不是普通“数据质量”，而是 ρ 输入里有一个未声明的 tie-break。

这是“同一 episode 两条记录间的一致性”，不是“两个评分人对同一 episode 的标注一致性”（D2 口径）；它更窄，但是免费的、已在数据里的真实观测。不能叫“标注一致性抽检”。

tie-break 敏感性（raw metadata 子集 73,413 行 / 2,432 个 `building||current_task` 簇）：

| 规则 | ρ | 95% | n_eff |
|---|---:|---:|---:|
| first | 0.1917369 | 0.1635868–0.2178353 | 6,082.826 |
| last | 0.1915476 | 0.1637314–0.2155634 | 6,086.621 |
| drop | 0.1918196 | 0.1660606–0.2177917 | 6,080.981 |

三组极差 <0.0003，区间全重叠；tie-break 在该子集上不改变 ρ 方向。**但该子集不是已发布的 93,994-episode 派生语料（2,432 簇 vs 53,714 cell），不能替换 published ρ。** 正式记录应声明 tie-break 规则；当前审计取首条。

## 6. 真实正例：三个等价类，不是“数据缺口”

`../2026-11-27-equivalence-classes/README.md`

- `exact`：58 组字段完全一致的重复记录；同一 HDF5 指纹相同，W 无关，构造性 FNR=0；不能冒充独立重采。
- `re-encoded`：150 对 0.5% + 150 对 2%；本日曲线只测这一类。
- `near-take`：同任务同 scene 不同执行；未定义、未测量。

FNR 的目标类必须写在指纹侧标定件首行；三类各自报 FNR，买方按自己的去重需求选类集合。`near-take` 与 ICR 直接冲突：把不同 take 判为重复，就是把 ICR 想要的重复多样性扣掉；两个模块必须显式声明该冲突，否则会在同一语料上给互相矛盾的建议。

## 7. 预检层：不具名、非记录、不是入口

`../../../entry/PRECHECK_LAYER.md`、`../../../entry/precheck-register.json`、`../../../tools/precheck_local.py`

委托方在本地跑公开工具，样本不上传，EEO-DSR 不接触输入。产出只有工具日志 + 输入哈希，带机器标记 `pre_check_not_a_record`；不含记录 schema、记录哈希、摘要、判定、发现、抬头。官方 `record.schema.json` 与 `validate_record.py` 拒收带该标记的文档；剥掉标记仍因缺少记录必填字段而失败。公开登记册只报 `n_prechecks` 与 `n_formal_entry` 聚合数，不具名、不报发现、不评级。正式记录在 `submitter.prior_prechecks` 披露“曾有预检及日期”。不设排他/embargo；EEO 可独立就同一语料发布读数；同方法同数，无“宽松预检版”。

## 8. 区间构造

`nominal_95_claim: not_permitted` 已在 `GOVERNANCE-ADDENDUM.md` 与 `fields.json` 落地；区间照发，但不写“95% 置信区间”。换 percentile/basic/BC/BCa 已证明不够；VST/studentized 是构造层重新设计，排在发布闸之外，本日未开始。
