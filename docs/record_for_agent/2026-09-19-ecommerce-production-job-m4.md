---
record_kind: architecture_implementation
topic_id: ecommerce-production-job-m4-shot-execution-repair
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Ecommerce Production Job M4 Record

Date: 2026-09-19

## Purpose

本文记录 Ecommerce Production Job 的 M4 `Shot Execution And Bounded Repair` 实现 checkpoint、已验证边界，以及阻止继续 M5–M7 的真实 control-plane ownership conflict。它不表示已经出片、完成视觉验收、执行 remote/paid Provider submit、激活真实 Production candidate、push 或 release。

## Current Runtime Truth

Commit `80bb58874eebdba49a8bc9214451fb2e65fb8ddf` 已实现：

- `EcommerceProductionJobService.advance_once()` 通过现有 `ecommerce_ad_coordinator.py` 执行 ordered Provider Shots，没有复制 ordered Shot algorithm。
- execution facade 在任何副作用前绑定 exact Project root、sealed `AdCreativePlan`、runtime handoff、compile profile provenance、commercial projection 与 durable request identity。
- job-level ceiling 从 canonical Manifest 中累计 exact Ecommerce Shot attempts；同 Shot 的另一 plan identity 会 fail closed，不能通过重封 plan 清零 ceiling。
- `FAIL` 进入 bounded media repair；`NOT_EVALUATED` 只允许 same attempt / same MP4 evidence repair；nested evaluator `INTENT` 与顶层 `OUTCOME_UNKNOWN` 均进入 `RECOVER_UNKNOWN_OUTCOME`。
- media repair 使用 `ecommerce_job_repair.py`，校验 diagnosis、单变量 delta、per-Shot/job ceiling，以及 provider switch 的 routing/binding/permit/attempt/resolved identity 全部更新。
- canonical commercial evidence repair 在 replacement evaluator 前先持久化 same-intent `INTENT`。evaluator 中断或 immutable evidence 已写而 Manifest 更新失败时，replay 不会再次调用 evaluator，必须 explicit recovery。
- 合法 Shot revision 演进必须由 exact succeeded `VideoAttemptPhase.ACTIVATE` 证明，并只允许 canonical video candidate owner 所定义的字段变化；Scene、Character、continuity 等 intent drift 会被拒绝。
- exact replay 不产生新的 Provider submit；evidence repair 的真实 canonical test 证明 `NOT_EVALUATED -> new immutable evidence -> PASS -> activation` 时 Provider submit count 不增加。

M4 保持 `ProductionStateCommitter` 为唯一 writer，Production Manifest 为唯一 mutable lifecycle owner，现有 video candidate/activation、commercial evidence、timeline 与 review truth 未被复制。

## Verification And Evidence

Focused 与扩展 offline verification：

- M4 focused suite 在最终修复前后持续通过；最终扩展组合包含 Ecommerce Job、repair、coordinator、quality gate、generation feedback、video service 与完整 generated-video E2E，共 `147 passed in 97.36s`。
- 后续补充的 interruption projection regression 与两份 Job suites 为 `25 passed`。
- canonical fault tests 覆盖 evaluator interruption、immutable evidence write 后 Manifest write failure、nested intent-only recovery，以及 request identity drift before validation。
- independent `reviewer_xhigh` 在最后一轮报告无剩余 P0/P1；其唯一 P2（中断当次 projection 不准确）已随后由 reopen recovery projection 与 executable regression test 修复。
- scoped `git diff --check` 通过。

Harness 对 exact commit range `cd6edd7..80bb588` 生成：

`.agent/harness/runs/ecommerce-production-job-m4-20260919-01/receipt.json`

该 receipt 的 integrity、snapshot 与 scope identity 均有效，但 status 为 `failed`，因此不是 passing completion receipt。唯一执行失败是 `policy_audit_check`：

- `tests/test_production_ecommerce_job.py` 尚未被 category pattern 映射；
- `tests/test_production_ecommerce_job.py` 与 `tests/test_production_ecommerce_job_repair.py` 尚未由 `ecommerce_production_job_tests` 引用。

最小 policy delta 是：

1. 在 `ecommerce_production_job.patterns` 中显式加入 `tests/test_production_ecommerce_job.py`；现有 `tests/test_production_ecommerce_job_*.py` 不匹配该文件名。
2. 在 `ecommerce_production_job_tests.argv` 中加入 `tests/test_production_ecommerce_job.py` 与 `tests/test_production_ecommerce_job_repair.py`。

`.agent/harness/policy.yaml` 当前已经包含另一 writer 的 staged voice/S02 changes；依据 task ownership contract，本 session 未写入、覆盖、stage 或 commit 该文件。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M4-COMMIT | commit:80bb58874eebdba49a8bc9214451fb2e65fb8ddf | ecommerce-production-job-m4 | implementation-80bb588 | N/A | NO_ARTIFACT:OFFLINE_IMPLEMENTATION | code_and_tests | PASS | NONE | NEW_ATTEMPT | NONE | git commit `80bb58874eebdba49a8bc9214451fb2e65fb8ddf` |
| M4-HARNESS | harness:ecommerce-production-job-m4-20260919-01 | ecommerce-production-job-m4 | harness-policy-audit | N/A | NO_ARTIFACT:POLICY_AUDIT_FAILED | harness | FAIL | CONTROL_PLANE_MAPPING | SAME_EVIDENCE_NEW_PROOF_LAYER | M4-COMMIT | `.agent/harness/runs/ecommerce-production-job-m4-20260919-01/receipt.json` |

## Assessment

M4 implementation 已形成 committed、offline-tested checkpoint，但尚未满足 repository completion contract，因为 exact-commit Harness 没有 passing receipt。这个失败不是产品测试回归，而是新增 tests 与当前 Harness policy 的 mapping/reference 缺口；在 conflict owner 合并最小 delta 并重新运行 exact-range Harness 前，不得把 M4 描述为 policy-verified completion。

M5 composition/render、M6 final QC/delivery 与 M7 offline E2E/docs 尚未开始。当前 `composition.py`、`composition_contracts.py`、`.agent/harness/policy.yaml`、`docs/agent-primary-contract-matrix.md` 与 `docs/v0.2-runtime-baseline.md` 均存在 unrelated dirty/staged ownership，后续 slice 若必须写入这些 same-file surfaces，必须先由用户决定 ownership/sequence。

## Remaining Blocker And Next Work

当前唯一可执行 next action 是先解决 `.agent/harness/policy.yaml` ownership：由现有 owner 合并上述最小 mapping delta，或明确把该文件 ownership 交给本 task。之后对 `cd6edd7..M4-final-commit` 重跑 Harness 并验证 receipt freshness/integrity。

在 M4 passing receipt 之前不继续 M5–M7；这避免让后续 milestone 建立在未闭合的 changed-path policy 上。

## Agent Guardrails

- 本记录仅覆盖 offline deterministic implementation 与 tests，不产生 live media、观看质量、P6、Final Acceptance 或 delivery truth。
- failed Harness receipt 不能作为 completion proof。
- 不得用 generic visual defaults、technical PASS 或 schema closure替代真实最终 MP4 的视觉、动作、节奏、音频和叙事验收。
- 不得触碰 unrelated staged/dirty voice、S02、composition、state-committer 或 canonical docs changes。
- 没有执行 remote/paid Provider submit、真实媒体生成、Production activation、push 或 release。
