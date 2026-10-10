# Canvas Known-Failure Repair Continuation

Date: 2026-10-11
Status: Implementation authorized; Native Codex execution.

## Goal And Scope

补齐[reusable canvas spec](../specs/2026-10-11-reusable-canvas-production-harness.md)的同入口恢复：
显式关闭已知失败后，经既有 GenerationFeedbackOrchestrator 准备一次有依据的 same-Shot 修复，
并从 canonical binding 的前序证据关系重开其 successor；不按 Manifest 顺序猜最新版本。

## Current And Target Behavior

目前单次失败返回 stop，两个同Shot attempts直接阻断；generic owner已有 exact rejection、
intervention、budget与execution guards，但Canvas无法调用或恢复。增加显式
`prepare_repair(limits, interventions)` / `start_repair(limits, interventions)`，只在当前
exact terminal quality-rejection上可用；旧start、unknown stop和所有提交gate保持。

多个attempt只在canonical execution binding逐个链接到已关闭前序、无分支、唯一末端时接续。
quality rejection receipt、request/evidence身份由原reader/committer重验；新helper仅选择关系明确的当前attempt，
不写状态、复制诊断、重置消费或生成adoption真值。显式repair仅准备/start，不能自己POST。

## Files And Ownership

- `src/ai_video/canvas_recovery.py`：read-only canonical attempt lineage选择。
- `src/ai_video/canvas_production.py`：共享application repair handoff，沿原orchestrator与generation owner。
- `tests/test_canvas_recovery.py`：实际committer/reader/Router恢复、预算、未知/歧义拒绝与replay回归。
- 原spec/plan、runtime baseline与mecha record：同步实现范围、真实human反馈、旧冻结的证明边界。

## Invariants And Acceptance

已知raw POV FAIL仍FAIL；用户声音/动作确认是human证据，不升级为旧analyzer听看或最终验收。
未关闭、unknown、branch/foreign predecessor、过期或不匹配receipt均无新attempt/POST。
修复binding继承完整失败历史、exact predecessor、原task和真实消费；重复start不重复副作用。
successor完整Gate合格后才采用与推进；失败前序不能成为accepted continuity source。
不增加Manifest schema、第二timeline、自动retry、story-specific分支或Provider。

## Major Milestones

先以真实Canvas fixture复现旧入口无法恢复；补齐最小共享seam并验证known closure→normal planner→
durable successor→reopen，拒绝fork/unknown及未关闭状态。执行changed-path Harness与Risk Gate后发布。
再为POV设计单一可归因变量，保留用户已确认的声音/动作，封存原失败和有限追加预算，经原owners实测。
任何新媒体完整重验；尚无新submit授权封套/permit，也不凭此plan执行POST。

## Verification And Self-Review

`PYTHONPATH=src:. .venv/bin/python -m pytest tests/test_canvas_recovery.py tests/test_canvas_production.py -q`
及policy要求的exact snapshot Harness；真实媒体和最终听看独立取证。
本slice补application缺口，恢复权仍归ProductionStateCommitter；不以新目录、新task或QA降标清掉旧失败。
共享实现再次变化后重新冻结证明范围，旧holdout结果仅证明旧bytes；AC-2/AC-7不能由这次修复自签。
