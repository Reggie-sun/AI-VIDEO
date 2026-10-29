---
record_kind: architecture_implementation
topic_id: elevenlabs-speech-integration
learning_eligibility: ineligible
---

# ElevenLabs Speech Integration

## Scope

用户要求配音链路适配 ElevenLabs。本次补齐现有 adapter 的有界 batch/CLI 与 selected
SEPARATE 路由，沿用 canonical P4、Budget Guard、one-use permit、committer、Registry 与 reader。
没有读取真实 credential、执行付费调用、生成真实语音或改动现有作品。

## Implementation

- `elevenlabs_batch.py` / `scripts/elevenlabs_speech_batch.py`：明确 voice_id、中文/英文、
  multilingual v2、48 kHz mono WAV；复用现有独立 speech project bootstrap，旧 MiniMax 默认保持。
- batch 封存台词、voice settings 与显式 operator monetary ceilings；成功 exact 重开不 POST，
  首次错误/unknown 停止，配置漂移拒绝。
- wire 使用 exact Secret Service reference，query encoding、有界读取、无 redirect/retry。
  lookup 在 permit 消费后发生，因此 lookup 异常保守标 UNKNOWN，不自动恢复。
- `voice_routing.py` 与 P4 handoff 使用 provider-aware 语言投影；ElevenLabs 仅允许 exact
  model/origin/ISO language/48k mono，MiniMax 默认 language 投影保持。
- 官方 API 不支持 multilingual v2 的 language_code；adapter 不再发送该 wire 字段，
  sealed request/provenance 仍保存语言。其余已有 model 的 wire 行为保持。

## Verification

修改前旧 ElevenLabs 62 tests、旧 MiniMax batch 16 tests 通过。
新旧 batch 合计 24 tests 通过，现有 adapter 修改后 62 tests 通过。
路由相关五个 suites 合计 36 tests 通过。原生独立 review 发现 CLI 丢失错误分类，
已修复并增加预算拒绝/UNKNOWN 脱敏输出回归，batch tests 10 passed；复核 APPROVE，
其余七个实现/测试文件 hash 未变，无 unresolved finding。架构检查相对 HEAD 为 PASS。
staged Harness 原始结果保存在 `.agent/harness/runs/elevenlabs-speech-20261029-*/receipt.json`，
以每个 receipt 的真实 status、level、snapshot/freshness 判断，不将本记录当作 PASS receipt。
首次 focused 在 CLI review 修复前启动，最终 snapshot 使用 `-focused-final` / `-related` / `-full`。
测试全部使用 fake transport，
真实 committer/loader 与本地音频 probe 不证明 Provider 或听感通过。

## Boundaries

操作和限制见 [ElevenLabs Speech](../elevenlabs-speech.md)。现有 1 MiB PCM 限制约 10.9 秒，
不自动拆句；费用、账户权限、音色表现、口型、整片和人工验收均为 NOT_EVALUATED。
本次 record 后执行 `distill-ai-video-learning` 评估为 `no_candidate`：只有工程测试，
没有独立真实实验支持通用媒体经验，不创建待采纳规则。
