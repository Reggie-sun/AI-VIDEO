---
record_kind: session_summary
topic_id: shizhen-opening-elevenlabs-voices
learning_eligibility: ineligible
---

# Shizhen Opening Voice Audition

## Request And Source

用户在多音色试听后要求“当前要生成的宏观开局也生成下,有资料了”，
随后明确选择“开局台词配音（沿用 ElevenLabs）”。本次范围为配音，不提交视频。
来源为 `outputs/shizhen-episode01/opening-dispatch-20261029/plan-v3.json`，
与同目录 `DISPATCH-SHOTBOARD.md` 对照；plan-v3 原文七句保持不变。
以 source-preserving 试听执行，不重新设计镜头或台词。

## Generation And Evidence

暂定 Evan Zhao (`MI36FIkp9wRP7cpWKPTl`) 读五句值班转报，
Stella Gu (`BqljjWyTnrioXPCNkCd4`) 读董文慧两句；未声称正式声线已定。
统一 eleven_v4、既有兼容默认参数；仍使用 canonical committer、预算、egress、
逐句 preview、durable intent 和 one-use permit，不用直连 MCP 绕过。
独立 root：`runs/shizhen-opening-voice-relay-20261030/` 与
`runs/shizhen-opening-voice-dong-20261030/`。七次 submit 全部 succeeded，无重试。
每字符 operator 上限 500 microunits；预计预留总上限 USD 0.041；每次硬上限
USD 0.05、每角色批次硬上限 USD 0.20，合计 USD 0.40。实际费用待确认。
凭据仅来自精确 Secret Service 引用；未读取 `.env`。

本地交付目录：`outputs/shizhen-episode01/opening-voices-elevenlabs-20261030/`。
`intent.json` 封存 source plan SHA、原文、角色/voice、预算和次数；
`index.json` 含 exact 原 WAV SHA、radio 派生 SHA、时长和源路径。
七个干声 WAV 与五个转报对讲滤波试听 WAV 本地保存，未接入来源项目或激活音轨。
滤波仅 highpass/lowpass/compressor，不增环境音、不改台词或语速。

| Line | Duration |
| --- | --- |
| L1 | 3.44 s |
| L2 | 3.76 s |
| L3 | 4.24 s |
| L4 | 4.32 s |
| L5 | 2.08 s |
| L6a | 1.28 s |
| L6b | 1.04 s |

七段合计语音时长 20.16 秒，不含问答间停顿，非 assembled timeline。
原音频逐一 SHA 核验、FFprobe 与完整 FFmpeg 解码通过；五个滤波版解码通过。
D3 台词加一秒留画面至少需 5.24 秒，旧窗口 5 秒不足，未压缩语速或擅改镜头。
D6 两句共享窗口，语音合计 2.32 秒；加一秒为 3.32 秒，尚未计问答间停顿。
L1 可在后续 D1 接报反应保留余量，不以此要求修改已接受的市政原片。
以上是装配前时长建议，不替代唯一 ResolvedTimeline 或声画验收。

## Frontend And Acceptance Boundary

前端 `http://127.0.0.1:18769/index.html` 只监听 loopback，已在桌面 Chrome 新窗口打开，
窗口标题“失帧 · 宏观开局配音 - Google Chrome”已读回。
页面含七个主播放器和五个展开的干声对照，支持按剧情顺序播放与停止。
独立 Playwright 浏览器验证 metadata 正常，原速播放推进到第二句，停止暂停所有音频，
无 pageerror；证据 `browser-verification.json`。这些不证明已听审或发音正确。

“绞盘还在收”“还在原来那层”的还=hái、调度平淡语气、人物匹配与声画最终时长待试听。
本次没有生成视频、拼接成片、替换旧试听、激活生产音轨或给 Final Acceptance。
媒体和试听页本地保留，仅本记录提交；其他窗口 dirty/staged 工作不变。
`record-ai-video-session`：recorded；`distill-ai-video-learning`：no_candidate。
这是已知成功生成与技术播放证据，没有本版人工听感结论。
