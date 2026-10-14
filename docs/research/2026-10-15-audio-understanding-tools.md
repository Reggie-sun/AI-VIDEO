# Audio Understanding Tool Research — 2026-10-15

## Decision

有可以听音频的模型接口。最匹配这次《界蚀》S01/S02核验的是 Google 官方 Gemini API 的两项能力：`gemini-3.5-transcribe`适合核对普通话原句、说话人标签与词级时间戳；Gemini Audio Understanding适合补充描述音频事件、说话语气和回答针对声音的问题。Google官方文档明确列出转写、speaker diarization、speech/music emotion detection及带时间戳片段分析；普通话（简体）的BCP-47代码为`cmn-Hans-CN`。[Audio Understanding](https://ai.google.dev/gemini-api/docs/audio) [Gemini 3.5 Transcribe](https://ai.google.dev/gemini-api/docs/transcribe) [模型卡](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-transcribe)

这证明“有可用接口”，不证明本项目已有可调用的Gemini音频工具，也不证明该模型会正确通过《界蚀》的声音Gate。本次只做了在线资料和公开源码核查，没有上传音频、发API请求、安装依赖或下载模型；实时效果与本项目集成均为`NOT_EVALUATED`。

## Fit For S01 And S02

对4秒左右的原始镜头，先用`gemini-3.5-transcribe`逐字模式，并给出已知普通话语言提示；需要验证词级区间时设置`mode.timestamp_granularities: ["word"]`。模型规格支持85种以上语言、普通话简体、词级时间戳和最多8位说话人；启用词级时间戳或说话人区分时，单请求最长音频为30分钟。官方也明确说明词级时间戳可能降低转写准确率，且自定义词汇不能与词级时间戳/说话人区分同时使用。[转写配置与限制](https://ai.google.dev/gemini-api/docs/transcribe#parameter-reference)

S01的首轮转写提示应要求逐字、不补写原句、不提供剧本预期答案，保留所有检测到的语音片段和时间；另一次对照时才把结果与“林砚，请在终点站下车。”及0.1–2.7秒要求比较。这样可降低提示把原句塞进模型输出的风险。词级时间戳可支持时间核验，但模型产出的时间仍要对照实际波形/逐段回放；音频模型不能判断林砚画面上是否张嘴，必须由同步画面分析负责。

S02应将转写结果与“刚才……叫的是我？”原句逐字比对，再单独询问声音是否像低声求证、是否存在喊叫感、停顿和吸气是否保留。Gemini Audio Understanding官方列出情绪检测能力，但该能力只是模型判断；它不等同于对表演质量的客观度量，也不能替代用户正常速度完整听看。官方普通音频理解示例的部分代码以YouTube视频输入展示时间戳/情绪结构输出，因此不要把该示例的输出时间格式或精度当成精确口型/声画同步保证。[音频理解能力与示例](https://ai.google.dev/gemini-api/docs/audio)

## Tool And Integration Assessment

官方音频转写文档给出`@google/genai` JavaScript SDK路径：调用`client.files.upload`，再调用`client.interactions.create`，指定`gemini-3.5-transcribe`并传入音频URI。短音频也能通过inline audio输入；官方文档建议超过20 MB用Files API。Gemini Files API单文件上限2 GB、每项目20 GB，上传文件自动保留48小时，也支持显式删除。[Audio input](https://ai.google.dev/gemini-api/docs/audio#input-audio) [Files API retention and deletion](https://ai.google.dev/gemini-api/docs/files#delete-uploaded-files)

公开社区MCP候选[`salviz/gemini-mcp-server`](https://github.com/salviz/gemini-mcp-server)确实实现了`gemini_analyze_audio`，MIT license；截至本次检索，GitHub显示1 star、5 commits且没有release。[Repository](https://github.com/salviz/gemini-mcp-server) [MIT license](https://github.com/salviz/gemini-mcp-server/blob/main/LICENSE) 源码检查发现：

- `gemini_analyze_audio`读取调用者传入的绝对路径，并把文件字节作为inline base64或Files API上传给Google；小于等于20 MB走inline，大于20 MB走上传。两条路径都将完整音频发给远端。[audio handler](https://github.com/salviz/gemini-mcp-server/blob/main/tools/chat.js#L218-L243) [file preparation](https://github.com/salviz/gemini-mcp-server/blob/main/tools/chat.js#L60-L111)
- 它默认`gemini-3.1-pro-preview`，但工具可传模型名；音频handler调用通用`models.generateContent`，没有暴露专用`gemini-3.5-transcribe`的`transcription_config`、词级时间戳或说话人分离参数。因此README虽称可“transcribe”，这个实现不能直接提供这次需要的专用转写合同。[shared model config](https://github.com/salviz/gemini-mcp-server/blob/main/tools/shared.js#L0-L21) [audio handler](https://github.com/salviz/gemini-mcp-server/blob/main/tools/chat.js#L218-L243)
- 路径校验只检查“绝对路径且文件存在”，没有将路径限制在项目媒体目录；与本项目只让工具读取被明确选中的项目媒体的边界不符。该MCP要求环境变量`GEMINI_API_KEY`，因此也不能未经适配就满足项目的exact injected supplier凭据合同。[path validation](https://github.com/salviz/gemini-mcp-server/blob/main/tools/chat.js#L60-L68) [credential initialization](https://github.com/salviz/gemini-mcp-server/blob/main/tools/shared.js#L0-L7)
- GitHub显示该仓库没有release、只有5次提交和1个star；`package.json`依赖版本使用caret范围，仓库另有`package-lock.json`。这说明它是较小的社区封装，不能仅凭MIT许可或README描述当作已审计的生产入口；本研究没有核对lockfile完整性、安装结果或依赖安全。

**建议不直接接入这个23工具的宽泛MCP。** 若现有project-local `video-analysis` owner可接受音频分析能力扩展，优先在该唯一owner上使用官方`@google/genai` SDK实现窄接口：仅允许当前attempt的精确音频文件、`realpath` containment、固定模型与schema、固定的最少调用数、明确记录模型/API版本与输入SHA；通过现有injected credential supplier注入key；上传成功后记录Files API file name并清理，失败/超时标`NOT_EVALUATED`并停止，不能把错误或空转写判成PASS。是否扩展该owner、当前runtime是否有凭据/预算/许可，须Parent按现有Provider和Gate合同核验；本研究未授权或执行调用。

## Local And Timing Alternatives

Qwen官方`Qwen2-Audio-7B-Instruct`支持“音频+文字指令”的本地音频分析，模型卡标Apache-2.0；官方repo建议片段小于30秒，展示Transformers加载7B模型。它可以作为已经安装且运行条件合适时的本地隐私候选，但不能假设当前主机已安装、显存足够或已取得有效音频语义证明；本研究没有下载模型。[Qwen2-Audio official repository](https://github.com/QwenLM/Qwen2-Audio) [model card](https://huggingface.co/Qwen/Qwen2-Audio-7B-Instruct)

WhisperX适合做转写对齐的补充，不是音色/情绪审听器。其仓库提供ASR、强制对齐和词级时间戳，含`zh`默认对齐模型映射；但README说明重叠语音处理较弱、speaker diarization并不完美、缺少语言对应对齐模型时需自备并验证。[WhisperX README](https://github.com/m-bain/whisperX) [Chinese alignment model mapping](https://github.com/m-bain/whisperX/blob/main/whisperx/alignment.py#L28-L40) 另需确认当前主机已经安装与缓存合适的模型；不要仅为本次阻塞自动安装依赖或下载新模型。

## Data And Evidence Boundary

Gemini API会将音频发送给Google。Google当前条款区分免费与付费API项目：免费服务的提交内容可能用于改进产品且可能由人工审核；付费服务不使用prompt/files/response改进产品，但仍会为滥用监控有限期记录。Files API文件独立于日志留存，需主动删除或等待过期。是否属于付费服务取决于API实际关联的Cloud Project billing状态，不由MCP名称或“本地运行MCP”决定。[Gemini API terms](https://ai.google.dev/gemini-api/terms) [zero-data-retention conditions](https://ai.google.dev/gemini-api/docs/zdr) [Files API](https://ai.google.dev/gemini-api/docs/files)

因此把该generated audio交给Google API之前，必须由Parent核对exact injected supplier、当前账号/项目的付费与数据处理模式、现有音频QA许可、预算和egress合同。在线查到的能力、SDK示例、ASR转写、分析工具输出、波形/响度与“音轨存在”只能补充证据，不能替代S01/S02逐项声音Gate或用户1.0x完整听看。当前音频输入阻塞可恢复为“接入或使用一个已可用的音频理解/转写工具并完成项目内验证”；在此之前声音语义状态保持`NOT_EVALUATED`。

## Source Scope

在线资料和GitHub `main`源码按2026-10-15检索；GitHub页面未向本次浏览器提供可独立验证的commit SHA，故没有声称固定源码revision。未执行远端代码、未安装软件、未调用模型、未发送媒体或凭据。所有工具在本项目runtime的可用性、当前产品账号条款、输出质量及真实性能仍待项目内核验。
