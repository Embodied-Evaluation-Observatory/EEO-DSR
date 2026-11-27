# EEO-DSR V0.5 发布说明

**V0.5 发布的是方法规格、记录与观测件规范、校验器、发布门，以及 2026-11-26 的 Phase 0 披露度普查；不是任何语料的 NEES 读数，也不是对任何语料可用性的结论。**

- 版本：`EEO-DSR-V0.5`
- 日期：2026-11-26
- schema：`eeo-dataset-review/0.5`
- 观测件：`eeo-sync-observation/0.1`（未变）
- tag：`v0.5`

## 一、本版包含

| 层 | 内容 |
|---|---|
| 方法 | `METHOD.md`、`README.md`、`ENTRY.md`、`CITATION.md`、`STATUS.md` |
| 规范 | `schema/record.schema.json`（0.5）、`schema/sync-observation.schema.json`（0.1） |
| 示例 | `schema/examples/` 七份记录与一份观测件，均为合成夹具，不是发出的记录 |
| 校验 | `tools/validate_record.py`、`tools/run_all_checks.py`、`tools/self_test_manifest.md` |
| 发布门 | `RELEASE_GATE.md`、`tools/freeze_release.py`、`tools/release_preflight.py`、`releases/v0.5/` |
| 普查 | `checks/cards-source.csv`、`tools/screen_cards.py`、`checks/README.md`、`checks/dataset/2026-11-26/` |
| 许可 | `LICENSE`（代码 MIT）、`CITATION.md`（引用四项） |

本版相对 V0.4 的变化：

1. **页首硬话。** README 与页面顶部固定写：
   “本集合 0 项 FAIL 不代表卡片自洽；S1 在 20 张卡上全部不可判。”
   0 FAIL 不再允许被读成好消息。
2. **集合级可判率。** 每项给出 `(PASS+FAIL)/m`，并判定为“不可判 / 无可区分信号 / 有区分”。
   这是集合分布，不是单卡评级。当前 S1/S2/S3/S5/S6 可判 0/20；S4 可判 12/20 且全 PASS，判为
   “无可区分信号”。
3. **放弃/分支条件。** 某项 100% MISSING 判为不可判，不得计入通过；全部行同构时声明“本集合上无区分信号”。
   当前状态组合 2 种，不触发整集合同构声明。
4. **S2 收紧。** 不再因为 `total_episodes`、`total_frames`、`fps` 同时存在就 PASS。脚本先算并印出
   `frames/episode` 与 `seconds/episode`，只有卡片另声明 `frames_per_episode` 或 `seconds_per_episode`
   且与重算在 1% 内一致时才 PASS；没有声明记 MISSING。12 张 LeRobot 卡片都没有声明这两个比值，所以
   S2 从 12/12 PASS 改为 12/12 MISSING。
5. **产品改名。** S1/S3/S5/S6 保持严格定义，在 20 张集合上 100% MISSING。既然定义严格、结果全不可判，
   产物不再自称“自洽性检查”，改名为 **Phase 0 披露度普查**；它报告披露了什么，不宣布是否自洽。
   若以后要判自洽，需先放宽定义或扩大可判集合，另立版本。
6. **扩集合。** 从 12 张 LeRobot 卡片扩到 20 张异源页面：加入 `robomimic`、`calvin`、`robocasa`、
   `maniskill` 的 GitHub README，以及 `droid`、`openx`、`bridge-data`、`libero` 的项目页。
   这仍是可及范围普查，不是随机样本，不能外推到整个行业。
7. **目录表修正。** `README.md` 的示例表只保留一行 `record-example.json`；观测件行指向
   `schema/examples/sync-observation-example.json`。

## 二、Phase 0 结果

2026-11-26 抓取 20 张公开、无需登录或审批的页面。结果：

- 20 张中 **0 张至少一项 FAIL，20 张至少一项 MISSING，两项都有的 0 张**。
- S1 可判 0/20，S2 0/20，S3 0/20，S5 0/20，S6 0/20。
- S4 可判 12/20（60%），PASS 12、FAIL 0、MISSING 8，判为“无可区分信号”。
- 状态组合 2 种，不是全部行同构。

S1 全部不可判的原因是 12 张 LeRobot 卡片与 8 张异源页面都没有同时给出 `scene_count` 与
`per_scene_episodes`；S2 全部不可判的原因是页面只给条数、帧数和 fps，没有声明两个被比值。
这不是它们的加法算错了，而是披露不足。

逐卡 URL、双哈希与逐项证据在 `checks/dataset/2026-11-26/cards.csv`；清单哈希在
`checks/dataset/2026-11-26/manifest.sha256`。

## 三、复算

```
python3 tools/run_all_checks.py
python3 tools/cosine_threshold_smoke.py --w 0.95
python3 tools/screen_cards.py --self-test
python3 tools/screen_cards.py --date 2026-11-26 --out checks/dataset/2026-11-26-r2
python3 tools/release_preflight.py --version v0.5
```

`run_all_checks.py` 覆盖 150 个自检用例、七份记录、观测件与 JSON Schema 交叉验证。
`screen_cards.py` 对新目录重新抓取；输出目录已存在时拒绝写入，不会原地改写旧结果。

## 四、冻结与更正

本版文件哈希见 `SHA256SUMS` 与 `releases/v0.5/manifest.json`；发布前预检记录在
`releases/v0.5/preflight.json`。冻结日期 2026-11-26。

已发布版本不静默修改，tag 不移、不删、不 force push。发现错误时发新版本，在发布说明写明改了什么、
为什么改、影响哪些字段；旧版本与其 tag 保留。V0.4 的 `checks/dataset/2026-11-25-r2/` 保留原样；
V0.5 使用新日期目录 `checks/dataset/2026-11-26/`。

## 五、本版不包含

- 任何真实语料的 NEES 读数。时钟模型、episode 指纹与簇级 bootstrap 尚未实现，`verified` 记录无法合法产生。
- 去重检测器与硬负例夹具；因此没有任何去重误判率读数。
- 标签一致性核验与 D1b（卡片对索引）；两者在 `scope_declaration` 中声明未做及回归条件。
- 对公开卡片行业普遍性的推断。20 张是当日可及集合，不是随机抽样。
- 认证、评级、入表背书或采购建议。
