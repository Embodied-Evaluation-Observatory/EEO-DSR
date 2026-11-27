# G3 单源三轴重跑

日期：2026-11-26。这是本地研究草案，不签发 NEES 记录。

## 为什么换单源

上一轮 G3 卡在 `episode_index ↔ uuid`：镜像有 `episode_index`/`building`，没有 `uuid`；raw metadata 有 `uuid`/`scene_id`，没有 `episode_index`。没有共同行键，跨源逐 episode 交集无法构造。

本轮不再尝试拼接两源，改用 **raw metadata 单源**，让三轴落在同一批 73,413 条 episode 上。

## 行集

| 读数 | 值 |
|---|---:|
| raw metadata 对象 | 74,896 |
| scene 非缺失且非 -1 | 73,511 |
| 与 `droid_scene.csv.gz` 对齐后 | 73,413 |
| 去重删除 | 98 |
| 结局与 `droid_scene.csv.gz` 不一致 | 0 |

`episode_id` 用 raw `uuid`；`outcome` 用 raw `success`。三轴共用这一张表，不跨源。

## 三轴

| 轴 | 键 | K | N | ρ 点 | n_eff 点 | deff | 零方差占比 | ρ 95% | n_eff 条件 95% | n_eff 条件相对宽 |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| site | `building` | 69 | 73,413 | 0.104613 | 589.745 | 124.483 | 13.24% | [0.064319, 0.147560] | [424.51, 921.13] | 73.81% |
| task_text | `building\|\|current_task` | 2,418 | 73,413 | 0.191744 | 6,053.998 | 12.126 | 39.26% | [0.165640, 0.221414] | [5,563.63, 6,614.52] | 17.26% |
| native | `scene_id\|building\|robot_serial` | 2,220 | 73,413 | 0.284524 | 5,953.539 | 12.331 | 47.83% | [0.258117, 0.313981] | [5,519.34, 6,428.41] | 15.22% |

native 轴的 K、N、ρ、n_eff 与 r3b 复合键完全一致；bootstrap 用同一 seed 20261126，区间也一致。

## 这个 task_text 轴不是镜像 cell 轴

raw 只有 `current_task`（1,220 个值），没有逐 episode 的 `language_instruction`（镜像 49,628 个值）。因此：

- 本轮 task_text 轴 K=2,418，镜像 `building||instruction` K=53,714；
- 本轮 task_text 轴是任务文本粒度，不是镜像的逐 episode 指令粒度；
- 两个读数不可直接比较，不能把 0.191744 写成“修正后的 DROID cell ρ”。

site 轴同样：raw 的 `building` 有 69 个值，镜像有 73 个；69 与 73 不可互换。

## 行宇宙

每个数都绑定到一个行宇宙；不同宇宙的数字不能直接相减或互换。

| 行宇宙 | 行数 | 定义与用途 |
|---|---:|---|
| mirror total | 95,658 | 镜像全部 episode 行，不限 building |
| mirror building 非缺失 | 93,994 | 镜像 building 轴；1,664 条 building 缺失被排除 |
| raw metadata objects | 74,896 | 抓到的 raw metadata 对象总数 |
| raw metadata 唯一 uuid | 74,795 | 去重后；重复行 101 |
| raw scene 非缺失 | 73,413 | 去掉 `scene_id=-1` 并去重；native 轴与单源行集 |
| raw scene 去重前 | 73,511 | 非缺失且非 -1，去重前；去重删除 98 |
| `scene_id=-1` | 1,382 | 只作 scene 排除，不算碰撞 id |
| 单源三轴 | 73,413 | 与 raw scene 非缺失同一批行 |

差额必须带宇宙名：

- `95,658 - 74,896 = 20,762`：mirror total 减 raw metadata objects。
- `93,994 - 73,413 = 20,581`：mirror building 非缺失减 raw scene 非缺失。
- `74,896 - 73,413 = 1,483`：raw metadata objects 减 raw scene 非缺失。

## 解决了什么，没解决什么

已解决：三轴现在有同一批 73,413 条 episode 的行集，不再依赖缺失的跨源连接键。

未解决：镜像与 raw 的 20,762 行差仍未逐 episode 对账；本轮没有构造 `episode_index ↔ uuid`，也没有把 raw scene 行当作镜像子集。

## 文件

`droid_raw_single_source.csv.gz` 是共用的六列行集；`site_corpus.csv.gz`、`task_text_corpus.csv.gz`、`native_corpus.csv.gz` 是三轴输入；`driver-*.json`、`bootstrap-*.json` 是逐轴输出；`three-axis.json` 是汇总。

## 边界

- 三轴都是成功率估计精度，`claim_scope` 为 `success_rate_precision_*_not_training_information`。
- 没有 NEES 记录，没有发布，没有提交。
- `5,953.539` 只留在本研究目录，不进对外材料。
