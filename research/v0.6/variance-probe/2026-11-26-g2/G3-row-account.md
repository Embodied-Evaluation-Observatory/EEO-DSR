# G3 行集对账

## 计数

| 项 | 值 |
|---|---:|
| 镜像总 episode | 95,658 |
| 镜像 building 非缺失 | 93,994 |
| raw metadata 对象 | 74,896 |
| raw metadata 唯一 uuid | 74,795 |
| raw metadata 重复行 | 101 |
| raw building 非缺失 | 73,511 |
| raw scene 非缺失 | 73,413 |
| raw `scene_id=-1` | 1,382 |
| building 轴 − scene 轴 | 20,581 |

镜像与 raw metadata 的总差为 20,762。按 building 的差不是随机缺失：前几项为 `bww` 5,219、`gates` 4,931、`evgrc` 1,779、`2300JaneLn` 1,524、`2479RichardCt` 1,286、`Lyman` 1,001、`780SharyAve` 753、`775Roble` 593、`EVGRD` 555。另有 4 个 building 在 raw 中为 0，共 3,722 条。

## 为什么还不能取交集

- 镜像有 `episode_index`、`building`，没有 `uuid`。
- raw metadata 有 `uuid`、`scene_id`，没有 `episode_index`。
- 两份抽取没有共同行键；不能构造逐 episode 交集，也不能把 raw scene 行当作镜像子集。

因此 G3 只完成了计数对账和差异定位，没有完成“同一批行重跑三轴”。

## 下一步

先建立 `episode_index ↔ uuid` 连接键（raw recording path 或公开 episode 表），再取交集，在同一批行上重跑 building、cell、native 三轴，隔离粒度效应。不得把 20,762 的差当成随机抽样误差。

`nees_record: not_issued`。
