# Qingyan Seedance Fast Supported Hero And Captioned Card Tail Record

Date: 2026-08-28

## Purpose

本文记录用户拒绝旧手持 Hero 中“盒子突然悬浮”后的一次受限修复：保留已接受的因果叙事与原生中文音轨，使用一次 `doubao-seedance-2-0-fast-260128` 生成从首帧到末帧都有物理支撑的桌面产品 Hero，并把用户指定的三张广告图片按顺序作为结尾播放。同时建立字幕 Gate，纠正旧 Shot 1 已烧入的错字字幕，避免双层字幕和重复 slogan。

Primary run：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/`

这是 paid cloud development proof 与 local review-only composition，不是 Production ingestion、candidate activation、P6、Final Acceptance、publication、commercial claim approval 或用户的最终主观验收。

## Superseded Human-Quality Evidence

直接受影响的旧成片：

`runs/qingyan-seedance2-reference-ugc-30s-20260828-001/final/qingyan-seedance2-reference-ugc-28s-review.mp4`

- SHA-256: `7818b1b0d94919d81dc411e0610dfa6f864b639caba99705fd35b48e3d1ffea3`
- 用户 verdict: 结尾盒子没有可见支撑面，读成突然浮空，拒绝该视觉收束
- 保留的历史事实: 旧文件的 codec、audio、frame uniqueness、Provider call count 与当时技术 Gate 测量
- 被取代的结论: `DYNAMIC_HERO_CLOSURE` / `NO_STATIC_OR_REPEATED_ENDING` 的技术 PASS 不再是当前 human-quality evidence

对应旧记录已增加 supersession notice：

`docs/record_for_agent/2026-08-28-qingyan-seedance2-reference-ugc-28s-review.md`

## Source, Claim And Egress Boundary

Fast 只收到一张不含人物的 exact product-layout reference：

`references/01-supported-product-layout.png`

- SHA-256: `24e4914b90961b9069843bd166529c926eb75ddc7b76d87dcfeb292ac20b2e5e`
- size: `375,537` bytes
- measured format: RGB24 PNG, `720x1280`
- source: 旧 Shot 2 repaired derivative 的 `0.000s` frame；布局中一瓶一盒已接触同一平面
- egress classification: `ordinary_non_character_image`

三张用户指定的结尾图片只在本地确定性拼接，未上传 Seedance：

| Order | Source SHA-256 | Converted SHA-256 | Claim boundary |
| ---: | --- | --- | --- |
| 1 | `32debed269633742801d21fcc949f7455cd9747ef47d2a0a1547e79df30bc058` | `e334203f684d53a8d8e42894e0245440166b40796b638f17ff1232f4f5e31c3d` | pain-point card，用户提供、未核验 |
| 2 | `833df162499c8a288c752355f872e4696709f7b65be2d90a01b8f049ed3ce0bb` | `b749abc0efe5fcba78cb08e4dbe97aeafc20360a5ffcf75b55e9418f390309e8` | 含 `15%`、`全天`、sweat-gland/mechanism claims，未核验 |
| 3 | `52079b00fb541fca36240f01ae1ba4826e31085585e43833b530efdb20e01e44` | `82f20c9c5f6295148de7b68b35f4e0435bb8b686822219f00bcc7bc05702787d` | 含 `14天`、`96.67%`、`93.33%`、`真人实测`，未核验 |

三个 source 虽以 `.png` 命名，magic bytes 实际为 RIFF WebP；本地用 `ffmpeg` 转成 exact RGB24 PNG。最终三张卡全程显示 `用户提供素材｜功效与数据未核验`，因此本次只允许 review-only，不得把 source copy 解释成已经 substantiated 或可发布。

## Paid Seedance Fast Execution

Exact request：

- model: `doubao-seedance-2-0-fast-260128`
- mode: `REFERENCE_TO_VIDEO`
- output: 4 seconds, `720p`, `9:16`, `24fps`, `generate_audio=true`
- references: 上述 1 张 ordinary non-character PNG
- exact submit ceiling: 1 POST
- blind retry、permit remint、fallback、activation: 全部为 0

公开 no-video-input rate 在本次 preflight 为 `37 CNY / million tokens`。`4 * 720 * 1280 * 24 / 1024 = 86,400` estimated tokens，对应估算上限 `3.1968 CNY`；finite ceiling 为 `4 CNY`。实际账单金额未读取，不能把估算值陈述为实扣费用。

第一次本地启动因 `production_project_factory` 未进入 `PYTHONPATH` 在 import 阶段停止：未读取 credential、未建立 Provider request、POST=0。修正本地启动环境后执行唯一一次远程 POST，未扩大预算或重新签发 permit。

Live report：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/live-report.json`

Fast raw artifact：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/output/seedance2-fast-supported-hero-native-audio-4s.mp4`

- SHA-256: `a2c17d29974cd55ef77c39833be1dc7f9a09e857823c49311d307c42b0e551de`
- size: `1,558,080` bytes
- duration: `4.096s`
- video: H.264 High, `720x1280`, `24fps`, 97 frames
- audio: AAC stereo, `32kHz`, mean `-44.7 dB`, max `-16.7 dB`
- state: fetched, unactivated

## Fast Per-Shot Gate

Exact Fast MP4 落盘后、开始拼接前，project-local `video-analysis` MCP 以 `0.5s` interval 检查 9 frames、audio transcription 与 scene continuity。全部 8 个 required findings 为 `PASS`：

- 一瓶一盒从首帧已在木桌上，完整底边与 contact shadows 全程可见；无 gap、entry、appearance、disappearance、levitation 或 morph
- exactly one bottle + one box，颜色与几何稳定
- 只有一个慢速直推镜头；无 orbit、whip、cut 或 effect transition
- background/light 有 live micro-motion，不是 frozen still
- 无人物、无 generated overlay、percentage、mechanism、medical、testimonial 或 CTA claim
- raw AAC 可解码、有非静音 signal；Whisper 检出 `0.0s` speech

Evidence：

- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/post-media-gate.json`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/fast-gate-contact-sheet.png`

该 PASS 只授权本地确定性拼接；不激活 candidate，也不批准三张 card claims。

## Caption Contract And Repair

旧 Shot 1 的 Provider MP4 已经烧入一层模型字幕，包含错字、分段不统一和 display tail。直接增加新字幕会形成双层字幕，因此本次建立并执行以下 Gate：

1. authored Mandarin copy 是字幕文本 owner；Whisper near-homophones 只用于测量 timing，不能成为最终文案。
2. clean-source caption 严格跟随 measured speech；final brand line 拆成 `青颜`、`抑汗净味`、`清爽舒适`、`近距离`、`更从容` 五个事件。
3. 两条 corrupt-source caption 使用 opaque backplate 完全遮住旧字。为防旧字在语音结束后短暂重新出现，只允许 `0.60s` 与 `0.31s` cleanup tail，不增加新文案。
4. `Noto Sans CJK SC`、最多两行、单行不超过 14 个中文字符；clean-source captions 使用 bottom safe area。
5. 三张 card 的对白字幕保持在 disclosure 上方，不覆盖 card main copy；不得再次口播或新增未核验数据。

Twenty-four start/inside/end boundary samples 与 8 representative samples 已人工复核；没有双层字幕、旧错字露出、clipping、card body-copy overlap 或 slogan repetition。

Evidence：

- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/shot-contract.md`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/captions.ass`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/final-caption-boundaries-24.png`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/final-caption-contact-sheet.png`

## Final Local Review Composition

Final review artifact：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/final/qingyan-seedance2-fast-image-cards-captioned-28s-review-only.mp4`

Measured facts：

- SHA-256: `e965db27a4f67ce4fcf2258ae83ef67643e8474c170e3c85cced2af1330fd694`
- size: `13,158,494` bytes
- duration: `28.065s`
- video: H.264 High, `720x1280`, `24fps`, 673 frames
- audio: AAC stereo, `44.1kHz`, mean `-14.6 dB`, max `-1.3 dB`

Timeline：

1. `0.000-15.041667s`: retained causal story Shot 1
2. `15.041667-19.541667s`: repaired Shot 2 macro proof + lifestyle excerpt
3. `19.541667-23.541667s`: new supported-tabletop Fast Hero
4. `23.541667-25.041667s`: user card 1
5. `25.041667-26.541667s`: user card 2
6. `26.541667-28.041667s`: user card 3

Final audio retains Shot 1 native audio and the existing repaired Shot 2 native audio once. Fast raw AAC was verified as Provider evidence but intentionally not mixed into final，避免双重 ambience 或声场跳变。最终音轨包含一次 problem/recommendation/result narration 与一次 brand line；没有重复 slogan 或 card-claim narration。

Project-local `video-analysis` MCP 对 exact final hash 执行 29-frame comprehensive call 与 Whisper `medium` transcription；`ffmpeg` full decode 无错误。Primary join pairs at `14.98/15.08s`、`19.48/19.58s`、`23.50/23.58s` 均为 clean direct cuts，无 whip、flash、dissolve、morph 或 floating-box reveal。

Final Gate：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/final-review-gate.json`

Verdict：`PASS_FOR_LOCAL_REVIEW`。

## Assessment

本次修复关闭的是旧版本已证实的人眼缺陷：Hero 的瓶与盒从第一帧就接触真实木桌，contact shadow 持续存在，不再通过后入场盒子制造悬浮感。三张指定图片按 exact order 各显示 1.5 秒，字幕从“模型任意生成”提升为有 timing、copy、layout、source-corruption replacement 与 boundary sampling 的明确 Gate。

仍须保持三层 truth：

1. Fast raw Provider artifact：exact per-Shot Gate PASS，fetched/unactivated。
2. Final local composition：`PASS_FOR_LOCAL_REVIEW`，字幕与 card order 已检查。
3. Human/commercial acceptance：仍待用户观看；三张 card claims 仍未核验，不能发布。

## Remaining Risks And Guardrails

- 新成片仍需要用户对整体节奏、第一段 opaque caption backplate、文化呈现、中文发音和 card readability 做最终人眼/听审。
- 三张 card 含高风险 claims；除非提供 substantiation 并完成独立合规确认，否则不得移除 disclosure 或把 review-only artifact 变成 commercial-ready。
- 实际 Provider billing 未验证；只有 request count、finite ceiling 与 token-based estimate。
- 本地 `runs/` artifacts 未 stage、commit、activate、push 或 publish。
- 任何新 variant、retry、不同 model/provider、1080p upgrade、重新生成 audio、移除 disclosure 或 publication 都是新 scope，需新的 current-task authorization 与对应 Gate。
- `MP4 contains AAC`、local ffmpeg composition、Whisper transcript 与 local Gate 都不等于 canonical P4 ingestion、P6 或 Final Acceptance。
- 后续若进入 Production，必须走 canonical Asset Registry、`ResolvedTimeline`、Manifest、Review/Repair 与 activation owners；本记录不拥有 production state。
