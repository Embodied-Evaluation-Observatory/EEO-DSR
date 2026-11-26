# G2 拆分：覆盖率网格研究注记 + 语料区间标注

日期：2026-11-26。两项分开，不共用“G2 已关闭”的说法。

## 第一件：四方法 × B 的覆盖率网格

形态：研究注记，不是语料记录，不签发 NEES 记录。

口径：cell 轴，K=53,714，N=93,994，multi=6,602，p_mean=0.8222971679；每个真 ρ 1,000 次模拟，B=25/100/500/2,000；区间 percentile 2.5/97.5；重抽在 6,602 个多例 cell 上固定次数 Multinomial。

必须同时印：尺寸表（K/N/multi/p_mean）、条件覆盖率（分母是可估点）、模拟器口径（固定多例子群，不是含单例全 K）。这张表只支持“在 cell 尺寸分布上、固定多例子群重抽时，percentile 覆盖率随 B 变化”，不外推到全 K bootstrap。

覆盖率表见 `cell-coverage-vs-b.csv`。B=2,000 的汇总：0.838–0.936，ρ=0.90 为 0.838。B 从 25 加到 2,000 把低 ρ 区抬到约 0.92–0.94，但 ρ=0.90 仍最低，偏斜没有随 B 消失。B 不是全部原因。

## 第二件：语料 ρ / n_eff 区间照常发

形态：语料读数，可以发；但不得写“95% 置信区间”。

字段：

```yaml
interval_calibration: measured_below_nominal
nominal_95_claim: not_permitted
```

旁边印：`interval_percentile`、`nominal: 0.95`、`measured_coverage: 0.838–0.936`、`bootstrap_reps: 2000`、`size_table: cell`、`calibrator_sha256`。cell 的实测覆盖与 native 的 0.910–0.938 不是同一个尺寸表，不得互相替代。

n_eff 区间同标：n_eff 区间是真 n_eff 的区间，不把 ρ 区间的名义水平直接搬过来；n_eff 真值按 `sum_k n_k / (1 + (n_k - 1) * rho_true)`，含单例。

## 全 K 对照（已完成）

300 次 × 2 模式，B=2,000，ρ=0.900：

| 模式 | ρ 覆盖 percentile | ρ 覆盖 BCa | n_eff 覆盖 | m_occ sd |
|---|---:|---:|---:|---:|
| fixed | 0.827 | 0.837 | — | 0.0 |
| full | 0.850 | 0.833 | 0.847 | 75.75 |

全 K 重抽把 m_occ 变异放回来了，但 coverage 只从 0.827 抬到 0.850；固定尺寸捷径是混淆之一，不是全部缺口。n_eff 区间没有更好（0.847）。BCa 的 |a|>0.1 占 37.3%、max 0.166，未见极端 |a|>0.3，BCa 更差不能只归因于极端加速度。详见 `../2026-11-26-cell-full-k/README.md`。

## 边界

- 覆盖率网格只有 cell 轴；native composite 已单独有 0.910–0.938，两者的尺寸表不同。
- full-K 只跑 ρ=0.900 一格。
