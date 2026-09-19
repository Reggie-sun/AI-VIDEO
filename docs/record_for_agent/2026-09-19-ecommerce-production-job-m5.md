---
record_kind: architecture_implementation
topic_id: ecommerce-production-job-m5-composition-render
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Ecommerce Production Job M5 Record

Date: 2026-09-19

## Purpose

本文记录 Ecommerce Production Job 的 M5 `Composition And Render` offline implementation checkpoint。它不表示已经生成真实媒体、完成主观视觉验收、执行 remote/paid Provider submit、激活真实 Production 项目、push 或 release。

## Current Runtime Truth

Commit `95bdda30e713db015a50d096f8618a419ce2644e` 已实现：

- `EcommerceCompositionExecutionPlan.prepare()` 校验 exact `AdCreativePlan`、runtime handoff、compile provenance、commercial projection 与 accepted Shot assets，并只消费 canonical `ResolvedComposition` 与 `ResolvedTimeline`。
- Ecommerce graphics、subtitle、product presentation、animation、sound cue 与 audio semantic roles 被投影到现有 composition contracts；没有创建第二套 timeline、renderer 或 activation truth。
- `EcommerceHyperFramesInvocation` 固定 canonical render identity 与 toolchain；`render()` 只调用 public `render_with_hyperframes()`，`ProductionStateCommitter` 仍是唯一 durable render writer/activation owner。
- replay 通过 standard Production loader 检查 active render 与四个 render-domain dependency nodes；只有 exact render hash、canonical desired fingerprints 与 graph evidence 全部一致才复用。
- matching durable render attempt 会恢复 original base revision、base render 与 selection identity。`RUNNING` / `OUTCOME_UNKNOWN` 要求 explicit recovery，terminal non-success 要求新的 diagnosed attempt，`SUCCEEDED` 必须重新 inspect exact active render。
- historical registry/project mismatch 被视为 stale rebuild frontier，而不是复用旧 render；exact completed replay 不再次调用 renderer 或写 Manifest。

M5 没有修改 dirty `composition.py`、`composition_contracts.py`、state-committer owners 或 canonical timeline implementation。新增 assembly facade 只验证、投影并委托既有 canonical owners。

## Verification And Evidence

Focused offline verification：

- Ecommerce Job、assembly 与 repair suites：`40 passed in 10.34s`。
- M5 plan focused suite（assembly、composition、audio、captions、HyperFrames）：`405 passed, 3 skipped in 53.54s`。
- `python scripts/agent_harness.py policy-audit`：`candidate_count: 739`，所有 diagnostics 为空。
- independent `reviewer_xhigh` 最终未报告 P0/P1/P2；其保留 concern 是 integration fixture 手工构造 prepared object 并替换 media probe/decode helpers，因此不能单独证明完整真实媒体的 `prepare -> render -> reopen -> replay` 观看质量。

Harness 对 exact commit range `b1c1a6c0a0ecbc4ef672f53d19b1eb2ef52fc1a3..95bdda30e713db015a50d096f8618a419ce2644e` 生成：

`.agent/harness/runs/ecommerce-production-job-m5-20260919-01/receipt.json`

该 run 包含：

- documentation contract gate PASS；
- Architecture Gate PASS；
- task-delta architecture tests `238 passed`；
- Production contract tests `3529 passed, 3 skipped, 1670 deselected`；
- 其余 selected checks 分别 `13 passed`、`60 passed`、`94 passed`。

随后从 commit `95bdda30e713db015a50d096f8618a419ce2644e` 的 clean ordinary clone 运行 `verify-receipt`；`fresh`、`artifact_integrity`、`snapshot_matches`、`scope_paths_match`、`policy_matches`、`complete_completion_proof` 与 `closure_eligible` 全部为 `true`。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M5-COMMIT | commit:95bdda30e713db015a50d096f8618a419ce2644e | ecommerce-production-job-m5 | implementation-95bdda3 | N/A | NO_ARTIFACT:OFFLINE_IMPLEMENTATION | code_and_tests | PASS | NONE | NEW_ATTEMPT | NONE | git commit `95bdda30e713db015a50d096f8618a419ce2644e` |
| M5-HARNESS | harness:ecommerce-production-job-m5-20260919-01 | ecommerce-production-job-m5 | exact-range-harness | N/A | edc595e40de119fe50d07afb06180c58bb9bda3b9df0b28f98a563c1e98450c9 | harness | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | M5-COMMIT | `.agent/harness/runs/ecommerce-production-job-m5-20260919-01/receipt.json` |

## Assessment

M5 已形成 committed、policy-verified 的 offline deterministic composition/render checkpoint。该结论只覆盖 contract binding、canonical delegation、durable transaction behavior、failure/recovery 与 replay semantics；测试生成的媒体与替换 runner 不构成真实 Ecommerce 广告质量、观看性或 Final Acceptance 证据。

## Remaining Risks Or Next Work

- M6 仍需把 exact current render hash 贯穿 universal/ecommerce/caption/final-output review，拒绝 evidence 不全的 PASS，并通过 canonical Final Acceptance owner 后进行原子 delivery packaging。
- M7 仍需完成 offline interruption/repair/replay E2E 与 canonical docs；`docs/agent-primary-contract-matrix.md` 和 `docs/v0.2-runtime-baseline.md` 当前存在 unrelated same-file changes，若 M7 必须写入则仍是 ownership blocker。
- 未运行 remote/paid Provider、真实 media generation、Production activation 或 human visual review；不得从本记录推断已经出片。

## Agent Guardrails

- exact Harness PASS 只证明 policy 覆盖的 engineering contracts，不替代对最终 MP4 的视觉、动作、连续性、节奏、音频、字幕与叙事验收。
- delivery、review 与 activation 必须继续委托现有 canonical owners，不得新增第二套 mutable lifecycle 或 acceptance truth。
- exact replay 必须保持零 renderer/Provider/Manifest side effect；unknown outcome 必须继续 explicit recovery。
- unrelated staged/dirty voice、S02、composition、state-committer 与 canonical docs changes 未被本 milestone stage 或 commit。
