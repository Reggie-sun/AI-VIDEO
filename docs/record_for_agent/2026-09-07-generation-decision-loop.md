---
record_kind: architecture_implementation
topic_id: generation-decision-loop
learning_eligibility: ineligible
---

# Generation Decision Loop Implementation Record

Date: 2026-09-07

## Purpose

用户明确要求实现 `docs/superpowers/specs/2026-09-06-ai-video-generation-decision-loop.md`。
本记录对应 deterministic decision/diagnosis/compilation contract，不是新媒体实验或 quality acceptance。

## Current Runtime Truth

- 新任务入口为 `VideoGenerationResolver.resolve_requirement(..., inputs=DecisionInputs)`。
  Router 比较 candidate recipes 与显式 evidence；`inspect_capability()` 只检查技术兼容，
  `_bind_requirement()` 是内部 exact binder。旧 sealed request 直接走既有 compile/replay/recovery。
- Planner 暴露 relational difficulty facts，固定 confidence 和历史 plan hash 保持原义。
  Production 不 import Planning/Q0/RAG；外层负责注入当前、完整、authority-separated 的投影。
- Recipe 绑定 selected `DomainAcceptancePolicy` 的完整 required IDs 与 versioned
  `generation_requirements`；不能只提供有利的 requirement 子集。Stage/proof/tolerance 由原 acceptance
  owner seal；compiler 不新增 Gate、不纠正旧 verdict。Final composition 字幕不误作 raw finding。
- Native grammar 由 `_h3_prompt.py` / `_vidu_prompt.py` 等 adapter owner 表达并说明非文本
  control coverage；generic compiler 验证 raw canonical value/coverage 和 output/audio controls。
  不可表达时 typed unsupported，不截断或改写目标。缺少完整 native compiler 的候选不能退回旧字段展开。
- Seed 与 attempt identity 分开；`CompiledComparison` 由 Router 从 validated actual baseline
  request 导出，compiler 比较真正 request delta。双方 None/-1 seed 均披露 uncontrolled stochasticity。
  不能借 request ID 变化宣称单变量，也不能借 intervention 重命名抹去已记录的 semantic hypothesis。
- Evidence 按 exact artifact 去重，required IDs 保持完整覆盖。Human 拒绝继续阻塞；无媒体 runtime
  failure、unknown outcome 与缺证据不作为模型质量 FAIL。Unknown outcome 只能交回 explicit recovery。
  当前结果合并同 request/artifact/recipe/facts/rubric/stage 的 proof layers，保留原 evidence hashes；
  补齐缺证据可关闭 `NOT_EVALUATED`，但技术 PASS 不能抹去同一媒体的 human FAIL。
- ExecutionLimits 是既有 orchestration 的当前 task 投影，不是新 ledger、budget reservation 或 permit。
  Local exemption、有限 batch、paid task ceiling、continuity route lock 与 existing effects gates 不变。

## Verification And Review

新增 `tests/test_production_generation_decision.py` 覆盖 spec A1–A18 的 deterministic seam，包括
public Router、reference delta、fixed seed、真实 Vidu native compiler→resolver（fake transport
零调用）、历史 hash、unexpressed canonical intent、完整 inventory、human/evidence gaps、stale
projection、tie/order、local/paid scope、未知 outcome、semantic resampling history 和 continuity lock。

原始 focused pass 不作为最终 acceptance：native `reviewer_xhigh` 首轮发现完整 coverage、baseline
authenticity、Vidu placeholder、同维度缺失 finding 四个 blockers；修复后再按同 tier 复核。
后续将非文本 controls 和缺失 historical intervention semantic identity 的情况纳入 fail-closed regression。
最终边界修复涵盖 unique-attempt resample 计数、资源停止、当前结果复用与分离 proof layers 的拒绝保留。
42 个 decision tests 已通过；较广 focused suite 在最终边界修复前为 484 passed。
Native `reviewer_xhigh` 最终 scoped re-review 为 `accept`，无剩余 blocking issues；另行检查
proof 隔离、原始 evidence 不变和顺序确定性，未执行任何 Provider/media action。
最终 exact commit-range Harness receipt 计划路径为
`.agent/harness/runs/generation-decision-loop-20260907-final/receipt.json`；以实际 receipt 与 freshness
verification 为准，文件名和本文不代替执行结果。

## Limits And Publication

现有 Product source/scripts 没有通用 Router caller；交付的是纯 API，未运行 autonomous Provider
loop。No Provider、ComfyUI、analyzer、media、Registry/Manifest mutation、activation 或 P6 effects。
没有冻结 empirical cohort/protocol，生成可用率和修复质量收益为 `not established`。
当前工作区已有 staged `runs/jieshi-*` 文件和 untracked 输入 spec，均保持外部工作，不纳入本任务 commit。
只创建 local commits，不 push/release。历史媒体失败与用户 1.0x verdict 全部不变。

## Learning Evaluation

按 `record-ai-video-session` → `distill-ai-video-learning` 自动评估为 `no_candidate`：本轮是
deterministic architecture implementation，没有新的独立媒体样本、受控多臂实验或能够更新现有
model-quality claim 的实证。不得把 regression tests 当成 Provider 学习证据；不创建占位 claim，
不修改 shared Skill/adopted policy，不主动重建 RAG。
