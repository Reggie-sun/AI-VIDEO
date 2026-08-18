# AI-VIDEO P8 Generated Video Providers Implementation Plan

> Implementation remains under the repository's Native Codex lifecycle. 用户已授权在 local `main` 从 accepted Paid Provider Gate base 执行 P8 offline/default-no-network implementation；本授权不包含 live calls、真实付费提交、push 或 release。

**Status:** Offline P8 implementation accepted on local `main` on 2026-08-19。Provider core、Paid Gate、Fake、H3/Hailuo/Seedance offline adapters、durable recovery与candidate activation已进入local `main`；最终activation/recovery checkpoint为`a089eac`。Hailuo有三条live-success MP4，H3 live因余额不足`HTTP 402 / code 1008`未成功，Seedance未授权live。独立MP4 composition compatibility已由`1362687`验收。

**Goal:** 建立 provider-neutral、crash-resumable、cost-aware 的 Generated Video capability，以 deterministic fake 完成 default acceptance，并以 MiniMax Hailuo V1 证明真实 Cloud adapter不污染 Production domain。

**Architecture:** `video.py`定义 immutable request/capability/task/provenance与 Provider Protocol；`video_generation.py`只做 stepwise orchestration；`ProductionStateCommitter`继续独占 durable write/activation/recovery。MiniMax与 Fake都是明确 adapter，P5只消费 resolved-generation desired evidence与 artifact applied evidence，Registry只保存 immutable generated-video provenance。

**Tech Stack:** Python 3.11+、Pydantic v2 strict/frozen models、existing `httpx>=0.27`、stdlib canonical JSON/SHA-256、existing ffprobe/held-FD primitives、pytest fake transport/committed MP4 fixture。No new runtime dependency、no new CLI、default no network/secret/cost。

**Spec:** `docs/superpowers/specs/2026-08-17-ai-video-agentic-production-harness-p8-generated-video-providers.md`

## Global Constraints

- 本文件记录 implementation contract；实际 runtime authority来自用户当前明确授权，且不扩展到 live-call、真实付费提交、push 或 release。
- Runtime base已满足 accepted P6、accepted P7、accepted Base AI Comic E2E 与 standalone Paid Provider Gate commit `cc82a49`。
- Task 0固定 Paid Gate checkpoint `cc82a49` 与 post-P7.1 exact execution base `3890295`、accepted Manifest `2.6` / Registry `2.1`，并分配 `P8_MANIFEST_SCHEMA = "2.7"` / `P8_REGISTRY_SCHEMA = "2.2"`。
- 所有 accepted pre-P8 Manifest/Registry versions保持 readable，no downgrade。
- `ProductionStateCommitter`是唯一 Manifest/Project/Registry/Graph writer、activation与recovery owner。
- Provider、resolver、service、reader、registry loader、dependency resolver不得直接写 state。
- Shot选择 `visual_strategy`；Provider不得选择、修改或 fallback strategy。
- request input hash、generation ID、resolved generation hash、Gate-owned billable-effect identity与 artifact SHA-256必须分离；P8不得持久化第二份 provider task ID。
- Paid submit POST never retries solely because `AiVideoError.retryable=True`。
- `outcome_unknown` never auto-resubmits or remints a permit。
- Secret、Authorization header、cookie、account ID、signed URL与 raw Provider response不得持久化或出现在 logs/fixtures。
- Legacy CLI/config/Manifest v1/flat runs/default-local ComfyUI保持不变。
- P8 provider core不修改Composition/ResolvedTimeline/HyperFrames；独立generated-MP4 compatibility plan已由`1362687`完成验收，且不改变provider lifecycle ownership。
- Default `pytest`必须 zero external network、zero real MiniMax submit、zero charge。

---

## Problem Boundary

### Single owner

- Durable owner: `src/ai_video/production/state_commit.py::ProductionStateCommitter`。
- Pure provider domain owner: `src/ai_video/production/video.py`。
- Stepwise orchestration owner: `src/ai_video/production/video_generation.py`；它只能通过 committer public P8 methods改变 durable state。
- Hailuo V1 protocol owner: `src/ai_video/production/minimax_hailuo.py`。
- Generated-video desired/applied owner: P8 Manifest schema + existing P5 resolver；graph本身保持 immutable。

### Old path to replace

P5当前只能通过 synthetic generated visual `AssetRecord`证明 future seam。P8不删除兼容 fixture；仅 P8 Manifest operation或带显式 P8 provenance pointer的 candidate必须由 exact request、durable submit/task/status、validated MP4、provenance receipt、P8 Registry record与 succeeded P8 Manifest attempt共同证明。Pre-P8 P2/P5 generated-video record保持 legacy applied semantics，直到被显式 P8 candidate supersede。

### Unchanged contracts

- P2 active project仍只含 concrete registered references；不添加 unresolved placeholder AssetRecord。
- Active old Project/Registry/graph在新 generation candidate成功前保持有效。
- Registry不保存 task lifecycle；Graph不保存 Provider operational state。
- `ResolvedTimeline`仍是 timing owner；P8 core只交付 registered video asset。
- P6 review/final state只通过 P6-owned exact identity-staleness helper改变。

## Exact File Map

### Create

- `src/ai_video/production/video.py` — provider-neutral strict models、capabilities、identities、normalized failures、Protocol、injected resolver。
- `src/ai_video/production/video_generation.py` — stepwise start/submit/refresh/fetch/recover service；no direct state writes。
- `src/ai_video/production/video_fake.py` — deterministic scripted fake与 call counters。
- `src/ai_video/production/minimax_hailuo.py` — MiniMax Hailuo V1 typed profile、transport、mapping与response/error parser。
- `tests/video_provider_contract.py` — reusable contract assertions/fixtures，不以 `test_`命名，避免独立 collection。
- `tests/test_production_video.py` — request/capability/identity/resolver/provenance unit tests。
- `tests/test_production_video_fake.py` — fake scenarios与 shared contract suite。
- `tests/test_production_minimax_hailuo.py` — official V1 payload/status/fetch/error/secret tests with fake transport。
- `tests/test_production_video_state_recovery.py` — crash/restart/outcome-unknown/fetch-resume tests。
- `tests/test_production_generated_video_e2e.py` — default no-network Project→Asset/Graph activation acceptance。
- `tests/external/test_minimax_hailuo_live.py` — triple-gated single-generation smoke，default skipped。
- `tests/fixtures/generated_video/fake-video.mp4` — small committed deterministic fake output。

### Modify

- `src/ai_video/errors.py` — finite P8 public error codes。
- `src/ai_video/production/models.py` — versioned P8 Registry video metadata；P8 Manifest video attempt/pointer/state fields。
- `src/ai_video/production/paths.py` — canonical request/profile/status/provenance/video asset paths。
- `src/ai_video/production/registry.py` — P8 Registry no-follow measured video verification。
- `src/ai_video/production/project.py` — read-only reopen/verify exact succeeded P8 evidence。
- `src/ai_video/production/dependency.py` — generated-video resolved-generation desired fingerprint与 applied evidence；no task lifecycle/write。
- `src/ai_video/production/state_commit.py` — sole P8 writer/permit/task/status/fetch/candidate/activation/recovery methods。
- `src/ai_video/production/__init__.py` — reviewed provider-neutral exports only。
- `src/ai_video/ffmpeg_tools.py` — reuse/extract narrow normalized video probe result if existing helpers cannot provide exact measured fields；no second subprocess framework。
- `tests/conftest.py` — explicit live-test option and default skip guard。
- `tests/production_project_factory.py` — P8 Manifest/Registry fixtures。
- Existing P2/P2A/P5/P6/state commit/recovery tests — backward-compatibility and composition tests named in each task。
- `README.md`、`AGENTS.md`、`docs/agent-primary-contract-matrix.md`、`docs/v0.2-runtime-baseline.md`、`docs/v0.2-agentic-production-roadmap.md` — only after verified implementation; describe runtime truth, not planned claims。

### Do not modify

- `src/ai_video/cli.py`、`src/ai_video/config.py`、`src/ai_video/pipeline.py`、`src/ai_video/manifest.py`、Legacy layout/config fixtures。
- `src/ai_video/production/composition.py`、`hyperframes.py`、P3 timeline/render schema in this slice。
- P7-owned image module/tests except exact accepted shared integration changes required by Manifest composition review。
- `.workflow/**`、`runs/**`、real credentials或 generated live output。

---

### Task 0: Freeze the Accepted Base and Reconcile Shared Asset Generation Contract

**Dependencies:** accepted P6、accepted P7、accepted Base AI Comic E2E、accepted Paid Provider Gate `cc82a49`、explicit P8 implementation authorization。全部已满足。

**Files:**

- Read: `AGENTS.md`
- Read: `.agent/context/session-handoff.md` if present
- Read: `docs/v0.2-runtime-baseline.md`
- Read: `docs/v0.2-agentic-production-roadmap.md`
- Read: accepted P6/P7 plans and exact implementation commits
- Modify: this plan to record exact accepted Manifest/Registry bases、selected P8 versions与 shared symbols before code

**Change:** Paid Gate checkpoint为 `cc82a49`，exact execution base为 `3890295`；current Manifest/Registry bases为 `2.6` / `2.1`；selected next-compatible versions为 `P8_MANIFEST_SCHEMA = "2.7"` / `P8_REGISTRY_SCHEMA = "2.2"`。P8复用 `DurablePaidProviderSubmitPermit` 与 `PaidProviderSubmitReceipt.external_effect_id`，不得新增 P8-specific paid permit或第二份 external task identity。P7.1 concurrent changes由 `3890295` 独立拥有；P8不改写该 ownership。

**Verification:**

```bash
git status --short --branch
git log --oneline --decorate -15
git rev-list --left-right --count origin/main...HEAD
git worktree list --porcelain
rg -n "Literal\[.*2\.5|ImageAssetProvider|DurableImageSubmitPermit|Base AI Comic" src tests docs
```

Run accepted P7/P6 focused baseline exactly as recorded by those slices, plus:

```bash
python -m pytest tests/test_production_models.py tests/test_production_project.py \
  tests/test_production_state_commit.py tests/test_production_state_recovery.py \
  tests/test_production_dependency.py tests/test_production_selective_rebuild.py \
  tests/test_production_review.py tests/test_production_repair.py -q
```

**Acceptance criteria:** explainable Gate checkpoint `cc82a49` / execution base `3890295`；P6/P7/Base E2E/Paid Gate accepted；exact Manifest/Registry bases与两个 P8 next-compatible versions recorded；no overlapping P8 writer；concurrent P7.1 ownership preserved；no P8 file exists under a conflicting owner。Failure at any gate stops runtime edits。

---

### Task 1: Define Provider-Neutral Request, Capability, Identity and Failure Contracts

**Dependencies:** Task 0。

**Files:**

- Create: `src/ai_video/production/video.py`
- Create: `tests/test_production_video.py`
- Modify: `src/ai_video/errors.py`

**Interfaces produced:**

- `VideoGenerationMode`
- `VideoOutputRequirement`
- `VideoImageReferenceBinding`
- `ProviderProfilePointer`
- `VideoGenerationRequest.create(...)`
- `ResolvedVideoGenerationRequest`
- `VideoCapabilityVariant`
- `VideoProviderCapabilities`
- `VideoGenerationPreview`
- shared `PaidProviderCallPreview(operation="video_generation")` / `PaidProviderAuthorizationDecision`
- `VideoSubmission`
- `VideoTaskState`
- `VideoTaskObservation`
- `VideoFetchReceipt`
- existing type-check-only `DurablePaidProviderSubmitPermit` nominal interface；no P8-specific permit
- `VideoProviderFailure`
- `VideoProvider` Protocol
- `VideoProviderRegistry.resolve(name)`

**Change:** Implement strict/frozen/self-sealing models from the spec. `request_input_hash` seals caller intent before resolution and excludes `generation_id`、effective values与 authorization receipts；`resolved_generation_hash` / `desired_generation_fingerprint` binds `generation_id + request_input_hash + capability/profile version + exact effective settings + output slot`。Both exclude `attempt_id`、task ID、timestamps、secret与 artifact bytes；remote/metered authorization直接使用 shared Paid Provider Gate并绑定 resolved hash。Provider profile is a content-addressed pointer, not arbitrary options dict. Resolver is injected mapping only and has no automatic selection/fallback. P8 V1不提供 cancellation method。

Add bounded `ErrorCode` values: `VIDEO_REQUEST_INVALID`、`VIDEO_CAPABILITY_UNSUPPORTED`、`VIDEO_PROVIDER_FAILED`、`VIDEO_PROVIDER_OUTCOME_UNKNOWN`、`VIDEO_ARTIFACT_INVALID`。Budget/egress failures复用 existing `PAID_PROVIDER_BUDGET_REJECTED` / `PAID_PROVIDER_EGRESS_NOT_AUTHORIZED`。Detailed operation/certainty/retry safety stays in `VideoProviderFailure` rather than multiplying global codes。

**Tests:**

- request input hash changes for prompt/source/provider/profile/requested duration but not generation ID；
- capability/profile version or effective setting changes resolved generation hash without mutating request input hash；
- task ID/timestamp/artifact bytes do not affect request/resolved hashes；
- changed budget/egress receipt leaves request/resolved hashes stable but changes authorization/submission binding；local/unmetered authorization does not require fake Cloud receipts；
- same params + new generation ID preserves request input hash and creates new resolved/desired fingerprint；
- T2V rejects image bindings；generic capability variants bound I2V `first_frame`/`reference` roles and counts；
- no unrestricted provider options mapping；
- coupled capability variant rejects unsupported combination before Provider call；
- registry unknown/duplicate name fails closed；
- negative prompt/seed/FPS are capability-gated；
- failure encodes operation、certainty与 retry safety independently from generic `retryable`。

**Verification:**

```bash
python -m pytest tests/test_production_video.py tests/test_errors.py -q
```

**Acceptance criteria:** pure/no-I/O module；no MiniMax name in core model fields；identity roles are structurally distinct without value-inequality validators；zero new dependency。

---

### Task 2: Add Deterministic Fake Provider and Shared Contract Tests

**Dependencies:** Task 1。

**Files:**

- Create: `src/ai_video/production/video_fake.py`
- Create: `tests/video_provider_contract.py`
- Create: `tests/test_production_video_fake.py`
- Create: `tests/fixtures/generated_video/fake-video.mp4`

**Interfaces produced:**

- `ScriptedFakeVideoProvider`
- `FakeVideoScenario`
- `VideoProviderCallCounts`
- reusable `assert_video_provider_contract(provider_factory, capability_cases)` test helper

**Change:** Fake validates capabilities, requires the shared `DurablePaidProviderSubmitPermit` nominal interface for remote metered submit, and uses a test-only protocol double before Task 4 proves the real committer permit. It returns an ephemeral stable task ID；durable polling evidence只绑定 caller提供的 Gate submit receipt fingerprint。Fake exposes one observation per `get_status()`，writes committed fixture bytes to caller-owned sink and records exact submit/status/fetch calls. It never sleeps、reads env、opens network或 writes state；the test double is never exported to runtime code。

Generate the fixture once as a repository test asset; tests treat committed bytes as immutable and compare repeated SHA-256, not encoder-version reproducibility。Fixture must contain one MP4 video stream、no audio、24fps、non-zero duration。

**Tests:** success、submit rejected、submit unknown、queued/running、transient status failure、terminal failure、timeout sequence、fetch failure、tampered bytes、call-count exactness、two instances return identical fixture hash。

**Verification:**

```bash
python -m pytest tests/test_production_video.py tests/test_production_video_fake.py -q
```

**Acceptance criteria:** all core contract tests run offline against fake；no timing sleeps；default fake artifact is probeable；scenario does not bypass permit or capability validation。

---

### Task 3: Compose Versioned P8 Manifest and Registry Schemas Without Adding a Writer

**Dependencies:** Tasks 0-2。

**Files:**

- Modify: `src/ai_video/production/models.py`
- Modify: `src/ai_video/production/paths.py`
- Modify: `src/ai_video/production/project.py`
- Modify: `src/ai_video/production/registry.py`
- Modify: `tests/production_project_factory.py`
- Modify: `tests/test_production_models.py`
- Modify: `tests/test_production_project.py`
- Modify: `tests/test_production_registry.py`

**Interfaces produced:**

- `VideoAssetMetadata`
- `VideoRequestReceipt` and canonical pointer
- `VideoStatusReceipt` and canonical pointer
- `VideoGenerationAttemptState` embedded only in `operation="video_generation"`
- `P8_MANIFEST_SCHEMA` compatibility validators
- `P8_REGISTRY_SCHEMA` compatibility validators
- canonical `state/video-generation/**` and `assets/video/**` path helpers

**Change:** Add fixed-shape P8 attempt summary containing request pointer/hash、generation ID、phase、Gate submit receipt pointer/fingerprint、optional provider file locator、latest observation pointer、candidate video asset IDs and candidate graph identity。Exact opaque external task ID只存在 `PaidProviderSubmitReceipt.external_effect_id`；P8 Manifest不得复制。Mutable phase lives only in Manifest。Add P8 Registry measured `VideoAssetMetadata`; remote egress expands only to generated voice/video, and remote generated video requires cost/egress/provenance evidence。

Project reader reopens only exact Manifest-selected request/status/provenance/Registry evidence using containment/no-follow/hash checks；it never scans newest files、recovers、creates directories or contacts Provider。

**Tests:**

- all accepted pre-P8 Manifest fixtures remain readable/serialization-compatible；
- explicit P8 fields rejected before `P8_MANIFEST_SCHEMA`；
- P8 video fields rejected for non-video operations；
- valid opaque task/file IDs exact round-trip；oversize/invalid structure fail closed；display redaction never changes durable ID；
- all accepted pre-P8 Registry versions unchanged；`P8_REGISTRY_SCHEMA` generated video requires video metadata；
- remote non-generated video remains invalid；
- path traversal/symlink/tamper/profile/request/status/provenance mismatches fail closed；
- no secret/raw response/signed URL fields are schema-accepted。

**Verification:**

```bash
python -m pytest tests/test_production_models.py tests/test_production_registry.py \
  tests/test_production_project.py tests/test_production_validation.py -q
```

**Acceptance criteria:** schema changes are backward-readable and version-gated；reader remains no-write/no-network；no placeholder asset or task lifecycle enters Registry/Graph。

---

### Task 4: Implement Durable Submit, Poll, Fetch and Recovery Lifecycle

**Dependencies:** Tasks 1-3。

**Files:**

- Create: `src/ai_video/production/video_generation.py`
- Create: `tests/test_production_video_state_recovery.py`
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `tests/test_production_state_commit.py`
- Modify: `tests/test_production_state_recovery.py`
- Modify: `tests/helpers/p2a_crash_worker.py`

**Interfaces produced:**

- reuse existing private `_DurablePaidProviderSubmitPermit` with `operation="video_generation"`；no second permit class
- `ProductionStateCommitter.begin_video_generation()`
- `record_video_submit_intent()`
- `record_video_submission()`
- `record_video_status_observation()`
- `record_video_provider_failure()`
- `prepare_video_fetch_sink()` / committer-owned held-FD fetch boundary
- `VideoGenerationService.start()`、`.submit_once()`、`.refresh_once()`、`.fetch_and_activate()`、`.resume_next_action()`

**Change:** Persist R+1 video request/profile before Gate submit intent。Gate persists preview/authorization/reservation and mints one existing paid permit only after exact Manifest replace is reopened and verified。Consume permit atomically at Provider submit boundary，then immediately persist the sole `PaidProviderSubmitReceipt` containing task ID。Every later service operation reopens that exact receipt and cannot call submit path。Restart with an existing unresolved `submit_intent` follows Gate recovery to `outcome_unknown` and never remints。

`refresh_once()` makes one status call and persists normalized observation；deadline produces resumable timeout with task identity retained。`fetch_and_activate()` is allowed only for durable succeeded observation. Recovery never calls Provider、never remints permit、never converts outcome unknown to failed/safe automatically。

**Crash matrix:** before/after request replace；before/after submit-intent replace；before/after permit consumption；after Provider accepted before handle persist；after handle replace；before/after each status receipt；during download；after validated bytes；candidate snapshot promotion；final Manifest replace and reopen。

**Tests:**

- all invalid authorization/capability gates call submit 0 times；
- permit wrong/stale/copied/serialized/reused rejected；
- process crash after consumed submit intent becomes outcome_unknown and call count stays1；
- durable task restart polls same ID；
- transient poll error never submits；
- timeout remains resumable；
- completed + download failure retries fetch only；
- exact replay after activation does zero provider/fetch/write；
- pre-existing P2A/P3/P4/P5/P6 recovery tests remain green。

**Verification:**

```bash
python -m pytest tests/test_production_video_fake.py \
  tests/test_production_state_commit.py tests/test_production_state_recovery.py \
  tests/test_production_video_state_recovery.py -q
```

**Acceptance criteria:** no black-box wait/generate API is required；every external action has a prior durable identity；post-submit ambiguity cannot produce a second POST；writer ownership remains singular。

---

### Task 5: Validate MP4, Register Immutable Provenance and Integrate P5 Freshness

**Dependencies:** Tasks 3-4。

**Files:**

- Modify: `src/ai_video/ffmpeg_tools.py`
- Modify: `src/ai_video/production/video.py`
- Modify: `src/ai_video/production/registry.py`
- Modify: `src/ai_video/production/dependency.py`
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `tests/test_ffmpeg_tools.py`
- Create or modify: `tests/test_production_video.py`
- Modify: `tests/test_production_dependency.py`
- Modify: `tests/test_production_selective_rebuild.py`
- Modify: `tests/test_production_state_commit.py`

**Interfaces produced:**

- `MeasuredVideoMetadata`
- `probe_generated_video_candidate(held_fd, expected_request)`
- `VideoProvenanceReceipt.create(...)`
- `build_generated_video_asset_record(...)`
- `resolved_video_generation_fingerprint(resolved_request)`
- generated-video applied-evidence verifier
- `ProductionStateCommitter.prepare_video_activation_candidate()` / final activate path

**Change:** Reuse existing ffprobe subprocess boundary and held-FD validation. Require bounded non-zero regular MP4、exactly one readable video stream、measured width/height/FPS rational/duration/frame/audio evidence and exact SHA-256. Audio presence必须符合 resolved capability的 native-audio policy；Fake与 Hailuo V1声明 `no_audio`，future native-audio Provider无需修改 core。Provider claims cannot override measured values。

Persist stable request/profile/result/probe/cost/egress/provenance receipts, append one P8 Registry VIDEO/GENERATED record, prepare exact target Project/Registry/graph candidate, reopen all evidence, then switch exact pointers/lifecycle in one final Manifest replace。

Extend P5 pure inputs so P8 generated-video desired fingerprint consumes `resolved_generation_hash`，not output bytes。Artifact SHA remains applied evidence。Status/poll/cost-only changes do not stale composition；new generation ID changes exact visual asset downstream only。Pre-P8 P2/P5 records retain legacy applied semantics until an explicit P8 candidate supersedes them。

**Tests:**

- empty/non-MP4/multi-video/oversize/unreadable/tampered files rejected；audio is accepted or rejected strictly by resolved native-audio policy；
- claimed vs measured duration/resolution/FPS mismatch rejected；
- Registry append-only prefix and canonical path enforced；
- request/profile/task/provenance/content hash agree end-to-end；
- changed prompt/source/profile/effective settings/generation ID changes desired；changed task ID/poll count/cost does not；
- artifact bytes are applied evidence and not request identity；
- unrelated image/voice/caption nodes stay fresh；
- same-desired failure not selected for automatic rebuild；
- P6 review state stales only through P6 helper after relevant final activation。

**Verification:**

```bash
python -m pytest tests/test_ffmpeg_tools.py tests/test_production_video.py \
  tests/test_production_registry.py tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py tests/test_production_state_commit.py -q
```

**Acceptance criteria:** downloaded bytes are not success until local measured validation passes；Registry/graph remain immutable；one final Manifest replace is the activation commit point。

---

### Task 6: Implement MiniMax Hailuo V1 Adapter Against Current Official Contract

**Dependencies:** Tasks 1-5；fresh official documentation/pricing review on execution date。

**Files:**

- Create: `src/ai_video/production/minimax_hailuo.py`
- Create: `tests/test_production_minimax_hailuo.py`
- Modify: `tests/video_provider_contract.py` only if adapter-neutral cases were missing

**Interfaces produced:**

- dated `MINIMAX_HAILUO_V1_COMPATIBILITY`
- `MiniMaxHailuoProfile`
- `MiniMaxHailuoPolicy`
- `MiniMaxHailuoTransportRequest/Response`
- `MiniMaxHailuoTransport` Protocol and bounded `HttpxMiniMaxHailuoTransport`
- `MiniMaxHailuoProvider`

**Change:** Implement exact official V1 endpoints and fields from the spec. T2V/I2V share submit endpoint；I2V uploads exact local image bytes as allowed Base64 data URL only after egress authorization。Poll normalizes five official statuses。Fetch uses authenticated same-origin retrieve-content endpoint，不持久化 signed URL。Capability table is model/mode/duration/resolution-combination aware；Hailuo V1 rejects negative prompt、seed、provider-native FPS与 explicit aspect request because official schema does not expose them。

Map HTTP + `base_resp.status_code` into normalized core failure. Submit transport ambiguity after permit consumption is always outcome_unknown。No automatic POST retry、internal poll loop、callback server、cancel simulation、task scan或 shell-out `mmx`。

**Tests:**

- exact auth/header/path/query/body mapping without logging secret；
- T2V/I2V payloads and source image limits；
- 2.3/2.3-Fast/02 model-mode-duration-resolution matrix；
- official status mapping and missing/malformed task/file ID；
- authenticated retrieve-content fetch size/type limits；
- auth、invalid params、sensitive rejection、balance/quota、rate limit、timeout/internal errors normalized；
- submit transport error outcome unknown，poll/fetch transient safe retry classification；
- raw response、API key、Authorization、download URL absent from exceptions/receipts/repr；
- shared contract subset passes against adapter with fake transport；
- compatibility date and official links are asserted in adapter metadata。

**Verification:**

```bash
python -m pytest tests/test_production_minimax_hailuo.py \
  tests/test_production_video.py tests/test_production_video_fake.py -q
```

**Acceptance criteria:** adapter can be deleted without breaking P8 core；no new dependency；tests make zero network calls；no account benefit such as daily free count appears in code/domain。

---

### Task 7: Prove Runtime Candidate Activation and Fake E2E

**Dependencies:** Tasks 1-5；accepted P7 candidate-scope vocabulary。MiniMax Task 6 is deliberately not required, proving core/Fake E2E survives deleting the adapter。

**Files:**

- Create: `tests/test_production_generated_video_e2e.py`
- Modify: `tests/production_project_factory.py`
- Modify: `src/ai_video/production/video_generation.py`
- Modify: `src/ai_video/production/state_commit.py` only for gaps exposed by E2E
- Modify: `src/ai_video/production/__init__.py` for reviewed provider-neutral exports

**Change:** Build two-Shot fixture with an exact generated-video target and unrelated image/voice/caption state. Run request→submit→restart→poll→transient poll failure→poll success→fetch→probe/hash→provenance→Registry/Project/graph candidate→final activation→reader reopen. Provider cannot alter Shot target/role/strategy/prompt/source/license。For first transition from non-video strategy, candidate strategy change must be present in the original Codex-authored request and exact scope validator；Provider output alone cannot authorize it。

Public root exports may include `VideoGenerationRequest`、`VideoProvider`、`VideoProviderCapabilities`、`VideoGenerationService` and stable result types. Do not export concrete MiniMax/Fake adapters、raw transport、private permit、snapshot writer or low-level status parser from package root。

**Tests:**

- exactly one submit before restart and zero resubmit after；
- poll failure only increments poll；download failure only increments fetch；
- active old state survives every pre-activation failure；
- final Project/Registry/graph/Manifest identities switch atomically；
- loader answers provider/model/Shot/prompt request/source image/task/config/artifact hash provenance；
- exact replay has provider=0、poll=0、fetch=0、probe=0、write=0；
- same request/generation ID reuses active artifact；new generation ID creates new immutable candidate；
- unrelated P5 nodes and P6 receipts remain current when identities are unaffected；
- no renderer/ComfyUI/MiniMax network executable is called。

**Verification:**

```bash
python -m pytest tests/test_production_generated_video_e2e.py \
  tests/test_production_video_state_recovery.py tests/test_production_dependency.py \
  tests/test_production_project.py tests/test_production_registry.py -q
```

**Acceptance criteria:** user target flow is proven through active registered asset and Production reference；provider lifecycle不假称自动render activation；独立`1362687` slice已证明带exact metadata的H.264 MP4可进入既有P3/P4 renderer；all default provider evidence deterministic/offline。

---

### Task 8: Add Triple-Gated Real MiniMax Smoke Harness

**Dependencies:** Tasks 1-7；separate explicit user authorization for one real paid call；current pricing/model availability/license/policy review。

**Files:**

- Create: `tests/external/test_minimax_hailuo_live.py`
- Modify: `tests/conftest.py`
- Modify: `pyproject.toml` only to register an `external` marker, not to add dependencies

**Change:** Add a test option `--run-minimax-live` and require all gates from spec Section 15. Credential alone never runs. The smoke makes at most one 6s/768P request, persists task before poll, fetches/validates output into pytest temp/project fixture, sanitizes report, and never commits output。

The test consumes an operator-supplied current `VideoPricingSnapshot` with finite upper bound and explicit budget/egress receipt fixture outside git。If pricing upper bound or authorization cannot be proven, skip/fail before submit; do not downgrade to warn-only。

**Tests:**

- default collection skip；
- key-only skip；
- flag-only skip；
- flag+key without exact confirmation skip；
- missing pricing/budget/egress/provider enable makes submit count 0；
- fake transport proves exactly one submit gate；
- sanitized failure output contains no credential/header/raw response/signed URL。

**Verification:**

```bash
python -m pytest tests/external/test_minimax_hailuo_live.py -q
python -m pytest -q
```

The first command must skip by default. The second must perform zero external calls。A real invocation is not part of this plan execution and requires a separate user-authorized command containing `--run-minimax-live` plus the exact environment gates。

**Acceptance criteria:** accidental `pytest`/credential presence cannot charge；one real smoke, if separately authorized, is bounded and auditable；live success does not change default Provider behavior。

---

### Task 9: Full P8 Gate, Independent Review, Documentation and Rollback Proof

**Dependencies:** Tasks 1-7 implementation complete；Task 8 live call remains optional/separately authorized，且不是offline P8 closure blocker。

**Files:**

- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/agent-primary-contract-matrix.md`
- Modify: `docs/v0.2-runtime-baseline.md`
- Modify: `docs/v0.2-agentic-production-roadmap.md`
- Modify: this plan with actual verification evidence only if repository convention requires status recording

**Change:** Document only verified runtime behavior：provider-neutral explicit lifecycle、exact Task-0-selected P8 Manifest/Registry versions、single committer、fake default、H3/Hailuo/Seedance thin explicit adapters、no live default、no CLI、P5 semantic/applied evidence、resume/no-blind-resubmit、rollback/read compatibility。明确Hailuo三条live success、H3余额失败、Seedance offline-only，并把独立`1362687` MP4 composition acceptance与provider lifecycle分开。不得用既有证据授权新live调用。

**Focused verification:**

```bash
python -m pytest \
  tests/test_production_paid_provider.py \
  tests/test_production_paid_provider_state.py \
  tests/test_production_paid_provider_e2e.py \
  tests/test_production_video.py \
  tests/test_production_video_fake.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_minimax_h3.py \
  tests/test_production_minimax_hailuo.py \
  tests/test_production_seedance.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
```

Then run:

```bash
python -m pytest -q
git status --short --branch
git diff --check
git diff --stat <P8_IMPLEMENTATION_BASE>...HEAD
git diff --name-only <P8_IMPLEMENTATION_BASE>...HEAD
```

**Independent review questions:**

1. Does delete-MiniMax leave a coherent P8 core?
2. Can a future ComfyUI adapter map prompt/task/history/output without core changes?
3. Is any POST reachable without exact durable permit and policy authorization, plus egress for remote and budget for metered execution?
4. Can any crash/retry path submit twice or change Provider?
5. Are request/generation/submission/artifact identities still distinct?
6. Does Registry contain only stable provenance and Manifest only mutable lifecycle?
7. Does P5 use the resolved generation fingerprint for desired and bytes only for applied evidence?
8. Are old Manifest/Registry/Legacy surfaces compatible?
9. Can secret/raw response/signed URL enter state/log/fixture/error?
10. Does default full pytest prove zero network/charge?

**Acceptance criteria:** reviewer verdict accept；all blocking issues resolved；focused/full tests actually pass；diff contains only P8 closure truth；Task 8 remains optional and default skipped；provider lifecycle与独立MP4 renderer compatibility claim不混淆；docs match Git/runtime truth。

**Closure evidence:** `a089eac feat: activate generated video candidates`通过fresh staged receipt `.agent/harness/runs/p8-video-activation-20260819-v6/receipt.json`与fresh commit-range receipt `.agent/harness/runs/p8-video-activation-20260819-range-v1/receipt.json`。两份receipt均self-verified；完整`production_video_provider_tests`为`742 passed`，production contracts为`2036 passed, 3 skipped`，state为`933 passed`，dependency为`1045 passed`，Architecture Gate PASS。Task 8仍是optional/separately authorized，本次closure没有新live/paid调用。

---

## Schema Migration

- Task 0 records exact accepted Manifest/Registry bases and assigns their next compatible minor versions as `P8_MANIFEST_SCHEMA` / `P8_REGISTRY_SCHEMA`。
- First P8 lifecycle write uses `P8_MANIFEST_SCHEMA`；first generated-video registration uses `P8_REGISTRY_SCHEMA`。
- All accepted pre-P8 Manifest/Registry versions remain readable；P8 fields rejected in older explicit versions。
- No automatic bulk migration、no downgrade、no Legacy Manifest v1 change。
- Selected values are Manifest `2.7` / Registry `2.2` because accepted Paid Provider Gate owns Manifest `2.6` and Registry remains `2.1` at exact execution base `3890295`。

## Rollback

Operational rollback disables/removes P8 start/submit entrypoints and concrete MiniMax resolver registration。It must preserve：

- P8 Manifest reader/recovery；
- P8 Registry reader；
- request/profile/status/provenance/cost/egress receipts；
- external task IDs and outcome-unknown records；
- registered MP4 bytes and old Registry/graph snapshots；
- Legacy CLI/local ComfyUI path。

Rollback must not：schema downgrade、delete unknown remote tasks、release unsettled reservations as zero、replace generated asset with placeholder、fallback to another Provider or call submit。

## Definition of Done

- provider-neutral request/capability/task/provenance contract exists without MiniMax dependency；
- fake passes all contract/failure/restart tests offline；
- request/generation/submission/artifact identities are distinct and verified；
- submit intent and task handle are crash-safe；unknown outcome never blind-resubmits；
- poll/fetch resume the same task；
- MP4 is locally measured、hashed、registered and provenance-bound before activation；
- P8 Registry append-only and P8 Manifest sole lifecycle ownership hold；
- P5 desired uses the resolved generation fingerprint and applied uses exact artifact evidence；
- H3/Hailuo/Seedance adapters通过offline acceptance并使用injected transport；只有Hailuo具有live-success evidence；
- API key alone cannot run live test；default full pytest zero network/charge；
- Legacy/P1-P7 contracts pass；
- generated-video rendering由独立`1362687` compatibility plan验收，不并入Provider lifecycle或自动activation；
- code/tests/docs are independently reviewed and committed at stable checkpoints；
- completion does not imply push、release、live operation或 authorization for another Provider。
