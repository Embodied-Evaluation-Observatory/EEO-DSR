# DROID 指纹样本（2,000 请求，1,999 成功）

日期：2026-11-26。抽样种子 20261130。输入：`droid_raw_meta.csv` 与 `droid_metadata_objects.json`；每条下载 metadata JSON 与 `trajectory.h5`，提取后丢弃 HDF5。

## 结果

- 请求 2,000，成功 1,999，失败 1。
- 失败：`IRIS+7dfa2da3+2023-04-13-15h-29m-41s`，`HTTP Error 404: Not Found`。失败保留在 `manifest.json`，没有静默补抽或改写分母。
- 表示：`summary` 203 维；`traj16` 464 维。
- 每个成功条目含 `h5_sha256`；`sample_meta.csv` 有 uuid、scene_id、building、current_task、lab、outcome、trajectory_length_meta、n、h5_sha256。
- 输入文件的 SHA256 在 `manifest.json`：`raw_meta_sha256`、`metadata_objects_sha256`。

## 输入信号

`observation/robot_state/joint_positions`(7)、`joint_velocities`(7)、`gripper_position`(1)、`action/joint_position`(7)、`action/joint_velocity`(7)。没有末端位姿、没有视频特征，本轮不宣称覆盖。

## 硬负例标定

见 `hard-negative-calibration.json`。正例是受控重编码副本（0.5% 与 2% 特征噪声），不是独立真实重复；负例是真实同任务不同 episode、同 scene 不同 task。W 是研究占位阈值，不是买方验收阈值。

摘要（W=0.90）：

| 表示 | 正例 | 负例 | FPR | FNR | 0.5% 副本 FNR | 2% 副本 FNR |
|---|---:|---:|---:|---:|---:|---:|
| summary | 300 | 246 | 2/246 = 0.0081 | 101/300 = 0.337 | 5/150 = 0.033 | 96/150 = 0.640 |
| traj16 | 300 | 246 | 0/246 = 0.000 | 60/300 = 0.200 | 0/150 = 0.000 | 60/150 = 0.400 |

W=0.95 时：summary FPR 1/246、FNR 134/300（0.5% 副本 28/150，2% 副本 106/150）；traj16 FPR 0/246、FNR 91/300（0.5% 副本 3/150，2% 副本 88/150）。

两种表示都在 0.5% 重编码下可用，2% 噪声下明显退化。这个退化是读数，不是把阈值往下调就能消掉；W 由买方声明。

精确单侧 95% 上界（Clopper–Pearson）在 JSON 的 `fpr_upper95` / `fnr_upper95` 与各副本类型字段里，不合并成“准确率”。

## 边界

- 1-of-16 时移不是正例：它移动重采样边界，余弦均值约 0（20 条测试为 0.101，1999 条为 -0.001），不能当重复。
- DROID 原始 metadata 没有声明 train/test split；D5b 跨 split 泄漏计数没有合法 split 定义，本轮不冒名计数。
- 未扩到 73,413；未做视频特征。
