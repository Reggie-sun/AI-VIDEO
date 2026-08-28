# Automatic Experience Learning Confirmation Implementation Plan

**Goal:** 在现有 session record 与 Agent Memory 之上增加一个 Development Governance-only 的自动经验蒸馏闭环：自动形成可追溯的 `Learning Claim`，但只有用户确认 exact candidate 后才允许进入既有 Skill / Policy / Preflight / Contract / Gate owner 的采纳流程。

**Scope:** 新增 `distill-ai-video-learning` Skill 与 claim template；让 `record-ai-video-session` 在稳定记录完成后自动执行 learning evaluation，并由session hook拒绝缺少learning outcome的`recorded` ACK；让现有 `experience` RAG 对 `docs/record_for_agent/learning/**` 返回独立的 `document_kind=learning_claim` 与 `authority=advisory_learning`；补齐 Harness routing、tests、contract matrix、runtime baseline、roadmap 与 control-plane routing。

**Contract Surfaces:** Agent Skill routing、Learning Claim Markdown artifact、Agent Memory metadata、Harness changed-path policy。不存在新的 Product API、CLI、Manifest、Provider、P6 或 Final Acceptance surface。

**Invariants:**

- `Memory` 继续保存和检索发生过的 evidence；`Learning Claim` 只表达基于多个 exact sources 的当前、可撤销知识主张。
- 自动流程最多创建或更新 `pending_approval_status: PENDING_CONFIRMATION` 的 advisory candidate；不得因为候选生成、RAG 命中、technical PASS 或模型分数而自动采纳。
- 已adopted的active lane与新pending lane必须分离；pending/reject/failed apply不得覆盖或虚报仍在生效的active版本。
- 用户确认必须绑定只包含claim path的candidate checkpoint commit、该commit中exact file bytes SHA-256及sanitized actor/time/evidence pointer。确认后evidence、commit或candidate bytes变化必须重新确认。
- `active_adoption_status: ADOPTED`只在目标owner已实际修改且完成其mandatory verification后成立。
- Learning workflow不运行Provider、生成媒体、写Manifest / Registry / P6、自动retry、自动activation、自动Final Acceptance或自动push；确认前不得commit adoption target，唯一允许的是保存confirmation preimage的path-limited candidate checkpoint。
- `src/ai_video/**` Product Runtime 不得 import 或调用 Skill；Agent Memory 仍为 Development Governance-only advisory retrieval。

**Current / Target Behavior:** 当前 session record 与 RAG 能回答“过去发生了什么”，但没有跨实验 claim、counter-evidence、scope、确认与 adoption lineage 的 current owner。目标行为是在稳定 record 后由 Agent 自动执行 bounded distillation，record hook要求`recorded` ACK同时声明`no_candidate`或`pending_candidate`；满足 evidence threshold 时写入 `docs/record_for_agent/learning/<claim-id>.md` 的 pending lane，形成exact candidate checkpoint，并向用户展示commit、hash、evidence、scope、target与verification preview。用户 `Confirm / Revise / Reject` 后，Agent按claim contract继续；没有确认时不得修改adoption target。

**Compatibility:** 继续复用 `experience` corpus 和现有索引 layout，不新增 corpus shard或公开 CLI。普通 `docs/record_for_agent/*.md` 仍返回 `advisory_experience / experience_record`；只有 clean relative path 位于 `learning/` 子目录的 Markdown 返回新 metadata。现有 index freshness 与 detached refresh 语义保持不变。

**Out of Scope:** 自动 LLM daemon、Product Runtime caller、Q0 automatic Product caller、通用代码生成/patch engine、自动 Provider selection、自动 Gate mutation、历史 Qingyan/H3/T8 claim 的未经确认采纳、媒体或 paid/live execution。

**Acceptance Criteria:**

- `distill-ai-video-learning` 明确定义 candidate threshold、support/counter evidence、scope、qualitative evidence status、confirmation hash、adoption target、state transitions、supersession/reopen 与 fail-closed boundary。
- `record-ai-video-session` 对完成的 substantial durable record 自动调用 distillation evaluation；无合格 claim 时显式 `no_candidate`，不得制造 artifact。
- Learning candidate 对用户确认前始终为 pending `PENDING_CONFIRMATION / NOT_ADOPTED`，且active adopted lane保持不变；确认preview精确绑定candidate commit/hash、target paths、动作与verification。
- Session hook不接受缺少`learning_outcome=no_candidate|pending_candidate`的`recorded` ACK；`no_record`只接受`not_applicable`。
- Agent Memory loader、retrieval text/JSON metadata 和 tests 能区分 learning 与 historical experience，同时保持同一 `experience` scope。
- Harness 对新 Skill test 不再 fallback，并选择 focused Skill、Agent Memory、control-plane 与 architecture checks。
- Canonical docs如实声明 implemented governance behavior及未实现的 Product/Q1 automatic learning边界。

**Verification:** 先运行新 Skill、session hook、Agent Memory、Harness focused tests与 `python -m scripts.architecture_gate check`；然后对只包含task-owned paths的exact commit range运行 Harness verify，并用`verify-receipt`复核fresh receipt。不得运行Provider、媒体或网络验证。

## File Structure

- Create `.agents/skills/distill-ai-video-learning/SKILL.md`：唯一 learning distillation / confirmation / adoption-routing workflow owner。
- Create `.agents/skills/distill-ai-video-learning/templates/learning-claim.md`：Learning Claim current artifact contract。
- Create `tests/test_distill_ai_video_learning_skill.py`：Skill package、state、confirmation、authority与template contract tests。
- Modify `.agents/skills/record-ai-video-session/SKILL.md` 与 `scripts/session_record_hook.py`：stable record后自动handoff，并将learning outcome纳入ACK handshake。
- Modify `tests/test_record_ai_video_session_hook.py`：覆盖recorded ACK强制learning outcome与既有checkpoint语义。
- Modify `.agents/skills/retrieve-ai-video-memory/{SKILL.md,references/experience.md}`：解释 `advisory_learning` authority与精确 source reopen规则。
- Modify `src/ai_video/agent_memory/{corpus.py,retrieval.py}`：按 `learning/` relative path派生 metadata与human-readable authority label。
- Modify `tests/test_agent_memory.py`：覆盖普通 experience兼容与learning metadata / formatting。
- Modify `.agent/harness/policy.yaml`、`tests/test_agent_harness.py`：新增 focused Skill check与changed-path routing。
- Modify `AGENTS.md`、`.agent/context/control-plane-playbook.md`：durable routing summary与详细 automatic confirmation flow。
- Modify `docs/agent-primary-contract-matrix.md`：新增 Development Control Surface single owner与forbidden alternate paths。
- Modify `docs/v0.2-runtime-baseline.md`、`docs/v0.2-agentic-production-roadmap.md`：记录 governance layer已实现，但Q0 Product caller、Q1 recommendation与automatic Production adoption仍未实现。

## Major Milestones

### Milestone 1: Learning Claim And Confirmation Contract

**Files:**

- Create: `.agents/skills/distill-ai-video-learning/SKILL.md`
- Create: `.agents/skills/distill-ai-video-learning/templates/learning-claim.md`
- Create: `tests/test_distill_ai_video_learning_skill.py`
- Modify: `.agents/skills/record-ai-video-session/SKILL.md`
- Modify: `.agents/skills/record-ai-video-session/scripts/session_record_hook.py`
- Modify: `tests/test_record_ai_video_session_hook.py`

**Contract:** Distillation由Agent在stable record后自动运行，且recorded ACK必须携带evaluation outcome。只有至少两个independent attempts、一个包含多个arms的controlled comparison，或会materially support/counter/reopen既有claim的新evidence才可生成candidate。Candidate必须列出exact supporting/counter evidence、scope/exclusions、qualitative `evidence_status`、recommended action、adoption target和candidate commit/hash confirmation流程。

**Implementation Notes:** 使用单一 `Learning Claim` Markdown current owner，不引入数据库或background daemon；文件内部严格分离active与pending lane，candidate checkpoint commit保存immutable confirmation preimage。`CONFIRMED`不能替代目标owner verification，`ADOPTED`必须回填target path、commit和verification evidence。Session record Skill负责handoff，hook负责ACK outcome enforcement，不复制distillation state machine。

**Acceptance:** Skill contract能够产生`no_candidate`或一个pending candidate；确认前明确禁止修改target。`Revise`生成新checkpoint/hash并重新确认；`Reject`与target verification failure保留active claim不变；新反证可将pending claim置为`CONTESTED`或主动retire active。

**Verification:** `python -m pytest -p no:cacheprovider tests/test_distill_ai_video_learning_skill.py tests/test_record_ai_video_session_hook.py -q`

### Milestone 2: Authority-Separated Retrieval

**Files:**

- Modify: `src/ai_video/agent_memory/corpus.py`
- Modify: `src/ai_video/agent_memory/retrieval.py`
- Modify: `tests/test_agent_memory.py`
- Modify: `.agents/skills/retrieve-ai-video-memory/SKILL.md`
- Modify: `.agents/skills/retrieve-ai-video-memory/references/experience.md`

**Contract:** `docs/record_for_agent/learning/**/*.md` 继续由 `experience` scope检索，但metadata固定为 `authority=advisory_learning`、`document_kind=learning_claim`；其他record维持现状。Frontmatter不得覆盖canonical authority或document kind。

**Implementation Notes:** 只依据相对corpus root的clean path classification，不根据标题或正文猜测。Human-readable formatter必须提醒learning仍需reopen source、检查confirmation/adoption状态，且不构成执行授权。

**Acceptance:** Loader、index与retrieval测试证明learning可检索、ordinary experience兼容、frontmatter spoofing无效、authority label准确。

**Verification:** `python -m pytest -p no:cacheprovider tests/test_agent_memory.py -q`

### Milestone 3: Routing, Canonical Truth, And Exact-Snapshot Proof

**Files:**

- Modify: `.agent/harness/policy.yaml`
- Modify: `tests/test_agent_harness.py`
- Modify: `AGENTS.md`
- Modify: `.agent/context/control-plane-playbook.md`
- Modify: `docs/agent-primary-contract-matrix.md`
- Modify: `docs/v0.2-runtime-baseline.md`
- Modify: `docs/v0.2-agentic-production-roadmap.md`

**Contract:** Harness必须将新Skill及其test映射到focused check并保持always-selected safety checks。Canonical docs只能宣称Development Governance自动候选/人工确认闭环；不得宣称Q0 Product caller、Q1 automatic recommendation、Provider policy automation或Production adoption已实现。

**Implementation Notes:** `AGENTS.md`只增加thin routing和authority summary；详细trigger、preview、confirmation hash和state transition由playbook与Skill独占。Contract matrix记录single owner、invariants、forbidden alternate path与focused verification。

**Acceptance:** `agent_harness inspect`无fallback path，包括未来`docs/record_for_agent/learning/**`；docs、policy audit、architecture gate与focused suites通过。Final exact commit range产生fresh passing receipt，并确认task commit没有包含existing `.codex/config.toml`、staged H3 record、`artifacts/`或既有untracked spec/plan。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_distill_ai_video_learning_skill.py \
  tests/test_agent_memory.py \
  tests/test_agent_harness.py -q
python -m scripts.architecture_gate check
python scripts/agent_harness.py inspect --base-ref HEAD^ --head-ref HEAD
python scripts/agent_harness.py verify --base-ref HEAD^ --head-ref HEAD
```

最后对 `verify` 输出中记录的 exact receipt path 运行
`python scripts/agent_harness.py verify-receipt --receipt PATH`，不得复用历史 receipt。
