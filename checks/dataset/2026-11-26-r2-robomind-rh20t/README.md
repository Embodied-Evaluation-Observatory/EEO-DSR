# 卡片口径明确性检查 2026-11-26 补充（RoboMIND + RH20T）

> 本页是卡片口径明确性检查，不是对数据质量的判定，不是对任何标准的符合性判断，不是核验结论。MISSING/AMBIGUOUS 反映卡片披露格式，不代表数据本身有问题。

EEO-RN-3

## 范围

本目录只补两张：RoboMIND 与 RH20T。它不替代 2026-11-26 的 20 张披露度普查，也不把两张的集合级读数冒充 22 张的普查。

本目录为**人工转录自钉住页面字节**，不是自动解析；每张卡片原始页面在 `pages/`，`page_sha256` 可复算。

## 逐项读数

| 项 | 可判 (PASS+FAIL)/2 | 可判率 | 判定 | PASS | FAIL | MISSING | AMBIGUOUS |
|---|---:|---:|---|---:|---:|---:|---:|
| S1 | 0/2 | 0% | 不可判 | 0 | 0 | 1 | 1 |
| S2 | 0/2 | 0% | 不可判 | 0 | 0 | 2 | 0 |
| S3 | 0/2 | 0% | 不可判 | 0 | 0 | 2 | 0 |
| S4 | 2/2 | 100% | 无可区分信号 | 2 | 0 | 0 | 0 |
| S5 | 0/2 | 0% | 不可判 | 0 | 0 | 2 | 0 |
| S6 | 1/2 | 50% | 无可区分信号 | 1 | 0 | 1 | 0 |

S1 的 AMBIGUOUS 只有 RoboMIND：107,877 对 107k，截断与四舍五入两种读法算术不同，卡片未声明舍入口径。

## 逐卡

### rh20t

- URL：https://rh20t.github.io/
- 页面：`pages/rh20t.html`；`page_sha256=fdf50f33b3ad379232530e4216e4d1343e446cecb30c0ab58ffc5fb73b3e256a`；`card_sha256=cab037f94bd38c9e05a6b0c5a6405e1615b0f0237cd43db7591d011486cc4120`
- S1：**MISSING**；声明总数 over 110,000，非精确总数；分任务 48+29+70=147，但卡片无逐任务 episode 计数
- S2：**MISSING**；卡片给 10 Hz 等模态频率；无精确 total_episodes、total_frames，也无 frames/episode 或 seconds/episode
- S3：**MISSING**；无版本标签；页面修订日期 2025-08-11
- S4：**PASS**；两个许可按场景切分：scene_0001-0005 CC BY-SA 4.0；scene_0006-0010 CC BY-NC 4.0
- S5：**MISSING**；下载列表给 tar.gz，无 sha256/checksum
- S6：**PASS**；路径含 task_0001_user_0001_scene_0001_cfg_0001 与 metadata.json；scene 与 cfg 可 join

### robomind

- URL：https://huggingface.co/datasets/x-humanoid-robomind/RoboMIND/resolve/main/README.md
- 页面：`pages/robomind.md`；`page_sha256=84f510133a9b3ba372a41e45dcc9637a7a1e17c1e7c0df1e2c2e80361376c271`；`card_sha256=1d982bd44434d09e301b5d3d14d0d397a90e5f32f1ba36de3d2f43c0a3856641`
- S1：**AMBIGUOUS**；声明总数 107k；分本体 52,926+19,152+10,629+25,170=107,877；截断到千位 107k 平，四舍五入 108k 不平；未声明舍入约定
- S2：**MISSING**；卡片未给 total_frames、fps 或 frames/episode、seconds/episode；只有 <200 / >500 timesteps 的定性描述
- S3：**MISSING**；卡片有 V2.0 与 1.1/1.2 两个版本标签；无页面修订日期
- S4：**PASS**；YAML license: apache-2.0
- S5：**MISSING**；卡片无 sha256/checksum 字段
- S6：**MISSING**；卡片无 scene_id/workstation_id/station_id 字段

## 不能说明什么

不能说明卡片是否诚实、语料是否可用、覆盖是否够、切分是否干净、标注是否正确。它只报告披露与算术，不给出自洽性结论；结果不得引用为核验结论，也不得用于它没有覆盖的语料。

Phase 0 的 linter 结果独立发布，不进入 T1/T2 记录；记录里的 DSR-D1 是在该记录语境下重新执行的卡片检查，不直接引用本目录的输出。

