# MiniMax H3 T8 SageAttention Quality Smoke Record

Date: 2026-08-21

## Purpose

本文记录 RTX 5090 上 `comfyui-minimax-h3-audio-T8`、SageAttention 与 MiniMax H3
本地 T2VA 的可复用 live checkpoint：active ComfyUI runtime、4-step Turbo smoke、
20-step quality smoke、显存/耗时、原生音频及无声播放诊断。

这是 local lab/runtime evidence，不是 AI-VIDEO Provider adapter、Production candidate、
quality acceptance、P4 audio activation 或新的 production truth。AI-VIDEO source、schema、
Manifest、Provider lifecycle、Comfy workflow 与 H3 profile 均未因本次 smoke 改动。

## Current Runtime Truth

- AI-VIDEO checkout 当时位于 local `main` commit `3c12cdd`，相对 `origin/main`
  ahead 1；本次 runtime 安装与媒体输出均在 `/home/reggie/ComfyUI`，不在 repository
  tracked source 中。
- ComfyUI 位于 `/home/reggie/ComfyUI`，commit
  `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa` / tag `v0.33.2`。live server 只监听
  `127.0.0.1:8188`，启动参数包含 `--use-sage-attention`，没有 remote listen 或
  Provider fallback。
- T8 custom node 位于
  `/home/reggie/ComfyUI/custom_nodes/minimax-h3-audio-T8`，version `1.36.2`，commit
  `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`。ComfyUI `/object_info` 当前发现 140 个
  T8 nodes；本次执行只使用 stable T2VA conditioning、dual-clock sampler 与 AV decode
  等必要节点。
- SageAttention `2.2.0` 安装于 active Python
  `/home/reggie/miniconda3/bin/python3.13`，source commit
  `d1a57a546c3d395b1ffcbeecc66d81db76f3b4b5`。live environment 为
  `torch 2.9.0+cu128` / CUDA 12.8；GPU 是 compute capability 12.0 的 RTX 5090，
  driver `595.84`，reported VRAM `32607 MiB`。
- 两次生成都使用 local files：MiniMax H3 FL2VA diffusion model、
  `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`、
  `minimax_h3_video_vae_fp16.safetensors` 与
  `minimax_h3_audio_vae_fp32.safetensors`。没有下载新权重、读取 API key、调用 MiniMax
  API、访问付费 Provider 或启用 T8 `Context IR Provider`。
- `h3-video` 只提供 H3 prompt/mode/settings guidance；实际 submission 通过现有
  AI-VIDEO `ComfyClient` 向 loopback ComfyUI 完成。T8 不拥有 `ProductionProject`、
  Asset Registry、Manifest、Dependency Graph、`ResolvedTimeline`、Review/Repair state
  或 Provider lifecycle。

安装前 source assessment 位于
`docs/research/2026-08-21-comfyui-minimax-h3-audio-t8.md`。该 note 当时只证明 source
facts，并建议隔离试验；用户随后明确授权在 active ComfyUI 安装与 smoke。本次成功只把
当前 exact stable/quality node path 从“未验证”推进为 local live proof，不证明其余
Long Video、Studio、Repair、Reel、Context IR、speech 或 Advanced/EXP routes compatible。

## Session Work And Decisions

两次生成固定同一 3-field 夜雨金属屋顶 intent、seed `123456789`、T2VA native audio、
`1344x768`、124 frames、24 fps 与 H.264 CRF 17。durable record 不保存 raw prompt；
只有 generation route 发生以下变化：

| Route | Turbo stable smoke | 20-step quality smoke |
| --- | --- | --- |
| prompt id | `de6d296e-ef8b-4f74-9f39-f89329fe8c2e` | `bb360cac-bcc7-4dbf-9136-5312c211467b` |
| diffusion | `minimax_h3_fl2va_int8_convrot.safetensors` | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` |
| LoRA | `minimax_h3_turbo_4步加速ema_comfyui.safetensors` | disabled |
| steps | 4 | 20 |
| sampler / scheduler | T8 default dual-clock/native-flow path | `res_multistep` / `simple` |
| Comfy execution time | `99.543 s` | `326.468 s` |
| output | `T8_Sage_5090_smoke_00001-audio.mp4` | `T8_Sage_5090_HQ20_00001-audio.mp4` |

20-step run 没有使用 T8 experimental SPEED workflow、upscaler、refiner、remote VLM
judge 或 external audio model。它是 quality hypothesis，不是把 4-step result 做后期放大。

## Verification And Evidence

### Runtime And GPU

- 两个 prompt history 都为 `status_str=success` / `completed=true`，且 output metadata
  指向 exact `-audio.mp4` artifact。
- 20-step run 的 0.5-second `nvidia-smi` trace 有 677 个 samples；observed peak 为
  `25980 MiB`，GPU utilization peak `100%`，power peak `580.16 W`。raw trace 位于
  ephemeral `/tmp/t8-hq20-vram.csv`，不属于 durable repository artifact。
- 20-step wall time 是 4-step 的 `3.280x`。4-step run 只有 earlier periodic VRAM
  observations，没有等价的 continuous trace，因此不把其显存数字升级为同等级 durable
  evidence。
- ComfyUI 当前 `/object_info` 实际注册
  `MiniMaxH3AudioConditioningT8`、`MiniMaxH3DualClockSamplerT8` 与
  `MiniMaxH3AVDecodeT8`；server argv 明确包含 `--use-sage-attention`。这证明 exact path
  已真实执行，但不能单独量化 SageAttention 相对其他 attention backend 的速度收益。

### Media Measurements

| Measurement | 4-step Turbo | 20-step quality |
| --- | --- | --- |
| final path | `/home/reggie/ComfyUI/output/MiniMaxH3/T8_Sage_5090_smoke_00001-audio.mp4` | `/home/reggie/ComfyUI/output/MiniMaxH3/T8_Sage_5090_HQ20_00001-audio.mp4` |
| SHA-256 | `e7e002b99940668426dd816a07b2392692356992c4422584c63f5a55a52ab339` | `0426d60104dcba83bdfdf65282d4f7728921357df63d2cdb0fa65b75ddd15e5c` |
| duration / frames | `5.167 s` / 124 | `5.167 s` / 124 |
| video | H.264 High, `1344x768`, `yuv420p`, `4789941 bps` | H.264 High, `1344x768`, `yuv420p`, `4763982 bps` |
| audio | AAC LC, 32 kHz stereo, `127425 bps` | AAC LC, 32 kHz stereo, `127510 bps` |
| measured volume | mean `-38.6 dB`, max `-24.2 dB` | mean `-30.6 dB`, max `-8.8 dB` |
| file size | `3184929` bytes | `3168059` bytes |

Project-local `video-analysis` 对两份 final artifact 都报告 one scene、6/6 unique sampled
frames、audio present。相同尺度六帧 diagnostic 的 Laplacian mean 从 `174.067` 变为
`302.756`，Tenengrad mean 从 `1874.904` 变为 `6808.067`；quality route 同时更亮，
luma mean 从 `13.517` 变为 `18.956`，且构图发生变化。因此这些指标只支持“本次
20-step artifact 有更多 measured high-frequency detail”，不能把变化完全归因于 steps，
也不能外推为通用 H3 quality acceptance。

### Why One File Was Silent

T8/VideoHelperSuite 在 quality output 中保留两个 sibling artifacts：

- `/home/reggie/ComfyUI/output/MiniMaxH3/T8_Sage_5090_HQ20_00001.mp4`：
  SHA-256 `3898f353e0aceceec947cf08f3fb3feddcc46af38ba75aed7b744b72d692ca17`，
  只含 H.264 stream，audio stream count 为 0。
- `/home/reggie/ComfyUI/output/MiniMaxH3/T8_Sage_5090_HQ20_00001-audio.mp4`：
  含 H.264 + AAC，decoded audio 为 164864 samples，非 silent payload。

因此“播放没有声音”的直接原因是 video-only intermediate 与 final muxed artifact 易被混淆；
必须交付或播放带 `-audio.mp4` suffix 的文件。即使 final artifact 包含 native AAC，它也只
是 local H3 candidate evidence；若将来进入 AI-VIDEO Production composition，仍不得绕过
canonical P4 audio tracks、`ResolvedTimeline` 与 HyperFrames mixer。

## Assessment

RTX 5090 当前能够在同一 active ComfyUI process 中完成 T8 stable 4V4A 和
`h3-video`-guided 20-step quality T2VA，SageAttention 没有在这两个 exact runs 中触发
import、OOM 或 execution failure。20-step result 的雨线、水花边缘与屋面纹理在 diagnostic
中更丰富，但它同时改变 diffusion checkpoint、LoRA、sampler/scheduler 和 steps，不能称为
single-variable sampler benchmark。

合理的 operational split 是：4-step Turbo 用于快速 prompt/motion preview；20-step
quality route 用于 selected hero/close-up candidate。该建议仍需按 Shot 单独 review，不能
成为全项目自动 routing 或无条件 quality truth。

## Remaining Risks Or Next Work

- 尚未完成 blinded human audiovisual review、跨多类 Shot benchmark、SageAttention
  on/off A/B 或 4-step continuous VRAM trace。
- ComfyUI output 位于 lab directory，没有导入 Asset Registry、创建 content-addressed
  Production evidence、写入 Manifest、通过 Review receipt 或 activation。
- 当前 live ComfyUI 已注册整个 T8 surface；除本次 exact nodes 外，其余 routes 仍未验证，
  也未获 AI-VIDEO runtime ownership。
- 若用户需要更响的 preview，可对 final `-audio.mp4` 创建显式 gain/normalization derivative；
  不应覆盖原始 artifact，也不应把 preview loudness processing误写为 P4 mastering。

## Agent Guardrails

- 交付 T8 AV result 时必须探测 audio stream，并明确选择 `-audio.mp4`；文件名相近不能替代
  `ffprobe` evidence。
- 不把 file size、亮度或 sharpness 单指标当作 quality acceptance；必须同时保留 prompt/seed/
  model/LoRA/sampler/steps、codec、音轨、wall time、VRAM 与人工 review boundary。
- 不启用或复制 T8 Long Video Manifest、Studio Timeline、Repair lifecycle、Provider routes
  或其他 state owners 到 AI-VIDEO。
- 不把 local ComfyUI success 当作 Provider adapter integration、candidate activation、P4 audio
  adoption、final delivery 或 paid/cloud proof。
- 任何未来 remote Provider、credential、T8 Context IR、production adapter、schema/Manifest、
  H3 profile 或 Comfy workflow 变更都需要独立 scope、授权与既有 AI-VIDEO gates。
