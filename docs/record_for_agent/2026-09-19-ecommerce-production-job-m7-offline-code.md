---
record_kind: architecture_implementation
topic_id: ecommerce-production-job-m7-offline-code
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Ecommerce Production Job M7 Offline Code Record

Date: 2026-09-19

## Supersession Notice — 2026-09-24

本记录下方 `5f743ca` 与后续 snapshot 的 Harness / review 状态均为各自当时的历史
证据，不代表当前 `main` 的 M7 验收。当前任务代码 checkpoint 是 `c5ec8e0`：
`9b739c7` 让 Job 在预检中识别持久化 Final Review 失败和 `NOT_EVALUATED`，
`a6fad2e` 增加真实 Job 对 canonical Final Acceptance → delivery → exact replay 的
测试，`481c2a5` 收紧 CAPTION 局部修复的失败原因和缺失证据路由。`481c2a5` 的
两份独立只读审查均复现：CAPTION 总裁决 `FAIL` 会遮住其他必需组因 cue 覆盖或工具
授权不足而产生的 `NOT_EVALUATED`，Job 仅看 raw findings 会错误投影重合成。
`b404e91` 在 P6 唯一 adjudicator 中暴露同一次裁决的 per-group verdict 和已授权
findings，Job 只消费这份 canonical 结果。`fc805ed` 的独立审查继续复现一项
blocking candidate：失败 finding 指向当前 CAPTION context 外的 cue 仍可触发
局部重合成。`c5ec8e0` 让 P6 对外部 subject 返回 `NOT_EVALUATED`，并从同一次
裁决提供每组 coverage completeness；Job 遇到证据不全先要求证据修复，不建立
第二套 QA 或 activation truth。

修复先有失败回归，再通过 `.venv/bin/python -m pytest -q`
`tests/test_production_ecommerce_job.py`、`tests/test_production_caption_quality.py`、
`tests/test_production_ecommerce_job_review.py`、
`tests/test_production_ecommerce_job_projection.py`，最新结果 `76 passed`。针对
`481c2a5` 的 Harness run
`.agent/harness/runs/ecommerce-production-job-final-481c2a5-20260924-01/receipt.json`
在所有 checks 执行时工作区 HEAD 已推进，`workspace_stable_confirmed=false`，
整体 `status=failed`；不得把其各子项通过当成当前 fresh closure。`fc805ed`
的 Harness 因后续 semantic fix 同样不属于最终快照。`c5ec8e0`
之后的 final exact-range Harness 与同快照双审在本记录写入时尚未完成。

M0–M6 code 与部分 M7 offline scenarios 已实现；M7 full canonical cross-stage E2E
仍未通过。现有真实双 Shot Job 测试止于 `PREPARE_COMPOSITION`，而已有 delivery
集成测试从另一个已 Final Accepted Project 开始。前者的 generated-video fixture
为 64×64、1 秒，封存 Shot / delivery 需要 3 秒、1080×1920。离线合成的临时
9:16 MP4 可以满足媒体事实，但还须使真实 creative projection、产品图层、音频、
P6 与 delivery identity 在同一 Project 串联；不能用 scripted projection、fake
metadata 或拆开的 owner tests 冒充该 E2E。当前没有 remote/paid Provider submit、
真实产品媒体生成、Production activation、人工视觉验收、push 或 release。

## Supersession Notice — 2026-09-23

下文关于 `5f743ca` 的 final Harness PASS 与 Kimi review 仅是该旧 snapshot 的历史证据，
不代表后续修复已经通过 final closure。Native Codex 对 `5f743ca` 的独立审查发现三个
blocking candidates：修复额度耗尽仍投影修复动作、重复 `NOT_EVALUATED` 证据导致
Manifest 卡在 `INTENT`、以及旧 attempt / Gate evidence 可驱动新的 media repair。
代码修复分别提交为 `6834cd049bdb0b357ce15bebdca94574cfdccc8d` 和
`8584bc4d7e5ad4f947eb54b2f52b2f8a27049307`；原审查结论不能转用于新 snapshot。

修复后 `tests/test_production_ecommerce_job.py` 全模块 `40 passed`，
`tests/test_production_generated_video_e2e.py` 为 `49 passed`。更广的 Ecommerce
focused suite 曾得 `111 passed`，但运行早于最后一项零额度投影修复；随后已单独重跑
Job 模块。exact range `86e39fe..8584bc4` 的 Harness inspection 确认本任务只有五个
changed paths、`closure_eligible=true`，但 run
`.agent/harness/runs/ecommerce-production-job-m4-m7-followup-20260923-01/receipt.json`
在 `policy_audit_check` 失败，后续 checks 被跳过。全仓 policy audit 报告七个其他
voice / runtime-repair 文件缺少 mapping，其中三个 test 缺少 check 引用；修复需要
修改当前由其他 writer staged 的 `.agent/harness/policy.yaml`，本轮未触碰该文件。
因此新 snapshot 没有 fresh passing Harness receipt，M4–M7 最终 closure 仍被阻断。
新的 Kimi deep review 对旧 snapshot 的执行结果为 `OUTCOME_UNKNOWN`（上游 502），
不构成 review verdict；修复后的 snapshot 尚未完成所需独立审查。

本轮只有 offline code、tests 和本记录；没有 remote/paid Provider submit、媒体生成、
真实 Production activation、人工视觉验收、push 或 release。现有 unrelated staged / dirty
work 保留；独立 RAG index 未刷新。

## Continuation — Final Harness Receipt And Kimi Independent Review

Date: 2026-09-20

Final milestone evidence for the immutable snapshot `5f743cac22447fec5a1fd29d4dd6bba5b0af09aa`:

- Fresh exact-range Harness run `ecommerce-production-job-m4-m7-final-20260919-05`
  over `cd6edd7802550f6c8ded4b3990930f62778d1af8..5f743cac22447fec5a1fd29d4dd6bba5b0af09aa`
  finished `status=passed` with `closure_eligible=true`; receipt SHA-256
  `06fd69bbeb22d3703c01153f7f62d753f8216f400ac7e68c52c57326d36e96d1` at
  `.agent/harness/runs/ecommerce-production-job-m4-m7-final-20260919-05/receipt.json`.
- Independent Kimi review of the same snapshot reported no P0 and no P1. All eight
  closure invariants (sole committer writer, declared-input repair binding,
  unknown-outcome fail-closed, exact resume/replay, plan-scoped admission lock,
  authoring stops, verified request delta, canonical evidence-repair frontier)
  were traced against real call paths, and the reviewer independently ran the
  policy-routed focused suite (168 tests) in a detached worktree at `5f743ca`
  with all tests passing. Four P2 findings remain as follow-ups, none of which
  violate a milestone invariant: raw `ValueError` from `job_execution_guard()`
  on an empty-shot plan escaping `advance_once` untyped; an unwrapped
  `inspect_ecommerce_review_frontier()` call in the no-`review_execution` branch
  of `ecommerce_job.py`; outer `except AiVideoError` in `advance_once`
  mis-classifying guard-cleanup failures as `ECOMMERCE_JOB_EXECUTION_BUSY`; and
  media repair not rejecting a caller-built repair plan that declares a fresh
  `attempt_id` for an already-activated sibling Shot (bounded by ceiling
  counting, no canonical caller does this).
- The Native Codex half of the required dual independent review was NOT
  completed: the Codex CLI quota was exhausted during this session and the user
  directed skipping it for now. Per the roadmap's final same-snapshot dual
  independent review requirement, M4–M7 final closure remains incomplete until
  a Native Codex review of snapshot `5f743ca` finishes with no unresolved
  P0/P1. This record does not claim full dual-review closure.
- After the reviewed snapshot, `main` advanced to `b7affb4` with unrelated
  committed work (voice routing, S02 prospective, MiniMax speech, docs). That
  work is outside the M4–M7 milestone scope; all milestone evidence above stays
  anchored to exact range `cd6edd7..5f743ca`.

## Continuation — Canonical Reopen And Repair Binding

Commit `66cfc73a4437ca46469db0599551af19bce32ea7` closes four blocking findings
from the independent review of snapshot `ae7f10621c7b1d04cbd775e15b1f691ebaaa768a`:

- repair execution now uses the exact declared input whose identity and request delta
  were validated; a deferred factory cannot replace it with a different request,
  Provider or service under the same Shot / attempt IDs;
- evidence repair returns the canonical `REPAIR_SHOT_MEDIA`,
  `REPAIR_SHOT_EVIDENCE` or `RECOVER_UNKNOWN_OUTCOME` frontier after a persisted
  `REVIEW_EVIDENCE_INVALID` result, while unrelated request-identity errors still
  fail closed as execution-input blockers;
- resume reads exact activated checkpoints from the declared canonical services and
  validates them before realizing deferred inputs, so an already completed Shot does
  not repeat compilation, materialization or Provider-side effects;
- the canonical two-Shot scenario in `tests/test_production_ecommerce_job.py`
  now exercises a real
  two-Shot `EcommerceProductionJobService` over `ProductionStateCommitter`,
  `VideoGenerationService`, persisted Manifest / Project / Registry state and
  deterministic local fixture Providers. It destroys and rebuilds Job, service,
  committer and plan instances after Shot 1 activation, proves that only Shot 2 is
  realized on resume, and proves completed replay leaves both Provider counters and
  Manifest bytes unchanged.

The earlier in-memory application scenarios remain useful orchestration unit tests,
but no longer carry the canonical reopen proof. Fresh verification for this
continuation is `60 passed` across the changed coordinator / Job / repair / canonical
E2E modules, `78 passed` for the M4 plan suite, and `101 passed in 214.74s` for the
M7 focused suite including the new canonical E2E. Final completion still requires a
new exact-range Harness receipt and independent Native Codex plus Kimi review of the
same later immutable snapshot.

## Continuation — Canonical Docs And Final-Review Fixes

Commit `4ab55a01d44c8992bd82748dfde302f3400635dc` resolved the previously recorded
same-file documentation blocker through a temporary Git index: it updated the Ecommerce
Production Job ownership/routing row, runtime baseline and roadmap while preserving the
pre-existing staged patch byte-for-byte.

The first immutable final review then found four real M4 defects. Commit
`a7b6439` fixes all four without changing canonical writer, activation, timeline,
renderer, review or delivery ownership:

- persisted `RUNNING + VideoAttemptPhase.SUBMIT_INTENT` now projects to
  `RECOVER_UNKNOWN_OUTCOME`; it is never treated as permission to resubmit;
- ordered generation can realize each Shot input after the prior Shot activation, so
  later requests can be recompiled and resealed against current canonical pointers;
- `CAPABILITY_BOUNDARY` and `SPLIT_SHOT` stop for authoring, and media repair requires
  an actual verified before/after request delta in addition to declared variables;
- one plan-scoped admission lock now covers locked reinspection, canonical attempt
  counting and coordinator execution, preventing different `attempt_id` values from
  concurrently crossing the finite ceiling.

The focused Ecommerce contract suite after these fixes is `108 passed in 219.97s`.
This is an offline engineering checkpoint. Completion still requires a fresh Harness
receipt and independent Native Codex plus Kimi reviews of one later immutable snapshot;
this record does not pre-claim those results.

## Purpose

本文记录 Ecommerce Production Job M7 的 offline application E2E code checkpoint，并由上方 continuation 补充 canonical documentation closure 与 final-review fix。它固定双 Shot 顺序执行、中断后重开与 exact replay 的 executable evidence。本文不表示已经生成真实媒体、完成人工视觉验收、执行 remote/paid Provider submit、激活真实 Production 项目、push 或 release。

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

- M7 final immutable snapshot 的 fresh Harness 与 Kimi 独立 review 已完成（见顶部 continuation）；Native Codex 独立 review 因额度原因尚未执行，dual-review closure 仍开放，完成后任何后续修复都会使旧 review 失效。
- 未运行 remote/paid Provider、真实 media generation、真实 HyperFrames CLI、Production activation 或 human visual review；不得从本记录推断已经出片。

## Agent Guardrails

- application scenario 只能委托现有 compiler、bootstrap、coordinator、composition、review 与 delivery owners；不得把 test driver 变成第二套 runtime state machine。
- exact replay 必须保持所有外部 effect counters 不变；reopen 只能依据 canonical activation truth 跳过 Shot。
- technical/schema/Harness PASS 只证明 offline engineering contract，不替代最终 MP4 的视觉、动作、连续性、节奏、音频、字幕与叙事验收。
- unrelated staged/dirty voice、S02、composition、state-committer 与 canonical docs changes 未被本 milestone stage 或 commit。
