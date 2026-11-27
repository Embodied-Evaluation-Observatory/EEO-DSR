# 公开仓库状态审计（research/v0.6）

日期：2026-11-27。检查对象：公开仓库 `Embodied-Evaluation-Observatory/EEO-DSR` 的 `main`。

## 事实

- 远端 `main` 为 `2ac1caf2f85fb22ad2d61524787a4f4ec8364509`。
- `HEAD` 下 `research/v0.6` 有 **136** 个 tracked 文件；这些文件都在公开仓库历史里，不存在“未推送”的已 tracked 文件。
- 最早把 `research/v0.6` 写入公开历史的是 `0426c4e`（2026-11-26）。`git log -S` 显示 `unreviewed_local_only_no_push` 只在 `0426c4e` 的 `schema/MIGRATION-V0.6.md` 示例里引入过；没有任何 `three-axis.json` 的任一历史版本含这个字符串。
- 两个 `three-axis.json` 的当前 `status` 都是 `unreviewed_draft_in_repo`，从 `0426c4e` / `1621640` 起就是公开 draft；它们本身没有 `unreviewed_local_only_no_push`。
- `schema/MIGRATION-V0.6.md` 的示例已改为 `unreviewed_draft_in_repo`，并加了“status 是记录状态，不是可见性声明”。当前 worktree 里除本审计的说明外，已不再有 `unreviewed_local_only_no_push` 字面量；git 历史仍保留旧字符串（未改写历史）。
- 2026-11-27 新产物尚未 commit/push；`publication-status.json` 列出全部 `untracked_but_unpushed` 与 `modified_tracked_but_unpushed` 路径（含本轮新增的预检、诊断、tie-break、连续量比较文件）。它们只在本地 worktree，不得称为“已公开”。

## 结论

外部反映的“不对外发布的数字实际在公开仓库”指向的是声明，不是文件本身：`schema/MIGRATION-V0.6.md` 的示例把“未审 draft”写成了“local_only_no_push”。本仓库没有改写历史，只改了当前声明。`three-axis.json` 的数字一直是公开的，任何把它称为“仅本地”的表述都应删除。

明细：`publication-status.json`（含 136 个 tracked 路径）。
