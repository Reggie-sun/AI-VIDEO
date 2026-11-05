---
record_kind: media_experiment
topic_id: ace-step-local-iris-song-audition
learning_eligibility: ineligible
evidence_index_version: "1"
---

# ACE-Step Local IRIS Audition

Date: 2026-10-30 (America/New_York); execution completed 2026-10-31 UTC.

## Supersession Notice — 2026-10-31 Lyric Repair

后续修复已得到新 G：两个无原词提示的 ASR 均转写出完整原词序列，large-v3／medium 的 WER 分别约1.33%／0%，G 已通过当前 cc-connect 飞书会话交付。具体来源、计数2→5→7、参考与输出身份见 [guided repair record](2026-10-31-iris-local-lyrics-guided-repair.md)。下述 A/B 的漏词观察仍为其真实历史；新 G 的听感、真唱、配乐与完整歌曲验收尚未完成，不代表旧 Suno 已恢复或 Production 已激活。

## Purpose And Scope

用户在获知 ACE-Step 本地方案后明确要求「那你运行啊」。本轮实际安装并运行该工具，沿用 IRIS EP01 原76词、英文女声、126 BPM、30秒与原音乐方向，生成两份独立的本地试听音频。没有操作 Suno、代做真人验证或结算旧未知请求。

原输入为 `outputs/ai-city-takeover/ep01/audio/suno-ui-intent.json`，bytes SHA `f5b2cf832a5d27203f2d5f67168937d27b1719537abad2b9c8d952c81005d6d6`；歌词 SHA `179b2bc93c75f4767837f0e09df6eb47ebaadc94a7f2134706fd835b7dbb57fe`。生成前与完成后均重新核验，未改原歌词。

## Installed Runtime And Actual Execution

工具安装在仓库外 `/home/reggie/.local/share/ai-video/ace-step/`，使用独立 Python 3.11.16 环境及官方 locked dependencies：PyTorch `2.10.0+cu128`、Transformers `4.57.6`、Diffusers `0.37.1`。RTX 5090 的实际 CUDA 张量计算通过，未修改 AI-VIDEO 项目依赖。

代码固定为 `ace-step/ACE-Step-1.5@ca1e85fe9430179831e6bc6be790c332190a3866`；官方公开权重固定为 `ACE-Step/Ace-Step1.5@19671f406d603126926c1b7e2adc169acbcade22`。约10.09GB、28个文件下载后核验 bytes 与 SHA，未使用凭据。官方初始化随后把两份模型 Python 文件同步到固定代码版本；下载 manifest 与同步后的 code hashes 分开保留。

实际调用官方 `AceStepHandler`、PyTorch `LLMHandler` 和 `generate_music`，使用 turbo DiT、1.7B LM、8 steps、每次 batch=1。生成过程启用离线模式，关闭 caption、lyrics、language 和 metadata 的 CoT 改写，未调用远程生成 API。第一版 caption 133 tokens、lyrics 166 tokens，均在实际 tokenizer 上限内，没有截断。

第一版已取得确切 WAV 后，两个无原词提示的本地 Whisper 模型都只识别出 intro／部分 verse，未识别 chorus／outro。第二版保留原歌词、30秒、126 BPM、显式 DiT seed，给 caption 追加紧凑连续人声和完整唱词的表演约束；原 intent、消费与结果 bytes 保留，另建 `repair-intent.json` 绑定 predecessor。LM sampling 不因此成为完全确定的受控比较，不能把差异归因为一项通用模型规则。

## Media And Verification

证据目录：`outputs/ai-city-takeover/ep01/audio/ace-step-local-20261031/`。

| Output | Exact WAV SHA-256 | Measured result |
| --- | --- | --- |
| A | `1f7f567a439384a25a7491ce42cf281027326b3501f4852018deb3dad3c86e19` | 30.000秒，48kHz，stereo，1,440,000 frames，完整解码通过 |
| B | `ab0000749101d9cc9d85526683b760ae1d2e20b5dad455ac2eb67c8c0d509b06` | 30.000秒，48kHz，stereo，1,440,000 frames，完整解码通过 |

两份 WAV 均为5,760,044 bytes，样本有限且非静音，没有达到整数满幅的样本。原 WAV、便于试听的同 bytes WAV 副本及 MP3 派生均保留。页面与两份 MP3 的实际 HTTP HEAD 为200：`http://127.0.0.1:8767/ep01/audio/ace-step-local-20261031/`。这只证明资源可访问，不代替聆听。

`attempt-01/asr.json` 与 `attempt-02/asr.json` 是不注入原歌词的 Whisper large-v3 实际转写。规范化 reference 为75词，两次 hypothesis 均为20词，词错误率分别约0.787和0.800。第二版识别到部分 hook，却仍未覆盖完整原词。第一版另有 `asr-crosscheck.json` 的 Whisper medium 交叉观察。ASR 只提供估计证据，不是人工听感、歌词一定不存在的证明或 canonical 字幕时序。

`intent.json`、`repair-intent.json`、两份 `consume.json` 和 `result.json` 保留参数、次数、精确输入及输出身份；`environment.json`、`weights-manifest.json`、`runtime-model-code.json` 保留运行与模型来源。`summary.json` 汇总实际结果；两个 runner 副本可供复核。总计2次、每次1份音频，原上限2次已使用完，没有自动重试。

独立只读 native `verifier` 重新执行两份 WAV 的 ffprobe、完整解码和 PCM 检查，并核对 intent／consume／result、runner、predecessor、原 brief、试听副本与 index hashes，支持本次两条真实产物的技术执行结论；仍将 human hearing 与完整唱词验收保留 `NOT_EVALUATED`。复核仅覆盖现有文件及本次实测，不是历史网络审计。runner 是本次实验的封存快照，不作为通用 unknown-recovery 实现：其后续分支仅检查前次 result 文件存在，本次已另行核对前次确为完整 success，不能推为所有未知状态都安全。

## Outcome And Publishing

本地工具执行成功、两份真实音频已落盘；完整歌词、女声表现、正常速度实际聆听与全片验收尚未通过，`human_listening=NOT_EVALUATED`。这两份音频没有导入 Registry、创建 canonical captions、修改 Production state、渲染全片或作为成片音轨采用。下一步仍需在原30秒和原歌词约束下解决可听的完整词句与表演适配，不能以技术解码成功代签。

外部付费生成调用0次，付费 Provider 费用0；本机计算未作电费估算。旧 Suno 结果与预算历史保留未决。原仓库 index 前后 bytes SHA 一致，没有 stage、commit 或 push；遵循成片优先，等待实际声音验收。此次只新增本任务试听素材、运行证据和记录，未认领并行 source/test 改动，未跑项目 pytest／Harness。

## Learning Assessment

已自动按 `distill-ai-video-learning` 评估为 `no_candidate`：这是单个作品内的一组有界本地试听，没有人工听感，也没有足以排除 LM 随机性的独立因果证据。不新增或采用 Skill、Policy、Provider 或 Gate 规则。

## Mobile Delivery Follow-up

用户随后说明手机正在通过 cc-connect 使用当前会话，无法打开本机文件链接。本轮只读确认运行中的唯一 `AI-VIDEO` 飞书 session，使用 `cc-connect send` 将媒体发送回该会话，没有公开分享或向其他接收者发送。

首个 A 版“原 MP3 文件＋语音”组合请求未获完整成功确认，其原文件送达状态保留未决，没有重放该组合请求。独立的 B 版 MP3 语音请求明确在本地转码阶段失败：服务所用 Conda ffmpeg 缺 `libopus` encoder，尚未进入音频上传。之后使用本机已有 `imageio_ffmpeg` 所带 ffmpeg 7.0.2，把两份 exact 原 WAV 转成48kHz双声道 Opus，仅转换编码，不裁切、不改变速度或音高；两份派生完整解码通过，原音频 bytes 保持不变。

将已验证 Opus 通过 native `--audio` 各发送一次后，A/B 均取得 CLI `Message sent successfully`、exit 0；B 版原 MP3 的独立 `--file` 请求也取得成功确认。证据为同目录 `mobile-opus-validation.json`、`mobile-delivery-20261031.json`。这些确认只证明服务完成发送，不代替手机界面实读、用户播放或听感验收。未重启服务或修改 cc-connect 配置；原完整唱词缺口和未 commit/push 状态保留，学习评估仍为 `no_candidate`。
