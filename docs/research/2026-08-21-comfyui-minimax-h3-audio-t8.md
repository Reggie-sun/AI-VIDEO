# ComfyUI MiniMax H3 Audio T8 Assessment

## Scope And Snapshot

本 note 评估 `T8mars/comfyui-minimax-h3-audio-T8` 是否适合进入 AI-VIDEO 的本地 MiniMax H3 路线，以及它与已安装 `h3-video` knowledge skill 的边界。只做了 source inspection；没有安装 custom node、依赖或模型，没有启动/探测 ComfyUI，没有生成媒体、调用 Provider 或读取 credential。

检查快照为 upstream `main` commit [`977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/tree/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40)，commit time `2026-08-21T02:38:33+08:00`。仓库当前没有 Git tag；若后续试验，应 pin exact commit，而不是跟随快速变化的 `main`。

## Executive Assessment

可以尝试 RTX 5090 的 `1344x768` quality hypothesis，但应先在 AI-VIDEO 已有 native H3 lane 做独立 controlled A/B；这不需要安装 T8 custom node。现有 AI-VIDEO evidence 已验证 `1344x672` + H.264 CRF 17 改善了编码与细节，但没有单独验证 `1344x768` 相对 `1344x672` 的收益，见 [`2026-08-20-minimax-h3-local-quality-parameters.md`](./2026-08-20-minimax-h3-local-quality-parameters.md)。

T8 仓库本身不是 knowledge-only skill，而是大型 ComfyUI runtime extension：upstream 声称 `1.36.2`、140 个 nodes，并包含 sampling、audio control、long-video state、repair、studio timeline、HTTP routes、model patching 和 delivery code。[README](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/README.md) · [node registry](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/nodes.py) 因此不应直接装进当前 active AI-VIDEO ComfyUI runtime，也不能成为新的 timeline、manifest、repair 或 Provider owner。

## Repository Claims

- 安装方式是 Comfy Registry 的 `comfy node install minimax-h3-audio-t8`，或复制整个仓库到 `ComfyUI/custom_nodes/minimax-h3-audio-T8`；安装后需要重启 ComfyUI。[README installation](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/README.md#%E5%AE%89%E8%A3%85)
- 仓库声明不自动下载 H3 weights，且没有强制的额外 pip dependency；用户需要自行准备 matching model、CLIP、video/audio VAE 和 LoRA。[README installation](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/README.md#%E5%AE%89%E8%A3%85) · [`pyproject.toml`](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/pyproject.toml) · [`requirements.txt`](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/requirements.txt)
- Stable entry 是 Turbo `4V4A`；`4V8A`/`4V10A` 属于 multi-rate experiments，仓库没有声称它们在所有素材上优于 `4V4A`。[basic workflow guide](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/examples/workflows/01-basic-generation/README.md)
- Motion/quality routes 要求一次只启用一种方法并固定 image、prompt、seed、resolution、NFE；仓库明确没有把任何单一路线定为全局最佳。[motion-detail guide](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/examples/workflows/07-motion-detail/README.md)
- SPEED route 的正式同输入对照比 baseline 更慢、占用更多显存，用户盲评也选择 baseline，所以 upstream 自己不推荐把 SPEED 当日常 sampler。[SPEED guide](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/examples/workflows/10-speed/README.md)

这些是 repository claims，不等于本机已验证，也不能替代 AI-VIDEO profile/receipt。

## Verified Code Facts

### Runtime Surface

- `__init__.py` 暴露 `comfy_entrypoint` 和 `WEB_DIRECTORY`，`nodes.py` 通过 `ComfyExtension.get_node_list()` 注册整组 nodes；没有发现 selective install 或只注册 stable subset 的 feature flag。[entrypoint](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/__init__.py) · [registry](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/nodes.py)
- `get_node_list()` 同时调用 `register_long_video_background_routes()`，向 ComfyUI server 注册 pause/resume/cancel HTTP routes；它不是只包含 passive node definitions。[route registration](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/long_video_routes.py)
- Sampling、long video、multi-keyframe、Prompt Relay、Hybrid 和 detail routes 会 clone/patch ComfyUI `MODEL` 或其 `model_options`；这虽多为 scoped patch，不修改 core source file，但仍与 core commit 和其他 custom-node patches 强耦合。[stable sampler](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/sampling.py) · [long-video patch](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/long_video.py) · [Prompt Relay patch](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/prompt_relay_advanced.py)
- 仓库当前快照没有 `SKILL.md`，尽管 README 的 development section 提到应先读“本地 `SKILL.md`”。因此它不能原样注册为 Codex knowledge skill；复制其文档或代码还需遵守 GPL 与来源边界。[repository tree](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/tree/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40)

### Dependencies, Models And Workflows

- Base package metadata 的 `dependencies = []`，`requirements.txt` 只说明 `torch`/`torchaudio` 由 ComfyUI 提供。代码还直接依赖 ComfyUI modules、NumPy、Safetensors 等 ComfyUI environment components。[package metadata](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/pyproject.toml) · [long-video imports](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/long_video_delivery.py)
- Optional features 会按需 import `faster-whisper`, `transformers`, OpenCV, `onnxruntime`, `ultralytics`, `psutil`, `pynvml`, PyAV 和 `soundfile`；相关 local ASR、WavLM、YuNet/SFace、SAM3.1、anime-face 等模型不随仓库分发。[optional dependency inventory](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/meta.json) · [speech verification](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/speech_verification.py) · [face refine](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/face_refine_advanced.py)
- Stable `4V4A` workflow references `minimax_h3_fl2va_int8_convrot`, a 4-step Turbo LoRA, `qwen3vl_32b_minimax_h3_nvfp4_awq`, video/audio VAE, and `VHS_VideoCombine`; importing it therefore also assumes matching local model files and VideoHelperSuite.[4V4A workflow](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/examples/workflows/01-basic-generation/2026-08-06_H3_Turbo_Stable_4V4A.json)
- Source inspection found no model downloader and no ComfyUI process launcher. Installing the node does not itself download weights or start ComfyUI; Manager/manual installation fetches code, and a later ComfyUI restart loads the runtime.

### Network, Provider And Credentials

- Base local H3 generation does not call MiniMax API and requires no Provider credential.
- 但 `Context IR Provider Advanced` 明确提供 `openai_compatible_visual` mode：在 `confirm_external_upload=true` 后，它读取指定 environment variable（UI default 为 `OPENAI_API_KEY`），将 sampled visual frames/transcript 发往默认 `https://api.openai.com/v1/chat/completions` 或用户配置 endpoint。[node schema](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/nodes_context_ir_advanced.py) · [provider implementation](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/context_ir_advanced.py)
- 因而“插件完全不联网/完全不需要 credential”是不准确的。准确边界是：默认 local generation 不需要；可选 external visual Provider 会联网并需要 credential。本轮没有触发该 path，也没有读取任何 environment key。

### Second-Truth Surface

- `long_video_delivery.py` 定义自己的 `minimax_h3_t8_accepted_manifest`、candidate/accepted segment lifecycle、timeline frame/sample fields、atomic writes、backup/lock/recovery 和 composition artifacts。[long-video manifest owner](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/long_video_delivery.py)
- `studio_advanced.py` 定义另一套 Studio Timeline、Shot selection 和 repair plan；`repair_execution_advanced.py` 又定义 repair overlay manifest 与 explicit acceptance writes。[Studio Timeline](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/studio_advanced.py) · [repair execution](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/repair_execution_advanced.py)
- 这些实现对 standalone ComfyUI workflow 可能有价值，但在 AI-VIDEO 内会与 `ProductionProject`, Asset Registry, Production Manifest, `ProductionStateCommitter`, Dependency Graph, `ResolvedTimeline`, Review/Repair lifecycle 形成第二套 production truth，必须视为 forbidden runtime ownership。

## Comparison With `h3-video`

| Surface | `open-video` `h3-video` guidance | T8 repository | AI-VIDEO treatment |
| --- | --- | --- | --- |
| Primary role | H3 mode、3-field prompt、settings 与 failure guidance | ComfyUI custom-node runtime + workflows | 前者可做 advisory knowledge；后者仅作 source/reference 或隔离 experiment |
| 5090 recipe | `1344x768`, 20 steps, `res_multistep` + `simple`, INT8 ConvRot | Stable baseline 是 Turbo `4V4A` + custom dual-clock/native-flow；更多 audio steps 是 EXP | 两种 recipe 不是同一个 controlled variable set，不能混配后宣称“最佳” |
| Prompt | 官方 3-field prompt，visible/audible detail、camera language | media tags、task/audio modes、Prompt Relay 和 conditioning | 先由 Shot Contract/Generation Requirement 固定 intent；两者只能提供 translation advice |
| Runtime | AI-VIDEO integration 已禁止 OpenVideo CLI/ComfyUI ownership | 直接注册 nodes/routes，并可写 manifest/candidate/repair artifacts | Provider Adapter/AI-VIDEO state owners 保持唯一 owner |
| Provider/credential | knowledge-only integration 不得调用 Provider | optional OpenAI-compatible visual Provider 读取 env key并上传 sampled media | 禁用整个 external-provider route，除非未来单独通过 paid/cloud-egress gates |

`h3-video` 的 exact guidance 来自 upstream [`skill/h3-video/SKILL.md`](https://github.com/open-video-ai/open-video/blob/95ce9c3588083ed33f42457c97c3cd0f0c7542d1/skill/h3-video/SKILL.md)。其中 `1344x768`/20-step recipe 与 T8 4-step Turbo workflow 是两个不同假设；前者也必须由当前 AI-VIDEO sealed profile、local workflow schema 和 controlled measurements 重新验证。

## Current Local Compatibility

只读检查显示本机 ComfyUI 为 commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa` / tag `v0.33.2`，已有 native `MiniMaxH3ImageToVideo`, `MiniMaxH3ReferenceToVideo`, `MiniMaxH3FlowSampling.audio_scale`, `ComfyExtension`, `ComfyNode` 和 cache-provider API；现有 relevant custom node 只有 VideoHelperSuite，未发现 T8 package。

T8 `meta.json` 声称当前 validated ComfyUI commit 是 `187eda8ef5e588c6a5765cad53e482765edae052`，该 commit 不在本机 checkout 的现有 object set；本机只确认包含其列出的一个 earlier commit `86aedfd943d36d485e5ed3cb9d962f21f73d1741`，不能据此推出当前 1.36.2 与 `v0.33.2` fully compatible。[validation metadata](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/meta.json)

主要 compatibility risks：

1. current package 针对快速变化的 ComfyUI internals、H3 tokenizer/packed layout、model sampling 和 patch APIs；core commit 不一致可能产生 semantic failure，即使 nodes 能 import。
2. package 一次注册 140 nodes 与 server routes，没有发现只装 audio/preflight/stable sampler 的官方 subset。
3. stable T8 workflow 的 model/LoRA/TE 组合与 AI-VIDEO 当前 sealed `minimax_h3_fl2va_quality` profile 不同；直接导入会同时改变 quant、LoRA、sampler、step count、save node 和 prompt，无法解释画质差异。
4. long-video/studio/repair/reel nodes 会写自己的 state/artifacts；在 active AI-VIDEO runtime 中使用会破坏 canonical ownership。
5. repository 迭代快、无 tags；应 pin SHA 并重新检查 upstream claims、workflow hashes 和 core compatibility。

## License

插件代码是 `GPL-3.0-or-later`，不是 MIT/Apache。[LICENSE](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/LICENSE) H3 weights、Qwen、ASR、SAM3.1、LoRA 等分别受各自 upstream license 约束；仓库不分发这些 weights。[README license note](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/977df788fcf8b971dc3d0fc7d6baa79a0edfaf40/README.md#%E9%93%BE%E6%8E%A5%E4%B8%8E%E8%AE%B8%E5%8F%AF) 仅研究 ideas/parameters 不等于复制 implementation；若未来复制或分发代码，需单独做 GPL compatibility review。

## Minimal Safe Evaluation Recommendation

1. **先试 5090 quality recipe，不装 T8。** 在现有 AI-VIDEO native H3 workflow 中新增一次受控 A/B：固定 Shot Contract、Generation Requirement、reference bytes、prompt、seed、model/quant、20 steps、sampler/scheduler、duration、audio path 和 encoder，只比较当前 `1344x672` 与候选 `1344x768`。生成前必须重新确认 exact workflow/profile schema；结果用 `ffprobe`、video-analysis、VRAM/wall-time 与人工音画 review，不用“文件更大”代替质量结论。
2. **T8 先保持 source-reference。** 可吸收的知识只有 media-tag validation、audio-mode semantics、frame/size preflight、一次只改一个 sampling hypothesis、以及其明确写出的 negative results；不得复制其 Manifest/Timeline/Repair/Provider lifecycle。
3. **若以后明确授权 runtime trial，使用隔离 ComfyUI instance。** Pin exact T8 commit 和与其 validated metadata 对齐的 ComfyUI commit，使用独立 custom-node set、output root 和 port；先做 import/object-info 与 `MiniMaxH3PreflightT8`，再做 stable short `4V4A` sample。不要在 active AI-VIDEO ComfyUI 中直接加载，也不要启用 Long Video、Studio、Repair、Reel、Context IR Provider、speech 或任何 Advanced/EXP route。
4. **AI-VIDEO 仍是唯一 owner。** 隔离 trial 输出只视为 external candidate evidence；若未来接入，必须由现有 MiniMax H3 Adapter 提交、记录 provenance、materialize、QA 与 activation。T8 的 manifest/candidate/repair state 永远不进入 AI-VIDEO truth path。

## Exact Sources And Symbols Inspected

- `README.md`, `LICENSE`, `THIRD_PARTY_NOTICES.md`, `pyproject.toml`, `requirements.txt`, `meta.json`, `features.json`
- `__init__.py`: `comfy_entrypoint`, `WEB_DIRECTORY`
- `nodes.py`: `MiniMaxH3AudioT8Extension.get_node_list`, `MiniMaxH3DualClockSamplerT8`
- `sampling.py`: `setup_dual_clock_sampling`
- `context_ir_advanced.py`: `PROVIDER_MODES`, `_call_openai_compatible`, `build_context_ir`
- `long_video_routes.py`: `register_long_video_background_routes`
- `long_video_delivery.py`: `MANIFEST_FORMAT`, `load_delivery_manifest`, candidate/accept/compose paths
- `studio_advanced.py`: `build_studio_timeline`, `build_selective_repair_plan`
- `repair_execution_advanced.py`: repair overlay manifest and acceptance paths
- `speech_reliability.py`: `_ensure_lifecycle_provider`
- `examples/workflows/01-basic-generation`, `07-motion-detail`, `10-speed`
- installed upstream OpenVideo `.agents/skills/h3-video/SKILL.md` at source commit `95ce9c3588083ed33f42457c97c3cd0f0c7542d1`

## Verification Boundary

本轮只验证 source tree、local Git/core symbols 和 note formatting。没有运行 plugin tests、ComfyUI import/startup、workflow execution、GPU measurement 或 media QA，所以不能声称 T8 1.36.2 与本机 ComfyUI compatible，也不能声称任何 T8 route 提升了画质、速度、音频或稳定性。
