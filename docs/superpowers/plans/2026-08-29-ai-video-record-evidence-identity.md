# AI-VIDEO Record Evidence Identity Implementation Plan

## Status

Proposed。本 Plan 是对现有 Automatic Experience Learning / confirmation 闭环的最小 correctness
补强，不重新设计 `record_for_agent`，也不引入新的 Product subsystem。

本 Plan 只定义后续 implementation contract；当前编写任务不执行代码修改、不迁移历史 records、不调用
Provider、不生成媒体、不修改 Production state、不 commit/push。当前 working tree 中已有的
`.codex/config.toml`、staged H3 record、`artifacts/`、既有 untracked spec/plan 均不属于本 Plan
文件的 ownership。

## Goal

让 automatic distillation 按真实 evidence identity 判断独立支持与反证，而不是把 Markdown 文件数、RAG hit
数、section 数或 proof item 数误当成 independent experiment 数；同时继续保留
`docs/record_for_agent/` 作为 human-readable durable record。

目标关系为：

```text
session boundary
  -> trigger record evaluation
  -> record one or more evidence units
  -> distill by independence identity
  -> create or revise a Learning Claim candidate
  -> user confirmation
  -> existing adoption owner and verification
```

`Memory` 回答“过去发生了什么”；`Learning Claim` 回答“基于当前 exact evidence，现在知道了什么”。两者是
独立概念，但共享 Markdown corpus 和现有 `experience` retrieval scope，不建立第二套数据库或 Product truth。

## Problem Boundary

当前主要缺口是 **distillation identity**，不是 narrative Markdown 本身：

- 一个 session record 可以合理包含多个 attempts、controlled arms、failure observations 与 proof layers；文件边界
  不是实验边界。
- 同一 attempt、artifact 或 validation chain 会被 run summary、record、follow-up record 与多个 RAG chunks
  重复引用；document/hit count 不能证明 evidence independence。
- 当前 records 往往已经保留 artifact path、SHA、verdict 与具体观察，但缺少稳定、统一的
  `experiment_id`、`attempt_id`、`independence_key` 与 evidence relationship。
- 当前 supersession prose 能供人理解，但不能稳定区分“新 attempt”“同一 evidence 新 proof layer”“旧 conclusion
  被替代”与“只复用了输入”。
- `record_for_agent` 同时承载 media experiment、architecture implementation、recovery、research 与 provider
  comparison；这对 durable history 合理，但 automatic distillation 需要显式 eligibility/classification。

因此 single owner 是 `distill-ai-video-learning` 的 evidence admission/dedup contract；
`record-ai-video-session` 只负责 capture envelope 与触发，Agent Memory 只负责 advisory retrieval 和 metadata
projection，不得各自实现第二套 independence rules。

## Scope

### In Scope

- 为新建或实质更新的 empirical records 定义 opt-in、flat-frontmatter-compatible 的 record classification。
- 在 Markdown 内增加 compact `Evidence Index`，表达 evidence item、attempt/arm independence 与 proof relation。
- 让 `distill-ai-video-learning` 按 unique `independence_key` 计算 support/counter evidence，并明确三种 admission
  basis。
- 提供 Skill-local、read-only validator，检测 identity 缺失、重复计数、SHA/proof/verdict/relation 不一致。
- 让 Agent Memory 在保持 path-owned authority 的前提下返回少量 supplemental classification metadata。
- 补齐 focused tests、Harness routing 与 canonical Development Governance documentation。
- 采用 forward-only rollout；历史 records 继续可检索，只有进入新 claim/revision 时才按需补 identity。

### Out of Scope

- 把 Markdown 全量转换成 JSON、SQL、vector database 或新的 corpus shard。
- 一次性回填、拆分或重写全部 `docs/record_for_agent/*.md`。
- 强制一个 attempt 一个文件，或禁止一篇 record 包含 controlled comparison / multi-attempt sequence。
- 仅凭标题、正文关键词或文件类型推断 independence。
- 自动生成 Q0 records、增加 Q0 Product caller，或使 Q0 成为 ordinary record capture 的强依赖。
- 自动采纳 Skill / Provider Policy / Preflight / Contract / Gate。
- 修改 Manifest、Registry、P6、Final Acceptance、Provider lifecycle 或 media gate semantics。
- Provider、paid/live、network、媒体生成与 human quality acceptance。
- 改写当前 pending Learning Claim 或已存在的 H3/Qingyan/T8 evidence bytes；任何 candidate bytes 变化仍需重新确认。

## Contract Surfaces

| Surface | Owner | Planned change |
| --- | --- | --- |
| Session capture trigger | `record-ai-video-session` | 要求 eligible empirical record 提供 classification 与 Evidence Index；不拥有 dedup |
| Evidence admission and dedup | `distill-ai-video-learning` | 定义 evidence identity、independence counting、admission basis 与 relationship semantics |
| Claim artifact | Learning Claim Markdown template | 以 structured evidence rows引用 supporting/counter evidence，不按 document count |
| Deterministic validation | Skill-local validator | 只读解析 opted-in Markdown；fail closed 报告 malformed/ambiguous identity |
| Advisory retrieval | Agent Memory `experience` corpus | 投影 flat supplemental metadata；authority/document kind 仍由 clean path 派生 |
| Changed-path verification | Harness policy | 将 validator、Skill contract、retrieval metadata 与 docs 映射到 focused checks |

不存在新的 Product API、public CLI、schema migration、runtime database 或 production-state owner。

## Evidence Identity Contract

### Identity Levels

| Identity | Meaning | Counting rule |
| --- | --- | --- |
| `evidence_id` | 一个可追溯 proof item，例如 artifact observation、human verdict 或 analyzer result | 用于引用与 relation，不直接计 independent support |
| `independence_key` | 一个真实 attempt 或 controlled arm 的归因边界 | 同一 claim 中相同 key 最多计一次 independent support/counter unit |
| `experiment_id` | 一组共享 hypothesis、held constants 与 comparison intent 的实验 | 用于分组，不等于 support count |
| `attempt_id` | 一次 submit/execution/observation attempt | 与 runtime/input boundary共同组成 independence identity |
| `arm_id` | controlled comparison 内的 arm | 不适用时使用显式 `N/A`，不得用空值掩盖歧义 |
| Artifact SHA | exact measured/generated bytes | 绑定 proof；同 SHA 被多文档引用仍是同一 bytes evidence |

优先级：存在 Q0 `AttemptIdentityKey.identity_hash` 时使用 `q0:<identity_hash>`；否则使用由 record 明确提供的
stable `independence_key`。非 Q0 key 必须绑定 runtime/provider/model/workflow boundary、`experiment_id`、
`attempt_id`，并引用 request/result/artifact identity 中至少一个可验证锚点。不得由文件 path 或 chunk id 自动合成。

### Minimal Record Envelope

新建或实质更新且准备进入 distillation 的 empirical record 使用 flat scalar frontmatter：

```yaml
---
record_kind: media_experiment
topic_id: h3-conditioning-attribution
learning_eligibility: eligible
evidence_index_version: "1"
---
```

允许的 `record_kind` 初始集合保持 coarse：

- `media_experiment`
- `provider_comparison`
- `architecture_implementation`
- `recovery_incident`
- `research_note`
- `session_summary`

`learning_eligibility` 只允许 `eligible`、`ineligible`、`needs_identity`。Classification 只控制 automatic
distillation admission，不改变 record 的 durable history、RAG 可见性、authority 或 Product status。

Eligible record 的正文增加一个 `## Evidence Index` Markdown table。最小 columns：

| Column | Requirement |
| --- | --- |
| `evidence_id` | record 内唯一、稳定、可被 claim 引用 |
| `independence_key` | attempt/arm dedup key；相同 evidence chain 必须复用 |
| `experiment_id` / `attempt_id` / `arm_id` | 分组与尝试 identity；不适用必须写明原因 |
| `artifact_sha256` | exact bytes SHA，或 pre-artifact failure 的 typed sentinel 与原因 |
| `proof_layer` | `TECHNICAL`、`ANALYZER`、`HUMAN`、`PROVIDER_RECEIPT` 等明确 layer |
| `verdict` | `PASS`、`FAIL`、`NOT_EVALUATED`、`UNKNOWN` 或 domain-specific exact verdict |
| `failure_class` | typed class；没有 failure 时显式 `NONE` |
| `relation_kind` | `NEW_ATTEMPT`、`SAME_EVIDENCE_NEW_PROOF_LAYER`、`CONCLUSION_SUPERSEDED`、`INPUT_REUSE_ONLY` |
| `related_evidence_id` | relation target；没有 relation 时显式 `NONE` |
| `source` | repository-relative source或明确 external artifact pointer |

正文 narrative 仍负责 intent、held constants、observations、decision 与 nuance；Evidence Index 不复制整篇内容，
只提供可机器校验的 identity/relationship spine。

### Distillation Admission

Learning Claim candidate 必须声明以下一个 `admission_basis`：

1. `TWO_INDEPENDENT_ATTEMPTS`：supporting rows 至少包含两个 distinct `independence_key`；同 attempt 的多个
   documents、chunks、artifact versions或proof layers只计一次。
2. `CONTROLLED_MULTI_ARM`：一个明确 controlled comparison，至少两个 arms共享 hypothesis与held constants，且
   每个 arm 有 distinct identity；它是一个 comparison basis，不伪装成多场独立复现。
3. `MATERIAL_EXISTING_CLAIM_UPDATE`：新 evidence 实质 support、counter、narrow、reopen 或 supersede 既有 claim；
   必须引用 target claim、旧 evidence identity 与具体 delta，不要求虚构第二次 attempt。

Supporting 与 counter evidence 都按 `independence_key` 去重。技术 PASS 与后续 human FAIL 可以共存为同一
attempt 的不同 proof layers；它们不得被计成两次 independent evidence，也不得用后一个 verdict 擦除前一个
layer 的事实。

## Invariants

- Session boundary 只触发 record evaluation；experiment/topic boundary 才决定 evidence grouping。
- Markdown document、RAG hit、heading chunk、record link、artifact version与proof layer都不是 independence proxy。
- Agent Memory ranking/retrieval 不决定 evidence eligibility、support count、confidence、confirmation或adoption。
- `authority` 与 `document_kind` 继续由 clean relative path canonical classification 决定；frontmatter 不得 spoof。
- Legacy records 没有新 metadata 时仍可检索，默认不自动当作 eligible independent evidence。
- `needs_identity` 必须 fail closed：允许人工阅读，不得自动计入 threshold。
- Same bytes + same attempt + multiple records = one independence unit；input reuse 本身既不是支持也不是反证。
- Supersession 不删除历史 evidence；claim conclusion 与 evidence interpretation 的 lifecycle 分开表达。
- Learning Claim remains advisory and confirmation-gated；通过 validator 不等于 user confirmation 或 target adoption。
- Validator 只读、no-network、no index rebuild、no Provider/media/Production mutation。

## Current / Target Behavior

| Concern | Current behavior | Target behavior |
| --- | --- | --- |
| Record form | Human-readable、session/topic narrative，常含多 attempts | 保留 narrative；eligible records增加 compact identity index |
| Independence | Skill有文字阈值，但无 canonical machine-checkable dedup key | 唯一按 `independence_key` 计数 |
| Supersession | 主要依赖 prose | 用 typed relation区分 new attempt、new proof、conclusion supersession、input reuse |
| Corpus classification | learning path与ordinary experience已分权；record kinds混合 | 保留同 corpus，增加 supplemental `record_kind` / eligibility metadata |
| Retrieval hits | 一个 document可产生多个 section/chunk hits | hits仍可多条，但明确不得作为 evidence count |
| Q0 linkage | 严格 identity schema存在，但普通 records无自动 caller | Q0 hash可选优先锚点，不新增 Product caller |

## Compatibility And Migration

- Rollout 是 forward-only、opt-in。旧 record 无 frontmatter/Evidence Index 时维持
  `experience_record / advisory_experience` 与既有 retrieval behavior。
- 不批量修改历史 Qingyan/H3/T8 records。新 claim 或 existing claim revision 若依赖旧 record，只为被引用的
  exact evidence 补最小 identity，或标记 `needs_identity` 后停止 automatic admission。
- Frontmatter 保持 flat scalar，兼容现有 YAML-free parser；Evidence Index 使用 Markdown table承载多行结构，
  不向 corpus parser引入通用 YAML dependency。
- 当前 pending Learning Claim 的 candidate commit/hash/bytes 在本 initial slice 中保持不变。若后续把它迁移到
  新 evidence contract，必须产生新 candidate checkpoint并重新请求用户确认。
- Existing `experience` scope、index layout、chunk IDs、query behavior、detached refresh semantics与 public CLI
  保持不变。
- Validator只对声明 `evidence_index_version: "1"` 或 Learning Claim新 contract 的文档强制检查；不得因历史
  narrative records缺字段而使整个 corpus不可用。

## File Structure

### Create

- `.agents/skills/distill-ai-video-learning/scripts/validate_evidence_identity.py`：Skill-local read-only validator，
  解析 opted-in record/claim 的 flat frontmatter 与 Evidence Index。
- `tests/test_experience_evidence_identity.py`：identity、dedup、relation、legacy compatibility 与 validator CLI tests。

### Modify

- `.agents/skills/record-ai-video-session/SKILL.md`：新增 record classification、eligible record envelope 与
  session-vs-experiment boundary；明确它不计算 independence。
- `.agents/skills/distill-ai-video-learning/SKILL.md`：成为 admission basis、independence counting 与 relation 的
  canonical owner。
- `.agents/skills/distill-ai-video-learning/templates/learning-claim.md`：为 support/counter rows、
  `admission_basis` 与 identity assessment提供规范位置。
- `tests/test_distill_ai_video_learning_skill.py`：覆盖新 Skill/template contract与Skill package完整性。
- `src/ai_video/agent_memory/retrieval.py`：在 `Hit` 与 JSON/human-readable output中投影允许的 supplemental
  metadata，不改变 ranking或canonical authority。
- `tests/test_agent_memory.py`：覆盖 eligible/ineligible/legacy records、frontmatter spoof resistance与多 chunk
  不等于多 evidence的输出边界。
- `.agent/harness/policy.yaml`、`tests/test_agent_harness.py`：为新 validator/test和关联Skill路径增加 focused
  changed-path routing。
- `.agent/context/control-plane-playbook.md`：维护详细 evidence identity、dedup、migration与failure handling。
- `docs/agent-primary-contract-matrix.md`：记录 single owner、forbidden alternate counting paths 与 focused checks。
- `docs/v0.2-runtime-baseline.md`：只在 implementation验证后陈述现有 Development Governance behavior与未实现边界。

`AGENTS.md` 已有 Memory/Learning authority与routing anchor；本 slice默认不复制表结构或enum。只有 implementation
发现 durable invariant缺少唯一入口时，才允许做一个 thin pointer change，并必须同步去重审查。

## Major Milestones

### Milestone 1: Freeze Evidence Identity Contract With RED Tests

**Owned files:**

- `.agents/skills/record-ai-video-session/SKILL.md`
- `.agents/skills/distill-ai-video-learning/SKILL.md`
- `.agents/skills/distill-ai-video-learning/templates/learning-claim.md`
- `tests/test_distill_ai_video_learning_skill.py`
- `tests/test_experience_evidence_identity.py`

**Implementation contract:** 先用 inline temporary Markdown fixtures固定三类 admission basis、record envelope、Evidence
Index columns与typed relation。测试必须证明同一 attempt 在两个 records、三个 chunks和两个proof layers中仍只计
一次；controlled arms可作为一个 comparison basis；material existing-claim update显式引用旧claim与delta。

**Acceptance:** Missing/blank identity、duplicate `evidence_id`、unresolved relation、malformed SHA、eligible record缺
Evidence Index以及把document count当support count的fixture均失败；legacy ineligible record不失败。

**Focused verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_distill_ai_video_learning_skill.py \
  tests/test_experience_evidence_identity.py -q
```

### Milestone 2: Implement The Skill-Local Read-Only Validator

**Owned files:**

- `.agents/skills/distill-ai-video-learning/scripts/validate_evidence_identity.py`
- `tests/test_experience_evidence_identity.py`

**Implementation contract:** Validator只读取显式 paths，输出每个document的identity errors、distinct support/counter
keys与admission result；不得写回文件、刷新Agent Memory index或搜索Provider/runtime state。Parser只实现已冻结的
flat frontmatter和canonical Markdown table，不演化成general Markdown/YAML framework。

**Acceptance:** CLI对valid record/claim返回0；对ambiguous/malformed/duplicate counting返回non-zero与stable diagnostic；
相同 SHA 不同真实 attempts不会仅因bytes相同被错误合并，相同attempt的多proof items不会被重复计数；Q0 hash与
explicit non-Q0 key都可验证。

**Focused verification:**

```bash
python -m pytest -p no:cacheprovider tests/test_experience_evidence_identity.py -q
python .agents/skills/distill-ai-video-learning/scripts/validate_evidence_identity.py --help
```

### Milestone 3: Project Supplemental Metadata Without Changing Retrieval Authority

**Owned files:**

- `src/ai_video/agent_memory/retrieval.py`
- `tests/test_agent_memory.py`

**Implementation contract:** 复用 corpus loader已经保留的 flat frontmatter，只把 allowlisted
`record_kind`、`topic_id`、`learning_eligibility`、`evidence_index_version`投影到 `Hit` / JSON / human-readable
provenance。不得用这些字段改变 scoring、filtering、authority、document kind、refresh或index identity。

**Acceptance:** Legacy hit字段为缺省值且输出兼容；eligible record多chunks可以返回多hits，但每个hit明确携带相同
record metadata；恶意frontmatter不能覆盖canonical `authority` / `document_kind`；retrieval text不声称独立证据数。

**Focused verification:**

```bash
python -m pytest -p no:cacheprovider tests/test_agent_memory.py -q
```

### Milestone 4: Sync Control-Plane Ownership And Exact-Snapshot Verification

**Owned files:**

- `.agent/harness/policy.yaml`
- `tests/test_agent_harness.py`
- `.agent/context/control-plane-playbook.md`
- `docs/agent-primary-contract-matrix.md`
- `docs/v0.2-runtime-baseline.md`

**Implementation contract:** Harness把Skill validator与Agent Memory projection映射到focused checks；playbook独占详细
table/enums/migration recipe；contract matrix只保存owner/invariant/forbidden paths/checks；baseline在exact behavior
通过后才更新。不得在`AGENTS.md`、playbook、matrix与Skill复制四份完整catalog。

**Acceptance:** Harness inspection对所有task-owned paths无unmapped fallback；docs如实区分 historical Memory、advisory
Learning Claim、user confirmation与adoption target；Q0 caller、automatic adoption、Provider/Production status仍标为未实现。
Independent `reviewer_xhigh` 检查memory/retrieval、dedup与confirmation semantic risk，parent复核所有blocking claims后
才能进入final integration。

**Focused verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_distill_ai_video_learning_skill.py \
  tests/test_experience_evidence_identity.py \
  tests/test_agent_memory.py \
  tests/test_agent_harness.py -q
python -m scripts.docs_contract_gate check
python -m scripts.architecture_gate check
python scripts/agent_harness.py policy-audit
```

实现完成时，只 stage task-owned paths，并对 non-empty exact staged snapshot 或 exact commit range运行 Harness
`verify`，随后对新 receipt执行 `verify-receipt`。不得复用历史 receipt，也不得把当前 unrelated dirty/staged files
带入execution tree。

## Acceptance Criteria

- Automatic distillation只按unique `independence_key`计support/counter units，不按documents、links、chunks、proof
  layers或artifact versions计数。
- 一篇record可包含多个attempts/arms；每个unit均有稳定identity，record granularity不再决定learning granularity。
- Same attempt的technical PASS与human FAIL作为不同proof layers保留，既不相互擦除，也不算两次独立实验。
- Controlled comparison与multiple independent attempts在claim中明确区分，不夸大confidence。
- Existing claim被新evidence support/counter/narrow/reopen时，结构化区分conclusion supersession与same-evidence
  reinterpretation。
- Architecture、recovery、research和ordinary session records继续可检索，但不会因存在document而自动进入learning
  threshold。
- Old narrative records无需迁移即可继续RAG；被新claim引用但identity不足时fail closed为`needs_identity`。
- Agent Memory只展示allowlisted supplemental metadata，不改变authority、ranking、Product truth或authorization。
- Validator与tests能够稳定复现duplicate-evidence failure mode，且运行期间无写入、Provider、media或network side effect。
- Canonical docs只宣称Development Governance identity/dedup已实现，不宣称automatic Production learning/adoption。

## Rollback And Failure Handling

- 若 supplemental metadata projection造成compatibility regression，可先移除Hit投影；Skill-local identity contract与
  Markdown records仍可独立工作。
- 若validator无法无歧义解析某record，将其标记`needs_identity`并停止candidate admission；不得猜测或按document数
  fallback。
- 若existing pending/active claim无法映射新identity，保持原claim状态与bytes不变，创建revision proposal而不是原地
  改写已确认preimage。
- 因为没有数据库migration或Product state write，rollback只涉及task-owned code/docs；历史records和artifacts不删除。

## Execution Boundary

本 Plan 的自然停止点是：identity contract、validator、retrieval metadata、focused tests、canonical docs与exact-snapshot
Harness evidence全部完成，并通过一次与风险匹配的independent review。任何历史record backfill、现有claim revision、
Provider/media experiment或adoption target change都必须作为后续独立scope，由用户按当次exact target确认。
