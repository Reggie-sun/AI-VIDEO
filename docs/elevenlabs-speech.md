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
其他既有 adapter model 调用保持显式 language 参数行为；不宣称任意新模型兼容。

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
