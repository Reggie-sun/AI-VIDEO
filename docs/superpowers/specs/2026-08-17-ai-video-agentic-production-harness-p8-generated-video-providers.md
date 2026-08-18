# AI-VIDEO P8 Generated Video Providers Specification

Status: Offline implementation accepted on local `main`. Provider core、Paid Provider Gate、Fake、MiniMax H3/Hailuo 与 Seedance offline adapters均已完成 executable acceptance；本状态不授权新的 live call、真实付费提交、push 或 release。

Implementation snapshot: 2026-08-19。P6、P7 与 Base AI Comic E2E 已在 local `main` accepted；standalone Paid Provider Gate 已于 `cc82a49` 完成 Manifest `2.6` implementation、independent review 与 executable acceptance。P8 的 exact execution base为`3890295`，并固定使用`P8_MANIFEST_SCHEMA = "2.7"`、`P8_REGISTRY_SCHEMA = "2.2"`；最终candidate activation/recovery closure由`a089eac`提交，fresh staged/range receipts为`.agent/harness/runs/p8-video-activation-20260819-v6/receipt.json`与`.agent/harness/runs/p8-video-activation-20260819-range-v1/receipt.json`。Hailuo已有三条真实 succeeded/fetched MP4 proof；H3 live到达真实API但因余额不足返回`HTTP 402 / code 1008`，因此只有offline acceptance；Seedance只完成offline/fake-transport acceptance且未授权live。独立 generated-MP4 compatibility slice已由`1362687`验收，不改变P8 provider lifecycle ownership。

## 1. Goal

P8 建立最小但真实的 provider-neutral Generated Video capability：Production domain 可以为一个显式 Shot visual requirement 构造 durable request，解析并验证显式选择的 Provider，持久化外部 task lifecycle，取得并验证视频，注册 immutable Asset，并把 exact provenance 与 P5 lifecycle 绑定，而不让 Production Pipeline、Shot、Asset Registry 或 dependency resolver 依赖 MiniMax-specific API。

MiniMax Hailuo 是第一个取得真实成功证据的 Cloud Video Provider adapter；H3与Seedance也已作为显式、可删除的offline adapters验证同一 abstraction。任何 concrete adapter都不是 core domain、默认 provider、fallback 或 creative planner。

目标链路：

```text
Shot / explicit visual requirement
  -> VideoGenerationRequest
  -> explicit Provider resolution
  -> capability validation + resolved request
  -> budget/egress preview + authorization
  -> durable submit intent
  -> provider submit
  -> durable external task identity
  -> status observations
  -> fetch same task result
  -> local media validation + content hash
  -> immutable provenance + Asset Registry candidate
  -> P5 graph candidate
  -> one Production Manifest activation
```

## 2. Repository Findings

### 2.1 Existing owners

- `Shot` 与六种 `VisualStrategy` 已由 `src/ai_video/production/models.py` 定义；`generated_video` 已存在，但 Shot 不是 Provider request。
- `src/ai_video/production/validation.py::validate_shot_strategy()` 当前要求 `generated_video` Shot 已绑定 Registry 中 `AssetType.VIDEO + AssetSourceKind.GENERATED` 的 concrete asset。因此 active P2 Project 能表示“已物化 generated video”，不能表示 unresolved placeholder。
- `AssetRegistrySnapshot` 当前为 2.0/2.1；Registry immutable、append-only、content-addressed。`EgressMetadata` 目前只允许 remote generated voice，因此 remote generated video 需要最小 versioned `2.2` extension。
- `ProductionManifest` 当前最高为 2.6；它是 mutable lifecycle、desired/applied、active pointers、Paid Provider Gate budget/attempt truth 与 attempt history 的唯一 owner。
- `ProductionStateCommitter` 是 project/registry/render/graph/review write、activation 与 explicit recovery 的唯一 owner；P8 不增加第二 writer。
- P5 graph 已有 visual asset 与 `GENERATION_INPUT` vocabulary，但 generated visual 仍按普通 asset 消费 output bytes。P8 必须增加 request-semantic projection，不能把 nondeterministic artifact hash误当成 desired request identity。
- Manifest 2.6 Paid Provider Gate 已证明 exact preview/authorization、budget reservation、durable submit intent、shared committer-issued one-use `DurablePaidProviderSubmitPermit`、Gate-owned `PaidProviderSubmitReceipt.external_effect_id`、`outcome_unknown`、fake transport与secret redaction。P8直接复用该 Gate contract，不复制 voice 或 P8-specific paid authority。
- `httpx>=0.27` 已是 runtime dependency；MiniMax adapter 不需要增加 HTTP dependency，也不 shell out 到 `mmx`。
- `ffmpeg_tools.probe_clip()` 与 P3 held-file-descriptor media verification 可复用；P8 不引入第二套视频 parser。
- Legacy CLI 仍只有 `validate | run | resume`。当前没有 v2 CLI，P8 不新增 CLI。

### 2.2 Composition boundary and accepted compatibility slice

P8 provider core本身不修改`CompositionSpec`、`ResolvedTimeline`或HyperFrames，也不把fetched candidate自动解释为render activation。独立 compatibility slice已于`1362687 feat: compose generated MP4 visual spans`完成：带exact `VideoAssetMetadata`的本地H.264 MP4可作为`GENERATED_VIDEO` / `EXISTING_VIDEO` visual span进入既有`CompositionSpec -> ResolvedTimeline -> HyperFrames`，并继续由P4独占audio/caption mix与mux。

Provider lifecycle mandatory E2E仍止于active Project/Registry/graph exact reference；consumer compatibility由独立plan与receipt验收。两者没有合并writer、timeline或renderer ownership，也不意味着任意fetched candidate会自动注册、激活或进入render。

### 2.3 Accepted P7/Base/Paid Gate

P7 与 Base AI Comic E2E 已 accepted。P8复用其 shared Asset Generation vocabulary（request sealing、candidate scope、append-only Registry activation），并复用 Manifest 2.6 Paid Provider Gate 的 one-use metered-submit permit与 billable-effect identity。Task 0 已从 accepted Manifest `2.6` / Registry `2.1` base 分配 next-compatible Manifest `2.7` / Registry `2.2`。

P8 implementation 开始前必须满足：

1. P6 contract 已 freeze、review 并形成 accepted base；
2. P7 与 Base AI Comic E2E 已 accepted；
3. P7/shared Manifest `2.5` / Registry `2.1` 与 Asset Generation seam 已确认；
4. Paid Provider Gate commit `cc82a49` 已具备 explicit opt-in、budget upper bound/reservation、egress authorization、secret redaction、crash-safe submit receipt、one-use permit 与 fake transport evidence；
5. P8不得复制 `PaidProviderSubmitReceipt.external_effect_id`；video polling/fetch lifecycle只引用 Gate-owned exact billable-effect identity。

## 3. Contracts P8 Must Preserve

- Shot owns creative intent and `visual_strategy`; Provider 不选择或改写 strategy。
- Provider-specific prompt tuning、model parameters 与 workflow fields不进入 Shot或 ProductionProject core schema。
- ProductionProject、Manifest、Registry、logs、fixtures、snapshots不得保存 secret、Authorization header、cookie、account identifier 或 signed URL。
- Asset Registry只保存 immutable identity/provenance，不保存 queued/running/failed/stale 等 mutable lifecycle。
- Dependency Graph只保存 immutable typed inputs/edges/contributions，不保存 provider task status。
- Production Manifest独占 mutable attempt、desired/applied 与 lifecycle；`ProductionStateCommitter`独占 write/activation/recovery。
- `ResolvedTimeline`继续独占 order/frame/sample/timing；P8 core不推导 timeline。
- Legacy `config.py`、`PipelineRunner`、`ComfyClient`、Manifest v1、flat `runs/<run_id>/` layout 与公共 CLI 行为不变。
- remote/cloud永远 explicit opt-in，永不成为 local/default fallback。
- same-desired failure不自动 retry；exact replay不重复 submit、poll已终态 task、fetch已验证 artifact 或写 state。
- default `pytest` no-network、no-secret、no-charge、deterministic。

## 4. Architecture Decision

### 4.1 Selected lifecycle: explicit primitives plus domain orchestration

选择 Option C：Provider 暴露显式 primitives，由 provider-neutral `VideoGenerationService` 逐步编排；每个有副作用的 durable transition仍由 `ProductionStateCommitter`执行。

```python
class VideoProvider(Protocol):
    def capabilities(self) -> VideoProviderCapabilities: ...
    def resolve(self, request: VideoGenerationRequest) -> ResolvedVideoGenerationRequest: ...
    def preview(self, request: ResolvedVideoGenerationRequest) -> VideoGenerationPreview: ...
    def submit(
        self,
        request: ResolvedVideoGenerationRequest,
        video_preview: VideoGenerationPreview,
        paid_preview: PaidProviderCallPreview | None,
        authorization: PaidProviderAuthorizationDecision | None,
        permit: DurablePaidProviderSubmitPermit | None,
    ) -> VideoSubmitResult: ...
    def get_status(
        self,
        submission: VideoSubmission,
        submit_receipt: PaidProviderSubmitReceipt,
    ) -> VideoTaskObservation: ...
    def fetch(
        self,
        submission: VideoSubmission,
        submit_receipt: PaidProviderSubmitReceipt,
        observation: VideoTaskObservation,
        sink: BinaryIO,
    ) -> VideoFetchReceipt: ...
```

Remote metered submit直接复用 standalone Gate 的 `DurablePaidProviderSubmitPermit`。P8不定义 `DurableVideoSubmitPermit` 或第二套 authorization authority；local/unmetered adapter以 `None` 表达不需要 paid authority，不得伪造 Cloud receipts。

`VideoGenerationService` 不直接写文件或 Manifest。它负责：

- 从 injected registry 按显式 name 取 Provider；
- 运行 pure capability validation；
- 调用 committer 写 R+1 request 与 R+2 submit intent；
- 调用一次 `submit()` 并立即交回 committer 持久化 handle；
- 对已持久化 handle执行一次 status refresh；
- 在 remote success 后让 committer提供 owned held-FD sink，调用 fetch、probe、hash、prepare candidate 与 activate；
- 根据 persisted phase选择 safe next action，不从 console/Agent memory猜测。

不选择 `await provider.generate()` 作为唯一 API，因为它会隐藏 task ID、poll、restart 与 download recovery。当前仓库是同步 Python API，P8 不为外部 API 引入 asyncio runtime；每个 method有界，poll scheduling由 caller/Codex/worker控制。

### 4.2 Module boundary

```text
src/ai_video/production/video.py
  strict core models, identities, capabilities, errors, Protocol, injected resolver

src/ai_video/production/video_generation.py
  stepwise provider-neutral orchestration; no direct state writes

src/ai_video/production/video_fake.py
  deterministic scripted fake for CI/offline development

src/ai_video/production/minimax_hailuo.py
  Hailuo V1 typed profile, transport, request/response mapping, error normalization

src/ai_video/production/state_commit.py
  sole durable request/intent/handle/status/fetch/candidate/activation/recovery owner
```

不建立 `providers/video/base/factory/router/...` 多层 hierarchy。若未来 Seedance/Kling/ComfyUI 加入，它们实现同一 Protocol并通过 injected resolver注册。

## 5. Provider-Neutral Domain

### 5.1 Request

`VideoGenerationRequest` 是 immutable/self-sealing core request，至少包含：

- `generation_id`：显式、durable generation intent identity；重启不改变；用户明确要求同参数再生成一个候选时必须创建新 identity；
- `request_input_hash`；
- exact base project/registry/graph pointers；
- target Shot artifact ID/revision/hash、target role 与 target strategy；
- `mode = text_to_video | image_to_video`；
- Unicode NFC prompt与 hash；optional negative prompt与 hash；
- image bindings tuple：每项含 `role = first_frame | reference`、Asset ID、content hash、MIME、dimensions；T2V 必须为空，具体 I2V binding role/count由 capability variant验证；
- duration requirement、minimum resolution/aspect requirement、optional provider-native FPS requirement；
- optional seed；
- explicit provider kind、model ID与 content-addressed provider profile pointer/fingerprint；
- canonical input artifact IDs/fingerprint；
- output asset slot/ID。

Core 不出现 `hailuo_model_name`、`prompt_optimizer`、`fast_pretreatment` 等字段。Concrete adapter的 non-secret typed profile作为 content-addressed snapshot保存；core request只绑定 profile identity/hash。Profile不得包含 credential或 signed URL。

Remote metered request在 Provider resolution之后构造 `PaidProviderCallPreview(operation="video_generation")`，并使用 Gate-owned `PaidProviderAuthorizationDecision` 绑定 exact resolved hash、egress、budget与 live opt-in。P8不另建 `VideoCallAuthorization`；Local ComfyUI一类未来 adapter传 `None`，不得被迫伪造 Cloud receipts。

### 5.2 Requested, resolved and measured values

三层事实必须分开：

1. requested：caller要求的 mode/duration/resolution/aspect/FPS/seed，并 seal 为 `request_input_hash`；
2. resolved/effective：adapter capability validation后实际提交的 provider/model/profile与输出约束，并与 `generation_id`一起 seal 为 `resolved_generation_hash`；
3. measured：下载 artifact 经本地 probe得到的 width/height/FPS/duration/container/codec/frame evidence。

Provider response不能覆盖 measured truth。requested 与 effective差异必须显式、可审计；P8不允许 silent downgrade。

### 5.3 Provider-specific extension boundary

每个 concrete adapter拥有 strict/frozen profile model与 profile snapshot reader。Provider profile pointer进入 `request_input_hash`，profile version/effective parameters进入 `resolved_generation_hash`；secret不进入 profile。Stable provenance保存 provider kind、model、profile identity/fingerprint与 allowlisted effective parameter receipt；raw Provider JSON不进入 core Manifest/Registry。

## 6. Capability Model and Resolution

`VideoProviderCapabilities` 使用 declarative variants，而不是若干彼此独立、可能产生非法组合的 lists。每个 `VideoCapabilityVariant` 绑定：

- provider/model/profile family；
- execution kind `local | remote` 与 billing kind `local_unmetered | metered`；
- supported mode；
- allowed duration + resolution profile combinations；
- aspect ratio rule；
- source image MIME/size/dimension constraints；
- allowed image binding roles与 maximum reference count；
- negative prompt、seed、provider-native FPS support；
- idempotent submit、lookup/reconcile、task list、callback等 operational capability flags与保证期（若官方有）；
- output container/MIME与 native-audio policy。

Resolution 与 capability matching解耦：

1. caller显式选择 provider name/profile；
2. `VideoProviderRegistry.resolve(name)` 只返回 injected instance，不自动选择“最佳/最便宜” Provider；
3. Provider pure `resolve()`验证 exact capability variant；
4. unsupported在零 transport call下返回 typed capability failure；
5. runtime failure不得触发跨 Provider fallback。

`None`/unknown capability表示未获官方保证，不能当作 unlimited或 supported。

## 7. Identity Semantics

P8固定区分五类 identity：

| Identity | Meaning | Includes | Excludes |
| --- | --- | --- | --- |
| `request_input_hash` | caller intent before Provider resolution | prompt/source hashes、requested common settings、explicit provider/profile pointer、target/output slot | generation ID、resolved/effective settings、authorization、task ID、artifact bytes |
| `generation_id` | caller-issued identity for one explicit candidate generation | stable opaque ID | request/effective values、attempt/task/artifact identity |
| `resolved_generation_hash` / `desired_generation_fingerprint` | one exact resolved creative generation intent and P5 desired evidence | generation ID + request input hash + capability/profile version + exact effective settings + output slot | authorization、attempt/task ID、poll state、artifact hash |
| submission identity | one billable submit lifecycle | Gate attempt、resolved generation fingerprint、Gate authorization/receipt fingerprint；exact task ID只在 `PaidProviderSubmitReceipt.external_effect_id` | artifact hash；P8 durable duplicate task ID |
| artifact identity | exact materialized output | asset ID、MP4 SHA-256、size、measured media metadata | request equivalence assumption |

相同 requested inputs甚至相同 seed不保证 bit-identical MP4。Schema按字段角色禁止用 artifact hash替代 request/resolved identity，而不依赖“两个 SHA-256 值必须不相等”的脆弱 validator。若明确要求“同参数再生成一个候选”，`request_input_hash`保持相同，但创建新 `generation_id`，从而得到新的 `resolved_generation_hash` / `desired_generation_fingerprint`与 output asset ID；不得伪装为 infrastructure retry。

## 8. Durable Async Lifecycle

### 8.1 Phases

```text
request
  -> authorized
  -> submit_intent
  -> submitted(task_id durable)
  -> polling
  -> provider_succeeded
  -> fetching
  -> validated
  -> candidate
  -> activate
```

Terminal/exception paths：

```text
pre-submit invalid/rejected     -> failed (known no task)
submit transport ambiguity      -> outcome_unknown
provider terminal failure       -> failed
poll deadline reached           -> resumable timeout, task ID retained
fetch/download failure          -> resumable fetch failure, same task retained
artifact validation failure     -> failed, bytes not registered
```

P8 V1不提供公共 cancellation contract；未来若加入 cancellation，必须另行设计 durable cancel intent、outcome ambiguity与 restart semantics。每次 `get_status()`只观察一个 Gate receipt-selected task；P8不在 Provider 内部无限 sleep。Exact opaque external task ID只由 `PaidProviderSubmitReceipt.external_effect_id`持久化；P8 Manifest保存该 submit receipt pointer/fingerprint，不复制 task ID。Status history使用 bounded immutable normalized receipts并绑定 submit receipt fingerprint，不落 raw response。

### 8.2 Crash windows

- request/authorization durable 前：Provider call count 0；可重新开始。
- submit intent durable 后、Provider call前：permit尚未消费，可继续 exact action。
- permit消费/POST 后、Gate submit receipt durable前：必须 `outcome_unknown`；不 mint新 permit、不自动 POST。
- accepted Gate submit receipt durable后：restart从 receipt reopen唯一 task ID并只 poll该 task。
- success observation durable 后、fetch失败：只 fetch同一 remote result。
- local bytes完成但 Registry/Manifest未 activate：reopen exact candidate并显式 recover；不重新 submit/fetch已验证 bytes。
- final Manifest replace后：exact replay返回现有 active asset，Provider/fetch/write counts均为0。

### 8.3 Duplicate charge boundary

提交成功后在保存 task ID 前 crash是无法由本地 atomic filesystem transaction完全消除的 network side-effect gap。P8通过以下方式降低风险：

1. submit前 durable保存 generation/request/submission identity、policy authorization、applicable budget reservation/egress authorization与 one-use intent；
2. adapter仅在 exact one-use permit消费时发送一次 POST；
3. task ID收到后立即写入唯一 Gate `PaidProviderSubmitReceipt`；
4. 只有官方明确提供 lookup或有保证期的 idempotent replay时才允许 reconcile；
5. 无官方保证时保持 `outcome_unknown`、预算 unsettled/reserved并要求 explicit operator reconciliation。

这不会保证“零未知”，但保证未知不会变成 blind double charge。

## 9. Retry and Failure Model

### 9.1 Safe automatic retry

- 已知 external task ID的 status GET；
- 同一 succeeded task/result的 metadata/file GET；
- 同一 remote artifact的 bounded download；
- local probe/hash/candidate reopen；
- Provider明确返回 task未创建前的 pure validation/config failure不需要 retry。

### 9.2 Never unconditional retry

- generation submit POST；
- `outcome_unknown`的新 key/new attempt submit；
- auth、budget、egress、unsupported capability、invalid request、content rejection；
- provider terminal generation failure；
- cross-provider fallback。

`AiVideoError.retryable=True` 不足以授权昂贵 submit。Normalized `VideoProviderFailure`必须同时记录：operation、failure kind、outcome certainty与 retry safety。

最小 failure kinds：configuration、authentication、unsupported capability、invalid request、quota/rate limit、provider unavailable/transient、generation rejected/failed、poll timeout、download failure、artifact invalid、submission outcome unknown。

## 10. Asset Registry and Provenance

### 10.1 Registry extension

P8从 accepted Registry `2.1` base派生 `P8_REGISTRY_SCHEMA = "2.2"`：

- 所有 accepted pre-P8 Registry reader行为保持；
- 新 `VideoAssetMetadata` 仅适用于 `VIDEO`；
- generated video必须有 measured container/codec/width/height/FPS rational/duration/frame evidence、probe receipt、generation request/provenance identity；
- P8 Registry version允许 remote egress仅用于 generated voice或 generated video；
- remote generated video必须有 complete egress metadata与 cost receipt ID；
- canonical artifact path为 content-addressed managed MP4 path；
- Registry append新 record，不覆盖/删除旧 output。

### 10.2 Three provenance classes

1. stable domain provenance：request snapshot、prompt、source asset hashes、Shot/project identity、provider/model/profile fingerprint、经 bounded validation且 exact round-trip 的 opaque task/file IDs、effective settings receipt、egress/cost/policy receipt IDs、artifact hash与 measured metadata；日志需要时另派生 redacted display ID；
2. provider operational metadata：normalized status observations、poll count、rate-limit/backoff hint、remote result token；由 Manifest attempt或bounded receipt保存；
3. debug/raw response：默认不持久化；如未来启用必须是独立 explicit diagnostic policy，经过 allowlist/redaction，绝不成为 domain truth。

Signed download URL、Authorization header、raw body、account ID、API key永不持久化。Prompt保存在 content-addressed request snapshot中而不是重复塞进 Manifest或 AssetRecord；因此系统仍可回答 exact prompt，同时保持 Manifest紧凑。

### 10.3 Atomic activation

成功路径必须：

1. provider result写入 committer-owned bounded temp；
2. held-FD probe、hash并验证 container/video stream/size/duration/resolution/FPS；
3. 写 immutable request/result/probe/cost/egress/provenance receipts；
4. append一个 generated VIDEO AssetRecord；
5. 构造 exact target Shot/project candidate与 P5 graph candidate；
6. promote/reopen全部 immutable snapshots；
7. 在一次 final Production Manifest replace中切换 project/registry/graph与 lifecycle；
8. 若 P6 review/final acceptance绑定旧 graph/render identity，调用 P6-owned exact staleness helper，不复制 QA规则。

## 11. Dependency and Freshness

P8不把 task、poll或 Provider error写入 immutable graph。P5 graph schema可保持 2.0，但 builder/resolver增加 generated-video semantic evidence：

- desired contribution使用 `desired_generation_fingerprint`（即绑定 generation ID、`request_input_hash`、capability/profile version、exact effective settings与 output slot的 `resolved_generation_hash`）；source asset hashes已进入 request input hash，不重复依赖 output bytes；
- artifact bytes hash只作为 applied evidence，不作为 desired request identity；
- 仅 P8 Manifest operation或带显式 P8 provenance pointer的 candidate，fresh才要求 succeeded video attempt、selected request/provenance、Registry record与 exact content hash一致；pre-P8 P2/P5 generated-video record继续使用其 legacy applied semantics，直到被显式 P8 candidate supersede；
- request change/new generation ID只 stale受影响 visual asset及其真实 downstream；
- poll/status/cost receipt变化不 stale composition；
- same desired failed不自动进入 rebuild frontier；
- activation前 active Project/Registry/graph继续指向旧 valid state，不能放 placeholder AssetRecord。

首次从 non-video strategy切换到 `generated_video` 必须由 Codex/authoring层显式请求并在 final candidate activation中完成；Provider不得自行改变 strategy。Existing `generated_video` replacement path保持 active concrete asset直到新 candidate成功。

## 12. Provider Registry, Config and Secrets

- `VideoProviderRegistry`由 application composition root显式注入 `{name: instance}`；无 global singleton、import-time construction或 scattered factory。
- Provider name/model/profile属于 runtime request/config；credential不属于 ProductionProject。
- concrete adapter constructor接收 opaque credential supplier与 non-secret typed profile；core不自动读取环境变量。
- future application wiring可显式从 environment/secret store读取 credential，但只把 `credential_reference_kind`写入 preview/provenance。
- 未配置 Provider时 base production path完全可用；resolver fail closed，不 fallback。
- P8不修改 Legacy YAML config或新增公共 CLI。未来 v2 CLI必须另有 plan。

## 13. MiniMax Hailuo V1 Adapter

### 13.1 Current official compatibility snapshot

截至 2026-08-17，MiniMax官方把 Hailuo 2.3/2.3-Fast/02列为 Legacy Models；flagship H3使用独立 V2 API。`MiniMaxHailuoProvider`是明确的 V1 adapter，已实现的H3 V2 adapter则以独立dialect复用同一core contract；V1 `file_id`没有进入core。两者均已offline accepted，但只有Hailuo有live-success evidence。

Live H3 V2 与 live Hailuo V1 使用 distinct credential variable：H3 V2 pay-as-you-go adapter 的 `PaidProviderCallPreview.secret_reference.reference_id` 必须是 `MINIMAX_H3_API_KEY`（normal pay-as-you-go key），而 Hailuo V1 Token Plan 仍使用 `MINIMAX_API_KEY`（`sk-cp…` Token Plan credential）。两个变量各自独立；H3 adapter 不 fallback 到 `MINIMAX_API_KEY`，Hailuo adapter 也不读取 `MINIMAX_H3_API_KEY`。Live wiring 必须分别为两个 provider 注入对应 secret，缺一即 skip live smoke。

Hailuo V1官方 contract：

- origin `https://api.minimax.io`；Bearer auth；
- submit `POST /v1/video_generation`；T2V/I2V成功返回 `task_id`；
- T2V `prompt` required、最长2000字符；I2V prompt optional；`prompt_optimizer`默认true，`fast_pretreatment`默认false；
- poll `GET /v1/query/video_generation?task_id=...`；状态 `Preparing | Queueing | Processing | Success | Fail`；
- success返回 `file_id`与 output width/height；
- fetch优先使用同源 authenticated `GET /v1/files/retrieve_content?file_id=...`，避免持久化/追随 signed `download_url`；
- T2V models：`MiniMax-Hailuo-2.3`、`MiniMax-Hailuo-02`；
- I2V models：上述两者加 I2V-only `MiniMax-Hailuo-2.3-Fast`；
- 2.3/2.3-Fast 768P支持6s/10s、1080P支持6s；Hailuo-02 I2V另有512P 6s/10s；output 24fps；
- I2V `first_frame_image`必须是 JPG/JPEG/PNG/WebP、小于20MB、短边大于300px、aspect ratio 2:5 到 5:2；P8只上传已注册 local source image的 exact bytes；
- V1未公开 negative prompt、seed、可选 FPS或显式 aspect-ratio request field；Hailuo capabilities必须据此拒绝这些 non-null requests；
- V1官方资料未发现 client idempotency key、lookup-by-client-key、task list、cancel、submit dedup、`Retry-After`或 download URL TTL保证。

Official error evidence必须先按 operation解释，再决定 retry safety：`1000/1001/1002/1024/1033/1039`可作为 transient候选；`1004/2049`是 authentication，`1008` balance，`1026/1027` content rejection，`2013` invalid parameters，`1041/2045/2056`是 connection/rate-growth/usage limits。即使错误类别 transient，submit阶段也不能在 outcome不确定时自动 POST。官方 rate-limit表的 free/paid RPM属于可变账户政策，只进入 dated operational snapshot，不进入 core capability常量。

Official sources：

- [Models](https://platform.minimax.io/docs/guides/models-intro)
- [Text-to-video](https://platform.minimax.io/docs/api-reference/video-generation-t2v)
- [Image-to-video](https://platform.minimax.io/docs/api-reference/video-generation-i2v)
- [Task query](https://platform.minimax.io/docs/api-reference/video-generation-query)
- [Video download](https://platform.minimax.io/docs/api-reference/video-generation-download)
- [Retrieve content](https://platform.minimax.io/docs/api-reference/file-management-retrieve-content)
- [Error codes](https://platform.minimax.io/docs/api-reference/errorcode)
- [Rate limits](https://platform.minimax.io/docs/guides/rate-limits)
- [Official CLI/SDK reference](https://github.com/MiniMax-AI/cli/blob/main/SDK.md)

### 13.2 Adapter boundary

`MiniMaxHailuoProfile`是 strict non-secret config，表达 model、resolution tier、duration、`prompt_optimizer`与`fast_pretreatment`。它是 adapter-owned profile snapshot，不进入 core fields。

`MiniMaxHailuoProvider`：

- 使用 injected narrow transport/default `httpx.Client`；明确 connect/read/write/pool timeout、response size与download size上限；
- submit前验证 exact Hailuo capability与 source image bytes；
- adapter-owned typed mapper生成 official JSON；
- normalization把 MiniMax status/error变为 core observation/failure；
- 只持久化 allowlisted task/file/request/trace IDs；
- 不内部循环 poll，不自动重试 POST，不 shell out到 `mmx`；
- 不把“每日赠送3条”等账户权益写入 capability或 domain。

MiniMax V1官方资料未提供 cancellation与 idempotency保证；P8 V1因此不暴露 cancellation method。Transport在 permit消费后失败或 response无法证明 task未创建时，adapter返回 `submission_outcome_unknown`。

## 14. Fake Provider

`ScriptedFakeVideoProvider`是 first implementation与 contract reference。它支持：

- deterministic T2V/I2V request validation；
- fixed capability variants；
- one submit产生stable fake task ID；
- scripted `queued -> running -> succeeded` observations；
- deterministic committed MP4 fixture fetch；
- pre-submit rejection、submit unknown、transient poll failure、terminal failure、timeout、download failure、tampered artifact、unsupported capability；
- exact call counters与 restart state injection。

Fake不写 Manifest/Registry，不访问网络，不读取 environment，不隐藏 sleep。Default CI绝不需要 MiniMax。

## 15. Real API Safety

Live smoke不是 default acceptance。仅存在 `MINIMAX_API_KEY` 时必须 skip。真实 submit同时要求：

1. pytest explicit `--run-minimax-live`；
2. exact confirmation `AI_VIDEO_CONFIRM_MINIMAX_PAID_VIDEO_GENERATION=I_ACCEPT_ONE_PAID_GENERATION`；
3. credential；
4. current operator-reviewed `VideoPricingSnapshot`与 finite one-generation upper bound；
5. budget reservation receipt与 cost ceiling；
6. egress authorization绑定 prompt/negative-prompt hash、content classification、exact source files/hash/size/MIME与 destination；
7. provider/profile explicit enabled + allow_remote；
8. dedicated external marker，default collection只 skip；
9. exactly one 6s/768P request maximum；
10. sanitized report，不打印 secret、header、raw response或 signed URL。

任一 gate缺失，submit call count必须为0。Live smoke的成功不自动授权长期 operation、release或重复调用。

## 16. Scope

P8 includes：

- provider-neutral video request/capability/lifecycle/provenance contract；
- injected resolver与 stepwise service；
- deterministic fake与 shared contract tests；
- crash-safe external task persistence、poll/fetch resume与 no-blind-resubmit；
- generated MP4 validation/hash/immutable Registry registration；
- P5 semantic desired/applied integration与 exact activation；
- MiniMax Hailuo V1 adapter与 no-network HTTP tests；
- explicit opt-in single-call external smoke harness；
- default no-network E2E gate。

P8 non-goals：

- 当前已验收H3/Hailuo/Seedance之外的Kling、Veo或完整ComfyUI provider implementation；
- provider marketplace、automatic routing、cheapest/best model selection；
- general billing/accounting、quota scheduler、multi-region/distributed queue；
- Take marketplace或 prompt engineering framework；
- new public CLI/v2 server/webhook callback surface；
- renderer/timeline redesign或第二 renderer；
- 在P8 provider core内实现generated MP4 composition；该能力由独立`1362687` compatibility slice提供；
- P1-P7 unrelated refactor；
- silent remote fallback或 real API call in default CI。

Future ComfyUI sanity check：一个 `ComfyUIVideoProvider`应主要新增 adapter、typed local profile与 capability variants；它可把 existing prompt ID映射为 external task ID，把 history映射为 status，把 output fetch映射为 local artifact copy，而无需改变 request、Manifest lifecycle、Registry provenance或 P5 activation contract。

## 17. Schema and Public Surface Impact

| Surface | Decision |
| --- | --- |
| Legacy ProjectConfig/CLI/Manifest/layout | no change |
| ProductionProject/Shot base schema | no provider fields、no secret；existing concrete-reference invariant preserved |
| Production Manifest | `P8_MANIFEST_SCHEMA = "2.7"` from accepted Paid Provider Gate Manifest `2.6`；保留 Gate-owned budget/submit lifecycle并新增 P8 video lifecycle |
| Asset Registry | `P8_REGISTRY_SCHEMA = "2.2"` from accepted Registry `2.1`；增加 backward-compatible video metadata/remote generated-video rules |
| Dependency Graph | keep graph schema 2.0; add typed generated-video semantic/applied evidence |
| Composition/ResolvedTimeline/renderer | no change in P8 provider core |
| Package root exports | only reviewed provider-neutral core/service types; concrete MiniMax/fake/permit constructors imported from explicit modules or remain private |
| Runtime dependencies | no new dependency; use existing `httpx`, stdlib, ffprobe boundary |

Migration：Task 0已记录 `P8_MANIFEST_SCHEMA = "2.7"` 与 `P8_REGISTRY_SCHEMA = "2.2"`；所有 accepted pre-P8 versions remain readable，P8 fields在旧版本 fail closed。No downgrade。P8 disable/rollback保留已写 schema readers、receipts、tasks与 registered artifacts；停止新 submit entrypoints，不删除历史 state。

## 18. E2E Acceptance

Default fake E2E：

```text
load exact ProductionProject
  -> select explicit target Shot/role and generated_video intent
  -> construct sealed provider-neutral request
  -> resolve ScriptedFakeVideoProvider
  -> validate capability with zero network
  -> durable request + authorization + submit intent
  -> exactly one submit
  -> persist one Gate submit receipt containing the fake external task ID
  -> process restart
  -> poll same task queued/running/succeeded
  -> inject one transient poll failure without resubmit
  -> fetch same task deterministic MP4
  -> held-FD size/container/stream/duration/resolution/FPS validation
  -> content hash
  -> immutable provenance + P8 Registry candidate
  -> exact target Project + P5 graph candidate
  -> one final P8 Manifest activation
  -> reopen with load_production_project()
  -> generated video AssetRecord/provenance/request/task/hash all agree
  -> exact replay submit=0, poll=0, fetch=0, write=0
```

Required failure E2E：

- unsupported negative prompt/seed/FPS for Hailuo fails before transport；
- submit transport ambiguity becomes outcome_unknown and restart never resubmits；
- task ID durable crash resumes poll；
- poll transient failure only retries poll；
- completed task + failed download only retries fetch；
- tampered status/provenance/MP4/Registry/graph fails closed；
- same-desired failed attempt does not auto retry；
- new explicit generation ID permits a separately authorized candidate；
- API key alone causes zero live submit；
- default full `pytest` performs zero external network/cost。

## 19. Quality Bar Self-Check

- 删除 `minimax_hailuo.py` 后，core request/capability/fake/lifecycle/Registry/P5 contract仍完整。
- 已验收的H3与Seedance证明新增Provider主要是adapter + typed profile + capability declaration + contract tests，不需要污染core lifecycle。
- worker crash后已有 task ID只继续 poll；无 task ID且无官方 reconcile时 fail closed。
- polling/fetch失败永不回到 submit。
- same Shot重跑由 generation ID、request input/resolved generation hash、Manifest attempt与 P5 applied evidence决定 reuse/recover/new generation。
- CI完全依赖 fake/fixture；MiniMax unavailable不影响 core acceptance。

## 20. Open Risks

- Hailuo V1已是 Legacy API，官方可能下线或改变 model availability；implementation与 live smoke前必须重新核对 official docs。
- V1缺少 idempotency/reconcile/cancel，submit-after-accept-before-task-persist gap只能 fail closed，不能完全消除。
- Base AI Comic/P7已accepted；未来adapter仍不得从未合并或并发lane猜schema。
- 已验收的独立composition slice只支持带exact metadata的本地H.264 MP4；P8 provider E2E本身仍不等于candidate已注册、激活或进入final render。
- provider pricing、quota、rate limits会变化；只接受 execution-time pricing snapshot，不写死账户权益。
- prompt/source media可能有隐私、license与内容政策风险；egress/license authorization必须独立存在。
