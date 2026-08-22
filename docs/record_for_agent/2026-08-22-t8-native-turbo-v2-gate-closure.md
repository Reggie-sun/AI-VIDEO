# T8-Native H3 Turbo V2 Gate Closure Record

Date: 2026-08-22

## Purpose

本记录保存`docs/superpowers/plans/2026-08-22-ai-video-t8-native-turbo-v2.md`实施中的
asset gate、local technical smoke、受控对比、recovery boundary和验证证据。它是本地
runtime/implementation receipt，不是主观media quality、P6 Final Acceptance、push或release证明。

## Gate 0A Exact LoRA Evidence

Shared V2 LoRA gate使用official revision source与pinned T8 converter：

| Evidence | Exact identity |
| --- | --- |
| Source | `DARK-MING/MiniMax-H3-Turbo-Lora@dff52016c06373336893f94e64b6dfea9a4d2db0/minimax_h3_turbo_4step_ema.safetensors` |
| Source bytes | `779849872`; SHA-256 `8d645b67e606874e9179b277cea721c1f1e75830532fcc2206e23353cb33edc5` |
| Converter | T8 commit `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`; file SHA-256 `bf4d9a0d32c528ca9cfe6712f1cc3eae782060be6286337f6a7e77d8030e850d` |
| Installed result | `minimax_h3_turbo_4step_ema_comfyui.safetensors`; `779858632` bytes; SHA-256 `5b8ad6cb7ac206852006f4efa3ce2d679cd6ffb5d5b8a4edce8e981393289df5` |
| Tensor evidence | 259 modules / 518 BF16 tensors; exact key, dtype, shape and source/output value identity |

转换后的safetensors metadata serialization order不是file-byte deterministic；重复转换的
key/metadata/value相同，runtime则seal本次installed result的exact bytes。旧中文命名artifact的
declared source hash不匹配已检查的official 4-step checkpoints，因此保留在本机但不进入
V2 seal或fallback。

## Gate 0B Ref2VA Evidence

Ref2VA required base的source identity为
`Comfy-Org/MiniMax-H3@0f7fb980293fcc4d55c1158cbda920806682ed5d/diffusion_models/minimax_h3_ref2va_int8_convrot.safetensors`，
expected size `34038894550`、SHA-256
`9eef934046a0671bc8a5daf87100705e1478419c574cfde70c50fbe6885f76a9`。

下载transport使用public `Comfy-Org/MiniMax-H3` ModelScope mirror的exact path；ModelScope API报告的
size/SHA与official source identity一致。完整下载后本机rehash为exact
`34038894550` bytes / `9eef934046a0671bc8a5daf87100705e1478419c574cfde70c50fbe6885f76a9`，
然后才用`mv --no-clobber`安装到ComfyUI model path。

首次Ref2VA submit在`MiniMaxH3AudioConditioningT8`以known terminal failure暴露API workflow使用
裸`ref_image_1`，而T8 `1.36.2`/ComfyUI autogrow execution要求
`ref_images.ref_image_0`。Official fixtures、node source和red-green regression确认root cause后，renderer只修复
group-qualified zero-based keys。新attempt使用exact non-pruned base和shared converted LoRA完成
submit/status/fetch、activation/reopen与exact replay，证明不需要第二LoRA artifact。

## Per-Lane Local Technical Evidence

全部smoke固定`1344x768`、124 frames、24fps、native audio、4 steps、
`dual_clock_euler/native_flow`，并走production intent/permit、loopback submit/status/fetch、
candidate activation/reopen与exact replay seam。Peak GPU为整卡`memory.used`，peak RSS为ComfyUI
process RSS。

| Lane | Profile SHA-256 | Provider request | Artifact SHA-256 / bytes | Wall | Peak GPU / RSS |
| --- | --- | --- | --- | ---: | ---: |
| T2VA | `ff374a645eb15112b4c9d4341d1c61bcb80f32bdc55f7325cfe1c8153db5d6bf` | `9c6babd4-562b-4710-ab0e-cfdfcea6eced` | `43c6133f240af118598a52f8348e1558d41eec4134d7b648ca3e09ff33c27000` / `1009896` | `124.531s` | `19932 MiB` / `57988484 KiB` |
| I2VA | `f73fe4a9adef3275ba4b6c9b3bd0307bed39a40542f80747867f2cb46df3e667` | `7bcb6b91-a017-4c2f-abf7-c26e5335abf6` | `090082556e24bb3309ba01c55eaafabff622277cf1a903b305cec5d0767844ef` / `1015850` | `119.068s` | `26236 MiB` / `57960876 KiB` |
| FL2VA | `5fbb4b367eec6854c23d98600d96e366053da07e7635a9e920a6d856172b7a4f` | `28e0bcae-a99d-4d0b-9791-7e88ee98dfb1` | `fcc4125e00ffc9a97319bc7e4478dd933b12f0c7e127d6d4b769725fea01d6d5` / `1388091` | `123.274s` | `24828 MiB` / `58056384 KiB` |
| Ref2VA | `0bb8ebf9688369f89d959d8273a81f73dcc6e02e96c1a20a52110583ace7db9d` | `de9e0337-7919-433e-81a2-44663577d919` | `3f068b69c122be33e7a0c2641dc2de6e1d9fbb2aa2ade0a70e8152868cf22145` / `843120` | `155.391s` | `26797 MiB` / `58233732 KiB` |

四条artifact均为H.264 High `1344x768`、24fps、124 frames、5.167s，含
32 kHz stereo AAC；前三条的project-local `video-analysis`为1 scene、166/166 unique sampled
frames且`issues=[]`，Ref2VA为1 scene并以`framemd5`确认124/124 decoded frames unique。
每条成功attempt的
submit/status/fetch count均为`1/1/1`，exact replay没有
第二次Provider effect。

## Controlled T2VA Comparison

三条lane使用同一exact prompt、seed `220828`、resolution、frame count、fps和native-audio
requirement。由于model/sampling stack不同，同一numeric seed不保证pixel-paired composition。

| Lane | Profile SHA-256 | Artifact SHA-256 / bytes | Wall | Peak GPU / RSS |
| --- | --- | --- | ---: | ---: |
| T8-native Turbo V2 | `ff374a645eb15112b4c9d4341d1c61bcb80f32bdc55f7325cfe1c8153db5d6bf` | `43c6133f240af118598a52f8348e1558d41eec4134d7b648ca3e09ff33c27000` / `1009896` | `124.531s` | `19932 MiB` / `57988484 KiB` |
| hybrid Turbo v1 | `317170c4574cf7b7f89ab144e63b00a64c9b4cf643bad61fde4b4011d36a2212` | `89400ad24925a8e469716447f9b44edebe2fcb0ab4db67d944561fb5f7d74942` / `1467253` | `152.301s` | `25726 MiB` / `58027460 KiB` |
| Quality v1 | `4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7` | `9a369039e65d2463542a8a59584eca81ab18b03231fd794f1b005f0bf62ef13c` / `1880840` | `361.914s` | `26334 MiB` / `45286780 KiB` |

独立reviewer验证三个filename hash、`ffprobe`、embedded workflow metadata和124/124 unique
decoded frames，并检查time-aligned frames、high-motion crops、background stability与audio metrics。
Verdict为`accept with concerns`：

- V2比Turbo v1快`18.2%`，比Quality v1快`65.6%`；
- V2 lantern水平位移约`7.5 px`，运动实现接近静态，纸张细节与边缘也比两个v1软；
- Turbo v1约`43.7 px`、Quality v1约`71.1 px`的水平位移更符合该prompt，且未见明显
  trailing/double-edge smear；
- V2 / Turbo v1 / Quality v1的客观loudness约为`-52.5 / -29.3 / -14.9 LUFS`；
  V2 ambience可能功能性不可闻，环境未支持直接audio playback，因此不声称主观
  audio content/quality或AV synchronization。

该对比只支持保留V2为additive speed-first / experimental T2VA option。它不支持将V2
设为default quality lane、替代Quality v1、退役Turbo v1、外推其他V2 modes或声称P6
Final Acceptance。

## Failure And Recovery Boundaries

- I2VA两次invalid fixture在ComfyUI `LoadImage`阶段known-no-effect fail closed；没有生成或激活不可信artifact。
- I2VA一次submit timeout进入`outcome_unknown`。Explicit recovery保留intent，server restart后
  queue/history/output均无exact request evidence；该request未被blind retry。
- Ref2VA首次submit为known terminal failure：ComfyUI已执行model/LoRA/load-image节点，但
  conditioning在裸`ref_image_1` keyword处立即失败，没有sampler或output。根因修复后使用
  全新project/attempt验证；这不是unknown outcome也没有blind retry。
- 受控对比的Turbo v1有两次known-no-effect pre-POST failure：先补齐old preflight显式调用，
  随后发现ComfyUI dynamic LoRA chooser因新V2 asset扩展而使raw schema hash漂移。兼容修复只对
  exact frozen Turbo v1 hash投影historical chooser inventory，先验证sealed v1 LoRA仍可选，且对其他
  field/type/constraint drift继续fail closed。V1 profile/workflow/binding/capability/family hashes保持不变。

## Verification And Publication

当前focused evidence：V2 + family promotion `49 passed`；修复前的更广
production provider/router/state/E2E surface `224 passed, 1 deselected`，其中deselected six-child test已在
Ref2VA完成后单独运行并通过。`ruff check --no-cache`已通过task-owned Python files。

Final exact commit-range Harness receipt、implementation commit和publication state在Gate 0B与final diff完成后
补记。当前没有push或release。

## Remaining Risks

1. 本次受控对比只有一个prompt/seed，不能推导更广cohort failure rate或主观质量。
2. V2 sample的低运动幅度与约`-52.5 LUFS` audio需要后续独立quality/P6 evidence；不应由
   technical media validity平滑成quality acceptance。
3. V1 retirement仍需独立产品决策与用户授权；本任务只做additive implementation。
