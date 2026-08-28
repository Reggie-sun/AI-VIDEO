# AI-VIDEO Caption Quality Gate Implementation Plan

## Status

Proposed implementation plan。本文固定 Caption Quality Gate 的目标架构、兼容边界、
milestones 与 verification contract；它不证明 Runtime 已实现，也不授权 Provider、媒体生成、
自动 repair、candidate activation、P6 PASS、Final Acceptance、push 或 release。

本计划基于 2026-08-28 当前 source/tests、
`docs/research/2026-08-28-caption-quality-gate-prior-art.md`、existing P4/P6 contracts、
Quality Gate architecture boundary 与 project-local Agent Memory advisory evidence 编写。
Current code/tests 始终优先于历史 plan、record 或 research。

## Goal

在 existing Universal Production QA 与 P6 lifecycle 内新增独立 `QaLayer.CAPTION`，使
captioned final media 必须取得绑定 exact `CaptionTrack`、`ResolvedTimeline`、active render
bytes、selected policy 与完整 cue coverage 的 requirement-level evidence，才能进入 existing
Domain Gate 与 `ProductionStateCommitter` Final Acceptance。

## Scope

- 新增 caption-specific policy、review context、requirement findings 与 deterministic adjudication；
- 将 `QaLayer.CAPTION` 接入 existing `ReviewRequest -> ReviewEvidence -> ReviewReceipt ->
  FinalAcceptanceReceipt` lifecycle；
- 保留 existing deterministic `CaptionTrack` / timeline / renderer validation，并把它们作为
  `SOURCE_INTEGRITY` 与 `TIMING_CONTRACT` 的 evidence source，而不是重复实现；
- 对 exact final media 建立 `RENDER_COMPLETENESS`、`LAYOUT_READABILITY`、
  `AUDIO_SEMANTIC_SYNC` 与 `UNINTENDED_TEXT` findings；
- 更新 Universal profile coverage，使新 profile 在 `has_captions=true` 时必须选择
  `QaLayer.CAPTION`；
- 迁移 canonical captioned Ecommerce/Base E2E evidence path，并证明 stale/replay/failure
  semantics；
- 同步 canonical docs 与 Harness routing。

## Contract Surfaces

- Public Python contracts：`QaLayer`、`QaPolicy`、`ReviewRequest`、`ReviewEvidence`、
  `ReviewReceipt`、`UniversalQaProfile`；
- Persistence：content-addressed QA policy/request/evidence/receipt artifacts 与 existing
  Manifest review pointers；
- State lifecycle：`ProductionStateCommitter.begin_review()`、`run_review_analysis()`、
  `record_review_receipt()`、`record_final_acceptance()`；
- Canonical media identity：active render SHA-256、timeline fingerprint、dependency graph revision、
  selected policy hash；
- Verification/control plane：`.agent/harness/policy.yaml`、contract matrix、runtime baseline、
  roadmap 与 exact-range Harness receipt。

## Invariants

- `CaptionTrack` 继续拥有 authored text、alignment、language、speaker 与 timing fingerprint；
- `ResolvedTimeline` 继续是唯一 frame/sample/order owner；Caption Gate 不创建第二条 timeline；
- selected renderer 继续只消费 resolved cues；OCR/ASR 或 final pixels 不得改写 canonical text；
- `UniversalHardCheck.AUDIO_CAPTION_BINDING` 继续负责 structural audio/caption binding，
  不升级为 final presentation verdict；
- `QaLayer.CAPTION` 是 existing Gate 1 / P6 lifecycle 内的 universal review layer，不是第三个
  top-level Gate，也不是新的 Manifest writer；
- durable receipt、freshness、repair invalidation 与 Final Acceptance 继续只属于
  `ProductionStateCommitter`；
- all-required `PASS` 才能通过；任一 required `FAIL` 阻断，任一 required
  `NOT_EVALUATED` fail closed 且保留 uncertainty semantics；
- human/evaluator evidence 不能覆盖 hash mismatch、stale identity、missing cue coverage 或
  out-of-bounds timing；
- Gate 不自动 retry、repair、activate、调用 Provider 或记录 Final Acceptance。

## Current / Target Behavior

### Current

```text
CaptionTrack
  -> composition._resolve_caption_cues()
  -> ResolvedTimeline.caption_cues
  -> HyperFrames source/materialization audit
  -> final render
  -> LAYOUT: caption_overflow + generic layout metrics
  -> P6 / Final Acceptance
```

Current structural owners 已验证 canonical bytes、track/audio/style identity、sample/frame bounds、
renderer source structure 与 timeline binding。Current `QaLayer.LAYOUT` 只判定
`caption_overflow_milli`、safe area、layer collision 与 transition boundary；它不能证明 final
pixels 中 cue 完整、文本一致、无双层字幕、与实际 audio 语义同步或 perceptual readability。

### Target

```text
CaptionTrack / registered style / source audio
  -> existing deterministic structural validation
  -> ResolvedTimeline.caption_cues
  -> selected renderer
  -> exact active render bytes
  -> P6 QaLayer.CAPTION requirement findings
  -> Universal Gate 1 coverage
  -> existing selected Domain Gate 2
  -> existing ProductionStateCommitter Final Acceptance
```

## Architecture Decision

### Selected: Independent `QaLayer.CAPTION` Inside Existing P6

新增 `QaLayer.CAPTION`，但不新增第二个 caption coordinator 或 lifecycle。Caption-specific
typed contracts 与 adjudication 由 cohesive module
`src/ai_video/production/caption_quality.py` 独占；
`review.py::adjudicate_review_evidence()` 仅进行 layer dispatch。

Rejected alternatives：

- 扩张 `QaLayer.LAYOUT`：会继续把 geometry 与 accuracy/sync/completeness 混成一个 verdict；
- 扩张 `AUDIO_CAPTION_BINDING`：hard check 没有 final-pixel/perceptual evidence，也不产生 durable
  caption receipt；
- 新建 Caption Gate coordinator/Manifest state：会形成 Gate 1 与 P6 之外的第二套 orchestration
  或 lifecycle owner；
- 让 OCR/ASR 直接签发 PASS：无法证明 complete coverage，也会把 analyzer 变成 Production
  verdict owner。

### Single Owner And Old-Path Retirement

Single caption-quality adjudication owner 是 `caption_quality.py`。

对 caption-aware policy：

- `QaLayer.CAPTION` 独占 caption text fidelity、cue completeness、caption-specific placement/
  readability、audio semantic sync 与 unintended text；
- `QaLayer.LAYOUT` 只保留 generic safe area、graphic/layer collision 与 transition boundary；
- `caption_overflow_milli` 不再能单独证明 caption quality，也不再是新 policy 的 caption verdict
  input；
- `AUDIO_CAPTION_BINDING PASS` 只证明 structural binding，不得作为 `CAPTION PASS` 的 alias。

Historical policy 未声明 caption policy 时，existing `LAYOUT` payload 与 verdict 保持原样，确保
既有 artifacts、receipts 与 Final Acceptance 能按原 contract reopen。

## Typed Caption Contract

### `CaptionQualityPolicy`

新增 `src/ai_video/production/caption_quality_contracts.py`，只定义无 lifecycle side effect 的
typed contracts，避免 `models.py` 与 adjudicator circular import。

`CaptionQualityPolicy` 必须绑定：

- `contract_version="caption-quality-policy/1"`；
- delivery profile identity，以及覆盖 current timeline 全部 caption tracks 的 ordered
  `CaptionTrackPolicy` tuple；每个 track policy 绑定 exact track ID、language tag 与该语言的
  line/reading/timing thresholds；
- `measurement_contract_version`；
- 六个 required requirement groups；
- policy-selected evaluator/tool identities 与每组允许的 `EvidenceStrength`；
- per-track line count、grapheme-per-line、reading-rate、cue-duration、audio-sync-offset 与
  caption-overflow limits；
- 哪些 groups 必须由 `EXPLICIT_EVALUATOR` 或 `HUMAN` 覆盖。

所有 numeric limits 都必须由 selected language/delivery policy 显式提供；不从 Netflix、BBC、
FCC 或单次项目经验推导 universal defaults。每个 strict-reopened `CaptionTrack` 必须恰好匹配一个
track policy；missing、duplicate、language mismatch 或 policy 中存在 timeline 未选中的 track 均
fail closed，不能用单一 `language_tag` 覆盖 mixed-language timeline。

### `CaptionReviewContext`

`ReviewRequest` 新增 optional `caption_context`。当 requested layers 包含 `CAPTION` 时，该字段
必须存在并绑定：

- exact caption policy hash 与 measurement contract version；
- ordered caption asset ID/SHA-256、track ID、timing fingerprint、style ID/hash；
- exact source audio track/asset identities；
- ordered canonical cue subject IDs；
- group-specific coverage domains：cue-window roster、audio/cue windows，以及覆盖
  `[0, total_frames)` × full output frame 的 whole-render temporal/spatial audit domain；
- approved non-caption text identities/regions，例如 exact `ResolvedCommercialGraphic` text；
- timeline fingerprint、render output SHA-256、dependency graph revision；
- full expected cue coverage manifest hash。

`caption_quality.py::build_caption_review_context()` 只从 strict-reopened current project、
Registry、active render 与 `ResolvedTimeline` 派生该 context；caller 不能提交 arbitrary MP4、
manual path、text、timing 或 cue roster。

Canonical cue subject ID 使用 caption track、segment、text、sample/frame bounds 与 style identity
的 canonical hash，避免不同 tracks 复用 `segment_id` 时发生碰撞。

### Requirement Findings

每份 caption evidence payload 使用 typed `CaptionRequirementFinding`，只允许以下 groups：

| Group | Required proof |
| --- | --- |
| `SOURCE_INTEGRITY` | authored text/language/speaker/script lineage 与 track/style identity current |
| `TIMING_CONTRACT` | cue bounds、duration、gap/overlap、frame/sample/audio projection 满足 selected policy |
| `RENDER_COMPLETENESS` | exact final media 覆盖全部 cue windows，无漏字、截断、错行、重复或 double burn |
| `LAYOUT_READABILITY` | actual frames 中 safe area、collision、glyph/font、contrast、line treatment 与 readable presentation 合格 |
| `AUDIO_SEMANTIC_SYNC` | actual dialogue/audio onset/offset、text coverage 与 speaker/context 合理 |
| `UNINTENDED_TEXT` | final pixels 中没有 canonical track 无法解释的模型内嵌或重复字幕 |

每个 finding 必须携带 `PASS | FAIL | NOT_EVALUATED`、typed reason code、对应 group 的 covered
cue/audio/render-domain subjects、raw evidence references 与 coverage status。禁止 aggregate score。
`UNINTENDED_TEXT` 不使用 cue roster 作为 completeness proof：它必须覆盖 whole-render audit domain，
并把 canonical captions、approved commercial/on-screen text 与 unexplained text 分开；任何未覆盖
时间/区域或无法分类的 text 都是 `NOT_EVALUATED`，已确认的 unexplained/duplicate subtitle 是 FAIL。

### Evidence Aggregation

`caption_quality.py::adjudicate_caption_review_evidence()` 执行以下固定规则：

1. 先验证 policy、context、render/timeline/graph identity 与 measurement contract；
2. 只接受 policy-authorized tool identity 和 allowed strength；
3. coverage 以 context 的 group-specific domain 为准，不能信任 analyzer 自报的
   `coverage_complete=true`；cue groups 必须覆盖 exact cue roster，`UNINTENDED_TEXT` 必须覆盖
   whole-render temporal/spatial domain；
4. 任一 current authorized `FAIL` 对对应 group 具有阻断优先级；
5. 没有 contradiction 且 allowed evidence 覆盖全部 required subjects 时，该 group 才可 PASS；
6. missing group、unsupported language/tool、low confidence、partial sampling、identity mismatch，
   或没有 direct FAIL 但 authorized PASS evidence 相互矛盾时返回 `NOT_EVALUATED`；
7. 六组全部 PASS 时 aggregate 才 PASS。

若同一 group 同时存在 current authorized FAIL 与 PASS，FAIL 优先；“evidence conflict 返回
NOT_EVALUATED”只适用于没有直接 FAIL、但多个 observations 无法形成一致 PASS 的情况。

`SOURCE_INTEGRITY` 与 `TIMING_CONTRACT` 可由 `MEASURED` / `RENDERER_BOUND` exact evidence
关闭；`RENDER_COMPLETENESS`、`LAYOUT_READABILITY`、`AUDIO_SEMANTIC_SYNC` 与
`UNINTENDED_TEXT` 必须满足 policy-selected final-media evaluator/human strength，renderer source
或“未发现问题”不能单独关闭。

### Canonical P6 Adapter And Gate Ordering

新增 private `_caption_quality_p6.py`，只复用 existing `ProductionStateCommitter` APIs。它提供两个
明确 seams：

- `run_caption_review_transaction(...)`：从 committer root reopen exact target，构造
  `ReviewRequest 2.1`，durably `begin_review()`，通过 existing one-use permit 调用一个
  preselected `CaptionQualityEvaluator`，构造/记录 `ReviewEvidence 2.1` 与
  `ReviewReceipt 2.1`；
- `reopen_current_caption_review_outcome(...)`：从 active Manifest pointer reopen receipt、request、
  caption context 与全部 evidence，验证 current state/freshness 后才返回
  `UniversalQaCheckOutcome`。

`CaptionReviewExecution` 必须显式携带 evaluator/tool identity 以及 attempt/request/evidence/review
IDs；没有 evaluator、tool 不在 selected policy、request outcome unknown 或 one-use permit 已消费时，
返回/传播 fail-closed outcome，不能生成 PASS 或 remint/retry。

Canonical Ecommerce ordering 固定为：

```text
reopen exact active render/timeline
  -> run or exact-replay P6 CAPTION review transaction
  -> Universal Gate 1
       CAPTION branch = internal strict-reopen adapter only
       other layers = existing injected ReviewLayerRunner
  -> Ecommerce Gate 2
  -> existing Final Acceptance
```

`run_ecommerce_ad_production()` 可增加 `caption_review_execution: CaptionReviewExecution | None`；
non-caption timeline 必须为 `None` 且不产生 caption effect，captioned v2 profile 缺失该 dependency
则在 Gate 2 前 `NOT_EVALUATED`。External `run_review_layer` 若收到 `QaLayer.CAPTION` 必须被视为
programming error；canonical closure 不调用该分支。Exact active CAPTION receipt 已存在且 current 时，
adapter zero-write reopen；存在 consumed/unknown attempt 时 STOP，不 blind retry。

### LAYOUT Compatibility Branch

`QaLayoutRules.caption_overflow_tolerance_milli` 在 historical `QaPolicy 2.0` 中继续是 LAYOUT owner。
对 caption-aware `QaPolicy 2.1`：

- legacy field 必须为 sentinel `0`，任何其他值在 policy validation 时拒绝；
- `review.py` 的 LAYOUT branch 明确忽略该 sentinel，不读取 caption measurements；
- actual caption overflow/readability limit 只来自 per-track `CaptionTrackPolicy`；
- tests 必须覆盖 legacy nonzero threshold 保持有效，以及 2.1 legacy/new divergent values 无法形成
  dual owner。

## Compatibility And Schema Strategy

### Artifact Versions

- `QaPolicy`、`ReviewRequest`、`ReviewEvidence`、`ReviewReceipt` 增加 additive `2.1` form；
- historical `2.0` artifacts 保持 byte-for-byte serialization 与 content hash；
- `caption_policy` / `caption_context` 在 absent 时必须从 historical serialization 省略；
- `CAPTION` layer、caption policy/context 只允许出现在 corresponding `2.1` artifacts；
- `ReviewReceiptPointer.layer` 与 `ReviewReceipt.layer` 的 allowed values 加入 `CAPTION`。

### Universal Profile Versions

`UniversalQaProfile` 增加 `profile_contract_version`：

- missing field 的 historical payload 按 `1` reopen，hash 与旧 validation semantics 不变；
- `UniversalQaProfile.create()` 只创建显式 version `2` profiles，禁止 silent legacy creation；
- version `2` 且 `has_captions=true` 时，必须同时包含
  `UniversalHardCheck.AUDIO_CAPTION_BINDING`、`QaLayer.LAYOUT` 与 `QaLayer.CAPTION`；
- selected `QaPolicy` 必须包含 matching caption policy 和 `CAPTION` required layer，否则在任何
  review effect 前返回 `NOT_EVALUATED`。

### Manifest And Container Versions

本 slice 显式引入 `ProductionManifest 2.15`，因为 `active_review_receipts`、`review_states`、
`FinalAcceptanceReceipt.required_review_receipts` 与 `RepairOutcomeReceipt.fresh_review_receipts`
都会 durable 承载新的 `layer="caption"`。不得让旧 `2.14` / artifact `2.0` schema 静默接纳新 enum。

- Manifest 2.0–2.14 strict reopen 与 bytes 保持不变，并明确拒绝 CAPTION pointers/states；
- selecting a caption-aware `QaPolicy 2.1` 通过 `ProductionStateCommitter` 显式升级到 Manifest 2.15；
  reader 不执行 migration；
- `FinalAcceptanceReceipt` 与 `RepairOutcomeReceipt` 增加 `2.1` form；只有 `2.1` 可引用 CAPTION
  receipt pointers；historical `2.0` forms 保持 byte/hash compatibility；
- `QaPolicy`、`ReviewRequest`、`ReviewEvidence`、`ReviewReceipt` 的 `2.1` 与 Manifest 2.15 一起
  形成 caption-aware persistence contract；
- all state modules that accept the current superset Manifest must explicitly accept 2.15；source-boundary
  等 exact-version checks 必须按 feature capability 改为 2.14-or-2.15，而不是散落 silent bypass；
- exact replay zero-write；rerender、caption/audio/timeline/policy mutation 使 old caption receipt、
  repair outcome 与 Final Acceptance stale。

Migration 只改变 current mutable Manifest revision/version，不重写任何 historical content-addressed
artifact。Rollback 不允许把含 CAPTION pointers 的 2.15 Manifest 降写为 2.14。

## File Map

### Create

- `src/ai_video/production/caption_quality_contracts.py`：policy、context identity、requirement group、
  finding/payload typed contracts；不导入 `models.py`，不执行 lifecycle/effects。
- `src/ai_video/production/caption_quality.py`：context build/validate、cue subject identity、evidence
  aggregation 与 deterministic caption verdict；不写 Manifest。
- `src/ai_video/production/_caption_quality_p6.py`：existing P6 的 private adapter；负责 durable
  request/one-use analyzer/receipt transaction，以及从 committer root strict-reopen current CAPTION
  receipt outcome；它不定义第二套 lifecycle 或 verdict。
- `src/ai_video/production/manifest_schema.py`：Manifest version/capability 的 single owner；2.15
  继承 2.14 capabilities 并新增 caption-aware P6 capability。
- `tests/test_production_caption_quality.py`：contract/adjudication/coverage/authority/failure-path tests。

### Modify — Runtime

- `src/ai_video/production/domain_acceptance.py`：additive `QaLayer.CAPTION`。
- `src/ai_video/production/models.py`：artifact `2.1` compatibility、caption policy/context fields、
  receipt/pointer layer support 与 validators/serializers。
- `src/ai_video/production/review.py`：对 `CAPTION` 委派到 single caption adjudicator；新 policy 的
  `LAYOUT` 不再消费 caption-specific verdict。
- `src/ai_video/production/_state_commit_review.py`：strict reopen caption context；CAPTION evidence
  使用 caption measurement contract，而不是 technical context version；保持 one-use intent、
  exact receipt、stale/replay 与 Final Acceptance ownership。
- `src/ai_video/production/_state_commit_repair.py`：RepairOutcomeReceipt 2.1 与 CAPTION fresh-review
  pointer version gate；不改变 repair authorization/invalidation owner。
- `src/ai_video/production/project.py`：CAPTION receipt reopen 必须同时 reopen/rehash exact
  ReviewRequest、caption context 与 evidence，并针对 current project/Registry/timeline 验证；missing
  或 tampered request 在 project load 与 Final Acceptance 前 fail closed。
- `src/ai_video/production/quality_gate_coordinator.py`：Universal profile version bridge 与 caption
  coverage requirement；不新增 coordinator。
- `src/ai_video/production/ecommerce_ad_coordinator.py`：canonical captioned final-media closure 内部
  拦截 `CAPTION` layer，通过 private P6 adapter 创建或 strict-reopen receipt；external
  `run_review_layer` 永远不能处理 CAPTION 或直接返回其 PASS。

### Modify — Manifest 2.15 Propagation

使用 `src/ai_video/production/manifest_schema.py` 作为 Manifest capability/version sets 的单一 owner，
并把下列当前硬编码 `2.14` acceptance sites 改为调用该 owner；只做 2.15 superset propagation，
不重构其 domain behavior：

- `src/ai_video/production/models.py`
- `src/ai_video/production/project.py`
- `src/ai_video/production/_lifecycle_schema.py`
- `src/ai_video/production/_state_commit_bootstrap.py`
- `src/ai_video/production/_state_commit_common.py`
- `src/ai_video/production/_state_commit_transaction.py`
- `src/ai_video/production/_state_commit_review.py`
- `src/ai_video/production/_state_commit_repair.py`
- `src/ai_video/production/_state_commit_recovery.py`
- `src/ai_video/production/_state_commit_recovery_attempts.py`
- `src/ai_video/production/_state_commit_dependency.py`
- `src/ai_video/production/_state_commit_render_lifecycle.py`
- `src/ai_video/production/_state_commit_voice_intent.py`
- `src/ai_video/production/_state_commit_voice_activation.py`
- `src/ai_video/production/_state_commit_image_intent.py`
- `src/ai_video/production/_state_commit_image_recovery.py`
- `src/ai_video/production/_state_commit_paid_provider.py`
- `src/ai_video/production/_state_commit_p0_qualification.py`
- `src/ai_video/production/_state_commit_video.py`
- `src/ai_video/production/_state_commit_video_commercial.py`
- `src/ai_video/production/_state_commit_video_continuity.py`
- `src/ai_video/production/_state_commit_video_source_boundary.py`
- `src/ai_video/production/_state_commit_commercial_source.py`
- `src/ai_video/production/_state_commit_commercial_source_recovery.py`
- `src/ai_video/production/_commercial_project_reader.py`
- `src/ai_video/production/_commercial_source_state.py`
- `src/ai_video/production/_image_project_reader.py`
- `src/ai_video/production/_video_project_reader.py`
- `src/ai_video/production/hyperframes.py`
- `src/ai_video/production/shot_continuity_source_operator.py`

`manifest_schema.py` 必须表达 named capabilities，例如 P6、P7、paid-provider、continuity、commercial
source、source-boundary 与 caption-aware P6；不得用 numeric/string comparison 猜 feature support。
Manifest 2.15 继承 2.14 的全部 capabilities，并新增 `caption_review_v1`。Architecture Gate/test 必须
禁止新的散落 literal-version sets。

### Modify — Tests And Fixtures

- `tests/test_production_models.py`
- `tests/test_production_review.py`
- `tests/test_production_quality_gate_coordinator.py`
- `tests/test_production_state_commit.py`
- `tests/test_production_state_recovery.py`
- `tests/test_production_project.py`
- `tests/test_production_state_commit_structure.py`
- `tests/test_production_composition.py`
- `tests/test_production_hyperframes.py`
- `tests/test_production_voice_captions_e2e.py`
- `tests/test_production_base_ai_comic_e2e.py`
- `tests/test_production_ecommerce_post_media_e2e.py`
- `tests/test_production_ecommerce_ad_coordinator.py`
- `tests/production_e2e_support.py`

### Modify — Control Plane

- `.agent/harness/policy.yaml`：精确映射全部四个新 source files 与新 test，消除 fallback paths：
  `caption_quality_contracts.py` -> `production_shared_contracts`；
  `caption_quality.py` -> `production_review`；
  `_caption_quality_p6.py` -> `production_review` + `production_state`；
  `manifest_schema.py` -> `production_shared_contracts` + `production_state`。
- `tests/test_agent_harness.py`：断言 new paths 的 category/check routing。
- `docs/agent-primary-contract-matrix.md`：新增 Caption Quality owner、forbidden bypass 与 focused
  verification；保持 Universal/Domain two-gate architecture。
- `docs/v0.2-runtime-baseline.md`：完成后记录 actual implemented behavior 与 evidence boundary。
- `docs/v0.2-agentic-production-roadmap.md`：更新 slice status、dependency 与未验证 empirical boundary。

Implementation 开始前必须重新检查这些 exact paths 的 dirty/live-writer ownership。当前
`.agent/harness/policy.yaml`、contract matrix、runtime baseline 与 roadmap 已有 unrelated
uncommitted edits；若届时仍为 same-file active ownership，必须按 repository rule 由用户决定
ownership/执行顺序，不能覆盖或自行合并。

## Major Milestones

### Milestone 1: Freeze Caption Contracts And Historical Compatibility

**Files:**

- Create: `src/ai_video/production/caption_quality_contracts.py`
- Modify: `src/ai_video/production/domain_acceptance.py`
- Modify: `src/ai_video/production/models.py`
- Test: `tests/test_production_models.py`
- Test: `tests/test_production_caption_quality.py`

**Contract:** 新增 `CAPTION` layer、caption policy/context/findings 与 P6 artifact `2.1` form；
`FinalAcceptanceReceipt` / `RepairOutcomeReceipt` 2.1 可承载 CAPTION pointers；historical `2.0`
JSON bytes、content hashes 与 accepted `QaLayer` behavior 不变。

**Acceptance:**

- old serialized policy/request/evidence/receipt round-trip bytes/hash unchanged；
- `2.0` artifact 明确拒绝 caption-only fields/layer；
- `2.1 CAPTION` artifact 缺 policy/context、duplicate group、unknown group、noncanonical cue roster 或
  mismatched contract version 时 fail closed；
- Caption policy 无法省略六个 required groups，也无法使用空 tool authority；
- mixed-language timeline 中每个 current track 恰好有一个 matching track policy；
- caption-aware policy 的 legacy layout overflow field 只能为 inert sentinel，无法与 per-track
  caption overflow limit 形成双 owner。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_models.py \
  tests/test_production_caption_quality.py -q
```

### Milestone 2: Implement Exact Caption Adjudication

**Files:**

- Create: `src/ai_video/production/caption_quality.py`
- Modify: `src/ai_video/production/review.py`
- Test: `tests/test_production_caption_quality.py`
- Test: `tests/test_production_review.py`

**Contract:** adjudicator 只消费 strict-typed, exact-bound raw evidence；不运行 OCR/ASR、不选择
evaluator、不修改 canonical captions、不产生 aggregate score。

**Acceptance:**

- all six groups with their exact group-specific coverage domains => PASS；
- one current FAIL => FAIL；
- missing/partial/unsupported/low-confidence/conflicting evidence => NOT_EVALUATED；
- stale/hash/timeline/policy/context mismatch => NOT_EVALUATED before content verdict；
- renderer-bound evidence 不能单独关闭 policy 要求 evaluator/human 的 groups；
- `UNINTENDED_TEXT` 的 cue coverage 即使完整，只要 whole-render temporal/spatial audit 不完整仍为
  NOT_EVALUATED；
- authorized FAIL 与 PASS 冲突时 FAIL；没有 direct FAIL 的 inconsistent observations 才为
  NOT_EVALUATED；
- new caption-aware `LAYOUT` 不因缺少 `caption_overflow_milli` 返回 NOT_EVALUATED，historical policy
  仍保持 current layout behavior。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_caption_quality.py \
  tests/test_production_review.py -q
```

### Milestone 3: Add A Committer-Backed Caption Review Adapter

**Files:**

- Create: `src/ai_video/production/_caption_quality_p6.py`
- Modify: `src/ai_video/production/_state_commit_review.py`
- Modify: `src/ai_video/production/_state_commit_repair.py`
- Modify: `src/ai_video/production/models.py`
- Modify: `src/ai_video/production/project.py`
- Test: `tests/test_production_state_commit.py`
- Test: `tests/test_production_state_recovery.py`
- Test: `tests/test_production_project.py`

**Contract:** CAPTION review 必须走 existing durable intent、one-use analysis permit、immutable evidence
and receipt、current-state reopen、freshness 与 Final Acceptance rollup。

**Acceptance:**

- `begin_review()` 在 analyzer effect 前持久化 exact request/context；
- `run_review_analysis()` unknown outcome 不 retry/remint；
- `record_review_receipt()` 以 caption context measurement version 验证 CAPTION evidence；
- canonical CAPTION outcome 只能由 private adapter strict-reopen current durable receipt；
- project reopen 与 Final Acceptance 必须 reopen/rehash request、caption context 与 evidence；
- strict reopen 必须重新调用 single caption adjudicator，并要求 recomputed verdict 与 stored receipt
  verdict 完全一致；envelope current 但 verdict forged/mismatched 仍 fail closed；
- missing/tampered request、context 或 evidence 即使 receipt envelope intact 也 fail closed；
- exact replay zero-write；different bytes/same identity conflict；
- caption/audio/style/timeline/render/policy mutation 使 old receipt stale；
- required CAPTION receipt missing、FAIL、NOT_EVALUATED 或 stale 时 Final Acceptance denied；
- CAPTION repair outcome 只接受 version-compatible fresh review pointers。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_project.py \
  tests/test_production_review.py -q
```

### Milestone 4: Migrate The Durable Container To Manifest 2.15

**Files:**

- Create: `src/ai_video/production/manifest_schema.py`
- Modify: all files listed under **Modify — Manifest 2.15 Propagation**
- Test: `tests/test_production_models.py`
- Test: `tests/test_production_project.py`
- Test: `tests/test_production_state_commit.py`
- Test: `tests/test_production_state_recovery.py`
- Test: `tests/test_production_state_commit_structure.py`

**Contract:** Manifest 2.15 is the first durable container version allowed to carry CAPTION policy,
review state/pointers, caption-aware RepairOutcomeReceipt 2.1 and FinalAcceptanceReceipt 2.1。All existing
2.14 capabilities remain available through named capability predicates。

**Acceptance:**

- Manifest 2.0–2.14 strict reopen bytes and behaviors remain unchanged and reject caption-only state；
- Manifest 2.14 即使还没有 CAPTION receipt/state，只要 `active_qa_policy` 指向 caption-aware
  `QaPolicy 2.1` 也必须被 standard reader 拒绝；
- selecting a non-caption policy preserves current Manifest version；selecting caption-aware policy performs
  one explicit atomic upgrade to 2.15；
- no reader, validator, renderer, Provider adapter or recovery path performs implicit migration；
- every current 2.14-capable operation accepts 2.15 through named capability checks；
- source-boundary/commercial/continuity/paid/image/voice/render/recovery paths retain their existing feature
  gates on 2.15；
- new literal-version sets outside `manifest_schema.py` fail Architecture Gate/structure tests；
- rollback never downwrites a 2.15 Manifest containing CAPTION evidence。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_models.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_state_commit_structure.py -q

python -m scripts.architecture_gate check
```

### Milestone 5: Make Caption Coverage Mandatory In New Universal Profiles

**Files:**

- Modify: `src/ai_video/production/quality_gate_coordinator.py`
- Test: `tests/test_production_quality_gate_coordinator.py`

**Contract:** newly created version 2 Universal profiles fail closed before review effects when captioned
media lacks structural binding, caption policy, CAPTION layer coverage or a current CAPTION outcome。

**Acceptance:**

- historical version 1 profile bytes/hash and validation remain reopenable；
- profile v2 + `has_captions=true` requires hard `AUDIO_CAPTION_BINDING` plus `LAYOUT` and `CAPTION`；
- policy missing caption configuration/layer => `QA_POLICY_COVERAGE_INCOMPLETE`；
- CAPTION `FAIL` / `NOT_EVALUATED` / stale / unknown outcome stops before Domain Gate；
- PASS only records `completed_review_layers` in memory and still cannot claim Final Acceptance。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_quality_gate_coordinator.py \
  tests/test_production_review.py -q
```

### Milestone 6: Close Canonical Captioned Production Paths

**Files:**

- Modify: `src/ai_video/production/ecommerce_ad_coordinator.py`
- Modify: `src/ai_video/production/_caption_quality_p6.py`
- Modify: `tests/production_e2e_support.py`
- Test: `tests/test_production_base_ai_comic_e2e.py`
- Test: `tests/test_production_ecommerce_post_media_e2e.py`
- Test: `tests/test_production_ecommerce_ad_coordinator.py`
- Test: `tests/test_production_voice_captions_e2e.py`
- Test: `tests/test_production_composition.py`
- Test: `tests/test_production_hyperframes.py`

**Contract:** canonical caller 必须从 committer reopen exact active render/timeline，先执行或
zero-write replay private CAPTION P6 transaction，再由 internal adapter strict-reopen current receipt；
caller-supplied arbitrary path、timeline、CAPTION Gate PASS 或 stale receipt 无法进入 Gate 1 completion、
Gate 2 或 Final Acceptance。

**Acceptance:**

- captioned Base AI Comic 与 Ecommerce no-Provider E2E 只有在 fresh CAPTION PASS 后完成；
- dropped cue、duplicate/unintended text、subtitle-without-audio 分别产生 FAIL；
- ambiguous/partial analyzer coverage 产生 NOT_EVALUATED；
- full cue-window coverage 但 whole-render audit domain 不完整时，`UNINTENDED_TEXT` 仍为
  NOT_EVALUATED；cue 间隙中的 duplicate text 必须 FAIL；
- same exact receipt replay zero effect；rerender 或 caption/audio/timeline change invalidates closure；
- no-caption timeline 不创建 CAPTION request/receipt，且不会被 caption policy误判；
- external `run_review_layer` 无法为 CAPTION 返回 PASS；missing/tampered request chain 不能被 active
  receipt pointer 绕过；
- Gate 2 与 Final Acceptance owner、ordering、exact target binding 不变。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py \
  tests/test_production_voice_captions_e2e.py \
  tests/test_production_base_ai_comic_e2e.py \
  tests/test_production_ecommerce_post_media_e2e.py \
  tests/test_production_ecommerce_ad_coordinator.py -q
```

### Milestone 7: Route, Document, Review, And Prove The Exact Snapshot

**Files:**

- Modify: `.agent/harness/policy.yaml`
- Modify: `tests/test_agent_harness.py`
- Modify: `docs/agent-primary-contract-matrix.md`
- Modify: `docs/v0.2-runtime-baseline.md`
- Modify: `docs/v0.2-agentic-production-roadmap.md`

**Contract:** changed-path routing、human-readable owner 与 runtime status 必须与 implemented code/tests
一致；research recommendation 不得被写成 media-quality proof。

**Acceptance:**

- Harness inspect 不再把 new caption source/test 归入 fallback；
- Harness inspect 对四个新 source files 分别返回上述 exact categories/check families；
- contract matrix 指向 single caption owner、old-path retirement 与 focused checks；
- baseline 只描述 executable behavior；roadmap 保留 empirical/human acceptance 边界；
- `reviewer_xhigh` 对 exact final diff 给出 `accept` 或所有 blocking issues 已按同 tier scoped re-review
  关闭；
- exact staged snapshot 与 immutable commit range 均取得 fresh passing receipt。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_caption_quality.py \
  tests/test_production_review.py \
  tests/test_production_quality_gate_coordinator.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_state_commit_structure.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py \
  tests/test_production_voice_captions_e2e.py \
  tests/test_production_base_ai_comic_e2e.py \
  tests/test_production_ecommerce_post_media_e2e.py \
  tests/test_production_ecommerce_ad_coordinator.py \
  tests/test_agent_harness.py -q

python -m scripts.architecture_gate check
```

Final Harness commands 必须根据完成时的 exact owned path set 由 policy inspection 重新确认；不能把
本计划中的预测 check list 当作 current receipt。

## Empirical Acceptance Boundary

Engineering tests 只证明 schema、identity、coverage、adjudication、state 与 fail-closed behavior。
在声明字幕 perceptual quality 前，另需用户授权的 local/no-Provider exact-media experiment，至少
包含以下 sealed cases：

- all-cues-correct control；
- one missing cue；
- duplicated/model-burned subtitle；
- subtitle present while required dialogue audio is absent；
- OCR/ASR unsupported or ambiguous case。

每个 case 必须绑定 exact MP4 SHA-256、timeline/caption policy/context identity，并给出六组
requirement-level verdict。Ambiguous case 的正确预期是 `NOT_EVALUATED`。该实验需要 human review
确认 actual readability/text classification；它不调用 paid Provider，不产生 automatic retry、repair、
activation 或 Final Acceptance。

## Rollback

- 回滚新 policy/profile selection 即可让新 production 停止要求 CAPTION，但不得删除或改写已经
  content-addressed 的 caption evidence/receipt；
- historical `2.0` artifacts 与 version 1 profiles 始终按旧 contract reopen；
- rollback 不得把 caption-aware Final Acceptance 重新解释为 layout-only acceptance；若 selected
  policy 改变，existing receipt freshness 必须失效并重新 review；
- 若 Manifest 2.15 capability propagation、Artifact 2.1 compatibility 或 historical reopen 不能同时
  成立，停止 implementation；不得回退到让 Manifest 2.14/Artifact 2.0 静默承载 CAPTION enum。

## Out Of Scope

- 新 OCR/ASR model、dependency、daemon、background watcher 或 automatic analyzer selection；
- 第二条 CaptionTrack/timeline、第二 renderer、renderer fallback 或 manual MP4 acceptance；
- 自动改字幕、自动 repair、blind retry、candidate activation 或 Final Acceptance；
- Provider、paid/cloud call、credential、media generation 或 benchmark；
- universal Chinese/English CPS/CPL defaults、translation quality model、market outcome prediction；
- Legacy `0.1.x` CLI、flat Manifest/artifact layout 或 public exit-code changes。

## Completion Evidence

Implementation 只有同时满足以下条件才可宣称完成：

- task-owned diff 只包含本计划列出的 accepted files，且未覆盖 concurrent/user work；
- old path retirement 与 unchanged contracts 有 executable assertions；
- focused tests、full policy-routed checks 与 Architecture Gate actual PASS；
- exact staged snapshot/commit range Harness receipt fresh、scope/policy/artifacts/snapshot 一致；
- independent `reviewer_xhigh` 无 blocking issue；
- session record 已按 `record-ai-video-session` 写入，并明确 `distill-ai-video-learning` 的
  `no_candidate | pending_candidate` outcome；
- 未执行的 real-media、human、Provider、push/release evidence 在 final delivery 中明确标注。
