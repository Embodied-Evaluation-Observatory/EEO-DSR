# 注入偏移标定件

日期：2026-11-27。`calibration.json` 是已知答案夹具：200 条 8 维单位向量为参照，前 120 条加 `N(0, 0.05)` 后再单位化。`reference_deviation.py --self-test` 的固定数值：

| 比较 | mean shift L2 | energy distance |
|---|---:|---:|
| identical | 0.0 | 0.0 |
| shifted | 0.1028678214 | 0.0042879333 |

用途：证明比较器对已知注入偏移有响应，且 identical 侧为 0。**这是合成标定，不是真实买方读数**；文件内已标 `eeo_synthetic: true`。

它只证明“方法有响应”，不证明“方法在真实语料上能分辨”。真实读数见 `../2026-11-27-buildings/`。
