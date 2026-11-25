# Phase 0 初筛

初筛页面顶部固定印 EEO-RN-3；初筛结果不构成对任何标准的符合性判断，也不得被读成"对标准的初步符合性检查"。

初筛是免费或低价的一步：只读卡片，不碰语料。它不产出 NEES，也不产出任何核验结论。
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

同一天第二次运行不加覆盖，改用 `checks/dataset/<YYYY-MM-DD>-r2/`；再往后 `-r3`，依此类推。
旧目录不原地修改。

## 什么进集合

检索当日公开可访问、无需审批、且卡片至少声明两项可检查字段（episode 总数、场景数、许可类型）的语料。
起步名单为 V0.3 已抓过的 12 张公开 LeRobot 卡片，按本模块的“卡片声明了哪些可算字段”重筛，
不是照搬 Archive 的“有没有逐次标签”清单。

需要审批的卡片不进集合：一次审批请求就破坏了"任何读者可复算"的前提。

这是检索当日可及范围的一次普查，不是随机样本。汇总给出两个集合分布：
"本集合 m 张卡片中 n 张至少一项 FAIL，k 张至少一项 MISSING；两项都有的 j 张"，
不推广到整个领域。两个分布不可合并成"至少一项不通过"：MISSING 是字段没公布，FAIL 是已公布的数算不平，
放弃条件问的是后者。未进入集合的卡片不代表它有缺陷，只代表当日按此规则查不了。

## 检查项

| 项 | 测什么 | 不通过意味着 |
|---|---|---|
| S1 | 分场景计数之和与声明总数 | 卡片自己的算术不平 |
| S2 | 单位一致、换算率已声明 | 声明的规模无法与另一张卡片比较 |
| S3 | 版本与日期互不矛盾 | 卡片版本与自身元数据不一致 |
| S4 | 许可存在且可机器识别 | 买方无法确认被授予的用途 |
| S5 | 校验和存在（只查存在，不复算全量字节） | 没有任何字节级承诺 |
| S6 | 场景/工位标识可跨表 join | 标识无法在两张表之间连接 |

`MISSING` 与 `FAIL` 同等记录：它表示这项检查需要的字段不在卡片上，这正是买方后来会自己发现的事。
每个 `FAIL` 格同时显示卡片声明值与初筛重算值；行按字母或日期排，不按失败数排。
初筛页不给分数、评级、排行榜或形容词。

初筛只覆盖 DSR-D1 与 DSR-D4 的算术部分。DSR-D2 需要原始录制里的时间戳（由内部时钟模型计算），DSR-D3 需要任务标签，DSR-D5a 需要 episode 指纹，DSR-D5b 需要切分声明，都不在初筛范围内。

## 每张卡片的字段

`dataset_id`、`version`、`source_url`、`retrieval_date`（UTC）、`card_last_modified`（日期或 `not available`）、
`card_sha256`、`page_sha256`，随后 S1–S6 各自一个 `PASS` / `FAIL` / `MISSING` 加声明值与复算值。

## 哈希

`card_sha256` 哈希的是解析后的卡片，不是页面：结构化字段（`dataset_id`、`version`、`total_episodes`、
`scene_count`、`per_scene_episodes`、`total_frames`、`total_tasks`、`total_videos`、`fps`、`license`）
按 `dataset_id` 排序后，以固定字段顺序、无空格 JSON、UTF-8 序列化，附检索日期，一次哈希。
序列化结果同时保存在 `manifest.json` 的逐卡记录里，读者可按字段复算。

`page_sha256` 哈希原始页面字节，属辅助项：页面上的导航、推荐与评论会变，卡片不变。

`manifest_sha256` 是 `manifest.json` 文件本身的 SHA-256。清单含 `dataset_id`、`version`、`url`、
`retrieval_date`、逐卡 `page_sha256` / `card_sha256`，以及 `cards.csv`、`index.html`、`README.md`
三个输出文件的哈希。用 `sha256sum -c manifest.sha256` 复算。

第一版由 `tools/screen_cards.py` 自动解析页面上的结构化字段，**没有人工转录**；README 逐目录标明这一点。
若以后改为人工转录，必须写成"转录自钉住页面"，并仍钉住 `page_sha256`。

上游卡片变了就是新版本、新目录。任何结果都不在原地修改。

## 页面

一行一张卡片，一格一项检查。按 `dataset_id` 字母序或按日期排序，绝不按不通过项数排序。
每个不通过的格子同时给声明值与复算值。格子里不放形容词。不出现总分、评分、排名。
唯一允许的汇总是本集合上的两个分布："m 张中 n 张至少一项 FAIL，k 张至少一项 MISSING；两项都有的 j 张"。

页首固定一行：

> 初筛只报告卡片上的算术与缺项，不出具合格结论，不做数据集排名，不做资产估值。

## 初筛不能说明什么

不能说明卡片是否诚实、语料是否可用、覆盖是否够、切分是否干净、标注是否正确。
它能说明算术，并且它只说算术。初筛结果不得引用为核验结论，也不得用于它没有覆盖的语料。


Phase 0 已于 2026-11-25 跑出第一份结果：12 张公开卡片中 0 张至少一项 FAIL，12 张至少一项 MISSING；
输入在 `checks/cards-source.csv`，脚本是 `tools/screen_cards.py`，结果在 `checks/dataset/2026-11-25-r2/`。
本版可交付的仍是方法、schema、校验器、阈值声明表与这份初筛。时钟模型与去重管线实现完成前，不会有 T1/T2 的 NEES 读数。初筛结果可用于供应商自查与初筛，
但不得引用为核验结论；初筛、T1、T2 三者不可互换。

Phase 0 的 linter 结果独立发布，不进入 T1/T2 记录；记录里的 DSR-D1 是在记录语境下重新执行的卡片自洽性检查，不直接引用本目录的输出。
