---
record_kind: architecture_implementation
topic_id: record-evidence-identity
learning_eligibility: ineligible
---

# Record Evidence Identity Validation Record

Date: 2026-08-29

## Purpose

本文记录 `docs/superpowers/plans/2026-08-29-ai-video-record-evidence-identity.md`
的 implementation checkpoint、已验证边界与 exact-snapshot Harness blocker。它是
Development Governance architecture implementation record，不是 empirical/model-quality
evidence，也不进入 automatic Learning Claim admission。

## Implemented Contract

commit `6a815d9da51575aad36da119f2371a0c19310361` 实现以下边界：

- `distill-ai-video-learning` 成为 `independence_key`、admission basis、evidence relation
  与 dedup 的唯一 owner；document、section、RAG hit、artifact version 与 proof layer 均不能充当
  independent evidence count。
- `record-ai-video-session` 只 capture flat classification envelope 与 eligible record 的
  `Evidence Index`，不计算 evidence independence 或决定 admission。
- Skill-local `validate_evidence_identity.py` 以显式 Markdown path、read-only、no-network 方式
  验证 record/claim identity、relation、source reference、key/tuple/anchor bijection 与 admission。
- Learning Claim template 使用 opt-in structured support/counter references；既有 pending claim bytes
  未迁移、未改写。
- Agent Memory 只为 `experience` corpus 投影 allowlisted supplemental metadata；canonical
  `authority` / `document_kind`、ranking、chunk ID、query behavior 与 adoption authority 不变。
- Harness policy、focused tests、contract matrix、control-plane playbook 与 runtime baseline 已同步。

没有新增 Product API、runtime dependency、Provider path、Production writer、Manifest/Registry state、
media generation、paid/network execution或自动 adoption。

## Verification And Evidence

实现前后的 focused evidence：

- identity/Skill scoped tests：`27 passed`。
- final focused suite：`261 passed, 1 deselected`；唯一 deselect 是下述已知 project-corpus
  calibration，用于先验证本 slice 的 deterministic behavior。
- `python -m scripts.docs_contract_gate check`：PASS。
- `python -m scripts.architecture_gate check`：PASS，`0 error(s)`；保留
  `src/ai_video/agent_memory/retrieval.py` oversized growth warning。
- `python scripts/agent_harness.py policy-audit`：`unmapped_paths=[]`、
  `missing_check_test_paths=[]`、`unverified_paths=[]`。
- independent native `reviewer_xhigh` scoped re-review：`accept`，无 blocking 或 non-blocking concern。

Exact range `c72ef8532f4b4c6191fdbcf2e5ac3e5d7754d428..6a815d9da51575aad36da119f2371a0c19310361`
由 Harness 在 detached snapshot 中执行，receipt 为：

`.agent/harness/runs/20260828T175002943865Z/receipt.json`

该 receipt 的 integrity 与 scope inspection 可解析，但状态为 `failed`，因此不是 completion proof。
通过项包括 Documentation contract gate、policy audit、Architecture Gate、
`product_runtime_skill_boundary_tests`（`2 passed`）与 Harness tests（`204 passed`）。
失败项只有：

`tests/test_agent_memory.py::test_local_multilingual_project_corpus_answerability_calibration`

noise query `zzzxqv_nonexistent_74291` 被 dense lane 接纳为一个 experience hit；诊断命中来自既有
`docs/record_for_agent/2026-08-26-qingyan-v10-cap-mechanics-and-moving-comparison-blocker.md`。

为区分 current regression 与历史 debt，同一测试已在 implementation base
`c72ef8532f4b4c6191fdbcf2e5ac3e5d7754d428` 的 `git archive` 临时快照中独立复跑，结果同样失败。
因此该 failure 先于本任务存在；本任务 commit 没有修改该 record、dense threshold、ranking、
admission lane 或 query behavior。

## Assessment

Evidence identity implementation 与 scoped semantic review 已完成，但 repository completion contract
要求 fresh passing Harness receipt；当前 checkpoint 因 pre-existing Agent Memory corpus calibration
failure 不能宣称 complete。

在本 Plan 内直接提高/改变 retrieval threshold 会违反“ranking/query behavior unchanged”；仅删除或
deselect calibration assertion 又会隐藏真实 false-positive。两种处理都属于需要单独决策的 scope expansion，
因此本轮没有静默采用。

## Automatic Learning Evaluation

`distill-ai-video-learning` outcome：`no_candidate`。

本记录已显式分类为 `architecture_implementation` / `ineligible`，只描述一次 governance
implementation checkpoint 与一个 pre-existing Harness blocker；它既不是两个独立 empirical attempts，
也不是 controlled multi-arm comparison，且没有对既有 Learning Claim 提供 material evidence update。
`experience` scope retrieval 返回 stale、tagged last-good fragments并排队 detached refresh；这些 fragments
仅用于 discovery，没有作为 source evidence、confidence 或 admission count。现有其他 topic 的 pending
Learning Claim 保持不变。

## Remaining Risk And Next Work

下一步必须先选择并批准一个独立的 Agent Memory calibration repair：

1. 保留 project-corpus gate，修正 dense answerability/admission behavior，并重新验证全部 retrieval contracts；或
2. 将 calibration 改造成稳定、版本化的 corpus fixture，同时保留能检测真实 corpus drift 的独立 gate；或
3. 接受当前 historical debt 作为显式 blocker，暂不把 `6a815d9` 宣称为完成。

任何 repair 都必须保持 path-owned authority、fail-closed stale-index behavior 与 retrieval provenance，
并重新运行 `c72ef85..repair-commit` 的 exact-range Harness。passing receipt 之前不得把 runtime baseline
中的实现陈述升级为 release、remote 或 Final Acceptance truth。

## Publication And Ownership

- implementation commit：local `main` 上的 `6a815d9da51575aad36da119f2371a0c19310361`。
- publication：未 push、未 release。
- Provider/media/Production effects：无。
- 其他 staged、dirty 与 untracked work 未被纳入 implementation commit；并行 session 在其后推进的
  commits 也不属于本任务。
- Agent Memory retrieval index 未因本记录刷新；上述 classification 只在未来 canonical build 后可见。
