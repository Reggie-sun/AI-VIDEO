# Sequence Destination Route Authority Implementation Plan

**Goal:** exact destination authority 只来自既有 canonical Router execution binding，sequence adapter
只能继承 source route 或消费该 evidence。

**Scope:** same-stack derivation、cross-stack evidence admission/reopen、focused regressions 与 canonical docs。

**Spec:** `docs/superpowers/specs/2026-10-04-sequence-route-authority.md`，Parent self-reviewed，按当前任务授权实施。

**Compatibility:** 既有 same-stack API calls/hash 保持；destination route/stack 可省略并继承。
旧 cross-stack bindings 仍可 pure read，但缺 authoritative evidence 不可新 execution。

**Invariants:** Planner 中立；Router 独占 ranking/selection；exact source、FULL frame/C2 gates、
QA/permit/budget/unknown-outcome protections 保持；零真实 Provider/credential/media effects。

## Milestone 1: Reproduce And Harden Existing Evidence Boundary

**Files:** `planning/sequence_continuity.py`、`production/generation_execution.py`、
`production/_shot_router_contracts.py`、`production/_sequence_source.py`；
`tests/test_planning_sequence_continuity.py`。

先验证无 destination 参数的 same-stack inheritance 与 naked cross-stack route RED。
execution binding owner 提供只读 selected-route evidence validator；sequence adapter 派生 source
route，cross-stack 复用现有 execution binding 并核验 exact seed/snapshots/lifecycle/stack。
binding additive 保存既有 type 的 canonical JSON，省略 None 保留历史 hash。
Production source proof seam 在 resolver/preparation/execution reopen 时重新核验 destination evidence，
因此手工重建 routing 不能旁路 builder 的限制。初始 selection 不允许 continuity-route 预选循环。
将既有 authoring-seal payload 归并到 source proof owner，所有 cross-stack reopen 关联 prior seed；
以 another valid neutral-seed selection 替换测试覆盖 feedback/public Resolver/resealed execution。

**Acceptance:** 用户 ten-test inventory 与 stale/tampered/legacy bypass 否定路径通过；有效 cross-stack
先前 Router selection 可被消费，最终 Router 仍可拒绝 destination mismatch。

## Milestone 2: Verify Exact Candidate And Publish Owned Change

**Files:** `docs/agent-primary-contract-matrix.md`、`docs/v0.2-runtime-baseline.md`、本 spec/plan、
`docs/record_for_agent/2026-10-04-sequence-route-authority.md`；直接相关旧 record 仅添加 supersession。

运行 `python -m pytest -p no:cacheprovider tests/test_planning_sequence_continuity.py
tests/test_planning_video_planner.py tests/test_production_shot_router.py tests/test_production_video_transition.py
tests/test_shot_readiness_gate.py tests/test_generation_feedback.py tests/test_generation_execution.py
tests/test_generation_execution_guards.py tests/test_production_generation_decision.py -q`。
运行 task Architecture Gate、exact staged snapshot 或 commit range changed-path Harness；核验 scope/artifact hashes/fresh receipt。
同一 stable final candidate 做双独立 native read-only T3 review，semantic fix 后重验与必要 re-review。
按 `record-ai-video-session` / `distill-ai-video-learning` 记录工程事实，不制造 media learning claim。
按精确 owned paths commit 并 push `main`，报告 receipt/publication/remaining evidence limits。

## Self Review

两个 milestone 完整覆盖 spec；source 与 destination evidence validation 不新增 selection owner。
不制造 worktree、依赖、额外 Provider 调用或 approval gate；没有 production sequence driver 的事实保留。
