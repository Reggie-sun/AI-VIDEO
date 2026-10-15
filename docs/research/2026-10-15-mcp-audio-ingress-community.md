# MCP Audio Ingress: Community Findings

Research snapshot: 2026-10-15。用户要求MCP将原音频交给当前Agent理解，不增加另一个识音模型。调查区分协议、server、client/proxy、当前会话及backend；某一层支持音频不证明全链路已交付或听懂。

## Findings

1. **原生server路径已存在。** MCP schema允许tool result返回包含base64 `data`、`mimeType`的`AudioContent`；官方filesystem的`read_media_file`说明也支持原生image/audio返回。无需为传输再安装识音模型，但README未固定package release，不能据协议断言任意host接受音频。[MCP schema `2026-07-28`](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/schema/2026-07-28/schema.json)、[filesystem README](https://github.com/modelcontextprotocol/servers/blob/main/src/filesystem/README.md#tools)

2. **社区真实修复：保留content类型。** `mcpproxy-go` [issue #368](https://github.com/smart-mcp-proxy/mcpproxy-go/issues/368)报告上游返回的image/audio被整体序列化为普通`TextContent`，使下游失去原生内容类型。[PR #369](https://github.com/smart-mcp-proxy/mcpproxy-go/pull/369)于2026-04-09合并，改为保留非text blocks，仅截断text，并报告mock text/image/audio透传验证。它证明该proxy修复了传输问题，不证明音频模型听懂；上游页面未给出对应发布版本，且本项目未证实使用该proxy，不直接照搬补丁。

3. **Codex已实现透传，但按会话能力过滤。** [PR #33932](https://github.com/openai/codex/pull/33932)于2026-07-18合并，将原音频转为Responses API `input_audio`；[PR #34080](https://github.com/openai/codex/pull/34080)同日合并，加入MCP/dynamic tool audio及`audio()`。后者的[`sanitize_mcp_tool_result_for_model`](https://github.com/openai/codex/blob/643de86a190a38a5f4afa5e3a15edf48153f9c64/codex-rs/core/src/mcp_tool_call.rs)读取`input_modalities`，不含`Audio`时以omission文本替换音频。当前公开main仍有此检查；源码与本次placeholder匹配，但本机CLI、托管host和实际backend的exact版本/能力不能互相代签。

4. **转写fallback需要另一个模型。** [mcp-server-whisper](https://github.com/arcaputo3/mcp-server-whisper)的`transcribe_audio`调用`whisper-1`/`gpt-4o-transcribe`并要求API key；README还说明已停止维护并迁往其他项目。它能返回识别文字，但不满足用户不增加识音模型的约束，不在本次推荐安装范围。

## Bounded Comparison

| Route | Evidence | Fit |
| --- | --- | --- |
| Native `AudioContent` | 全链路保留音频且当前模型实际接受后，才可能取得原音频语义观察。 | 符合目标；缺host/model能力时MCP本身无法补足。 |
| Transcription adapter | 独立识音模型提供词句/估计时间戳。 | 不符合本次约束；转写文字不等于听过音色或表演。 |
| Waveform / spectrogram | 可测能量、停顿及频谱结构，参见[librosa RMS](https://librosa.org/doc/0.11.0/generated/librosa.feature.rms.html)和[STFT](https://librosa.org/doc/main/api/generated/librosa.stft.html)。 | 可辅助声学QA，不能证明词义、情绪或原句正确。 |

## Practical Implication

先核验server返回typed audio，再检查client/proxy有没有将它变成text或删除，最后绑定当前会话声明及真实backend的audio支持。只有发现可修复的具体接点才适配；不手改缓存伪造`audio`能力，不把base64当文字发送，也不据播放器或工具成功声称Agent听过。

本项目MCP/audio helper的实际omission、local cache的有限证据及下一恢复条件见[primary record](../record_for_agent/2026-10-15-audio-understanding-mcp.md#community-audio-ingress-diagnosis)。本次调查没有新模型调用、依赖安装、客户端升级或音频重提；当前语义QA仍未恢复。

## Native Subagent Follow-up

后续用户明确要求开subagent打通，原生子会话一次read与一次同payload转交也被省略。Parent检查内置catalog和[`gpt-6.1-sol`官方Modalities](https://developers.openai.com/api/docs/models/gpt-6.1-sol)，后者明确Audio `Not supported`；这为该profile的音频限制补上了官方能力依据。当前可见TUI建任务/发消息接口仅有text `prompt`，无audio附件字段；未发现已暴露的另一条可用原生入口。该追加实验及host/backend identity剩余边界归[同一primary record](../record_for_agent/2026-10-15-audio-understanding-mcp.md#native-subagent-ingress-attempt)；仍未恢复听音，没有新识音模型或Provider调用。

## Case Applicability And Active Host

“社区有透传修复案例”不能扩大为“当前Codex已存在可直接照搬的听音修复”。Parent追加核对真实复现、mock及Codex正/负测试后，收敛如下：

| Case | Proven condition | Applicability here |
| --- | --- | --- |
| `mcpproxy-go #369` | 真实复现用`get-tiny-image`；mock验证text/image/audio blocks透传，没有模型理解音频的断言。 | 本次outer返回exact omission，而非整个result的JSON文本；未发现可归因的同类扁平化缺陷。 |
| Codex unsupported-media test | `InputModality::Text`时断言audio替换为本次exact omission。 | 与本次现象匹配，不能用proxy透传补丁补齐模型能力。 |
| Codex supported-media test | 明确给出`Text,Image,Audio`才断言原结果保持不变。 | 正向测试是传输条件验证，没有证明当前模型/会话支持Audio。 |

测试锚点归[合并提交的实际965–1045行](https://github.com/openai/codex/blob/643de86a190a38a5f4afa5e3a15edf48153f9c64/codex-rs/core/src/mcp_tool_call_tests.rs#L965-L1045)，案例实证归[PR #369](https://github.com/smart-mcp-proxy/mcpproxy-go/pull/369)。Parent经工具子进程的`/proc` executable ancestry找到正在运行的app-server binary，版本`0.162.1`，SHA `628e35487d888a28f0427fc37501da529dd3d81fcbad7a2c3421c1e8670d92e1`；直接读取该binary的bundled catalog，11条均只声明`text,image`。Binary包含exact omission字串、`input_audio`及`input_modalities`，但字串存在不等于取得特定函数执行trace。当前恢复任务因此不能只凭社区案例宣称可由项目MCP补丁完成；实际host绑定与剩余backend identity边界归[primary record](../record_for_agent/2026-10-15-audio-understanding-mcp.md#active-host-and-case-applicability)。

## Evidence Gaps

- MCP历史[discussion #88](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/88)曾提出音频/客户端支持问题；未重测当前Claude，不以历史request判断今天能力。
- `mcpproxy-go`合并与Codex上游实现均不证明本项目实际运行对应代码，也不证明当前托管backend接受音频。
- 当前host executable已绑定，实时selected model metadata/backend response identity仍未绑定；父子会话均收到omission，blind audio理解结果仍缺失。不得通过降低逐镜声音验收标准来推进。
