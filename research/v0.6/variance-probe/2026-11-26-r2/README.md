# V0.6 方差探针与数据集侧驱动（修正版 r2）

日期：2026-11-26。上一版把零方差占比当作否决开关，误判了 DROID 单元轴。本版改用逐簇精确求和、单例分层、信息判据；旧结果保留在 `../2026-11-26/`，见其中的 `SUPERSEDED.md`。

## 1. 语料与不可定簇读数

来源：DROID 1.0.1 episode 表，经 `lerobot/droid_1.0.1` 镜像读取，抽取日 2026-11-21。

| 读数 | 值 |
|---|---:|
| 源 episode | 95,658 |
| 无 `building`、无法定簇 | 1,664 |
| 进入探针 | 93,994 |
| 不可定簇占源 | 1.7395% |

不可定簇是独立读数，不从 95,658 静默缩成 93,994。派生三列只有 `episode_id,scene_id,outcome`；两份表分别用 `building` 和 `building||instruction` 作 `scene_id`。

源文件哈希：

```text
droid_ep_clean.csv   c90865acea1620d35795cd5c5ebf334231050773363d7d9c88911a8b9ce639d2
droid_episodes.jsonl d511a7c2924d70e6275f0ee34c033bdc20e44e228bd3bdcb64f535ccd63fadb8
```

派生表哈希：

```text
droid_site.csv.gz  4db8080475b56f424cf24f2c02e5049e8f3ba728fb33ddf2309d60c3ca2140ff
droid_cell.csv.gz  6ca4bf3b814c27910d00bec813b2063b356338c041295b8d3f48e84661ab2ae3
```

## 2. 逐簇求和替代 m̄

对每个簇，精确贡献是：

\[
n_{\mathrm{eff},k}=\frac{n_k}{1+(n_k-1)\rho}
\]

单例簇 \(n_k=1\) 的贡献恒为 1，与 ρ 无关。总有效样本：

\[
n_{\mathrm{eff}}=\sum_k \frac{n_k}{1+(n_k-1)\rho}
\]

ρ ∈ [0,1] 时：

\[
K \le n_{\mathrm{eff}} \le N
\]

下界 K（ρ=1）和上界 N（ρ=0）都是严格端点，不依赖 ρ。DROID 单元轴：

- K = 53,714
- N = 93,994
- n_eff 区间 = [53,714, 93,994]
- 下界占去重条数 = 57.14%
- 区间宽度 = 40,280，相对宽度 = 42.85%

单例 47,112 个，恰好贡献 47,112；多例 6,602 簇、46,882 条，在 ρ=1 时贡献 6,602，在 ρ=0 时贡献 46,882。

m̄ 近似（`N/(1+(mbar−1)ρ)`）只保留为封顶和对照。偏斜簇下它高估：

| 轴 / ρ | 逐簇和 | m̄ 法 | m̄ 高估 |
|---|---:|---:|---:|
| 单元轴，ρ=0.5 | 56,838.27 | 68,361.82 | 20.27% |
| 单元轴，点 ICC 0.766531 | 54,853.99 | 59,685.55 | 8.81% |
| 站点轴，点 ICC 0.081593 | 791.65 | 886.93 | 12.04% |

上一版转述的“ρ=0.5 逐簇约 58,686、高估 16.5%”与本语料复算不符；本表按 53,714 簇逐簇求和给出 56,838.27，高估 20.27%。

## 3. 零方差是读数，不是否决

DROID 单元轴：

| 读数 | 值 |
|---|---:|
| 多例簇 | 6,602 |
| 有变化簇 | 93 |
| 常数簇 | 6,509 |
| 零方差占比（多例分母） | 98.59% |
| 零方差占比（全簇分母） | 99.83% |
| 有变化簇覆盖 episode | 19,067 |

93 个有变化簇比 Archive 估站点 ρ 的 74 个还多。常数簇对 MSW 贡献 0，却进入 MSB；把它们计入，ICC(1) 点估计为 **0.766531**，不是不可估。这个值仍只是点估计，没有 bootstrap 区间。

站点轴：73 簇，单例 1，多例 72，有变化簇 65，常数簇 7，零方差占比 9.72%。ICC 点估计 **0.081593**。

`K` 口径：站点轴的 n_eff 用总簇数 73；ICC 只用 72 个多例簇；单例在 n_eff 中精确贡献 1。三个数并列，不把 72 与 73 混成一个 K。上一版 887 是 m̄ 法；逐簇精确值是 791.65。

## 4. 两轴并列，不塌成一个数

| 轴 | K | n_eff 区间 | 点 ICC | 点 n_eff | 点 deff | claim scope |
|---|---:|---|---:|---:|---:|---|
| 站点 `building` | 73 | [73, 93,994] | 0.081593 | 791.65 | 118.732 | 成功率估计的有效样本量；站点层 |
| 单元 `building\|\|instruction` | 53,714 | [53,714, 93,994] | 0.766531 | 54,853.99 | 1.7135 | 成功率估计的有效样本量；任务单元层 |

两个轴回答不同问题，不取“较大 deff”合并。它们都不回答训练信息量。报告里 `claim_scope` 固定写 `success_rate_precision_not_training_information`，不把成功率精度写成“训练数据值”。

## 5. 数据集侧驱动

`tools/dataset_driver.py`：

- `aggregate`：episode→簇，拒绝重复 episode、空键、非 0/1 结局。
- `summarize_clusters`：单例、多例、有变化簇、常数簇、n_eff 区间。
- `icc1`：所有多例簇进入，常数簇不排除；无簇内变化时返回不可估，不硬给 0。
- `neff_at_rho` / `neff_interval`：逐簇精确和；单例恒为 1。
- `n_eff_diagnostics`：逐簇和与 m̄ 法并列，打印高估比例。
- `zero_failure_bounds`：按簇 / 按条两端。
- `cluster_budget`：29 / 59 / 299。
- `rho_low_cap`：只用 m̄ 法，注明方向；无区间则不输出。
- `nees_record`：固定 `not_issued`，等簇级 bootstrap 区间。

已知答案夹具 `tests/fixtures/dataset-driver-known-answers.json` 新增两例：

- 极端偏斜：1 个 100 条簇 + 50 个单例；K=51、N=150、区间 [51,150]；ρ=0.5 逐簇和 51.9802，m̄ 法 76.1194，高估 46.44%。
- 全单例：K=N=7；ρ 不可估，但 n_eff 恒为 7。

## 6. 未做与验收边界

- 没有 bootstrap，所以没有 ρ 区间；`rho_low_cap` 和 NEES 记录都不输出。
- 没有 RH20T 分级结局；二值化是否制造零方差，尚未证伪。
- 没有时钟、去重、硬负例。
- DROID 单元轴的 [53,714, 93,994] 是严格 ρ-free 区间，不是 NEES 点值，也不是“不可算”。

## 7. 复现

```bash
python3 tools/variance_probe.py \
  --input research/v0.6/variance-probe/2026-11-26-r2/droid_cell.csv.gz \
  --out /tmp/droid-cell-r3 \
  --label droid-cell --source-rows 95658 --cannot-cluster 1664

python3 tools/dataset_driver.py \
  --input research/v0.6/variance-probe/2026-11-26-r2/droid_cell.csv.gz \
  --out /tmp/droid-cell-driver.json \
  --source-rows 95658 --cannot-cluster 1664 \
  --claim-scope success_rate_precision_at_task_unit_cluster_not_training_information
```

## 8. 文件

| 文件 | 内容 |
|---|---|
| `droid_site.csv.gz` / `droid_cell.csv.gz` | 三列派生语料 |
| `site/probe.json` / `cell/probe.json` | 探针汇总、不可定簇读数、n_eff 区间 |
| `site/clusters.csv` / `cell/clusters.csv` | 每簇 n、successes、failures、rate、zero_variance |
| `site/driver-report.json` / `cell/driver-report.json` | 驱动报告，含逐簇 n_eff 与 m̄ 对照 |
| `two-axis.json` | 两轴并列，各带 `claim_scope`，不含合并数 |
| `../2026-11-26/SUPERSEDED.md` | 上一版错误判据的留档说明 |
