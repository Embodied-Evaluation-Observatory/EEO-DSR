# 引用规则

引用本模块的记录，必须同时给出四项，缺一不可：

1. `method_version`（例如 `EEO-DSR-V0.2`）；
2. 语料 id 与版本；
3. 检索日期（公开卡片）或委托日期（委托记录）；
4. 记录自身的 sha256。

格式：

```
EEO-Dataset-Review <method_version>, corpus <corpus_id>@<corpus_version>,
<retrieval_or_commission_date>, record sha256:<hash>
```

不得引用未发出的草稿，不得把初筛结果引为核验结论，不得把 T1 引为 T2。
fork 可以自由使用代码，但无法诚实地引用官方 `method_version` 与官方记录哈希；
名称与记录格式标识不在 MIT 授权范围内，不得自称本模块。
