# V0.6 方差探针与数据集侧驱动

日期：2026-11-26。本目录只回答两个问题：真实语料上的零方差簇占比是否使 ρ 不可辨识；episode→簇的算术能否从语料算出数。

## 1. 语料与口径

来源：DROID 1.0.1 的 episode 表，经 `lerobot/droid_1.0.1` 镜像读取，抽取日 2026-11-21。原始抽取 95,658 条 episode，字段含 `episode_index`、`building`、`language_instruction`、`is_episode_successful`。

派生三列：

- `episode_id`：`episode_index`
- `scene_id`：站点层为 `building`；单元层为 `building||language_instruction`
- `outcome`：`is_episode_successful`，0/1

原始 `building` 缺失 1,664 条。缺失场景无法定簇，先从两份派生表中剔除，并在 README 明示；剩余 93,994 条。派生表只有三列，探针会拒绝其他列名。

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

## 2. 结果

| 簇轴 | 簇数 K | 可估簇 K(n≥2) | 单例簇 | 零方差簇（可估） | 零方差占比（可估） | 判定 |
|---|---:|---:|---:|---:|---:|---|
| 站点 `building` | 73 | 72 | 1 | 7 | 9.72% | 未触发否决；ρ 可估但不给值 |
| 单元 `building\|\|instruction` | 53,714 | 6,602 | 47,112 | 6,509 | 98.59% | **ρ 不可辨识；该语料上 NEES 不可算** |

单元层若把单例也算进分母，零方差占比是 99.83%。探针主口径只算 `n≥2` 的簇，因为单例没有簇内方差；两个数都写入 `probe.json`，不混用。

站点层通过只说明“零方差否决没有触发”，不等于给出 ρ。点估计 ICC(1) 为 0.081593，按 `mbar=1287.589` 得 `deff=105.977`、`n_eff=886.927`。这不是记录 NEES：没有簇级 bootstrap 区间，也没有 `rho_low`，因此 `rho_low_cap` 和 `nees` 都明确输出不可算，不补点值。

单元层 98.59% ≥ 90%，结论按 §8.6：`unestimable_zero_variance`。不输出 NEES、不输出封顶值，只保留三个独立读数：零方差占比、去重后条数、零失败上界；本语料有 16,703 个失败，零失败上界不适用。

## 3. 公式

簇成功率：

\[
\hat p_k = \frac{\sum_{i \in k} y_i}{n_k}
\]

零方差簇：\(\hat p_k \in \{0,1\}\)。占比分母为 \(K_{n\ge2}\)。

ICC(1)：

\[
\mathrm{MSB}=\frac{\sum_k n_k(\hat p_k-\bar p)^2}{K-1},\quad
\mathrm{MSW}=\frac{\sum_k n_k\hat p_k(1-\hat p_k)}{N-K}
\]

\[
m_0=\frac{N-\sum_k n_k^2/N}{K-1},\quad
\rho=\frac{\mathrm{MSB}-\mathrm{MSW}}{\mathrm{MSB}+(m_0-1)\mathrm{MSW}}
\]

设计效应与有效样本：

\[
\mathrm{deff}=1+(\bar m-1)\rho,\qquad n_{\mathrm{eff}}=\frac{N_c}{\mathrm{deff}}
\]

ρ<0 截断到 0。零失败精确上界：

\[
p_{95}=1-0.05^{1/n_{\mathrm{ind}}}
\]

簇预算：

\[
K_{\mathrm{need}}=\left\lceil \frac{\ln 0.05}{\ln(1-\text{target})}\right\rceil
\]

ρ 下端封顶：

\[
\mathrm{bound}=\frac{N_c}{1+(\bar m-1)\rho_{\mathrm{low}}}
\]

## 4. 数据集侧驱动

`tools/dataset_driver.py` 是纯函数库，带 CLI。它从三列语料聚合，不读校验器里的既有数字。

覆盖：

- `aggregate`：episode→簇，拒绝重复 episode、空键、非 0/1 结局。
- `summarize_clusters`：K、N、单例、零方差占比（全簇与可估簇两口径）。
- `icc1`：二值结局 one-way ICC(1)，只用 n≥2 的簇。
- `design_effect` / `effective_n`：deff、n_eff，负 ρ 截断。
- `upper95_zero_failure` / `zero_failure_bounds`：按簇与按条两端。
- `cluster_budget`：10%/5%/1% 对应 29/59/299。
- `rho_low_cap`：无区间时返回不可算，不造数。
- `report`：把上述结果组织成 JSON，明确标出 `nees: not_output`。

已知答案夹具：`tests/fixtures/dataset-driver-known-answers.json`。等簇 3×10、成功率 0/.5/1，期望 ICC=13/18、deff=7.5、n_eff=4；另有不等簇、零失败两端、预算、封顶。测试：

```bash
python3 tools/dataset_driver.py --self-test
```

## 5. 复现

```bash
python3 tools/variance_probe.py \
  --input research/v0.6/variance-probe/2026-11-26/droid_cell.csv.gz \
  --out research/v0.6/variance-probe/2026-11-26/cell-rerun \
  --label droid-cell

python3 tools/dataset_driver.py \
  --input research/v0.6/variance-probe/2026-11-26/droid_site.csv.gz \
  --out /tmp/driver-site.json \
  --label droid-site
```

`variance_probe.py` 拒绝覆盖已有目录；同日重跑请用新目录名。

## 6. 文件

| 文件 | 内容 |
|---|---|
| `droid_site.csv.gz` / `droid_cell.csv.gz` | 三列派生语料 |
| `site/probe.json` / `cell/probe.json` | 探针汇总与哈希 |
| `site/clusters.csv` / `cell/clusters.csv` | 每簇 n、successes、failures、rate、zero_variance |
| `site/driver-report.json` / `cell/driver-report.json` | 驱动报告；后者走不可算路径 |

## 7. 限制

- 这是 DROID 一个语料的两条簇轴，不是跨语料分布。单元层结论不能外推到所有公开语料。
- 站点层通过不证明任务层可估；`building` 把不同任务混在同一簇。
- 没有 bootstrap，没有去重，没有时钟。探针只做否决，不估计 ρ 区间。
- 成功标签取自 episode 表；未对标签本身做一致性核验。
