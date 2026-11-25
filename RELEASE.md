# EEO-DSR V0.3 发布说明

**V0.3 发布的是方法规格、记录与观测件规范、校验器、发布门，以及 2026-11-25 的 Phase 0 卡片初筛；不是任何语料的 NEES 读数，也不是对任何语料可用性的结论。**

- 版本：`EEO-DSR-V0.3`
- 日期：2026-11-25
- schema：`eeo-dataset-review/0.3`
- 观测件：`eeo-sync-observation/0.1`（未变）
- tag：`v0.3`

## 一、本版包含

| 层 | 内容 |
|---|---|
| 方法 | `METHOD.md`、`README.md`、`ENTRY.md`、`CITATION.md`、`STATUS.md` |
| 规范 | `schema/record.schema.json`（0.3）、`schema/sync-observation.schema.json`（0.1） |
| 示例 | `schema/examples/` 七份记录与一份观测件，均为合成夹具，不是发出的记录 |
| 校验 | `tools/validate_record.py`、`tools/run_all_checks.py`、`tools/self_test_manifest.md` |
| 发布门 | `RELEASE_GATE.md`、`tools/freeze_release.py`、`tools/release_preflight.py`、`releases/v0.3/` |
| 初筛 | `checks/phase0_screen.py`、`checks/README.md`、`checks/dataset/2026-11-25/` |
| 许可 | `LICENSE`（代码 MIT）、`CITATION.md`（引用四项） |

本版相对 V0.2 的变化：

1. **撤回去重标定门。** 去重检测器尚不存在；`neev.dedup.calibration_status` 新增，当前只能写
   `not_established`，此时 `calibration` 必须为 `null`，`threshold_binding.calibration_fixture_id` 也为 `null`。
   `established` 路径保留给真实检测器，校验器要求 ≥59 对、FPR/FNR 分开、精确上界、已执行与双哈希。
2. **余弦 helper 降级为冒烟测试。** `tools/cosine_threshold_smoke.py` 用随机单位向量与 σ=0.005 抖动，
   任何种子都通过；它不测检测器，也不测 `episode-embedding-cosine-v1`。W 由 `--w` 传入，不再写死在源码里。
   输出明确标 `gate: false`，不带 `passed`，不得引用为标定证据。
3. **补发布纪律。** `STATUS.md` 写清存在与不存在；`RELEASE_GATE.md` 规定冻结清单、预检记录、tag 不移、
   纠错发新版本；`tools/freeze_release.py` 拒绝覆盖已冻结版本；`tools/release_preflight.py` 写
   `preflight.json`，记录是文件不是声称。
4. **补 CI。** `.github/workflows/reproduce.yml` 在每次 push 与 PR 上跑自检、示例、观测件与 schema 交叉验证。
5. **修方法与文本冲突。** `m` 默认值 3 不再写成"3 倍容差覆盖多数抖动"；本版明确它没有可复算依据，
   默认使用时 `basis` 写 `no_declared_basis`，不得作为验收依据。`neev.chain` 保持四个字段并逐字段复算。

## 二、Phase 0 结果

2026-11-25 抓取 12 张公开、无需登录或审批的 Hugging Face LeRobot 卡片。12 张中 12 张至少一项不通过：
S1 分项覆盖、S2 条数/单位/帧率、S4 许可机器可读各 12 张 PASS；S3 版本与日期、S5 文件级校验和、
S6 场景/工位标识各 12 张 MISSING。

这是卡片算术，不是核验结论，不说明语料可用性。逐卡 URL、抓取时 sha256 与逐项证据在
`checks/dataset/2026-11-25/cards.csv`。

## 三、复算

```
python3 tools/run_all_checks.py
python3 tools/cosine_threshold_smoke.py --w 0.95
python3 checks/phase0_screen.py
python3 tools/release_preflight.py --version v0.3
```

`run_all_checks.py` 覆盖 150 个自检用例、七份记录、观测件与 JSON Schema 交叉验证。
`phase0_screen.py` 按固定 URL 清单重新抓取；同一日重复运行结果一致。

## 四、冻结与更正

本版文件哈希见 `SHA256SUMS` 与 `releases/v0.3/manifest.json`；发布前预检记录在
`releases/v0.3/preflight.json`。冻结日期 2026-11-25。

已发布版本不静默修改，tag 不移、不删、不 force push。发现错误时发新版本，在发布说明写明改了什么、
为什么改、影响哪些字段；旧版本与其 tag 保留。引用须给 `method_version`、语料 id 与版本、检索日期、
记录自身哈希。

## 五、本版不包含

- 任何真实语料的 NEES 读数。时钟模型、episode 指纹与簇级 bootstrap 尚未实现，`verified` 记录无法合法产生。
- 去重检测器与硬负例夹具；因此没有任何去重误判率读数。
- 标签一致性核验与 D1b（卡片对索引）；两者在 `scope_declaration` 中声明未做及回归条件。
- 认证、评级、入表背书或采购建议。
