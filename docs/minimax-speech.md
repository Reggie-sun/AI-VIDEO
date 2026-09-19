# MiniMax Speech Configuration

## Runtime Contract

批量测试脚本现在默认国内站；官方 [国内同步语音 HTTP API](https://platform.minimaxi.com/docs/api-reference/speech-t2a-http) 为 `https://api.minimaxi.com/v1/t2a_v2`，Bearer authentication。`MiniMaxSpeechProviderPolicy.origin` 只允许国内站与历史国际站 `https://api.minimax.io`，不跟随 redirect、不自动 fallback。底层 adapter 的缺省 origin 保留国际站，保证旧调用者的 preview/hash 不变；新国内批次显式 seal `region=cn`，使用 CNY 作为账本币种标签，费用依然未知。

使用现有 `MiniMaxSpeechVoiceProvider`，显式注入 transport、`VoicePricingSnapshot`、credential capability 和 `MiniMaxSpeechProviderPolicy`。没有默认 Provider 或自动网络调用。当前 adapter 支持 `English` 和 `Chinese`，不自动猜测或转换语言标签。历史英文 request/hash 与输出规则保持不变。

官方 [HTTP API](https://platform.minimax.io/docs/api-reference/speech-t2a-http) 的 `language_boost=Chinese` 用于普通话；[系统音色列表](https://platform.minimax.cn/docs/faq/system-voice-id) 包含 `male-qn-jingying`。这些能力声明不证明本机账户、音质或具体台词时间窗通过。

## S03 Selection

当前用户选择 MiniMax Speech 为已保留的 S03 画面补对白。准备参数为 `speech-2.8-hd`、`Chinese`、系统音色 `male-qn-jingying`、`speaker_id=P2`、对白“什么？没报站啊。”、`speed_milli=1000`、mono 44,100 Hz PCM s16le WAV。音色是首个候选，不声称已试听或已成为跨镜头验收声线。0.50–2.60s 是最终对白覆盖目标，不得通过截断语音或伪造 alignment 宣称满足。

Secret Service lookup 的唯一操作引用见 [control-plane playbook](../.agent/context/control-plane-playbook.md#3-provider-credential-and-paid-execution-details)。配置只保存引用，不能复制密钥到 JSON、环境文件、命令参数或日志。

## Execution Boundary

MiniMax Speech development tests 使用 standing task scope，无需逐次向用户请示、无需用户提供金额预算。`MiniMaxSpeechTestBatch.scripts` 封存有限、按序的批次，列表长度就是本批次 submit ceiling；每次调用仍经 `ProductionStateCommitter.generate_voice_asset()` 的 durable voice intent、paid gate、count reservation 与内部 one-use permit。停止于首个失败或 unknown，不自动重试；相同 root / exact batch 的已完成调用只重开，不重复 Provider effect。新批次使用新的独立身份；不能用新批次自动重试 unknown。

`paid_provider.py` 的 `minimax_speech_batch` 模式仅接受 MiniMax Speech 的两个既有模型和上述两个 exact origins，账本绑定固定 `voice_batch_submit_limit`，不能混用视频金额账本。`max_submit_count=1` 仍限制每张内部 permit；它不是用户批准次数。`unit_price_microunits`、估算与金额上限使用 `null` 表示未提供，不填零、不使用历史免费资格。MiniMax 返回用量但未报告费用时，submit 为 ACCEPTED，reservation 为 RESERVED，`actual_cost_microunits=null`；语音资产可独立 SUCCEEDED，不能把费用未知等同于 submit outcome unknown。视频与 ElevenLabs 历史路径不变。

批次使用全新 bootstrap 的独立 Production project 和 authoring dependency graph，WAV 仍由既有 candidate/activation/Registry owner 注册；没有 composition/render consumers，不生成带声视频。来源 project 只读，source Manifest SHA 进入新项目 provenance；这不是 S03 recovery、正式音轨接入或音质验收。

## Test Entry

```bash
python -m scripts.minimax_speech_batch \
  --region cn \
  --root runs/minimax-speech-test-unique-id \
  --source-project runs/jieshi-e01-i2v-20260907-attempt10/production-s03-v1/project.yaml \
  --text '什么？没报站啊。'
```

重复 `--text` 可构造有限连续测试；脚本不询问授权或预算。Secret Service lookup 只在已封存调用中执行，不能输出 raw credential。Python 入口为 `run_minimax_speech_batch(root, batch, transport=..., credential=..., toolchain=...)`；真实 transport 与凭证引用在上述脚本中配置。返回 canonical WAV paths；Manifest 和 `state/voice/`、`state/paid-provider/` 下的 exact receipts 保留实际尝试与费用未知证据。

`preview()` 的 supported flags 只验证 adapter 参数。上述授权变化不代表官方免费资格或实际扣费证明。正式接回 S03 仍需处理原 lifecycle、P4 timeline/mixer 与验收；不能 direct mux 或将生成音频伪装成普通导入。环境声单独作为明确的 P4 track，最终音质、口型与自然度仍需验收。

## Verification

国内接入的验证与当前凭证阻断见[国内接入记录](record_for_agent/2026-09-12-minimax-speech-domestic.md)。国内使用独立 Secret Service reference `MINIMAX_SPEECH_CN_API_KEY`（本机配置方式见 playbook），不复用旧引用。CLI 省略 `--region` 等同 `cn`；重开旧国际批次需显式 `--region international`。Python batch 省略 `region` 保留历史国际语义与序列化/hash；`region="cn"` 才是国内。跨 region 复用既有 root 会在 submit 前拒绝；改 region 不能解除旧 unknown，也不授权自动重试。

本轮真实结果见[batch test record](record_for_agent/2026-09-11-minimax-speech-batch-tests.md)：离线实现与复审通过，但唯一 live attempt 为 `OUTCOME_UNKNOWN`，没有 WAV，禁止自动重试。不把下面的测试通过声称为 live 可用。

`python -m pytest -p no:cacheprovider tests/test_production_minimax_speech.py -q`

测试覆盖中文 UTF-8 原文、language/voice/provenance binding、真实 committer permit、旧英文路径和未配置语言拒绝。Fake transport 验证不等于真实声音已生成。
