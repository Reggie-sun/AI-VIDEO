# AI-VIDEO Post-QA Q0 Capture Specification

## Status

Accepted。本文是本 slice 的 accepted target contract，不是 runtime truth。Accepted 只表示 scope、
owner、边界与验收标准已收敛并获用户批准，不表示代码、tests、Manifest schema、Pilot dataset 或任何
quality/live 结论已经实现或已被验证。

本 Spec 不授权 Provider 调用、媒体生成、network/paid execution、RAG rebuild、Pilot GO、Q1/Q2、
automatic learning、automatic Provider selection、repair、activation、P6 verdict 或 Final Acceptance。

## Planning Base And Governing Documents

Planning 与 implementation base 均为已复核的 commit `d9dcdbe`。本 slice 在用户明确授权的独立
worktree 中从该 commit 开始，current code/tests 与 Harness policy 仍是 executable truth。

本 Spec 显式承接并受以下 canonical artifacts 约束，不重复抄写其内容：

- `docs/superpowers/specs/2026-08-21-ai-video-quality-experience-record-v1.md`：原始
  `QualityExperienceRecordV1` schema 1.0、四层 truth model、single Q0 owner、storage/hash 规则、P6 边界、
  privacy denylist 与 Q0
  phase boundary。
- `docs/superpowers/plans/2026-08-21-ai-video-quality-experience-record-v1.md`：Q0 minimum implementation
  的 change surface、fixture/acceptance matrix、rollback 与 Harness/commit boundary。
- `docs/superpowers/specs/2026-08-19-ai-video-shot-continuity.md`：provider-neutral continuity contract、
  `TerminalFrameEvidence`/`ContinuityReferenceBinding`、Bounded Hybrid Continuity Evaluator V1 的
  measurement/verdict contract 与 durable validation checkpoint。
- `docs/superpowers/plans/2026-08-19-ai-video-shot-continuity.md`：continuity milestone 顺序、
  Milestone 11 的 authorized surface 与 TDD/compatibility order。

冲突时优先级依次为：用户当前指令 > 当前 code/tests/runtime evidence > `AGENTS.md` 与
`docs/agent-primary-contract-matrix.md` > 上述 spec/plan > 本 Spec。

## Problem Boundary

当前仓库已存在 Q0 passive capture data plane（`src/ai_video/quality_intelligence/**`）与 Manifest 2.9
continuity evaluator checkpoint（`src/ai_video/production/_state_commit_video_continuity.py`）。两者之间
缺一段可信的衔接：

- Continuity-bound attempt 在 evidence checkpoint 之后立即 `adjudicate_generated_shot_continuity()`；
  verdict 非 PASS 时抛出 `REVIEW_EVIDENCE_INVALID`，流程停在 candidate preparation 之前。
- 因此 FAIL 路径不会持久化 fetched MP4 的 canonical artifact、`VideoProbeReceipt` 与
  `VideoProvenanceReceipt`；PASS 与 FAIL 的 durable evidence 不对称。
- `QualityExperienceRecordV1` 的 `ArtifactEvidenceKnown` 要求 exact `file_sha256`、measured geometry、
  `ffprobe_hash`、`video_probe_receipt_id`/`probe_receipt_hash` 与
  `provenance_receipt_id`/`provenance_receipt_hash`。缺少 durable receipts 时，FAIL attempt 只能被降级
  成没有 artifact evidence 的 record，或者由人手工拼装数值——后者正是本 slice 要淘汰的旧做法。
- 现状下也没有显式的 post-QA capture entry point：把 canonical runtime evidence 映射成一条 record 的
  组装逻辑散落在调用方，容易出现第二套 truth 与 privacy 泄漏面。

被替换的旧路径是：“先人工阅读 Manifest/receipt/analyzer 输出，再手写 record 字段”，以及“continuity
FAIL 只留下一条 typed error，不留可复核的 artifact/probe/provenance 证据”。

## Accepted Decision (Option A)

用户选择 Option A，授权一个 additive **Manifest 2.10 continuity capture checkpoint** 作为本 slice 的
prerequisite，使 continuity PASS 与 FAIL 两种结果在 adjudication 之前都已经拥有 durable、可 strict
reopen 的：

1. exact fetch artifact（既有 canonical fetched MP4 bytes 与 durable fetch pointer）；
2. `VideoProbeReceipt`；
3. `VideoProvenanceReceipt`；
4. evaluator intent 与 evaluator evidence（沿用现有 2.9 intent-before-effect / evidence-before-candidate
   语义）。

在该 checkpoint 完成后，`adjudicate_generated_shot_continuity()` 保持 **pure adjudication**：它只从已
durable 的 evidence 派生 verdict，不产生 durable write、不再触发 sampler/ONNX evaluator/human fallback、
也不改变 activation 结果。verdict 非 PASS 时仍然 fail closed，仍不得 activation。

在此之上，本 slice 增加一个**显式 post-QA capture API**：调用方在 QA 结论产生之后提交 exact
project root、attempt selector、dataset root 与 Q0-only context；capture 自己 strict reopen canonical
pointers，不接受 caller 预先拼好的 `QualityExperienceRecordV1`。

## Manifest 2.10 Continuity Capture Checkpoint

### Ordering And Single Writer

- `ProductionStateCommitter` 仍是唯一 durable writer、activation 与 recovery owner。capture checkpoint
  必须在同一 committer transaction boundary 内完成，不得新增第二 writer、第二 lifecycle 或 helper 直写。
- 固定顺序：`intent -> evaluator evidence -> capture checkpoint -> pure adjudication -> candidate
  preparation/activation`。capture checkpoint 之前不得 adjudicate；adjudication 之后不得再写 capture
  evidence。
- capture checkpoint 只 seal 已经存在的 exact bytes 与 measured metadata：held-FD fetched MP4、
  measured metadata、fetch receipt、evaluator intent/evidence。它不重新 fetch、不重新 probe、不重新
  extract、不重新运行 evaluator，也不调用 Provider、renderer、analyzer 或 human fallback。

### Additive Schema Rule

- Manifest schema 从 `2.9` additive 前进到 `2.10`：attempt 的 video generation state 增加 capture
  checkpoint phase 与 canonical、content-addressed pointers（fetch artifact、probe receipt、provenance
  receipt），pointer 必须绑定 evaluation fingerprint、artifact SHA-256 与 receipt content hash。
- 历史 Manifest `2.0`–`2.9` 必须保持可读、可 reopen、可 recovery；只有携带新 capture pointer 的 attempt
  才要求 `2.10`。`2.9` 不得偷带 `2.10` pointer，`2.10` 不得改写历史 pointer 语义或既有 receipt payload/
  hash。
- Registry schema、artifact layout public contract 与 Legacy Manifest/CLI 不变。历史
  `QualityExperienceRecordV1` schema `1.0` bytes/validation 保持兼容。

### Accepted Q0 Schema Amendment

首轮 independent review 证明 schema `1.0` 没有合法位置保存 continuity evaluator intent/evidence pointer；
复用 `p6_observations` 会把 continuity evidence 冒充 P6 lifecycle truth。用户因此明确授权 additive
schema `1.1`：新增独立 required `continuity_evidence` binding，保存 intent/evidence exact pointer、
evaluation fingerprint、artifact/generation/target/constraints/policy/profile/authority hashes 与 tagged human
fallback hash。Schema `1.0` 不得携带该字段，schema `1.1` 必须携带；P6 observations 继续只允许真实
Review/Repair/Final Acceptance receipt。

Schema `1.1` 同时允许 runtime lineage 使用既有 tagged evidence variant：capture 只能从 reopened
request/registry/runtime evidence 派生已知值；planning、routing、workflow、structured-intent、compiler 或 input
receipt payload 若未被本 attempt 持久化，必须保存为明确 `not_applicable`，不得接受 caller 编造的 hash、
identity 或 parameter projection。Schema `1.0` 的 legacy exact-string validation 与 canonical bytes 保持不变。

### PASS And FAIL Symmetry

- PASS：checkpoint 之后照旧进入 candidate preparation 与 activation；durable evidence 与今日一致，并额外
  拥有 capture pointer。
- FAIL（或任何非 PASS 的完整 evidence 结论）：checkpoint 已经持久化 fetch artifact、probe receipt、
  provenance receipt 与 evaluator intent/evidence；随后 adjudication 仍然 fail closed，attempt 不成为
  candidate、不进入 Registry activation、不进入 P3/P4。
- FAIL 路径持久化 evidence 不等于质量结论、不等于 candidate、不等于 activation，也不改变
  `ErrorCode` 语义与 retryability。

### Retry, Replay, Recovery

- exact retry/recovery 只能 reopen、rehash 与 re-adjudicate 已 durable 的 evidence；不得重复 sampler、
  ONNX evaluator、human fallback、probe、fetch 或 Manifest 重复写入。
- capture checkpoint 已写但后续阶段 crash 时，recovery 必须复用既有 checkpoint，不得重新生成第二份
  artifact/receipt identity，也不得删除完整 orphan evidence。
- tampered、wrong-request、wrong-policy、wrong-profile、wrong-artifact、stale 或 incomplete 的 pointer
  一律 fail closed。

## Post-QA Capture API

### Owner And Direction

- single capture owner 仍是 `ai_video.quality_intelligence`；`QualityExperienceStore` 仍是唯一
  dataset writer，且只写显式传入的 non-Production `pilot_dataset_root/quality-experience/v1/`。
- `src/ai_video/production/**` 与其他 Production runtime module **不得** import、调用或以任何方式依赖
  `ai_video.quality_intelligence`。依赖方向只允许 `capture caller -> quality_intelligence -> 已 reopen 的
  Production typed objects`。
- 没有 automatic product caller：committer、Provider adapter、Router、Planner、P6、recovery 与 CLI 都不得
  自动触发 capture。capture 只能由显式的、已获授权的 post-QA 调用发起。

### Explicit Post-QA Contract

- capture 是 post-QA：只有在该 attempt 的 QA 结论（continuity adjudication verdict，以及本次 capture
  protocol 要求的 analyzer evidence 与 human review 结论）已经产生之后才能调用。
- capture 只接受 caller 提供的 exact selector 与 strict/frozen Q0 advisory/analyzer/human context；runtime-owned
  planning/routing/provider/prompt/parameter/input projection 不属于 public request。它自己不 scan `latest`、
  不遍历 Production root、不调用 recovery、不 submit/fetch/analyze、不激活 asset、不改变 P6 state、不把
  record 写进 Manifest。
- 所有 Production 输入必须逐项 strict reopen 并 rehash 验证：Manifest revision/file hash、attempt 与
  generation identity、capture checkpoint pointer、probe/provenance receipt、evaluator evidence、artifact
  bytes SHA-256。任何 mismatch、stale、tamper、wrong-attempt、symlink escape 或 containment 违规必须
  typed fail closed，不得降级为 best-effort capture。
- capture 成功返回 `QualityRecordPointer`；record sealing 语义与 governing Q0 spec 一致：一个 exact
  attempt 一条 record，seal 一次，不回填、不覆盖、不修订。

### Outcome Mapping

capture 必须把 canonical runtime observation 映射成 schema `1.1`；outcome variants 保持不变，新增的
`continuity_evidence` 只承载 exact evaluator checkpoint binding：

| Runtime observation | Record outcome | Durability activation |
| --- | --- | --- |
| continuity PASS 且已 activation | `succeeded` / `activated` | `activated` |
| continuity PASS 且只到 candidate | `succeeded` / `candidate` | `candidate` |
| continuity FAIL，capture checkpoint 完整 | `succeeded` / `fetched` | `not_candidate` |

`succeeded` 只表示“Provider 产出了已 durable 的 exact artifact”，与 QA verdict、candidate、activation、
human `GO` 与 P6 PASS 全部不等价。continuity FAIL 的 record 必须在 human review 与 outcome boundary 中
明确表达“未成为 candidate、未 activation、未获质量接受”。

## Analyzer Evidence Rules

- 只有 analyzer evidence 完整时才允许写 record 的 `analyzer.state = "known"`：canonical Q0 measurement
  set（`audio_integrity`、`black_ratio`、`continuity_score`、`detail_score`、`freeze_ratio`、
  `scene_change_count`）必须齐全且按 schema 规定顺序，evidence item 按 `evidence_id` 排序且唯一。
- 每个 measurement 必须绑定 exact `evidence_id`/`evidence_hash`、tool name/version、measurement contract
  version、subject identity 与 span hash；`subject_id` 必须等于 artifact evidence 的 `asset_id`。Caller
  还必须提供 content-addressed `analysis/**` source-document pointer；capture 使用 no-follow containment
  strict reopen 文件 bytes，并要求文件反序列化后的 exact `AnalyzerEvidenceItem`、file SHA、artifact SHA、
  `source_document` 与 caller binding 全部一致。
- capture 不得自己运行 analyzer、不得补算缺失 measurement、不得用 evaluator 的 continuity measurement
  冒充 `video-analysis` measurement。缺任一项即 typed fail closed，而不是写 partial record。
- analyzer evidence 是 raw measurement，不是 verdict；record 中不得由 measurement 推导 PASS/GO。

## Human Fallback And Q0 Metadata Rules

- human fallback 是独立授权的 evidence source。automatic evidence 不完整本身不能 PASS；human 结论也不得
  被伪装成 model observation 或 analyzer measurement。
- record 的 `human_review` 只允许三种状态：`GO`、`NO_GO`、`NOT_REVIEWED`。reviewer 只记录
  pseudonymous ID/kind；rubric 必须绑定 exact ID/version/hash 与逐项 verdict。continuity FAIL 的
  attempt 仍可携带 `NO_GO` 或 `NOT_REVIEWED`，但 human `GO` 永远不得被映射为 `QaVerdict.PASS`、
  candidate、activation 或 Final Acceptance。
- 非 `NOT_REVIEWED` metadata 必须另带 canonical `reviews/**` no-follow document pointer；capture strict reopen
  exact file SHA，并要求反序列化 metadata、reviewer source spans、evaluation fingerprint 与 durable human
  fallback hash 全部一致。`captured_at` 不得冒充 `watched_at`。
- Q0-only metadata（`experiment_id`、`pilot_id`、purpose、hypothesis、capture actor、authorization
  boundary、intervention taxonomy/changed variables/unchanged controls/confounders/rationale、outcome
  boundary 的 allowed conclusions 与 forbidden extrapolations）必须由 caller 显式提供，并受 bounded
  free-text、NFC 与 redaction validator 约束。capture 不得从 runtime state、文件名、时间邻近、默认
  profile 或 RAG 结果推断这些字段。
- `canonical_runtime_boundary` 必须真实：Production Manifest attempt 使用 `production_manifest` 与
  canonical artifact boundary；lab-only attempt 使用独立 namespace 与 lab boundary，且不得进入 Pilot
  dataset index 或 4–8 Shots gate。

## P6 Pointer Rules

- record 只保存已存在 P6 receipt 的 exact kind/relative path/content hash/file hash，以及 capture 时观察到的
  freshness；不得嵌入 receipt payload、不得重算 policy verdict、不得复用 P6 `active_*` fields。
- 无 P6 receipt 时保持 `not_present` 且不得携带 pointer；有 pointer 时必须排序、唯一且可 strict reopen。
- `active_review_receipts`、current approved repair 与active Final Acceptance只有通过Production strict freshness
  reopen后才标记`fresh`；累积历史`repair_outcome_receipts`没有active owner，固定标记`stale`。Boundary仅在
  至少一个pointer为`fresh`时使用`present`，全为非fresh observation时使用`stale`。
- 不得从 Q0 human review、analyzer measurement 或 continuity verdict 反推 P6 receipt 或 Manifest state；
  也不得由 P6 pointer 推断 Final Acceptance。

## Privacy And Redaction

- 沿用 governing Q0 spec 的 denylist：raw prompt/negative prompt、raw Provider request/response、signed
  URL、HTTP header/cookie、credential 与 credential value/hash、absolute home path、browser session、chat
  transcript、reviewer PII 与大块 analyzer payload 一律拒绝。
- public capture 入口不得先接收 raw payload 再尝试清洗；被拒绝的内容不得进入 error message、`repr`、
  temporary artifact、fixture、Harness receipt 或 RAG projection。
- capture 只允许持久化 hash、identity、bounded typed taxonomy 与 bounded free text；secret 只允许 stable
  reference name 的 presence marker。

## Replay, Conflict, And Idempotence

- capture 对同一 `AttemptIdentityKey`：same canonical bytes 为 zero-write replay；same key + different
  bytes 为 typed conflict，不得覆盖或静默二次写入。
- 整个 capture 路径对 Production 必须是 zero side effect：Provider、renderer、analyzer、committer、
  recovery、activation 与 Agent Memory build/search 的 call count 均为 0，Production root 的 bytes 与
  mtime 不变。
- capture 失败必须 fail closed 并保持 dataset root 一致；不得留下 partial record、mutable `latest`
  pointer、background indexer 或数据库。

## Out Of Scope

- 非 continuity attempt 的 capture（例如纯 T2V、reference/semantic lane、image/voice attempt）。
- provider-failure capture（Provider submit/fetch failure、`outcome_unknown`）在本 slice 不实现 capture
  路径；相应 record variant 继续只由既有 Q0 surface 与未来独立 slice 覆盖。
- 任何 automatic product caller、CLI command、service、queue、database、background job 或新 dependency。
- 除已授权 schema `1.1` continuity binding 外的 Q0 record 字段/语义变更、Registry schema 变更、
  artifact layout public contract 变更、P6 lifecycle 变更、Router/Planner/ReadinessGate 行为变更。
- Pilot GO、4–8 Shots dataset 完成度声明、Q1/Q2、automatic learning/selection、RAG rebuild、live/paid
  Provider execution、媒体生成与 quality/Final Acceptance claim。

## Unchanged Contracts

- `ProductionStateCommitter` 继续独占 durable write、activation 与 recovery；`ProductionProject`、Asset
  Registry、Production Manifest ownership 不变。
- P5 继续独占 dependency/desired fingerprint/precise invalidation；`ResolvedTimeline` 继续独占 timing；
  HyperFrames 继续是 Production renderer。
- P6 继续独占 Review/Repair/Final Acceptance lifecycle 与 semantic verdict；continuity verdict 仍只由
  `adjudicate_generated_shot_continuity()` 派生。
- Planner、`ShotReadinessGate`、Router、Provider adapters 与 Paid Provider Gate 不读取 Q0、不因 capture
  改变行为。
- Legacy CLI/Manifest/layout、default no-network 与 local-first policy 不变。

## Acceptance Criteria

1. Manifest `2.10` capture checkpoint 在 continuity PASS 与 FAIL 两条路径上都持久化 exact fetch artifact、
   `VideoProbeReceipt`、`VideoProvenanceReceipt` 与 evaluator intent/evidence，并可 strict reopen。
2. adjudication 在 checkpoint 之后保持 pure：无 durable write、无 evaluator/sampler/human fallback 再执行；
   非 PASS 仍 fail closed 且不 activation。
3. 历史 Manifest `2.0`–`2.9` 与既有 receipt payload/hash 保持可读、可 recovery；只有携带新 pointer 的
   attempt 要求 `2.10`。
4. exact retry/replay/recovery 在 checkpoint 前后各 crash point 上都不重复 Provider/evaluator/probe/fetch
   side effect，也不产生第二份 artifact/receipt identity。
5. post-QA capture API 对 PASS 与 FAIL 各产出一条 strict-validating schema `1.1` record，独立
   continuity evidence 与 outcome/durability/artifact/analyzer/human/P6 bindings 一致；历史 schema `1.0`
   canonical bytes 与 validation 保持兼容。
6. capture 对 Production 为 zero side effect，只写显式 dataset root；传入 Production `state/`、`assets/`、
   `creative/`、Legacy `runs/` 或 Agent Memory index root 必须 fail closed。
7. analyzer 不完整、human 结论伪装 model observation、P6 pointer stale/tampered、privacy denylist 命中、
   wrong-attempt/wrong-generation pointer 与 same-key different-bytes conflict 全部有 typed 拒绝测试。
8. tests 证明 Production runtime 不 import `ai_video.quality_intelligence`，且不存在 automatic capture
   caller。
9. Harness 按真实 changed paths 路由 focused Production 与 Quality Intelligence tests 及 task
   Architecture Gate，并对 exact staged snapshot 生成 fresh passing receipt。

## Resolved Assumptions And Remaining Boundary

- FAIL record 使用 sealed request 已经确定的 `output_asset_id`；它只标识 fetched artifact subject，不宣称
  Registry registration、candidate 或 activation。
- PASS candidate path 复用 checkpointed probe/provenance receipts；FAIL 保留既有 canonical fetch bytes，
  不新增第二份 MP4 layout 或 Registry write。
- `pilot_dataset_root` 与 Q0 experiment/reviewer/rubric context 仍必须由 explicit caller 提供；本 Spec 不预批
  Pilot、dataset 完成度或 automatic product caller。
