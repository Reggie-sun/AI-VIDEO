# AI-VIDEO T8-Native H3 Turbo V2 Provider Implementation Plan

## Status

Accepted implementation plan for
`docs/superpowers/specs/2026-08-22-ai-video-t8-native-turbo-v2.md`。
本文件只规划后续实现；它不代表四条 capability 已实现、已进入 Router snapshot、已完成
local ComfyUI smoke、已通过媒体质量验收或已替代现有 Quality / hybrid Turbo v1 lane。

四条 required lane 均在本计划内：

- `minimax-h3-t8-t2va-turbo-native-v2`
- `minimax-h3-t8-i2va-turbo-native-v2`
- `minimax-h3-t8-fl2va-turbo-native-v2`
- `minimax-h3-t8-ref2va-turbo-native-v2`

只有四条 lane 分别通过 offline seal、local technical smoke 与 artifact verification 后，
才能把整份 Spec 标记为 complete。按阶段只完成 T2VA 时，状态必须保持 `partial`。

## Goal

在 `comfy-local-h3-t8` family 中新增四个独立、additive、sealed、local-only 的
T8-native Turbo V2 child。Larry 只提供 converted Turbo LoRA provenance；
`MiniMaxH3DualClockSamplerT8` 是唯一 sampling-policy owner；Shot Router 继续独占
provider/profile/capability selection；adapter 继续复用现有 local permit、
submit/status/fetch、`ProductionStateCommitter` 与 recovery lifecycle。

本计划不修改 `ProductionProject`、Manifest、Registry、provider-neutral requirement、
timeline、repair 或 final-acceptance ownership，不引入 fallback、remote API、credential、
T8 `L2VA` 或 `Hybrid`。

## Implementation Boundary

### Single Owners

| Concern | Single owner after implementation |
| --- | --- |
| Provider/profile/capability selection | `VideoGenerationResolver` in `shot_router.py` |
| Generic role/group cardinality model | `video_contracts.py` |
| Capability fingerprint projection | new `_video_capability_fingerprint.py` |
| T8-native Turbo V2 profile/workflow seal | new `comfy_t8_native_turbo_profile.py` |
| T8-native Turbo V2 ComfyUI adapter | new `comfy_t8_native_turbo_video.py` |
| Family exact dispatch | existing `LocalH3VideoProviderFamily` |
| Durable intent, permit, state, activation, recovery | existing `VideoGenerationService` + `ProductionStateCommitter` |
| Final AV artifact selection | V2 adapter using existing local status/fetch contract |

### Unchanged Contracts

- `ProviderNeutralVideoRequirement` 和 `_video_requirement_routing.py` 不增加 T8 私有字段。
- Existing Quality v1、hybrid Turbo v1、native H3、remote MiniMax、Seedance 与 Hailuo
  identity、profile seal、selection behavior 和 replay lineage 不变。
- `LocalH3VideoProviderFamily` 仍只做 exact identity dispatch，不 ranking、不 fallback。
- V2 child 不直接写 Manifest/Registry，不激活 candidate，不拥有 timeline 或 QA truth。
- Existing workflow/profile/binding bytes 不修改。
- Existing `upload_image()` public behavior 保持兼容；新增 generic local input upload 只复用
  相同 loopback ComfyUI input route。

### Old Paths Retained

本任务是 additive implementation，不退休以下路径：

- `src/ai_video/production/comfy_t8_video.py`
- `src/ai_video/production/comfy_t8_turbo_video.py`
- `workflows/*minimax_h3_t8_t2va_quality*`
- `workflows/*minimax_h3_t8_t2va_turbo*`

V1 retirement 是独立产品决策，只有完成受控 A/B、recovery compatibility、local proof
并得到单独用户授权后才能另立任务。

## Frozen Baseline

### Source And Runtime Provenance

Gate 0 以以下当前已读取 bytes 为起点；implementation window 必须重新计算并把结果写入
mode-specific profile seal，不能仅复制本文：

| Artifact | Current observed identity |
| --- | --- |
| AI-VIDEO implementation base | `d9dcdbe572050fbacb28ca5147c84b996445f8bf` |
| ComfyUI commit | `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa` |
| T8 commit / version | `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40` / `1.36.2` |
| VideoHelperSuite commit | `4ee72c065db22c9d96c2427954dc69e7b908444b` |
| Larry comparison commit | `4274783a23afcfdbea3b4876cb79effd6c510785` |
| SageAttention version / source | `2.2.0` / `d1a57a546c3d395b1ffcbeecc66d81db76f3b4b5` |
| T8 converter SHA-256 | `bf4d9a0d32c528ca9cfe6712f1cc3eae782060be6286337f6a7e77d8030e850d` |
| Stable 4V4A upstream workflow SHA-256 | `f5608f8da04e6f300202c1cfb778ad801a6d1b2ec050131c4c90c1181af3d105` |
| Upstream I2VA example SHA-256 | `651e88f18411ee9f50b8e222b97981e1200a230ecd32c29e7c5e663c7e413fc6` |
| Upstream FL2VA example SHA-256 | `bfd62090558f6ff2ef7784693224c237ed11ebc4353243b730e7100195168adb` |
| Upstream Ref2VA example SHA-256 | `ac5fb422e9abf388fceb1033f7f836b4cf6bec4f8158d5645b8a10ce3b6bdb9d` |

当前可用于Gate 0复核的local asset observations：

| Role | Filename | Size | SHA-256 |
| --- | --- | ---: | --- |
| T2VA/I2VA/FL2VA non-pruned base | `minimax_h3_fl2va_int8_convrot.safetensors` | `34038892334` | `7ad4c73e6e378b822ffd1629f27f632d3787d95f5e468e3af958f98c58df96a5` |
| Text encoder | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `15687142551` | `35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6` |
| Video VAE | `minimax_h3_video_vae_fp16.safetensors` | `5207808496` | `7c1f131492e7eddacaac9069a61b81bdd39de5cc96561e677c5eab1cdce5e522` |
| Audio VAE | `minimax_h3_audio_vae_fp32.safetensors` | `605254808` | `8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48` |
| Converted Turbo LoRA | `minimax_h3_turbo_4步加速ema_comfyui.safetensors` | `779858752` | `b07ab477437c6a525dfdaf11107722aad609975ac172f3b577a7a87b228ff7b3` |

这些值是plan编写时的observations，不是未来implementation commit的自动证明；preflight
profile生成前必须从实际local bytes重新计算。AI-VIDEO source commit也要重封为实现时的exact
commit，而不是永久固定为本plan之前的`d9dcdbe...`。

### Frozen Backward-Compatibility Fingerprints

Regression tests必须 pin 当前 legacy projection 的 exact values：

| Snapshot | SHA-256 |
| --- | --- |
| Quality v1 variant | `6ed812530fb4cff8fc3b3667396b1a50c3829ce5b109efa048ad649c8555aa31` |
| Quality v1 provider snapshot | `3b9e58ee57b38c51506573e9cb59127f75dd5b4ee4fe65c9efb97aed06e01761` |
| Turbo v1 variant | `1db0db35311e01b3a5a49af0caf63b9fd0163e99743bcbccf511aa10db037ffb` |
| Turbo v1 provider snapshot | `dc10a59156e1ab820f86f2fae0d8107ee7c3a55ead417a084eafeae579683799` |
| Existing two-child family snapshot | `fe029252f59553434aeb23cfc0576ef5d6d476f27fb0bce57ed17ca0d7d68210` |

新增四个 child 后的 six-child family snapshot 合理地会变化；compatibility test 要求的是：
只组装原两个 child 时仍得到上述旧 family hash，单个 v1 variant/provider hash 不变，
historical Turbo v1 provider-bound lineage 能 reopen/replay。

## Gate 0 — Asset And Conversion Evidence

### Gate 0A — Shared Converted Turbo LoRA

T2VA、I2VA、FL2VA 都依赖这个 gate；Ref2VA 还需通过 Gate 0B。

已观察的 converted artifact：

```text
filename: minimax_h3_turbo_4步加速ema_comfyui.safetensors
size: 779858752
sha256: b07ab477437c6a525dfdaf11107722aad609975ac172f3b577a7a87b228ff7b3
tensor count: 518 BF16
metadata source filename: minimax_h3_turbo_4步加速ema.safetensors
metadata source sha256: 8a1265e81e5368ab0e52cbb990aee3cb59b28b91fdfa415ef8dbabf81aef890e
```

当前本机另一个 Larry raw file 的 SHA-256 是
`5f3a626cd72c93a8b9318d6760c510bc5092d2ab13aaba1f932c5bab07a416d3`，
不等于 converted artifact metadata 中的 source hash。它不能作为 conversion proof。

Implementation 必须先完成以下一次性 offline evidence：

1. 重新取得或定位 exact source bytes
   `minimax_h3_turbo_4步加速ema.safetensors`，验证 size、SHA-256 与来源 revision。
2. 用 pinned T8 converter 对 exact source 做 isolated conversion，或对已有 converted file
   完成同等强度的 key-set、tensor count、dtype、shape、value-identity 与 metadata audit。
3. 证明输出为 518 个 BF16 tensor，source/output value identity 成立，converted keys 符合
   native ComfyUI layout，并记录 converter commit/file hash。
4. 将 converted filename、size/hash、source identity、converter identity、schema version、
   tensor evidence写入 shared V2 asset seal。
5. Profile load与每次 preflight只验证 sealed converted result，不在 submit path重新转换，
   也不要求 source file永久留在 runtime tree。

Gate 0A 未通过时，任何 V2 capability 都不得进入 live-ready capability snapshot。

### Gate 0B — Ref2VA Base And Compatibility

当前本机缺少 required non-pruned
`minimax_h3_ref2va_int8_convrot.safetensors`。Ref2VA implementation 可以先完成
offline profile/workflow/parser tests，但 capability 必须保持 unavailable，直到：

1. 安装 exact non-pruned Ref2VA base；
2. 记录 filename、size、SHA-256 和来源；
3. 单独验证 converted Turbo LoRA 与该 Ref2VA base 兼容；
4. 证明没有退回 `pruned_*` model；
5. 完成 Ref2VA local technical smoke。

如果 Ref2VA 需要不同 LoRA/conversion artifact，则必须建立独立 exact seal，不能继承
FL2VA-family 的 compatibility evidence。

## Target File Map

### New Production Modules

- `src/ai_video/production/_video_capability_fingerprint.py`
  - 唯一 shared backward-compatible fingerprint projection。
  - Empty `binding_cardinality_constraints` 从 legacy projection 省略；non-empty constraints
    使用 canonical representation。
- `src/ai_video/production/comfy_t8_native_turbo_profile.py`
  - V2 profile/binding models、mode-specific topology/schema validation、hash seal与load。
- `src/ai_video/production/comfy_t8_native_turbo_video.py`
  - 单一 cohesive `ComfyUIT8NativeTurboVideoProvider` implementation；四条 lane 由四个
    exact profile instance 暴露，不创建四份重复 provider lifecycle。

### Modified Production Modules

- `src/ai_video/production/video_contracts.py`
  - 增加 public immutable `VideoBindingCardinalityConstraint` 与纯 evaluator。
- `src/ai_video/production/video.py`
  - `VideoCapabilityVariant` 增加 default-empty constraints。
  - snapshot seal/validation改用 shared projection。
  - `ResolvedVideoGenerationRequest.create()` 做 defense-in-depth cardinality validation。
- `src/ai_video/production/shot_router.py`
  - `VideoGenerationResolver` 在 selection 阶段执行 exact role/group cardinality。
- `src/ai_video/production/video_compiler.py`
  - lineage comparison改用同一个 shared projection。
- `src/ai_video/comfy_client.py`
  - 增加 generic loopback `upload_input(path)`；保留 `upload_image()` compatibility。
- `src/ai_video/production/__init__.py`
  - 最小导出 V2 provider/profile loader和public constraint type。

`video_requirement.py`、`_video_requirement_routing.py`、`local_h3_provider_family.py`、
`video_generation.py` 不计划修改；现有接口已能表达 mode mapping、exact child dispatch和
lifecycle reuse。只有 executable test证明存在真实 protocol mismatch时，才能在独立 diff中
最小修改，并同步更新本计划的 owner/verification reasoning。

### New Workflow Data

每个 mode都有独立 template、binding与profile，共十二个文件：

```text
workflows/templates/minimax_h3_t8_t2va_turbo_native_v2_api.json
workflows/bindings/minimax_h3_t8_t2va_turbo_native_v2_binding.yaml
workflows/profiles/minimax_h3_t8_t2va_turbo_native_v2.json

workflows/templates/minimax_h3_t8_i2va_turbo_native_v2_api.json
workflows/bindings/minimax_h3_t8_i2va_turbo_native_v2_binding.yaml
workflows/profiles/minimax_h3_t8_i2va_turbo_native_v2.json

workflows/templates/minimax_h3_t8_fl2va_turbo_native_v2_api.json
workflows/bindings/minimax_h3_t8_fl2va_turbo_native_v2_binding.yaml
workflows/profiles/minimax_h3_t8_fl2va_turbo_native_v2.json

workflows/templates/minimax_h3_t8_ref2va_turbo_native_v2_api.json
workflows/bindings/minimax_h3_t8_ref2va_turbo_native_v2_binding.yaml
workflows/profiles/minimax_h3_t8_ref2va_turbo_native_v2.json
```

### Tests

- New `tests/test_production_comfy_t8_native_turbo_video.py`
- Modify `tests/test_comfy_client.py`
- Modify `tests/test_production_video.py`
- Modify `tests/test_production_shot_router.py`
- Modify `tests/test_production_provider_neutral_adapters.py`
- Modify `tests/test_production_local_h3_provider_family.py`
- Modify `tests/test_production_local_video_state.py`
- Modify `tests/test_agent_harness.py`

Frozen regressions must continue to pass without changing their expected v1 bytes:

- `tests/test_production_comfy_t8_video.py`
- `tests/test_production_comfy_t8_turbo_video.py`
- `tests/test_production_comfy_video.py`
- `tests/test_production_minimax_h3.py`
- `tests/test_production_seedance.py`

### Canonical Docs And Harness Routing

- `.agent/harness/policy.yaml`
- `docs/agent-primary-contract-matrix.md`
- `docs/v0.2-runtime-baseline.md`

Runtime baseline 只在实现完成后记录真实状态：每条 lane 必须分别标记 offline-only、
live-ready 或 blocked；不得把 T2VA evidence外推到其它 mode。

## Milestone 1 — Generic Cardinality And Fingerprint Compatibility

### Contract

`VideoBindingCardinalityConstraint` 固定 role universe和canonical order：

```text
first_frame
last_frame
reference
reference_video
reference_audio
```

Validation rules：

- `roles` non-empty且内部unique；存储前按固定顺序canonicalize；
- 同一个canonical role tuple不得重复；
- `0 <= min_count <= max_count <= 32`；
- overlapping constraints必须存在至少一个全局可满足count vector；
- unknown role、duplicate group、invalid bound、unsatisfiable set全部fail closed；
- constraints按canonical role tuple稳定排序后进入seal。

Satisfiability evaluator只需处理五个固定role。实现使用deterministic bounded search：
逐role枚举仍可能满足所有partial interval的count；对每个group计算已分配和、剩余role的
minimum/maximum可达区间进行pruning。不要引入solver dependency。

V2 exact constraints：

| Lane | Constraints |
| --- | --- |
| T2VA | five individual roles exactly `0`; reference group exactly `0` |
| I2VA | `first_frame=1`; other four roles `0`; reference group `0` |
| FL2VA | `first_frame=1`, `last_frame=1`; references `0`; reference group `0` |
| Ref2VA | first/last `0`; image `0..9`; video `0..3`; audio `0..3`; reference group `1..15` |

### Red Tests

先在 `tests/test_production_video.py` 与
`tests/test_production_shot_router.py` 添加失败用例：

- semantic-equivalent role/group declaration canonicalize为相同 representation/hash；
- unknown、empty、duplicate、invalid bound和contradictory overlap被拒绝；
- Router在构造 provider-bound request前拒绝missing/extra/duplicate/cross-mode inputs；
- I2VA和FL2VA即使同为provider-bound `IMAGE_TO_VIDEO`也不能互相选择；
- Ref2VA没有任何reference、超过per-medium上限或group上限时拒绝；
- unknown/denied V2 selection不fallback。

### Green Implementation

1. 在 `video_contracts.py` 添加constraint model、canonicalizer、satisfiability validator与
   request count evaluator。
2. 在 `_video_capability_fingerprint.py` 添加variant/snapshot projection：
   - legacy empty constraints完全省略新field；
   - non-empty constraints包含canonical JSON value；
   - snapshot children也递归使用同一projection。
3. `VideoProviderCapabilities` seal/validation、Router selected fingerprint、compiler lineage
   全部调用同一helper，删除这三个surface对raw `model_dump()`的直接hash ownership。
4. Router selection调用shared evaluator；resolved request creation重复验证selected
   constraint，作为defense in depth，不接管selection。

### Exit Criteria

- 所有constraint model/router tests通过。
- 四个 frozen v1 variant/provider fingerprint完全不变。
- 只组装Quality + Turbo v1时family snapshot不变。
- Historical Turbo v1 provider-bound request lineage可reopen/replay。
- Non-empty V2 constraints参与Router与compiler相同fingerprint。

## Milestone 2 — Shared V2 Profile And Provider Core

### Profile Model

`comfy_t8_native_turbo_profile.py` 定义一个shared schema和四个mode-specific validators。
每个 profile封存：

- exact capability/provider kind/model ID/profile version/lane ID；
- required neutral mode与provider-bound mode；
- fixed `task_type`；
- template/binding/profile hashes；
- exact required/forbidden node inventory；
- required node `object_info` input schema hashes；
- ComfyUI、T8、VideoHelperSuite、SageAttention、converter provenance；
- base model、text encoder、video VAE、audio VAE、converted LoRA identities；
- `steps=4`、video shift `12.0`、audio shift `3.0`、
  `sampler_name=dual_clock_euler`、`scheduler=native_flow`；
- `1344x768`、124 frames、24 fps、native audio、H.264、CRF 17；
- literal loopback endpoint、remote/cloud fallback false；
- declared unique final AV output node和`*-audio.mp4` suffix。

All workflow validators reject：

- `MiniMaxH3TurboLoRA`
- `MiniMaxH3TurboSampler`
- `BasicScheduler`
- `KSamplerSelect`
- external sigma/scheduler owner
- zero或multiple `MiniMaxH3DualClockSamplerT8`
- pruned base
- regular/folding LoRA loader
- LoRA strength不等于 `1.0`
- workflow task type与profile lane不一致

### Provider Core

`ComfyUIT8NativeTurboVideoProvider` 每个instance只暴露一个 exact capability。
Constructor接收：

- sealed profile；
- existing `ComfyClient`-compatible client；
- asset resolver `(asset_id, asset_sha256) -> Path`；
- existing local permit/state dependencies。

Provider只消费provider-bound request。它在permit mint之后、permit consumption与ComfyUI
POST之前执行profile/runtime/asset preflight；失败不得consume permit、不得POST、不得fallback。

复用 existing T8 adapter 的 status/history/fetch/final AV semantics时，只抽取或调用已有
无状态contract；不得让V2继承v1 profile identity或改变v1 behavior。若复用导致v1 module
改动风险，V2在新module中保留最小独立workflow resolve/preflight/submit逻辑，并继续调用
既有 `ComfyClient` 与 state lifecycle。

### Input Upload Contract

`ComfyClient.upload_input(path)` POST到同一个 loopback `/upload/image` input route，返回
server filename。`upload_image()` 保持existing API与tests，可作为兼容wrapper调用
`upload_input()`。Adapter在上传前验证resolved path containment、size、SHA-256和sealed MIME；
server filename只用于workflow binding，不能替代原asset identity/provenance。

### Output Contract

Status/history只接受profile-declared output node的唯一`*-audio.mp4`。以下均fail closed：

- video-only sibling；
- wrong node或wrong suffix；
- zero或multiple final AV locator；
- missing audio stream；
- wrong resolution、frame count或fps；
- zero bytes、hash/materialization mismatch或ambiguous history。

## Milestone 3 — T2VA Lane

### Files

- `minimax_h3_t8_t2va_turbo_native_v2_api.json`
- `minimax_h3_t8_t2va_turbo_native_v2_binding.yaml`
- `minimax_h3_t8_t2va_turbo_native_v2.json`

### Workflow Grammar

- Neutral/provider-bound mode：`TEXT_TO_VIDEO -> TEXT_TO_VIDEO`。
- Fixed `task_type=T2VA`。
- 禁止 first/last/reference media。
- Required backbone：`UNETLoader`、`CLIPLoader`、two `VAELoader`、
  `LoraLoaderBypassModelOnly`、`MiniMaxH3AudioConditioningT8`、exactly one
  `MiniMaxH3DualClockSamplerT8`、`RandomNoise`、`BasicGuider`、
  `SamplerCustomAdvanced`、`MiniMaxH3AVDecodeT8`、`VHS_VideoCombine`。

### Tests And Exit

- exact profile/template/binding hash seal；
- exact required node/input schema；
- single sampling owner与forbidden node rejection；
- converted LoRA/base/preflight drift rejection before permit consumption/POST；
- explicit Router selection/no fallback；
- local permit/state/status/fetch/recovery reuse；
- video-only sibling rejection与`*-audio.mp4` materialization。

Gate 0A + offline tests + Harness完成后状态为`partial/offline-ready`；只有local technical smoke
完成后才能把T2VA标记为live-ready，仍不能宣称其它三条lane完成。

## Milestone 4 — I2VA Lane

### Files And Grammar

- `minimax_h3_t8_i2va_turbo_native_v2_api.json`
- `minimax_h3_t8_i2va_turbo_native_v2_binding.yaml`
- `minimax_h3_t8_i2va_turbo_native_v2.json`
- Neutral/provider-bound mode：`IMAGE_TO_VIDEO -> IMAGE_TO_VIDEO`。
- Fixed `task_type=I2VA`。
- Exactly one `first_frame`；禁止`last_frame`和all reference roles。
- Resolver提供的exact registered PNG bytes通过`upload_input()`绑定到`LoadImage`；不得由
  adapter选择bridge frame或重新编码accepted terminal image。

### Tests And Exit

- Router拒绝zero/two first frames、last frame、reference和T2VA/FL2VA cross-selection。
- Asset ID、expected SHA、resolved bytes、MIME、size、path containment在upload前一致。
- Workflow把exact filename绑定为frame 0 conditioning，不接受placeholder或host path。
- I2VA独立offline tests、Harness与local smoke通过后才进入live-ready snapshot。

## Milestone 5 — FL2VA Lane

### Files And Grammar

- `minimax_h3_t8_fl2va_turbo_native_v2_api.json`
- `minimax_h3_t8_fl2va_turbo_native_v2_binding.yaml`
- `minimax_h3_t8_fl2va_turbo_native_v2.json`
- Neutral/provider-bound mode：`FIRST_LAST_FRAME_VIDEO -> IMAGE_TO_VIDEO`。
- Fixed `task_type=FL2VA`。
- Exactly one `first_frame` + exactly one `last_frame`；禁止all reference roles。
- Exact first/last bytes分别绑定T8 contract中的frame `0`与`frame_count - 1`。
- Accepted upstream terminal continuity bytes只能由Router/continuity binding提供，adapter不自行
  抽帧、不用视频末帧猜测、不回退到I2VA。

### Tests And Exit

- Provider-neutral regression证明FL2VA mapping不需要T8私有requirement字段。
- Router精确区分I2VA与FL2VA，并拒绝missing/duplicate/extra roles。
- 两个image asset分别完成path/hash/MIME/size/provenance validation与deterministic binding。
- FL2VA独立offline tests、Harness与local smoke通过后才进入live-ready snapshot。

## Milestone 6 — Ref2VA Lane

### Files And Grammar

- `minimax_h3_t8_ref2va_turbo_native_v2_api.json`
- `minimax_h3_t8_ref2va_turbo_native_v2_binding.yaml`
- `minimax_h3_t8_ref2va_turbo_native_v2.json`
- Neutral/provider-bound mode：`REFERENCE_TO_VIDEO -> REFERENCE_TO_VIDEO`。
- Fixed `task_type=Ref2VA`。
- 禁止first/last frame；至少一个reference medium。
- Image `0..9`、video `0..3`、standalone audio `0..3`、total `1..15`。
- Reference video必须24 fps且48–360 frames；profile还要封存exact size/MIME/duration bounds。

### Deterministic Binding

按provider-bound request的sealed canonical order上传并绑定：

```text
image             -> LoadImage            -> ref_images.ref_image_N
video             -> VHS_LoadVideo        -> ref_videos.ref_video_N
standalone audio  -> VHS_LoadAudioUpload   -> ref_audios.ref_audio_N
```

`ref_video_audios.*` dynamic input必须不存在。Profile/workflow validator遇到任何
`ref_video_audios.ref_video_audio_N` key、same-ordinal soundtrack linkage或自动合成关系时
fail closed。空值语义由“没有这些dynamic input”表达，不用placeholder filename表达。

### Tests And Exit

- Empty group、per-medium overflow、total overflow、first/last role、unsupported MIME/size/duration
  与non-24-fps video全部拒绝。
- Canonical request order决定stable `N`，不能用filesystem enumeration或ComfyUI history order。
- Standalone audio只进入`ref_audios.*`，任何`ref_video_audios.*` input被拒绝。
- Gate 0B、独立profile/model compatibility tests、Harness与local smoke全部通过后，Ref2VA
  才能进入live-ready snapshot；否则它保持unavailable且整份Spec保持partial。

## Milestone 7 — Family, Lifecycle, And Compatibility Integration

### Family Assembly

Tests以dependency injection组装existing Quality、hybrid Turbo v1和四个V2 child。
`LocalH3VideoProviderFamily` 应无需生产逻辑变化：

- capability ID exact dispatch；
- `(provider_kind, model_id, profile_version, mode)` exact dispatch；
- deterministic six-child snapshot；
- denied/unknown/ambiguous identity fail closed；
- child failure不fallback到任何sibling。

不要新增global family registry或第二条provider selection path。

### Lifecycle Reuse

`tests/test_production_local_video_state.py` 覆盖每条V2 lane：

- durable intent先于permit；
- preflight在permit mint后、permit consumption/POST前；
- successful submit只消费一次permit；
- status/fetch/materialization使用existing state；
- restart从persisted provider-bound identity exact dispatch回同一child；
- unknown outcome进入existing explicit recovery，不blind retry、不remint permit；
- fetch success不直接激活candidate。

### Frozen Regression

- Quality v1与hybrid Turbo v1 profile/workflow/binding hashes不变。
- Native H3与remote MiniMax behavior不变。
- Existing provider-neutral mappings不变。
- Old two-child family snapshot和historical v1 lineage不变。
- V2从不自动成为default/preferred capability。

## Milestone 8 — Harness And Canonical Documentation

### Harness Policy

`.agent/harness/policy.yaml` 的 production video provider category加入：

- two new V2 source modules；
- shared fingerprint helper；
- four V2 template/binding/profile patterns；
- dedicated V2 provider test；
- modified generic video/router/family/local-state/client tests。

若 `comfy_client.py` 同时命中legacy runtime category，保留两类mandatory checks；不得为缩短
Harness而移除现有route。`tests/test_agent_harness.py`证明每类new path触发预期checks，
unmapped owned path仍fail safe。

### Canonical Docs

`docs/agent-primary-contract-matrix.md` 增加或扩展 Local T8 H3 Native Turbo V2 row，明确：

- Router selection owner；
- four capability identities与mode grammar；
- no fallback；
- local lifecycle reuse；
- exact seal/final AV semantics；
- focused verification commands。

`docs/v0.2-runtime-baseline.md` 只记录fresh executable evidence：

- implementation commit与Harness receipt；
- 每条lane的offline/live/blocked状态；
- exact local media proof path/hash；
- Ref2VA asset gate；
- v1仍保留且未自动退役。

## Milestone 9 — Local Technical Smokes And Controlled Comparison

这一步在implementation window执行；当前plan-only任务不启动ComfyUI、不生成媒体。
当前repository rule允许已配置loopback local ComfyUI generation无需额外task-scoped授权，
但profile/preflight/local permit/recovery/media verification gates全部仍然mandatory。

### Per-Lane Technical Smoke

每条lane独立运行一次sealed loopback submit/status/fetch/materialize，并记录：

- exact implementation commit；
- capability/profile/workflow/template/binding hashes；
- endpoint必须literal loopback；
- runtime commits、SageAttention launch capability、node schema；
- exact input asset ID/hash/MIME/size/duration；
- provider file locator必须为declared node的`*-audio.mp4`；
- materialized artifact SHA-256、size和path；
- `ffprobe`：H.264、`1344x768`、24 fps、124 frames、native audio stream；
- wall time、peak VRAM/RAM与失败边界；
- Manifest/Registry activation和final acceptance分别报告，不相互推断。

Ref2VA Gate 0B未通过时不得用pruned model或FL2VA model代替；报告blocked即可。

### Controlled V1/V2/Quality Comparison

T2VA至少做一次固定prompt、seed、resolution、frames、runtime launch与output checks的
Quality v1 / hybrid Turbo v1 / T8-native Turbo v2 comparison。独立review记录motion smear、
细节、audio、wall time、VRAM/RAM和artifact hashes。结果只支持promotion decision，
不自动改变Router default或授权v1 retirement。

## Test Sequence

### 1. Cardinality And Router

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_video.py \
  tests/test_production_shot_router.py \
  tests/test_production_provider_neutral_adapters.py -q
```

### 2. V2 Profile, Workflow, Client, Family, And State

```bash
python -m pytest -p no:cacheprovider \
  tests/test_comfy_client.py \
  tests/test_workflow_loader.py \
  tests/test_workflow_renderer.py \
  tests/test_production_comfy_t8_native_turbo_video.py \
  tests/test_production_local_h3_provider_family.py \
  tests/test_production_local_video_state.py -q
```

### 3. Frozen Provider Regression

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_comfy_t8_video.py \
  tests/test_production_comfy_t8_turbo_video.py \
  tests/test_production_comfy_video.py \
  tests/test_production_minimax_h3.py \
  tests/test_production_seedance.py -q
```

### 4. Final Focused Suite

```bash
python -m pytest -p no:cacheprovider \
  tests/test_comfy_client.py \
  tests/test_workflow_loader.py \
  tests/test_workflow_renderer.py \
  tests/test_production_video.py \
  tests/test_production_shot_router.py \
  tests/test_production_provider_neutral_adapters.py \
  tests/test_production_comfy_t8_video.py \
  tests/test_production_comfy_t8_turbo_video.py \
  tests/test_production_comfy_t8_native_turbo_video.py \
  tests/test_production_local_h3_provider_family.py \
  tests/test_production_local_video_state.py \
  tests/test_production_comfy_video.py \
  tests/test_production_minimax_h3.py \
  tests/test_production_seedance.py -q
```

### 5. Architecture And Harness Routing

```bash
python -m scripts.architecture_gate check
python -m pytest -p no:cacheprovider tests/test_agent_harness.py -q
```

### 6. Exact Snapshot Harness

只stage本任务files，并对non-empty exact staged snapshot执行：

```bash
python scripts/agent_harness.py inspect --staged
python scripts/agent_harness.py verify --staged
```

Commit后对exact commit range重新验证并检查receipt freshness/integrity：

```bash
python scripts/agent_harness.py verify --base-ref HEAD^ --head-ref HEAD
python scripts/agent_harness.py verify-receipt <repository-relative-receipt-path>
```

如果当前Harness CLI的exact flag spelling与上述示例不同，先运行
`python scripts/agent_harness.py --help`，使用其等价exact staged/commit-range参数；不得改用
包含unrelated dirty files的working-tree verification。

## Checkpoint Strategy

后续implementation在current `main`上按可独立验证的stable checkpoint提交；每次只stage
task-owned files。建议checkpoint边界：

1. Generic cardinality + backward-compatible fingerprint projection。
2. Shared V2 profile/provider core + T2VA。
3. I2VA + FL2VA input lanes。
4. Ref2VA lane（Gate 0B通过后）。
5. Family/lifecycle/policy/docs整合与fresh Harness receipt。

若Gate 0B尚未通过，checkpoint 4不得伪造live support；可以提交offline parser/workflow tests，
但profile capability exposure必须fail closed，runtime baseline明确记录blocked。

## Independent Review

Core behavior完成后使用native named `reviewer` 做独立read-only review。Reviewer必须检查：

- Router确实在selection阶段执行cardinality且无fallback；
- shared fingerprint projection是否真的保持v1 exact hashes/lineage；
- V2是否只有一个sampling-policy owner；
- adapter是否绕过local lifecycle或直接激活candidate；
- Ref2VA是否意外连接`ref_video_audios.*`；
- tests是否覆盖video-only sibling、preflight timing、restart/recovery和cross-mode rejection；
- policy/matrix/runtime baseline是否与真实diff/evidence一致。

Parent随后直接复核所有blocking claim、final diff、exact staged/commit-range receipt与task-owned
path集合。Review verdict必须为`accept`或所有blocking issue修复并re-review后才能宣称完成。

## Completion Criteria

本计划只在以下全部成立时完成implementation：

1. 四个distinct capability/profile/template/binding存在并通过各自exact seal。
2. Gate 0A通过；Gate 0B通过且Ref2VA使用non-pruned Ref2VA base。
3. Shared cardinality/fingerprint contracts通过tests，existing v1 hashes/lineage bit-for-bit不变。
4. Router explicit selection、no fallback与四mode exact grammar通过tests。
5. V2 graph使用converted Larry LoRA + `LoraLoaderBypassModelOnly` + exactly one T8
   dual-clock sampler；Larry runtime sampler/LoRA node与external scheduler不存在。
6. Existing local permit/state/status/fetch/committer/recovery lifecycle被复用，无第二owner。
7. Final artifact唯一为declared output node的`*-audio.mp4`，video-only sibling被拒绝。
8. 四条lane分别完成local technical smoke与`ffprobe`/hash/materialization evidence。
9. Focused tests、architecture gate与exact snapshot Harness fresh passing。
10. Native independent review没有blocking issue。
11. Canonical matrix、Harness policy和runtime baseline与实际行为同步。
12. Final report区分offline tests、live technical proof、media quality、activation、push/release，
    并明确v1仍未退役。

## Spec Traceability

| Spec acceptance | Implementation and verification owner |
| --- | --- |
| 1. Additive child, explicit selection, no fallback | Milestones 1、7；Router/family tests |
| 2. Quality v1 / Turbo v1 unchanged | Frozen fingerprints；Milestones 1、7 regression tests |
| 3. Non-pruned base + converted LoRA + T8 sampler | Gate 0；Milestones 2–6 profile/workflow validators |
| 4. Forbidden Larry/external sampler nodes absent | Milestone 2 topology tests |
| 5. Exact 4-step 12/3 dual-clock settings | Milestone 2 profile/schema tests |
| 6. Exact provenance and preflight timing | Gate 0；Milestone 2 preflight tests |
| 7. Existing local lifecycle reuse | Milestone 7 local-state/recovery tests |
| 8. Unique final native AV artifact | Milestones 2、3 output tests；Milestone 9 `ffprobe` |
| 9. Four distinct lane identities and grammars | Milestones 3–6；Router/family snapshots |
| 10. Router-owned role/group cardinality | Milestone 1 model/router tests |
| 11. Ref2VA standalone audio only | Milestone 6 workflow/binding rejection tests |
| 12. Backward-compatible shared fingerprint | Milestone 1 pinned hashes and lineage replay |
| 13. Independent per-mode profile/model/live proof | Milestones 3–6 and 9；per-lane baseline status |
| 14. Required offline regression surface | Test Sequence 1–5 |
| 15. Per-lane sealed local smoke | Milestone 9 technical smoke records |
| 16. Controlled v1/v2/Quality comparison | Milestone 9 comparison; no automatic promotion |
| 17. Exact Harness and independent review | Test Sequence 6；Independent Review |

## Remaining Risks

- Converted LoRA的metadata source bytes当前未在本机得到同hash复核；Gate 0A是所有lane的
  live-ready blocker。
- Non-pruned Ref2VA base当前缺失；Gate 0B是Ref2VA和整份Spec completion blocker。
- ComfyUI upload route虽可传任意input bytes，video/audio loader对uploaded filename的实际行为
  仍需local smoke验证，offline mock不能替代。
- Four-step T8-native Turbo的实际质量、wall time和VRAM/RAM尚无fresh受控证据；架构正确
  不等于质量优于hybrid Turbo v1或Quality v1。
- Local technical smoke不等于Production Final Acceptance；continuity与跨shot观感仍由后续
  composition/review流程判定。
