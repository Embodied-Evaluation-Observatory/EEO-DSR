# 自检覆盖对照表（self-test manifest）

`tools/validate_record.py --self-test` 的每个证伪用例给一个 ID；下表把校验规则与用例对上，供审查者核对"规则写了但没测"的缺口。

**覆盖率声明**：本表覆盖校验器规则 37 组，全部有对应证伪用例（记录 142 个 R01–R142、观测件 8 个 O01–O08）；另有 1 条语义项——对齐规则是否真的可执行——无自动用例，依赖人工复核标记 `applicable`，校验器只检查字段是否填了。

| 规则（方法层口径） | 证伪用例 ID |
|---|---|
| τ 由策略推出、可复算；EEO 不得自设 | R01, R11, R106, R107, R108 |
| m 由谁定、默认值署名 | R02, R06 |
| m 敏感性须含声明值与 m=2 / m=3 | R03, R04, R05 |
| W 声明与去重敏感性 | R08, R09, R10 |
| 度量属于方法，不得下放给买方 | R07, R29 |
| 默认套餐：用途阻断、显著声明、敏感性上摘要 | R87, R109, R86, R115, R116 |
| 同步由 EEO 自算、无外部依赖 | R12, R13 |
| 时间线免责固定句 | R20 |
| 观测件哈希可溯源 | R14 |
| 自验夹具：必须有、跑过、覆盖五类 | R15, R16, R17, R18, R19 |
| 六类计数闭合；降级二值、无加权比例 | R21, R22, R23 |
| 结构性故障分类、事件数与已识别不进未核验 | R74, R75, R103, R104, R105, R102 |
| 结构性后果随可界定性 | R33, R34, R35, R36, R37, R76, R38, R39 |
| 对齐规则：类型 + 出处 + 哈希 + 可适用性 | R77, R78, R79 |
| 链条四字段必须齐、逐个复算、未核验可见 | R24, R25, R26, R27 |
| 未核验不得超过池子 | R118 |
| 去重标定状态：未建立必须为空、不得夹带对象、建立必须给对象、绑定不得单独命名夹具 | R119, R120, R121, R122 |
| 去重检测器标定门（仅 established 分支）：夹具、对数、上界、已执行、哈希、runner 可执行 | R123, R124, R125, R126, R127, R133 |
| 度量身份与 W 绑定（family 枚举 / threshold_binding 对象） | R128, R129, R134 |
| 流连续性发现：计数与边界成对、只作附件、摘要可见 | R135, R136, R142 |
| 范围收缩显式声明：标注一致性、D1b、维度代码 DSR- 前缀 | R137, R138, R139 |
| 分散度决策映射：支持什么、不支持什么 | R140, R141 |
| 链条闭合等式 sync_filtered = n_pass + n_unverified | R130 |
| 全局 τ 注记必须印偏向 | R132 |

| 不清洗：去重不执行、计数可复算 | R28, R30, R31, R32 |
| 封顶：ρ 区间下端、按式重算、买方语言 | R45, R46, R47, R48, R85, R49, R43, R44 |
| NEES 状态与边界 | R50, R51, R52, R57, R58, R59, R60 |
| ρ 的依据带格式 | R53, R54, R55, R56 |
| 不可算：独立读数与去重条数存活 | R40, R41, R42, R61, R62 |
| 零失败界：两端 + 预算 + 决策映射 | R63, R64, R65, R66, R67, R68, R69 |
| 轨迹分散度：位置、门槛、本体、主读数固定 | R70, R72, R71, R80, R81, R82, R83, R101, R100, R73, R84 |
| 轨迹分层：不报裸总量、按层判门槛、摘要给层内分布 | R98, R99, R110, R111, R112, R113, R114 |
| 分级措辞与摘要 | R89, R90, R91, R92, R88, R96 |
| 单元与固定句 | R93, R94, R95 |
| 记录形状 | R97 |
| 观测件：无外部工具、判定与档位一致、故障不得判 pass | O01, O02, O03, O04, O05, O06, O07, O08 |

## 用例索引（记录）

| ID | 用例 |
|---|---|
| R01 | thresholds set by EEO |
| R02 | m missing |
| R03 | declared m absent from its sweep |
| R04 | sensitivity without m=2 |
| R05 | declared m=4 outside the sweep |
| R06 | m from EEO but not equal to its default |
| R07 | metric smuggled into thresholds |
| R08 | dedup w missing |
| R09 | declared w absent from its sweep |
| R10 | single dedup threshold |
| R11 | tau undeclared on verified sync |
| R12 | external timing tool cited as the source |
| R13 | clock model declared external |
| R14 | verified sync without an observation hash |
| R15 | verified sync without a fixture run |
| R16 | fixture run not fully passed |
| R17 | fixture with too few cases |
| R18 | fixture without a runner |
| R19 | fixture covering only late packets |
| R20 | scope note dropped |
| R21 | sync states do not close |
| R22 | degraded weighted instead of excluded |
| R23 | weighted degraded ratio reintroduced |
| R24 | chain does not close |
| R25 | chain field omitted |
| R26 | chain hides the unverified share |
| R27 | chain unverified share does not match |
| R28 | dedup executed on the corpus |
| R29 | dedup metric removed |
| R30 | distinct count does not recompute |
| R31 | exact copies exceed all copies |
| R32 | cross-split exceeds all duplicates |
| R33 | alignment executed anyway |
| R34 | excluded segment without its extent |
| R35 | segment outcome without excluded episodes |
| R36 | unknown extent still prints a number |
| R37 | unknown extent without its reason |
| R38 | alignment counted as fail only |
| R39 | unestimated alignment with a point value |
| R40 | unestimated alignment without diagnostics |
| R41 | alignment case hides the dedup count |
| R42 | alignment case still prints zero variance |
| R43 | unverified sync without a cap |
| R44 | unverified sync classified as pass |
| R45 | cap value does not recompute |
| R46 | cap at the point estimate instead of the low end |
| R47 | cap without rho_source |
| R48 | cap without the cluster-mean definition |
| R49 | upper bound with an interval |
| R50 | NEES exceeds pool |
| R51 | point value outside interval |
| R52 | computable on unmeasured rho |
| R53 | assumed rho without a typed basis |
| R54 | borrowed rho without a corpus id |
| R55 | sensitivity range without a range |
| R56 | measured rho without an interval |
| R57 | not computable prints a value |
| R58 | zero-variance dominance with a capped value |
| R59 | frame-wise split with a point value |
| R60 | split and axis disagree |
| R61 | n_dedup does not match the count |
| R62 | diagnostics without a basis |
| R63 | n_ind below the observed outcomes |
| R64 | dedup n_ind disagrees with the count |
| R65 | cluster-count n_ind disagrees with clusters |
| R66 | zero-failure bound off the closed form |
| R67 | cluster budget off the closed form |
| R68 | zero-failure budget dropped |
| R69 | decision note dropped |
| R70 | trajectory signal missing |
| R71 | trajectory computed across embodiments |
| R72 | trajectory computed upstream of dedup |
| R73 | trajectory signal as a NEES substitute |
| R74 | clock reset recorded as a spike |
| R75 | non-monotonic spike treated as a segment |
| R76 | unlocatable range with a guessed extent |
| R77 | documented rule without provenance |
| R78 | built-in rule without a reset point |
| R79 | rule marked inapplicable yet used |
| R80 | insufficient sample still computed |
| R81 | mixed embodiment carrying a value |
| R82 | variance cutoff as the main rule |
| R83 | spectral entropy presented as the main rule |
| R84 | trajectory value presented as cross-corpus comparable |
| R85 | cap without a buyer note |
| R86 | default package without its acceptance boundary |
| R87 | thresholds origin missing |
| R88 | summary header without the limitation text |
| R89 | sample tier without a scope statement |
| R90 | sample tier speaking for the corpus |
| R91 | sample tier without a cap basis |
| R92 | full tier carrying a sample cap |
| R93 | unit is a sample |
| R94 | use limitation rewritten |
| R95 | reference note dropped |
| R96 | buyer summary without a continuity line |
| R97 | six lines in the buyer summary |
| R98 | unknown top-level field |
| R99 | multi-task corpus published pooled |
| R100 | stratified reading without per-stratum entries |
| R101 | effective dimension dropped |
| R102 | spectral entropy mixed into the main count |
| R103 | identified fault carried as unverified |
| R104 | structural fault without its event count |
| R105 | spike crossing a boundary counted as an affected episode |
| R106 | spike affects more than two episodes |
| R107 | tau off its declared period |
| R108 | unknown pairing policy without a convention |
| R109 | pairing policy contradicted by its factor |
| R110 | default package without its notice |
| R111 | multi-task pooled dimension printed bare |
| R112 | multi-task total without its between-task share |
| R113 | stratum below the floor still prints a dimension |
| R114 | stratum median does not recompute |
| R115 | multi-task summary falls back to a bare total |
| R116 | default package notice omits the acceptance bar |
| R117 | default package without a sensitivity headline |
| R118 | chain unverified exceeds the pool |
| R119 | calibration status missing |
| R120 | unestablished calibration claims an object |
| R121 | established calibration missing |
| R122 | binding names a fixture without a calibration |
| R123 | calibration below the positive-pair floor |
| R124 | calibration merging distinct episodes |
| R125 | calibration upper bound above five percent |
| R126 | calibration not actually executed |
| R127 | calibration fixture hash missing |
| R128 | threshold binding disagrees with family |
| R129 | threshold binding W drifts from thresholds |
| R130 | chain filtered not an equation |
| R131 | dimension code without its prefix |
| R132 | global tau note hides its bias |
| R133 | calibration not passed |
| R134 | metric family unnamed |
| R135 | stream continuity count without boundaries |
| R136 | continuity note claims a NEES effect |
| R137 | scope declaration dropped |
| R138 | label consistency quietly assumed |
| R139 | dimension codes reused as a crosswalk |
| R140 | decision mapping dropped |
| R141 | decision overreach |
| R142 | spike crossing leaves no continuity trace |

## 用例索引（观测件）

| ID | 用例 |
|---|---|
| O01 | model version dropped |
| O02 | producer declares an external dependency |
| O03 | observation names an external tool |
| O04 | degraded below the band |
| O05 | pass above tolerance |
| O06 | fail on a non-fatal episode inside the band |
| O07 | clock reset carried as pass |
| O08 | unknown violation type |
