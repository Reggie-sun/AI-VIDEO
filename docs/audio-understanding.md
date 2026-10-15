# Project Audio Understanding Tool

## Native Audio Delivery

用户只要求MCP把原音频直接送给当前Codex、且不接受额外识音模型时，先核验原生输入路线：现有`filesystem.read_media_file`可返回`AudioContent`（`type=audio`、`mimeType=audio/wav`、base64 data），见[MCP协议](https://modelcontextprotocol.io/specification/2025-06-18/server/tools#audio-content)。协议可表达音频，不证明当前host/model会交付或理解音频；不能仅凭工具成功、JSON里有data或能播放就声称听过。

2026-10-15本会话用现有4.032秒历史WAV实测：MCP structured content含audio/wav，但模型可见content被替换为`audio content omitted because you do not support audio input`；再用原生audio helper转交同一payload，仍被省略。本会话直听路线为`UNSUPPORTED_THIS_SESSION`，声音语义/human acceptance仍`NOT_EVALUATED`。这只约束该会话及实际路线，不推论所有Codex客户端或未来窗口。证据见[session record](record_for_agent/2026-10-15-audio-understanding-mcp.md#native-audio-input-probe)。

WAV/MP3/base64转码、波形、频谱、响度或静音统计不能补出对白及表演语义；这类输出只能支撑其实际测得的声学事实。原生输入受阻时保留`EVIDENCE_REPAIR_FIRST`，恢复条件是host/model路径真正交付音频并取得可核验听音证据。用户禁止额外模型时，不自动改走下文Gemini或另装ASR/本地识音模型；原有Per-Shot Gate、exact identity和human1.0x要求保留。

## Entry And Evidence Boundary

项目本地`video-analysis` MCP注册`audio_understand`，用Gemini官方音频理解接口补充语音内容、声线/语气和环境声观察。它接收原MP4或PCM WAV；不要求Codex主模型能接收audio content，也不强制Qwen/ComfyUI。`video_transcribe`仍是Whisper转写入口，不能据转写文字推断音色、求证表演或完整聆听。[官方能力](https://ai.google.dev/gemini-api/docs/generate-content/audio)

当前实现是可测试的MCP/adapter/逐镜证据接点；没有已绑定的qualified Gemini operator或本项目实际模型听音结果。官方文档的模型能力、mocked tests、正常decode和preview均不证明原片声音PASS。模型生成时间戳是估计，不是sample/frame测量；精确对白时窗须另有实际证据，原`ResolvedTimeline`独占剪辑/混音时序。用户完整1.0x听看与raw逐镜Gate独立。[研究及限制](research/2026-10-15-audio-understanding-tools.md)

## MCP Parameters

```json
{
  "media_path": "/absolute/project/runs/selected/exact.mp4",
  "expected_sha256": "exact lowercase 64-character SHA-256 of that file",
  "execute": false
}
```

上例路径/hash须替换为已实测的exact media，不是可提交fixture。`execute=false`默认只做无网络preview：封存source SHA/bytes、分析WAV SHA/bytes/duration/source audio clock offset、exact模型/endpoint/request fingerprint，不导入runtime、不取credential、不上传。只接受配置的项目媒体目录内regular no-follow `.mp4`/`.wav`，source<=128MiB、完整音轨<=120秒、inline wire body<=20MB。视频仅临时提取原完整音轨为PCM derivative，不改原MP4、原生音轨或最终composition。

MP4的probe和decode均显式固定MOV/MP4 demuxer、file-only protocol并关闭external track与absolute alias，不能按扩展名自动识别HLS/concat后读取目录外音轨；相关选项见[FFmpeg官方说明](https://ffmpeg.org/ffmpeg-formats.html#mov_002fmp4_002f3gp)。组合`video_analyze`先完成本地处理，拒绝无效参数后才可能调用远端，避免已知无效请求消费授权。

`execute=true`才请求真实分析；缺qualified runtime立即EVIDENCE_REPAIR_FIRST/KNOWN_NO_EFFECT且无POST。工具/模型只输出`segments`、`voice_description`、`delivery_description`、`background_sounds`、`uncertainties`，没有自签PASS、人类听过或activation。盲观察prompt不含剧本预期台词，后续selected evaluator再对照原句/时窗/声线/嘴部证据。

## Trusted Operator Binding

`ServerConfig.audio_media_root`是absolute允许目录（源码运行时默认当前repository）；`audio_model_id`默认`gemini-3.8-flash`，只是当前官方接口表达选择，不能据名称宣称account/profile已qualified。`audio_runtime_factory`是可信、已安装的`module:function`，只能由operator配置，不能作为MCP调用者参数。三项是non-secret运行接线，不含API key；不自动加载.env或搜其他secret source。

Factory返回`ai_video_mcp.tools.audio_understand.AudioUnderstandingRuntime`：

- `analyzer`为`GeminiAudioAnalyzer`，其credential仅经exact injected supplier获得；从不使用ambient `GEMINI_API_KEY`或把key塞进JSON/argv/log。
- `permit_supplier(exact_preview)`须重验真实selected model/profile/window、authorization、预算reservation、egress和durable intent，返回有`validate(preview)`/`consume(preview)`的实际一次性capability，两方法成功返回literal `True`。不能用固定True、caller JSON或测试Permit代替真实门。
- 现有Production Paid owner没有audio-analysis operation；此接入没有擅自把它标作image/video_generation或创建第二Product ledger。真实audio runtime未绑定时保留阻断，不把接口的permit Protocol当作已经实现/qualified的外部授权owner。

一旦真实runtime齐备，adapter重编当前request核验完整source/audio/model/wire preimage，先验证permit，再取exact supplier、消费一次capability，最后固定Google origin只POST一次。不redirect/retry/Files API/fallback。UNKNOWN立即停止，调查原调用；credential failure、wrong SHA/permit、source drift均不发送新的调用。响应不留raw HTTP/key，保存actual modelVersion及response SHA，所有错误保持secret-safe。

## Per-Shot Review Integration

普通`video_analyze`兼容原默认输入/输出，`understand_audio=false`不会触发远端。显式`understand_audio=true`时必须传`expected_sha256`，音频观察作为`audio_understanding`进入原MCP response；音频缺失/error不能只返回视觉PASS来推进。

`CanvasProductionService.evaluate(..., understand_audio=True)`和`review_generation_attempt(..., understand_audio=True)`沿原exact fetched MP4→project-local MCP→selected evaluator/presentation→committer路径。`ProjectAnalysisSession`可从trusted operator注入`audio_runtime_factory/audio_media_root/audio_model_id`，仅传non-secret接线至隔离MCP进程；audio observation须与fetched SHA/size一致并带request/audio/response hashes与actual model identity，strict evidence重开拒绝错source。既有review要求缺audio时必须显式evidence repair，不重新生成视频补证。

这不新建QA authority、不自动批准任何finding、不改变原QA profile/hash、原生音轨/字幕、canonical trim或HyperFrames。未登记selected QA/qualified声音证据、首帧失败或任一required finding FAIL/NOT_EVALUATED时，原S01→S02仍停止；工具成功本身不移除这些条件。

## Agent Procedure

1. 读取原Shot声音要求与[Per-Shot Gate](../.agent/context/control-plane-playbook.md#per-shot-post-media-gate)，固定exact文件/hash；先preview核对完整出网内容与来源。
2. 使用实际qualified operator，核验一次调用的supplier、模型/窗口、有限预算/计数、egress、intent/permit；缺失保留EVIDENCE_REPAIR_FIRST，不搜key、不跑未授权云端测试。
3. 取得真实观察后逐条判断原广播/对白、声线/语气、环境与噪声；精确时序/同步另验。不可把ASR同音错字直接当姓名错读，也不能在观测前向转写模型提供目标句补答案。
4. 只经原QA/presentation/evidence/committer记录，raw全PASS才actual handoff与下一镜；最终成片还须原速听看。Model-only判断不得标human。
