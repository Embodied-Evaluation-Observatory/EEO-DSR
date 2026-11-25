# Phase 0 披露度普查

页面顶部固定印 EEO-RN-3。本产物不再自称卡片自洽性检查：它测的是卡片披露了什么，以及已披露的数能否复算；它不出具合格结论，也不得被读成"对标准的初步符合性检查"。

**本集合 0 项 FAIL 不代表卡片自洽；S1 在 20 张卡上全部不可判。**

这个改名是二选一的结果：S1/S3/S5/S6 保持严格定义，在 2026-11-26 的 20 张集合上 100% MISSING；因此不能继续叫"自洽性检查"。若以后要判自洽，必须先放宽定义或先在集合里找到足够可判卡片，另立版本；不能把 MISSING 当通过。

## 输入与输出

输入固定为 `checks/cards-source.csv`，只含 `dataset_id` 与 `url`。一个目录一次检索：

```
checks/cards-source.csv
tools/screen_cards.py
checks/dataset/<YYYY-MM-DD>/
  cards.csv        一行一张卡片，一列一项检查
  README.md        查了什么、什么进了集合、怎么哈希的
  index.html       一行一张卡片，一格一项检查
  pages/           逐卡原始页面字节，供复算 page_sha256
  manifest.json    输入与输出文件的清单
  manifest.sha256  manifest.json 的哈希
```

同一天第二次运行不覆盖，改用 `checks/dataset/<YYYY-MM-DD>-r2/`；再往后 `-r3`。旧目录不原地修改。

## 什么进集合

检索当日公开可访问、无需审批、页面描述一个具身数据集或具身数据项目。V0.5 不再要求页面预先声明两项可检查字段，因为本次要测的正是披露本身；范围是 10–20 张。

2026-11-26 集合共 20 张：12 张 Hugging Face LeRobot 卡片，加上 `robomimic`、`calvin`、`robocasa`、`maniskill` 的 GitHub README，以及 `droid`、`openx`、`bridge-data`、`libero` 的项目页。它仍是可及范围的普查，不是随机样本。

需要审批的页面不进集合：一次审批请求就破坏"任何读者可复算"的前提。

## 集合级可判率

每项可判率 = `(PASS + FAIL) / m`。它是集合上的分布，不是对单张卡片的评级，不出现总分、评分或排名。

- 某项 100% MISSING：判为**不可判**，不得计入通过。
- 可判但没有 FAIL（全 PASS）或没有 PASS（全 FAIL）：判为**无可区分信号**。
- 同时有 PASS 与 FAIL：判为**有区分**。
- 全部行状态相同：声明"本集合上无区分信号"。

2026-11-26 结果：

| 项 | 可判 | 可判率 | 判定 |
|---|---:|---:|---|
| S1 | 0/20 | 0% | 不可判 |
| S2 | 0/20 | 0% | 不可判 |
| S3 | 0/20 | 0% | 不可判 |
| S4 | 12/20 | 60% | 无可区分信号 |
| S5 | 0/20 | 0% | 不可判 |
| S6 | 0/20 | 0% | 不可判 |

汇总同时给两个分布：

> 本集合 20 张卡片中 0 张至少一项 FAIL，20 张至少一项 MISSING；两项都有的 0 张。

两个分布不可合并成"至少一项不通过"：MISSING 是字段没公布，FAIL 是已公布的数算不平；放弃条件问的是后者。

## 检查项

| 项 | 测什么 | 不通过意味着 |
|---|---|---|
| S1 | 分场景计数之和与声明总数 | 卡片自己的算术不平；无分场景计数则不可判 |
| S2 | 两个被比值 `frames/episode`、`seconds/episode` 与卡片声明的换算率一致 | 声明的规模无法与另一张卡片比较；只给字段不算声明换算率 |
| S3 | 版本与日期互不矛盾 | 卡片版本与自身元数据不一致 |
| S4 | 许可存在且可机器识别 | 买方无法确认被授予的用途 |
| S5 | 校验和存在（只查存在，不复算全量字节） | 没有任何字节级承诺 |
| S6 | 场景/工位标识可跨表 join | 标识无法在两张表之间连接 |

`MISSING` 与 `FAIL` 同等记录：它表示这项检查需要的字段不在页面上。每个 `FAIL` 格同时显示声明值与重算值；行按 `dataset_id` 字母序，不按失败数排。

S2 不再因为 `total_episodes`、`total_frames`、`fps` 同时存在就 PASS。脚本先算两个被比值并印在证据里，只有卡片另声明 `frames_per_episode` 或 `seconds_per_episode` 且与重算在 1% 内一致时才 PASS；声明了但对不上记 FAIL；没有声明记 MISSING。

## 每张卡片的字段

`dataset_id`、`version`、`source_url`、`retrieval_date`（UTC）、`card_last_modified`（日期或 `not available`）、`page_file`、`page_sha256`、`card_sha256`，随后 S1–S6 各自一个 `PASS` / `FAIL` / `MISSING` 加声明值与复算值。

## 哈希

`card_sha256` 哈希的是解析后的卡片，不是页面：结构化字段（`dataset_id`、`version`、`total_episodes`、`scene_count`、`per_scene_episodes`、`total_frames`、`total_tasks`、`total_videos`、`fps`、`license`）按固定字段顺序、无空格 JSON、UTF-8 序列化，附检索日期，一次哈希。序列化结果同时保存在 `manifest.json` 的逐卡记录里，读者可按字段复算。

`page_sha256` 哈希原始页面字节；原始字节存在 `pages/`，可直接用 `sha256sum` 复算。

`manifest_sha256` 是 `manifest.json` 文件本身的 SHA-256。清单含 `dataset_id`、`version`、`url`、`retrieval_date`、逐卡 `page_sha256` / `card_sha256`，以及 `cards.csv`、`index.html`、`README.md` 三个输出文件的哈希。用 `sha256sum -c manifest.sha256` 复算。

第一版由 `tools/screen_cards.py` 自动解析页面上的结构化字段，**没有人工转录**；README 逐目录标明这一点。若以后改为人工转录，必须写成"转录自钉住页面"，并仍钉住 `page_sha256`。

上游页面变了就是新版本、新目录。任何结果都不在原地修改。

## 页面

一行一张卡片，一格一项检查。按 `dataset_id` 字母序或按日期排序，绝不按不通过项数排序。每个不通过的格子同时给声明值与复算值。格子里不放形容词。不出现总分、评分、排名。

页首固定一行：

> 本集合 0 项 FAIL 不代表卡片自洽；S1 在 20 张卡上全部不可判。

## 本产物不能说明什么

不能说明卡片是否诚实、语料是否可用、覆盖是否够、切分是否干净、标注是否正确。它只报告披露与算术，不给出自洽性结论；披露度普查结果不得引用为核验结论，也不得用于它没有覆盖的语料。

Phase 0 于 2026-11-26 跑出 V0.5 集合：20 张公开页面，0 张至少一项 FAIL，20 张至少一项 MISSING；S4 可判 12/20 且全 PASS，其余五项 0/20。输入在 `checks/cards-source.csv`，脚本是 `tools/screen_cards.py`，结果在 `checks/dataset/2026-11-26/`。

本版可交付的仍是方法、schema、校验器、阈值声明表与这份披露度普查。时钟模型与去重管线实现完成前，不会有 T1/T2 的 NEES 读数。披露度普查、T1、T2 三者不可互换。

Phase 0 的 linter 结果独立发布，不进入 T1/T2 记录；记录里的 DSR-D1 是在记录语境下重新执行的卡片自洽性检查，不直接引用本目录的输出。
