# Schema 作为参考实现候选

状态：候选，未提交，未被任何标准组织采纳。当前 schema 版本仍是 `eeo-dataset-review/0.5`；V0.6 的 `chain.readout` 迁移未完成。

## 可复算入口

- `schema/record.schema.json`：记录结构；
- `schema/sync-observation.schema.json`：时钟观测件；
- `tools/validate_record.py`：执行层校验，`--self-test` 150 例；退出码 0 通过、1 不合法、2 用法；
- `tools/run_all_checks.py`：CI 入口，跑自检、示例、观测件与 JSON Schema。

## 变更节奏

1. 现行版本在 `STATUS.md` 与 release tag 中列明；
2. 修正不移动旧 tag，发新版本并在 `STATUS.md` 标“superseded”；
3. schema 变更必须同时给迁移说明与校验器用例；没有用例的结构变更不发布；
4. 对外引用必须给方法版本、语料 id 与版本、检索日期、记录自身哈希。

## 边界

- 这是候选参考实现，不是标准文本，不声称与任何标准相符。
- 代码 MIT；名称与记录格式标识不在 MIT 授权范围内。
- fork 剥掉用途限定后，官方 schema/validator 拒收；这是防伪机制，不是认证。
