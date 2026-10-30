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

## Context Auditions

用户随后要求“多生成几个”“不同语境环境下的”，并要求在前端打开。
本次新增独立 batch `runs/elevenlabs-contexts-stella-20261030/`，固定同一
Stella Gu/eleven_v4，以四段不同台词比较语境，场景标签不进入朗读文本：

| Context | Text | Duration |
| --- | --- | --- |
| 日常闲聊 | 行，那就这么定了，明天见。 | 2.56 s |
| 安慰朋友 | 没事，你慢慢说，我听着呢。 | 2.72 s |
| 紧急提醒 | 小心！你脚下有东西，先退回来！ | 2.96 s |
| 失望质问 | 你昨天不是答应过我吗？怎么又变了？ | 3.36 s |

独立只读概念检查修正“别动/退回来”的指令矛盾，仅证明文本合理，非音频验收。
四次 submit 均 succeeded，无重试；预留估计总上限 USD 0.029，单次硬上限
50,000 microunits、batch 硬上限 200,000 microunits；实际费用待确认。
所有输出经 SHA-256 对照 exact outcome、FFprobe 与 FFmpeg 完整解码。
听感未人工验收，不宣称轻声/紧迫/克制表演已经实现，没有添加环境声。

本地交付目录 `outputs/elevenlabs-contexts-stella-20261030/`：
`01.wav` 至 `04.wav` 为原 WAV 的字节一致副本，`index.json` 保留原路径和 SHA，
`index.html` 提供四个独立播放器；媒体与本机预览页本地保存，不随本记录推送。
仅监听 loopback 的预览服务为 `http://127.0.0.1:18767/index.html`。
已在桌面 Chrome 新窗口打开，窗口标题“不同语境试听 - Google Chrome”，
页面和四个 WAV 均有 HTTP 200 请求读回。共享 DevTools profile 被占用，
采用现有桌面 Chrome profile 新窗口；没有停止或重启共享浏览器/daemon。

本次 `record-ai-video-session`：recorded；`distill-ai-video-learning`：no_candidate。
没有受控听感结论或用户反馈，不从四段内容不同的单批次推广模型表现规则。
