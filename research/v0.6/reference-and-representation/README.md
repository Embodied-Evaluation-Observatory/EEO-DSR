# 买方参照分布偏离度 + 共享特征表示

日期：2026-11-26。研究实现，未签发记录。

## 依赖顺序

`买方参照分布 → 特征表示 → 去重标定 / ICR`

特征表示是去重与 ICR 的共同上游：同一份 episode 指纹既用于余弦近重复候选，也用于簇内特征分散。两条路不能各自拟合一套表示，否则 DSR-D5a 的重复计数与 ICR 的特征基底不可比。

## 已完成

### 特征表示

`tools/feature_representation.py`

输入 `.npz`：`episode_id`、`features`（逐 episode 数值矩阵）、可选 `cluster_id`。

固定管线：

1. 中位数填补；
2. IQR 稳健缩放（IQR 为 0 时退回标准差）；
3. 去中心；
4. SVD 截断；
5. 载荷符号固定；
6. 行 L2 归一化。

输出 `.npz` 含 `fingerprints` 与 `loadings`；JSON 记录输入 SHA256、维度、解释方差、阈值及“候选不是重复计数”的边界。

去重：`--dedup-threshold W` 只列余弦 ≥ W 的候选对，W 必须由买方声明。它不产出 DSR-D5a 的重复条数。

ICR：同一 `fingerprints` 作为特征基底输入；本工具不计算 ICR 区间。

自测：160 条合成 episode、12 维，重复对平均余弦 0.99997，异质对平均余弦 -0.606，输出 8 维。

### 买方参照分布偏离度

`tools/reference_deviation.py`

输入两份 `fingerprints.npz`：`reference` 为买方参照群体，`target` 为待核验语料。输出：

- 标准化均值漂移向量、L2 范数、最大单维 |z|；
- 能量距离（V-statistic，非负；附 bootstrap 95% 区间）；
- 逐维 KS 统计的最大值；
- target 落在 reference 0.5–99.5% 分位范围外的比例；
- target 到最近 reference 点的距离中位数与 P95。

这些是描述读数，不含阈值、评级、验收结论。参照群体由买方提供，EEO 不选参照、不拥有参照。

自测：同分布时均值漂移与能量距离为 0；加 0.05 噪声后均值漂移 0.1029、能量距离 0.00429。

## 尚不能产出

- 没有买方参照群体，因此没有真实 `reference_deviation` 读数；只有工具与自测。
- 没有 DROID 逐 episode 视频/动作特征矩阵，因此没有 73,413 条真实指纹；只有接口与自测。
- ICR 仍只到“共享上游就位”，没有区间；区间要等 G2 的方法修正与 cell/native 覆盖标定。

## 复算

```bash
python3 tools/feature_representation.py --self-test
python3 tools/reference_deviation.py --self-test

python3 tools/feature_representation.py \
  --input episode_features.npz \
  --out-prefix fingerprints \
  --dims 64 \
  --dedup-threshold 0.95

python3 tools/reference_deviation.py \
  --reference buyer_reference.npz \
  --target fingerprints.npz \
  --out reference-deviation.json
```

`nees_record: not_issued`。`icr_record: not_issued`。
