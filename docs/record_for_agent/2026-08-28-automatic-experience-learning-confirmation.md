# Automatic Experience Learning Confirmation Record

Date: 2026-08-28

## Purpose

本文记录 AI-VIDEO 在现有 `record-ai-video-session`、Agent Memory 与 historical run/record evidence 之上增加的最小 Experience Learning governance layer。目标是让 Agent 在 substantial stable record 后自动判断是否存在跨实验 Learning Claim candidate，同时把任何 Skill / Provider Policy / Preflight / Contract / Gate adoption 停在 exact 用户确认边界。

本文是 Development Governance implementation record，不是 Product Runtime、Provider qualification、Production policy adoption、P6、Final Acceptance 或 release evidence。

## Current Implemented Truth

- `Memory / record` 继续回答“过去发生了什么”；`Learning Claim` 回答“基于多次 exact evidence，目前能成立的 scoped、可撤销知识主张是什么”。两者共享 `experience` corpus，但 Learning Claim 使用 `document_kind=learning_claim` 与 `authority=advisory_learning`。
- `record-ai-video-session` 完成 substantial durable record 后必须执行 `distill-ai-video-learning`。Session hook 只接受以下 ACK 组合：
  - `recorded + no_candidate`
  - `recorded + pending_candidate`
  - `no_record + not_applicable`
- Candidate admission 只接受 two independent attempts、multi-arm controlled comparison，或 materially support/counter/narrow/reopen existing claim 的新 evidence。
- Learning Claim 将仍被 target 消费的 `Active Claim` 与新 `Pending Candidate` 分离。Pending、Reject 或 failed adoption 不得覆盖 active adopted version。
- 用户确认绑定只包含 claim path 的 candidate checkpoint commit、该 commit 中 exact file bytes SHA-256，以及 sanitized actor/time/evidence pointer。确认前不得修改或 commit adoption target。
- `CONFIRMED` 不等于 `ADOPTED`。只有 target canonical owner 的真实修改完成 mandatory tests、review 与 Harness 后，pending 才能替换 active 并记录 adoption evidence。
- `docs/record_for_agent/learning/**` 已进入 focused Harness routing；Agent Memory path-derived metadata 会覆盖 frontmatter spoofing。Claim 被纳入 corpus 后仍需下一次 authorized refresh 才能由 RAG 检索。

该 slice 没有新增 Product CLI、schema、database、daemon、Provider selector、generic patch executor、Q0 Product caller 或 Q1 automatic recommendation engine。

## Session Work And Decisions

Primary implementation commit：`3b0c235ec0823b1dd6d745cd6d3a3ffee8536cca`（parent `05b181fcc18c89d860d49f251fa2d57e71f6dc7f`）。该 commit 包含 19 个 task-owned paths，主要包括：

- `.agents/skills/distill-ai-video-learning/SKILL.md`
- `.agents/skills/distill-ai-video-learning/templates/learning-claim.md`
- `.agents/skills/record-ai-video-session/SKILL.md`
- `.agents/skills/record-ai-video-session/scripts/session_record_hook.py`
- `src/ai_video/agent_memory/corpus.py`
- `src/ai_video/agent_memory/retrieval.py`
- `.agent/harness/policy.yaml`
- 对应 Skill、hook、Agent Memory 与 Harness tests
- `AGENTS.md`、control-plane playbook、contract matrix、runtime baseline、roadmap 与 implementation plan

初次 independent `reviewer_xhigh` 正确拒绝了单一 mutable claim 的两个缺陷：confirmed preimage 无 durable identity，以及 pending revision 会覆盖仍在生效的 adopted version。实现随后改为 candidate checkpoint commit + `git show` hash verification，以及 active/pending 双 lane。最终 scoped `reviewer_xhigh` follow-up verdict 为 `accept`，无 remaining blocking issue。

## Verification And Evidence

Focused verification：

- `273 passed, 14482 warnings in 274.01s`：`tests/test_distill_ai_video_learning_skill.py`、`tests/test_record_ai_video_session_hook.py`、`tests/test_agent_memory.py`、`tests/test_agent_harness.py`、`tests/test_runtime_skill_boundary.py`。
- Reviewer concern 修正后的 quick rerun：`172 passed in 4.74s`。
- `python -m scripts.docs_contract_gate check`：PASS。
- `python scripts/agent_harness.py policy-audit`：无 missing、unmapped、unreferenced 或 unverified paths。
- Working-tree Architecture Gate：PASS；其 warning 来自 concurrent/unrelated Production changes，不属于本 task。

由于 concurrent session 在 task commit 后推进了 shared checkout `HEAD`，Harness 的 closure contract 正确拒绝以 non-current `3b0c235` 直接在 moving primary checkout 生成 fresh receipt。最终 verification 使用 local object-sharing temporary clone，将 current `HEAD` 精确固定为 `3b0c235`，再验证 immutable range `05b181f..3b0c235`。未创建 Git worktree、未移动 primary branch/ref，也未把后续 `provider-console` commits 纳入 scope。

Fresh exact-range Harness receipt：`.agent/harness/runs/experience-learning-confirmation-20260828/receipt.json`。Checks：

- Documentation Contract Gate：PASS。
- Policy Audit：PASS，`candidate_count=575`，无 mapping diagnostics。
- Product Runtime Skill Boundary：`2 passed`。
- task-range Architecture Gate：PASS，`0 error / 0 warning / 0 info`。
- Harness tests：`198 passed`。
- Agent Memory tests：`99 passed`。
- Experience Learning Skill tests：`7 passed`。

在 exact `3b0c235` snapshot 上执行 `verify-receipt` 返回：`complete_completion_proof=true`、`fresh=true`、`fresh_for_snapshot=true`、`snapshot_matches=true`、`artifact_integrity=true`、`passed=true`。Receipt 与 check artifacts 已复制回上述 repository-relative path；临时 clone 随后通过 recoverable trash 操作移除。

## 2026-08-29 Language Format Follow-Up

Learning Claim 的人类可读格式已显式对齐 repository `AGENTS.md`：使用英文 section title 与中文正文；`command`、path、filename、config key、API、schema field、enum、hash、model、Provider 与 Skill name 保持原文并在适合时使用反引号。Machine-readable frontmatter key 与 enum value 不翻译。

实现 commit：`675bbb3ab165404e5c1ca271ace6f0223fe65699`（parent `812213ff17a6a47fbae3e8a57f3f15a2cd2d29a6`）。修改范围仅包括：

- `.agents/skills/distill-ai-video-learning/SKILL.md`
- `.agents/skills/distill-ai-video-learning/templates/learning-claim.md`
- `tests/test_distill_ai_video_learning_skill.py`

该 follow-up 没有改变 candidate admission、confirmation hash、promotion lifecycle、promotion target 或 adoption boundary。Focused Skill tests 为 `8 passed in 0.03s`，Skill validator 返回 `Skill is valid!`，`git diff --check` 通过。

Fresh exact-range Harness receipt：`.agent/harness/runs/learning-claim-language-format-20260829/receipt.json`。Receipt 覆盖 immutable range `812213f..675bbb3`，其中 Documentation Contract Gate、Policy Audit、Product Runtime Skill Boundary、task-range Architecture Gate、Experience Learning tests 与 Harness tests 均 PASS；`verify-receipt` 返回 `complete_completion_proof=true`、`fresh=true`、`fresh_for_snapshot=true`、`snapshot_matches=true`、`artifact_integrity=true`、`passed=true`。

## Publication And Workspace State

- `3b0c235` 已是 current local `main` history 的 ancestor；本记录创建时 moving local `HEAD` 为后续 concurrent commit，不能把当前 `HEAD` hash归属给本 task。
- Cached `origin/main` 尚不包含 `3b0c235`；本轮没有 push 或 release。
- 既有 staged `docs/record_for_agent/2026-08-27-h3-conditioning-attribution-gate-stop.md` 保持 index blob `1aa1c60bef374440e09d594042e466e71bfb9d6f`，未被 task commit 包含。
- `.codex/config.toml`、`artifacts/`、既有 empirical-quality plan/spec 与其他 concurrent work 均未 stage、commit、revert 或修改。

## Automatic Learning Evaluation

结果：`no_candidate`。

理由：本 session 实现的是 Experience Learning governance mechanism 与 confirmation contract，没有新增 Qingyan / H3 / T8 的真实多-attempt媒体 evidence、controlled comparison 或 materially changing existing claim evidence。把本实现自身写成 Learning Claim 会混淆 architecture decision 与 empirical production learning，因此未创建 `docs/record_for_agent/learning/**` placeholder，也没有请求 adoption confirmation。

2026-08-29 的 language-format follow-up 同样为 `no_candidate`：它只修正 Skill 输出契约与 template 表达，没有新增 empirical experiment evidence，也没有改变既有 claim 的 supporting、counter、scope 或 confidence 判断。

## Remaining Boundaries

- 首个真实 Learning Claim 尚未产生；因此尚无真实 candidate checkpoint、用户 Confirm/Revise/Reject 或 target adoption E2E evidence。
- Focused tests 会校验 checked-in claim 的 state enums 与 confirmed actor/time/hash/commit fields，但在首个真实 claim/adoption 前仍值得增加只读 validator，以重开 commit/path/hash并验证 adoption evidence；不需要 generic patch engine。
- 本轮没有刷新 Agent Memory derived index；未来 claim 写入 corpus 后，在下一次 authorized refresh 前 RAG 可保持 stale。
- 未调用 Provider、未生成或分析媒体、未写 Manifest / Registry / P6 / Final Acceptance、未进行 paid/live/network execution。

## Agent Guardrails

- 不得把 `advisory_learning`、RAG score、candidate commit或用户确认解释为 Provider authorization、Production acceptance或release receipt。
- 不得在用户确认前修改 Skill / Provider Policy / Preflight / Contract / Gate target。
- Pending candidate 不得覆盖 active adopted claim；Reject或failed apply必须保留active lane。
- Memory记录history，Learning Claim表达scoped current synthesis；两者不应合并为同一种 authority。
