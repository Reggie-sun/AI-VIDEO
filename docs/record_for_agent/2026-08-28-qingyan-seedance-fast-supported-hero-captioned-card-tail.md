# Qingyan Seedance Fast Supported Hero And Captioned Card Tail Record

Date: 2026-08-28

## Caption Repair V4 — 2026-08-28

用户以 exact screenshots 否决 V3 opening captions：源 Shot 1 已烧录模型字幕，V3 又在同一画面
叠加整行 authored captions，形成可见双层重影，而且修正层停在画面中部而不是底部。当前 local
review artifact 更新为：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/final/qingyan-seedance2-fast-image-cards-caption-repaired-v4-28s-review-only.mp4`

- SHA-256: `087497ae1b4be12b260899706c19698c8d7d88635708528a6b8cf0d1fd7ac4e1`
- size: `12,909,584` bytes
- 修复: 只重构源 Shot 1 的前两个 scene；将源烧录字幕裁出 output canvas，再在 bottom safe area 烧录唯一一层 authored captions
- scene-boundary discipline: 两组 crop 在 measured hard cuts `3.083333s` 与 `6.541667s` 切换，不在同一连续镜头中跳变
- rejected alternatives: `delogo` / `removelogo` 会在服饰与银饰上留下明显糊块；逐字覆盖无法稳定匹配源字体，均未进入 V4
- 保持不变: `28.065s`、`720x1280`、`24fps`、`673` decoded video frames、后续 Shot/card 顺序和 caption timing
- audio invariance: V3 / V4 decoded audio SHA-256 均为 `e5e682a1991a30a936a275b878f7a499dd313c8a4888b20453dbb017719c2952`
- Provider / network / paid call: `0`；本次仅执行 local deterministic re-composition

Exact V4 opening frames 覆盖 `0.50s`、`1.15s`、`3.20s`、`4.95s`，scene-cut frames
覆盖 `3.04/3.10s` 与 `6.50/6.55s`。可见文案只有 `出汗黏衣` / `靠近也不自在` /
`长辈递来这瓶` / `喷一下` 一层，统一位于 bottom safe-area baseline；embedded `粘` / `考` /
`坤` 错字与原中部字幕均不再进入画面。Evidence：

- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/caption-repair-v4-final/opening-sheet.png`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/caption-repair-v4-final/scene-cut-sheet.png`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/caption-repair-v4-final/tail-sheet.png`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/caption-repair-v4-gate.json`

Project-local `video-analysis` 对 exact V4 MP4 抽取 18 frames，并确认 duration、fps、resolution
与 audio presence。其 generic `low_resolution` hint 使用 landscape-oriented baseline 比较 portrait
width，不是 caption failure，也不改变本任务已接受的 `720x1280` contract。V4 verdict 仍只为
`PASS_FOR_LOCAL_REVIEW_ONLY`；三张 card claims 继续 `NOT_EVALUATED`。

## Caption Repair V3 — 2026-08-28

用户再次以 exact screenshot 指出第一个 advertising-card window 中，底部
`用户提供素材｜功效与数据未核验` disclosure 与既有对白字幕形成视觉竞争，并明确要求移除该
disclosure。当前 local review artifact 更新为：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/final/qingyan-seedance2-fast-image-cards-caption-repaired-v3-28s-review-only.mp4`

- SHA-256: `1921abae6ffd7bad5800163ffc80e909860b4b9b514513ec85cca8c8fa7c5ffa`
- size: `13,457,230` bytes
- 修复: 从 `compose_review.sh` 与 `captions.ass` 移除完整 disclosure render event；三个 card window 均不再显示该字条
- 保持不变: `28.065s`、`720x1280`、`24fps`、`673` decoded video frames、Shot/card 顺序与既有对白字幕 timing
- audio invariance: V2 / V3 decoded audio SHA-256 均为 `e5e682a1991a30a936a275b878f7a499dd313c8a4888b20453dbb017719c2952`
- Provider / network / paid call: `0`；本次仅执行 local deterministic re-composition

用户随后以上述 exact opening screenshots 否决 V3 的双层字幕与中部 baseline；V3 现为历史
artifact，不再是当前 caption-quality evidence。

Exact V3 tail frames 已覆盖 `23.60s`、`24.20s`、`25.20s` 与 `27.20s`。第一个 card
window 的 `清爽舒适` 仍位于既有 lower-third baseline，旧 disclosure 已消失；后两个 card
window 同样不再显示该字条。Evidence：

- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/caption-repair-v3-tail-sheet.png`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/caption-repair-v3-gate.json`

这次用户指令改变的是 local review overlay，不是 claim substantiation。三张用户素材中的功效、
机理、百分比与 testimonial claims 仍未核验；V3 继续是 local review-only，移除字条不构成
publication、commercial approval、P6 或 Final Acceptance。

## Caption Repair V2 — 2026-08-28

用户随后以 exact screenshots 否决下文初版 `e965db27...fd694` 的字幕视觉：开场两条 opaque backplate 过大，Hero 上的短词 `青颜` 形成孤立方块。该初版的 timeline、audio、card order、Provider call count 与 codec 测量仍是历史事实，但不再作为当前 caption-quality evidence。

该版本此前作为 current local review artifact，现已被上方 V3 取代；其字幕视觉修复与媒体测量仍保留为历史 evidence：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/final/qingyan-seedance2-fast-image-cards-caption-repaired-v2-28s-review-only.mp4`

- SHA-256: `2cb2b744e80e445515cf5d75e503347a4cb5f21bd3236a3069ebeade00c130bd`
- 修复: 所有 dialogue / brand captions 移除矩形底板，统一为白字、黑描边和轻阴影
- 开场拆分: `出汗黏衣` / `靠近也不自在`
- 推荐拆分: `长辈递来这瓶` / `喷一下`
- corrupt-source handling: corrected larger glyphs 放在原字幕 baseline，覆盖 embedded `粘` / `考` / `坤` 错字；不使用 opaque box、blur strip 或第二行重复字幕
- Provider / network / paid call: `0`；本次仅执行 local deterministic re-composition

本记录后续 `Caption Contract And Repair`、`Final Local Review Composition` 与 `Remaining Risks And Guardrails` 已更新到 V4；初版、V2 与 V3 文件保留在本地，仅作为历史 evidence。

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

三个 source 虽以 `.png` 命名，magic bytes 实际为 RIFF WebP；本地用 `ffmpeg` 转成 exact RGB24 PNG。V2 三张卡全程显示 `用户提供素材｜功效与数据未核验`；V3 及后续版本按用户明确指令移除该 on-video disclosure，但 claim status 没有变化。因此 V4 仍只允许 review-only，不得把 source copy 或字条移除解释成已经 substantiated 或可发布。

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
3. 开场长句按自然语义与 measured audio 拆成 `出汗黏衣` / `靠近也不自在`，推荐句拆成 `长辈递来这瓶` / `喷一下`，避免横向长条字幕。
4. `Noto Sans CJK SC`、最多两行、单行不超过 14 个中文字符；dialogue / brand captions 统一使用白字、黑描边与轻阴影，禁止 opaque 或 translucent rectangular backing。V4 将 corrupt embedded captions 裁出 output canvas，并在 bottom safe area 只保留一层 authored captions；不得出现 cover box、blur strip 或 duplicate line。
5. V4 不包含 disclosure track。三张 card 的对白字幕保持既有 lower-third baseline，不覆盖 card main copy；不得再次口播或新增未核验数据。

V4 opening、scene-cut 与 tail contact sheets 及 exact full-size frames 已人工复核；没有矩形 dialogue backing、双层字幕、旧错字露出、blur strip、clipping、card body-copy overlap、disclosure overlay 或 slogan repetition。

Evidence：

- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/shot-contract.md`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/captions.ass`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/caption-repair-v4-final/opening-sheet.png`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/caption-repair-v4-final/scene-cut-sheet.png`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/caption-repair-v4-final/tail-sheet.png`
- `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/caption-repair-v4-gate.json`

## Final Local Review Composition

Final review artifact：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/final/qingyan-seedance2-fast-image-cards-caption-repaired-v4-28s-review-only.mp4`

Measured facts：

- SHA-256: `087497ae1b4be12b260899706c19698c8d7d88635708528a6b8cf0d1fd7ac4e1`
- size: `12,909,584` bytes
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

Project-local `video-analysis` MCP 对 exact V4 final hash 以 `0.5s` interval 抽取 18 frames；字幕修复 sheets 另覆盖 opening、source hard-cut boundaries 与 tail。`ffmpeg` full decode 无错误；V3 与 V4 decoded audio SHA-256 同为 `e5e682a1991a30a936a275b878f7a499dd313c8a4888b20453dbb017719c2952`。

Final Gate：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/caption-repair-v4-gate.json`

Verdict：`PASS_FOR_LOCAL_REVIEW_ONLY`。

## Assessment

本次先关闭旧版本已证实的 Hero 悬浮缺陷，再根据用户 screenshots 关闭初版 caption backing、后续 disclosure collision，以及 V3 opening 双层字幕与中部 baseline 缺陷。Hero 的瓶与盒从第一帧就接触真实木桌，三张指定图片按 exact order 各显示 1.5 秒；V4 opening 只保留 bottom safe area 的一层 authored captions，且不再显示 disclosure track。

仍须保持三层 truth：

1. Fast raw Provider artifact：exact per-Shot Gate PASS，fetched/unactivated。
2. Final local composition V4：`PASS_FOR_LOCAL_REVIEW`，字幕与 card order 已检查。
3. Human/commercial acceptance：仍待用户观看；三张 card claims 仍未核验，不能发布。

## Remaining Risks And Guardrails

- 新成片仍需要用户对整体节奏、V4 opening 的局部近景构图、字幕字重与位置、文化呈现、中文发音和 card readability 做最终人眼/听审。
- 三张 card 含高风险 claims；V4 不含 on-video disclosure，但除非提供 substantiation 并完成独立合规确认，仍不得把 review-only artifact 变成 commercial-ready 或可发布素材。
- 实际 Provider billing 未验证；只有 request count、finite ceiling 与 token-based estimate。
- 本地 `runs/` artifacts 未 stage、commit、activate、push 或 publish。
- `retrieve-ai-video-memory` 本次返回 tagged last-good stale fragments 并排队 detached refresh；未等待、轮询或重建索引，当前字幕结论来自 exact media、composition files 与本轮视觉证据。
- 任何新 variant、retry、不同 model/provider、1080p upgrade、重新生成 audio 或 publication 都是新 scope，需新的 current-task authorization 与对应 Gate。
- `MP4 contains AAC`、local ffmpeg composition、Whisper transcript 与 local Gate 都不等于 canonical P4 ingestion、P6 或 Final Acceptance。
- 后续若进入 Production，必须走 canonical Asset Registry、`ResolvedTimeline`、Manifest、Review/Repair 与 activation owners；本记录不拥有 production state。
