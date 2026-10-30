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

## More Voices And New Contexts

用户试听上一轮后反馈“现在好多了”，要求“多用几个音色”并补充“语境也换”。
这更新上一节当时尚无反馈的状态：用户给出了有界正面听感反馈，不能扩大为模型普遍自然、
所有声音已接受或正式成片验收。

新增 Coco Li (`Ca5bKgudqKJzq8YRFoAz`)、Julia (`tOuLUAIdXShmWH7PEUrU`)、
Evan Zhao (`MI36FIkp9wRP7cpWKPTl`)、Martin Li (`WuLq5z7nEcrhppO0ZQJw`)。
提交前经 elevenlabs-direct MCP get_voice 逐一只读查询，均 HTTP 200。
四个音色各读相同三段新台词，统一 eleven_v4 与默认兼容参数：

- 惊喜报喜：中了！真的中了！你快看，是我们俩的名字！
- 尴尬道歉：那个……杯子是我碰倒的。对不起，我赔你一个。
- 紧张提醒：别回头……有人跟着我们。装作没发现，继续走。

独立只读文本复核后，12 次受控生成全部 succeeded，无失败、重试或追加生成。
四个独立 canonical root 为 `runs/elevenlabs-newctx-{coco,julia,evan,martin}-20261030/`。
每 root 三个 attempt 均有 request/preview/authorization/submit-intent/outcome/cost 等证据。
每字符 operator 上限 500 microunits，预计总预留上限 USD 0.128；每次硬上限
USD 0.05、每 root 硬上限 USD 0.20，四 root 合计硬上限 USD 0.80。实际费用待确认。
不从本次 MCP 音色查询成功推导 MCP TTS 生成资格；生成仍走项目 canonical 入口。

本地交付目录 `outputs/elevenlabs-voices-newcontexts-20261030/`，`intent.json` 封存范围，
`index.json` 含全部 exact SHA-256、台词、音色、源路径和时长。12 个 WAV 是原音频的
字节一致副本，逐条 SHA 对照、FFprobe、完整 FFmpeg 解码通过；时长 3.68–4.88 秒。
页面按语境分组，每组四个音色并列。前端 URL `http://127.0.0.1:18768/index.html`，
仅监听 loopback；页面和全部 12 个 WAV HTTP 200。桌面 Chrome 新窗口标题
“四音色 · 新语境试听 - Google Chrome”已读回，旧试听页与音频保留。

媒体和本机预览页仅本地保存，记录提交；未修改业务代码或其他窗口的 dirty/staged 工作。
新 12 段尚无用户听感反馈，scene 标签只表示预期语境，没有环境音，不预宣称情绪实现。
`record-ai-video-session`：recorded；`distill-ai-video-learning`：no_candidate。
用户对上一轮的相对改善反馈与新生成样本不构成已完成的受控听感归因结论。
