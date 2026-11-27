# 2026-11-27 复盘落实清单

本页是复盘后的执行对照记录，不是策略文件。它只回答：哪条已落地、哪条只是计划、哪条仍不做。所有“已落地”都指 worktree，不代表已 commit/push。

## 1 生态位与交付边界

- **落地**：`README.md` 的定位段改为“送检前自检核验”：声明是否自洽、样本结构缺口、证据链是否完整；明确“不保证送检通过”。
- **落地**：`MINIMAL-SIGNABLE.md` 把可签发集与“不能说什么”并列；溯源包/行数账/卡片检查只作为存在性与完整性核验读数，ITR 只说明成功率精度，不证明记录条数。
- **不做**：估值、入表背书、合规认定、审计意见、评级。

## 2 路径一：ITR 欠覆盖，不强行达标

- **已落地**：`nominal_95_claim: not_permitted` 保持；G2 实测覆盖 0.910–0.938（native composite，1,000×100）与文本单元 B=2,000 的 0.838–0.936 作为区间方法标签保留；不贴点值。
- **已落地**：`research/v0.6/variance-probe/2026-11-26-g3-single-source/three-axis.json` 的单源三轴（site/task_text/native，73,413 行）已有 point ρ/n_eff；`ITR-READOUT.md` 明确不把镜像 `building||language_instruction` 文本单元轴叫 task 轴，也不与单源轴并列。task_text 的 K=2,432 vs 2,418 未对账，列发布前阻塞。
- **已落地**：配对连续量比较（宽度/端点）与旧 c=0 区间撤回，见 `../variance-probe/2026-11-27-cell-paired/`。
- **未做**：站点 energy 的 0.9 子采样比例敏感性；0.9 是可调参数。主口径仍是两个单边基；合并拟合基未实现，下一版再改成“合并基主口径、两个单边敏感性”。越界比例已从站点读数撤下。
- **仍不做**：不把 BCa/studentized 当作“修到 0.95”的发布门；不把 ρ-free 界写成条件区间。
- **待完成**：把“偏斜分布下簇 bootstrap 欠覆盖”整理成方法论短文；本轮未投稿。

## 3 路径二：Phase 0 基线

- **已有**：20 张普查（旧三态口径，四态未重跑），0 FAIL / 20 MISSING；S1/S2/S3/S5/S6 可判 0/20，S4 12/20。另 2 张补充（RoboMIND/RH20T）在 `../../../checks/dataset/2026-11-26-r2-robomind-rh20t/`，两个目录，不合并。
- **未做**：扩到 50–100 张、公开 Dashboard、任何人输入 URL 一键生成报告。当前只是基线，不是行业结论。
- **下一步**：先补输入源与抓取稳定性，再扩样本；不把 20 张的分布外推到“行业”。

## 4 路径三：分层预检

- **已落地**：`entry/PRECHECK_LAYER.md` 已写层 0/1/2；层 2 本地日志只含输入哈希，带 `pre_check_not_a_record`，官方 schema/validator 拒收；公开登记册只收 `n_prechecks` / `n_formal_entry` 聚合数，当前 entries 为空，不编 N/M。
- **已落地**：层 2 不提供排他/embargo；正式记录用 `submitter.prior_prechecks` 披露“曾有预检及日期”。
- **边界**：层 1 是公开卡片普查，不是“预核验”；层 2 不是记录，不是认证，不是审计意见。

## 5 路径四：schema 参考实现候选

- **已落地**：`schema/REFERENCE-IMPLEMENTATION.md` 说明候选状态、版本与变更节奏。
- **未做**：尚未向标准工作组提交；不声称已被采纳。

## 6 行动指南落地状态

| 项 | 状态 |
|---|---|
| G2 覆盖率按网格落盘、绑定标签 | 已完成研究层；`nominal_95_claim` 仍禁止 |
| 发布 DROID ITR 单源三轴点值 | 研究读数已有；条件区间未发布；task_text 受 tie-break 未对账阻塞 |
| 最小可签发集 | 清单已落地，见 `../../../MINIMAL-SIGNABLE.md` |
| Phase 0 扩到 50–100 张 | 未执行 |
| Linter Dashboard | 未建 |
| 三等价类声明 | 已落地，`../reference-and-representation/2026-11-27-equivalence-classes/` |
| 溯源包 PDF/CSV 接口 | 未封装 |
| DSB1.0 / DSR1.0 | 未封装 |
| 层 2 企业试点 | 未启动 |
| 方法论论文 | 未投稿 |

## 7 内部实验

- **I1 MLE 对照**：未执行。原因：在同一文本单元网格上做 300×B=2,000 的 beta-binomial MLE + percentile，优化成本远高于现有矩估计工具；未用低 B 冒充结果。
- **I2 VST 一格**：未执行。VST/studentized 仍在研究层，不插发布队；先要有可复算的变换与覆盖证据。
- **I3 studentized**：不做。6,602 簇 × B=2,000 × 1,000 次 jackknife 成本撞墙；近似变体要另行标定。
- **I4 m-out-of-n**：排队；必须在 ≥2 个不同尺寸分布上验证，避免过拟合。
- **I5 时钟模型/D5b/买方参照**：不催外部输入；没有就不输出。

## 8 结论

本轮把“复盘意见”转成可检查的边界，而不是新增算子：可签发集有清单，负结果有落点，预检有三层，公开状态有核对；未完成项明确写成“未做”。VST/studentized 不在发布闸内。
