# Suno Human Check And Local Song Options

Date: 2026-10-30 (America/New_York); sources checked 2026-10-31 UTC.

## Supersession Notice — Local Execution

用户随后明确要求运行，主会话已隔离安装 ACE-Step 并生成两条真实30秒音频，完整解码通过；原歌词输入未变，但两次自动转写均未覆盖完整原词，人工听感与完整歌曲资格仍未验收。当前运行证据、试听入口与边界见 [local audition record](../record_for_agent/2026-10-30-ace-step-local-iris-audition.md)。下文“未安装、未下载、未生成”是研究阶段的历史状态；Suno 真人验证与旧未知请求没有因此解决。

## Scope And Result

本次仅核对官方资料，回答 IRIS EP01 的 Suno 人工验证阻塞与独立本地歌曲候选。目标摘要为 30 秒英文女声、spoken-word verse + short sung hook、dark electroclash / minimal techno、126 BPM；不复制完整歌词或原 prompt。

不能使用解题器、token 导出或反机器人规避工具代过真人验证。本地歌曲模型可以独立生成另一份候选，但不代表 Suno 已恢复，也不能确定之前未知请求是否提交或结算。当前平台状态应读主会话的 [只读 receipt](../../outputs/ai-city-takeover/ep01/audio/suno-continuation-readback-20261031T0214Z/readback.json)，本文不更新其结论。

## Official Recovery Evidence

Cloudflare 的官方排障项包括支持的最新版浏览器、JavaScript、扩展干扰和稳定网络，并提供兼容性检查及诊断报告途径。这是恢复正常浏览器使用的指导，不是自动代过验证码的方法；也没有证明本次阻塞的具体原因。本轮未修改浏览器、扩展、账户或网络节点。[Cloudflare challenge solve issues](https://developers.cloudflare.com/cloudflare-challenges/troubleshooting/challenge-solve-issues/)

Suno 官方确认技术支持地址为 `support@suno.com`、账务支持为 `billing@suno.com`。若正常浏览器仍要求人工验证，平台恢复或支持处理仍是独立事项；本轮未发送邮件或代替用户处理验证。[Suno official support](https://help.suno.com/en/articles/2551617)

## Local Model Facts

| 项目 | ACE-Step 1.5 | HeartMuLa |
| --- | --- | --- |
| 本地入口 | 官方 Python API、Gradio、REST API；生成接口有 `caption`、`lyrics`、`vocal_language`、`bpm`、`duration`。[Inference](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/docs/en/INFERENCE.md) | 官方 `examples/run_music_generation.py`，读取独立 lyrics/tags 文件；有 `--max_audio_length_ms`。[README](https://github.com/HeartMuLa/heartlib/blob/5858ca8f1ffe58d62be7c007ea55f1033c5ca456/README.md) |
| 英语女声和歌词 | `vocal_language="en"` 有文档；教程将 `female vocal` 列为 caption 特征，歌词支持段落与表演提示。属于条件输入能力，不保证唱词或音色效果。[Tutorial](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/docs/en/Tutorial.md) | 官方有英语歌词示例和 lyrics + tags 条件生成；本次未找到女声确定控制承诺。女声效果及 spoken-word / sung 切换未验证。[README](https://github.com/HeartMuLa/heartlib/blob/5858ca8f1ffe58d62be7c007ea55f1033c5ca456/README.md) |
| 30 秒约束 | API 目标时长范围 10–600 秒；教程称 30–60 秒较稳定，同时明确实际时长可能偏移。完整唱词、自然收尾仍需实测。[Inference](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/docs/en/INFERENCE.md)、[Tutorial](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/docs/en/Tutorial.md) | `max_audio_length_ms=30000` 是上限，不是保证 30 秒完整音乐结构；可能在唱词完成前截止。[Official example](https://github.com/HeartMuLa/heartlib/blob/5858ca8f1ffe58d62be7c007ea55f1033c5ca456/examples/run_music_generation.py#L38-L75) |
| 环境和体积 | 官方要求 Python 3.11–3.12，核心模型磁盘约 10GB；2B/XL 与 LM 组合的显存需求不同。20–24GB 档公开支持 XL + 1.7B LM；XL 权重显存约 9GB。磁盘量与显存量不能混用。[Install](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/docs/en/INSTALL.md)、[GPU guide](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/docs/en/GPU_COMPATIBILITY.md) | 官方推荐 Python 3.10，需 HeartMuLaGen 元数据、HeartMuLa 模型及 HeartCodec；单卡可 `--lazy_load true`。本次未确认官方最小 VRAM 或完整下载体积。[README](https://github.com/HeartMuLa/heartlib/blob/5858ca8f1ffe58d62be7c007ea55f1033c5ca456/README.md) |
| License / 版本 | 代码 MIT，官方主模型卡也标 MIT；本次代码文档锚定 `ca1e85fe9430179831e6bc6be790c332190a3866`。[License](https://github.com/ace-step/ACE-Step-1.5/blob/ca1e85fe9430179831e6bc6be790c332190a3866/LICENSE)、[model card](https://huggingface.co/ACE-Step/Ace-Step1.5) | 官方代码及相关模型权重更新为 Apache-2.0，当前 README 推荐 `HeartMuLa-oss-3B-happy-new-year` + `HeartCodec-oss-20260123`；开源 7B 仍列为待发布。文档锚定 `5858ca8f1ffe58d62be7c007ea55f1033c5ca456`。[README](https://github.com/HeartMuLa/heartlib/blob/5858ca8f1ffe58d62be7c007ea55f1033c5ca456/README.md)、[model card](https://huggingface.co/HeartMuLa/HeartMuLa-oss-3B-happy-new-year) |

## Handoff And Verification Boundary

主会话传来的本机只读结果为 RTX 5090、32607MiB 总显存、23540MiB 空闲；已装 `torch` / `diffusers` / `transformers`，当前核查的 Python 环境未安装 `acestep` / `heartlib`，标准 Hugging Face cache 与所检 ComfyUI 目录未发现两者权重。研究者没有重复核查本机，因此这些只作为主会话提供的前提；不能从显存容量推出当前 Python/CUDA 栈已经兼容。

ACE-Step 的公开输入字段覆盖本次目标的歌词、语言、BPM、时长和女声描述，足以供主会话评估一个有界本地试验；这是文档能力映射，不是依赖采纳或成片质量推荐。若后续采用，需先固定代码与权重、检查实际安装栈及可用资源，再验证完整唱词、spoken/sung 变化、自然收尾、真实时长及音色。不得把替代模型产物记为 Suno 输出或关联到失败的 Suno request ID。

本轮只完成外部一手来源核对和本文档；未安装、下载权重、生成媒体、修改 Product state、运行代码测试、commit 或 push。音乐试听、歌词准确性、女声质量、口型、字幕时序和最终成片均为 `NOT_EVALUATED`。旧 Suno 未知请求与原预算历史保持原状。
