# DROID ITR 单源三轴研究读数（不是记录）

日期：2026-11-27。来源：`research/v0.6/variance-probe/2026-11-26-g3-single-source/three-axis.json`。这是研究读数，不是正式记录；`nees_record: not_issued`。`nominal_95_claim: not_permitted`。

**行宇宙：73,413 条 raw 单源 episode。** 原始 74,896 条，`scene` 非缺失 73,511 条，同键去重后 73,413 条（去重 98 条）；不是镜像 93,994 条。三个轴共用同一批 73,413 行与同一批结局。

| 轴 | 键 | K | 点 ρ | 点 n_eff | 说明 |
|---|---|---:|---:|---:|---|
| site | `building` | 69 | 0.104613 | 589.745 | 单源站点轴 |
| task_text | `building\|\|current_task` | 2,418 | 0.191744 | 6,053.998 | `current_task` 1,220 个值；不是 `building\|\|language_instruction` |
| native | 复合 `scene_id` | 2,220 | 0.284524 | 5,953.539 | 原生复合 scene 键 |

## 镜像轴为什么不混进来

镜像 `building||language_instruction` 的 K=53,714、n_eff=54,853.99（93,994 行），是**文本单元轴**：`language_instruction` 有 49,628 个值，键近乎逐条唯一。它既不是 `task_text`（K=2,418），也不是任务轴；仓库自己的 `label_correction` 已写“do not call it cell”。本页不再把它叫 cell，也不把它和 73,413 行单源轴并列。

## 覆盖与区间

G2 已测区间方法在 native 与文本单元尺寸上的覆盖率：native 0.910–0.938（1,000×100），文本单元 B=2,000 网格 0.838–0.936；未达名义 0.95。**故本文件不发条件区间。** 单源 K=69/2,418/2,220 不在该覆盖网格内，未单独标定；源文件的 bootstrap 区间只作研究记录，不作“95% 置信区间”。`nominal_95_claim: not_permitted`。

## 发布前阻塞项

tie-break 敏感性子集报 K=2,432（73,413 行 raw 子集），单源 `task_text` 报 K=2,418，差 14 个簇，尚未对账。**对账前 `task_text` 轴不签发。** site/native 轴不受这个 14 簇差额影响，但仍只是点值研究读数。

## 用途

只说明成功率估计的精度；不证明记录条数，不回答训练信息量，不替代任务轴标注一致性。
