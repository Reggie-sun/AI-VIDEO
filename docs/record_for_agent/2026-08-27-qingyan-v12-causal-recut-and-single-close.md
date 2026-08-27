# Qingyan V12 Causal Recut And Single Close Record

Date: 2026-08-27

> **Superseded current verdict — 2026-08-27:** 用户完成正常观看后否决 v12 作为当前可接受方案：老人推荐与少女取得产品之间仍缺少可见的交接动作，因果桥没有成立；因此本记录下方的 `PASS_FOR_HUMAN_REVIEW` 只保留为当时的技术检查边界，当前 human verdict 已替换为 `NEEDS_REVISION`。新的单 Shot Seedance Mini 交接实验及其 credential blocker 记录在 `docs/record_for_agent/2026-08-27-qingyan-seedance-mini-handoff-preflight-blocker.md`。原有 codec、frame、audio 和 static-analysis 测量仍是 v12 exact bytes 的历史事实，但不再构成创意结构通过。

## Purpose

本文记录用户对 v10 的第二轮完整观看修正，以及基于 v10 / v8 已接受媒体完成的 v12 本地重剪。用户指出：
老人应先推荐，少女随后才喷用并表现效果；首 Shot 没有声音也未形成明确问题；约 `11s` 后运镜异常；
`22s` 切镜与转场异常；最后两张静图和反复广告词均不自然。

本记录不把 v12 描述成 P6、Final Acceptance、publication-ready 或投放效果证据。媒体与 composition
artifact 仍为 local-only；本轮没有新的 AI-VIDEO Provider、ComfyUI、paid submit、Production Manifest
mutation、activation、release、push 或 publication action。

## Current Runtime Truth

v12 不是新的生成 Shot。仓库当前普通创作没有可直接复用的 canonical H3 operator；
`ShotContinuity` operator 属于 qualification 专用。为避免绕过 durable intent / permit 或扩大成新的
Production qualification，本轮只消费已落盘且绑定 SHA-256 的 v10 / v8 accepted media，并使用 FFmpeg
完成确定性重剪、对白重构、图形和混音。

project Agent Experience Memory 对
`qingyan v10 narrative elderly recommendation spray result camera transitions repeated slogan`
返回有效空结果 `[]`；没有把 missing retrieval 当成 runtime truth，也没有前台重建 RAG index。

## Session Work And Decisions

新 authoring surface：

```text
artifacts/qingyan-miao-ad-20260827-v12/
```

exact timeline 为 `720` frames at `24fps`：

| Beat | Frames | Time | Decision |
| --- | ---: | --- | --- |
| problem | 108 | `0.000-4.500` | 少女先察觉腋下不适；问题文案与衣物摩擦 SFX 同时建立冲突。 |
| elder recommends | 66 | `4.500-7.250` | 老人先完成唯一一次产品推荐；此时没有喷用动作。 |
| treatment | 144 | `7.250-13.250` | 连续开盖、放盖、抬臂、喷用；源素材冻结尾帧被退休。 |
| immediate result | 91 | `13.250-17.042` | 轻微慢动作表现放松微笑与收好产品。 |
| social result | 175 | `17.042-24.333` | 两人保持一个连续同行镜头。 |
| single product close | 136 | `24.333-30.000` | 一个持续缓慢推进的 packshot；无第二张静图、无结尾口播。 |

因此 `11s` 对应 frame `264`，位于 treatment 内；`22s` 对应 frame `528`，位于 social result 内。
两处都不是切点。成片只使用有因果动机的 hard cut；没有 `xfade`、闪白、方向突变、数字抖动或突然推拉。

老人推荐音轨只消费现有已接受 native dialogue：从老人原声保留称呼，再将现有合规产品语句做一次低音高重构。
全片只保留一次产品 speech，结尾只有 BGM 与轻微提示音。该方法消除了旧问答和重复广告词，但不等于新的
逐字 lip-sync Shot；正常速度下的声音自然度和口型仍需用户判断。

`ecommerce-ad-workflow` 的 input 与 package 都已建立：

```text
artifacts/qingyan-miao-ad-20260827-v12/ecommerce-input.json
artifacts/qingyan-miao-ad-20260827-v12/ecommerce-package.json
```

input 和 package validator 均返回 `status=valid`、`diagnostics=[]`；package 的
`source_input_hash=f358082ffcd80bd3ed3867bb1c03b0d44e9fd1aebb4e0ed0cae729d219d5469a`，
`package_id=b3dd381614b057275afbbdb86354ddc7894999560785cd62e042e9b8afbcebef`。

## Exact Outputs And Verification

Primary master：

```text
artifacts/qingyan-miao-ad-20260827-v12/final/青颜_苗家腋下止汗完整广告_30s_9x16_v12.mp4
SHA-256 94c6b7fc92202f6c7e979bb94b31ecd58aab40e3652113f1e78d66c3535a16a4
30,888,974 bytes; H.264; 1080x1920; 24fps; 720 frames;
AAC 48kHz stereo; container duration 30.022s
```

No-BGM review master：

```text
artifacts/qingyan-miao-ad-20260827-v12/final/青颜_苗家腋下止汗完整广告_30s_9x16_v12_no-bgm.mp4
SHA-256 deb515e8e94a78f253889bf8fc72df31b2ff025dd3ac2604de865817577e75ff
```

Primary audio measured `-15.6 LUFS`, `6.1 LU LRA`, `-2.4 dBTP`。fresh
`silencedetect=-42dB:0.35s` 和 `freezedetect=-50dB:1.0s` 均无区段。project-local
`video-analysis` 对 exact primary 运行：`video_review` 返回 `issues=[]`、`unique_frame_ratio=1.0`；
Whisper 只返回一段 speech，时间覆盖 `0.0-7.48s`，文本为
`姑娘 青岩一汉精尾喷屋 清爽舒適`。同音字误写只证明一次 speech / timing，不替代产品 copy truth。

Requirement-level Gate：

```text
artifacts/qingyan-miao-ad-20260827-v12/review/final-gate.md
```

结构、技术、静音、冻结、`11s` / `22s` 连续性、单一动态结尾与口播不重复均为 `PASS`；老人重构对白的
主观自然度、逐字口型和人类整体观感为 `NOT_EVALUATED`。当前边界是 `PASS_FOR_HUMAN_REVIEW`。

## Assessment

v12 已把 v10 的动作顺序改成 `问题 -> 老人推荐 -> 少女喷用 -> 清爽结果 -> 连续同行 -> 单一动态产品收口`。
它直接关闭用户点名的结构与切点问题，并退休 v10 treatment 的冻结尾帧、golden-fluid 静图、第二张静态
CTA 卡和结尾重复口播。

技术 evidence 支持把 exact primary master 交给用户完整观看/试听；它不证明重构对白自然、平台审核、
P6、Final Acceptance 或投放效果。

## Remaining Risks And Next Work

1. 用户需正常速度完整观看 primary master，重点判断 `4.500-7.250s` 重构推荐的音色连续性与口型，以及
   `13.250s` 由喷用到结果的 hard cut 是否自然。
2. `bgm-tech-house.mp3` 与 SFX 的 publication license provenance 在正式投流前仍需确认。
3. package validation 证明 authoring contract 闭合，不代表 Production Manifest activation 或 Runtime P6。
4. project RAG index 未由本轮刷新；experience retrieval 的空结果仍是本轮 advisory truth。

## Agent Guardrails

- 不得把 Whisper、`video_review issues=[]`、freeze/silence、contact sheet 或 package validator 当作人类声音自然度结论。
- 不得把对白重构描述成新生成的老人逐字 lip-sync Shot。
- v12 是 local development preview；不得宣称 Production candidate、P6、Final Acceptance、publication-ready 或转化效果。
- 后续若用户只否决推荐对白，应只替换 frames `108-173` / `4.500-7.250s`，保持其余 `654` frames 不变。
- 后续若需要新 H3 Shot，必须走当时 current canonical durable intent / permit path；不得恢复旧 direct `ComfyClient` 旁路。
