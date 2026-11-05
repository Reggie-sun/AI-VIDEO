---
record_kind: media_experiment
topic_id: iris-local-lyrics-guided-repair
learning_eligibility: ineligible
evidence_index_version: "1"
---

# IRIS Local Lyrics Guided Repair

Date: 2026-10-31 (America/New_York).

## Purpose And Current Result

交付 A/B 后，用户要求「那继续修」。本轮继续修复原歌词在30秒歌曲候选中的可识别完整性，保持原词、词序、音乐方向和输出时长，不以删词或成品加速解决。G 曾发回当前飞书会话，两份不提示原词的 ASR 识别完整；随后用户试听明确指出缺少 BGM，当前歌曲结果为 `REJECTED`／音乐要求 `FAIL`。后续独立伴奏及副歌源修复见 [BGM repair record](2026-10-31-iris-bgm-and-sung-source-repair.md)，不得继续以 G 的 ASR 完整性表示歌曲合格。

当前 G 的 exact WAV SHA 为 `b469c215138b3b517dad78c84de0614fdf97821d853059f7c7106f8e99f4df13`，30.000秒、48kHz、双声道、PCM s16le、1,440,000 frames、5,760,044 bytes。WAV 原片和便于播放的同 bytes 副本保留，MP3／Opus 仅为编码派生。

## Preserved Source And Bounds

原输入仍为 `outputs/ai-city-takeover/ep01/audio/suno-ui-intent.json`，SHA `f5b2cf832a5d27203f2d5f67168937d27b1719537abad2b9c8d952c81005d6d6`；原歌词 SHA `179b2bc93c75f4767837f0e09df6eb47ebaadc94a7f2134706fd835b7dbb57fe`。D 后仅规范 section labels、短句换行，并将原表演描述移入 caption；去除结构标签和规范空白后，正文词序及标点与原始输入一致。

先核对 A/B 两次均为已知成功的本地产物，再封存新增3次的有限单元，上限由2累积至5；C/D/E 未改善后，保留旧计数再封存完整朗读参考与最多2次 cover，上限由5累积至7。实际本轮新增5次 ACE、1次 TTS；累计7次 ACE，TTS 参考仅用了2次上限中的1次。没有 consumed-but-unknown 单元或自动重试。G 准备时的 Path helper／missing intent 错误都发生在 consume 前，保留在 `preflight-recovery.json`，没有因此增加生成次数。

## Execution And Actual Observations

前段证据目录为 `outputs/ai-city-takeover/ep01/audio/ace-step-repair-20261031-r2/`；参考与最终候选位于 `outputs/ai-city-takeover/ep01/audio/ace-step-guided-repair-20261031-r3/`。

| Unit | Bounded change | Unprompted large-v3 observation |
| --- | --- | --- |
| C | 保留 B 输入，仅关 LM，直接 turbo DiT | 12个规范化词，WER86.67%，未改善 |
| D | 规范标签、短句换行，保留全部原词与表演意图 | 15词，WER89.33%，未改善 |
| E | 换2B SFT，50步、CFG7，保持 D 输入 | 16词，WER81.33%，未改善 |
| Reference | Kokoro 正常合成速度1.0，全原词女声朗读 | 75词，WER1.33%；只是节奏参考 |
| F | SFT cover，完整30秒参考，`cover_noise_strength=0.0` | 40词，WER49.33%，仍缺后段 |
| G | 仅把 F 的 `cover_noise_strength` 改为0.6 | 75词，WER1.33%；medium 独立交叉为75词、WER0% |

原规范化 reference 为75词。词数不等于覆盖率；实际保留的完整转写与词序比较才是上述证据。G large-v3 的唯一规范化差异为 `347`／`3.47` 的数字表示。两份 G 转写都没有注入原词或使用 forced alignment，不是由原稿生成字幕制造“唱词完整”。

## Models And Source Reference

ACE 代码继续固定 `ca1e85fe9430179831e6bc6be790c332190a3866`。新增 SFT 固定为 `ACE-Step/acestep-v15-sft@c410d249e71ea9385a7b586865e65b1473e1098d`，约4.79GB、8个文件下载后核验 SHA。官方初始化会把3份 checkpoint Python 文件同步为固定代码目录；权重下载 manifest 与执行代码 identity 分开保存，不覆盖原下载历史。

完整朗读只用作节奏参考：独立环境安装 `hexgrad/kokoro@dfb907a02bba8152ca444717ca5d78747ccb4bec`／0.9.4，权重固定为 `hexgrad/Kokoro-82M@f3ff3571791e39611d31c381e3a41a3af07b4987`，仅下载 config、v1.0 模型、`af_heart` 女声，共约327.7MB。英语 G2P 使用已实际初始化的 bundled EspeakFallback，固定 `en_core_web_sm` 3.8.0，生成期间不下载或跳过未知词。

参考原片为24kHz单声道、25.175秒、speed1.0、一个完整 chunk；返回 graphemes 与原正文一致。后续只做重采样、双声道化和尾部补静音至30秒，无后加速或裁词。独立 verifier 在内存重做该变换，所得 PCM 与 `reference-30s.wav` 完全相同。参考正确不构成歌曲正确或 voice 接受。

F/G 显式使用官方 `TASK_INSTRUCTIONS['cover']`，`src_audio` 绑定30秒完整参考，`audio_codes` 为空，LM 与 CoT 改写关闭，SFT50步／CFG7、batch1。cover 的实际时长由参考决定，不依赖 duration 字段压缩。G 的0.6改变源 latent 初始化与去噪日程，不是“保留60%原人声”的混音或逐词冻结保证。

## Verification And Delivery

本轮 C–G 都通过实际完整解码；G 原片、两个 ASR、输入／consume／result、前序和系列 hashes 已由独立只读 native `verifier` 核对。主会话保存 `summary.json`、`independent-verification.json`、`delivery-assets.json` 和 `mobile-delivery.json`。独立 verifier 未重跑 ASR、未重读全部大型权重，也不以 index hash 推断范围外所有 Manifest 状态。

G MP3 和手机 Opus 均由 exact WAV 编码、完整解码；使用既有可用 ffmpeg 的 libopus，避免 cc-connect Conda ffmpeg 的旧转码问题。当前唯一 AI-VIDEO 飞书 session 与先前 route hash 一致，发送后 CLI exit0、`Message sent successfully`。这证明服务确认发送，手机播放与聆听仍待实际用户反馈。G 后段相对参考静音区存在非零信号，只保留为声学观察，不能据此判配乐质量通过。

本机 Codex 音频输入不受支持，不能把 filesystem 返回 audio block 当作已经听过。MCP audio understanding 仅进行了离线 preview，没有远程执行。声音自然度、sung hook 是否成立、音乐风格及整片声画体验仍需正常速度试听，不能只凭 ASR 判断最终歌曲合格。

所有生成／转写／TTS 均为本机执行，外部付费生成调用0，Provider费用0；公开下载代码和权重不包含向云端发送歌词。没有修改 AI-VIDEO source/tests、Registry、Manifest、canonical captions 或最终时间线，没有新影片 render／激活／Final Acceptance，也没有重新操作 Suno 或清除其旧未知请求。原 index bytes SHA 仍为 `19aac7a1a7e30c07d802baa33d8203e54202362b5e291b233465a164091f30e9`。

只运行实际媒体和文档精准检查，没有跑项目 pytest／Harness／full regression。新产物与记录保持 local-only，未 commit/push，等待实际声音接受后再推进后续镜头与工程发布。

## Learning Assessment

已按 `record-ai-video-session` 记录稳定节点，并自动评估 `distill-ai-video-learning` 为 `no_candidate`。这是一部作品的一组有界试验；F/G 的测量差异不构成跨模型、跨作品质量规则，且尚无真唱或音乐听感证据。没有新增或采用 Skill、Policy、Provider 或 Gate 规则。

## Human Rejection And Repair Continuation

用户试听 G 后明确反馈「这个版本为什么bgm都没有，只有词语」。该反馈绑定上述 exact G WAV，歌曲结果更新为 `REJECTED`／音乐要求 `FAIL`；前文的 NOT_EVALUATED 是交付时状态，不再代表当前结论。ASR 完整性证据保留，不能抵消配乐和 sung hook 未成立的失败。新修复先分开制作器乐及真正演唱的副歌，仍保留原词、词序、30秒及冷峻 electroclash/minimal techno 方向；不再把强保留 TTS 的 cover 当作成歌。旧7次生成与上限均保留，后续有限单元另行封存，不复写历史。
