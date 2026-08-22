---
surface_id: provider_neutral_generation_requirement
canonical: true
spec_status: accepted
implementation_status: implemented_offline
live_status: not_applicable
quality_status: not_evaluated
release_status: unreleased
runtime_status_owner: docs/v0.2-runtime-baseline.md
roadmap_owner: docs/v0.2-agentic-production-roadmap.md
contract_version: provider-neutral-video-requirement/1
---

# AI-VIDEO Provider-Neutral Generation Requirement Specification

## Status

Accepted and implemented offline。Current `video-planner/3` plan内嵌sealed provider-neutral
requirement；verified projection、Router-owned exact selection、provider-bound request、deterministic
compilers与request/resolved/activation lineage均已有source/test evidence。Historical top-level
generation fields只保留read-only compatibility projection，不是current serialized truth。

该offline status不证明Provider、ComfyUI、credential或media execution，也不升级为Shot Quality
Gate、subjective quality acceptance、activation、Final Acceptance或release truth。Local H3 T8
family当前已完成provider-name-scoped stateless local pass-through；concrete product caller和各lane的
live/quality evidence仍由runtime baseline分层记录。

## Problem Boundary

当前 runtime 已有三段有效但尚未形成唯一端到端合同的 truth：

- `VideoGenerationPlan` 保存 provider-neutral generation mode、continuity、motion、required roles 与 capability requirements；
- Shot Router 独占 exact capability matching 与 Provider/profile selection boundary；
- `VideoGenerationRequest` 同时保存 Shot/asset/output intent、Provider/model/profile identity和已经写成 prompt 的 creative content。

这使 production orchestration 仍可能在 Planner 与 Router 之外直接构造 provider-bound request，run-local code 仍可能拼 prompt，adapter 也可能在缺少明确 neutral requirement 时补做 creative decision。目标不是新增第四个 planner 或新的 lifecycle，而是把已有 plan 中的 generation semantics收敛成一个 hash-bound、可验证、只能由 Planner 派生的深层合同。

## Goal

建立唯一链路：

```text
Canonical Shot + Intent Evidence + Continuity
  -> VideoGenerationPlan
     -> embedded ProviderNeutralVideoRequirement
        -> Shot Router exact capability matching and Provider/profile selection
           -> ProviderBoundVideoRequest
              -> Provider Adapter deterministic prompt/request/payload compilation
                 -> existing VideoGenerationRequest / resolved request
                    -> existing Production lifecycle
```

该链路必须保证：

- requirement 不成为独立、可漂移的第三套 creative truth；
- Router 继续是 Provider/profile/capability selection 的唯一 runtime owner；
- Adapter 只能表达已经批准的 neutral requirement，不能重创作、降级、选 Provider 或 fallback；
- existing `ProductionStateCommitter`、Manifest、Registry、permit、recovery、Dependency Graph、`ResolvedTimeline`、Review/Repair 与 Final Acceptance ownership全部不变；
- fake/offline acceptance、Local H3 live proof与cloud/paid live proof严格分层。

## Non-Goals

- 不实现或替代 `ShotReadinessGate`、Shot Quality Gate、post-fetch quality gate、P6 Review/Repair或human Pilot Reality Gate；
- 不判断 identity drift、motion naturalness、continuity quality、画面美感、subjective sharpness或Final Acceptance；
- 不新增 Provider ranking、automatic selection policy、fallback、retry、repair、candidate iteration或Candidate 2/3；
- 不新增global Provider catalog、automatic candidate discovery、Registry-owned selection或
  Registry-to-Service automatic assembly；
- 不改变 canonical Shot、Asset Registry、Manifest、Dependency Graph、`ResolvedTimeline`、renderer、committer、permit或recovery schema ownership；
- 不把 Local H3 Alice C2 Candidate 1 的 prompt、locked-camera 英文句子或任何 run-local prompt提升为通用 Shot truth；
- 不调用 Creative Skill、Provider、ComfyUI、network、credential或media tooling；runtime Skill calls必须保持 `0`；
- 不新增 CLI、dependency、queue、API server、Agent runtime或第二个 production coordinator。

## Current Source Truth

- `VideoPlanningRequest` 的 semantic seal排除 diagnostic `request_id`；`VideoGenerationPlan.plan_id` 由 source request hash派生，`plan_hash`覆盖除自身以外的整个 plan。
- `VideoPlanner.plan()` 是当前唯一 provider-neutral planning decision owner；`require_current_video_plan()`负责 current request/plan STOP。
- `ShotRoutingContext` 绑定 exact activated Shot、selected Registry revision、Character/Scene references、terminal/keyframe与typed semantic continuity state。
- `VideoGenerationResolver` 对一个 exact selected capability做 role、asset、output、local/remote policy与budget匹配；denial返回 typed blocked decision且不 fallback。
- `VideoProviderRegistry`按exact `provider_name`保存多个injected Provider objects；只拒绝duplicate
  name，不做selection、ranking或fallback。
- `VideoGenerationService`每个实例只接收一个exact `VideoProvider | LocalVideoProvider`；它不查询
  Registry，也不在remote/local Providers之间自动dispatch。
- `comfy-local-h3-t8` family合并Quality/Turbo capabilities，并按durable exact identity无状态委托
  compile/resolve/preview/preflight/submit/status/fetch完整local seam；Seedance、
  Hailuo与MiniMax cloud H3使用distinct provider names和各自adapter，不进入该family。
- `VideoGenerationRequest` 当前混合 Provider/model/profile、prompt、bindings、output、base snapshot与lifecycle identity；request `/1`–`/4`、resolved request `/2`–`/5`与activation scope `/1`–`/3` hashes已有兼容契约。
- Provider adapters当前在 `resolve()` 验证 request/capability，并在 submit boundary构造 provider payload；它们不得成为 state writer或activation owner。

## Ownership Model

| Concern | Single owner | This slice rule |
| --- | --- | --- |
| Canonical Character / Scene / Shot intent | `ProductionProject` creative artifacts | requirement只投影 exact identity与approved semantics，不回写 |
| Intent and Review evidence | existing typed projections / P6 evidence | requirement绑定 exact evidence hash，不创建 approval |
| Requirement derivation | `VideoPlanner` | 只有 Planner 可从 current request 派生；model constructor只 seal，不做 creative decision |
| Requirement schema and verified boundary envelope | pure cycle-neutral `src/ai_video/production/video_requirement.py` | Planning 与 Router可共同 import；该 module无 IO、Provider、writer或lifecycle dependency |
| Provider/profile/capability selection | Shot Router | Provider identity只能从 Router decision进入 provider-bound request |
| Exact Provider object lookup | `VideoProviderRegistry` | exact-name lookup only；可以并列多个distinct-name Providers，不选择、不fallback |
| Registry-to-Service assembly | explicit caller/orchestration boundary | 按selected `provider_name`和sealed `execution_kind`注入exact adapter；本Spec不新增coordinator |
| Provider-native expression | selected Provider adapter compiler | 只做 deterministic expression；不能改变 requirement |
| Request/submit/fetch/activation lifecycle | existing P8 owners and `ProductionStateCommitter` | 不新增 writer、attempt state或activation path |
| Desired fingerprint and invalidation | Dependency Graph / existing resolved generation identity | requirement hash作为新 input contribution，不建立第二 resolver |
| Quality/Review/Final Acceptance | P6 Review/Repair + human gate | requirement只声明 objective capability need，不判质量 |

`production` modules不得 import `ai_video.planning`。cycle-neutral schema module同时定义requirement和携带sealed requirement + minimal hash lineage的`VerifiedGenerationRequirementProjection`；semantic builder与plan/requirement freshness verifier仍只位于Planning。Router和Adapter不得调用 builder、接收`VideoGenerationPlan`类型或从 Shot重新派生 requirement。

## One Truth Relationship

### Embedded, not parallel

`ProviderNeutralVideoRequirement` 是 `VideoGenerationPlan` 的 required nested field，不单独持久化、不拥有独立 lifecycle、不允许 caller在 plan之外替换。新 plan contract为 `video-planner/3`：

```text
VideoPlanningRequest video-planner/3
       generation_intent: ProviderNeutralGenerationIntentProjection
  -> VideoGenerationPlan video-planner/3
       source_request_content_hash
       generation_requirement: ProviderNeutralVideoRequirement
       reason_codes / warnings / outcome / rationale / confidence
       plan_hash
```

现有 top-level `generation_mode`、`continuity_mode`、`motion_requirement`、`required_asset_roles`与`capability_requirements`不再作为 serialized duplicate fields。短期 source compatibility只允许 read-only properties代理到 `generation_requirement`；所有 hash、Router mapping与tests只读取 nested requirement。不得同时序列化两份值，也不得提供能够分别更新两份值的 API。

### Unique derivation

`VideoPlanner.plan()` 内的一个 private pure builder是唯一 semantic derivation path。`ProviderNeutralVideoRequirement.create()`只执行 strict validation、canonical ordering与seal；它只能消费v3 request中的typed projection，不得从 prose、Shot自由文本、Provider或policy猜测缺失内容。Router、orchestration、adapter、fixture helper均不得调用另一套 derivation algorithm。

### Hash relationship without a cycle

1. `VideoPlanningRequest.request_content_hash`继续绑定 exact Shot、intent、asset、Review和policy projections。
2. requirement绑定 `source_request_content_hash`，计算 `requirement_hash`；`requirement_id = "video-requirement-" + requirement_hash[:24]`，ID不参与自身 hash。
3. `VideoGenerationPlan.plan_hash`覆盖完整 nested requirement，包括其 ID/hash；requirement不反向保存 `plan_hash`，避免循环。
4. plan validator强制 target Shot identity、source request hash、mode/continuity semantics与nested requirement一致。
5. Planning current-plan boundary验证request、plan和embedded requirement后，创建cycle-neutral `VerifiedGenerationRequirementProjection`；该envelope只保存plan hash、requirement和verified source/target hashes，不复制generation fields。
6. 任何 caller传入独立 requirement、替换 nested bytes、绕过verified envelope或使用 stale request都会在 Router前 STOP。

## Typed v3 Planning Input

Current `VideoPlanningRequest video-planner/2`没有完整的space/axis/action endpoint/motion envelope/pacing/camera endpoint typed input。为了禁止builder从`Shot.intent`或prompt prose猜测，本slice将request升级为`video-planner/3`，新增required `ProviderNeutralGenerationIntentProjection`：

| Group | v3 projection rule |
| --- | --- |
| open/close state | explicit typed refs/hash；unknown必须使用enum `UNSPECIFIED`，不得用空字符串猜测 |
| identity/scene/space/axis | exact artifact/constraint identities加typed preservation/crossing policy；没有evidence时显式`UNSPECIFIED` |
| action/motion/pacing | typed start/progression/endpoint、envelope与cadence；与existing `ShotIntentEvidence` current hash一致 |
| camera intent/endpoint | typed movement/stability/framing endpoints和expression strength；不保存Provider grammar |
| reference/output/audio/quality needs | provider-neutral role与objective capability projection；不得包含selection identity |

`UNSPECIFIED`不是Adapter自由发挥许可。Planner必须依据mode/policy将其判为允许、需要human review或`BLOCKED`；若requirement已通过但selected Adapter仍无法表达，则返回typed unsupported。v2 request/plan fixtures保留原hash测试，但不能进入new production-attempt path；caller必须以current canonical inputs重建v3 request。

## Provider-Neutral Requirement Contract

所有 models均 frozen、`extra="forbid"`、NFC-normalized、canonical ordered，并使用 `provider-neutral-video-requirement/1` schema。以下是 logical field groups；implementation可拆为 cohesive nested models，但不得改变语义或引入 Provider字段。

### Identity and freshness

| Field | Contract |
| --- | --- |
| `contract_version` | exact `provider-neutral-video-requirement/1` |
| `requirement_id` / `requirement_hash` | deterministic ID与canonical SHA-256 seal |
| `source_request_content_hash` | exact current `VideoPlanningRequest video-planner/3` semantic identity |
| `target_shot` | exact Shot id、revision、content hash |
| `scene` / `characters` | exact contributing artifact IDs、revisions与content hashes；canonical order |
| `intent_evidence_hash` / `generation_intent_hash` | canonical hashes of exact `ShotIntentEvidence` and v3 typed generation-intent projections |
| `review_evidence` | optional exact evidence ref、target Shot identity、projection hash；没有 Review时显式为 `None` |
| `asset_evidence` | exact role、asset id、SHA-256、canonical owner identity与measured metadata；Router在独立的current-context/provider-bound lineage中绑定selected Registry revision，不修改requirement，也不由Planner猜测 |

Requirement freshness不是第三个 clock或mutable status。它只由上列 identities与hash比较得出；任一 source变化必须重新运行 Planner并得到新 requirement/plan。

### Semantic generation fields

| Group | Required provider-neutral content |
| --- | --- |
| `generation_mode` | Planner选择的 neutral mode；仅使用 current planner vocabulary |
| `continuity_mode` | `EXACT_TERMINAL | REFERENCE | SEMANTIC | NONE` |
| `open_state` / `close_state` | typed state refs、state text/hash与required change；不得保存 Provider prompt grammar |
| `identity_continuity` | exact Character identities、allowed variation约束、identity preservation strength |
| `scene_continuity` | exact Scene identity、time/mood/state constraints |
| `space_continuity` | subject position、screen direction、entrance/exit state与spatial transition |
| `axis_continuity` | camera axis、crossing policy与framing continuity；unknown必须显式，不得猜测 |
| `subject_action` | action start、action progression、action endpoint与required state change |
| `motion_envelope` | onset、peak、settle、direction、amplitude class；只表达 Shot intent |
| `pacing` | neutral cadence/tempo class及Shot duration relationship |
| `camera_intent` | movement kind、framing intent、stability/locked intent与expression strength |
| `camera_endpoint` | start/end framing、position、orientation和endpoint constraints |
| `semantic_reference_roles` | typed roles such as identity、scene、first frame、last frame、continuity、video、audio；不预先压成 Provider role |
| `output_need` | timing mode、duration/frame contract、exact/adaptive geometry policy、ratio、fps、container/MIME |
| `audio_need` | `forbidden | optional | required` native audio requirement；P4 canonical mix ownership不变 |
| `quality_need` | objective tier、minimum raster/codec/container/fidelity capability与whether native enforcement is required；不包含主观 PASS |

`expression_strength` 至少区分：

- `semantic_prompt_allowed`：Adapter可用 deterministic prompt grammar表达；
- `native_control_required`：Provider capability必须有原生结构化控制；只有 prompt文字不算满足。

这使 Adapter可以诚实返回 unsupported，而不是假装一句 prompt等价于原生 camera/endpoint/control contract。

### Exact evidence rule

每个 semantic reference role必须指向 requirement中的一个 exact `asset_evidence` entry。Asset availability、Registry lookup或Ark materialization不是 requirement owner；它们仍由 current projections、Router binding和Provider-specific preflight验证。Candidate 1 MP4及其 SHA-256只可作为后续 Local H3 regression oracle，由单独 live-acceptance task引用；不进入通用 requirement fixture或默认 prompt。

## Forbidden Requirement Content

`ProviderNeutralVideoRequirement` MUST NOT contain：

- Provider name、Provider kind、model ID、Endpoint ID、profile ID/version/path/hash或capability ID；
- H3 workflow、binding、node ID、sampler、scheduler、CRF或ComfyUI execution details；
- Provider-native prompt grammar、payload key、Ark `asset://` identity、MiniMax task fields或signed URL；
- Skill name、Skill output、Skill routing evidence或runtime Skill call；
- fallback order、ranking score、retry policy、candidate count或automatic downgrade；
- Candidate 1的具体英文 prompt、locked-camera英文句子或run-local prompt fragments；
- Manifest phase、permit、budget reservation、task ID、fetch URL、activation、Review verdict或Final Acceptance。

Strict forbidden-field tests必须递归检查 nested models，而不是只检查top-level字段名。

## Router Contract

### Inputs

Router只消费：

- Planning current-plan boundary签发的cycle-neutral `VerifiedGenerationRequirementProjection`；
- exact `ShotRoutingContext` / current readiness evidence；
- available sealed Provider capability snapshots与profile pointers；
- explicit routing policy和task authorization/budget decisions。

### Selection ownership

Provider/profile/capability identity只能由 Router decision产生。Planning先验证plan与embedded requirement并只投影verified hash lineage；`shot_router.py`不得import或解析plan。Orchestration可以提供explicit candidate set或selected policy input，但不能把Provider identity直接写入 request。Router保持 current no-fallback semantics：一个 exact decision被 capability/policy拒绝时返回 blocked；不得尝试第二个 Provider/profile。

### Multi-Provider coexistence and assembly

Provider-neutral architecture必须允许以下peer Providers同时存在：

```text
comfy-local-h3-t8 -> Local H3 Quality/Turbo capability family
seedance           -> SeedanceVideoProvider
minimax_hailuo     -> MiniMaxHailuoVideoProvider
minimax_h3         -> MiniMaxH3VideoProvider
future name        -> future explicit Provider adapter
```

`VideoProviderRegistry`是exact injected lookup，不是candidate catalog、Router或fallback engine。
它可以同时保存上述distinct names；“sole/unique registration”只能限定在某一个exact
`provider_name`内部。例如`comfy-local-h3-t8`不能同时把Quality child、Turbo child与family注册为
三个同名entries，但这不限制Registry同时保存Seedance、Hailuo或future Providers。

Router对caller显式提供的candidate capability snapshot做exact selection。当前
`VideoGenerationResolver`一次消费一个`VideoProviderCapabilities` snapshot；本Spec不声称已经存在
一个自动汇总所有Providers的global catalog。若future orchestration提供多个candidate snapshots，
它仍必须把exact candidate set和policy作为显式input交给Router，不得在Router外预选、排序或fallback。

Router成功后，existing explicit caller按selected `provider_name`获取exact Provider object，并按
sealed `execution_kind`进入local或remote lifecycle seam。`VideoGenerationService`只消费已经注入的
exact Provider；它不查询Registry，也不决定execution kind。Registry、Service与Provider adapter都
不得成为第二个selector。

Local H3 T8 target family聚合same-name Quality/Turbo capabilities，并按durable identity把
`compile_request()`、`resolve()`和完整`LocalVideoProvider` seam原样委托给exact child。Current source
只完成compile/resolve，因此同名children的runtime assembly尚未闭合。Remote Providers继续拥有
独立`VideoProvider` seam；family不得吸收remote variants、代理remote calls或成为global execution
façade。

### `ProviderBoundVideoRequest`

Router成功后创建一个 sealed、pure、non-durable projection：

| Field group | Content |
| --- | --- |
| lineage | plan hash、requirement hash、target Shot identity、Router semantic/audit decision hashes |
| selection | exact Provider name/kind/model/profile pointer、capability ID/fingerprint、execution/billing kind |
| bindings | deterministic mapping from semantic reference roles to exact current image/media bindings |
| output | exact selected output requirement supported by capability |
| lifecycle envelope | generation/output asset IDs与base project/registry/dependency pointers supplied by existing owner |
| compiler contract | expected adapter compiler ID/version and required expression strengths |
| seal | `provider_bound_request_hash` |

它不包含 prompt或Provider payload。它不是 Manifest、attempt state或candidate lifecycle owner，也不得持久化Provider outcome。

### Projection determinism

相同 current plan、requirement、Router policy/capability snapshots和base pointers必须产生 byte-identical `ProviderBoundVideoRequest`。变化矩阵：

| Changed input | Required effect |
| --- | --- |
| diagnostic request ID only | no requirement/plan/provider-bound hash change |
| Shot、intent、continuity、asset或Review identity | new request hash -> requirement hash -> plan hash -> routing/provider-bound hash |
| Provider capability/profile/policy | requirement hash unchanged；routing/provider-bound hash changes |
| adapter compiler version | requirement和Router semantic requirement不变；compiled request hash changes |
| output/provider binding | P5 desired generation contribution changes；only exact downstream closure invalidates |
| unrelated Shot/asset | no target requirement或desired fingerprint change |

## Adapter Compilation Contract

Adapter新增 pure `compile_request(provider_bound, requirement)` seam，返回 discriminated result：

```text
ProviderRequestCompilationResult
  = CompiledProviderVideoRequest
  | ProviderRequirementUnsupported
```

### Compiled result

`CompiledProviderVideoRequest`包含：

- exact `provider_bound_request_hash`与`requirement_hash`；
- adapter compiler ID/version/hash；
- deterministic provider-native prompt；
- deterministic existing `VideoGenerationRequest` projection；
- payload projection fingerprint或payload compiler inputs，但不包含secret、signed URL或submit outcome。

Existing `VideoGenerationRequest`继续作为 lifecycle DTO。新 requests使用 additive request `/5` hash branch，绑定 `requirement_hash`、`provider_bound_request_hash`和compiler identity；历史 request `/1`–`/4`缺少这些字段时必须保持 byte-for-byte hash/reopen compatibility。不得改写历史 fingerprint projection。

`ResolvedVideoGenerationRequest`当前`/5`已属于hard-cut schema，因此new compiled lineage必须使用resolved request `/6`，不能复用`/5`。`VideoActivationScope`对new lineage使用activation scope `/4`；历史resolved `/2`–`/5`和activation scope `/1`–`/3`必须保持byte-identical。三个version branches都由是否存在完整new lineage fields显式选择，不能只根据continuity/hard-cut presence猜测。

### Unsupported result

`ProviderRequirementUnsupported`至少包含：

- requirement、provider-bound request与selected capability identities；
- typed reason code，例如 `REFERENCE_ROLE_UNSUPPORTED`、`NATIVE_CONTROL_UNSUPPORTED`、`OUTPUT_UNSUPPORTED`、`AUDIO_UNSUPPORTED`、`PROMPT_EXPRESSION_UNSUPPORTED`或`COMPILER_VERSION_UNSUPPORTED`；
- exact unsupported field paths；
- `retryable=False`和空 prompt/payload。

Lifecycle boundary把该result映射为 existing `ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED`（必要时可在 implementation review中批准更窄的 additive error code），但不得：

- 改写或删除 requirement field；
- 把 `native_control_required`降为prompt文字；
- 选择另一个 Provider/profile/capability；
- 自动fallback、retry、remint permit或提交部分payload；
- 产生durable intent、budget/egress side effect或Provider call。

### Mechanical defaults vs creative decisions

Adapter可应用 sealed profile中不改变semantic requirement的mechanical defaults，例如provider-required false/default字段省略、container spelling或fixed endpoint mapping。任何会改变action、camera、continuity、reference role、audio或quality need的default都是creative decision，必须返回unsupported或要求重新规划。

## Capability Mapping Matrix

该matrix描述当前 offline source truth；implementation当天必须重新验证 exact profile/capability snapshots。它不是Provider selection order，也不授权live call。

| Lane | Current capability expression | Neutral mapping | Must return unsupported when |
| --- | --- | --- | --- |
| Local H3 `comfy-local-h3` `fl2va` | I2V；required `first_frame`；optional `last_frame`；`max_reference_count=0`；PNG；exact dimensions within sealed bounds/multiple；24fps；native audio；seed supported；loopback-only | open endpoint -> `first_frame`；close endpoint可在requirement明确时 -> `last_frame`；camera/action/pacing只按reviewed deterministic H3 grammar表达；output必须匹配sealed profile | requirement需要identity/scene/continuity reference slots、reference media、negative prompt、unsupported native camera control、超出profile geometry/timing，或只靠prompt不能满足native enforcement |
| Local H3 T8 `comfy-local-h3-t8` family | T2V；Quality与Turbo为两个exact local/unmetered capabilities；current family已完成stateless local pass-through | Router必须显式选择Quality或Turbo；family按durable capability/identity委托，不产生第二次选择 | missing/wrong capability、duplicate/foreign identity、unsupported output，或任何需要remote/reference/edit/extend的requirement；不得改选sibling或remote Provider |
| MiniMax cloud H3 | T2V only；fixed 4s/1366x768；no image/media refs；native audio；no seed/negative prompt | 仅适合无reference且允许T2V的requirement；semantic fields可编译进prompt | any exact first/last/reference role、seed、negative prompt、different output或native structured control required |
| `MiniMax-Hailuo-2.3` I2V | exactly one `first_frame`；no `last_frame`/reference；adaptive `768P`；141 frames@24fps；MP4；no native audio；no seed/negative prompt | open endpoint -> `first_frame`；output必须保留adaptive geometry；neutral action/camera/pacing编译为Hailuo prompt | close endpoint必须由last-frame control保证、任何reference slot/native audio/seed/negative prompt、fixed pixel claim或native control requirement无法表达 |
| Seedance 2.0 Mini I2V | required `first_frame`；supports `last_frame`；480p/720p exact or adaptive family mapping；provider-selected/exact duration；MP4；native audio false/true | first/last endpoints映射为role；audio/output由exact capability选择；Ark asset identity由existing sealed materialization resolver提供，不进入requirement | required asset无sealed Active Ark identity、output/audio不匹配、reference semantics被错误压成I2V role、或native control在selected capability不存在 |
| Seedance 2.0 Mini R2V/edit/extend | R2V reference images up to 9；reference video/audio up to 3 each and family total duration limit 15s；no seed | semantic reference roles映射到`reference`/typed media bindings；exact asset and duration evidence保留 | reference count/measurements/duration超限、audio-only违反family contract、asset materialization缺失或mode不匹配 |
| Seedance 2.5 family | family-level R2V/edit/extend and larger reference limits；model/profile-specific output and task type | 仅在Router选择exact 2.5 capability后由adapter编译 | 不得把2.5能力外推到2.0/1.x profile；any exact profile mismatch blocks |

Reference counting继续只统计映射为 `role == "reference"` 的bindings；required `first_frame`和optional `last_frame`分别验证，不能计入reference quota。

## Error and STOP Contract

| Stage | Typed failure | Required behavior |
| --- | --- | --- |
| Planner derivation | `PLANNING_PREFLIGHT_BLOCKED` / invalid requirement seal | Router、adapter、Provider call count为0 |
| Freshness recheck | stale request/plan/requirement/Shot/evidence identity | rebuild current projection；不得patch旧requirement |
| Router mapping | existing blocked missing-input/capability/policy/authorization outcome | no adapter compilation、no fallback |
| Adapter expression | `ProviderRequirementUnsupported` -> `VIDEO_CAPABILITY_UNSUPPORTED` | no prompt/payload submit、no alternate Provider |
| Existing lifecycle | existing typed P8 errors | current permit、unknown-outcome、recovery semantics不变 |

Unsupported不是quality verdict，也不是自动repair signal。只有新的明确user/Review decision改变canonical inputs后，Planner才可产生新的requirement。

## Fingerprint and Invalidation Contract

- `request_content_hash`：current Planner input identity；v3加入typed generation-intent projection，同时保留diagnostic-ID exclusion与historical v2 fixtures。
- `requirement_hash`：唯一neutral generation semantics/evidence identity。
- `plan_hash`：requirement + planning outcome/audit identity。
- `semantic_routing_hash`：requirement-to-capability semantic selection；必须新增requirement hash contribution，但不复制requirement payload。
- `audit_decision_hash`：policy/reasons/outcome/capability snapshot。
- `provider_bound_request_hash`：exact selection、bindings、output、base pointers与compiler contract input。
- `request_input_hash`：compiled existing lifecycle request；new request `/5`包含requirement/provider-bound/compiler lineage。
- `resolved_generation_hash == desired_generation_fingerprint`：new resolved request `/6`包含完整new lineage；existing equality owner继续保持。
- `scope_fingerprint`：new activation scope `/4`绑定request `/5`；historical `/1`–`/3`不变。

P5只消费既有desired generation contribution。Requirement改变必须使target generated-video node及其真实typed downstream closure stale；Provider/profile/compiler-only变化不回写Shot或requirement，但必须改变resolved desired fingerprint。Unrelated Shot、Review或asset不得产生blanket invalidation。

## Old-Path Retirement

| Old path | Replacement | Retirement proof |
| --- | --- | --- |
| run-local prompt construction | Adapter compiler consumes sealed provider-bound request + neutral requirement | production search/import test无run script/caller prompt builder；only adapter compiler owns provider grammar |
| orchestration直接创建provider-bound `VideoGenerationRequest` | Planner -> requirement -> Router -> `ProviderBoundVideoRequest` -> adapter compile | production constructors for new `/5` require lineage；direct constructor remains only in explicit legacy `/1`–`/4` reopen fixtures |
| Adapter内隐式creative decision | deterministic mapping table + typed unsupported result | mutation/forbidden-default tests证明adapter不能删降requirement或选Provider |
| duplicate planner/router enums and manual projection | one explicit versioned projection table and exhaustive enum tests | each Planner mode/continuity/motion maps exactly once or blocks |

Implementation已删除production call sites的旧path；不得重新引入永久dual-write或shadow-run两套
truth。Compatibility fixtures可reopen历史requests，但不得用于创建新production attempts。

## Unchanged Contracts

以下全部保持不变：

- canonical Character / Scene / Shot schema and ownership；
- Asset Registry identity、provenance、selected revision与measured bytes；
- Shot Router Provider/profile/capability selection ownership和no-fallback rule；
- `ProductionStateCommitter` single writer、Manifest attempt lifecycle、candidate activation和explicit recovery；
- Paid Provider preview、budget、egress、secret reference、durable intent与one-use permit；
- Dependency Graph desired fingerprint、precise invalidation和rebuild frontier ownership；
- `ResolvedTimeline` order/frame/sample/timing ownership；
- HyperFrames renderer selection、P4 native-audio isolation与composition semantics；
- P6 Review/Repair、human Pilot Reality Gate与Final Acceptance；
- Legacy `0.1.x` CLI、Manifest v1、local-first ComfyUI default和flat run layout。

## Compatibility and Migration

### Ephemeral planner migration

- Historical `VideoPlanningRequest` / `VideoGenerationPlan video-planner/2` fixtures stay readable and hash-compatible，但不能进入new attempt path。
- New caller必须从current canonical inputs创建`VideoPlanningRequest video-planner/3` with typed generation intent；new Planner只对v3 request emit `VideoGenerationPlan video-planner/3` with embedded requirement。
- Current source accessors may delegate old field names to the nested requirement for one implementation checkpoint, but serialized duplicate fields are forbidden。
- Planning boundary验证v3 request/plan/requirement并签发cycle-neutral verified envelope；Router不importplanning package。
- v2 plans are not durable state；new boundary rejects them with typed stale/unsupported result and requires replanning。
- 后续独立的`ShotReadinessGate` slice已于commit
  `404facdb254115b79d156e5d42f2136b5510d800`实现，并消费v3 verified projection而不重新推导
  requirement；该gate不属于本slice，也不反向扩大本slice的ownership。

### Durable request migration

- Historical `VideoGenerationRequest` `/1`–`/4`、resolved request `/2`–`/5`和activation scope `/1`–`/3` hashes must reopen unchanged。
- New production attempts require request `/5`、resolved request `/6`和activation scope `/4` lineage；missing requirement/provider-bound/compiler hashes在durable intent前拒绝。
- No Manifest/Registry layout migration is required solely for the embedded ephemeral requirement；existing attempt serialization may carry additive request fields through the existing request envelope only after compatibility tests prove reopen。
- No automatic conversion of historical requests to `/5`；replay of historical attempts keeps historical hashes and zero external effects。

## Accepted T1-T9 Implementation Criteria

1. One current request deterministically produces one plan with one embedded requirement；same input bytes yield identical hashes。
2. Top-level plan generation fields are not serialized duplicates；compatibility properties read the nested requirement only。
3. Any Shot/intent/continuity/asset/Review identity change invalidates requirement and plan；diagnostic ID change does not。
4. Requirement recursively rejects all forbidden Provider/workflow/prompt/Skill/fallback/candidate fields。
5. Router is the only source of Provider/profile/capability identity and preserves exact no-fallback behavior。
6. `ProviderBoundVideoRequest` projection is deterministic and binds exact requirement, Router decision, assets, output and base pointers。
7. Fake adapter compiles supported requirements deterministically and returns typed unsupported results for every unexpressible field without side effects。
8. Local H3, cloud H3, Hailuo and Seedance offline mappings match current sealed capabilities, including role counting and adaptive/fixed output distinctions。
9. New request `/5`、resolved `/6`和activation scope `/4` lineage changes new fingerprints while all historical branches remain byte-identical。
10. Exact downstream invalidation is proven；unrelated Shot/assets remain fresh。
11. Production direct construction、run-local prompt builder和adapter creative-default paths are removed and protected by architecture tests。
12. Existing lifecycle, permit, unknown-outcome, activation, recovery, timeline, Review and Final Acceptance tests remain green。
13. Default acceptance uses fake/offline/no-network execution；no credential、Provider、ComfyUI或media generation occurs。
14. Exact staged/commit-range Harness receipt is fresh、passing、integrity-valid、policy-valid和snapshot-valid。

## Multi-Provider Assembly Criteria

以下是T11与Local H3 T8 family的current implementation acceptance；它不属于T1–T9历史receipt或
commit `15ef1d5`的已验证范围，必须由本slice的fresh receipt单独证明：

1. `VideoProviderRegistry`允许Local H3、Seedance、Hailuo、MiniMax H3和future distinct-name
   Providers并列exact lookup；duplicate exact name fail closed，且lookup不选择或fallback。
2. Local H3 family capabilities不包含remote variants；family只实现same-name local identity
   pass-through，绝不实现remote或cross-provider dispatch。
3. The sole `comfy-local-h3-t8` Registry entry can be injected into `VideoGenerationService` and routes
   Quality/Turbo preview/submit/status/fetch to the exact child by durable identity。
4. Fresh-family restart routes status/fetch to the same child without process-local last-selection state。
5. Exact source/test/canonical-doc snapshot取得fresh passing、integrity-valid、policy-valid、snapshot-valid Harness
   receipt后，才能声明target assembly complete。

## Acceptance Lanes

| Lane | What it can prove | What it cannot prove |
| --- | --- | --- |
| Pure/fake | model seals、determinism、freshness、unsupported results、zero side effects、old-path retirement | real Provider grammar acceptance、media or quality |
| Provider offline mappings | exact current capability/profile/payload projection for H3/Hailuo/Seedance | account access、billing、network、visual quality |
| Local H3 live, separately authorized | one exact compiled `/5` request reaches loopback adapter/lifecycle and matches Candidate 1 regression oracle boundaries | cloud portability、subjective universal quality、Candidate 2/3 |
| Cloud/paid live, separately authorized | one exact Provider/model/profile request passes paid gates and provider response | other Providers/models、fallback、Final Acceptance |

## Rollback

- Documentation status rollback只revert本次状态文字，不改变runtime。
- Implemented vertical slice在任何future live acceptance之外的rollback：revert
  requirement/Router/compiler integration as one unit；保留historical `/1`–`/4` reopen tests与
  existing lifecycle bytes。
- 若new `/5` attempt已durable begin，必须使用existing explicit recovery完成或fail closed；不得downgrade成legacy request、删除complete orphan evidence或恢复direct-construction path。
- Rollback不得重新引入automatic fallback、第二 requirement truth或adapter creative defaults。

## Design Review Decisions

本Spec已固定以下可能产生歧义的选择，implementation不得自行改写：

- schema model位于cycle-neutral Production contract module，semantic builder只属于Planner；
- requirement内嵌plan且不独立持久化；
- request/plan一起升级为v3；typed generation-intent projection禁止从prose猜测，并移除serialized duplicate generation fields；
- Planning签发cycle-neutral verified envelope；Router不importplan type；
- Router输出不含prompt的`ProviderBoundVideoRequest`；
- Adapter返回compiled或typed unsupported result；
- distinct-name Providers可并列存在；Registry exact lookup、Router selection、Service injection与Provider execution保持不同owners；
- Local H3 T8 family是provider-name-scoped完整local pass-through，不是global catalog或cross-provider execution façade；historical partial与current source/test truth必须明确区分；
- existing `VideoGenerationRequest`作为lifecycle DTO，以request `/5`、resolved `/6`、activation scope `/4`接入并保持全部历史hash；
- capability denial和adapter unsupported均fail closed，不触发fallback。

任何改变上述选择、引入Manifest schema/layout mutation、Provider ranking或新的quality owner，均是新的scope expansion，必须单独Spec与用户授权。
