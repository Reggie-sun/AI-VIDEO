---
record_kind: architecture_implementation
topic_id: ecommerce-production-job-m7-offline-code
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Ecommerce Production Job M7 Offline Code Record

Date: 2026-09-19

## Purpose

本文记录 Ecommerce Production Job M7 的 offline application E2E code checkpoint。它固定双 Shot 顺序执行、中断后重开与 exact replay 的 executable evidence，也明确 canonical documentation 尚因 existing same-file ownership 冲突未完成。本文不表示已经生成真实媒体、完成人工视觉验收、执行 remote/paid Provider submit、激活真实 Production 项目、push 或 release。

## Current Runtime Truth

Commit `c99f77767ddf1c801f721b46d8604595a8d7311b` 在现有 `tests/test_production_ecommerce_job.py` 中增加两个 application-level offline scenarios：

- fresh 双 Shot job 使用真实 ecommerce compiler/bootstrap adapter、真实 `EcommerceProductionJobService.advance_once()`、真实 `EcommerceShotExecutionPlan` 与既有 coordinator 顺序语义，从 Shot execution 推进到 composition、final review、delivery；完成后的 exact replay 不再产生 generation、composition、review 或 delivery side effect。
- interrupted/reopened job 从 first Shot 已 canonical-activated 的状态继续，只执行 second Shot，不重新提交或激活 first Shot。

这些 scenarios 使用 deterministic injected services 代替真实 Provider、renderer、analyzer 与 filesystem delivery effects。它们验证 application orchestration 和 owner delegation；真实 state mutation、repair、composition、review 与 delivery invariants 由同一 focused suite 中已有的 owner-level tests 分层覆盖。M7 没有新增第二套 Manifest、timeline、renderer、writer、activation、review 或 delivery truth。

## Verification And Evidence

针对 commit `c99f77767ddf1c801f721b46d8604595a8d7311b` 的验证包括：

- 新增的两个 offline scenarios：`2 passed, 27 deselected`。
- 完整 ecommerce job test module：`29 passed`。
- M7 plan 指定的九文件 focused suite：`90 passed in 221.96s`。
- `git diff --check 78faa047ff89f0c26e8e7dd7c4803863e74d73d7..c99f77767ddf1c801f721b46d8604595a8d7311b`：PASS。

Harness 对 exact commit range `78faa047ff89f0c26e8e7dd7c4803863e74d73d7..c99f77767ddf1c801f721b46d8604595a8d7311b` 生成：

`.agent/harness/runs/ecommerce-production-job-m7-code-20260919-01/receipt.json`

该 run 的 policy-selected结果包括 documentation contract、policy audit、runtime Skill boundary 与 Architecture Gate 全部 PASS；主要 suites 分别为 `95 passed`、`94 passed`、`962 passed` 与 `567 passed`。`verify-receipt` 返回 `passed=true`、`artifact_integrity=true`、`snapshot_matches=true`、`scope_paths_match=true`、`policy_matches=true`、`fresh=true`、`fresh_for_snapshot=true`、`complete_completion_proof=true` 与 `closure_eligible=true`。Receipt SHA-256 为 `fc55c35409801af85bffac59d72293966290be7c4283d3ec6de8e6b797f175d7`。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M7-CODE-COMMIT | commit:c99f77767ddf1c801f721b46d8604595a8d7311b | ecommerce-production-job-m7-offline | implementation-c99f777 | N/A | NO_ARTIFACT:OFFLINE_IMPLEMENTATION | code_and_tests | PASS | NONE | NEW_ATTEMPT | NONE | git commit `c99f77767ddf1c801f721b46d8604595a8d7311b` |
| M7-CODE-HARNESS | harness:ecommerce-production-job-m7-code-20260919-01 | ecommerce-production-job-m7-offline | exact-range-harness | N/A | fc55c35409801af85bffac59d72293966290be7c4283d3ec6de8e6b797f175d7 | harness | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | M7-CODE-COMMIT | `.agent/harness/runs/ecommerce-production-job-m7-code-20260919-01/receipt.json` |

## Assessment

M7 application E2E code 已形成 committed、policy-verified 的 offline checkpoint。它覆盖双 Shot 顺序、reopen 后跳过既有 activation 与 completed job exact replay；evidence repair、bounded media repair、unknown outcome stop、composition-local repair、delivery identity replay 继续由 M4-M6 的 executable owner-level tests覆盖。该分层证据不等价于一次真实 Provider-to-final-MP4 的 monolithic run，也不构成广告观看质量或人工验收。

## Remaining Risks Or Next Work

- `docs/agent-primary-contract-matrix.md` 与 `docs/v0.2-runtime-baseline.md` 存在其他 writer 的 same-file staged changes；M7 需要分别补充 ecommerce job owner/routing 与 implemented offline/Python-API boundary，但本 checkpoint 未写入这些文件。
- `docs/v0.2-agentic-production-roadmap.md` 仍需同步 M4-M7 的实际 completed/deferred 状态。
- M7 final immutable snapshot 尚需在 documentation ownership 解决后完成 native Codex 与 Kimi 双侧 independent review，并重新运行 final Harness。
- 未运行 remote/paid Provider、真实 media generation、真实 HyperFrames CLI、Production activation 或 human visual review；不得从本记录推断已经出片。

## Agent Guardrails

- application scenario 只能委托现有 compiler、bootstrap、coordinator、composition、review 与 delivery owners；不得把 test driver 变成第二套 runtime state machine。
- exact replay 必须保持所有外部 effect counters 不变；reopen 只能依据 canonical activation truth 跳过 Shot。
- technical/schema/Harness PASS 只证明 offline engineering contract，不替代最终 MP4 的视觉、动作、连续性、节奏、音频、字幕与叙事验收。
- unrelated staged/dirty voice、S02、composition、state-committer 与 canonical docs changes 未被本 milestone stage 或 commit。
