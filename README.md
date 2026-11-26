# EEO-DSR 数据集声明与标识层核验＋成功率精度层（V0.6 修订草案）

EEO-DSR 是数据集声明与标识层的独立核验器，和可复算的溯源尺；并提供成功率精度层的独立试次折算与区间。

它回答两类问题：公开声明能不能被第三方按同一口径复算；已声明的计数与标识能不能被唯一追溯。

它不回答“这份数据值多少钱”“能不能训出好模型”“合不合规”。

六维中能用计数与哈希回答的部分，做到可追问；需要读内容、跑模型、判合规的部分，明确标为“有界可建”或“不涉及”。输出读数，不输出结论。

标题保留“成功率精度层”：逐簇求和、单例分层、ρ-free 界、簇级 bootstrap、偏差/覆盖模拟、极端偏斜夹具是推断而非计数，且与 ρ 算在什么之上无关，是可复用资产。

> 本文是 V0.6 定位修订，统计逻辑未改；已发布到 `main`。

## 三种读数必须分开

| 读数 | 基底 | 回答什么 | 状态 |
|---|---|---|---|
| ITR 独立试次折算 | 二值结局 ICC | 给定簇轴上，成功率估计相当于多少独立试次 | 方法已跑通，读数待发布闸 |
| NEES 净有效 episode 量 | 二值结局 ICC ＋ D2 ＋ D5a | 扣除同步不合格与重复后的成功率精度 | D2/D5a 检测器未实现 |
| ICR 信息量读数 | 特征分散 | 语料承载多少独立内容信息，只给区间 | 路线保留，未建，带止损 |

NEES 即使补齐 D2 与 D5a，仍是结局基底，不是信息量。两条轨迹可以标签相同而内容完全不同；信息在二值化那一步已经丢弃。保留 ICR 的理由在此。

**三步链仍固定**：

```
raw → sync 筛选 → dedup 计数 → ITR / NEES
```

当前 ITR 不是 NEES；NEES 补齐后仍是结局基底。

## 三级交付

### 第 1 级：已跑通（可交付）

| 交付物 | 内容 | 边界 |
|---|---|---|
| 卡片口径明确性检查 | 两道顺序闸、四态 | 只查卡片文本可复算性；MISSING/AMBIGUOUS ≠ 数据差 |
| 集中度与覆盖读数 | 变化簇的 building/task 分布、top10/top20、簇大小分布 | 描述性；不判“够不够分散”；cell 轴标 45/93 空 instruction |
| 零失败界采样预算 | 10%→29、5%→59、1%→299 独立簇 | 采集设计工具；有失败样本不适用 |
| 溯源包 | 七项齐全 | 缺任一项不得引用为可复算 |
| 不可算说明书 | 原因、三个独立读数、关注方语言 | 合法输出，不是失败 |

### 第 1 级附：方法已通、读数待发

核验他人增益声称的统计有效性（Archive 核可辨识性与多重比较；DSR 供独立试次数、跨 split 泄漏计数、零方差占比）。跨模块交付需 Archive 侧配合。

首个 DROID 原生 scene 轴 ITR 已在本地研究目录跑通，读数未过三道发布闸；本 README 不印点值与区间，对外一页纸也不印。

## 发布闸 G1–G3

任何带区间的读数发行前必须全关。ITR 数字不进对外材料，直至三闸关闭。

| 闸 | 现状 | 关闭条件 |
|---|---|---|
| G1 簇键唯一性 | **已发现碰撞**：2,207 个 raw scene_id 中 9 个跨 >1 个 building、2 个跨 >1 个 robot_serial；这 9 个 id 覆盖 2,172 条 episode，占 73,413 的 2.96%。覆盖键仍是 `scene_id`，精度键改为 `scene_id｜building｜robot_serial`，重跑后 K=2,220。读数只留在研究目录，不印在本 README。仍未闭合：2,207 raw ≠ 论文 2,080 ≠ 564，564 语义去重未复现 | 564 的语义映射仍缺；不得把 2,207 或 2,220 写成论文 scene 数 |
| G2 覆盖率标定 | native composite 已跑 1,000 模拟 ×100 reps：覆盖率 0.910–0.938。cell 轴 B=25/100/500/2,000 各 1,000 模拟，B=2,000 覆盖率 0.838–0.936；另比了 percentile／basic／BC／BCa：percentile 在 8 个 ρ 中 7 个最好，ρ=0.90 仍只有 0.838，basic 0.739，BC 0.824，BCa 0.819。换区间名字不能修复 | 改估计量或区间构造（studentized／m-out-of-n／方差稳定变换）；或明写实际覆盖并禁止按名义 0.95 使用。ICR 在 G2 关闭前不建区间 |
| G3 行集一致 | 计数已对账：镜像 95,658、raw metadata 74,896，差 20,762；按 building 的差集中在 bww 5,219、gates 4,931、evgrc 1,779 等；镜像无 uuid、metadata 无 episode_index，精确交集仍无法构造 | 先建立 episode_index↔uuid 连接键；再取交集同批行重跑三轴；不得把 raw scene 行当作镜像子集 |

### 第 2 级：有界可建

按依赖重排：买方参照分布偏离度 → 指纹/特征表示 → 去重标定／ICR → 分级结局与时钟并行 → 标注一致性抽检（取数门）。

### 第 3 级：不涉及

模型增益验证、资产计价与入表背书、合规与符合性认定、排名评级合格结论、标注正确性认定、内容层准确性。

## 当前状态

| 部分 | 状态 |
|---|---|
| schema 与跨字段规则 | V0.5；V0.6 的 `readout` 迁移待做 |
| 校验器 | 可运行，`--self-test` 150 例按预期拒绝 |
| 去重检测器 | 不存在：没有 `episode-embedding-cosine-v1`，也没有硬负例夹具 |
| 时钟模型 | 只有规格与观测件格式，没有实现代码 |
| episode 指纹 / 簇级 bootstrap | bootstrap 已有研究脚本；指纹研究实现 `tools/feature_representation.py`，无真实特征矩阵 |
| 数据集侧驱动 | 研究实现，未发布：episode→簇、逐簇 n_eff、零失败界、预算、ρ 下端封顶 |
| ITR | 方法已跑通；DROID 原生 scene 读数未过发布闸，不进对外材料 |
| NEES 端到端 | 尚不可算：D2/D5a 未实现 |
| ICR | 路线保留，未建，带 F1–F3 与止损 |
| Phase 0 | 卡片口径明确性检查待迁移；旧披露度普查结果在 `checks/dataset/2026-11-26/` |

`schema/examples/` 里的记录是合成校验夹具，不是发出的记录；本模块至今未发出任何记录。

**现在能交付什么**：卡片口径明确性检查（四态）、集中度与覆盖读数、零失败界采样预算、溯源包、不可算说明书；ITR 方法已通，首个语料读数待三道发布闸。

**现在不能交付什么**：任何真实语料的 NEES 读数（D2/D5a 未实现）、ICR 数值、模型增益/合规/评级结论。

## 阈值都由买方声明：τ、W、m

τ、W、m 都写在 `thresholds` 里：谁声明的、依据哪份文件、至少两档敏感性。三个都会改变 episode 的去向或计数，
不能由 EEO 暗定。

m 的默认值是 3；用了默认值，记录写 `m_origin: eeo_default` 并在 basis 里说明。同步敏感性必须出现
m=2、m=3，以及声明的 m（若声明值不是 2 或 3）。

买方无法声明时（政府采购、平台验收），用明示的默认套餐：W=0.95、m=3，τ 由配对策略推出：
最近邻配对系数 0.5（最近样本最多半周期远），零阶保持系数 1.0（保持样本最长一整个周期）。记录写
`pairing_policy` / `tau_factor` / `period_basis` / `pairing_direction`，并用 `sampled_stream_period_ms`
或 `shortest_stream_period_ms` 复算。周期取被采样那条流的（相机帧配到最近状态样本，相关周期就是状态流的）；
方向不明时取最短并写"取最严"。卡片未声明策略时降回明示约定并封顶。敏感性保留 0.5 与 1.0 两档，
作为两种策略的对照，不是任意两点。

一个全局 τ 是简化，且有方向：30 Hz↔250 Hz 与 30 Hz↔30 Hz 的自然容差不同，全局 τ 取最严的那对强加给
所有对，可能多剔合格 episode，**NEES 偏低**；记录写 `tau_scope: global_simplified` 与 `global_tau_note`，
把偏向印出来，理想形态是逐流对 τ。

套餐记录写 `acceptance_use: not_declared_by_buyer`，印"本记录阈值系默认套餐，未获买方声明，不得作为验收
判定依据；验收方须自行声明阈值后重跑"，摘要显著位置印敏感性移动量。阻断按用途做，不按阶段做；
仓库附一页 `thresholds-declaration.md` 声明表，套餐是罕用兜底。

**W 与度量绑定。** 去重度量由方法固定：`neev.dedup.metric.family` 是互不同义的枚举
（`embedding_cosine` / `perceptual_hash` / `exact_byte`）；`threshold_binding` 是绑定对象
`{metric, w, calibration_fixture_id}`，写明 W 切在哪个度量上。余弦 0.95 与感知哈希 0.95 不是一回事，
不写度量，W 就只是一个裸常量。若让买方挑度量，就等于允许挑一个少算重复的度量。

**去重检测器尚不存在，本版不宣称已过门。** 记录字段 `neev.dedup.calibration_status` 只有两值：
`not_established`（默认，`calibration` 必须为 `null`，`threshold_binding.calibration_fixture_id` 也为 `null`）
或 `established`（仅当真实检测器与夹具存在时才可出现，届时须 ≥59 对已知重复、≥59 对已知相异，
FPR 与 FNR 分开报，各自印 Clopper–Pearson 95% 上界，runner 已执行并带夹具哈希与结果哈希）。
`tools/cosine_threshold_smoke.py` 只是余弦阈值 helper 的冒烟测试：随机单位向量加抖动，任何种子都会通过，
它不测检测器，也不测 `episode-embedding-cosine-v1` 的真实分布，不得引用为标定证据。

## 同步：自己算，六类判定

判定由 EEO 自己的时钟模型给出：量偏移、抖动、漂移、缺口，按声明的 τ 与 m 分档。不接外部工具、不引外部依赖。

| 判定 | 处理 | 对 NEES |
|---|---|---|
| 合格 `pass` | 进池 | 计入 |
| 降级 `degraded` | 留在语料、零权重 | 不计入 |
| 不合格 `fail` | 出池 | 其余照算 |
| 结构性段出池 `alignment_excluded` | `clock_reset` 段可定位，或 `non_monotonic_spike` 的实际条数 | 该范围出池，其余照算 |
| 结构性范围未知 `alignment_unlocatable` | 重置点不可定位，或异常无法定性、无法排除段级故障 | 全量不可算 |
| 未核验 `unverified` | 没有可用的时间戳，量不了 | 计入但封顶 |

轻抖动、录坏的、时间轴断的，是三件不同的事。结构性故障还分两类：`clock_reset` 是段级
（重置点之后整段失去同一基准），`non_monotonic_spike` 是孤立型，按"内部配对是否被破坏"计：
异常对跨边界且两侧各自单调 → 影响 0 条（另记 `stream_continuity_findings`：计数与边界，可复算，不进 NEES）；落在某条内部 → 1 条；被用来界定边界 → 2 条。
`n_events` 与 `affected_episodes` 分开记，一个事件可影响 0/1/2 条。不让一个单点把整段拖下水。

**本版不执行对齐**：时间轴断裂只报发现。对齐规则的出处记三样——`rule_type`（是否属于可复算的类别）、
`source`（规则在哪里）、`rule_hash`（规则有没有变），`applicable` 是人工复核标记，校验器只能检查字段。
后果只按可界定性路由：可定位则段（或 spike 的那几条）出池、其余照算；不可定位才让全量不可算。
已量到的故障不进 `unverified`——那是已识别的异常，不能按"未识别"进池。不存在"买方同意降级"这条路。

**时钟量的是记录时间线，不是物理同步。** 每份记录印一句：本核验只核验记录时间线自洽，不认定采集时物理同步。

观测件（`eeo-sync-observation/0.1`）由 EEO 时钟模型生成，不引用外部工具输出，字段口径由本模块定义；
随记录一起发布，作为可复算附件，记录只引其哈希。

时钟模型必须自带可执行夹具，覆盖迟到、丢帧、漂移、重置、非单调五类、至少 8 例且全过；只凑 8 个迟到用例不算验证。

## 核验，不清洗

`neev.dedup.executed` 恒为 `false`，`nees.cleaning` 恒为 `not_performed`。EEO 数出重复、报出重叠，
但不在语料上删任何一条。

"同一内容"按写死的口径判：一个方法固定的度量、一个买方声明的 W，DSR-D5a 与 DSR-D5b 共用；字节完全相同的副本
单列为 `n_exact_copies`，是副本总数的子集。

| 项 | 问什么 | 去向 |
|---|---|---|
| DSR-D5a 语料内重复 | 有多少条是同一内容算了两遍 | 进 NEES 计数 |
| DSR-D5b 跨 split 泄漏 | 有多少重复横跨训练与测试 | 评测有效性发现，不进 NEES |

## 五个维度、六个检查项

| 项 | 问什么 |
|---|---|
| DSR-D1 声明自洽 | 卡片上的数能不能自己算平 |
| DSR-D2 时序合格 | 各模态是否在描述同一时刻 |
| DSR-D3 覆盖 | 覆盖了哪些工位、物体、失败模式，哪些是空格 |
| DSR-D4 溯源 | 这批字节可不可复算 |
| DSR-D5a 语料内重复 | 多少条是同一内容算了两遍 |
| DSR-D5b 跨 split 泄漏 | 多少重复横跨训练与测试 |

只有 DSR-D2 与 DSR-D5a 进 NEES；DSR-D1、DSR-D3、DSR-D4、DSR-D5b 是与 NEES 并列的读数。DSR-D1 不是 Phase 0 的结果：
Phase 0 的 linter 独立发布，记录里的 DSR-D1 是在记录语境下重新跑的卡片检查。

**本版不做标注一致性，也不做 DSR-D1b（卡片对索引）。** 六项里没有一项碰标签，所以"标签能否直接进训练管线"
本版没有读数；这是产品范围的收缩，不是措辞调整，写在记录的 `scope_declaration` 里，并说明理由与何时补。
DSR-D1–DSR-D5b 是本模块局部代号，不与早期材料做 crosswalk。

## 两个级别，两种措辞

| 级别 | 覆盖 | 措辞 |
|---|---|---|
| T1_sample | 抽到的 episode | 样本内读数，封顶，说"抽到的"，标明是上界 |
| T2_full | 全量 episode | 全量读数，仍明确未执行清洗 |

T1 的 `n_declared` 是抽样量，不是语料总量。T1 在 T2 发布后不撤回；引用以 T2 为准。

## 封顶与不可算

封顶是一条能复算的式子：`bound = n_dedup / (1 + (mean_cluster_size - 1) * rho_low)`，
其中 `mean_cluster_size = n_dedup / n_clusters`（层级与 `cluster.level` 一致），
**ρ 取区间下端**——ρ 越小读数越大，点值或中值都不是上界。不等簇是近似，记录须印这条定义。
**这个式子只在 ρ 有区间估计时适用**；ρ 完全不可估计时不输出 bound，走"不可算"三读数路径。

买方语言一并印出：封顶值假设 ρ 取区间下端；若实际 ρ 更高，真实 NEES 会更低。封顶是上界，不是估计值。

零失败上界用精确式 `1 - 0.05^(1/n_ind)`；`3/n` 只是 n 较大时的近似，小 n 不用。**两端都印**：
`upper95_by_cluster`（假设簇内完全同命运，保守端）与 `upper95_by_dedup`（假设完全独立，偏窄端），真值在两者之间。
`n_ind` 的主口径取簇数；取去重条数时必须写明"未扣残余聚类，上界偏窄"。

另印 `cluster_budget`：要压到 10% 需 29 个独立簇、5% 需 59 个、1% 需 299 个。买方看到"6 簇"，该拿到的是
"还差 23 个簇才能声称 10%"。`decision_note` 写明这个宽界撑不起什么。

不可算分三种：零方差占优、对齐范围未知、其他（切分未声明等）。读数各自独立、各带口径，
**不是 NEES 的分项，不能相加**。对齐不可算时，去重后条数照报（它不依赖时间轴），零方差占比标记为不可算。

不可算的买方语言：当数据无法支撑统计推断时，本核验报告"不可算"及原因，不输出点值——这是为了避免给出一个
看似精确但无依据的数字。

一句风险说明要写进摘要：未核验的封顶是上界，不代表数据质量好于降级；降级是已识别的风险，未核验就是"量不了"。
检测到但定不了性的断裂走 `alignment_unlocatable`，不进未核验。

链条印成四个字段：`chain.sync_filtered`（合格 + 未核验）、`chain.sync_unverified`（其中未核验的条数）、
`chain.dedup_count`（去重后条数）、`chain.nees`（读数或 `null`）；空值写 `null` 不省略。池子不再是一个
不可拆的总数，读者能看出多少条是量不了的。

摘要页顶部先整段印 `EEO-DUL-2`（`buyer_summary_use_limitation`，与记录中 `use_limitation` 同文），再给读数。

## 轨迹分散度：NEEV 下游的一行

NEES 说买到了多少独立证据；轨迹分散度说这些证据的形状有多分散。它算在去重后的池上，
写在记录里的一行 `trajectory_diversity_signal`。

- **不给阈值**："多少维算够"取决于买方的任务多样性需求，EEO 只报"去重后池子在策略空间的有效维度数"，不判够不够。
- **主读数固定为参与比** (Σλ)²/Σλ²：无截断、确定。主口径固定是跨记录比较的必要条件，不是充分条件；
  表示法与分层仍不同，跨语料比较继续受这两条限制。
- **分层**：同一本体跨任务，任务多样性会冒充策略多样性。`task_count > 1` 必须按任务分层逐层报，
  `pooled` 只允许单任务。多任务不给裸的总分散度：摘要印层内中位数、范围、可算/样本不足层数；
  技术段若要印 `pooled_total`，必须同时印 `between_task_share`。
- **样本门槛**：`n_dedup ≥ 50` 才算；单任务按池判，多任务**按层判**，不达标的层标 `insufficient_sample`。
- **本体边界**：只允许单一 embodiment；`mixed` 标 `not_computable_mixed_embodiment`，不输出数值。
- **摘要可见**：流连续性发现不进 NEES 算式，但摘要必须有一行 `流连续性发现 n 条`，不许只藏在技术段。
- **决策映射**：支持"是否要求供应商在某个任务内增加做法变化"，不支持"这份语料能否训出更好的策略"；
  两句都写进记录，否则这个数无处可用。
- **两句固定说明**：不是 NEES 的替代；主口径固定是跨记录可比的必要条件，不是充分条件，跨语料比较仍受
  表示法与分层限制；本值仅在单一 embodiment 内可解释。

## 这不是什么

不以任何标准为判定依据。参考了 YD/T 6771—2026 的维度划分思路，但五个维度是独立定义的，不构成对照关系；
不引其条款与阈值，也不声明相符（`EEO-RN-3`）。

不是采购建议、不是资产估值、不是尽职调查意见、不是标注正确性核验（`EEO-DUL-2`）：

> 本核验只给出该数据集在 episode 层面的统计可用性读数，不说明任务难度匹配、不说明标注正确性、
> 不构成资产估值、不构成采购建议。

## 入口与开源

入口按"带什么材料"分，不按"你是谁"分：

| 入口 | 拿到什么 | 产出 | 前置 |
|---|---|---|---|
| 公开卡片 | 已发布的卡 | 披露度普查（免费） | 无，无需登录与许可 |
| 委托样本 | 卡＋样本＋标签＋场景 id | 采购前数据体检（付费） | 阈值声明表、样本框声明、DATA_TERMS |
| 全量 | 语料与记录 | 深度核验 | 同上＋数据协议与算力 |

公开入口是"工具自己走路"的机制：Phase 0 页面任何人可看、供应商可自己跑。委托的三件前置在出数前完成；
验收方走不动声明流程时落默认套餐，记录显著印"不得作为验收判定依据"。

界面是装甲不是风格：无分数、无评级、无排行榜、无形容词；FAIL 格同时显示声明值与重算值；
按字母或日期排，不按失败数排；聚合只写两个集合分布："m 份中 n 份至少一项 FAIL，k 份至少一项 MISSING"；每页顶部先整段印用途限定。
中文只用"披露度普查 / 采购前数据体检 / 深度核验"三个名字。委托即公开、委托方具名；认证、评级、
入表背书没有入口。

开源三段式：代码 MIT、本模块计算产出 CC-BY-4.0、第三方字段依源方条款。方法、schema、校验器、
纯算术、披露度普查脚本、观测件格式，以及实现后的时钟模型与去重检测器连同夹具，全部开源——"每一项都能被第三方按同一口径
复算"就是产品本身。语料与样本、买方私有件、未发出草稿、委托报价不公开。

付费买的是"在委托方样本上、按委托方声明的阈值、出一份带日期、可复算、委托方具名的记录"。
fork 防伪靠三层可验证性：用途限定必填且校验器拒收剥掉的记录；引用须给方法版本、语料 id 与版本、
日期、记录哈希；代码可自由用，但不得自称本模块。详见 `ENTRY.md`。

## 目录

| 路径 | 内容 |
|---|---|
| `METHOD.md` | 方法：单元、切分、五维与 NEES 的关系、阈值归属、六类同步判定与结构性故障映射、去重发现、NEES 数学、封顶公式、精确零失败界、轨迹分散度、引用规则、放弃条件 |
| `schema/record.schema.json` | 记录规范形式（`eeo-dataset-review/0.5`） |
| `schema/sync-observation.schema.json` | 时钟观测件（`eeo-sync-observation/0.1`） |
| `schema/examples/record-example.json` | 全量、同步已核验、可算 |
| `schema/examples/record-example-unestimable.json` | 不可算（零方差占优），分散度仍可算 |
| `schema/examples/record-example-degraded.json` | 样本级、同步未核验、封顶 |
| `schema/examples/record-example-alignment-segment.json` | 结构性段出池、其余可算 |
| `schema/examples/record-example-alignment-unlocatable.json` | 结构性范围未知、NEES 不可算 |
| `schema/examples/record-example-default-package.json` | 默认套餐：用途阻断、敏感性上摘要 |
| `schema/examples/record-example-multitask.json` | 多任务分层：层内中位数，不印裸总量 |
| `schema/examples/sync-observation-example.json` | 观测件示例 |
| `tools/validate_record.py` | 执行层：0 通过、1 不合法、2 用法；`--self-test` 跑证伪用例 |
| `tools/run_all_checks.py` | 一次跑完自检、全部示例、观测件与 JSON Schema 交叉验证 |
| `tools/cosine_threshold_smoke.py` | 余弦阈值 helper 的冒烟测试；不是去重检测器标定，不带门 |
| `thresholds-declaration.md` | 一页阈值声明表，验收方自行声明阈值后重跑 |
| `tools/self_test_manifest.md` | 规则与证伪用例的对照表：哪条规则由哪个用例守住 |
| `STATUS.md` | 当前存在什么、不存在什么、各版本状态与纠正政策 |
| `RELEASE_GATE.md` | 发布门：冻结清单、预检记录、tag 不移、纠错发新版本 |
| `tools/freeze_release.py` | 冻结一个版本的逐文件清单；已存在则拒绝 |
| `tools/release_preflight.py` | 发布前复算冻结清单、全量检查，写 `preflight.json` |
| `releases/v0.5/manifest.json` | V0.5 冻结清单 |
| `.github/workflows/reproduce.yml` | CI：每次 push/PR 跑自检、示例与 schema |
| `ENTRY.md` | 三个入口、界面硬约束、开源范围与 fork 防伪 |
| `LICENSE` | MIT（代码）；名称与记录格式标识不在授权范围内 |
| `CITATION.md` | 引用必给四项：方法版本、语料 id 与版本、日期、记录哈希 |
| `entry/DATA_TERMS.md` | 委托样本文档模板：要文件不要链接、用后删除、禁止再分发 |
| `entry/sampling-frame.md` | 样本框模板：committed（规则哈希与种子）或 supplier-provided（封顶） |
| `checks/README.md` | 卡片口径明确性检查规则（两道闸、四态） |
| `checks/cards-source.csv` | Phase 0 输入：`dataset_id` 与公开卡片 URL |
| `tools/screen_cards.py` | 抓卡、双哈希、跑 S1–S6，写出 CSV/HTML/README/manifest |
| `checks/dataset/2026-11-25/` | V0.3 的旧版 Phase 0 结果，保留但不改写 |
| `checks/dataset/2026-11-25-r2/` | V0.4 结果：12 张 LeRobot 卡片、双哈希 |
| `checks/dataset/2026-11-26/` | V0.5 结果：20 张异源页面、可判率、FAIL/MISSING 分开 |

## 校验

```
python3 tools/validate_record.py schema/examples/record-example.json
python3 tools/validate_record.py schema/examples/record-example-alignment-unlocatable.json
python3 tools/validate_record.py --sync schema/examples/sync-observation-example.json
python3 tools/validate_record.py --self-test
python3 tools/run_all_checks.py   # 自检 + 全部示例 + 观测件 + jsonschema，CI 用这一条
```

`run_all_checks.py` 是 CI 入口：`.github/workflows/reproduce.yml` 在每次 push 与 PR 上跑这一条，任一示例或自检不过即非零退出。

schema 管不了、由校验器执行的规则：阈值（含 m）由谁定、声明值必须进敏感性档、同步敏感性缺 m=2/m=3/声明值、
度量不得下放给买方、时钟模型不得声明外部依赖、已核验却未跑夹具或覆盖不全、六类计数必须闭合、
降级不得计入且不得出现加权比例、对齐不得执行、结构性故障后果必须与可界定性一致、
四个链条字段必须齐（空值写 `null` 不省略，且 `sync_filtered = n_pass + n_unverified`、`sync_unverified ≤ sync_filtered`）、
不可算必须给带口径的独立读数且不得印点值、封顶 ρ 必须取区间下端并按式重算、
零失败必须两端都印并合精确式、轨迹分散度必须在去重后池上、单一本体且按任务分层、样本级不得替整份语料说话。

## 引用

引用时给 `method_version`、语料 id 与版本、检索日期、记录自身哈希，以及级别（T1/T2）。
披露度普查、样本级记录、全量记录三者不可互换，也不得用于它没有覆盖的语料。

## License

代码采用 MIT 许可；名称、记录格式标识与发布物标识不在授权范围内。全文见 [`LICENSE`](LICENSE)。
