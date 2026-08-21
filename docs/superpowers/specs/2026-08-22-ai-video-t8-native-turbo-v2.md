# AI-VIDEO T8-Native H3 Turbo V2 Provider Specification

## Status

Proposed，spec-only。本文定义后续窗口可实施的 additive `T8-native Turbo v2` target；当前没有实现、测试、Harness receipt、local live smoke、media quality acceptance、push 或 release truth。

本 Spec 是 `2026-08-21-ai-video-local-h3-t8-provider-family.md` 的 provider-specific child。现有 `comfy-local-h3-t8` Quality lane 与 hybrid Turbo v1 仍是当前 runtime truth；本文不得被引用为它们已经迁移或退役的证据。

## Goal

在现有 `provider_name = "comfy-local-h3-t8"` family 内新增一条显式、sealed、local-only 的 T8-native Turbo capability，使：

- Larry 只提供 Turbo LoRA weight provenance；
- T8 独占 H3 audio/video conditioning、双时钟 sampling setup 与 AV decode；
- ComfyUI `SamplerCustomAdvanced` 只执行 T8 输出的唯一 sampler/sigma contract；
- Shot Router 继续独占 provider/profile/capability selection；
- 现有 local permit、status/fetch、`ProductionStateCommitter` 与 recovery lifecycle 原样复用；
- 当前 hybrid Turbo v1 保持可重放、可恢复且不被静默替换。

目标 backbone：

```text
MODEL path
UNETLoader (non-pruned H3 INT8 ConvRot)
  -> LoraLoaderBypassModelOnly (T8-converted Larry Turbo LoRA)
  -> MiniMaxH3DualClockSamplerT8.model
  -> MiniMaxH3DualClockSamplerT8.model output
  -> BasicGuider.model

CONDITIONING / LATENT path
CLIPLoader + video VAE + audio VAE
  -> MiniMaxH3AudioConditioningT8
     ├── positive -> BasicGuider.conditioning
     └── av_latent -> MiniMaxH3DualClockSamplerT8.av_latent
                   -> SamplerCustomAdvanced.latent_image

SAMPLING / OUTPUT path
MiniMaxH3DualClockSamplerT8
  ├── sampler -> SamplerCustomAdvanced.sampler
  ├── sigmas  -> SamplerCustomAdvanced.sigmas
  └── model   -> BasicGuider.model
RandomNoise + BasicGuider + av_latent
  -> SamplerCustomAdvanced
  -> MiniMaxH3AVDecodeT8
  -> VHS_VideoCombine
  -> final video + native audio MP4
```

## Problem Boundary

当前 Turbo v1 是一个明确 sealed 的 compatibility hybrid：

```text
MiniMaxH3AudioConditioningT8
  -> MiniMaxH3TurboLoRA
  -> MiniMaxH3TurboSampler
  -> SamplerCustomAdvanced
  -> MiniMaxH3AVDecodeT8
```

它使用 `minimax_h3_fl2va_pruned_int8_convrot.safetensors`、Larry custom LoRA node、Larry custom sampler、6 steps 与 `simple` scheduler。Larry sampler 在支持 native `ModelSamplingAV` 的新 ComfyUI 上会退化为 single-schedule behavior，因此现有结果不能仅凭结构认定为损坏；但该 lane 仍让 Larry plugin参与 runtime sampling，并非 T8 官方 Stable 4V4A graph。

T8 `1.36.2` 的官方 stable graph和 converter给出另一条明确路径：

- converter 将 Larry H3 Turbo LoRA 转为 native ComfyUI-prefixed keys；
- converted LoRA 通过 `LoraLoaderBypassModelOnly` 应用；
- `MiniMaxH3DualClockSamplerT8` 独占 `steps`、video/audio shifts、sampler 与 scheduler；
- `SamplerCustomAdvanced` 直接消费 T8 node输出；
- graph 不包含 Larry sampler、external scheduler 或第二个 sigma owner。

关键兼容性约束是：T8 的普通 converted Larry LoRA声明兼容 non-pruned H3 BF16 / INT8 ConvRot base，并明确拒绝 `pruned_*` base。后续实现不能只替换 sampler而继续复用当前 v1 pruned model；model、converted LoRA、workflow与profile必须作为一个新 seal整体引入。

## Authoritative Upstream Baseline

第一版 implementation 必须以以下 exact upstream evidence 为 baseline，不从 UI截图、历史 run script或当前 hybrid v1反推：

- T8 repository：`https://github.com/T8mars/comfyui-minimax-h3-audio-T8`
- T8 commit：`977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`
- T8 version：`1.36.2`
- Stable workflow：`examples/workflows/01-basic-generation/2026-08-06_H3_Turbo_Stable_4V4A.json`
- Converter：`tools/convert_minimax_h3_lora_for_comfyui.py`
- Larry node repository comparison baseline：`https://github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo`
- Larry node commit：`4274783a23afcfdbea3b4876cb79effd6c510785`

Implementation preflight 必须重新计算并 seal upstream workflow、converter、local workflow/template/binding/profile 和 installed runtime bytes 的 exact SHA-256。仅有 repository commit 或 filename 不足以证明 local bytes identity。

AI-VIDEO 只提交自身 adapter、tests、workflow data和profile seal；不得复制 T8 GPL implementation或 Larry node implementation。Converted LoRA 与模型只作为本机 runtime assets，不得提交 repository。

## Architecture Decisions

### Single Sampling Owner

V2 graph 必须只有一个 sampling-policy owner：`MiniMaxH3DualClockSamplerT8`。

固定 stable settings：

| Field | Value |
| --- | --- |
| `steps` | `4` |
| `shift_video` | `12.0` |
| `shift_audio` | `3.0` |
| `sampler_name` | `dual_clock_euler` |
| `scheduler` | `native_flow` |

V2 workflow 禁止包含：

- `MiniMaxH3TurboSampler`；
- `MiniMaxH3TurboLoRA`；
- `BasicScheduler`；
- `KSamplerSelect`；
- `MiniMax H3 Sigma Shift` 或等价 external sigma/scheduler node；
- 第二个 `MiniMaxH3DualClockSamplerT8`；
- 任何把 Larry sampler输出再输入 T8 sampler，或把 T8 sampler输出再交给另一个 sampler-policy node 的链路。

`SamplerCustomAdvanced` 是 execution node，不是第二个 policy owner；它必须原样消费同一个 T8 dual-clock node输出的 `sampler` 和 `sigmas`。

### Model And LoRA Compatibility

V2 baseline model必须是 non-pruned：

```text
minimax_h3_fl2va_int8_convrot.safetensors
```

V2 baseline LoRA必须是 T8 converter输出的 native ComfyUI-key artifact，当前本机候选 filename 为：

```text
minimax_h3_turbo_4步加速ema_comfyui.safetensors
```

Conversion/build verification 必须 seal：

- exact base model size和SHA-256；
- exact source Larry LoRA repository/revision/filename/size/SHA-256；
- exact T8 converter commit、converter file SHA-256 与 conversion contract version；
- converted LoRA filename、size、SHA-256 和 metadata identity；
- conversion当次的source/output tensor count、key-set validation和value-identity evidence；
- `LoraLoaderBypassModelOnly` input schema；
- `strength_model = 1.0`。

Source LoRA 不要求永久保留在ComfyUI runtime tree。Runtime preflight只验证converted LoRA的exact size/hash、518-tensor key/schema、metadata中绑定的source hash与converter identity，以及bypass loader input schema；它不得在每次submit时重新执行conversion、要求source LoRA仍在场，或创建新的durable receipt/lifecycle owner。Conversion时的bit/value identity由converter和offline verification证明，runtime只消费其sealed结果。

Preflight 必须拒绝：

- any `pruned_*` base；
- unconverted Larry key layout；
- regular/folding LoRA loader substituted for the bypass loader；
- converted LoRA source/hash/metadata drift；
- LoRA strength drift；
- unknown、duplicate或ambiguous LoRA artifact。

若未来需要支持 pruned base，必须使用独立 capability/profile和单独验证过的 conversion/loading contract；不得放宽本 V2 seal。

### Provider And Lifecycle Ownership

V2 是 `LocalH3VideoProviderFamily` 的 additive child：

- Shot Router 选择 exact `provider_name`、profile与capability；
- family 只按 sealed identity dispatch，不 ranking、不 fallback；
- child adapter只消费 Router 已绑定的 `ProviderNeutralVideoRequirement` / `ProviderBoundVideoRequest`；
- child拥有 workflow rendering、runtime preflight与ComfyUI transport action；
- `VideoGenerationService` + `ProductionStateCommitter` 继续独占 durable intent、permit、submit/status/fetch、candidate、activation与recovery；
- adapter、workflow或profile不得创建第二套 lifecycle、Registry、Manifest、timeline、repair或final-acceptance truth。

V2 failure不得 fallback到Turbo v1、Quality、原生H3、Seedance、Hailuo或remote MiniMax。V1与V2只能由Router显式选择。

## Capability Model

### Required First Slice

第一实施 slice 只要求 T2VA：

| Field | Required value |
| --- | --- |
| `provider_name` | `comfy-local-h3-t8` |
| proposed `capability_id` | `minimax-h3-t8-t2va-turbo-native-v2` |
| proposed `provider_kind` | `minimax_h3_t8_t2va_turbo_native` |
| proposed `model_id` | `minimax-h3-t8-t2va-turbo-native` |
| `profile_version` | `v2` |
| `mode` | `TEXT_TO_VIDEO` |
| `execution_kind` | `LOCAL` |
| `billing_kind` | `LOCAL_UNMETERED` |
| image/media bindings | none |
| output | `1344x768`, 124 frames, 24 fps, native audio MP4 |
| remote/fallback | disabled |

最终命名前 implementation 必须验证它不会与 current family snapshot中的现有 identity/capability冲突。命名变化必须同步code、tests、profile、matrix和policy，不能由adapter内部 alias。

### Mode Expansion Contract

T8-native backbone后续可扩展 I2VA、FL2VA 与 Ref2VA，但每种模式必须是独立 capability/profile，不得把不同 binding grammar压进一个宽泛 capability：

| T8 task | Provider-neutral `GenerationMode` | Provider-bound `VideoGenerationMode` | Required bindings | Minimum contract |
| --- | --- | --- | --- | --- |
| T2VA | `TEXT_TO_VIDEO` | `TEXT_TO_VIDEO` | none | text + native audio output |
| I2VA | `IMAGE_TO_VIDEO` | `IMAGE_TO_VIDEO` | exactly one `first_frame` | exact first-frame bytes/provenance |
| FL2VA | `FIRST_LAST_FRAME_VIDEO` | `IMAGE_TO_VIDEO` | one `first_frame` + one `last_frame` | exact first/last-frame bytes/provenance |
| Ref2VA | `REFERENCE_TO_VIDEO` | `REFERENCE_TO_VIDEO` | explicit `reference` image/video/audio roles within sealed limits | exact role/count/size/duration policy |

Mode-specific adapter必须从现有 provider-neutral roles映射 T8 `task_type`，不得修改 `ProviderNeutralVideoRequirement` 来容纳 T8私有参数。Exact terminal continuity继续由Router/continuity binding把 accepted upstream terminal bytes映射为 `first_frame`；adapter不能自己选 bridge frame。

I2VA、FL2VA、Ref2VA 在完成各自 template/binding/profile seal、offline tests和独立 local live media proof前，不得出现在 production capability snapshot中。T2VA V2完成不自动证明其它模式可用。

## Workflow And Output Contract

T2VA V2 API workflow必须至少包含并正确连接：

- `UNETLoader`；
- `CLIPLoader`；
- two `VAELoader` nodes for video/audio；
- `LoraLoaderBypassModelOnly`；
- `MiniMaxH3AudioConditioningT8`；
- exactly one `MiniMaxH3DualClockSamplerT8`；
- `RandomNoise`；
- `BasicGuider`；
- `SamplerCustomAdvanced`；
- `MiniMaxH3AVDecodeT8`；
- `VHS_VideoCombine`。

T2VA fixed media baseline：

- `task_type = "T2VA"`；
- `audio_mode = "native"`；
- width `1344`；
- height `768`；
- frame count `124`；
- fps `24`；
- native audio required；
- H.264 MP4；
- CRF `17`，作为AI-VIDEO质量profile对上游Stable 4V4A示例CRF `19`的deliberate encoder override；
- remote/cloud fallback disabled。

Output history必须从profile-declared output node唯一选择 final `*-audio.mp4`。Video-only sibling、wrong node、wrong suffix、zero/duplicate final AV、missing audio stream、wrong resolution/frame count或ambiguous locator都必须 fail closed。

## Profile And Preflight Seal

Profile 必须封存并在 permit/submit之前验证：

- exact T8 commit/version/license；
- exact ComfyUI commit和T8 stable `dual_clock_euler/native_flow` runtime capability；native `FLOW_AV`只属于未来选择其它ComfyUI sampler的可选route，不是本stable-default V2的前置条件；
- exact VideoHelperSuite commit；
- exact SageAttention version/source commit/launch capability；
- exact workflow/template/binding/profile hashes；
- exact required node inventory与每个required node的input schema hash；
- exact non-pruned diffusion model、text encoder、video VAE、audio VAE和converted LoRA identities/hashes；
- exact converter provenance和conversion evidence；
- 4 steps、12/3 shifts、`dual_clock_euler/native_flow`；
- resolution/frame/fps/output bounds；
- literal loopback endpoint；
- final AV output semantics；
- `remote_provider_enabled=false` 与 `cloud_fallback_enabled=false`。

沿用现有local lifecycle sequencing：`VideoGenerationService`先持久化intent并mint permit，selected child随后在`submit_local()`内完成preflight。Preflight必须在permit consumption和ComfyUI POST之前拒绝任何drift；失败时不得消费permit、不得POST，也不得通过回退到v1或其它profile恢复。本Spec不要求在permit mint之前preflight，也不改变现有intent/permit owner或sequencing。

## Compatibility And Migration

- 现有 Quality `minimax-h3-t8-t2va-quality-v1` bytes、behavior与identity不变；
- 现有 hybrid Turbo `minimax-h3-t8-t2va-turbo-v1` bytes、behavior与identity不变；
- historical v1 attempts继续按原profile reopen/replay/recover；
- V2 不修改 Manifest、Registry、request、resolved request或artifact layout schema；
- V2 不改变 `comfy-local-h3` native H3、Seedance、Hailuo、remote MiniMax H3行为；
- V2 不自动成为default或preferred capability；
- 只有受控A/B和explicit product decision能批准未来deprecation；即使V2胜出，也必须另行更新Router policy与canonical docs；
- rollback V2只移除V2 child、workflow/profile/tests/docs，不改写v1历史证据。

## Non-Goals

- 本 Spec 不实现代码、workflow或profile；
- 不启动/停止ComfyUI，不生成视频，不做paid/remote调用；
- 不复制T8或Larry implementation；
- 不修改 `ProductionProject`、Manifest schema或Provider-neutral requirement；
- 不引入global Provider catalog、automatic ranking或fallback；
- 不把T8设为Manifest、Registry、Dependency Graph、Timeline、Repair或Final Acceptance owner；
- 不引入T8 Long Video、Studio Timeline、Repair、Reel、Context IR、remote API或credential；
- 不把T2VA完成外推为I2VA/FL2VA/Ref2VA完成；
- 不声称4-step Turbo质量、速度、显存或音频优于现有v1/Quality，除非有fresh受控证据。

## Acceptance Criteria

1. V2 作为 `comfy-local-h3-t8` family中的distinct additive child暴露，Router必须显式选择，unknown/denied selection不fallback。
2. Quality与hybrid Turbo v1 profile/workflow/binding hashes和behavior保持不变。
3. V2 graph使用non-pruned INT8 ConvRot base、T8-converted Larry LoRA、`LoraLoaderBypassModelOnly`和exactly one `MiniMaxH3DualClockSamplerT8`。
4. V2 graph不包含 `MiniMaxH3TurboLoRA`、`MiniMaxH3TurboSampler`、`BasicScheduler`、`KSamplerSelect`或external sigma/scheduler owner。
5. T8 dual-clock settings精确为4 steps、video shift 12、audio shift 3、`dual_clock_euler/native_flow`。
6. Base model、source LoRA、converter、converted LoRA、T8/ComfyUI/runtime nodes、workflow/binding/profile和output semantics全部exact seal；任一drift在permit/submit前fail closed。
7. V2复用existing local permit/state/status/fetch、`ProductionStateCommitter`与recovery contracts，不创建第二lifecycle。
8. Final output唯一选择declared output node的`*-audio.mp4`并测得native audio；video-only sibling被拒绝。
9. T2VA只暴露`TEXT_TO_VIDEO`且拒绝image/media bindings。
10. 后续I2VA、FL2VA、Ref2VA各自使用独立 capability/profile并严格验证required roles；未完成local proof前不暴露。
11. Offline tests证明Router explicit selection、no fallback、profile/input-schema seal、single sampler owner、pruned-base rejection、converted-LoRA verification、local lifecycle/restart dispatch和v1 behavior不变；FL2VA必须精确证明neutral `FIRST_LAST_FRAME_VIDEO`投影为provider-bound `IMAGE_TO_VIDEO`并保留`first_frame + last_frame` grammar。
12. T2VA V2在声明live-ready前必须完成至少一次sealed loopback smoke，验证`1344x768`、124 frames、24 fps、native audio、final suffix和artifact materialization。
13. V1/V2受控A/B必须固定prompt、seed、resolution、frames、runtime launch与output checks，并分别报告wall time、VRAM/RAM、motion/blur、audio和artifact hashes；A/B结果不自动改变Router default。
14. Exact implementation staged snapshot或commit range必须取得fresh passing Harness receipt，且native independent review没有blocking issue。

## Verification Contract

后续 implementation plan必须覆盖以下最小测试面：

- dedicated V2 provider/profile/workflow tests；
- `tests/test_production_shot_router.py` 的explicit V2 selection、unsupported/no-fallback和mode binding cases；
- provider-neutral adapter regression，证明不引入T8私有requirement grammar；
- provider family regression，证明Quality、hybrid Turbo v1与T8-native Turbo v2 deterministic coexistence和restart dispatch；
- local state lifecycle tests，证明intent/permit/status/fetch/recovery reuse；
- output tests，证明video-only sibling rejection和`*-audio.mp4` materialization；
- Harness routing tests和`.agent/harness/policy.yaml` / `docs/agent-primary-contract-matrix.md`同步；
- focused `python -m pytest`；
- exact staged snapshot或commit-range Harness；
- native independent review；
- 单独的local live technical/media smoke。

Harness只证明tracked implementation/control-plane snapshot，不执行live ComfyUI或媒体质量验收。Live artifact、review derivative、activated candidate和Final Acceptance必须分别报告。

## Promotion Gates

### Gate A — Offline T2VA Contract

V2 adapter、workflow、binding、profile和tests通过offline focused tests与Harness；不得据此声称live compatibility或质量。

### Gate B — Local T2VA Technical Smoke

Exact sealed environment完成一次loopback submit/status/fetch/materialize，输出通过codec、resolution、frame、audio和hash验证；不得据此自动成为default。

### Gate C — Controlled V1/V2/Quality Comparison

固定输入和环境完成blind或至少independent media review。若V2没有明确收益，保留为experimental/additive lane；不得为“架构更干净”而删除可用v1。

### Gate D — Mode Expansion

按I2VA、FL2VA、Ref2VA逐个新增独立profile、binding、tests和live proof。每个mode independently通过前不得在Router capability snapshot中宣称支持。

### Gate E — Optional V1 Retirement

只有V2完成recovery兼容、live technical proof、受控质量/性能评审，并有单独用户授权时，才可提出v1 deprecation/retirement。Historical manifests与attempts仍必须保持可reopen/recover。

## Open Questions For The Implementation Window

这些问题必须通过本机bytes、T8 `object_info`和可执行evidence回答，不能凭filename推断：

1. `minimax_h3_turbo_4步加速ema_comfyui.safetensors` 对应的exact Larry source filename、source SHA-256、converted SHA-256和metadata是否完整匹配T8 converter contract？
2. 当前ComfyUI commit对 `LoraLoaderBypassModelOnly` 与 `MiniMaxH3DualClockSamplerT8` 暴露的exact input schema是什么，是否与upstream Stable 4V4A UI graph一致？
3. Non-pruned INT8 ConvRot base在RTX 5090、1344x768、124 frames、native audio、4 steps下的实际VRAM/RAM和wall time是多少？
4. V2与hybrid v1在相同prompt/seed下的motion smear、细节、音频稳定性和failure rate是否有material差异？
5. I2VA、FL2VA、Ref2VA各自的first/last/reference数量、格式、尺寸、时长和audio-mode bounds应如何seal，且如何映射现有provider-neutral roles而不修改neutral schema？

上述未决项不阻塞spec acceptance，但阻塞对应capability的implementation/live-ready或promotion claim。
