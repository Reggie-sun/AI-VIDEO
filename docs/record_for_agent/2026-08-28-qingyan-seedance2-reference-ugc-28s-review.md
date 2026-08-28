# Qingyan Seedance 2.0 Reference UGC 28s Review Record

Date: 2026-08-28

## Purpose

本文记录青颜喷雾一次真实 `doubao-seedance-2-0-260128` 双 Shot、原生音频、逐 Shot Gate 与确定性修复实验。目标是复用用户提供的 28.863 秒真人电商视频的抽象广告节奏，重新建立以下因果：

`问题可见且有声音 -> 老人先推荐 -> 完整递交 -> 苗家女性直接喷腋下 -> 使用后放松 -> 生活化效果 -> 动态产品收束`

本记录绑定本地 run `runs/qingyan-seedance2-reference-ugc-30s-20260828-001/`。它是 paid cloud development proof 与 local review composition 记录，不是 Production ingestion、candidate activation、P6、Final Acceptance、publication、commercial claim approval 或 human subjective acceptance。

## Source And Egress Boundary

用户提供的参考视频只用于本地导演结构分析：

- path: `/home/reggie/文档/xwechat_files/wxid_ut5o9e1igztd22_f3a1/msg/video/2026-08/b88a613c5a8305c86d04b6bd195cc12f.mp4`
- SHA-256: `24dcb6371dafae573d74fecbfee35e72e8b876c3ca1e5b2b31366e89d7262a28`
- measured media: `28.863s`, `720x1280`, `29fps`, H.264 Main + 44.1kHz stereo AAC
- content boundary: 含清晰真人面孔，因此 `provider_egress=DENIED_AND_EXCLUDED`
- 只迁移 hook 节奏、产品特写节奏、生活 montage 密度与 application-to-payoff 结构；未迁移真人 identity、faces、wardrobe、location、audio、dialogue、captions、testimonials 或不安全功效 claims

Provider 只收到两张用户提供的普通非人物产品图及 exact Shot prompt：

1. `references/01-qingyan-packshot.png`
   - SHA-256: `8b9efd8236c5d705b291faf8517fb49c07af494585c59c29f53a77b80aeea68d`
   - source SHA-256: `9f6c5e4ac802cdcedd5c5bb2370aa318a9366420ef2290ccdddf37a63b372f7f`
2. `references/02-qingyan-ingredient-graphic-rgb24.png`
   - SHA-256: `b749abc0efe5fcba78cb08e4dbe97aeafc20360a5ffcf75b55e9418f390309e8`
   - source SHA-256: `833df162499c8a288c752355f872e4696709f7b65be2d90a01b8f049ed3ce0bb`

第二张 source 虽以 `.png` 命名，实际 magic bytes 为 RIFF WebP。首次 local pre-submit 因严格 PNG measurement fail closed，`submit_posts=0`、`paid_provider_outcome=not_submitted`；随后用 `ffmpeg` 转成严格 RGB24 PNG，未搜索其他 credential 或降低 input gate。

该 ingredient graphic 含 `15%`、sweat-gland mechanism 与 duration-style visual claims，只允许迁移金色液体/高光质感。两个 Shot 的 frozen requirement 都明确禁止输出 `15%`、`全天`、sweat-gland mechanism、arrows、diagrams、testimonials、`官方正品/用户推荐/热销` 与 medical、quantified、duration、absolute claims。

## Paid Provider Execution

两个 Shot 均使用：

- model: `doubao-seedance-2-0-260128`
- mode: `REFERENCE_TO_VIDEO`
- output request: `15s`, `720p`, `9:16`, `24fps`, `generate_audio=true`
- references: 上述两张普通非人物 PNG
- exact submit ceiling: 每 Shot 1 POST
- activation、fallback、blind retry、permit remint: 全部为 0

2026-08-28 从火山引擎公开定价页核对的 no-video-input rate 为 `46 CNY / million tokens`。每个 15 秒请求按 `324000` tokens 估算上限 `14.904 CNY`，有限 ceiling 为 `16 CNY`；两次请求的估算上限合计 `29.808 CNY`，aggregate ceiling `32 CNY`。实际账单金额未读取，因此不得把估算值陈述成实扣费用。

Provider effect summary：

| Shot | Attempt | Submit POSTs | Result | Raw SHA-256 |
| --- | --- | ---: | --- | --- |
| 1 | `qingyan-seedance2-reference-ugc-shot-01-attempt-2` | 1 | fetched, raw Gate PASS | `d938fb29a0b0af897b2093504877bf75a730445ac6abd1a47af7d5a11c1a97c6` |
| 2 | `qingyan-seedance2-reference-ugc-shot-02-attempt-1` | 1 | fetched, raw Gate FAIL | `6064d07a875085cd303ae1421d8f9b86ff715ac4848679527475ae7879a26204` |

Shot 2 只在 Shot 1 的 13 个 required findings 全部 `PASS` 后提交。全 run 合计 exact Provider POSTs 为 2；没有额外 variant、retry 或其他 Provider/model call。

## Per-Shot Gate Results

### Shot 1

Raw artifact：

`runs/qingyan-seedance2-reference-ugc-30s-20260828-001/shot-01/output/seedance2-base-shot-01-native-audio-15s.mp4`

Measured facts：

- SHA-256: `d938fb29a0b0af897b2093504877bf75a730445ac6abd1a47af7d5a11c1a97c6`
- size: `8,224,049` bytes
- duration: `15.070s`
- video: H.264 High, `720x1280`, `24fps`
- audio: AAC stereo, `44.1kHz`, `15.069002s`, mean `-14.6 dB`, max `-1.3 dB`

Project-local `video-analysis` MCP 以 `0.5s` interval 检查 30 frames，并用 Whisper `small` 与 `medium` 复核音频。13 个 frozen requirements 全部 `PASS`：第一秒有湿黏腋下、拉衣与不适；开场 narration 同步解释问题；老人先展示产品；完成 sole holder -> offer -> younger secures -> elder releases；之后才开盖并对准暴露腋下喷一次透明细雾；放松与微笑只在喷后出现。无重复瓶、anime、identity morph、奇怪运镜、静态尾卡、unsafe claims 或重复 slogan。

Evidence：

- `shot-01/evidence/post-media-gate.json`
- `shot-01/evidence/live-report.json`

### Shot 2 Raw Failure And Local Repair

Raw artifact 前 2 秒在桌面/手中同时生成多瓶产品，违反 frozen `PRODUCT_IDENTITY` 的“一瓶一盒、不得 duplicate”要求，因此 raw Gate 为 `FAIL`，raw output 未进入最终拼接。

Evidence：

- `shot-02/evidence/post-media-gate.json`
- `shot-02/output/seedance2-base-shot-02-native-audio-15s.mp4`
- raw SHA-256: `6064d07a875085cd303ae1421d8f9b86ff715ac4848679527475ae7879a26204`

未调用 Provider 重试，而是做一次确定性 local trim：删除 source `0.000-2.000s`，不添加生成帧、copy、audio 或 Provider effect。Exact repaired derivative：

`shot-02/output/seedance2-base-shot-02-trimmed-gate-candidate-13s.mp4`

Measured facts：

- SHA-256: `25a24ba959a4c6a81fc1246c812048e299869429158c15961400dd9e11f74045`
- size: `5,695,871` bytes
- duration: `13.093s`
- video: H.264, `720x1280`, `24fps`
- audio: AAC stereo, `44.1kHz`, `13.069002s`, mean `-14.6 dB`, max `-1.5 dB`

`video-analysis` MCP 对 27 个 `0.5s` frames、Whisper `medium` transcript 与 576 个 decoded review samples 重新 Gate；10 个 frozen requirements 全部 `PASS`。生活人物不做 testimonial；透明灰白 mist 无黄色/生物动画；近距离效果只由自然同行表达；产品保持一瓶一盒；尾镜是有 hand/camera micro-motion 的单个 live hero，不是重复静图；final advertising line 只说一次。

Evidence：`shot-02/evidence/post-media-repair-gate.json`。

## Local Review Composition

最终 local review artifact：

`runs/qingyan-seedance2-reference-ugc-30s-20260828-001/final/qingyan-seedance2-reference-ugc-28s-review.mp4`

Measured facts：

- SHA-256: `7818b1b0d94919d81dc411e0610dfa6f864b639caba99705fd35b48e3d1ffea3`
- size: `14,594,886` bytes
- duration: `28.166s`
- video: H.264, `720x1280`, `24fps`
- audio: AAC stereo, `44.1kHz`, `28.141995s`, mean `-14.6 dB`, max `-1.3 dB`
- composition: Shot 1 PASS raw + Shot 2 PASS trimmed derivative，15 秒处 clean hard cut

整片通过 8 个 local-review requirements。`video-analysis` MCP 检查 29 个 `1.0s` frames，并对 `14.0-17.0s` join 用 `0.25s` dense review；join 是使用后微笑到 product/mist proof 的 clean direct cut，没有 whip、flash、dissolve、morph 或 freeze。1240 个 decoded review samples 全部 unique，结尾为持续微动的手持产品镜头，不是两张 static cards；完整 final brand line 只出现一次。

Evidence：`final/evidence/local-review-gate.json`。

## Assessment

这次 development experiment 已证明当前 Seedance 2.0 base 路径能在两张普通产品图片 conditioning 下生成 photorealistic fictional Miao-themed ad、原生中文 audio、可读 problem hook、老人推荐与 handoff、直接腋下应用、post-use payoff、生活 montage 与动态 product closure。

同时保留三层不同 truth：

1. raw Shot 1 Provider artifact：exact per-Shot Gate PASS。
2. raw Shot 2 Provider artifact：exact per-Shot Gate FAIL，不得偷换成通过。
3. Shot 2 deterministic derivative 与 28.166 秒 composition：只通过 local development review Gate。

最终 MP4 是 `ffmpeg` local composition，直接保留两段 generated native audio。它没有进入 `CompositionSpec -> ResolvedTimeline -> HyperFrames` 的 Production P4 path；不得据此声称 Seedance embedded audio 已被 canonical P4 ingest/mix，也不得将 local output 当作 active candidate 或 published ad。

## Remaining Risks

- 用户尚未给出 exact 28.166 秒成片的 human visual/audio verdict；文化呈现、人物年龄观感、产品 label fidelity、中文发音、节奏与转化质量仍是 human acceptance boundary。
- `video-analysis` Whisper 对 `黏衣`、`青颜`、`抑汗净味` 存在 near-homophone substitutions；它支持 timing/content sequence，但不能替代用户对真实发音自然度的听审。
- 720p 是本次 accepted model/request boundary；tool review 的 generic resolution heuristic 报告 `low_resolution`，未据此升级为 1080p 或扩大付费 scope。
- 实际 Provider billing 未验证；只有 request count、finite ceiling 与 token-based estimate。
- Run artifacts 在本地 `runs/`，未 stage、commit、push、activate 或 publish。
- Project RAG search 本轮使用 last-good advisory snapshot；refresh 由 detached task 排队，未轮询、未重建，也不影响本次 exact runtime evidence。

## Agent Guardrails

- 真人参考视频继续保持 local-only；不得因本次 fictional output 成功就恢复 person-reference egress path。
- 任何新 Shot、variant、retry、benchmark、1080p upgrade、不同 model/provider 或 publication 都需要新的 current-task authorization 与完整 paid Provider Gate。
- Raw Provider FAIL 不得通过重命名、只看最终拼接或总分掩盖；任何 deterministic repair 必须绑定 parent SHA、exact operation 与独立 requirement-level Gate。
- `MP4 contains AAC`、local ffmpeg composition 与 good Whisper transcript 都不等于 P4 audio ingestion、P6、Final Acceptance 或 commercial claim approval。
- 后续若进入 Production，必须走 canonical project/asset/timeline/state/review owners；本记录与 run artifacts不拥有 activation 或 publication truth。
