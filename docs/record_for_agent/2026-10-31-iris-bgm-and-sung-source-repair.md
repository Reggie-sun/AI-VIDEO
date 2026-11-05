---
record_kind: media_experiment
topic_id: iris-bgm-and-sung-source-repair
learning_eligibility: ineligible
evidence_index_version: "1"
---

# IRIS BGM And Sung Source Repair

Date: 2026-10-31 (America/New_York).

## Purpose And Human Failure

用户试听 G 后反馈「这个版本为什么bgm都没有，只有词语」。G exact WAV SHA 为 `b469c215138b3b517dad78c84de0614fdf97821d853059f7c7106f8e99f4df13`，歌曲结果已记为 `REJECTED`／音乐要求 `FAIL`。G 的完整 ASR 只证明被识别的词，不能抵消缺少伴奏或证明演唱成立。

沿 `open-video`／Music Direction 保留原词、词序、30秒和 dark electroclash/minimal techno 方向；改为独立音乐源，不再让强保留朗读的 cover 同时负责恢复伴奏。本轮是上游歌曲源试听制作，没有修改最终影片时间线、Registry、Manifest、激活或 P6；正式影片混音仍由 `ResolvedTimeline` → P4/HyperFrames 拥有。

## Bounded Execution

证据根为 `outputs/ai-city-takeover/ep01/audio/ace-step-music-repair-20261031-r4/`。先确认前7次均有已知输出，再封存最多新增3次，上限历史保留为 `2 → 5 → 7 → 10`。实际新增 H/I/J 3次、累计10次 ACE；原有 TTS 仍是1次，上限2次，没有再次合成。没有自动重试或 consumed-but-unknown。本轮没有新增下载、付费或远程生成，Provider费用0。

继续使用固定 ACE 代码 `ca1e85fe9430179831e6bc6be790c332190a3866` 和已安装 SFT 权重，50步／CFG7、固定 seed、batch1、LM关闭。H/I/J 均在 consume 前核对输入、runner、模型和前序输出身份。

| Unit | Source purpose | Actual observation |
| --- | --- | --- |
| H / ordinal8 | 纯器乐，126 BPM、4/4、E minor、dry kick、hats、sub bass、analog arp | 实际生成30秒源；尾部过早收束，未据此称全程有音乐 |
| I / ordinal9 | 原副歌的 a cappella 演唱候选 | ASR识别到多余 Oh/looked，缺一次重复，WER50%，不整段采用 |
| J / ordinal10 | 仅改 caption 为紧凑、有伴奏的旋律副歌，原词／时长／seed不变 | ASR仍缺一句，WER31.25%，不整段采用 |

E minor 是原稿未固定时由 Agent 选定的音乐调性。126 BPM 是目标；自动 beat observation 的离散 tempo estimate 不是人工节奏验收。固定版本中 `instrumental=True` 不能单独证明生效；H 还显式使用 `[Instrumental]` 与纯器乐 caption。官方支持边界及 API 由只读 native researcher 核对，未新增 Provider 或模型依赖。

## Source Editing And Current Candidate

当前候选位于 `complete-source-preview/IRIS-01-Music-and-Hook-preview.wav`，SHA `9e007d2a8d0b8a5a826c5ce1e77e4e2c3729059eece57edb03ba727be79522d8`，30.000秒、48kHz、双声道、PCM16、1,440,000 frames、5,760,044 bytes。

这是上游 music-source editing，非最终影片第二条 timeline：原完整朗读源保留主歌、pre-chorus 和 outro；移除13.05–13.48的低能量停顿；副歌使用 J 的第一句和 I 的后一句，移除 I 生成的多余 looked，完整短句重复两次，保留原文次序。H 在自动观察的同拍位置复用一段器乐源，保持整个30秒有独立音乐分轨，再作静态 gain、交叉淡化和线性求和。没有成品加速或裁掉原词。完整源操作及输入 hashes 封存在 `complete-source-preview/intent.json`／`runner.py`，没有写入 Product state。

完整人声编辑长29.523秒，副歌 phrase4.314秒×2。该做法仍可能有声线、旋律或切词接缝，实际真唱感和 whisper 均保持 `NOT_EVALUATED`，不因来自演唱提示词就代签听感。

## Verification And Delivery Evidence

主会话实际全解码成功、无削波；不提示原稿的 Whisper large-v3 识别完整75个规范化词，WER1.33%，唯一差异为347／3.47数字表示。这里没有 forced alignment，也没有用原词生成转写。

独立 native verifier 新跑 ffprobe／完整解码，并将封存 source editor 的写入重定向到内存：mix、voice、instrumental 三份 WAV bytes 均与现有文件相同。音乐分轨在30个逐秒窗口的 RMS 为0.04815–0.099504；重建证明其确实加入混音。该证据证明分轨存在和可复现，不证明音乐好听。Verifier 核对现有 ASR／重算 WER，未重跑 ASR，也不能听音。

证据文件：`series-intent.json`、H/I/J 的 intent/consume/result、`complete-source-preview/source-mix-evidence.json`、`audio-validation.json`、`asr.json`、`delivery-assets.json` 和 `mobile-delivery.json`。MP3／Opus 来自同一 exact WAV，仅编码派生并全解码；通过唯一当前 AI-VIDEO 飞书会话发送，不将本地路径当成手机交付。发送是否获服务确认以 `mobile-delivery.json` 为准，客户端播放和人工接受不由发送 exit0 代签。

未跑项目 pytest／Harness／full regression；没有项目 source/tests 修改，也不把媒体校验说成完整工程回归。原 index SHA 保持 `19aac7a1a7e30c07d802baa33d8203e54202362b5e291b233465a164091f30e9`，未 stage 他人改动。Suno旧未知状态保留，未重新提交。新记录和产物 local-only；按成片优先，实际声音接受前未 commit/push。

## Assessment And Remaining Work

`record-ai-video-session`：record。`distill-ai-video-learning`：no_candidate。这是同一作品的实验和音乐缺失修复，当前候选未经人工接受；没有提出或采用跨作品 Skill／Policy／Gate 规则。

结论限于「完整30秒试听候选含独立伴奏，现有ASR支持完整原词」。歌曲音乐质量、唱法、声线接缝、whisper、手机实际播放及最终声画匹配仍待真实试听；不得称完整歌曲、影片或 Product 验收通过。后续正式影片集成仍走 canonical audio admission、Registry/committer、CompositionSpec／ResolvedTimeline／HyperFrames。

## Delivery Readback

当前唯一 AI-VIDEO 飞书 route hash 与前序一致；30秒新版 MP3＋Opus 已发送，服务于 `2026-10-31T09:02:36.388392+00:00` 返回 exit0／`Message sent successfully.`，receipt 为 `complete-source-preview/mobile-delivery.json`。这不证明手机客户端已播放或用户接受。

## Subsequent Actual Audio Observation

用户提醒 Google `.env` key 后，已通过既有 trusted operator 对同一 SHA 完成一次真实 Gemini 音频分析，观察到电子伴奏和两遍女性旋律演唱。详情及费用待结算边界见 [actual audio record](2026-10-31-iris-google-audio-listening.md)；此为新增模型听音证据，主模型直听、人工听感／接缝／whisper 验收仍未完成。
