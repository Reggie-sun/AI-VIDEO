---
record_kind: architecture_implementation
topic_id: continuity-first-provider-routing
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Continuity-First Provider Routing Record

Date: 2026-08-30

## Purpose

本文记录 Shot Router 的 sequence-aware Provider continuity 约束落地，以及本轮 Agent Memory preflight 的可验证边界。它是已提交 runtime architecture checkpoint，不是 Provider/model quality acceptance，也不授权新的媒体生成、paid call、activation、push 或 release。

## Current Runtime Truth

仓库没有新增 `continuity_group` 第二 owner。Sequence continuity 继续由相邻 Shot 的 exact `ContinuityTransitionPolicy` 表达：`BoundaryKind` 区分 continuous take、hard cut 与 scene boundary，`ContinuityObligation` 区分 `FULL_CONTINUITY`、`IDENTITY_STYLE_CARRYOVER` 与 `SUBSTANTIAL_RESET`。

`VideoGenerationResolver.resolve_requirement()` 现在接收 hash-bound `ContinuityProviderRouteBinding`，将以下身份封存为同一 routing evidence：

- exact previous `ProviderBoundVideoRequest`；
- source/target Shot 与 Project/Registry snapshots；
- source/destination `GenerationExecutionStackIdentity`；
- source/destination exact Provider/model/profile/capability/compiler route；
- transition policy、previous request 与 route-binding hashes。

同一 execution stack 下，上一 Shot 的 exact Provider route 被锁定；上游即使因为价格预选了另一 Provider，也会以 `CONTINUITY_PROVIDER_LOCKED` fail closed。`hard_cut` 本身不释放空间连续性；只有 obligation 明确降为 identity/style carryover 或 substantial reset 时，才允许相应重新路由。

显式 cross-stack `FULL_CONTINUITY` 要求：

1. requirement 提供明确的 subject position、screen direction、camera axis 与 framing continuity；
2. previous exact terminal evidence 必须属于 exact previous request；
3. 目标 capability 必须把该 terminal 作为第一个 `first_frame` binding；
4. reference-only capability 不得冒充 spatial/camera continuity。

Context、requirement continuity mode 与 transition obligation 必须一致。`FULL_CONTINUITY` 只接受 terminal-bearing `exact_terminal` / `multi_anchor`；`SUBSTANTIAL_RESET` 只接受 `none`；identity/style carryover 必须使用 reference 或有 typed identity continuity 的 semantic mode。Public `resolve()` 拒绝所有 continuity-bearing context，避免旧 single-Shot API 绕过 sequence evidence。

既有 capability grammar 仍是唯一能力 owner：I2V `first_frame`、FL2VA `first_frame + last_frame`、C4 cardinality/multi-anchor 与 R2V reference。没有新增平行的 support booleans；reference input acceptance 只证明 Provider 能消费 reference，不证明人物、空间位置、构图或 camera/scene continuity 已通过。

## Workflow Boundary

`prepare_shot_for_existing_production()` 在给定 transition policy 时会 round-trip 验证并把 exact policy 传入 injected `production_handoff`。仓库当前没有 monolithic production generator caller；外部 orchestration 仍负责从真实 previous request 与 execution stacks 构造完整 `ContinuityProviderRouteBinding`。这是真实 integration boundary，不是本轮代码已经证明的 live workflow。

## Verification And Evidence

Implementation commit：`1e405dd` (`feat: enforce continuity-first provider routing`)。

Exact commit-range Harness：

- receipt：`.agent/harness/runs/continuity-first-provider-routing-20260830/receipt.json`；
- receipt verification：`passed=true`、`fresh=true`、`snapshot_matches=true`、`scope_worktree_clean=true`、`complete_completion_proof=true`；
- mandatory checks：documentation contract、policy audit、runtime Skill boundary、task Architecture Gate、Provider/requirement/Router/planner/readiness suites全部通过；
-主要 suite counts：`743 passed`、`370 passed`、`278 passed`、`119 passed`、`209 passed`。

核心 regression 覆盖：

- continuous take 拒绝 lower-cost Provider preselection；
- hard cut + identity carryover 允许新 Provider，并实际绑定 identity reference；
- cross-Provider full continuity 传递 previous ending frame 为首帧；
- reference-only Provider 不能声称 spatial/camera continuity；
- public API omission、stale policy、stale target binding、unsealed destination route、same-route/different-stack 与 `none + T2V` identity-carryover mismatch 均 fail closed；
- exact terminal binding 已经 compiler/adapter tests 继续投影到目标 Provider payload。

Independent `reviewer_xhigh` 最终 verdict 为 `accept with concerns`；mechanical final import-location check为 `accept`。没有 Provider call、媒体生成、Production state write 或 paid/network submit。

## Agent Memory Preflight Boundary

本轮最初 RAG failure 有两层原因：当前 `.venv` 缺少 `agent-memory` optional dependencies；补齐后，旧 Chroma physical index 与当前 library versions 不兼容。完成 local derived-index rebuild 后，project CLI real query 可执行并返回 continuity 相关 `advisory_experience` / run-summary hits。

在本次 docs 发生变化后，后续 query exit code仍为 `0`，但部分 experience shards 被如实标记 `index_freshness=stale` 并排队 detached refresh；因此只能称为 retrieval path已恢复，不能声称所有 shards 当前 fresh。一次 dirty-tree全仓 pytest 还暴露当前 tracked corpus 的 multilingual dense-calibration drift，以及未安装 `openai-whisper` 时两个 MCP transcribe tests 的环境失败；它们未被篡改或降阈值以制造通过，也不是 exact Router Harness 的失败。

## Remaining Risks

- Architecture Gate 对 `_shot_router_contracts.py` 报告 `ARCH001 oversized-module-growth` warning；当前是已映射的 canonical contract owner，warning不阻断 Harness，但后续在能够同步 policy/contract-matrix ownership 时应评估 cohesive extraction。
- Deterministic Router evidence不证明模型实际输出的人物、产品、空间位置、构图或 camera continuity；真实媒体仍需逐 Shot `video-analysis` Gate 与人工质量判断。
- Actual Production orchestration 必须传入 exact transition、previous request、route 与 execution-stack identities；只传 readiness projection不能满足 sequence continuity。
- Local commit未 push，remote/release truth未改变。

## Agent Guardrails

- 不得因为 `hard_cut` 字样自动释放 continuity；必须读取 obligation。
- 不得把 identity reference acceptance 当成 spatial/position/camera continuity保证。
- 不得为成本优化绕过 sealed destination route或 previous terminal binding。
- start/end frame或multi-keyframe只能在 requirement已有 exact endpoint/anchors且单个 capability完整满足 grammar时使用；不得跨 capability union或伪造输入。
- 代码/Harness acceptance、RAG advisory hit、Provider payload acceptance与真实媒体质量 verdict必须保持分层。
