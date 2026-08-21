# AI-VIDEO QualityExperienceRecord v1 Specification

## Status

Proposed docs-only contract。本文定义 `Q0 passive capture` 的数据边界，尚未实现
schema、validator、serializer、store、Pilot dataset、exact lookup 或 RAG projection。
它不授权 Provider execution、media generation、Agent Memory rebuild、Pilot GO、自动学习、
自动选参、automatic Provider selection、repair、activation、P6 verdict 或 Final Acceptance。

Planning base 是 local `main` commit `33beb13d5b8ae68ee109e41d2df7f186ea1f1b1b`。
该 commit 已包含 `7c22cae` 的 Quality Intelligence start gate 与后续 Local H3 Provider
family runtime change。本文只描述 proposed additive data contract；current code/tests/runtime
truth 仍以 repository 和 fresh execution evidence 为准。

## Decision

下一次获授权的 4–8 Shots、30–60 秒 Pilot 只有在本 Spec 对应的 minimum implementation
slice 完成后，才能把其 Shot generation attempts 作为 prospective Q0 dataset 采集。

每个 exact Shot generation attempt 产生一条 immutable、machine-readable
`QualityExperienceRecordV1`。失败、outcome unknown、repair 后的 retry 和任何新 generation
都产生新 attempt、新 record；不得覆盖、修订或把后来的 verdict 回填到旧 record。

Q0 只被动记录已经发生且可由 evidence 证明的 truth。它不向 Planner、
`ShotReadinessGate`、Router、Provider、Registry、Manifest、`ProductionStateCommitter`、P6、
`ResolvedTimeline`、HyperFrames 或 Final Acceptance 反馈决策。

## Problem Boundary

当前 canonical Production contracts 已能持久化 Project/Scene/Shot identity、generation
request/resolution、generated artifact、activation/recovery 与 P6 Review/Repair receipts；人类经验则
散落在 `docs/record_for_agent/`，由 local Agent Memory RAG 做 advisory semantic retrieval。
后者不提供 per-attempt exact lookup，也会因 corpus digest drift fail closed。

需要替换的旧实践是：下一次 Pilot 仍依赖“每 Shot 一篇 Markdown + 后续靠 RAG/人工搜索恢复
request、参数、artifact、measurement 和 verdict”。历史 Markdown 不删除、不改写，但它不再是
新 Pilot 的唯一或 primary per-attempt record。

## Four-Layer Truth Model

| Layer | Content | Authority and mutation rule |
| --- | --- | --- |
| Canonical runtime truth | `ProductionProject`、selected Manifest/Registry、generation request/resolved state、artifact/provenance、P6 receipts | 既有 owner 不变；Q0 只保存 exact pointer/hash，不复制 lifecycle，不写回 |
| Advisory structured experience | one immutable `QualityExperienceRecordV1` per exact attempt；immutable `PilotDatasetIndexV1` | exact comparison/audit source；不是 activation、QA 或 acceptance truth |
| Human-readable summary | `docs/record_for_agent/` 中引用 exact dataset/record hashes 的 curated experiment summary | 人类可读 advisory narrative；不得补造 machine fields |
| Derived retrieval | Agent Memory corpus/index 与由 exact records 生成的 sanitized projection | local derived access layer；可删除/rebuild，不能成为唯一 discovery path 或 handoff owner |

依赖方向固定为：

```text
canonical Production identities / receipts
  -> PilotCaptureCohortV1 -> PilotAttemptRosterV1
  -> QualityExperienceRecordV1
     -> PilotDatasetIndexV1 (exact roster closure)
        -> optional sanitized Markdown projection / human summary
           -> derived Agent Memory index
```

反向引用禁止。Production artifacts不引用Quality records；record不引用dataset index；cohort/roster只
保存strict-read时的Manifest observation identity与attempt projection，不复制active lifecycle owner；dataset
index不引用Markdown或RAG collection。这样不会形成lifecycle或content-hash cycle。

## Ownership And Storage

### Single owner

Future implementation 的 single writer 是 top-level advisory module
`ai_video.quality_intelligence.QualityExperienceStore`。它只拥有显式传入的
`pilot_dataset_root/quality-experience/v1/`，不属于 `ai_video.production`，也不获得
Production project root、Manifest、Registry、P6 receipt 或 activation 的 write authority。

`ProductionStateCommitter` 继续是唯一 Production writer。Quality store 只能通过既有 strict
readers 或 caller 提供的 reopened typed objects构造 references；它不得 scan `latest`、调用
recovery、submit/fetch/analyze、激活 asset、改变 P6 state，或把 Q0 record 加入 Manifest。

### Canonical layout

```text
<pilot_dataset_root>/quality-experience/v1/
  records/sha256/<first-two>/<file_sha256>.json
  cohorts/<pilot_id>/cohort.<file_sha256>.json
  rosters/<pilot_id>/roster.<file_sha256>.json
  datasets/<pilot_id>/index.<file_sha256>.json
  imports/sha256/<first-two>/<file_sha256>.json
```

`pilot_dataset_root` 必须是显式的 non-Production dataset root；不得位于 Production
`state/`、`assets/`、`creative/`、Legacy `runs/` 或 `.agent/memory/index/` 中。Q0 不新增数据库、
service、queue、mutable `latest` pointer 或 background indexer。

Writes 使用 create-exclusive/no-follow、file fsync、parent-directory fsync、canonical reopen
verification。相同 canonical bytes 的 replay 是 zero-write；同路径不同 bytes、symlink、absolute
path、`..`、tamper 或 incomplete file 均 fail closed。Rollback 不删除已完成 records。

Store使用`quality-experience/v1/store.lock`做cross-process exclusive serialization，不把lock-file
existence当durable truth。从strict-scan bounded `records/`、`AttemptIdentityKey` conflict check、record
promotion到canonical reopen必须全程持锁；same key + same canonical bytes是zero-write，same key +
different bytes是typed conflict。Record promotion完成后即使process crash，下一次scan仍能发现该
binding；不需要mutable identity pointer、startup recovery或数据库。

### Hashing

- JSON 使用 UTF-8、sorted keys、stable separators、NFC strings 与单个 trailing LF；禁止
  float NaN/Infinity 和 unordered map semantics。
- `content_hash` 是排除自身后的 semantic payload SHA-256。
- `file_sha256` 是包含已 sealed `content_hash` 的 final canonical bytes SHA-256，并决定 path。
- `QualityRecordPointer` 与 `PilotDatasetPointer` 同时保存 relative path、schema、
  `content_hash` 和 `file_sha256`；reader 必须逐项 reopen verify。

## QualityExperienceRecordV1

### Record identity and attempt rule

`record_kind = "prospective_q0_attempt"`，`schema_version = "1.0"`。一条 record 必须绑定：

- `experiment_id`、`pilot_id`、UTC `captured_at`、repository commit、purpose、hypothesis、
  capture actor 与 authorization boundary；
- exact project artifact ID/revision/content hash、selected Manifest revision/file hash、Registry
  revision/file hash、Scene ID/revision/content hash、Shot ID/revision/content hash；
- exact `generation_id` 与 Manifest `attempt_id`；lab-only attempt 必须使用独立 namespace、
  stable ID 和 `canonical_runtime_boundary = "lab_only"`，不得伪装成 Manifest attempt；
- `attempt_sequence`、`attempt_kind = initial | retry | repair | comparison`，以及 optional
  backward-only predecessor `QualityRecordPointer`。predecessor 仅表达实验 lineage，不授权 repair。

`AttemptIdentityKey`由`canonical_runtime_boundary + project_id + attempt_id + generation_id`确定；
`attempt_sequence`不是新lifecycle，由selected terminal Manifest中该attempt的canonical tuple order派生。
同一个key不得对应两个不同records。repair/retry必须有新`attempt_id`；旧record永不因新measurement、
human review或P6 receipt而变化。

Record只在该attempt的declared Q0 measurement + human-review protocol完成后seal一次。若required
evidence未完成，capture失败而不是先写partial prospective record；后来取得的新证据不能修改已sealed
record，也不能为同一attempt伪造第二条prospective record。

### Exact binding sections

| Section | Required exact binding |
| --- | --- |
| Planning | planning request content hash、plan hash、requirement hash、readiness request/result hash、`READY/BLOCKED` 和 exact check reason codes |
| Routing | Router semantic/audit decision hash、policy identity、Provider capabilities fingerprint、selected capability ID/fingerprint、provider-bound request hash |
| Provider | provider name/kind、execution/billing kind、profile ID/version/path/SHA-256、workflow ID/version/path/SHA-256（或 typed `not_applicable`）、model ID、adapter compiler ID/version/hash |
| Prompt | prompt SHA-256、negative-prompt SHA-256、structured intent hash、compiler identity；v1 禁止 raw prompt text |
| Parameters | requested/effective seed、effective output、duration/frame count/fps、steps/sampler/scheduler/audio mode，以及 canonical sorted provider parameters；requested/default/provider-selected state 必须显式 typed |
| Inputs | role、asset/artifact ID、revision（若 owner 有 revision）、content/file SHA-256、MIME、bytes、Registry identity、creation/provenance receipt identity |
| Continuity | `exact_terminal | reference | semantic | none`、terminal/keyframe/continuity-state content hashes、source/target Shot identity、first/last-frame bindings |
| Outcome | typed failure/succeeded/fetched/candidate/activated/outcome-unknown boundary、error code、retryability 与 observation timestamps |
| Artifact | canonical/lab boundary、clean relative path、asset ID、SHA-256、bytes、container/codec、width/height、fps fraction、duration、frame count、audio streams、exact `ffprobe`/`VideoProbeReceipt`和provenance receipt hashes |
| Durability | activation state、Manifest revision、strict reopen result、recovery observation、exact replay counters/result；unobserved state必须 typed，而非默认 success |
| Analyzer | selected `video-analysis` evidence IDs/hashes、tool name/version、measurement contract version、subject/span identity、black/freeze/scene/audio/detail/continuity measurements |
| Human review | pseudonymous reviewer ID/kind、rubric ID/version/hash、观看时点、per-item verdict/concerns、overall `GO | NO_GO | NOT_REVIEWED` |
| Intervention | failure taxonomy、changed variables、unchanged controls、confounders、rationale；无 intervention 时显式 `none` |
| Outcome boundary | exact artifact-level claim、P6 pointers/freshness observed（若存在）、allowed conclusions 与 forbidden extrapolations |

Named parameters、variables、controls、measurements 与 rubric items 使用 canonical unique keys；
validator拒绝 duplicate、unsorted、ambiguous free-form bool/status 和 field-level contradictions。

### Failure and incomplete evidence

Generation failure 仍必须形成 record。Failure variant 不伪造 artifact/probe/activation；它记录 exact
attempt、last durable phase、typed error/outcome boundary 和 human review是否 `NOT_REVIEWED`。
`outcome_unknown` 独立于 known failure，不能被序列化为 retryable success/failure。

Prospective Q0 required identity 不能是 unknown。某个 provider-specific field确实不适用时，使用
tagged `EvidenceValue = known | not_applicable`；未观测但本应存在则 record validation失败，不能用
`None` 静默通过。

## P6 And Acceptance Boundary

Q0 只引用已存在的 `ReviewRequestPointer`、`ReviewEvidencePointer`、`ReviewReceiptPointer`、
`ApprovedRepairReceiptPointer`、`RepairOutcomeReceiptPointer` 或
`FinalAcceptanceReceiptPointer` 的 exact path/content/file hashes，并记录 capture 时观察到的
freshness。它不嵌入 receipt payload、不重算 policy verdict、不复用 P6 `active_*` fields，也不把
human `GO` 映射为 `QaVerdict.PASS`。

`READY`、Provider submit/fetch success、artifact candidate、activation、human `GO`、P6 layer PASS
和 Final Acceptance 是互不等价的 fields。缺少 P6 receipt 时保持 `not_present`；不得从 Q0
human review反推 receipt或Manifest state。

## Prospective Cohort And Attempt Roster

Pilot开始前写immutable `PilotCaptureCohortV1`，绑定：

- `pilot_id`、purpose/hypothesis、authorization boundary、capture/rubric contract、repository commit；
- exact base `ManifestObservationV1`和4–8 logical Shot keys `(project_id, scene_id, shot_id)`；
- allowed attempt source。v1 Pilot dataset只允许`production_manifest`，不让Q0拥有lab execution ledger。

`ManifestObservationV1`不是Manifest copy或pointer：它保存observed relative path、project ID、revision、
file SHA-256、base attempt count和ordered attempt-ID sequence hash。Cohort creation必须从一次
strict-read的live Manifest生成；
不扫描history、不写Production root，也不声称该mutable Manifest永远保持相同bytes。

Attempt-ID sequence hash使用domain-separated canonical payload；terminal validation先要求
`base_count <= terminal_count`，再验证前`base_count`个IDs的exact ordered hash。

Pilot结束后，pure roster builder strict-read terminal Manifest，先验证project identity、revision前进和base
attempt-ID sequence仍是terminal sequence的exact prefix，再取terminal suffix中
`operation == "video_generation"`、
且request target属于cohort Shot keys的每个attempt。它reopen
`video_generation_state.request`取得exact target Shot与`generation_id`，按terminal Manifest tuple order
生成immutable `PilotAttemptRosterV1`。Roster绑定cohort pointer、terminal `ManifestObservationV1`和每个
`AttemptIdentityKey`，并拒绝wrong Shot、duplicate、missing request或ambiguous generation identity。

若cohort Shot在terminal closure中没有attempt，Pilot dataset不完整并fail closed。`lab_only` record仍可
用于独立exact experiment audit，但在有独立获批、immutable lab attempt roster owner之前，不得进入
`PilotDatasetIndexV1`或计算4–8 Shots gate。

## PilotDatasetIndexV1

`PilotDatasetIndexV1` 是 immutable、content-addressed aggregate，不是 mutable catalog。它必须：

- 绑定一个 `pilot_id`、dataset purpose、rubric identity、capture contract version、创建commit、exact
  `PilotCaptureCohortPointer`和`PilotAttemptRosterPointer`；
- 包含 4–8 个 distinct logical Shot keys `(project_id, scene_id, shot_id)`；每条record仍绑定该attempt
  exact project/Scene/Shot revisions与hashes。每个Shot至少一个record，可包含失败 + repair/new attempt，
  因此record count可以大于Shot count；
- 只纳入 strict-reopened `prospective_q0_attempt` records；historical imports不得算进4–8 Shots gate；
- record `AttemptIdentityKey`集合必须与roster exact相等；missing、extra、duplicate、wrong-Shot或
  wrong-generation records全部拒绝，因此失败attempt不能被漏掉后仍通过；
- 按 `(project, scene, shot, attempt_sequence, attempt_id, file_sha256)` canonical排序；
- 每个 entry 保存 record pointer以及exact lookup projection：experiment/pilot/project/Scene/Shot/
  attempt/generation、Provider/profile/capability/model、outcome、human verdict、coverage tags；
- reopen每个 record并验证 projected fields exact equality，禁止 index 自报第二套 truth；
- 声明覆盖的 shot classes、continuity/audio/composition cases和已知 confounders，但不声明
  training readiness、quality acceptance 或 Q1 promotion。

新增record或closed roster变化时写一个新的immutable index file；旧index保留。没有`latest` pointer。
`list_dataset_pointers(pilot_id)`只deterministically枚举`datasets/<pilot_id>/index.*.json`并strict-reopen；
caller随后携带exact `PilotDatasetPointer`。该typed discovery不依赖RAG。

## Exact Lookup Versus RAG

Exact lookup 只通过 content hash/path和 `PilotDatasetIndexV1` 的 typed fields完成：

- `load_record(pointer)`、`load_dataset(pointer)`；
- `get_by_record_sha256()`；
- in-memory exact filters for project/Scene/Shot/attempt/generation/Provider/profile/capability/model/
  outcome/verdict。

这些 APIs 不依赖 embeddings、score、Agent Memory index freshness或 Markdown。不存在 record hash
或 exact field match 时返回 typed not-found/ambiguous，不能退化为 semantic search。

RAG projection 是 deterministic、sanitized Markdown bytes，必须标记
`authority = advisory_experience`，并引用 dataset/record hashes。它只包含允许公开到 advisory
summary 的 structured fields，不包含 raw prompt、raw Provider response、signed URL、absolute local
path、credential、private reviewer identity或大块 analyzer payload。Projection 本身不写
`docs/record_for_agent/`、不调用 Agent Memory build/search；是否形成 curated human summary 和
何时 explicit rebuild 仍是独立 authoring action。

## Historical Markdown Migration

历史 `docs/record_for_agent/*.md` 保持原文件和authority。Migration只能生成独立
`HistoricalQualityExperienceImportV1`，存放于 `imports/`，不得生成 prospective record或修改历史
Markdown。

Historical import 使用 tagged：

```text
EvidenceValue<T> = known(value, source_document, source_span)
                 | unknown(reason)
                 | incomplete(known_fragment, missing_fields, source_span)
                 | not_applicable(reason)
```

只有 source text、linked immutable artifact或current verified receipt直接证明的字段可为 `known`。
不得从文件名、日期邻近、默认 profile、later runtime、RAG score或“看起来合理”反推 seed、attempt、
Provider、hash、verdict或参数。Imports可单独 exact lookup，但不得进入 Pilot index、Q0 completeness、
Q1 evidence count或自动 recommendation。

## Security And Privacy

v1 schema和serializer必须拒绝：raw credential、credential reference value、signed URL、HTTP headers、
cookies、complete raw Provider request/response、raw prompt/negative prompt、absolute home path、browser
session、chat transcript和不必要的 reviewer PII。只允许 stable secret reference name的 presence marker，
不得记录 secret value或hash。

所有purpose、hypothesis、rationale、concerns、confounders等free-form strings必须NFC、拒绝control
characters、受field-specific hard length cap，并通过同一个redaction validator拒绝URL、header、secret、
prompt/response envelope和private identity patterns。可表达中文不等于允许unbounded arbitrary text；
failure/variable/rubric keys优先使用bounded typed taxonomy。

Redaction validator仅是defense-in-depth；public constructors不得接收raw Provider/prompt/identity payload
后再尝试清洗，也不得把被拒内容写入error、repr或temporary artifact。

Provider task/file IDs只有在既有 canonical receipt允许 durable persistence时才通过 pointer间接引用；
Q0 不额外复制。Error、repr、fixture、projection与Harness receipt使用同一 redaction boundary。

## Phase Boundaries

### Q0 passive capture

Future minimum implementation slice只实现strict schema、validator、serializer/store、cohort/roster、
legacy import、Pilot index、exact lookup、sanitized projection和fake/no-network tests。它不改变任何
generation或acceptance decision。

### Q0 -> Q1 advisory

只有 start gate定义的代表性覆盖、可复现对照、complete/reopenable records、Provider-specific boundary
和 held-out review 均满足后，才另写 Spec。Q1只能返回 rationale与bounded options；不改 Planner、
Router、Manifest、Provider或P6 state。

### Q1 -> Q2 constrained local search

只有Q1独立回顾通过后，才可能另批 local/unmetered、白名单参数空间、resource budget和human GO。
Q2仍不得自动activation、创建第二Router/P6 owner或执行remote/paid submit。

Automatic Provider selection、automatic repair和Final Acceptance当前没有start date，也不在v1实现面。

## Unchanged Contracts

- `ProductionProject` 继续拥有 canonical Character/Scene/Shot；Manifest/Registry与
  `ProductionStateCommitter` ownership不变。
- Planner/requirement、`ShotReadinessGate`、Router exact selection与Provider adapters不读取Q0。
- P5继续独占 desired fingerprint/invalidation；`ResolvedTimeline`继续独占 timing。
- P6继续独占 Review/Repair/Final Acceptance lifecycle和semantic verdict。
- HyperFrames继续是current Production renderer；Q0 store/capture不发起渲染、probe或analyzer call，
  只消费当前task已授权流程产生并strict-reopened的existing evidence。
- Legacy CLI/Manifest/layout不变；不新增public CLI、database、service、dependency、training job、
  Provider fallback或remote/paid path。

## Acceptance Criteria For The Future Runtime Slice

1. Prospective success、failure、outcome-unknown和repair/new-attempt fixtures strict validate。
2. Records/indexes canonical serialize、content/file hash、no-follow reopen和zero-write replay可证明。
3. 4–8 distinct Shots、base/terminal Manifest-derived roster、multiple attempts per Shot、跨调用/并发
   same-attempt collision、missing/extra/duplicate/mismatched/foreign/historical record cases有tests。
4. Exact lookup在Agent Memory缺失或stale时仍完整工作；ambiguous/missing exact query fail closed。
5. Sanitized RAG projection包含source hashes/authority，且secret/raw prompt/response/URL/privacy denylist
   全部被拒绝。
6. Legacy imports只迁移evidence-backed fields，unknown/incomplete保持typed且不能进入Pilot index。
7. Tests证明Q0不写Production root、不调用Provider/analyzer/recovery/activation、不修改P6 state。
8. Harness为future source/tests路由focused Quality Intelligence tests和task Architecture Gate。
9. 只有上述implementation取得fresh passing exact-snapshot receipt后，下一次Pilot才可作为
   prospective Q0 dataset开始；本docs-only Spec不满足该gate。
