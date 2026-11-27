# 最小可签发集与 Phase 1 边界

日期：2026-11-27。这里说的是**可签发范围**，不是“已签发记录”。本模块至今没有发出任何正式记录；下面每项都标了当前证据与不能说的话。

## 1 可签发集

| 项 | 当前证据 | 可签发什么 | 不能说什么 |
|---|---|---|---|
| 卡片口径普查 | `checks/dataset/2026-11-26/`：20 张普查，旧三态（PASS/FAIL/MISSING）口径，四态未重跑；0 张至少一项 FAIL，20 张至少一项 MISSING；S1/S2/S3/S5/S6 可判 0/20，S4 12/20。另有 `checks/dataset/2026-11-26-r2-robomind-rh20t/` 2 张补充（RoboMIND/RH20T），两个目录，不合并为 20 或 22 张普查 | 旧三态口径下的 FAIL/MISSING 分布、逐项可判率；补充 2 张单列 | 0 FAIL 不是“通过”；不是四态结论；不是单卡评级；不把 20 与 2 合成普查 |
| 集中度与簇分布 | `research/v0.6/variance-probe/2026-11-26-g3-single-source/README.md`：单源 73,413 行；site K=69，task_text K=2,418，native K=2,220 | building/task 分布、簇大小、空格计数；标明单源行宇宙 | 不判“够不够分散”；不把成功率精度当训练信息量；不把镜像 K=53,714 的文本单元轴叫 task 轴 |
| 簇预算 | `README.md` 的零失败界与 `cluster_budget` | 10%→29、5%→59、1%→299 个独立簇；两端上界 | 不是采样承诺；有失败样本时不适用 |
| 标签冲突计数 | `research/v0.6/reference-and-representation/2026-11-27-label-conflicts/` | 43 组同 episode 冲突、43/43 涉及 success、字段组合分布 | 不是 D2 标注一致性；不是对生产方的评级 |
| 溯源包 | DSR-D4 检查项已定义（快照 pin、文件级哈希、采集/生成声明、检索日期）；DROID 具体包尚未组装 | 七项齐全性检查、缺项清单 | 缺项时不得称“可复算”；不是审计意见，不是资产估值 |
| 不可算说明书 | `METHOD.md` 与 `schema/examples/record-example-unestimable.json` | 原因、独立读数、关注方语言 | 不输出点值；不把不可算写成“差” |
| ITR 单源三轴点值 | `research/v0.6/variance-probe/2026-11-26-g3-single-source/three-axis.json`，73,413 行：site ρ=.104613 / n_eff=589.745（K=69）；task_text ρ=.191744 / n_eff=6,053.998（K=2,418）；native ρ=.284524 / n_eff=5,953.539（K=2,220） | 点 ρ、点 n_eff、轴口径、行宇宙（73,413）；task_text 不叫 cell；tie-break K=2,432 vs 2,418 未对账前不签发 task_text | 不写“95% 置信区间”；不把 ρ-free 界当条件区间；不外推到训练信息量；不把镜像 K=53,714 当同一任务轴 |
| 站点对偏离 | `research/v0.6/reference-and-representation/2026-11-27-buildings/`：TRI↔Gates 双向，energy 用 0.9 子采样区间；越界比例已从读数撤下 | 两方向 energy/mean shift/KS；`claim_scope: basis_fit_direction_dependent` | 越界比例不进入读数；不把单侧基拟合当唯一读数；0.9 子采样比例敏感性未做；合并拟合基尚未做，先不作主口径 |

**覆盖标签贴在区间方法上，不贴在点值上。** G2 已测区间方法在 native 与镜像文本单元尺寸上的覆盖：native 0.910–0.938（1,000×100），B=2,000 文本单元网格 0.838–0.936；未达名义 0.95，所以本文件不发条件区间。单源 K=69/2,418/2,220 不在这张网格里，未单独标定，更不能把网格覆盖贴到点值。`nominal_95_claim: not_permitted` 继续有效。

## 2 Phase 1 尚未完成的事项

- **发布前阻塞：tie-break 子集 K=2,432 与单源 `task_text` K=2,418 差 14 簇，未对账。** 对账前 `task_text` 不签发；别把 2,432 当单源任务轴 K。

- Phase 0 仍是 20 张普查（旧三态口径，四态未重跑）＋2 张补充（另一目录，不合并）；扩到 50–100 张、做公开 Dashboard 是下一阶段，不是当前结果。
- DROID 七项溯源包尚未组装成 PDF/CSV 核验读数包；现在只有检查项与方法。
- DSB1.0（设计预算包）、DSR1.0（标准化核验工具）尚未封装；不要用“已发布”描述。
- schema 作为标准参考实现只是候选，尚未向标准工作组提交；当前版本仍是 `eeo-dataset-review/0.5`，变更按 release/tag 走。

## 3 方法边界

- 阈值 τ、W、m 可以由买方声明；算子、度量、判定规则由 EEO-DSR 单方维护。买方声明阈值不等于联合署名方法。
- 预检产出带 `pre_check_not_a_record`，不是记录、不是认证、不是审计意见；正式记录仍要求委托方具名。
- 数据支撑不了推断时，输出不可算说明书，不输出点值。
- 不为了“达标”强行引入 BCa/studentized；偏斜下 percentile 欠覆盖作为方法论负结果发布，不伪装成 95%。

## 4 与当前研究读数的关系

`research/v0.6/reference-and-representation/2026-11-27-readout/README.md` 是本轮读数汇总；`research/v0.6/publication-audit/` 是公开状态核对；`research/v0.6/2026-11-27-recap/` 是复盘落实清单。三处都只描述读数与边界，不把“可签发”写成“已签发”。
