---
record_kind: architecture_implementation
topic_id: ecommerce-commercial-performance-review
learning_eligibility: ineligible
---

# Ecommerce Commercial Performance Review Record

Date: 2026-10-28

## Purpose

Full baseline `.agent/harness/runs/claude-takeover-full-baseline-20261027/receipt.json` 中
`test_production_ecommerce_job_e2e.py` 7 例失败，均被 `performance_authoring` Gate 以
`generation_intent.performance_intent.character_directions.talent-presenter.acceptance` 拦截。
调查确认这不是 fixture 遗漏，而是两个已提交功能间的产品契约缺口；用户选择"电商 profile 加表演条目"，不放宽 Gate。

## Root Cause

- `performance_authoring`（`b886f0b`，2026-10-19）：有人物的新生成前，selected QA 须有 required
  `acceptance/raw_generation`、analyzer|human 条目覆盖 `generation_intent.performance_intent`。
- 商业失败评审（`ecommerce_generation_bridge.py`，2026-09-24）只为 binding 的 `applicable_requirement_ids`
  （须为电商 profile 的 `shot.*`）产出 observation；Qingyan profile 12 条 `shot.*` 无表演项。
- 结果：商业 QA policy 下有人物 Shot 新生成即被 Gate 拦；若以 `shot.*` 外表演条目过 Gate，失败后修复无法映射而停止。
  通过路径测试为绿，仅因共享 factory 自动补了非商业表演条目。

## Current Runtime Truth

- `ecommerce_media_acceptance.py`：`SHOT_PERFORMANCE_REQUIREMENT_ID = "shot.performance.character_direction"`
  列入 `QINGYAN_SHOT_REQUIREMENT_IDS`（`shot.cast.allowed_count` 之后），profile `profile_version` 1→2，content hash 随之改变。
- `commercial_execution.require_commercial_performance_review(requirement, commercial_binding)` 于
  `GenerationDecisionExecutionBinding.create` 紧随 `require_performance_authoring` 调用：有商业 binding 且
  `requirement.characters` 非空而缺该 ID 时以 `AiVideoError(VIDEO_REQUEST_INVALID)` 拒绝。仅新建，reopen/replay 不检查。
- 判据为 Shot 实际 cast（与 Gate 同源），不是 `CommercialExecutionProjection.character_requirement_ids`
  ——后者是整片 protagonist 列表（`min_length=1`），恒非空。
- 未定义该 ID 的 profile（含 Qingyan v1）下有人物商业 Shot 新生成/修复 fail closed，须显式修订 profile 并重封 QA policy；
  已封存 v1 证据按其 sealed hash reopen 不受影响（无代码从 `create_qingyan_ecommerce_acceptance_profile()` 重算）。
- Workflow 说明：`docs/canvas-production-harness.md` 表演控制节。

## Session Work And Decisions

Commits：`97f6161`（profile 加 ID + projection 级校验 + 测试迁移）→ `639476e`（校验移到执行绑定创建 seam，
修正恒真判据；迁移直接构造 binding 的通用商业 fixtures）→ `2f8a826`（去除 `getattr` 默认值的 fail-open；报错与文档写明 profile/QA 迁移）。

- `97f6161` 在复审完成前被并发会话的 push（`7e9457a`）一并发布到 `origin/main`；未 force push，后续修复向前追加。
- 首版 projection 级校验由 reviewer 指出恒真并会过度拦截无人物商业 Shot；已移除。
- 未实现：QA 表演规则 `requirement_id` 与 binding ID 的激活期联动校验（残余，bridge 在修复时仍 fail closed）。

## Verification And Evidence

- Related receipt `.agent/harness/runs/ecommerce-performance-seam-related-20261028/receipt.json`（`46f9c80..639476e`）
  status `failed`：6 项结构检查 passed；`generation_feedback_tests` 仅既有
  `test_generation_runtime_repair.py::test_cross_provider_canvas_reopen_after_paid_intent_uses_consumed_lineage`
  失败（Seedance compiler/4 写作 Gate 与旧 fixture，基线既有），其余 14 项被 harness 跳过。
- 干净 worktree @`2f8a826` 按 policy argv 直跑该 14 项及 `generation_feedback_tests`：除上述 1 例外全部 passed
  （合计 6409 passed），含 `ecommerce_production_job_tests` 149、`production_video_provider_tests` 1297、
  `commercial_source_preparation_tests` 1040、`production_state_tests` 962。
- 更早 receipt：`ecommerce-performance-contract-related-20261027`（并发提交致 `source scope changed` 失败）、
  `-r2`（HEAD 已前移致 closure 不合格未运行）；`97f6161` 的跳过项另于干净 worktree 直跑 7 项全部 passed。
- e2e seam 测试 `test_cast_commercial_shot_without_performance_review_stops_before_binding` 经 mutation 验证
  （移除 `create()` 调用即失败）。
- Read-only `oh-my-claudecode:code-reviewer`：`97f6161` 1 major（恒真判据）、4 minor；`639476e` 复审
  `NO_BLOCKING_ISSUES`，1 major（profile 迁移未说明）及 `getattr` minor 于 `2f8a826` 采纳。
- 未运行 full regression；未生成媒体，未调用 Provider。

## Agent Guardrails

- 有人物的商业 Shot：`applicable_requirement_ids` 必含 `shot.performance.character_direction`，selected QA 中同 ID 的
  raw 规则 `intent_paths` 绑定 `generation_intent.performance_intent`，proof 与商业评审一致。
- 不得用 `shot.*` 外的表演条目满足 Gate；不得以放宽 Gate 换取旧 fixture 通过。
- 判断"Shot 是否有人物"用 `requirement.characters`，不用 projection 的 protagonist 列表。

## Record And Learning Evaluation

`distill-ai-video-learning` 评估为 `no_candidate`：契约修复，非重复媒体实验。
