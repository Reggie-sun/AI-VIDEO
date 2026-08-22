# AI-VIDEO P8 Seedance Cloud Provider Specification

Status: Dated compatibility matrix frozen and offline implementation accepted on 2026-08-19. A separately authorized Mini diagnostic reached provider `succeeded` and fetched an MP4 on 2026-08-19; the tracked audio-opt-out payload correction remains offline-verified and has not been re-submitted live. On 2026-08-20 the accepted adapter gained a sealed, human-observed Ark Console materialization receipt and exact local-asset resolver; no new Asset API or video submit was made. On 2026-08-22 the user authorized a bounded additive exception for project-owned fictional photorealistic identities with sealed generated/derived provenance and an exact task-scoped human claim; real、protected、ambiguous or unsealed identities remain forbidden from inline transport. Default verification remains fake-only/no-network. This document does not authorize another paid/live call, push or release.

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
- [Trusted asset library](https://www.volcengine.com/docs/82379/2315856?lang=zh)：真人授权、Ark Console materialization、`Asset ID`与`asset://<asset_id>`使用规则。
- [Advanced creation entitlement](https://www.volcengine.com/docs/82379/2377608?lang=zh)：基础权益的Console/API边界与Assets API订阅条件。
- [CreateAsset](https://www.volcengine.com/docs/82379/2318271?lang=zh)：Assets API的独立provider operation；本slice不猜测或调用该operation。

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
- Payload emission is value-sensitive: `generate_audio` is always emitted because it is part of the resolved output contract; `watermark=false`, `return_last_frame=false`, `service_tier=default`, `output_format=mp4` and `priority=0` are omitted. Non-default values remain explicit. This prevents optional defaults from changing Mini request acceptance while preserving an exact audio opt-out.
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

The production import surface is `SeedanceAssetMaterializationReceipt` plus `SeedanceAssetReferenceResolver`. It accepts only an Ark Console observation of an `Active` `asset-...` identity, binds it to the exact local asset ID/SHA-256/MIME/size, requires a human observer and exact confirmation-evidence SHA-256, and rejects ambiguous or mismatched mappings before permit consumption and before network. A local Registry ID can never be interpolated into `asset://`. This is a truthful import path for an already materialized Ark asset, not an uploader and not proof that a specific Alice asset currently exists.

### 5.1 Synthetic / Illustrated Image Input Lane

Status: offline runtime contract implemented on `2026-08-20` behind injected read-only evidence、Registry and Paid Provider gates. The additive image-only `reference_to_video` extension was implemented offline on `2026-08-22`; it has fake-transport/test evidence only. No uploader、remote materialization、Provider submit、activation or live proof was executed for this lane, and those actions remain separately authorized.

#### Official Transport Boundary

The current [Create video generation task](https://www.volcengine.com/docs/82379/1520757?lang=zh) field contract explicitly documents three values for `content.image_url.url`: a public image URL, inline `data:image/<format>;base64,<bytes>`, or a material URI `asset://<ASSET_ID>`. The same page includes `Seedance 2.0 mini` in the supported 2.0-family matrix, limits each image to less than 30 MB and the request body to 64 MB, and says not to use Base64 for large files. AI-VIDEO uses the current decimal-byte constants `SEEDANCE_MAX_IMAGE_BYTES = 30_000_000` with strict `<` eligibility and `SEEDANCE_MAX_REQUEST_BODY_BYTES = 64_000_000` with inclusive `<=` eligibility. The page also states that Seedance 2.5 / 2.0 do not directly accept reference images or videos containing a real human face, directing those cases to the platform's authorized/material solutions.

These are separate trust and egress surfaces, not interchangeable spellings:

| Surface | Officially evidenced use | Proposed AI-VIDEO rule |
|---|---|---|
| inline Base64 | Exact Create video field accepts a `data:image/...;base64,...` value | May carry only an eligible sealed project-owned fictional synthetic、illustrated or ordinary non-character local asset for `image_to_video` or image-only `reference_to_video`; bytes are encoded in memory from an exact Registry revision and are listed as image egress in preview. |
| stable public HTTPS URL | Exact Create video field accepts an image public URL | May carry only an eligible sealed asset through an approved, controlled, immutable origin receipt. The Provider adapter does not upload, mint, discover or silently replace the URL. |
| `asset://<ASSET_ID>` | Exact Create field supports preset material / virtual-person IDs; [Trusted asset library](https://www.volcengine.com/docs/82379/2315856?lang=zh) requires authorized real-person material to be enrolled and used by exact Asset ID | Remains the only accepted lane for real persons, protected identities and any face/identity case that is ambiguous under this proposal. |
| Files / Assets API | The Create video field does not document `file_id` or a general Files API. [CreateAsset](https://www.volcengine.com/docs/82379/2318271?lang=zh) is a separate AK-authenticated Assets operation that ingests a public URL and explicitly does not accept Base64 | Not an ordinary-image uploader and not part of this proposal. No guessed upload endpoint, AK credential, implicit enrollment or conversion from local Registry ID is allowed. |

The implementation selects inline Base64 and `image/png` only. It supports `image_to_video` first/last-frame image bindings and image-only `reference_to_video` reference bindings; synthetic inline video/audio media remain forbidden. The official Create surface supports additional image formats, but V1 deliberately reuses AI-VIDEO's exact PNG byte/geometry measurement seam instead of introducing a new decoder or trusting declared metadata. Although the official Create surface also accepts a public URL, AI-VIDEO currently has no approved publisher/materializer, immutable object-origin contract or retention proof for that path. HTTPS therefore remains a documented future transport gate, not a V1 fallback. A non-PNG、oversized or synthetic media-bearing request must stop; it must not silently transcode, upload, switch to URL or route through Assets API.

[Advanced creation entitlement](https://www.volcengine.com/docs/82379/2377608?lang=zh) describes Assets API/private material management as a separate enterprise entitlement/subscription, while [Model pricing](https://www.volcengine.com/docs/82379/1544106?lang=zh) prices video generation separately. Therefore this contract distinguishes: ordinary image transport (no official standalone per-image upload price is established by these sources), video-generation billing, and asset-library/API entitlement. None proves an account's current access, effective price or authorization.

#### Classification and Provenance Gate

Transport eligibility must be decided from sealed provenance plus a task-scoped human attestation. Agent/model visual inspection may raise risk but cannot establish that a depicted person is fictional, that an identity is unprotected, or that the caller holds rights.

| Required class | Ordinary Base64 / HTTPS lane | Required disposition |
|---|---:|---|
| `real_person_or_protected_identity` | forbidden | Resolve through the existing trusted `SeedanceAssetMaterializationReceipt -> SeedanceAssetReferenceResolver -> asset://...` path only when an authorized provider asset exists; otherwise stop. |
| `synthetic_photorealistic_person` | conditionally eligible | Requires the mode-specific sealed `permitted_use` claim: `project-owned-fictional-no-protected-identity:seedance-i2v` for `image_to_video`, or `project-owned-fictional-no-protected-identity:seedance-r2v` for `reference_to_video`; it also requires a task-scoped human attestor and a matching Registry record whose source is `generated` or `derived`, whose tool and creation receipt match the child receipt, and whose usage license is `project-owned-synthetic` or `provider-output`. A claim for one mode cannot authorize the other. A generator label、prompt or Agent visual conclusion alone cannot open this lane. |
| `clearly_illustrated_anime_non_real_character` | conditionally eligible | Requires explicit human attestation that the subject is non-real, the source/creator and rights are known, and no protected identity is intentionally reproduced. |
| `ordinary_non_character_image` | conditionally eligible | Requires explicit human attestation that no recognizable real person, protected identity or character is present and that source rights permit the egress/use. |

The immutable `SeedanceSyntheticImageReferenceReceipt` binds:

- exact local Asset Registry ID and selected revision, SHA-256, MIME, byte size, width and height;
- exact creator/source/tool identity and version, source record or generation-evidence digest, and a rights/permission statement;
- one of the four classes above, human attestor identity, task ID/scope, attestation timestamp and content digest;
- selected transport, Provider/model/mode and permitted use;
- for HTTPS only, canonical approved origin, non-secret object identity, remote-byte SHA-256, read-back evidence, retention-until and expiry semantics.

The immutable `SeedanceSyntheticImageEgressPolicyReceipt`, owned by the same `seedance_asset.py` boundary, aggregates one request's children. It binds the canonical ordered tuple of every `(role, asset_id, child_receipt_content_hash)` to the exact prompt/image preview identity, task scope, Provider/model/mode, selected transport, destination and retention. `image_to_video` permits only `first_frame` / `last_frame` children; `reference_to_video` permits only `reference` children. Missing、extra、duplicate、reordered、cross-mode role or role/asset-mismatched children invalidate the aggregate. Its content hash changes when any child evidence, role, order, prompt/preview identity or egress setting changes.

For `synthetic_photorealistic_person`, `permitted_use` is a typed-by-validation canonical claim rather than free-form prose. Its exact value, the human `attested_by` identity and the task scope are sealed into the child content hash; the child hash is then sealed into the aggregate egress-policy receipt and Paid Provider authorization fingerprint. The resolver additionally compares the selected Registry `source_kind`、`tool`、`creation_receipt_id` and `usage_license` to the receipt before it may construct inline bytes. The injected evidence source must also return the exact underlying generation/extraction receipt bytes by that `creation_receipt_id`; both the authorizer and resolver independently require their SHA-256 to match the child's sealed `source_evidence_sha256`. This additive exception does not change the trusted `asset://` owner or permit arbitrary portrait input.

Missing provenance, conflicting evidence, an unknown source, suspected real-person likeness without the exact fictional-identity claim, an intentionally reproduced protected identity, or classification uncertainty makes the synthetic lane ineligible. The caller must either provide a separately authorized trusted-material receipt or stop; there is no automatic downgrade from HTTPS/Base64 to `asset://`, no inference from filename/prompt/style metadata, and no classification based solely on Agent vision.

#### Input Identity and Cloud Egress

- Base64 is constructed only after re-reading the selected Registry PNG bytes and independently measuring and matching the sealed SHA-256/size/`image/png` MIME/geometry. The raw Base64 value is never persisted in Manifest, Registry, receipt, logs, errors, fixtures or repr; its bytes still count as explicit cloud egress and toward the 64 MB request-body ceiling.
- HTTPS requires a pre-existing approved publisher/materializer receipt and separately authorized typed network preflight that prove read-back bytes equal the exact local bytes. Allowed origins are explicit and typed; the object must remain immutable and reachable through at least the selected sealed capability/profile execution-expiry window. Anonymous third-party temporary hosts, redirects, mutable object keys, unknown retention, unsealed uploads and automatic host fallback are forbidden. The preflight must not hide network I/O inside model validation.
- Raw signed URLs, query credentials and bearer material are never persisted. V1 does not accept a signed-URL-only origin; adding such a mechanism would require a separate secret/expiry contract and approval.
- The existing `PaidProviderCallPreview.egress_items` continues to name prompt egress and every image's exact asset ID, SHA-256, MIME and byte size. That is necessary but does not alone bind the separate classification/provenance/attestation receipt. `VideoGenerationRequest.input_artifact_ids` must not carry a bare receipt fingerprint: those IDs are canonical dependency-graph inputs and later Asset Records require them to identify real graph-addressable artifacts.
- `SeedanceSyntheticImageEgressPolicyReceipt` is the single sealed task egress-policy evidence for the request. Its exact safe content-addressed ID is `seedance-synthetic-egress:<content_hash>` with the lowercase 64-hex receipt hash; each child is retained under `seedance-synthetic-image:<content_hash>`. The caller injects a read-only source that returns exact canonical bytes for those IDs and, for a photorealistic fictional child, exact source-receipt bytes under the child's `source_record_id`. `SeedanceSyntheticImageAuthorizer` and `SeedanceSyntheticImageReferenceResolver` independently reopen、parse、hash and compare the aggregate plus every ordered child; they also independently hash the photorealistic child's source-receipt bytes against `source_evidence_sha256`. Missing、non-canonical or mismatched evidence fails closed. The source's durable storage remains caller-owned and read-only to AI-VIDEO; this slice adds no Registry/Manifest writer or artifact layout.
- The resolver also reopens injected canonical `AssetRegistrySnapshot` bytes, verifies their semantic revision and exact file SHA-256 against `ResolvedVideoGenerationRequest.activation_scope.request.base_registry`, and requires one exact image `AssetRecord` matching every receipt、binding and locally measured PNG. A photorealistic fictional exception additionally requires a `generated|derived` record, exact tool/creation-receipt equality and an accepted `project-owned-synthetic|provider-output` usage license.
- The durable `PaidProviderGateReceipt` persists the full authorization and the operation-permit projection now binds `authorization_fingerprint` through minting、video projection、validate/consume/consumed checks and durability reopen comparison. Because the fingerprint seals `egress_policy_receipt_id`, the authorization supplied to `SeedanceVideoProvider.submit()` must be the exact authorization stored in the durable Gate. Gate `A1/R1` with submit `A2/R2` for the same preview leaves the permit unconsumed and performs zero POST. This is a bounded internal permit-safety change, not a persisted Manifest/Gate schema or layout change.
- `SeedanceSyntheticImageReferenceResolver` is the single owner for validating the request-side receipt/Registry/bytes identity and producing the in-memory `image_url` payload item. It neither uploads nor writes Registry/Manifest state and cannot select a Provider or transport. The existing trusted receipt/resolver remain unchanged and authoritative for their lane.
- The resolver validates each image's exact bytes and strict `size_bytes < 30_000_000` ceiling. The adapter owns aggregate size: after constructing the final compact JSON body, and before permit consumption, it must reject `len(body) > 64_000_000`. No resolver may infer aggregate safety from individual image sizes.

#### Failure and Recovery Semantics

The following are semantic labels for typed `AiVideoError` behavior to be mapped to approved `ErrorCode` values during implementation; they are not claims that these runtime enums already exist:

| Condition | Fail-closed behavior |
|---|---|
| classification/provenance ambiguity | Reject before egress, durable intent and permit consumption; require trusted materialization or corrected human evidence. |
| HTTPS unreachable/expired/redirected | Reject that exact reference before Provider POST; do not switch host, inline bytes, upload, fallback or consume the submit permit. |
| local/remote bytes, MIME, size or geometry mismatch | Integrity failure; invalidate the synthetic receipt and require explicit re-materialization/re-attestation. |
| Provider rejects a known submitted task/input | Persist the exact known failure against the consumed permit/task identity; do not retry with another transport/model or remint a permit automatically. |
| POST outcome unknown | Preserve existing `outcome_unknown` behavior: no blind retry, transport fallback, new upload or permit remint; reconcile the exact durable intent explicitly. |

All validation and payload construction complete before submit. The one-use permit is still validated and consumed immediately adjacent to the sole Provider POST. The additive lane creates no second writer or mutable lifecycle and changes no persisted Manifest/Gate schema or layout, CLI, timeline, renderer, activation owner or Provider selector. Missing injected canonical receipt or Registry evidence keeps the synthetic lane unavailable and fails closed.

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
- Ark asset import/resolve is local and zero-network; Ark Console enrollment remains an external human action. Basic rights do not imply Assets API automation, and this slice adds no AK/SK credential or guessed upload endpoint.
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

Offline blocker: final review/Harness/commit only for the post-live payload correction. The authorized Mini diagnostic used the exact Model ID, one POST and the existing durable gate, reached `succeeded`, and fetched a 1,278,577-byte H.264 MP4 with SHA-256 `b6ea0864d3b400cf1648868a816eedc1c24f42c2bc605a60335b9f982ea91c67`. Its minimal diagnostic payload omitted `generate_audio`, so Ark produced an AAC stream despite the requested `native_audio=false`; it proves cloud submit/poll/fetch connectivity, not acceptance of the tracked audio-opt-out payload or final activation. The reservation remains unsettled pending exact provider billing evidence. Any new live submit still requires a fresh rotated credential, exact access, current pricing snapshot, finite one-call budget, egress authorization and explicit one-submit authorization.
