# V0.6 schema 迁移草案

本文件是迁移清单，不是已生效 schema。当前 `record.schema.json` 仍是 `eeo-dataset-review/0.5`；在迁移完成、150 例校验器通过之前，不得据此签发记录。

## 1 读数字段

- 旧 `chain.nees` 保留为兼容字段。
- ITR 记录强制 `chain.nees = null`，读数进入 `chain.readout`。
- `chain.readout` 形状：

```json
{
  "type": "ITR",
  "axis": "native_scene",
  "value": 5990.513564485708,
  "rho": 0.2798279662781307,
  "rho_free_interval": [2207, 73413],
  "rho_conditional_range": [0.25375274872213655, 0.3069055492779254],
  "n_eff_interval": [5565.297625321255, 6469.139848800033],
  "bootstrap_reps": 1000,
  "n_eff_interval_relative_width": 0.15020930150202536,
  "bootstrap_seed": 20261126,
  "status": "unreviewed_draft_in_repo"
}
```

- `status` 是记录状态，不是可见性声明。`unreviewed_draft_in_repo` 只表示“已入公开仓库、未审”，不得写成“未推送”或“仅本地”。
- `readout_type` 取值：`ITR`／`NEES`／`ICR`。
- 若使用 `readout_type: ITR` 而保留旧 `chain.nees` 字段，旧字段必须为 `null`；机器忽略旧字段里的任何值。
- `interval_reading` 只能挂在 `rho_conditional_range`，不得挂在 `rho_free_interval`。二者分列，不互相替代。

## 2 新增字段

| 字段 | 位置 | 含义 |
|---|---|---|
| `rho_free_interval` | `chain.readout` / `neev` | `[K,N]` 的平凡界，不依赖 ρ |
| `rho_conditional_range` | `chain.readout` / `neev` | 簇级 bootstrap 的 ρ 分位区间 |
| `dedup_scope` | `neev.dedup` | `not_executed`／`exact_only`／`full` |
| `axis_provenance` | `neev.cluster` | 轴定义、字段来源、源版本、是否原生 |
| `row_account` | `dataset` / `neev` | 源→剔除→采用的行数账，逐轴并列，不合并 |

## 3 校验器迁移顺序

1. 加可选字段，旧例仍通过。
2. 新增 ITR 例，断言 `chain.nees=null`、`readout.type=ITR`、`rho_free_interval` 与 `rho_conditional_range` 不混用。
3. 重跑 150 例；任何旧例被破坏即停止。
4. 更新 `schema_version` 到 `eeo-dataset-review/0.6`，旧版本记录保留为历史。

## 4 当前状态

- 本迁移未实施；`record.schema.json` 与 `validate_record.py` 仍是 0.5。
- 因此本轮不签发任何 ITR/NEES/ICR 记录。
