# ElevenLabs Speech

## Runtime Contract

独立配音可显式使用 `ElevenLabsVoiceProvider`，由现有 P4 request、preview、paid gate、
`ProductionStateCommitter`、Registry 和 candidate materializer 管理。默认模型
`eleven_multilingual_v2`，支持 `zh` / `en`；输出为 mono 48,000 Hz PCM s16le WAV，
字符 alignment 保留在 canonical voice receipts，字幕仍归 `CaptionTrack`，时间仍归 `ResolvedTimeline`。

依据 [官方带时间戳 TTS API](https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps)
（2026-10-29 核对），POST 路径为 `/v1/text-to-speech/{voice_id}/with-timestamps`，
`output_format=pcm_48000` 在 query，认证为 `xi-api-key`。multilingual v2 不支持
`language_code`，语言保存在 sealed request/provenance，不发送该 wire 参数。
`eleven_v4`（2026-10-30 `/v1/models` 核对：支持 zh，`can_use_style`／`can_use_speaker_boost` 为 false）
可用 `--model-id eleven_v4` 显式选择：发送 `language_code`，默认 voice settings 只含
stability／similarity_boost／speed；带 style 或 speaker boost 的 v4 请求在消费 permit 前以
`VOICE_REQUEST_INVALID` 拒绝。v2 默认值与既有 batch 哈希不变。
其他既有 adapter model 调用保持显式 language 参数行为；不宣称任意新模型兼容。

真实 2026-10-29 zh 响应（multilingual v2）与官方文档有两处差异，adapter 按证据处理：
顶层多一个未写入文档的 `quality_check`，只接受 `null`、不落盘，其他值或其他未知字段仍 fail closed；
`normalized_alignment` 为带空格拼音（如 ` Ji Shang ,Di Shi Si Qi `），所以原文 `alignment`（NFC）
或 `normalized_alignment` 任一与台词逐字一致即可。字符对齐只证明 Provider 回报的文本，
不证明音频读对；读音仍须试听与逐镜 Gate。History API 返回的 `character_end_times_seconds`
是逐字时长而非结束时间，不能当作 with-timestamps 响应的证据。

## Entry

```bash
python -m scripts.elevenlabs_speech_batch \
  --root runs/elevenlabs-speech-unique-id \
  --source-project /absolute/path/to/production/project.yaml \
  --voice-id YOUR_AUTHORIZED_VOICE_ID \
  --text '什么？没报站啊。' \
  --unit-price-microunits "$ELEVENLABS_OPERATOR_UNIT_CEILING" \
  --per-call-ceiling-microunits "$ELEVENLABS_OPERATOR_CALL_CEILING" \
  --project-ceiling-microunits "$ELEVENLABS_OPERATOR_PROJECT_CEILING"
```

三个金额变量是 operator 预配置的正整数 USD microunits 上限，不是 credential，
也不是官方报价或用户必须另行批准的预算。缺配置不 submit；不得猜值、填零或套用 MiniMax
count-only 账本。`--text` 可重复形成有限有序批次，首个失败或 unknown 停止。
Python 入口为 `run_elevenlabs_speech_batch(root, batch, transport=..., credential=..., toolchain=...)`。

脚本创建独立音频测试 Production project，并只读记录 source Manifest SHA；不激活来源项目音轨。
同 root/exact batch 成功重开无新 POST，改变台词、音色、参数或预算拒绝复用 root；
失败或 unknown 需要显式 recovery，不能用新 root 自动重试。
真实 transport 不 retry、不 redirect；credential 仅在 wire 边界通过 exact Secret Service
`application ai-video / provider elevenlabs / credential ELEVENLABS_API_KEY` 获取，
不从环境、`.env` 或其他引用 fallback。lookup 失败因 permit 已消费而保守保留 UNKNOWN。

## Limits And Evidence

沿用 adapter 的 1 MiB raw PCM、2 MiB JSON 响应上限，48 kHz mono 对应约 10.9 秒音频。
批次每句独立生成，不承诺长台词自动分段或跨句无缝表演。超时、缺失/损坏 alignment、超限响应
均不能自动重试。`enable_logging=true` 使用 Provider 标准保留策略；未声明 enterprise zero-retention。
账户音色权限、PCM 输出资格及实际费用要由真实账户确认，不因本地配置变为已验证。

当前验证通过 fake transport 经真实 committer/loader、音频 probe、immutable receipts 和 Registry；
不等于真实 ElevenLabs 可用、音质/口型通过或成片验收。实际费用未由 Provider 报告时为未知，
reservation 保留。正式声音接回视频须经选中 route、P4 composition 与完整声画验收。

验证结果见[接入记录](record_for_agent/2026-10-29-elevenlabs-speech-integration.md)。

## Performance Controls

`VoiceProviderParameters.audio_tags` 是可选的封存表演提示，当前只允许显式
`elevenlabs/eleven_v4`；CLI 使用可重复的 `--audio-tag`。每次最多三个标签，
每个最多 120 字符，必须是无方括号和控制字符的 NFC 文本。
空标签不进入序列化，既有参数、batch/request hash 与默认 wire text 保持兼容。

`script_text`/`script_hash` 始终是原台词；`VoiceGenerationRequest.synthesis_text`
经 `elevenlabs_performance` 唯一编译器派生模型输入。参数定义归 `voice_parameters.py`，
原有 `audio.VoiceProviderParameters` 导入兼容。提示进入参数/request 指纹，预算 preview
按完整合成文本保守计字符/字节；paid egress 与 committer 校验绑定完整输入 SHA/bytes。
字幕、Registry 台词和对齐仍使用原台词，不把提示混入朗读文字或另建时间线。

[官方 v4 指导](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices#prompting-eleven-v4)
支持内嵌表演标签，但不保证每个提示有效或听感自然。本地先严格校验 Provider 两组原始时间数组；若其字符逐字等于已封存的 synthesis_text，
仅允许在字符条目边界投影本次编译的 exact tags 前缀，保留全部原始绝对时间。
映射后的原 alignment 或 normalized alignment 至少一组仍须逐字等于原台词。
receipt 的 synthesis_alignment 保留两组原始数组、exact prefix、输入 SHA 和原响应 body SHA；
无标签 receipt 字节保持兼容。非精确前缀、漏字/多字、跨条目边界或错误时间仍 UNKNOWN 停止，
不使用 History duration 数组补造时间，不泛化剥离括号、不自动重试。
对齐成功不证明标签没被读出，模型表演与逐字发音仍须原速试听。

## Shared Performance Context Entry

Codex 与 Claude 在同一 working tree 使用同一个显式 CLI，不需要复制台词或标签：

```bash
.venv/bin/python -m scripts.elevenlabs_speech_batch \
  --performance-context outputs/shizhen-episode01/opening-dispatch-20261029/performance-context.v1.json \
  --line-id L3 --preview-context
```

该模式只读、无网络、不读取凭据、不建 Production project；输出完整导演上下文、
选中原台词、经过校验并重新编译的模型输入、包 SHA 与 source plan SHA。
这是 authoring preview，不是 canonical paid preview 或执行授权。完整导演说明供 Agent
创作/审听，实际模型输入仍是选中行的 audio_tags + 原台词；没有暗中接入 Text to Dialogue。

执行时去掉 `--preview-context` 并提供原有 root、source-project、明确 voice-id、预算参数；
context 与 `--text`/`--audio-tag` 互斥，不能覆盖来源台词或模型。来源 plan SHA、ID、
role/unit/时长逐项核对，拒绝重复 key/ID、symlink、路径逃逸和超限 JSON。
包 SHA 与 line ID 封存进既有 batch source_reference，重开时沿 exact batch 校验。

当前开局包仍 BLOCKED，且保留 blocked_by_attempt 指针；实际执行在加载 Production、
取凭据和发请求前拒绝。READY_FOR_CANONICAL_PREFLIGHT 只表示输入没有该项额外限制，
不授予执行权限；原 permit、预算、egress、UNKNOWN/recovery 与验收仍由既有 owner 管理。
任何 unresolved 指针仍阻断，无 force 参数，不用改包字段冒充 canonical recovery。

## Nonoverlapping Audition Units

上下文包可声明 `excluded_line_ids`；入口在选行前拒绝被排除 ID，即使它仍出现在 rows 中。
前序 UNKNOWN 的原包、attempt、reservation 保留，不把它改为 READY。用户明确要求新的
试听时，只能为确实未提交的、不同的选中行封存不重叠的有限单元；记录 predecessor、
排除原因、新旧次数及预算。新包字段不代替授权或 canonical state，不允许借新文件/新root
重发被排除的未知请求。任何新 UNKNOWN 立即停止本单元。
