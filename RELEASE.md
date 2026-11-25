# EEO-DSR V0.2 发布说明

**V0.2 发布的是方法规格、记录与观测件规范、校验器、阈值声明表，以及首份 Phase 0 卡片初筛；不是任何语料的 NEES 读数，也不是对任何语料可用性的结论。**

- 版本：`EEO-DSR-V0.2`
- 日期：2026-11-25
- schema：`eeo-dataset-review/0.2`
- 观测件：`eeo-sync-observation/0.1`（未变）
- tag：`v0.2`

## 一、本版包含

| 层 | 内容 |
|---|---|
| 方法 | `METHOD.md`、`README.md`、`ENTRY.md`、`CITATION.md` |
| 规范 | `schema/record.schema.json`（0.2）、`schema/sync-observation.schema.json`（0.1） |
| 示例 | `schema/examples/` 七份记录与一份观测件，均为合成夹具，不是发出的记录 |
| 校验 | `tools/validate_record.py`、`tools/run_all_checks.py`、`tools/dedup_calibration.py`、`tools/self_test_manifest.md` |
| 声明 | `thresholds-declaration.md`、`entry/DATA_TERMS.md`、`entry/sampling-frame.md` |
| 初筛 | `checks/phase0_screen.py`、`checks/README.md`、`checks/dataset/2026-11-25/` |
| 许可 | `LICENSE`（代码 MIT）、`CITATION.md`（引用四项） |

本版相对 V0.1 的规范变化：

1. 去重标定门改为每类已知重复、已知相异各不少于 59 对，误合并率与误拆分率分开报，各给点值与 Clopper–Pearson 95% 上界；记录必须带 `executed`、`fixture_hash`、`result_hash`，runner 文件存在且实际执行并通过。
2. 去重度量拆成一个互不同义的枚举（`embedding_cosine` / `perceptual_hash` / `exact_byte`）加一个绑定对象 `{metric, w, calibration_fixture_id}`。
3. `buyer_summary` 必须有一行写“流连续性发现 n 条”，摘要读者能看见该发现；它仍不进 NEES 算式。
4. 维度代号统一加 `DSR-` 前缀（`DSR-D1` … `DSR-D5b`），与早期材料代号分开命名空间，不建 crosswalk。
5. `global_tau_note` 必须写明“取最严”与“NEES 偏低”；链条闭合改为等式 `sync_filtered = n_pass + n_unverified`。
6. Phase 0 初筛脚本入库，并跑出 2026-11-25 的首份结果。

## 二、Phase 0 结果

2026-11-25 抓取 12 张公开、无需登录或审批的 Hugging Face LeRobot 卡片。12 张中 12 张至少一项不通过：S1 分项覆盖、S2 条数/单位/帧率、S4 许可机器可读各 12 张 PASS；S3 版本与日期、S5 文件级校验和、S6 场景/工位标识各 12 张 MISSING。

这是卡片算术，不是核验结论，不说明语料可用性。逐卡 URL、抓取时 sha256 与逐项证据在 `checks/dataset/2026-11-25/cards.csv`。

## 三、复算

```
python3 tools/run_all_checks.py
python3 tools/dedup_calibration.py
python3 checks/phase0_screen.py
```

`run_all_checks.py` 覆盖 147 个自检用例、七份记录、观测件与 JSON Schema 交叉验证。`phase0_screen.py` 按固定 URL 清单重新抓取；同一日重复运行结果一致。

## 四、冻结与更正

本版文件哈希见 `SHA256SUMS`，按相对路径逐文件列出，可用 `sha256sum -c SHA256SUMS` 复核。冻结日期 2026-11-25。

已发布版本不静默修改。发现错误时发新版本（V0.3 起），在发布说明写明改了什么、为什么改、影响哪些字段；旧版本与其 tag 保留。引用须给 `method_version`、语料 id 与版本、检索日期、记录自身哈希。

## 五、本版不包含

- 任何真实语料的 NEES 读数。时钟模型、episode 指纹与簇级 bootstrap 尚未实现，`verified` 记录无法合法产生。
- 标签一致性核验与 D1b（卡片对索引）；两者在 `scope_declaration` 中声明未做及回归条件。
- 认证、评级、入表背书或采购建议。
