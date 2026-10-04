# Sequence Continuity Implementation Plan

**Goal:** 在 Planner前materialize结构化sequence edge，并使policy沿标准handoff保持完整。

**Spec:** `docs/superpowers/specs/2026-10-04-sequence-continuity-materialization.md`。

**Invariants:** 既有typed模型/唯一committer；prompt非truth；缺证停止；independent/reset合法；
FULL gate和METASO能力不变；零外部/媒体效果；历史hash与evidence保留。

## Changed Paths

- Create `src/ai_video/planning/sequence_continuity.py`：canonical sequence authoring adapter。
- Create `src/ai_video/production/_sequence_source.py`：共用只读accepted lineage/causal proof核验，
  不增加edge materializer；`generation_feedback.py`、`generation_execution.py`接入实际边界。
- Modify `_planner_models.py`、`video_planner.py`、`planning/__init__.py`：内嵌existing policy及handoff消费。
- Modify `_current_plan_projection.py`：保留同asset不同canonical owner的exact freshness lookup。
- Modify `generation_feedback_context.py`、`scripts/generation_feedback_driver.py`：route/policy不丢失。
- 若复现成立，Modify `_shot_router_contracts.py`、`_video_requirement_routing.py`：仅移除错误的
  previous-base/target-current snapshot相等假设，保留exact source/target/terminal及capability校验。
- Modify `shot_router.py`：validated v2 causal edge满足重复的legacy semantic-state证明要求。
  public resolver在新activation pointer存在时重开project；identity/style无terminal保持合法。
- Modify `tests/production_generation_execution_factory.py`：测试source经标准Planner/Readiness封存intent与stack。
- Tests `tests/test_planning_sequence_continuity.py`、existing readiness/Router/feedback suites；
  `.agent/harness/policy.yaml`仅添加新suite到existing categories。
- Update `docs/agent-primary-contract-matrix.md`、`docs/v0.2-runtime-baseline.md`；完成session record。

## Milestone 1: Materialize And Block Before Planning

先写完整十维prop-neutral fixture及缺证、identity/hash mismatch RED tests。
adapter使用standard loader、Storyboard adjacency、source execution/evaluation/terminal readers；
核验source activated lineage、source close/target open columnhash，然后create policy及derive previous。
FULL同时要求既有QA recipe与analyzer/human评价证明exact close-column；技术PASS不能升格。
新request封存existingpolicy，明确independent不读取source，不因顺序强制FULL。

## Milestone 2: Preserve Canonical Handoff

嵌入policy默认进入`require_current_video_plan`和`prepare_shot_for_existing_production`；
冲突/缺失route在feedback helper停止。支持explicit driver route binding反序列化，无remote效果。
hard-cut FULL只有现有registered C2 keyframe/HardCutKeyframeBinding才能进入I2V；缺图明确block。
复现并最小修正source activation与target snapshot不同的lineage阻塞，不动Provider gate。

## Milestone 3: Verify And Complete

运行新suite及Planner/readiness/transition/Router/feedback/generation suites；
跑task Architecture Gate、exact staged Harness；通过后对同一snapshot双独立native review。
semantic修复后重跑affected checks与适用review。Parent核对final diff、记录结果、仅commit owned paths。

## Acceptance Criteria

continuous/FULL、hard-cut/FULL、reset、identity-only、independent五种路径可区分；
缺十维state/accepted source/stale identities必须block；standard readiness确实消费policy；
soft-only FULL仍返回`CONTINUITY_FRAME_CONDITIONING_REQUIRED`；valid derived I2V可route。
工程PASS不证明H3媒体质量或Production acceptance。

## Self Review

三个milestones覆盖spec全部要求；不增加第二schema或state owner；
仅source snapshot阻塞有具体复现才修改旧validation；无新增worktree/Provider依赖/执行授权。
