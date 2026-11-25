# EEO-DSR V0.4 发布说明

**V0.4 发布的是方法规格、记录与观测件规范、校验器、发布门，以及 2026-11-25 的 Phase 0 卡片初筛；不是任何语料的 NEES 读数，也不是对任何语料可用性的结论。**

- 版本：`EEO-DSR-V0.4`
- 日期：2026-11-25
- schema：`eeo-dataset-review/0.4`
- 观测件：`eeo-sync-observation/0.1`（未变）
- tag：`v0.4`

## 一、本版包含

| 层 | 内容 |
|---|---|
| 方法 | `METHOD.md`、`README.md`、`ENTRY.md`、`CITATION.md`、`STATUS.md` |
| 规范 | `schema/record.schema.json`（0.4）、`schema/sync-observation.schema.json`（0.1） |
| 示例 | `schema/examples/` 七份记录与一份观测件，均为合成夹具，不是发出的记录 |
| 校验 | `tools/validate_record.py`、`tools/run_all_checks.py`、`tools/self_test_manifest.md` |
| 发布门 | `RELEASE_GATE.md`、`tools/freeze_release.py`、`tools/release_preflight.py`、`releases/v0.4/` |
| 初筛 | `checks/cards-source.csv`、`tools/screen_cards.py`、`checks/README.md`、`checks/dataset/2026-11-25-r2/` |
| 许可 | `LICENSE`（代码 MIT）、`CITATION.md`（引用四项） |

本版相对 V0.3 的变化只有 Phase 0：

1. **输入改为一个源清单。** `checks/cards-source.csv` 只含 `dataset_id` 与 `url`；脚本不再把 12 个 URL
   硬编码在源码里。起步 12 张，范围 10–20 张，按本模块的纳入规则重筛：公开可访问、无需审批、
   卡片至少声明 episode 总数、场景数与许可中的两项可检查字段。
2. **S1 按方法文本执行。** `checks/README.md` 一直写的是“分场景计数之和与声明总数”，V0.3 的脚本实际
   测的是 `splits` 连续区间，两者不是一回事。V0.4 的 `tools/screen_cards.py` 改为解析 `scene_count`
   与 `per_scene_episodes`，没有分场景计数时记 MISSING；有计数但不平才记 FAIL。
3. **双哈希落盘。** 原始页面字节算 `page_sha256`；结构化字段按固定字段顺序、无空格 JSON 序列化，
   附检索日期，算 `card_sha256`。两者逐卡写入 `cards.csv` 与 `manifest.json`。
4. **汇总拆成两个集合分布。** 不再只写“n 张至少一项不通过”，改为
   “m 张中 n 张至少一项 FAIL，k 张至少一项 MISSING；两项都有的 j 张”。MISSING 是字段没公布，
   FAIL 是已公布的数算不平；放弃条件问的是后者，不能用一个混合计数代替。
5. **manifest_sha256 固定输出目录。** 脚本先写 `cards.csv`、`index.html`、`README.md`，再写
   `manifest.json`（含三个输出文件的哈希），最后写 `manifest.sha256`。
6. **同日重跑不覆盖。** 输出目录已存在时脚本拒绝写入；同一天第二次运行改用
   `checks/dataset/<YYYY-MM-DD>-r2/`，再往后 `-r3`。V0.3 的 `checks/dataset/2026-11-25/` 保留原样。
7. **第一版自动解析，不冒充人工转录。** README 逐目录写明“自动解析自钉住的页面字节；没有人工转录”。
   以后若改为人工转录，必须写“转录自钉住页面”。

## 二、Phase 0 结果

2026-11-25 抓取 12 张公开、无需登录或审批的 Hugging Face LeRobot 卡片。结果：

- 12 张中 **0 张至少一项 FAIL，12 张至少一项 MISSING；两项都有的 0 张**。
- S2 条数/单位/帧率、S4 许可机器可读各 12 张 PASS。
- S1 分场景计数、S3 版本与日期、S5 文件级校验和、S6 场景/工位标识各 12 张 MISSING。

S1 全部 MISSING 的原因是这 12 张 LeRobot 卡片都给了 `total_episodes` 和 `total_tasks`，但没有
`scene_count` 与 `per_scene_episodes`；不是它们的加法算错了。V0.3 的旧结果说“12 张至少一项不通过”，
其中 12 张由 MISSING 撑起，读不出这个区别；V0.4 的汇总把两者分开。

这是卡片算术，不是核验结论，不说明语料可用性。逐卡 URL、双哈希与逐项证据在
`checks/dataset/2026-11-25-r2/cards.csv`；清单哈希在 `checks/dataset/2026-11-25-r2/manifest.sha256`。

## 三、复算

```
python3 tools/run_all_checks.py
python3 tools/cosine_threshold_smoke.py --w 0.95
python3 tools/screen_cards.py --date 2026-11-25 --out checks/dataset/2026-11-25-r3
python3 tools/release_preflight.py --version v0.4
```

`run_all_checks.py` 覆盖 150 个自检用例、七份记录、观测件与 JSON Schema 交叉验证。
`screen_cards.py` 对新目录重新抓取；输出目录已存在时拒绝写入，不会原地改写旧结果。

## 四、冻结与更正

本版文件哈希见 `SHA256SUMS` 与 `releases/v0.4/manifest.json`；发布前预检记录在
`releases/v0.4/preflight.json`。冻结日期 2026-11-25。

已发布版本不静默修改，tag 不移、不删、不 force push。发现错误时发新版本，在发布说明写明改了什么、
为什么改、影响哪些字段；旧版本与其 tag 保留。V0.3 的 `checks/dataset/2026-11-25/` 与
`checks/phase0_screen.py` 留在 V0.3 tag 内；V0.4 用新目录和新脚本，不改旧结果。

## 五、本版不包含

- 任何真实语料的 NEES 读数。时钟模型、episode 指纹与簇级 bootstrap 尚未实现，`verified` 记录无法合法产生。
- 去重检测器与硬负例夹具；因此没有任何去重误判率读数。
- 标签一致性核验与 D1b（卡片对索引）；两者在 `scope_declaration` 中声明未做及回归条件。
- 认证、评级、入表背书或采购建议。
