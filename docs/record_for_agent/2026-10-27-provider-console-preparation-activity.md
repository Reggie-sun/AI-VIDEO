---
record_kind: architecture_implementation
topic_id: provider-console-preparation-activity
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Provider Console Preparation Activity

## Problem And Boundary

用户报告 S05 已开始准备但顶部仍显示 S04。真实 `S05/references/` 已有图片，
尚无对应 `project.yaml` 或 video attempt；旧 UI 仅汇总 canonical attempts，不能观察准备阶段。
同时核对用户的裁切截图：截图尚为旧版固定高度预览；当前服务和重新加载后的同一 B-motion
记录已完整显示 1672×941 图片，Registry 共 12 项、10 张图片成功加载，页面无横向溢出。

新增 `provider_console_preparation.py`，复用既有 bounded runs discovery，从显式 `references/`
目录只读观察 PNG/JPEG/WebP。最多 6 组、每组 16 张、单图 16 MiB、总读取 64 MiB；
失败读取也消耗总字节预算。跳过链接、hardlink、非普通文件、超限或读取中变化的文件。
不读取 JSON/Prompt/凭据，不创建或改变 Production state，不以目录名称推断 canonical Shot。

Catalog 返回独立 `preparations` 投影，Node bridge 复用已有 exact SHA/bytes、containment、
no-follow 验证与 opaque media token；公开结果不携带本机绝对路径。图片改写后旧 token 失效。
顶部和生成记录侧栏展示“本地参考准备／未关联生成请求”，点击完整预览。
保留原始文件名，包括 `not-selected` 草稿；不把目录图片当作已经提交或已选定的 reference。
生成中的 canonical attempt 继续优先，准备材料使用明确的素材更新时间；截断或不可读状态可见。

## Verification

- Python 测试覆盖无 Project/attempt 的准备目录、内容变更后的 token、symlink/hardlink、
  非参考目录、字节/组数/张数上限，以及读取中变化和预算扣减。
- Node 测试覆盖 catalog 的 exact image GET、绝对路径隐藏、文件变化拒绝与 token 撤销；
  SSR 覆盖无 attempt 的准备卡片、与正在生成的 attempt 共存、预览和消失记录。
- Chrome MCP 在真实 `127.0.0.1:5174` 检查 S05：准备图从 2 张增加到 4 张，
  页面展示新增素材；390×844 下 4 张图均成功加载且页面宽度 390px，无横向溢出。
- 无 Provider 调用、付费生成、Production mutation 或新建准备文件。本次只是读取其他制作任务
  正在产生的材料，不签署其质量／生成／验收状态。
- 本轮 receipts：`.agent/harness/runs/20261027-console-preparation-focused/receipt.json`、
  `.agent/harness/runs/20261027-console-preparation-related/receipt.json`、
  `.agent/harness/runs/20261027-console-preparation-full/receipt.json`；各自级别与结果以 receipt 为准。
- 实现 commit `64b198876670ce61e0d7b4f5fceec1601c54a8b2` 的独立 `git archive` 快照：
  83 项 Python、113 项 Node 测试及 offline Vite build 全部通过。桌面准备图放大、Escape
  关闭及焦点返回也已实测。日志：`/tmp/console-prep-exact-verification.log`（本机临时证据）。
- Harness focused 在策略自检中失败：`full_tests.covers_check_ids` 缺少既有
  `reference_planning_tests`、`authored_visual_revision_tests`，另有 7 个既有未映射路径；
  已在修改前 `e45a40ed8fd1f270259e44275fa5b9c9ab230463` 的独立 archive 上复现相同两项失败。
  related/full 仍被根 AGENTS.md 14,185/14,000 bytes 阻断。本任务新增模块已映射；
  没有扩大范围去修复或隐藏这些基线问题，不声称 Harness 完整通过。

## Review And Publication Boundary

Parent self-review：`NATIVE_REVIEW_NOT_REQUIRED`，新增只读本机图片观察，沿用原有传输权限与
identity 校验；主要失败路径有执行测试与真实 UI 检查，不新增 Production writer。
`distill-ai-video-learning=no_candidate`：工程修复，不构成独立媒体实验学习。
共享 index 中存在其他任务的暂存修改，使用私有临时 index 构建仅本任务候选并按 commit range
验证；policy/matrix 只纳入本任务追加段落，不夹带已有未提交改动。
