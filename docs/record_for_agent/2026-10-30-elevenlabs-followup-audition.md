---
record_kind: session_summary
topic_id: elevenlabs-followup-audition
learning_eligibility: ineligible
---

# ElevenLabs Followup Audition

## Result

用户在直连 MCP 安装验证后要求再生成声音试听。单次生成已成功：Stella Gu
(`BqljjWyTnrioXPCNkCd4`)、`eleven_v4`、原台词“记上，第十四起。”。
官方固定 MCP TTS 总是发送 style/speaker_boost，与项目当前 v4 限制冲突；
此次明确使用既有 `scripts.elevenlabs_speech_batch` 和 canonical committer，
不是 MCP text_to_speech 的付费调用验证，也没有修改插件、MCP 或业务代码。

## Evidence And Boundaries

独立 root：`runs/elevenlabs-direct-followup-stella-20261030/`。
Exact WAV：`assets/audio/660301ee4c88ff000c99d0533ce019ead2ed14117c98d2c6e1576f25fb9f2131.wav`。
FFprobe：2.000 秒、48 kHz、mono、PCM s16le；FFmpeg 全量解码 exit 0。
证据位于 `state/voice/attempts/elevenlabs-direct-followup-stella-20261030-1/`，
含 request、preview、authorization、submit-intent、outcome、cost、provenance 与 alignment。
本次 1 次提交，无重试；沿用已封存 operator 单位上限 500 microunits，
每次及本次项目硬上限均 50,000 microunits；实际费用待确认。
凭据来自精确 Secret Service 引用，未读取 `.env`。
原试听和源项目保持只读；未接回原片、未激活生产音轨、未生成 MP4。
已提供原速音频试听；技术探针不证明台词发音、自然语气或人工接受，质量 NOT_EVALUATED。

`record-ai-video-session`：recorded；`distill-ai-video-learning`：no_candidate。
本次单例生成无受控听感对照，不形成通用音质结论。
