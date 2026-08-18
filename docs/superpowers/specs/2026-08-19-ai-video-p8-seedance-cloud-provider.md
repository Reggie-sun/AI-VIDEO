# AI-VIDEO P8 Seedance Cloud Provider Specification

Status: Dated compatibility matrix frozen and offline implementation accepted on 2026-08-19. Native review verdict is `accept`; default verification is fake-only/no-network. This document does not authorize a paid/live call, push or release.

## 1. Goal

本 slice 增加一个可删除的 `SeedanceVideoProvider` adapter，以 strict typed profile 和 declarative capability variants 覆盖执行日火山方舟官方 Model List 中仍公开可调用的全部 Seedance Model ID。adapter 复用 P8 Paid Provider Gate、stepwise submit/poll/fetch 和 fetched-candidate boundary，不增加 CLI、schema writer、resolver、renderer、自动选择或 fallback。

研究先发现完整 Seedance surface 无法由原 P8 core 无损表达并按约停止；用户明确授权后，slice 只扩展 provider-neutral media/mode/output contracts，并保持旧 request/resolved hashes 兼容。Seedance-specific fields 仍只存在于 adapter profile。

## 2. Authoritative Snapshot

执行日：`2026-08-19`。

Primary sources:

- [Model List](https://www.volcengine.com/docs/82379/1330310?lang=zh)：公开 Model ID、能力、输出格式和配额。
- [Create video generation task](https://www.volcengine.com/docs/82379/1520757?lang=zh)：`POST /api/v3/contents/generations/tasks`、鉴权、输入、参数和限制。
- [Get video generation task](https://www.volcengine.com/docs/82379/1521309?lang=zh)：同一 task 查询、状态和短期下载 URL。
- [Model pricing](https://www.volcengine.com/docs/82379/1544106?lang=zh)：当前按量刊例价、活动折扣和 token 估算公式。
- [Model retirement notice](https://www.volcengine.com/docs/82379/1350667?lang=zh)：EOM/EOS 与迁移目标。

官方 API Explorer 是 Create API 的交互入口，但动态页面不作为独立 alias source。只有 Model List 中的 exact Model ID，或账户中显式绑定到这些 Model ID 的 exact Endpoint ID，能进入 allowlist。

## 3. Model Eligibility Matrix

### 3.1 Included Model IDs

| Exact Model ID | Official status | Modes | Resolution / fps / duration | Container |
|---|---|---|---|---|
| `doubao-seedance-2-5-260628` | current | T2V; first-frame; first+last-frame; multimodal reference; video edit; video extend | 480p, 720p, 1080p; 24 fps; 4–30s | mp4, mov |
| `doubao-seedance-2-0-260128` | current | T2V; first-frame; first+last-frame; multimodal reference; video edit; video extend | 480p, 720p, 1080p, 4k; 24 fps; 4–15s | mp4 |
| `doubao-seedance-2-0-fast-260128` | current | same 2.0 mode family | 480p, 720p; 24 fps; 4–15s | mp4 |
| `doubao-seedance-2-0-mini-260615` | current | same 2.0 mode family | 480p, 720p; 24 fps; 4–15s | mp4 |
| `doubao-seedance-1-5-pro-251215` | legacy/EOM; EOS is 2026-09-21 14:00 UTC+8; existing service remains callable before EOS | T2V; first-frame; first+last-frame | 480p, 720p, 1080p; 24 fps; 4–12s | mp4 |
| `doubao-seedance-1-0-pro-250528` | current legacy generation | T2V; first-frame; first+last-frame | 480p, 720p, 1080p; 24 fps; 2–12s | mp4 |
| `doubao-seedance-1-0-pro-fast-251015` | current legacy generation | T2V; first-frame | 480p, 720p, 1080p; 24 fps; 2–12s | mp4 |

“Legacy” 只表示仍公开可用但接近 retirement 或属于旧 family；它不能绕过执行时的 account access 和 current status preflight。

### 3.2 Endpoint IDs

`model` 可传 Model ID 或 Endpoint ID。Endpoint ID 是账户/区域/计费配置相关的 `ep-*` identity，不存在可由公共文档冻结的全局列表。typed profile 必须同时固定：

- exact `endpoint_id`；
- endpoint 所绑定的 exact included Model ID；
- dated capability/pricing snapshot identity；
- expected region/origin。

任意未绑定底层 included Model ID 的 Endpoint ID、运行时发现的不同绑定、停用 endpoint 或未知计费类型都 fail closed。adapter 不把营销名转换成 Endpoint ID，也不静默从 Endpoint ID fallback 到 Model ID。

### 3.3 Explicit Exclusions

- `doubao-seedance-1-0-lite-i2v-250428` 与 `doubao-seedance-1-0-lite-t2v-250428` 已于 2026-05-11 终止服务，调用会被拒绝。
- `doubao-seedance-1-0-pro-fast-250610` 等不在执行日 Model List 的旧版本或 repo alias。
- `seedance-2.5`、`seedance-2.0`、`pro-fast` 等营销/族名。
- 未公开 preview、控制台展示名、任意 caller-supplied string。

## 4. Capability Matrix

Legend: `Y` supported, `N` unsupported, `A` adaptive/model-selected path, `—` not applicable.

| Family | T2V | first | last | reference image/video/audio | edit/extend | ratio | duration / frames | audio out | seed | watermark | draft | service tier |
|---|---:|---:|---:|---|---|---|---|---:|---|---:|---:|---|---|
| 2.5 | Y | Y | Y | 1–30 / 0–10 / 0–10; audio-only allowed | Y / Y | T2V/reference: named or `adaptive`; first/edit/extend: `adaptive` | `4..30` or `-1`; edit requires `-1`; no `frames` | Y, mono | N | Y, default false | N | `default` only |
| 2.0 | Y | Y | Y | 1–9 / 0–3 / 0–3; audio needs image/video | Y / Y | named or `adaptive` | `4..15` or `-1`; no `frames` | Y, mono | N | Y, default false | N | `default` only |
| 2.0 fast | Y | Y | Y | same 2.0 limits | Y / Y | named or `adaptive` | `4..15` or `-1`; no `frames` | Y, mono | N | Y, default false | N | `default` only |
| 2.0 mini | Y | Y | Y | same 2.0 limits | Y / Y | named or `adaptive` | `4..15` or `-1`; no `frames` | Y, mono | N | Y, default false | N | `default` only |
| 1.5 pro | Y | Y | Y | N | N | named or `adaptive` | `4..12` or `-1`; no `frames` | Y, mono | `-1..2147483647` | Y, default false | Y; 480p only; no last-frame/flex | `default`, `flex` |
| 1.0 pro | Y | Y | Y | N | N | named; I2V may use `adaptive` | `2..12` or `frames=25+4n`, 29..289 | N | `-1..2147483647` | Y, default false | N | `default`, `flex` |
| 1.0 pro fast | Y | Y | N | N | N | named; I2V may use `adaptive` | `2..12` or `frames=25+4n`, 29..289 | N | `-1..2147483647` | Y, default false | N | `default`, `flex` |

Additional typed fields:

- `camera_fixed`: 1.5 pro and 1.0 models only; reference-image scenario does not support it.
- `return_last_frame`: boolean, default false; returned PNG URL is short-lived evidence, never durable state.
- `output_format`: 2.5 supports `mp4|mov`; all other included models are `mp4`.
- `omni_reference_task_type`: 2.5 only, exact enum `auto|reference|edit|extend`; safe profile defaults to an explicit non-`auto` value for nontrivial multimodal tasks.
- `priority`: integer `0..9`, 2.5/2.0 only, unsupported with `flex`.
- `execution_expires_after`: `3600..259200`, default 172800 seconds.
- `callback_url` is excluded from V1 adapter. Poll remains the sole observation path.
- `tools`, `safety_identifier` and draft-to-final task chaining need explicit profile policy; they are not silently emitted.
- Detailed Create field documentation restricts `frames` to 1.0 pro/pro-fast, while the API Explorer summary labels it more broadly. The detailed field contract wins fail closed: 2.x/2.5 never emit `frames` until official documentation is reconciled or an explicitly authorized live check proves support.

### 4.1 Named Ratios and Measured Output

Named ratios are `21:9|16:9|4:3|1:1|3:4|9:16`; `adaptive` is model/mode dependent. Supported raster classes are:

- 2.5: 480p/720p/1080p; first-frame, first+last, edit and extend force adaptive preservation.
- 2.0: 480p/720p/1080p/4k.
- 2.0 fast/mini: 480p/720p.
- 1.5 and 1.0: 480p/720p/1080p.

Official exact pixels vary by family for the same label/ratio (for example 480p 16:9 is 854×480 on 2.5, 864×496 on 2.0/1.5, and 864×480 on 1.0). Therefore capability resolution must be a declarative `(model, resolution, ratio, mode) -> expected-or-adaptive dimensions` variant, not a global width/height lookup. Actual fetched dimensions remain measured evidence.

The strict profile freezes these official named-ratio rasters; columns are ordered `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`:

| Family / resolution | 21:9 | 16:9 | 4:3 | 1:1 | 3:4 | 9:16 |
|---|---|---|---|---|---|---|
| 2.5 480p | 992×432 | 854×480 | 752×560 | 640×640 | 560×752 | 480×854 |
| 2.5 720p | 1470×630 | 1280×720 | 1112×834 | 960×960 | 834×1112 | 720×1280 |
| 2.5 1080p | 2206×946 | 1920×1080 | 1664×1248 | 1440×1440 | 1248×1664 | 1080×1920 |
| 2.0 family 480p | 992×432 | 864×496 | 752×560 | 640×640 | 560×752 | 496×864 |
| 2.0 family 720p | 1470×630 | 1280×720 | 1112×834 | 960×960 | 834×1112 | 720×1280 |
| 2.0 standard 1080p | 2206×946 | 1920×1080 | 1664×1248 | 1440×1440 | 1248×1664 | 1080×1920 |
| 2.0 standard 4k | 4398×1886 | 3840×2160 | 3326×2494 | 2880×2880 | 2494×3326 | 2160×3840 |
| 1.5 480p | 992×432 | 864×496 | 752×560 | 640×640 | 560×752 | 496×864 |
| 1.5 720p | 1470×630 | 1280×720 | 1112×834 | 960×960 | 834×1112 | 720×1280 |
| 1.5 1080p | 2206×946 | 1920×1080 | 1664×1248 | 1440×1440 | 1248×1664 | 1080×1920 |
| 1.0 family 480p | 960×416 | 864×480 | 736×544 | 640×640 | 544×736 | 480×864 |
| 1.0 family 720p | 1504×640 | 1248×704 | 1120×832 | 960×960 | 832×1120 | 704×1248 |
| 1.0 family 1080p | 2176×928 | 1920×1088 | 1664×1248 | 1440×1440 | 1248×1664 | 1088×1920 |

Create API only accepts `resolution` and `ratio`; it has no output `width`/`height` fields. For named-ratio requests the adapter verifies caller-declared expected pixels against this matrix but submits only the official fields. Adaptive requests carry no invented pre-submit dimensions.

## 5. Input Limits

| Input | Official constraint |
|---|---|
| prompt | Chinese and English on all models; official guidance is <=500 Chinese characters or <=1000 English words |
| image | jpeg/png/webp/bmp/tiff/gif; 1.5+ also heic/heif; ratio 0.4..2.5; each side 300..6000 px; <30 MB each; request body <=64 MB |
| first / first+last | exactly 1 / 2 images with exact roles; first and last mode is mutually exclusive with multimodal reference |
| 2.5 reference images | 1..30 |
| 2.0 reference images | 1..9 |
| video reference | mp4/mov; 480p..4k; side 300..6000; ratio 0.4..2.5; total pixels 407696..8295044; <=200 MB; 24..60 fps |
| 2.5 reference video | 2..30s each, edit input 4..30s; <=10 videos and <=30s total |
| 2.0 reference video | 2..15s each; <=3 videos and <=15s total |
| audio reference | wav/mp3; <=15 MB each; request body <=64 MB |
| 2.5 reference audio | 2..30s each; <=10 clips and <=30s total; audio-only allowed |
| 2.0 reference audio | 2..15s each; <=3 clips and <=15s total; at least one image/video required |
| face-bearing reference | 2.5/2.0 do not accept arbitrary real-face uploads; only officially allowed trusted/authorized asset paths may be used |

V1 adapter must accept already materialized, measured, sealed local inputs only. Public remote input URLs, inline Base64, `asset://` IDs and draft task IDs are distinct egress/provenance surfaces and cannot be enabled implicitly.

## 6. API, Status and Price Semantics

### 6.1 Endpoints and Authentication

- Base origin: `https://ark.cn-beijing.volces.com`.
- Submit: `POST /api/v3/contents/generations/tasks`.
- Query: `GET /api/v3/contents/generations/tasks/{task_id}`.
- Delete/cancel is not part of current P8 `VideoProvider` protocol and is out of this adapter slice.
- Authentication: Bearer API Key. The fixed secret reference name is `ARK_API_KEY`.

The adapter receives an injected credential supplier; it never reads environment variables itself. There is no `SEEDANCE_API_KEY`, MiniMax key, shared-key or anonymous fallback.

### 6.2 Status Normalization

Official observed states are `queued`, `running`, `succeeded`, `failed`, `cancelled`, and `expired`. P8 core has queued/running/succeeded/failed; the adapter maps `cancelled|expired` to normalized failed and never preserves raw provider responses or URLs.

`video_url` and `last_frame_url` are short-lived results (24h; 2.5 also documents a 100-download limit). Official docs do not promise a fixed result hostname, redirect behavior, `Content-Length`, or reliable MIME. Fetch must re-query the same persisted task, reject redirects and any origin not present in an explicit typed allowlist, stream into the caller sink with byte ceiling, and validate expected container/MIME before producing a receipt. The live allowlist cannot be guessed from Ark origin; it requires separately authorized real result-host evidence. URL strings never enter Manifest, Registry, logs, exceptions, repr, fixtures or provenance.

### 6.3 Dated Pricing Snapshot

| Model | Online list price, CNY / million tokens | Offline `flex` |
|---|---|---|
| 2.5 480p/720p | 70 without video input; 42 with video input | unsupported |
| 2.5 1080p | 77 without video input; 46 with video input | unsupported |
| 2.0 480p/720p | 46 without video input; 28 with video input | unsupported |
| 2.0 1080p | 51 without video input; 31 with video input | unsupported |
| 2.0 4k | 26 without video input; 16 with video input | unsupported |
| 2.0 fast | 37 without video input; 22 with video input | unsupported |
| 2.0 mini | 23 without video input; 14 with video input | unsupported |
| 1.5 pro | 16 with generated audio; 8 without generated audio | 8 / 4 |
| 1.0 pro | 15 | 7.5 |
| 1.0 pro fast | 4.2 | 2.1 |

Execution-day promotional discounts are transient evidence, not stable capability data: 2.5 1080p is 72% of list through 2026-09-17 14:00 UTC+8; 2.0 fast is 75% and mini is 40% through 2026-09-07 14:00 UTC+8. Profiles must retain list price and a separately dated promotion/account-price observation; they must not bake the promotion into model capability.

Only succeeded videos are billed. Official estimated token usage is `(input video duration + output video duration) × output width × output height × output fps / 1024`; actual billing uses returned `usage.completion_tokens`. 2.x/2.5 requests with video input also have model/resolution/ratio/duration-dependent minimum token usage.

Prices are evidence, not constants suitable for silent billing decisions. `SeedancePricingSnapshot` is dated, content-sealed and injected into the typed profile; it must provide a conservative per-model call upper bound for every included Model ID. Missing model coverage or an expired snapshot fails preview before durable intent and before network. The adapter does not derive a payable budget from public list price. A future live preview must inject an account-visible effective snapshot and conservative request upper bound, rather than assume public list or promotion eligibility.

## 7. Safety and Lifecycle Contracts

- resolve/capability/preview are pure and zero-network.
- Remote input upload/egress, account lookup and pricing refresh are separate explicit operations; none occurs during request construction.
- The committer issues the exact one-use Paid Provider permit only after durable intent. `submit()` validates and consumes it immediately adjacent to the single POST.
- POST is never automatically retried. Transport ambiguity becomes `outcome_unknown`, is durably persisted, and waits for explicit reconciliation.
- poll/fetch bind provider, model/endpoint, billable effect identity and the same task ID.
- Provider errors expose finite typed codes only. Secret, raw Authorization, raw body, account ID, signed URL and raw provider response are forbidden in state/log/error/repr/fixture surfaces.
- `httpx` transport is injected; default tests use fake transport and forbid external network/cost.
- No automatic provider/model selection, downgrade, retry, fallback or alias normalization.
- The previously exposed key is compromised and is not usable. Any future live test requires a rotated key supplied via process environment or secret store.

## 8. Provider-Neutral Core Extension

The pre-slice P8 core could not truthfully represent the complete matrix:

| Required Seedance contract | Current P8 contract | Result |
|---|---|---|
| `last_frame` image role | `VideoImageReferenceBinding.role` is only `first_frame|reference` | core change required |
| reference video/audio and audio-only | image bindings only | core change required |
| explicit reference/edit/extend modes | mode is only `text_to_video|image_to_video` | core change required |
| adaptive dimensions | `VideoOutputRequirement` requires positive exact width/height | core change required |
| provider-selected `duration=-1` and `frames` | positive integer `duration_seconds` only | core change required |
| 2.5 `mov` output/fetch | container literal is `mp4` | core and fetched-candidate validation change required |

These are provider-neutral capabilities, not fields that may be hidden in a Seedance profile without changing request semantics. The authorized extension added typed media bindings, generic modes, flexible timing/dimensions and container support in `video_contracts.py` plus compatibility-preserving integration in `video.py`. Legacy request and resolved hashes remain fixed by regression tests; Fake/H3/Hailuo behavior remains compatible. No Manifest/schema/activation/renderer change was required.

## 9. Acceptance Boundary

The provider-neutral scope gate was satisfied by explicit user authorization. Offline adapter acceptance still requires Harness mapping/receipt, Architecture Gate, native independent review and a task-only commit. No schema, CLI, renderer, activation, Registry/Project/Graph, or automatic fallback change is implied.

Offline implementation includes:

- exact seven-Model-ID allowlist and fail-closed retired/alias handling;
- strict dated capability/profile/raster/pricing identity;
- default-no-network fake transport tests for resolve/preview/submit/poll/fetch;
- one-use Paid Provider permit consumption immediately before the only POST;
- same-task polling/fetching, explicit result-origin allowlist, redirect/size/MIME/container checks and redacted representations/errors.

Offline blocker: final review/Harness/commit only. Live blockers remain rotated key, exact account Model/Endpoint access, current pricing snapshot, finite single-call budget, egress authorization and explicit one-submit authorization. No live call was made.
