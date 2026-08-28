---
record_kind: architecture_implementation
topic_id: record-evidence-identity
learning_eligibility: ineligible
---

# Record Evidence Identity Validation Record

Date: 2026-08-29

## Purpose

本文记录 `docs/superpowers/plans/2026-08-29-ai-video-record-evidence-identity.md`
的 implementation completion、已验证边界与 exact-snapshot Harness blocker closure。它是
Development Governance architecture implementation record，不是 empirical/model-quality
evidence，也不进入 automatic Learning Claim admission。

## Blocker Closure — 2026-08-29

用户选择独立修复 Agent Memory calibration gate 后，原 blocker 已在保持 ranking、path-owned
authority、stale-index fail-closed 与 retrieval provenance contract 的前提下关闭：

- root cause 不是 evidence-identity metadata projection，而是 Chroma approximate ANN 的 real query
  使用 `candidate_limit`、null control 只请求 Top-1，导致同一 null embedding 在不同 ANN budget 下
  返回不同 nearest distance，并把约 `0.005047` 的搜索近似误判成 semantic excess。
- `16823ff0399a4275dbc14cc7ec0e9e65c5cdf930` 让 real query 与 null control 使用相同
  `candidate_limit`，并把 integration calibration 区分为 dense/hybrid false positive 与 exact lexical
  provenance；durable blocker record 中字面出现的 `zzzxqv_nonexistent_74291` 继续允许 lexical 命中，
  但不能被误报为 dense false positive。
- `bd85507d28cf063264bd63e604786898865ca53c` 增加 fail-closed cardinality invariant；null backend
  必须实际返回完整 `candidate_limit` 个 distance，不能用部分 response 继续 admission。
- `ec55422342abad434924b02e0b53fbd2417812a3` 明确 mismatch diagnostic，保持既有 public
  `IndexMismatchError` wrapping boundary。

最终 exact range
`da077c6273c52309fcba9767d323d867c14d82c4..ec55422342abad434924b02e0b53fbd2417812a3`
的 fresh passing receipt 为：

`.agent/harness/runs/20260828T200555310227Z/receipt.json`

`make harness-receipt` 已再次验证该 receipt 的 artifact integrity、scope、policy、snapshot、freshness、
workspace stability 与 completion proof 全部为 `true`。Agent Memory check 在 exact snapshot 中为
`104 passed`；Documentation contract gate、policy audit、boundary tests 与 Architecture Gate 也全部通过。

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

Evidence identity implementation、Agent Memory calibration repair、scoped semantic review 与 repository
completion proof 均已完成。修复没有提高 threshold、删除 calibration assertion、改变 ranking、引入
fallback，或把 lexical exact match 当成 dense semantic admission。

原 implementation receipt 与两次因 concurrent `HEAD` advance 而失败的 repair receipts继续是历史记录，
不作为 passing proof；当前完成声明只绑定上方已验证的 fresh passing receipt。

## Automatic Learning Evaluation

`distill-ai-video-learning` outcome：`no_candidate`。

本记录已显式分类为 `architecture_implementation` / `ineligible`，只描述一次 governance
implementation、calibration repair 与 deterministic closure；它既不是两个独立 empirical attempts，也不是
controlled multi-arm comparison，且没有对既有 Learning Claim 提供 material evidence update。
`experience` scope retrieval 返回 stale、tagged last-good fragments并排队 detached refresh，其中仍包含本记录
更新前的 blocker sections；automatic evaluation 已重新打开当前 exact record，并由 validator 确认为
`admitted=false`、`errors=[]`。RAG fragments 仅用于 discovery，没有作为 source evidence、confidence 或
admission count。现有其他 topic 的 pending Learning Claim 保持不变。

## Remaining Risks Or Next Work

- `src/ai_video/agent_memory/retrieval.py` 仍有 Architecture Gate oversized-module warning；本次只增加最小
  calibration contract，没有扩大为 module split。
- Agent Memory suite 仍输出既有 Pydantic deprecation warnings；本次没有把 unrelated dependency migration
  纳入 scope。
- completion proof 只证明 local repository implementation 与 deterministic verification；不产生 remote
  publication、release、Provider qualification、P6、Final Acceptance 或 human quality verdict。

## Publication And Ownership

- implementation commit：local `main` 上的 `6a815d9da51575aad36da119f2371a0c19310361`。
- calibration repair commits：`16823ff0399a4275dbc14cc7ec0e9e65c5cdf930`、
  `bd85507d28cf063264bd63e604786898865ca53c`、
  `ec55422342abad434924b02e0b53fbd2417812a3`。
- publication：未 push、未 release。
- Provider/media/Production effects：无。
- 其他 staged、dirty 与 untracked work 未被纳入 implementation commit；并行 session 在其后推进的
  commits 也不属于本任务。
- Agent Memory retrieval index 未因本记录刷新；上述 classification 只在未来 canonical build 后可见。
