# 分层预检层

状态：V0.6.5 之后新增的治理层；不是记录，不是发布闸，不是认证，不是审计意见。

## 0 三层

| 层 | 做什么 | 数据去向 | 产出 |
|---|---|---|---|
| 层 0 自检/预算 | 公开工具在客户本地跑；样本预算、卡片口径自检 | 不上传，EEO 不接触 | 本地工具日志 |
| 层 1 公开卡片 | 公开普查，只查公开信息 | 公开页面 | 披露度普查分布 |
| 层 2 样本预核验 | 委托方不具名的样本预算/预核验 | 样本不交给 EEO | 工具日志＋输入哈希，带 `pre_check_not_a_record` |

层 2 才使用 `pre_check_not_a_record`；层 1 是公开卡片普查，不是“预核验记录”；层 0 是客户本地自检。三层都不产生可引用记录哈希。

## 1 为什么要有这一层

正式记录要求委托方具名、样本瑕疵公开、中间结果公开。对监管方和国企，这等于在采购前先做一次公开披露；内部合规审批的成本高于体检本身。预检层只解决“先自己看一眼”，不改变正式记录的具名与公开规则。

## 2 层 2 本地预检：数据不出门

- 工具：`tools/screen_cards.py` 与 `tools/precheck_local.py` 都是公开代码；在委托方自己的机器上运行。
- 数据：样本、卡、标签、路径不离开本地；不上传，不发给 EEO-DSR，EEO-DSR 不接触输入文件。
- 产出：仅工具日志＋输入文件哈希。日志带机器标记 `pre_check_not_a_record`。
- 日志不含：记录 schema、可引用的记录哈希、摘要、判定、发现、抬头、分数、评级。
- 官方 schema 拒收任何带 `pre_check_not_a_record` 的文档；剥掉标记仍然过不了校验，因为日志没有记录必填字段。与 fork 防伪同一机制。

用法示例（本地）：

```bash
python3 tools/screen_cards.py --source local_cards.csv --out local-screen
python3 tools/precheck_local.py \
  --input local_cards.csv --tool screen_cards.py \
  --command "python3 tools/screen_cards.py --source local_cards.csv --out local-screen" \
  --exit-code 0 --out precheck-log.json
```

`local-screen/` 是本地自检目录，不是记录；不得当作记录上传。

## 3 层 2 公开登记册：只报聚合数

`entry/precheck-register.json` 只接受以下聚合字段：

| 字段 | 含义 |
|---|---|
| `period_start` / `period_end` | 登记周期 |
| `n_prechecks` | 本期预检次数 |
| `n_formal_entry` | 其中进入正式核验的次数 |

禁止字段：委托方名称、样本名称、语料 id、发现、判定、单次日志、单次输入哈希、任何可回指单方的标识。

登记册不是评级：它只报“本期预检 N 次，其中 M 次进入正式核验”的集合分布。买方看到两成进入正式核验，自会折扣；这不是对任何一方的评价。

当前 `entry/precheck-register.json` 的 `entries` 为空：尚无已报告的周期，不填 0、不编 N/M。`tools/validate_precheck_register.py` 会拒绝任何非聚合字段与 M>N。

## 4 与正式记录的关系

- 预检不是入口，也不是记录；不产生可引用哈希。
- 进入正式核验时，记录在 `submitter.prior_prechecks` 披露“曾有预检及日期”（此时已具名，披露成本为零），防止“跑五次发第六次”不可见。
- 正式记录仍要求委托方具名、样本瑕疵公开、中间结果公开；预检不替代任何一项。
- 同方法同数：不得有“宽松预检版”。预检与正式核验使用同一 `screen_cards.py`、同一规则；否则它就是软闸。
- 无排他、无 embargo：EEO 可独立就同一语料发布读数，不受预检阻挡；预检买不到沉默权。
- **核验不是通行证**：层 2 的日志不是记录、不是认证、不是审计意见；正式记录仍按具名与公开规则走。

## 5 数据条款

预检不改变 `entry/DATA_TERMS.md`：要文件不要链接；用后删除；不再分发。预检阶段数据不交给 EEO；正式核验阶段才按 DATA_TERMS 交付。
