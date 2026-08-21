# AI-VIDEO Local H3 T8 Quality/Turbo Provider Family Specification

## Status

Proposed v1；docs-only specification。本文件描述当前 Local MiniMax H3 T8/T2VA
Quality + Turbo lane 的目标合同与验收边界，不声明 working-tree draft 已完成，不授权
修改 source/test/workflow，不启动 ComfyUI，不生成媒体，也不构成主观质量、P6 Review、
Final Acceptance、push 或 release truth。

Source snapshot：既有 Quality adapter 由 commit `e10c494` 引入；Turbo adapter、
`LocalH3VideoProviderFamily`、对应 workflow/profile/tests 与 canonical docs/policy 在写本文时
仍属于并发 working-tree implementation lane。只有 exact staged snapshot 或 exact commit range
取得 fresh passing Harness receipt 后，才能把对应实现写成 accepted runtime truth。

## Problem Boundary

`comfy-local-h3-t8` 已有一条显式 Quality T2VA capability。当前 draft 又增加 Turbo T2VA，
两条 lane 共享 local H3/T8 runtime family，但具有不同 model/profile identity、sampling graph、
step count 与 LoRA requirement。

如果直接用一个 adapter 替换另一个，或让 Router 只看到模糊的 provider-level capability，
会产生以下风险：

- Turbo 静默覆盖已经 sealed 的 Quality profile；
- Router 选择 provider 后由 adapter 再决定 Quality/Turbo，形成第二个 selector；
- capability mismatch 自动 fallback，破坏 exact selection；
- family wrapper 扩张为第二套 submit/status/fetch/recovery lifecycle owner；
- offline workflow/schema tests 被错误外推为真实 ComfyUI compatibility、媒体质量或音画验收。

本 slice 只解决一个边界：在同一个 provider name 下 additive 暴露两个显式、互不歧义的
capability，并把 selected child 一直保持到既有 local-video lifecycle。它不扩大 T8 upstream
runtime 的 ownership，也不采用 upstream Long Video、Studio、Repair、Reel、Context IR
Provider 或其它 advanced/experimental subsystem。

## Goal

建立唯一链路：

```text
ProviderNeutralVideoRequirement
  -> Shot Router selects one exact capability
     -> LocalH3VideoProviderFamily compile/resolve produces one exact resolved request
        -> existing VideoGenerationService uses the family as one registered provider
           -> family dispatches each LocalVideoProvider action to the exact child
              -> existing ProductionStateCommitter owns lifecycle/activation/recovery
```

该链路必须保证：

- Quality 与 Turbo 是 additive siblings，不是 replacement、ranking 或 fallback 顺序；
- Router 继续独占 Provider/profile/capability selection；
- family 是无durable state的dispatch façade，并按 exact identity委托完整local provider seam；
- selected child 继续消费 existing durable local permit并执行具体Provider action；
- existing Manifest、Registry、Dependency Graph、Timeline、Review/Repair 与 activation owner不变；
- offline contract acceptance、local live technical proof、media/subjective acceptance严格分层。

## Non-Goals

- 不修改或重新封装既有 `minimax_h3_t8_t2va_quality_local` bytes；
- 不把 Turbo 设为 default、preferred、faster-is-better 或 quality-is-better route；
- 不实现 Provider ranking、automatic selection、fallback、retry或multi-candidate generation；
- 不安装/升级 T8、Turbo、ComfyUI、VideoHelperSuite、SageAttention、模型或 LoRA；
- 不启用 upstream Long Video、Studio、Repair、Reel、Context IR Provider、speech、
  multi-keyframe、Prompt Relay 或 Advanced/EXP routes；
- 不改变 `VideoGenerationRequest`、resolved request、Manifest、Registry 或 artifact layout schema；
- 不新增 credential、remote endpoint、cloud egress、paid permit或Provider API path；
- 不生成视频，不判断速度、显存、画面锐度、motion、identity、continuity或audio quality；
- 不修改 Legacy `0.1.x` CLI、Manifest或local-first semantics。

## Current Source Truth

### Accepted base

- `src/ai_video/production/comfy_t8_video.py` 定义 sealed Quality child
  `ComfyUIT8VideoProvider`。
- Quality profile只公开 `minimax-h3-t8-t2va-quality-v1`，固定
  `1344x768`、124 frames、24 fps、native audio、20 steps、
  `res_multistep` + `simple`、CRF 17、无 LoRA、loopback-only。
- existing local-video request、durable permit、status、fetch、activation、replay与explicit
  recovery contracts已经存在；本 slice 不建立替代实现。

### Draft additions

- `src/ai_video/production/comfy_t8_turbo_video.py` 定义 Turbo child draft；
- `src/ai_video/production/local_h3_provider_family.py` 定义 Router-facing family draft；
- `workflows/{templates,bindings,profiles}/minimax_h3_t8_t2va_turbo*` seal Turbo graph；
- focused tests覆盖 Turbo profile/preflight/submit/positive status-fetch与family exact dispatch；
- Harness policy、contract matrix、runtime baseline与Production package exports正在同步。

这些 file presence 只证明 draft surface 存在。它们不证明 tests passing、real runtime
compatibility、negative status/fetch matrix、media generation 或 quality acceptance。

## Ownership Model

| Concern | Single owner | This slice rule |
| --- | --- | --- |
| Provider-neutral generation intent | current Planning / requirement owners | 不加入T8/Turbo字段或Provider grammar |
| Provider/profile/capability selection | Shot Router | 必须选择exact Quality或Turbo capability；denial不fallback |
| Capability aggregation and in-memory action dispatch | `LocalH3VideoProviderFamily` | 组合、排序、校验并按sealed identity委托；无durable state、无fallback |
| Provider-native compile/resolve | selected Quality或Turbo child | 只能表达selected capability；不能换lane |
| Workflow/profile/preflight | selected child + exact sealed artifacts | exact bytes、runtime inventory、node schema在submit前fail closed |
| Preview/submit/status/fetch implementation | selected child | family只做same-child pass-through；不得改写request、permit、observation或artifact |
| Durable local permit/lifecycle | existing `VideoGenerationService` + `ProductionStateCommitter` | 不新增writer、attempt table或recovery path |
| Candidate validation/activation | existing P8/P5 owners | fetch不等于activation |
| Media/quality acceptance | P6 Review/Repair + human gate | offline adapter acceptance不判质量 |

## Capability Contract

| Field | Quality lane | Turbo lane |
| --- | --- | --- |
| `provider_name` | `comfy-local-h3-t8` | `comfy-local-h3-t8` |
| `capability_id` | `minimax-h3-t8-t2va-quality-v1` | `minimax-h3-t8-t2va-turbo-v1` |
| `provider_kind` | `minimax_h3_t8_t2va` | `minimax_h3_t8_t2va_turbo` |
| `model_id` | `minimax-h3-t8-t2va-quality` | `minimax-h3-t8-t2va-turbo` |
| `profile_version` | `v1` | `v1` |
| `mode` | `TEXT_TO_VIDEO` | `TEXT_TO_VIDEO` |
| `execution_kind` | `LOCAL` | `LOCAL` |
| `billing_kind` | `LOCAL_UNMETERED` | `LOCAL_UNMETERED` |
| Output | `1344x768`, 124 frames, 24 fps, MP4, native audio | same |
| Sampling | 20 steps, `res_multistep`, `simple` | 6 steps, Turbo sampler, `simple`, denoise 1.0 |
| LoRA | none | exact `minimax_h3_turbo_v4_step600_ema.safetensors`, strength 1.0, `low_vram=false` |
| Output node | `11` | `13` |
| Encoder | H.264 MP4, CRF 17 | H.264 MP4, CRF 17 |
| Remote/fallback | disabled | disabled |

两条 lane 的 identity tuple 必须按以下 exact key保持唯一：

```text
(provider_kind, model_id, profile_version, mode)
```

`capability_id` 在一个 family capability snapshot 内也必须唯一。任何 duplicate capability ID 或 duplicate identity tuple
在 family construction 时返回 non-retryable `VIDEO_REQUEST_INVALID`，不得按插入顺序选一个。

## Provider Family Contract

`LocalH3VideoProviderFamily` 是同一个 `provider_name` 的唯一 registered provider façade，并实现
完整 `LocalVideoProvider` seam。它只允许以下 public responsibilities：

1. `capabilities()`：合并所有 child variants，并按 `capability_id` deterministic排序；
2. `compile_request()`：以 Router 已选的 `capability_id` 委托给唯一 child；
3. `resolve()`：以 exact identity tuple 委托给唯一 child；
4. `preview()`、`preflight()`与`submit_local()`：从sealed resolved request identity选择同一个
   child实例并原样委托；
5. `get_local_status()`与`fetch_local()`：从`LocalVideoSubmission.resolved`的sealed identity选择
   同一个child并原样委托。

`VideoProviderRegistry`只注册一次`("comfy-local-h3-t8", family)`；不得用相同provider name分别
注册Quality和Turbo child。`VideoGenerationService`接收family作为完整`LocalVideoProvider`，从
durable request reopen得到的identity在submit、restart后的status与fetch阶段都必须路由回同一个
child profile。Family可以持有immutable child lookup与child实例，但不得保存attempt phase、permit、
task ID、poll result、artifact locator、activation或recovery truth。

Family 必须 fail closed：

- children为空；
- child `provider_name` 不是 `comfy-local-h3-t8`；
- duplicate capability ID；
- duplicate identity tuple；
- request来自另一个 provider；
- selected capability或request identity不存在。

Family只允许执行identity-based pass-through，MUST NOT在委托前后重写Provider inputs/outputs，
也MUST NOT保存permit、provider task ID、poll history、artifact locator、activation或recovery
state。任何phase都不得在resolve后按性能、runtime availability、错误类型或插入顺序重新选择
另一个child。Family restart必须从durable resolved identity重建同一dispatch，不依赖process-local
“last selected child”。

## Profile and Workflow Sealing

### Quality preservation

- existing Quality profile/workflow/binding bytes与capability identity保持不变；
- Turbo不得复用Quality capability ID、`provider_kind`或`model_id`；
- Turbo adoption test必须固定Quality profile file SHA-256，证明新增lane没有re-seal旧lane；
- Quality tests必须与Turbo/family tests一起运行。

### Turbo seal

Turbo profile必须至少绑定：

- exact T8 repository/commit/version/license；
- exact Turbo repository commit `4274783a23afcfdbea3b4876cb79effd6c510785`、
  version `1.2.3`与Apache-2.0 metadata；
- exact ComfyUI、VideoHelperSuite、SageAttention identities；
- exact four H3 model components与Turbo LoRA size/SHA-256；
- exact workflow/binding bytes；
- exact custom-node input schema hash；
- loopback endpoints、launch capabilities、dimensions、frames/fps、native audio、steps、
  scheduler、denoise、CRF、output node与final AV suffix；
- `remote_provider_enabled=false`、`cloud_fallback_enabled=false`。

`required_turbo_nodes` 只表示需要做input-schema hash的四个T8/Turbo custom nodes：
`MiniMaxH3AudioConditioningT8`、`MiniMaxH3TurboLoRA`、
`MiniMaxH3TurboSampler`、`MiniMaxH3AVDecodeT8`。完整 `required_nodes` 可以包含该
sealed workflow实际使用的ComfyUI/VHS core nodes，但任何增删都必须更新exact profile、
workflow seal与tests，不能在runtime动态扩张。

### Upstream ownership exclusion

T8 upstream是GPL-3.0-or-later runtime reference；Turbo plugin metadata是Apache-2.0。
AI-VIDEO adapter必须保持project-native implementation，不复制或分发未审查的upstream
implementation。即使对应custom nodes已安装，也不得消费upstream自带Manifest、Timeline、
Repair、Studio、delivery或external-provider state。

## Execution and Lifecycle Contract

Family + selected child必须继续满足existing local provider seam：

```text
resolve
  -> preview
  -> preflight exact runtime/components/nodes
  -> ProductionStateCommitter records durable local submit intent
  -> family dispatches to exact child
  -> selected child consumes one-use local permit immediately before submit
  -> status observation
  -> held-FD fetch and measured artifact validation
  -> explicit candidate validation/activation
  -> reopen / exact replay / explicit recovery
```

Quality/Turbo child可以共享implementation helper或inherit stable behavior，但动态字段必须读取
`self.profile`。Turbo继承的 status/fetch path必须使用Turbo `output_node_id="13"`与
`final_av_filename_suffix="-audio.mp4"`，不得硬编码Quality node `"11"`。

当前 source中 `_final_av_artifact(history, self.profile)` 已按实例profile选择output node，且
current Turbo focused test已经覆盖node `13` terminal history -> succeeded observation -> fetch receipt
的positive path。Future acceptance仍必须补齐wrong node、video-only sibling、zero/duplicate final AV、
wrong suffix与ambiguous locator的fail-closed negative matrix；positive path本身不得再描述为缺失。

Unknown submit/poll outcome继续使用existing typed fail-closed behavior；不得因Turbo失败自动切换
Quality、remint permit、blind resubmit或手工激活某个ComfyUI output。

## Compatibility and Migration

- 不需要Manifest、Registry、request、resolved request或artifact layout migration；
- existing Quality attempts、hashes、profile与capability继续reopen和replay；
- new Turbo attempt必须从current requirement和Router exact selection创建，不能把historical
  Quality request改写成Turbo；
- public package exports可以additive暴露Turbo/family types，但不得移除Quality exports；
- Harness policy必须覆盖Turbo source/tests/workflow/profile/binding与family path；
- runtime baseline只能在exact implementation receipt通过后写为offline accepted；在此之前
  应明确标记working-tree draft或proposed。

## Acceptance Criteria for Future Implementation

1. Existing Quality profile bytes、file SHA-256、capability identity与focused tests保持不变。
2. Turbo profile/workflow/binding exact互相seal，并拒绝path、hash、component、LoRA、runtime
   identity、node inventory或input schema drift。
3. Turbo只公开一个distinct explicit local/unmetered T2VA capability；不公开remote/fallback。
4. Family deterministic暴露Quality + Turbo，拒绝empty、foreign provider、snapshot内duplicate ID与
   duplicate identity。
5. Router对Quality与Turbo都必须要求explicit capability selection；missing或wrong capability
   typed BLOCKED且不fallback、不触发runtime inspection。
6. Family compile只委托selected capability owner；resolve与每个local provider action只委托
   durable identity对应的同一个child，并可作为唯一`comfy-local-h3-t8` registration传给
   `VideoGenerationService`。
7. Quality child拒绝Turbo request，Turbo child拒绝Quality request；不能相互吸收。
8. Turbo preflight在permit/submit前验证exact runtime、四组件、LoRA与node schema；任何drift
   保持zero submit effect。
9. Turbo render固定6 steps、`simple`、denoise 1.0、exact LoRA、T2VA、native audio、
   `1344x768`、124 frames、24 fps、CRF 17和output node `13`。
10. Turbo offline lifecycle tests保留现有node `13` positive status/fetch proof，并证明video-only
    sibling不构成成功；wrong node、zero/duplicate final AV、wrong suffix或ambiguous locator fail closed。
11. Existing local durable intent、one-use permit、status/fetch、activation、reopen、replay与
    recovery tests保持green；family不出现第二套state。
12. Production exports、contract matrix、runtime baseline与Harness path mapping准确同步；docs不把
    offline acceptance写成live或quality truth。
13. Default acceptance全部pure/fake/offline/no-network；不读credential、不启动ComfyUI、
    不生成媒体。
14. Independent review无blocking issue；exact staged snapshot或commit range取得fresh passing、
    integrity-valid、policy-valid、snapshot-valid Harness receipt。

## Acceptance Lanes

| Lane | Can prove | Cannot prove |
| --- | --- | --- |
| Pure/profile | schema、hash、identity、workflow binding、determinism、fail-closed | installed runtime compatibility、submit、media |
| Fake/offline lifecycle | Router selection、selected-child dispatch、permit、node 13 status/fetch、replay/recovery | GPU、wall time、VRAM、real audio/video |
| Local live technical, separate explicit execution task | one exact loopback runtime/profile succeeds with measured MP4/audio evidence | universal quality、Turbo better than Quality、Final Acceptance |
| Controlled media A/B, separate task | fixed-input Quality vs Turbo measurements and human verdict | other prompts/assets/hardware or default ranking |

用户当前只要求spec/plan，因此本轮停在docs-only lane。未来Local ComfyUI execution若由用户明确
要求，可按repository的local-unmetered authorization exemption执行，但仍必须完成sealed profile、
preflight、permit、lifecycle、recovery与media verification gates；该exemption不是本Spec的live授权。

## Explicitly Unverified

- T8 `1.36.2`、Turbo `1.2.3`与本机ComfyUI exact commit的真实compatibility；
- real model/LoRA bytes与profile declarations是否匹配当前host；
- real `/object_info`是否匹配sealed custom-node input schema；
- Turbo submit/status/fetch是否在真实host成功；
- actual wall time、VRAM/RAM、audio sync、motion、identity、continuity、sharpness或stability；
- Turbo是否比Quality更快、更好或更适合作为默认lane；
- `1344x768`相对既有`1344x672`quality lane的受控收益。

上述事实只能由后续fresh runtime/media evidence补充，不得由unit tests、profile file、upstream claim、
larger bitrate或历史Quality evidence推断。

## Rollback

- Docs-only rollback：删除本Spec与配套Plan；runtime无变化。
- Future offline implementation rollback：删除Turbo adapter/family/workflow/profile/tests及additive
  exports/policy/docs delta；必须保留Quality adapter/profile/workflow/binding与所有历史evidence。
- 若Turbo attempt已经durable begin，只能使用existing explicit recovery记录known-no-effect、failed
  或outcome-unknown；不得通过rollback删除complete orphan evidence、改写成Quality attempt或blind
  retry。
- Rollback不得引入automatic fallback、第二lifecycle owner或remote endpoint。

## Design Decisions

本Spec固定以下选择：

- shared provider name + distinct explicit capability identities；
- family是唯一registered、无durable state的完整`LocalVideoProvider` dispatch façade；
- child执行具体Provider action，committer拥有durable lifecycle；
- Quality bytes保持不变，Turbo是additive profile；
- exact identity tuple为`provider_kind + model_id + profile_version + mode`；
- no ranking、no fallback、no runtime availability selection；
- offline acceptance必须补Turbo node 13 status/fetch fail-closed negative matrix；
- upstream second-truth subsystems永不进入AI-VIDEO production truth；
- live technical proof与Quality-vs-Turbo A/B均是独立future execution task。

任何改变这些选择、启用remote/external-provider route、修改Manifest/Registry/request schema、引入
default ranking或把family扩张为lifecycle owner，均是新的scope expansion，必须单独Spec与用户授权。
