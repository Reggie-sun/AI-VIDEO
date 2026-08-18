# MiniMax H3 RTX 5090 Provider Assessment

## Executive Summary

截至 2026-08-17，MiniMax H3 已发布开放权重，但它不是通用文本/Agent LLM，而是一个以视频为主要输出、同时原生生成同步立体声音频的 omni-modal generation system。它支持 text-to-video-and-audio、首/尾帧控制，以及图片/视频/音频参考驱动的生成；公开 H3-Base 本地输出以 768p 为基线，官方完整 2K 流程仍依赖未开源的托管 `H3-Context-IR` 与 `H3-Regenerate-2K`。[MiniMax 官方模型仓库](https://github.com/MiniMax-AI/MiniMax-H3#system-overview)

对单张 RTX 5090（32 GB VRAM）的结论是：

- **适合做本地实验性 `generated_video` Provider**：优先使用 ComfyUI 原生 H3 workflow、AdaLN-pruned `INT8 ConvRot` DiT、量化 Qwen3-VL-32B text encoder，并接受 CPU/RAM offload、较长生成时间和量化质量差异。ComfyUI 官方教程给出的默认本地文件组合就是 `minimax_h3_*_pruned_int8_convrot` + `qwen3vl_32b_minimax_h3_nvfp4_awq` + video/audio VAE。[ComfyUI 官方教程](https://docs.comfy.org/tutorials/video/minimax/minimax-h3#minimax-h3-text-to-video-t2v)
- **不适合把官方原始 BF16 checkpoint 作为单卡 production baseline**：单个原始 DiT 约 61.73 GiB，尚未计入 text encoder、VAE 和 activation；MiniMax 官方 integration index 的 24 GB 首跑建议依赖裁剪/量化与分阶段装载，而非完整 BF16 常驻。[MiniMax 官方组织的 integration index](https://github.com/MiniMax-AI/awesome-minimax-h3-integration#by-vram-and-hardware)
- **不应宣称“本地完整 2K H3”**：开源的是 H3-Base；`H3-Context-IR` 和 `H3-Regenerate-2K` 未开源，官方 full-2K workflow 需要 MiniMax API、凭据和云端媒体交换。[MiniMax 官方架构说明](https://github.com/MiniMax-AI/MiniMax-H3#h3-context-ir)
- **Provider 定位正确，但必须是显式 opt-in**：H3 应被建模为 video/audio generation capability，而不是对话、规划或通用 Agent Provider。首个本地 slice 建议只接 `FL2VA`（覆盖 T2VA/I2VA/首尾帧），将更重、更复杂的 `Ref2VA` 与云端 2K 分开评估。

## Release and Model Identity

MiniMax 于 2026-07-31 宣布 H3，并表示权重将在随后数日开放；当前官方 GitHub 与 Hugging Face 已提供模型代码/权重入口，所以准确说法是 **open weights under a custom community license**，不是 OSI 意义上的宽松开源软件。[MiniMax 发布文章](https://www.minimax.io/blog/minimax-h3) · [官方 GitHub](https://github.com/MiniMax-AI/MiniMax-H3) · [官方 Hugging Face](https://huggingface.co/MiniMaxAI/MiniMax-H3)

H3 的主要产品身份是多模态音视频生成：输入可包含 text、image、video、audio；输出为最高 15 秒、24 FPS、带 32 kHz stereo audio 的视频。公开 variant 如下：[官方模型卡镜像](https://github.com/MiniMax-AI/MiniMax-H3#model-variants-and-input-specifications)

| Variant | Capability | Input boundary | Local open-weight output |
|---|---|---|---|
| `H3-Base-FL2VA` | `t2va`, first/last-frame `fl2va` | text + 0–2 keyframe images | 768p video + stereo audio |
| `H3-Base-Ref2VA` | `ref2va`, including V2V | text + up to 9 images, 3 videos, 3 audio clips; maximum 12 files | 768p video + stereo audio |

完整 H3 system 由 `H3-Context-IR`、`H3-Base`、`H3-Regenerate-2K` 三部分组成；只有 Base 已开放权重。官方明确指出 Context-IR 是多模型/服务组成的 hosted preprocessing system，而 Regenerate-2K 也尚未开源。[官方 system overview](https://github.com/MiniMax-AI/MiniMax-H3#system-overview)

## Architecture and Weight Footprint

H3-Base 包含：

- 使用完整 Qwen3-VL-32B 权重的 `H3-Encoder`；
- `H3-VisualVAE`（`f16t4d24`，visual token 的有效空间下采样为 32×、时间下采样为 4×）；
- 独立 `H3-AudioVAE`；
- 33B dense single-stream `H3-Omni-Transformer`，其中约 13B 参数位于 AdaLN branches。AdaLN 输出在固定推理配置下可预计算，但官方原始 checkpoint 仍包含完整 branches。[官方 architecture](https://github.com/MiniMax-AI/MiniMax-H3#model-architecture)

初始开放版本仅提供 full attention inference；官方 sparse-attention implementation 尚待后续发布。这会让当前消费级显卡部署比模型最终设计目标更吃显存与算力。[官方 H3-Base 说明](https://github.com/MiniMax-AI/MiniMax-H3#h3-base)

官方原始 checkpoint 是 BF16。MiniMax 官方组织维护的 integration index 给出的文件规模显示：每个 FL2VA/Ref2VA 原始 DiT 为约 61.73 GiB；完整官方模型仓库同时包含两个 task family、text encoder 与 VAEs，总下载集合很大，因此应只下载实际需要的一个 task family。[官方下载建议](https://github.com/MiniMax-AI/MiniMax-H3#local-deployment-of-h3-base) · [integration checkpoint table](https://github.com/MiniMax-AI/awesome-minimax-h3-integration#checkpoints)

## Single RTX 5090 Feasibility Matrix

下表的“可行”指能启动本地生成实验，不代表所有组件同时常驻显存，也不代表官方 BF16/2K 品质。量化文件多为 community conversions；MiniMax 的官方 release 只有 BF16 checkpoints，官方 integration index 也明确要求逐个核验 runtime compatibility 与 license。[MiniMax integration quantization notice](https://github.com/MiniMax-AI/awesome-minimax-h3-integration#quantized-models)

| Path | Representative weight footprint | Single 32 GB RTX 5090 | Evidence level | Assessment |
|---|---:|---|---|---|
| Original BF16 H3-Base | DiT alone ~61.73 GiB, plus Qwen3-VL-32B encoder, VAEs and activations | No, not as resident single-GPU baseline | Official weights/sizes | 不合适；即使 aggressive CPU offload，仍没有官方单卡验证，吞吐和 host RAM 风险很高 |
| Official SGLang lossless BF16/FP32 with layerwise offload | Verified peak 26.3 GiB **per GPU**, but on 2×5090 + 377 GiB host RAM | Not officially supported on one card | Upstream SGLang measured run | 官方验证下限是双卡；50-step 1344×768×5s 用时 559.67s，不应外推为单卡 production SLA |
| ComfyUI AdaLN-pruned INT8 ConvRot DiT + NVFP4/AWQ TE | DiT 19.53 GiB; TE 14.61 GiB; VAEs loaded/offloaded separately | Yes, experimental | Official ComfyUI recipe; quant/repack path | **推荐首跑**；依赖 sequential loading/offload，VRAM 不能只按文件大小相加判断 |
| Pruned NVFP4 / mixed INT4-INT8 / W4A8 | DiT roughly 10.56–18.92 GiB depending conversion; TE and VAEs additional | Yes, more headroom | Community conversions catalogued by MiniMax official org | 显存更稳，但质量、node/runtime patch、许可证与 reproducibility 风险更高 |
| GGUF low-bit | DiT roughly 3.78–24+ GiB depending quant; separate reduced TE still needed | Technically possible | Community only | 适合容量探索，不建议作为首个 production-quality contract；最小档明确存在明显质量下降 |

官方 SGLang 的 RTX 5090 capacity run 只验证了 `2× RTX 5090` 的 TP2 layerwise-offload topology，使用约 384 GiB-class system RAM。其完整 50-step、1344×768、5 秒请求耗时 559.67 秒；5-step 实验约 78 秒。该结果说明 H3 在消费卡上“能跑”与“适合作为低延迟 Provider”是两回事。[SGLang H3 deployment guide](https://docs.sglang.io/cookbook/diffusion/MiniMax/MiniMax-H3#3-serve-minimax-h3) · [RTX 5090 capacity run](https://docs.sglang.io/cookbook/diffusion/MiniMax/MiniMax-H3#rtx-5090-capacity-run)

MiniMax 官方组织的 community index 给出更现实的消费卡路线：24 GB 首跑用 pruned INT8 ConvRot DiT + reduced TE；RTX 50-series 可采用 Blackwell 优化 attention 路线。但这部分是社区集成索引，不是 MiniMax 对单卡质量、速度或稳定性的保证。[官方组织 integration index](https://github.com/MiniMax-AI/awesome-minimax-h3-integration#by-vram-and-hardware)

## Current Host Evidence

本机只读检查于 2026-08-17 完成，当前状态足以进入受控 feasibility smoke，但尚不能当作 H3 已部署或已通过运行时验收：

| Surface | Verified current state | Implication |
|---|---|---|
| GPU | NVIDIA GeForce RTX 5090；32,607 MiB VRAM；检查时约 29,485 MiB free；compute capability 12.0 | Blackwell 硬件适合量化路线，但桌面进程已占约 2.6 GiB，首跑必须记录真实 peak VRAM |
| Driver/runtime | NVIDIA driver 595.84；`nvidia-smi` CUDA 13.2；AI-VIDEO Python 可用 PyTorch 2.9.0+cu128 | CUDA 基础链路正常，不再存在“GPU 未被 NVIDIA runtime 识别”的阻塞 |
| ComfyUI | `/home/reggie/ComfyUI` 为 0.31.0，H3 native nodes 已存在；专用 env 为 PyTorch 2.11.0+cu128，`comfy_kitchen` 已安装 | 已超过 ComfyUI 官方 `>=0.30.0` 要求；但官方 H3 repack 对 diffusion model 建议 `int8_convrot` 配合 cu130，当前 cu128 环境应先走 `fp8_scaled`，或在隔离环境升级到 cu130 后再验证 INT8 |
| Host RAM | 93 GiB total，检查时约 83 GiB available；40 GiB swap | 足够尝试 ComfyUI sequential loading/offload，但远低于 SGLang 双 5090 无损配置使用的 377 GiB host RAM |
| Storage | 根卷约 2.9 TiB free | 单个 FL2VA Comfy 量化组合约需 40 GiB 权重空间，磁盘不是阻塞；仍应只下载一个 task family |
| Existing weights | 当前 ComfyUI model directories 未发现 H3 / Qwen3-VL-32B H3 权重 | 尚未下载、部署或生成；结论仍是 feasibility assessment |

Comfy-Org 当前推荐组合的文件体积约为：pruned INT8/FP8 DiT 19.5 GiB、NVFP4/AWQ text encoder 14.6 GiB、video VAE 4.85 GiB、audio VAE 0.56 GiB。总文件大于单卡显存，所以可行性依赖 ComfyUI 的 staged load/offload，而不是全部同时驻留。文件与路线来自 [ComfyUI 官方 H3 教程](https://docs.comfy.org/tutorials/video/minimax/minimax-h3#minimax-h3-text-to-video-t2v) 和 [Comfy-Org 官方模型仓库](https://huggingface.co/Comfy-Org/MiniMax-H3)。

为保护现有 Wan 运行环境，推荐使用独立 ComfyUI Python environment、独立 model path 和独立端口做 H3 smoke；不要原地替换当前已工作的 CUDA/PyTorch 组合。该隔离建议是基于本机状态与回归风险的工程判断，不是 MiniMax 官方要求。

## License and Provider Risks

权重采用定制的 `MiniMax H3 Community License Agreement`，不是 Apache/MIT。关键条款包括：[官方 LICENSE](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE)

- 许可的 `Applicable Territory` 排除 European Union、United Kingdom、Republic of Korea 和 United States；在排除地区部署或使用需要另行取得授权。
- 商业产品或服务年收入超过 USD 20 million 时，需要 MiniMax 的事先书面授权；商业 UI 还必须显著展示 `MiniMax H3`。
- 对外提供 Hosted Service 时，需要让用户接受至少同等保护的使用限制，并持续实施、测试和审查合理的技术/组织 safeguards，以及违规举报与处置机制。
- 不得使用 H3 Works 或 Outputs 改进 H3/H3 derivatives 以外的 AI model。
- MiniMax 不主张生成 Output 的权利，但使用者对 Output 与后续用途承担责任。

因此，把 H3 加入 AI-VIDEO Provider 之前必须把 license territory、下游用户条款、内容安全、输出 AI 标识和商业展示要求作为独立 release gate。即使纯本地运行也不豁免这些条款。

## Recommended Provider Positioning

建议把 H3 定位为：

> Optional, explicit-opt-in `generated_video` Provider that can emit a short visual asset with synchronized native audio, with separate local-768p and hosted-2K capability profiles.

不建议将其定位为：

- 通用 LLM、Agent planner 或 prompt-rewrite Provider；
- 当前本地 Wan/ComfyUI default 的无条件替代；
- 默认 remote fallback；
- “完全本地 2K”能力。

推荐分层：

1. **Local H3-Base FL2VA preview Provider**：单 RTX 5090、ComfyUI、官方教程指定的 pruned INT8/NVFP4 文件组合；只承诺 768p short-edge、T2VA/I2VA/first-last-frame 与同步音频。先做离线 manual benchmark，不写入产品 runtime。
2. **Local Ref2VA experimental capability**：单独 checkpoint、单独磁盘预算与验收，覆盖 image/video/audio reference；不能与 FL2VA checkpoint residency 混为一谈。
3. **Hosted H3 2K Provider**：若未来获批，必须作为 remote/paid/cloud-egress capability，采用 MiniMax API 的 Context-IR/Regenerate-2K，经过 Budget Guard、egress、task persistence/resume 与 license gates。

由于 H3 的 native audio 与当前 production audio/voice/caption contract 可能重叠，Provider contract 应明确 H3 音频是候选 generated asset stream，不能直接绕过现有 `ResolvedTimeline`、voice/caption ownership 或 final composition activation。

## Uncertainties and Required Validation

- 本评估没有下载权重、安装 runtime 或运行推理；所有性能结论均来自官方/上游文档。
- 单卡 5090 的 ComfyUI quantized path 有明确 recipe，但未找到由 MiniMax 或 ComfyUI 发布的统一 single-5090 latency/peak-VRAM benchmark；实际结果依赖分辨率、时长、steps、attention backend、RAM/offload 与具体 quant。
- MiniMax 官方组织的 integration index 明确包含 community conversions；每个量化 checkpoint 的 license、hash、node dependency、质量损失与来源都必须单独核验。
- 官方 sparse attention 与本地 `H3-Regenerate-2K` 尚未发布，后续可能显著改变显存/速度结论。
- 应在任何实现授权之前验证主机的可用 system RAM、磁盘空间、CUDA/PyTorch/ComfyUI compatibility 和现有 ComfyUI workspace 是否能隔离这些大权重。

## Recommended Next Step

先做一个 **不改 AI-VIDEO runtime 的 bounded local feasibility smoke**：在隔离的 cu130 ComfyUI 环境中只下载 FL2VA 所需的 pruned INT8 ConvRot DiT、NVFP4/AWQ text encoder 和两个 VAE；如果暂不升级 cu130，则改用官方 fallback `pruned_fp8_scaled`。生成 4–5 秒、低分辨率与 1344×768 两档样本，记录 cold-load time、peak VRAM、peak system RAM、generation time、输出 MP4 streams、音画同步和 determinism。只有结果达到可接受门槛后，再为 H3 Provider 单独写 implementation plan；计划应把 local 768p 与 hosted 2K 分成两个 capability/backend，不应合并授权。

## Sources Inspected

- [MiniMax H3 launch article](https://www.minimax.io/blog/minimax-h3)
- [MiniMax H3 official repository/model card](https://github.com/MiniMax-AI/MiniMax-H3)
- [MiniMax H3 official Hugging Face repository and license](https://huggingface.co/MiniMaxAI/MiniMax-H3)
- [MiniMax official-organization integration index](https://github.com/MiniMax-AI/awesome-minimax-h3-integration)
- [SGLang MiniMax-H3 deployment guide and benchmarks](https://docs.sglang.io/cookbook/diffusion/MiniMax/MiniMax-H3)
- [ComfyUI native MiniMax H3 tutorial](https://docs.comfy.org/tutorials/video/minimax/minimax-h3)
