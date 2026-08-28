# Caption Quality Gate Prior Art Research

Date: 2026-08-28

Status: Advisory research only; the recommendation below is not an accepted AI-VIDEO contract.

Scope: 成熟字幕/closed-caption pipeline 的 source-of-truth、pre-render validation、final-artifact QC、verdict 与 human-review 分层。

## Executive Findings

1. 成熟体系通常保留一份结构化 timed-text artifact，而不是把最终像素当作唯一字幕真相。W3C IMSC 1.3 将字幕建模为 TTML2 的 text profile，覆盖 timing、style、layout、language、profile 与 related video synchronization；EBU-TT-D 则以受约束的 XML/TTML profile 作为 IP distribution format；WebVTT 也把 external text track 表达为带时间区间和 cue settings 的 cues。[W3C IMSC 1.3](https://www.w3.org/TR/ttml-imsc1.3/)、[EBU Tech 3380](https://tech.ebu.ch/publications/tech3380)、[W3C WebVTT](https://www.w3.org/TR/webvtt1/)
2. Pre-render validation 可以可靠覆盖 syntax/profile、timing bounds、region/style constraints、language/glyph、render-complexity 等确定性问题，但不能证明最终字幕“看起来正确”。BBC 的官方 `ttml-validator` 明确说明 standalone technical validation 不能替代把字幕和关联媒体一起 preview，也不能确认 editorial 或 presentation guidelines；W3C IMSC HRM 也明确不约束 readability complexity。[BBC `ttml-validator`](https://github.com/bbc/ttml-validator)、[W3C IMSC HRM](https://www.w3.org/TR/imsc-hrm/)
3. 成熟 QC 会把 automatic inspection 和 manual/media-context review 分开。Netflix 的公开 QC 流程包含 Asset Upload、Auto QC/IaaS、Manual QC；Localization QC 会把 timed-text events 与 waveform 对齐检查 sync，并由 QC operator 记录修改和错误分类。[Netflix Introduction to QC](https://partnerhelp.netflixstudios.com/hc/en-us/articles/115000353211-Introduction-to-Netflix-Quality-Control-QC)
4. Published style rule 不等于 automated enforcement。Netflix 公布了 duration、line treatment、positioning、shot-change timing 与 gap rules，但同时说明大多数语言的 characters-per-line 目前并没有 Automated QC enforcement。[Netflix General Requirements](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements)、[Netflix Subtitle Timing Guidelines](https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines)、[Netflix characters-per-line FAQ](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215274938-What-is-the-maximum-number-of-characters-per-line-allowed-in-Timed-Text-assets)
5. FCC 14-12 将 caption quality 明确拆为 `accuracy`、`synchronicity`、`program completeness`、`placement`；其中 accuracy 包含 dialogue/sounds/music 与 speaker identity，synchronicity 同时包含 audio coincidence 和 readable speed，placement 要避免遮挡 faces、featured text、graphics 等重要信息。[FCC 14-12](https://docs.fcc.gov/public/attachments/fcc-14-12a1.pdf)
6. **Inference for AI-VIDEO:** 需要的不是把更多规则塞进现有 layout metric，而是建立两段式证据链：`CaptionTrack/ResolvedTimeline` 的 deterministic pre-render lint，加上绑定 exact rendered artifact 的 post-render Caption Quality Gate；只有 required findings 全部得到可靠证据时才能 `PASS`。

## Canonical Timed-Text And Timing Contracts

### Source facts

- W3C IMSC 1.3 是 2026-05-21 发布的当前 IMSC text-profile Recommendation，目标是 worldwide subtitle/caption authoring and delivery；它定义显式 profile designator，并约束 timing、style、regions、fonts、writing modes、active area 与 related-video synchronization。[W3C IMSC 1.3 Recommendation](https://www.w3.org/TR/2026/REC-ttml-imsc1.3-20260521/)
- IMSC 1.3 的 synchronization contract 将每个 Intermediate Synchronic Document 绑定到 related video object 的特定显示帧和移除帧。因此 timed text 与媒体的关系不是一串无上下文 timestamp，而是同一 presentation timebase 上的 frame-resolved contract。[W3C IMSC 1.3, Synchronization](https://www.w3.org/TR/ttml-imsc1.3/#synchronization)
- WebVTT cue 同样具有 start/end timestamps，并可携带 `vertical`、`line`、`position`、`size`、`align` 等 presentation settings；这说明 timing 和 placement 都属于 timed-text artifact，而非只能在 burn-in 后逆向猜测。[W3C WebVTT](https://www.w3.org/TR/webvtt1/)
- EBU-TT-D 是基于 TTML、为 IP subtitle distribution 收敛后的 XML format；EBU 说明该 profile 同时承载 text、styling、timing 与 positioning，并通过减少 feature set 来提高 decoder/renderer interoperability。[EBU Tech 3380](https://tech.ebu.ch/publications/tech3380)、[EBU publication announcement](https://tech.ebu.ch/news/ebu-puts-subtitles-on-line-30jan14)
- BBC 当前 Subtitle Guidelines 将 closed subtitles 视为独立于画面的可开关文件，并说明 BBC 一般接受 EBU-TT Part 1（broadcast）及 EBU-TT-D（online-only）。[BBC Subtitle Guidelines](https://www.bbc.co.uk/accessibility/forproducts/guides/subtitles/)

### Inference

跨这些体系可抽取的 license-safe contract pattern 是：canonical timed-text 至少要稳定标识 `content/language`、cue identity、半开或等价明确的 start/end 边界、media timebase、style/region、speaker/role（适用时）以及关联媒体 identity。最终 renderer 是该 contract 的 consumer；burned-in pixels 是 presentation outcome，不应反向成为第二份 source of truth。

对 AI-VIDEO 而言，这与当前 `CaptionTrack -> ResolvedCaptionCue -> ResolvedTimeline` 方向一致：`CaptionTrack` 继续拥有 script/transcript/alignment/segment identity，`ResolvedTimeline` 继续独占 sample/frame timing，renderer 只消费 resolved cues。这里没有证据支持引入第二条 caption timeline 或让 OCR 结果改写 canonical text。

## Automated Pre-Render Validation

### What mature systems validate

| Validation surface | First-party example | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Syntax/profile/conformance | IMSC 1.3 profile constraints；规范同时指出附带 XML Schema 是 non-normative，且不足以单独证明 document conformance。[W3C IMSC 1.3, XML Schema Definitions](https://www.w3.org/TR/ttml-imsc1.3/#xml-schema-definitions) | Document 满足选定 profile 的 machine-checkable constraints | 实际 renderer 输出、编辑质量、可读性 |
| Render-complexity budget | IMSC HRM 在 distribution 前用 static analysis 约束 presentation complexity；authoring system 可标记超限点，ingest 可拒收。[W3C IMSC HRM](https://www.w3.org/TR/imsc-hrm/) | 内容不超过约定的 hypothetical rendering complexity | 实际 renderer 性能、subpixel fidelity、readability；规范明确排除 readability complexity |
| Broadcaster technical rules | BBC `ttml-validator` 对 EBU-TT-D/BBC technical requirements 输出 `Pass`、`Info`、`Warn`、`Fail`，覆盖 namespace、font/style、region、timing expression、subtitle IDs 等要求。[BBC validator README](https://github.com/bbc/ttml-validator)、[BBC validator technical requirements](https://github.com/bbc/ttml-validator/discussions/10) | 精确 technical requirement 是否命中 | 与媒体一起 preview 后的 presentation、editorial correctness |
| Distribution QC tests | EBU 的 subtitling overview 列出 format compliance、language validation、subtitle duration、subtitle synchronisation 等 QC test examples。[EBU Subtitling factsheet](https://tech.ebu.ch/docs/factsheets/Subtitling_v4.1.pdf) | 可重复的格式、语言、时长、同步检查 | 观众是否易读、翻译/文案是否自然 |
| Platform style lint | Netflix 公开 minimum/maximum duration、最多两行、语义 line breaking、top/bottom positioning、shot-change timing 与 gap rules。[Netflix General Requirements](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements)、[Netflix Timing Guidelines](https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines) | 对选定 delivery policy 可量化的 authored-track 规则 | 所有规则都已自动化；Netflix 明确说大多数语言 CPL 没有 Automated QC enforcement |

### Inference

AI-VIDEO 的 pre-render lint 应只裁决它能从 canonical track、timeline、policy 和 registered style/font evidence 确定证明的事项，例如：

- track/content/style identity、hash 与 freshness；
- cue 非空、顺序、start/end、overlap/gap、media bounds、sample/frame projection；
- approved script/transcript 与 cue text 的 exact lineage；
- policy-selected duration、line count、line breaking、reading-rate/CPS、glyph/font coverage；
- style/region/active-area/safe-area 的静态可满足性；
- selected renderer/profile 的 feature support 与 render-complexity ceiling。

阈值必须是 language/delivery-policy scoped。不能因为 Netflix、BBC 或 EBU 采用某个数字，就把它无条件复制成 AI-VIDEO 的跨语言 universal rule；Netflix 自身也要求同时遵守 language-specific、timing 和 file-type-specific guidelines。[Netflix General Requirements](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements)

## Post-Render And Final-Artifact QC

### Source facts

- BBC 的 validator 明确要求 standalone validation 之外仍要 preview “presented file against the media it relates to”。这是 final presentation check，验证对象已从 abstract timed-text document 变成字幕与媒体共同呈现的结果。[BBC `ttml-validator`](https://github.com/bbc/ttml-validator)
- Netflix Localization QC 把 timed-text events 与 audio waveforms 对齐，用于 sync verification；QC operator 还会检查 translation quality、consistency 和 style-guide conformance，并记录每次修改及 error category。[Netflix Introduction to QC](https://partnerhelp.netflixstudios.com/hc/en-us/articles/115000353211-Introduction-to-Netflix-Quality-Control-QC)
- Netflix 同时区分 Spot QC 与 Full QC；高优先级内容会 review entire asset，而不是仅凭抽样或一次自动检查宣称整片通过。[Netflix Introduction to QC](https://partnerhelp.netflixstudios.com/hc/en-us/articles/115000353211-Introduction-to-Netflix-Quality-Control-QC)
- Netflix 对 burned-in locator text/subtitles/forced narratives 的公开说明进一步表明，generic BQC 并不默认逐行检查所有 graphical text；titles/credits 与 production post team 对其完整性、准确性另有明确 ownership。[Netflix Credit Spelling and Grammatical Errors](https://partnerhelp.netflixstudios.com/hc/en-us/articles/1500004567161-Credit-Spelling-and-Grammatical-Errors)

### Inference

对 burned-in/final MP4，post-render Gate 至少应针对 exact output bytes 检查：

- 每个 required cue 是否在预期 frame window 中实际出现并按时消失；
- rendered text 是否与 canonical cue text 一致，是否发生缺字、错字、截断、错误换行、重复或双层字幕；
- bbox、safe area、与画面内文字/商品图层的 collision、contrast、font fallback、字号和视觉可读性；
- cue 与实际 audio/dialogue 的 onset/offset、speaker/semantic coverage 是否合理；
- source footage/model output 中已有文字时，是否出现无法由 canonical `CaptionTrack` 解释的额外 burned-in text。

OCR、ASR、waveform、frame sampling 和 renderer telemetry 可以提供 measured evidence，但不能单独证明完整 editorial/perceptual acceptance。尤其当 OCR/ASR confidence 低、语言模型不支持、字幕与画面文字难以区分、抽样没有覆盖全部 cue window，或 media/hash 不匹配时，正确结果应是 `NOT_EVALUATED`，而不是把“没有检测到问题”升级成 `PASS`。

## Verdicts And Human Review

### Source facts

- BBC technical validator 使用 `Pass/Info/Warn/Fail`，同时明确 technical validation 不能确认 editorial/presentation quality。[BBC `ttml-validator`](https://github.com/bbc/ttml-validator)
- Netflix timing guidance 直接要求在 shot change、subtitle hanging、gap closure 等情况下运用 good judgement，并说明很多 timing decisions 具有主观性。[Netflix Subtitle Timing Guidelines](https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines)
- Netflix Localization QC 是人工 operator review，并把 technical、translation、language 等 error rates 分开统计，而不是压成一个总分。[Netflix Introduction to QC](https://partnerhelp.netflixstudios.com/hc/en-us/articles/115000353211-Introduction-to-Netflix-Quality-Control-QC)
- W3C HRM 明确是 technical complexity model，不是 readability model。[W3C IMSC HRM](https://www.w3.org/TR/imsc-hrm/)
- FCC 对 pre-recorded programming 要求四个维度同时满足，而不是把 accuracy 或 placement 作为其它维度的替代指标。[FCC 14-12](https://docs.fcc.gov/public/attachments/fcc-14-12a1.pdf)

### Inference

AI-VIDEO 应保留 requirement-level 三态：

- `PASS`：该 requirement 所需 evidence 完整、current、绑定 exact inputs/output，且判定满足 policy；
- `FAIL`：已有 current evidence 直接证明违反 requirement；
- `NOT_EVALUATED`：缺少 required evidence、identity/freshness 不匹配、工具不支持、coverage 不完整，或 machine evidence 不足以可靠裁决。

Aggregate Gate 只有在全部 current required requirements 均为 `PASS` 时才可 `PASS`。任何 required `FAIL` 应阻断；任何 required `NOT_EVALUATED` 也应 fail closed，但必须保留“未判定”和“已证明失败”的语义差异。Human review 应负责 editorial accuracy、自然分段、主观 timing/readability、speaker/context 与 machine ambiguity；它不应覆盖 hash mismatch、stale evidence、out-of-bounds timing 等 deterministic failures。

## Comparison

| System | Canonical/authoring representation | Automated or deterministic layer | Media-context/final layer | Explicit separation lesson |
| --- | --- | --- | --- | --- |
| W3C IMSC 1.3 + HRM | TTML2 text profile，含 timing/style/layout/profile/related-video semantics | Conformance + static render-complexity model | Presentation processor/actual viewing不由 HRM 证明 | HRM 明确不证明 readability。[IMSC 1.3](https://www.w3.org/TR/ttml-imsc1.3/)、[HRM](https://www.w3.org/TR/imsc-hrm/) |
| EBU-TT-D | 受约束的 TTML/XML distribution document | Format/language/duration/synchronisation QC examples | Broadcaster presentation/editorial流程在 format spec 之外 | Distribution interoperability 与 audience quality 不是同一 verdict。[Tech 3380](https://tech.ebu.ch/publications/tech3380)、[EBU factsheet](https://tech.ebu.ch/docs/factsheets/Subtitling_v4.1.pdf) |
| BBC | EBU-TT-D/EBU-TT aligned subtitle files | `ttml-validator` technical requirements；`Pass/Info/Warn/Fail` | 必须把 presented file 与 media 一起 preview；editorial/presentation另行判断 | 官方工具明确声明 technical validation 不是 final QC。[BBC validator](https://github.com/bbc/ttml-validator) |
| Netflix | Delivery timed-text asset + language/file/timing-specific style contract | Ingest Auto QC/IaaS + 可量化 style rules | Manual QC；events 对 waveform；Spot/Full review；operator corrections | Published rule、automated enforcement、manual localization QC 是不同层。[Netflix QC](https://partnerhelp.netflixstudios.com/hc/en-us/articles/115000353211-Introduction-to-Netflix-Quality-Control-QC)、[Netflix style guide](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements) |
| FCC 14-12 | 监管定义的 closed-caption quality contract | 可将 technical measurements 分别归入四维 | 预录节目须同时 accurate、synchronous、complete、appropriately placed | Accuracy、sync、coverage、placement 是并列质量轴，不应压成 layout 或总分。[FCC 14-12](https://docs.fcc.gov/public/attachments/fcc-14-12a1.pdf) |

## Recommended Minimum Gate Contract For AI-VIDEO

以下只是 prior-art-driven proposal，不是 accepted architecture，也不授权修改 runtime、Manifest、P6 policy 或 Final Acceptance：

### Placement

```text
CaptionTrack
  -> deterministic caption lint
  -> ResolvedTimeline.caption_cues
  -> selected renderer
  -> exact final media bytes
  -> Caption Quality Gate
  -> existing P6 review / Final Acceptance ownership
```

Pre-render lint 可以在 render 前阻断确定性错误；真正的 Caption Quality Gate 必须在 final artifact 产生后运行，因为 overflow、font fallback、collision、缺字、重复 burn-in、实际 audio-sync 和视觉可读性只有 presentation outcome 才能证明。该分层是对 BBC preview requirement、Netflix waveform/manual QC 与 W3C HRM scope limit 的综合推论。[BBC validator](https://github.com/bbc/ttml-validator)、[Netflix QC](https://partnerhelp.netflixstudios.com/hc/en-us/articles/115000353211-Introduction-to-Netflix-Quality-Control-QC)、[W3C IMSC HRM](https://www.w3.org/TR/imsc-hrm/)

### Required immutable inputs

- selected caption policy ID/version/content hash；
- exact `CaptionTrack` identity/content hash/timing fingerprint；
- exact approved script/transcript identity；
- exact `ResolvedTimeline` fingerprint、fps/sample rate、cue projection；
- selected renderer/style/font identity；
- exact source audio identity；
- exact final MP4 SHA-256/container/probe identity；
- evaluator/tool/actor identity、coverage manifest 与 evidence hashes。

### Required finding groups

| Group | Minimum required findings | Preferred evidence |
| --- | --- | --- |
| `SOURCE_INTEGRITY` | authored text、language、speaker、script/transcript lineage、cue/style identity current（FCC `accuracy`） | deterministic structured comparison |
| `TIMING_CONTRACT` | sample/frame bounds、duration、gap/overlap、shot-boundary policy、cue/audio projection（FCC `synchronicity`） | `CaptionTrack` + `ResolvedTimeline` + waveform/alignment evidence |
| `RENDER_COMPLETENESS` | 每个 cue 在 exact frame window 中出现；无缺失、截断、错误换行、重复/双层字幕（FCC `completeness`） | full cue-window frame coverage + OCR/renderer evidence；低置信时 human |
| `LAYOUT_READABILITY` | safe area、collision、font fallback、glyph、contrast、line count/size（FCC `placement`，并覆盖 readable speed 的呈现结果） | renderer-bound measurements + actual-frame review |
| `AUDIO_SEMANTIC_SYNC` | 与实际 dialogue 的 onset/offset、text coverage、speaker/context 合理（FCC `accuracy + synchronicity`） | waveform/ASR/alignment + human editorial review |
| `UNINTENDED_TEXT` | final pixels 中不存在 canonical track 无法解释的额外模型内嵌/重复字幕（FCC `accuracy + placement`） | full-frame text detection/OCR + human disambiguation |

### Verdict rule

每个 required finding 独立记录 `PASS | FAIL | NOT_EVALUATED`、evidence IDs、reason 与 exact coverage。Gate aggregate 只接受 all-required `PASS`；不使用单一总分，不允许 OCR/ASR “无发现”替代 coverage proof，不允许 human statement 修复 stale/hash mismatch，也不让 Gate 自行 activation、repair、retry 或 Final Acceptance。Durable lifecycle 仍应回到 AI-VIDEO 现有 P6/`ProductionStateCommitter` owner；是否新建 QA layer、扩展现有 `LAYOUT`，或作为 typed caption sub-policy，仍需单独 architecture decision。

## Risks And Open Questions

- IMSC、EBU-TT-D、BBC 与 Netflix 的主流材料大多面向 sidecar/closed timed text；AI-VIDEO 的 selected renderer 可能 burn captions into final pixels。因此 format conformance 可以借鉴，但 final-pixel coverage 不能照搬。
- Language-specific CPS/CPL、中文断句、广告短片中的 kinetic typography、竖排/双语字幕可能需要不同 policy；目前没有证据支持一个 universal threshold。
- OCR/ASR 对 stylized font、运动背景、中文专名、方言、音乐和多人重叠说话会产生不确定性；必须保留 `NOT_EVALUATED` 和 human escalation。
- “字幕”和 deliberate on-screen commercial text 必须有不同 semantic identity，否则 unintended-text detector 会制造 false positive。
- 当前仓库 `QaLayer.LAYOUT` 已覆盖 `caption_overflow`、safe area、layer collision、transition boundary，但未证明 authored text fidelity、full cue presence、audio/semantic sync、double-burn 或 readability。是扩展现有 layer 还是新增 caption-specific typed sub-policy，应先由 current code/tests/ownership 做 architecture mapping；本报告不作 accepted decision。
- 本轮只研究公开 primary sources，没有对 AI-VIDEO exact MP4 做 OCR、ASR、waveform 或 human viewing，因此不产生任何 runtime、P6 或 quality-acceptance verdict。

## Primary Sources

- [W3C IMSC Text Profile 1.3](https://www.w3.org/TR/ttml-imsc1.3/)
- [W3C IMSC Hypothetical Render Model](https://www.w3.org/TR/imsc-hrm/)
- [W3C WebVTT](https://www.w3.org/TR/webvtt1/)
- [EBU Tech 3380: EBU-TT-D](https://tech.ebu.ch/publications/tech3380)
- [EBU Subtitling factsheet](https://tech.ebu.ch/docs/factsheets/Subtitling_v4.1.pdf)
- [BBC Subtitle Guidelines](https://www.bbc.co.uk/accessibility/forproducts/guides/subtitles/)
- [BBC `ttml-validator`](https://github.com/bbc/ttml-validator)
- [BBC validator technical requirements](https://github.com/bbc/ttml-validator/discussions/10)
- [Netflix Timed Text Style Guide: General Requirements](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements)
- [Netflix Timed Text Style Guide: Subtitle Timing Guidelines](https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines)
- [Netflix characters-per-line FAQ](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215274938-What-is-the-maximum-number-of-characters-per-line-allowed-in-Timed-Text-assets)
- [Netflix Introduction to Quality Control](https://partnerhelp.netflixstudios.com/hc/en-us/articles/115000353211-Introduction-to-Netflix-Quality-Control-QC)
- [Netflix Credit Spelling and Grammatical Errors](https://partnerhelp.netflixstudios.com/hc/en-us/articles/1500004567161-Credit-Spelling-and-Grammatical-Errors)
- [FCC 14-12: Closed Captioning of Video Programming](https://docs.fcc.gov/public/attachments/fcc-14-12a1.pdf)
