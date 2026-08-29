---
record_kind: architecture_implementation
topic_id: architecture-deepening-three-slices
learning_eligibility: ineligible
---

# Architecture Deepening Three-Slice Plan Record

Date: 2026-08-29

## Purpose

本文记录 Agent Memory retrieval、`VideoGenerationService` lifecycle 与 provider-neutral requirement
invariants 三个 architecture slice 的 plan checkpoint、current evidence boundary 与后续 execution gates。

这是 architecture planning evidence，不是 runtime implementation、regression fix、Provider qualification、
P6 / Final Acceptance 或 release evidence。Canonical implementation contract 位于
`docs/superpowers/plans/2026-08-29-ai-video-architecture-deepening-three-slices.md`；current code/tests仍是
runtime truth。

## Current Runtime Truth

截至 plan commit `73d71b1`：

- Agent Memory 仍同时公开 canonical `retrieve_project()` 与 strict compatibility `search()`；
  `_search_unlocked()` / `_search_runs()` 尚未退役。
- `VideoGenerationService` 仍保留 local/remote parallel methods、atomic `validate_once()` / `activate_once()`
  与 legacy `fetch_and_activate()`；`ContinuityReviewCoordinator` 仍是后者的真实 caller。
- `video_requirement.py` 与 `_video_intent_validation.py` 仍形成 local-import/runtime-import hidden cyclic seam；
  `_h3_prompt.py` 仍调用 granular neutral validators。
- 本 session 未修改上述 runtime code、tests、contracts或state，也未调用 Provider、生成媒体或执行 live/paid action。

## Session Work And Decisions

本 session 对 current code、callers、tests、contract matrix、runtime baseline、roadmap 与 fresh Agent Memory RAG
进行了 read-heavy mapping，并形成三个独立 Slice：

1. **Slice A — Agent Memory retrieval**
   - `retrieve_project()` 保持 canonical project interface。
   - `search()` 因 current export/durable compatibility contract 与未知 external consumers，先保留为 thin adapter。
   - 共同 query lifecycle 收敛到一个 deep implementation；退役 `_search_unlocked()` / `_search_runs()`，不保留 fallback。

2. **Slice C — provider-neutral invariants**
   - `video_requirement.py` 保留 public model、strict reopen与hash owner；不搬迁 public classes。
   - 新 private invariant implementation只计算 neutral diagnostics，不接收 model class/callback，不复制 schema/hash owner。
   - causal readiness迁到 `video_transition.py`；H3 在 expression 前通过 stable neutral strict reopen fail closed，
     但不复制 neutral rules。

3. **Slice B — generated-video lifecycle**
   - 新 canonical `submit_attempt_once()` 避免与 current remote `submit_once()` signature冲突；
     `LocalSubmitContext` / `PaidSubmitContext` 从 stable `video_generation.py` interface导出。
   - `poll_once()` / common `fetch_once()` 根据 reopened durable evidence选择 lane，caller不再重复 lane branch。
   - `ProductionStateCommitter` 继续是唯一 state/permit/activation/recovery owner；一次 call最多一个 Provider effect，
     允许紧邻必要的 intent/permit/outcome writes，但不得自动跨 lifecycle actions串联。
   - `fetch_and_activate()` full retirement需要 separate public-contract approval与
     `ContinuityReviewCoordinator` migration；未获批准时必须如实停在 compatibility阶段。

推荐 execution order 是 `Slice A -> Slice C -> Slice B`。三个 Slice 没有 implementation dependency，必须各自
使用独立 checkpoint、`reviewer_xhigh`、focused tests、Architecture Gate 与 exact Harness receipt。

## Review And Corrections

initial `reviewer_xhigh` verdict 为 `reject`，指出三个 blocking contradictions：

- new/old `submit_once()` 同名 signature 无法同时成立；
- H3 若只信任 nominal Pydantic object，会漏掉 `model_construct()` / `model_copy(update=...)` bypass；
- “one durable phase”与 submit必需的 intent/effect/outcome choreography冲突。

Plan 已分别改为 `submit_attempt_once()`、stable neutral strict-reopen seam、one-Provider-effect contract；同时补齐
M0/source qualification tests、避免迁移 public model classes，并把 Agent Memory retirement proof从 private-symbol
behavior test改为 public parity + Architecture Gate / exact `rg`。scoped re-review 结果为
`accept with concerns`、无 blocking issue；最后一项 strict-reopen owner concern随后明确为
`video_requirement.py` 独占 concrete reopen/hash、private module只计算 diagnostics。

## Verification And Evidence

- Plan checkpoint commit：`73d71b1` (`docs: plan architecture deepening slices`)。
- Exact range：`73d71b1^..73d71b1`。
- Harness receipt：`.agent/harness/runs/architecture-deepening-three-slices-plan-20260829/receipt.json`。
- Receipt verification：`passed=true`、`fresh=true`、`fresh_for_snapshot=true`、`scope_paths_match=true`、
  `complete_completion_proof=true`。
- Documentation Contract Gate：PASS。
- Harness policy audit：无 unmapped、unverified、missing或unreferenced paths。
- Product Runtime / Skill boundary：`2 passed`。
- 未运行 future Slice implementation tests；plan中的 commands是后续 acceptance contract，不是本 session pass claim。

## Assessment

三个问题均属于 substantive architecture debt，但没有 current outage、data-loss、Provider incident 或已证实
regression evidence。Slice B 的 implementation semantic risk最高，Slice C 次之，Slice A 最适合作为先行
behavior-preserving convergence。

本 record 标记 `learning_eligibility: ineligible`：它记录一次 architecture decision与plan review，不包含两个
independent empirical attempts、controlled comparison或 material existing Learning Claim update，不能进入 automatic
Learning Claim admission。

Automatic `distill-ai-video-learning` evaluation outcome：`no_candidate`。本 record 为 ineligible architecture
planning evidence；fresh `experience` discovery只返回历史 architecture/lifecycle records，没有两个独立 empirical
attempts、controlled multi-arm evidence或 material existing-claim update。没有创建 Learning Claim placeholder，
也没有进入 confirmation/adoption flow。

## Remaining Risks Or Next Work

- Future Slice开始前必须重新检查 current `HEAD`、dirty ownership、callers、contracts与Harness routing；本 plan可能随
  repository演进而 stale。
- `search()` 与 lane-specific lifecycle methods 的 public removal都需要独立 compatibility approval，不能从内部 caller
  migration自动推导。
- Slice C 必须用 exact historical bytes/hash、class identity与bypass fixtures证明 zero semantic drift。
- Slice B 必须证明 local guard in-lock revalidation、Paid Provider Gate、unknown outcome、zero resubmit、held-FD fetch、
  candidate/activation separation与exact replay。
- 本 session 没有 push/release。automatic learning discovery返回 tagged stale last-good hits，并由 current CLI
  enqueue了 `experience` background refresh；本 session没有该 refresh完成/新 record已索引的 proof，因此不得声称
  current RAG index已包含本 record。

## Agent Guardrails

- 不得把 plan、record、review verdict或Harness receipt描述成 runtime implementation完成。
- 不得为统一 interface复制 `ProductionStateCommitter` phase table或创建第二 lifecycle owner。
- 不得让 H3自己拥有 neutral validity，也不得省略 compile seam的 strict reopen/tamper check。
- 不得删除 compatibility path后保留 hidden fallback或dual active implementation。
- 任一 Slice的完成必须使用其 exact current commit/snapshot重新验证，不能复用本 plan receipt。
