# T8 LatentSync Speaking Subtitle Experiment Record

Date: 2026-08-25

## Purpose

本文补记一个已完成的 Local MiniMax H3 T8 development experiment：先用 T8 自有
conditioning、dual-clock sampler 与 AV decode 节点生成近景普通话 speaking source，
再串行使用 LatentSync v1.6 校正嘴型、用 SyncNet 对比 automated AV offset，最后生成
burned Chinese subtitle derivative。

本记录描述 development media 与 post-processing evidence，不是 Production Provider
qualification、P4 caption integration、P6、Final Acceptance、active capability 或 canonical
reference。Automated SyncNet improvement 与 human full-speed lip-sync verdict 必须分开。

## Experiment Contract

T8 source 固定为一个约 5.17 秒的同场景近景说话镜头：同一 short black bob East Asian
woman、beige trench coat、red satchel strap 与 railway-station scene；人物从 screen-right
profile 转到稳定 three-quarter face，不走动、不后退，台词 contract 为：

```text
我们快到了，再往前走一段。
```

Generation surfaces：

- local ComfyUI / MiniMax H3 T8 only；remote submit `0`，paid effect `0`；
- model：`minimax_h3_fl2va_pruned_int8_convrot.safetensors`；
- `1344x768`、24 fps、124 frames、20 steps、seed `320005`；
- `dual_clock_euler/native_flow`，video/audio shift `12/3`，native audio；
- Turbo LoRA off；no fallback；
- compact request SHA-256：`099ee71290247637351e33de8587acca2d0c8131801d724ca4de234ba12509fd`；
- prompt UTF-8 SHA-256：`e0fcf1d2abab909d8e28cd88bb1f16ae778d0c8d2e577468e36ff4623eec62aa`；
- experiment-only opening frame SHA-256：`d9d61842d13a6ad6f3a591f4269d2413bc5fd6853d3c6d0af10dc32ef66e7c74`。

Exact request graph包含：

```text
MiniMaxH3AudioConditioningT8
MiniMaxH3DualClockSamplerT8
MiniMaxH3AVDecodeT8
```

它不包含 `MiniMaxH3TurboLoRA`、`MiniMaxH3TurboSampler`、
`LoraLoaderBypassModelOnly` 或 `ComfyUI-MiniMax-H3-Turbo` reference。主机上预先存在
Larry plugin checkout不等于该 graph 使用它；本轮没有安装、更新或修改 Larry plugin。

## T8 Source Result

唯一实际 T8 sampling prompt ID：

```text
5f0029ef-6880-4af0-83db-b89c1e0457da
```

Terminal history为 `success` / `completed=true`。Raw T8 native-audio source：

```text
/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0j_t8_closeup_speaking_source_v1_seed320005_20260825_00001-audio.mp4
```

- SHA-256：`be73b86125623a31e3a62c6e1c11eef40e211017cc3edde23e310f740c251f4e`；
- size：`946954` bytes；
- H.264、`1344x768`、24 fps、124 frames、video duration `5.166667` seconds；
- AAC、32 kHz、stereo、audio duration `5.152` seconds；
- full video decode与full audio decode通过。

LatentSync InsightFace detector在全部124个raw source frames中均找到usable face，retention
为 `124/124`；face bbox median约为 `161x235` pixels。这关闭了E0-I侧脸过小、部分帧
缺脸导致嘴型校正不可用的入口问题，但不等于lip-sync quality PASS。

## LatentSync Runtime And Result

LatentSync checkout：

```text
/home/reggie/.cache/ai-video/latentsync-v1.6
commit a229c3948406bc2cf6eaf4873e662e70c6a04746
```

T8 custom-node checkout为commit
`28cb160827c245b2d6a37539df30c1d7c5e7aecd`。LatentSync使用isolated
`.venv-5090`、Torch `2.11.0+cu130`、20 inference steps、guidance `1.5`、seed
`1247`；ComfyUI与LatentSync串行运行，未让两套大模型并发驻留GPU。

第一次LatentSync invocation在diffusion sampling前的face affine transform失败：

```text
nvrtc: error: failed to open libnvrtc-builtins.so.13.0
```

CUDA 13 NVRTC library实际已存在。只为本次进程把
`/home/reggie/micromamba/envs/comfyui/lib/python3.12/site-packages/nvidia/cu13/lib`
置于`LD_LIBRARY_PATH`前部；最小`torch.det()` CUDA repro通过后，恢复同一input、seed与
inference settings。该动作是pre-sampling infrastructure correction，不是生成另一个
candidate、model retry、prompt change或fallback。

LatentSync corrected output：

```text
/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0k_latentsync16_lipsync_v1_from_e0j_t8_20260825.mp4
```

- SHA-256：`2a25aa3f18b7704b97e30f4f66552a5c8a639c070d92c72d5ad85dad63fec51b`；
- size：`875265` bytes；
- H.264、`1344x768`、25 fps、130 frames、video duration `5.200` seconds；
- AAC、16 kHz、mono、audio duration `5.152` seconds；container `5.216` seconds；
- full video decode与full audio decode通过。

25 fps / 130-frame output是LatentSync v1.6 preprocessing normalization，不是T8
generation contract变化。

## SyncNet And Subtitle Evidence

使用同一个official `syncnet_v2.model`和独立temp directories测得：

| Artifact | SyncNet confidence | AV offset |
| --- | ---: | ---: |
| Raw T8 source | `4.01` | `-2` |
| LatentSync corrected | `4.34` | `0` |
| Burned-subtitle derivative | `4.34` | `0` |

Offset从`-2`归零，confidence仅从`4.01`小幅升到`4.34`。因此automated verdict只能是
`technical improvement`，不能宣称中文逐字viseme、自然度或主观口形完全对齐。

Burned-subtitle derivative：

```text
/home/reggie/ComfyUI/output/development_experiment/shot_continuity_e0k_latentsync16_lipsync_v1_from_e0j_t8_20260825_burned_subtitles.mp4
```

- SHA-256：`26574a4285c25baa7747862e0f682a9c607656851931c71d03d2572c1f794bf3`；
- size：`934870` bytes；
- H.264、`1344x768`、25 fps、130 frames；AAC、16 kHz、mono；
- 字幕文本为“我们快到了，再往前走一段。”，显示区间 `0.80--3.90` seconds；
- LatentSync output与subtitle derivative的decoded 16 kHz mono PCM SHA-256均为
  `3676ab3cc29182d80775bf3e067572a139090f794889888e3bf5a5788745bc34`；
- full video/audio decode通过，subtitle frame visual inspection通过。

当前ffmpeg没有`subtitles/libass` filter；本轮用`drawtext/libfreetype`与本机Noto CJK
font烧录，并用`-c:a copy`保持corrected audio。固定字幕来自accepted dialogue contract，
不能反向证明native T8 speech逐字完全一致。

## Assessment And Boundaries

Technical verdict为`PASS with human lip-sync pending`：T8-only source真实生成；所有source
frames保留usable face；LatentSync完成；SyncNet offset归零；字幕版完整解码且音轨保持。
Human verdict仍需用户以正常速度、开启声音观看最终字幕版，判断：

- 中文音节与嘴唇/下颌形状是否逐字自然；
- voice clarity、naturalness与台词是否可接受；
- initial head turn、identity、coat、satchel与station是否稳定；
- subtitle timing与可读性是否合适。

Provider/media effects：local T8 sampled candidate `1`；LatentSync derivative `1`；burned
subtitle derivative `1`；remote/paid submit `0`；fallback `0`。Production code、Manifest、
Registry、qualification、activation、P6与Final Acceptance effects均为`0`。

实验完成时本窗口启动的ComfyUI unit已停止。补记录时发现另一个后续窗口拥有新的
`ai-video-comfyui-152a33b045004b339d028a0353fec99b.service`、PID `516222`与empty
queue；本轮只读观察，没有停止、提交或修改该并发owner。

Environment与启动操作细节见：

```text
.agent/context/t8-latentsync-local-runtime.md
```

Next One Thing：用户观看最终burned-subtitle MP4并给出human lip-sync verdict。没有明确
新缺陷与新授权时，不再生成candidate，也不把本次development result升级为Production。

## Agent Guardrails

- T8 node graph不等于Larry Turbo graph；installed plugin presence也不等于request use。
- Face retention `124/124`不等于mouth/audio sync PASS。
- SyncNet offset `0`和confidence improvement不替代human Mandarin viseme review。
- LatentSync post-process不属于T8 native generation，也不是P4 canonical audio/caption path。
- Burned subtitle不是Production caption integration。
- Local technical PASS不得升级为Production qualification、P6、Final Acceptance、active
  capability或canonical reference。
