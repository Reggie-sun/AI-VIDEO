---
record_kind: media_experiment
topic_id: iris-google-audio-listening
learning_eligibility: ineligible
evidence_index_version: "1"
---

# IRIS Google Audio Listening

Date: 2026-10-31 (America/New_York).

## Purpose And Actual Result

用户在询问 R4 歌曲评价后提醒「我记得google有key，.env」。本次使用既有 dotenv-first credential supplier 和 trusted development operator，对已经发到当前飞书的 exact30秒 WAV 做一次真实 Gemini 音频分析，不再用 ASR、分轨 RMS 或原生 host 的音频 omission 代替声音观察。

真实结果为 `SUCCEEDED / OBSERVATION_AVAILABLE`，`consumed=true`，请求／响应模型均为 `gemini-3.8-flash`。不是离线 preview。当前 Codex host 仍未直接听音，下述可听描述归 Gemini，不标作人工接受。

## Exact Source And Observation

源文件为 `outputs/ai-city-takeover/ep01/audio/ace-step-music-repair-20261031-r4/complete-source-preview/IRIS-01-Music-and-Hook-preview.wav`，SHA `9e007d2a8d0b8a5a826c5ce1e77e4e2c3729059eece57edb03ba727be79522d8`，30秒、5,760,044 bytes，分析前后未变。

Gemini 观察到 electronic dance music、synth bass、drum beats、atmospheric synths。两次副歌均识别为 melodic、rhythmic female sung vocals，完整转述原副歌两遍及其他原词。

主歌声线被描述为 smooth／neutral mid-range American female voice，表演 calm、steady、semi-monotone spoken narration；副歌为 airy、digitally tuned、带 reverb 的女性演唱。模型把这两种发声标成 Speaker1/2，只能支持声音描述存在差异，不能证明是不同真人或自动判接缝失败。digitally tuned 也不等于 brief 禁止的 heavy autotune。whisper、声线统一和音乐审美未被此次观察证明。

## Runtime And Credential Boundary

先按 `retrieve-ai-video-memory` 搜索 experience，结果为空；继续用当前源码、委托 owner 和官方音频文档。现有 `/home/reggie/.local/share/video-mcp/venv/bin/python` 的实际 Python3.11.16、MCP1.30.0、httpx0.28.1 和 server/operator import 可用。现有 supplier 成功取得凭据；Agent 未读取或显示 `.env` 内容／key，值未进入 argv、记录、prompt 或 receipt。

当前 `audio_operator._secret_service_credential()` 已先查固定根目录 `.env` 的 exact `GOOGLE_API_KEY`，再查 exact Secret Service。`docs/audio-understanding.md` 的旧 Secret-Service-only 段落与当前代码／AGENTS 不一致，本次不沿旧 bootstrap 另找或转存 key，也未因此修改源代码或放宽凭据规则。

Fresh stdio MCP 通过既有 `ai_video_mcp.audio_operator:build_runtime` 启动，注入单个 non-secret unit/hash、media root 和 model；initialize、tool inventory、offline preview 与封存 request fingerprint 全部核对后，才调用一次 `execute=true`。盲观察 prompt 没有注入预期歌词。egress 沿固定 Google origin，未改 proxy/node、未新增 Provider、未重试。

## Budget And Evidence

只封存并消费1次 audio-analysis，10分钟窗口，内部预留上限USD0.05；该数值不是市场价或实际扣费。实际费用待结算确认。歌曲生成次数仍为10，新增生成0；前轮「本地生成费用0」口径不包含本次远程音频分析。

证据根为 `outputs/ai-city-takeover/ep01/audio/iris-google-listening-20261031/`：`preview.json`、`mcp-handshake.json`、`mcp-preview.json`、`dispatch-intent.json`、`operator-binding.json`、`operator-01/intent.json`／`reservation.json`／`consume.json`／`outcome.json`、`mcp-result.json`、`summary.json` 以及 source/runtime code identities。请求 fingerprint 为 `0769a0cd79f929905f12e58576bfda57b5b686d7583154aa268fd01b7d869b3a`；记录的 response SHA 为 `efdc1d759b30f3d9b27197a36473026d65c04487c206402537516732d4f2d8e3`。

独立 native verifier 只读核对 source bytes、四份 operator artifacts 的 intent hash、count1、时间窗、request/egress/fingerprint、MCP 与 outcome 的 observations／response hash，确认真实 observation 而非 preview。原始 HTTP response 按既有 owner 不保留，不能独立重算其 hash；没有用这个缺口伪装已做额外 Provider 调用。

## Assessment And Remaining Boundary

本次支持「这版实际包含电子伴奏和两遍演唱副歌」，并给出主歌与副歌的声音描述。没有声线／审美／whisper PASS，没有 raw Shot Gate、P6、Production activation 或人类接受。原 MP4／WAV、最终影片时间线和 Product state 均未修改；没有新的媒体生成或歌曲修复提交。

记录判断为 record；自动经验评估 no_candidate。只验证既有路线和一个 exact 源，不产生新的跨作品 Skill／Policy／Gate 规则。未运行项目 tests／Harness／full regression；没有项目 source/tests 改动。新记录与回执保持 local-only，当前歌曲未人工接受，未 commit/push。
