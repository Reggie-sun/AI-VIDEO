# AI-VIDEO Local H3 T8 Quality/Turbo Provider Family Specification

## Status

Proposed v2 target contract。Local `main` commit
`15ef1d510a59cc9d46445b1fafff2ac2b34a1473` 已实现capability aggregation、
`compile_request()`与`resolve()`，但尚未实现本Spec要求的完整stateless
`LocalVideoProvider` execution façade，也未闭合Registry-to-Service runtime assembly。

本文件只描述`provider_name = "comfy-local-h3-t8"`的local child slice，不是全局Provider
selector、registry owner或lifecycle owner。Target family即使实现完整local seam，也只在该exact
provider name内按durable identity委托，不选择Seedance、Hailuo或其它Provider。

Canonical matrix 与 runtime baseline 已记录current partial implementation；本次文档修正时，workspace
中没有找到覆盖 exact implementation snapshot 且状态为 `passed` 的 Harness receipt。因此本文只把
source/test/workflow presence写成committed partial implementation truth，不把它升级为target contract
complete、fresh gate closure、
live media、quality acceptance、Final Acceptance、push 或 release truth。重新声明 offline acceptance
前必须对 exact implementation commit range 运行并验证 fresh Harness receipt。

本 Spec 是
`2026-08-21-ai-video-provider-neutral-generation-requirement.md` 的 provider-specific child spec。
跨 Provider coexistence、Router selection 与 assembly boundary 由该 parent spec 定义；本文件只约束
Local H3 T8 Quality/Turbo family 内部。

## Problem Boundary

`comfy-local-h3-t8` 在同一个 local runtime identity 下公开两条 T2VA lane：

- Quality：既有、无 LoRA、20 steps、`res_multistep`；
- Turbo：additive、exact Turbo LoRA、6 steps、`simple`。

它们共享一个 `provider_name`，但拥有不同 `capability_id`、`provider_kind`、`model_id`、
profile、workflow 与 runtime requirements。若把二者注册为同名 Provider objects、让 adapter 在
Router 后再次选 lane，或把 family 扩张为全局 Provider selector，会产生 duplicate registration、
silent fallback、identity drift 或第二套 lifecycle truth。

本 slice 只解决：

1. 在一个 provider-name-scoped capability snapshot 中 additive 暴露 Quality + Turbo；
2. 按 Router 已选择的 exact capability 委托 `compile_request()`；
3. 按 sealed resolved identity 委托 `resolve()`；
4. 让同一个registered family按durable resolved identity将完整local execution seam委托给
   exact selected child；
5. 保持具体 child adapter对Provider action的implementation ownership，同时由family提供无状态
   pass-through。

它不解决跨 Provider candidate discovery、global catalog、automatic Registry assembly、remote/local
cross-provider dispatch或Provider ranking；但它必须闭合`comfy-local-h3-t8`自身的exact-name
Registry-to-Service handoff。

## Architecture Context

```text
Provider-neutral requirement
  -> explicit candidate Provider capability snapshots
     ├── comfy-local-h3-t8: LocalH3VideoProviderFamily
     │    ├── Quality child
     │    └── Turbo child
     ├── seedance: SeedanceVideoProvider
     ├── minimax_hailuo: MiniMaxHailuoVideoProvider
     ├── minimax_h3: MiniMaxH3VideoProvider
     └── future distinct-name Providers
  -> Shot Router selects one exact provider/profile/capability
  -> selected adapter/family compiles and resolves
  -> exact registry entry is injected into existing local or remote lifecycle
  -> ProductionStateCommitter remains the only durable lifecycle/activation/recovery owner
```

`LocalH3VideoProviderFamily` 只存在于第一条 local branch 内。它不得吸收 Seedance、Hailuo、
MiniMax cloud H3 或 future distinct-name Provider，也不得拥有上图中的 candidate-set、Router、
Registry assembly 或 execution-kind dispatch。

## Goal

Local H3 T8 branch 的target唯一链路是：

```text
LocalH3VideoProviderFamily.capabilities()
  -> Shot Router selects exact Quality or Turbo capability
  -> LocalH3VideoProviderFamily.compile_request() delegates to selected child
  -> LocalH3VideoProviderFamily.resolve() delegates by exact sealed identity
  -> VideoGenerationService receives the same registered family
  -> family delegates preview/preflight/submit_local/status/fetch by durable identity
  -> selected child performs the exact Provider action
  -> VideoGenerationService + ProductionStateCommitter own durable lifecycle
```

必须保证：

- Quality 与 Turbo 是 additive siblings，不是 replacement、ranking 或 fallback order；
- Router 独占 exact Provider/profile/capability selection；
- family 是无durable state的完整`LocalVideoProvider` façade；
- family只做immutable lookup与identity-based pass-through，不实现Provider-native action logic；
- selected child实现具体preview/preflight/submit/status/fetch action；
- no availability/error/performance-based reselection；
- offline、local live、media/subjective acceptance严格分层。

## Non-Goals

- 不实现 global Provider catalog、automatic candidate discovery、Provider ranking 或 fallback；
- 不修改 `VideoProviderRegistry`、`VideoGenerationService` 或跨 Provider assembly；
- 不把 remote `VideoProvider` 与 local `LocalVideoProvider` 合并成新 protocol；
- 不修改 Seedance、Hailuo、MiniMax cloud H3 或其它 distinct-name Provider；
- 不修改或重新封装既有 Quality workflow/profile bytes；
- 不把 Turbo 设为 default、preferred、faster-is-better 或 quality-is-better route；
- 不安装/升级 T8、Turbo、ComfyUI、VideoHelperSuite、SageAttention、模型或 LoRA；
- 不改变 request/resolved request、Manifest、Registry 或 artifact layout schema；
- 不新增 credential、remote endpoint、cloud egress、paid permit 或 Provider API path；
- 不生成视频，不判断速度、显存、画面锐度、motion、identity、continuity 或 audio quality；
- 不修改 Legacy `0.1.x` CLI、Manifest 或 local-first semantics。

## Current Source Truth

Commit `15ef1d5` contains：

- `ComfyUIT8VideoProvider` Quality child；
- `ComfyUIT8TurboVideoProvider` Turbo child；
- `LocalH3VideoProviderFamily` capability aggregation、compile dispatch 与 resolve dispatch；
- Turbo workflow/template/profile/binding seals；
- focused Quality/Turbo/family/Router/provider-neutral tests；
- package exports、Harness routing、contract matrix 与 runtime baseline updates。

Current family source只定义：

- `capabilities()`；
- `compile_request()`；
- `resolve()`。

它没有实现 `preview()`、`submit_local()`、`get_local_status()` 或 `fetch_local()`，也没有production
wiring将family作为完整`LocalVideoProvider`传给`VideoGenerationService`。因此commit `15ef1d5`
只闭合offline capability/compiler/resolver slice；full runtime assembly仍是本Spec与Plan中的明确
implementation blocker，不得描述成已经完成或intentional final boundary。

## Ownership Model

| Concern | Single owner | This slice rule |
| --- | --- | --- |
| Provider-neutral intent | Planning / requirement owners | 不加入 T8/Turbo grammar |
| Cross-Provider candidate set | explicit caller/orchestration input | family 不发现或加入其它 Providers |
| Provider/profile/capability selection | Shot Router | exact selection；denial不 fallback |
| Local T8 capability aggregation and action dispatch | `LocalH3VideoProviderFamily` | 合并同名child snapshots，并按durable identity原样委托完整local seam；无durable state |
| Provider-native compile/resolve | selected Quality/Turbo child through family | family按 exact capability/identity委托 |
| Preview/preflight/local submit/status/fetch implementation | selected Quality/Turbo child | family只做identity pass-through，不重写inputs/outputs |
| Exact Provider lookup | `VideoProviderRegistry` | exact-name lookup only；不选择、不 fallback |
| Durable lifecycle | `VideoGenerationService` + `ProductionStateCommitter` | 不新增 writer、attempt table 或 recovery path |
| Quality/Final Acceptance | P6 Review/Repair + human gate | offline tests不判质量 |

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

Identity tuple必须为：

```text
(provider_kind, model_id, profile_version, mode)
```

`capability_id` 与 identity tuple 在一个 family snapshot 内必须分别唯一。duplicate、empty family、
foreign `provider_name`、unknown capability 或 unknown identity都必须 fail closed。

## Provider Family Contract

`LocalH3VideoProviderFamily` target public responsibilities只有：

1. `capabilities()`：合并同属 `comfy-local-h3-t8` 的 child variants并按
   `capability_id` deterministic排序；
2. `compile_request()`：按 Router 已选择的 `capability_id` 委托给唯一 child；
3. `resolve()`：按 exact identity tuple 委托给唯一 child；
4. `preview()`与`preflight()`：从sealed resolved request identity选择同一child并原样委托；
5. `submit_local()`：从request/preview/intent/permit绑定的exact identity选择同一child并原样委托；
6. `get_local_status()`与`fetch_local()`：从durable `LocalVideoSubmission.resolved` identity
   选择同一child并原样委托。

Family MUST NOT：

- 保存process-local last-selected child、attempt phase、permit、task ID、poll result、artifact locator、activation或
  recovery truth；
- 修改或重新签发child inputs、outputs、permit、submission、observation或fetch receipt；
- 按 runtime availability、性能、错误类型、插入顺序或历史成功率重新选 child；
- 聚合不同 `provider_name` 的 capabilities；
- 充当 `VideoProviderRegistry`、global catalog 或 cross-provider execution dispatcher。

## Multi-Provider Coexistence Contract

`VideoProviderRegistry` 是 exact injected lookup，可同时包含：

```text
("comfy-local-h3-t8", <LocalH3VideoProviderFamily>)
("seedance", <SeedanceVideoProvider>)
("minimax_hailuo", <MiniMaxHailuoVideoProvider>)
("minimax_h3", <MiniMaxH3VideoProvider>)
(<future-distinct-name>, <future provider>)
```

“唯一”只表示：同一个 `provider_name = "comfy-local-h3-t8"` 不能同时注册 Quality child、
Turbo child 与 family形成 duplicate entries。它不表示 global Registry 只能有一个 Provider。

Registry 不做 selection、execution-kind dispatch 或 fallback；`VideoGenerationService`也不会自行
查询Registry。Existing explicit caller必须按durable `request.provider_name`获得exact registered
Provider object，并按sealed `execution_kind`使用local或remote lifecycle seam。对
`comfy-local-h3-t8`，该registered object必须是完成本Spec target contract的family；当前partial
implementation尚不满足这一assembly requirement。

## Profile and Workflow Sealing

- Quality profile/workflow/binding bytes与existing hashes保持不变；
- Turbo template、binding与profile互相 seal exact bytes；
- Turbo固定 T8 runtime、Turbo plugin、四组件、exact LoRA、node inventory、node input schema、
  output node `13`、H.264 MP4/native audio/CRF 17；
- both lanes保持 literal loopback-only origin、`remote_provider_enabled=false` 与
  `cloud_fallback_enabled=false`；
- output history必须唯一选择 profile-declared output node中的一个 final `*-audio.mp4`；
  wrong node、video-only sibling、zero/duplicate final AV、wrong suffix或ambiguous locator fail closed。

## Execution and Lifecycle Contract

Router/family acceptance不执行 ComfyUI。进入 local execution 时：

1. explicit assembly按provider name注入registered family；
2. `VideoGenerationService` reopen durable resolved request；
3. family按durable identity委托selected child执行preview/preflight与local permit-gated submit；
4. family在restart后的status/fetch阶段继续从durable submission identity委托同一child；
5. `ProductionStateCommitter`独占durable intent、permit、state、candidate、activation与recovery。

Turbo failure不得切换Quality，Quality failure不得切换Turbo；local failure不得切换Seedance、Hailuo或
其它 remote Provider。Unknown outcome继续使用existing typed fail-closed recovery，不 blind retry、
remint permit或手工激活 output。

## Compatibility and Migration

- 不需要 Manifest、Registry、request、resolved request 或 artifact layout migration；
- historical Quality attempts、hashes与profile继续reopen/replay；
- new Turbo attempt必须由current requirement + Router exact selection创建；
- public package exports只做 additive exposure；
- Seedance、Hailuo、MiniMax H3 identities、profiles、permits与historical evidence不变；
- Base AI Comic E2E 在没有 Video Provider时仍必须可运行；
- current family尚未实现完整的local lifecycle façade；target family也永远不是global Provider registry。

## Acceptance Criteria

1. Quality profile bytes、identity与focused tests保持不变。
2. Turbo profile/workflow/binding exact seal，并拒绝 runtime、component、LoRA、node或output drift。
3. Family deterministic暴露Quality + Turbo，拒绝empty、foreign、duplicate与unknown identity。
4. Router对两条lane都要求explicit capability selection；denial不fallback。
5. Family对compile/resolve和完整local execution seam都只做identity-based pass-through；不得保存durable state。
6. Selected child继续实现具体local action logic；family可作为sole `comfy-local-h3-t8` Registry entry注入`VideoGenerationService`。
7. A pure coexistence regression应证明同一 Registry可同时保存Local H3、Seedance、Hailuo与其它
   distinct-name fake Providers，exact name返回exact object，duplicate name fail closed，且不调用runtime。
8. Family capability snapshot不得混入remote Provider variants。
9. Fresh-family restart必须从durable resolved identity把status/fetch路由回同一child，不依赖last-selected state。
10. No schema、global catalog、automatic selection、ranking或fallback change。
11. Exact target implementation snapshot必须取得fresh passing Harness receipt后才能声明contract complete。

## Acceptance Lanes

| Lane | Can prove | Cannot prove |
| --- | --- | --- |
| Pure/profile | schema、hash、identity、determinism、coexistence lookup | runtime、submit、media |
| Fake/offline compiler | Router selection、family compile/resolve dispatch、unsupported/no-fallback | complete family lifecycle、GPU、media |
| Family lifecycle regression | full identity pass-through、restart same-child、existing child semantics | live quality |
| Local live technical, separate task | exact loopback profile produces measured artifact | universal quality、default ranking |
| Controlled A/B, separate task | fixed-input Quality vs Turbo comparison | other providers or default selection |

## Explicitly Unverified

- fresh passing Harness closure for exact commit `15ef1d5`；
- complete Registry-to-`VideoGenerationService` wiring for this family；
- family preview/submit/status/fetch pass-through and restart proof；
- real T8/Turbo/ComfyUI compatibility and installed bytes；
- Turbo live submit/status/fetch、wall time、VRAM/RAM或media quality；
- Turbo是否优于Quality或适合成为default；
- any new Seedance/Hailuo/MiniMax H3 live behavior。

## Rollback

- 本次文档修正可通过只撤销对应 docs commit回滚，不改变runtime。
- Implementation rollback必须整体移除Turbo/family/additive exports/policy/docs delta，同时保留
  Quality child、historical evidence与其它 Providers。
- 已经durable begin的attempt只能走existing explicit recovery；不得改写为另一lane或Provider。

## Design Decisions

- Local H3 family是 provider-name-scoped、stateless、完整local provider façade，不是global Provider family；
- Quality/Turbo共享provider name但使用distinct explicit capability identities；
- Registry可并列保存多个distinct-name Providers；
- Router selects；family aggregates and identity-dispatches；selected child executes；committer persists；
- no ranking、no fallback、no runtime availability selection；
- local与remote seams保持分离；
- current assembly尚未闭合，是future implementation blocker；
- live/media/quality均需要独立evidence。

修改 Seedance/Hailuo/其它Provider本身、引入global catalog、automatic assembly、cross-provider ranking/
fallback、新schema或第二lifecycle owner，都是独立scope；但这些 Providers 的既有共存不是future
scope expansion，而是必须保持的unchanged architecture contract。
