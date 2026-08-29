# Seedance 2.0 Mini R2V Usage And Ark Asset Flow

Date: 2026-08-29

Status: `advisory_research`

Scope: Seedance 2.0 / Seedance 2.0 Mini 的 reference-video、video extension、输入传输，以及两个连续 15 秒生成段的实际接法。本文不授权 Provider 调用，也不证明当前账号 entitlement、价格、质量或生产链已就绪。

## Executive Answer

可以用 `R2V`，而且如果目标是让第二个 15 秒生成段紧接第一个生成段，`video extension` 比“只取尾帧再做 I2V”更贴近用户意图。

先前“必须把 Shot 1 上传到 Ark Console 并获得 `Active asset-...` 才能 R2V”的说法过于绝对。当前官方资料支持两类 reference-video 输入：

1. Provider 可在任务执行期间直接访问的公开 `http(s)` URL；
2. 已启用素材库后的 `asset://<ASSET_ID>`。

官方资料没有把 `asset://` 写成普通非真人 reference video 的唯一输入方式。它还明确把 Base64 仅列为 image/audio 的输入方式，因此原始 Ark/ModelArk API 不能读取本机路径，也不应假设 `data:video/...;base64,...` 可用。[BytePlus LAS official operator documentation](https://docs.byteplus.com/en/docs/byteplus_las/video_gen_enhanced)

调查开始时，AI-VIDEO repository 确实只允许 `asset://` + sealed `Active` receipt；这是本仓库当时的 fail-closed Production contract，不是 Seedance 2.0 Mini 的模型能力限制，也不是 Ark API 的普遍硬要求。本文末尾记录了本轮据此实施的provider-output垂直切片。

对新增候选方案的独立判断是：方向正确，但必须把短期 transport 与 durable identity 分开。Seedance 产出的 Shot 应保留 Provider task/model provenance，并在 URL 有效期内优先直接用于下一 Shot 的 R2V；`video_url` 本身只有 24 小时有效，不能作为 durable identity 或长期 Manifest truth。Durable identity 应由 exact fetched bytes、SHA-256、size/MIME、Provider task binding 与 fetch/materialization receipt 组成。Local H3/T8 输出若要进入 Ark R2V，可经受控 object storage 自动上传并生成机器可验 receipt；这比普通非真人素材也强制人工 Ark Console confirmation 更符合官方 API 形态，但属于尚未实现、需要 canonical owner 与 egress/security gate 的 repository architecture change。

| Question | Evidence-backed answer |
| --- | --- |
| Seedance 2.0 Mini 能否吃 reference video？ | 能。官方矩阵把 Mini 的 Video reference、Edit video、Extend video 都标为支持。 |
| Wire request 怎么传？ | `content[].type="video_url"`、`video_url.url=<public URL or asset://...>`、`role="reference_video"`。 |
| R2V、edit、extend 是三个不同上传协议吗？ | 不是。官方 prompt guide 将它们区分为不同 task intent；wire 层仍使用 `reference_video`，由 prompt 指明“参考”“严格编辑”或“延长”。 |
| 本机 `shot-1.mp4` 能否直接放进 JSON？ | 不能放本地路径。官方 raw API 的视频输入是公开 URL 或 Asset ID；官方文档未给 video Base64。 |
| 是否必须走 Ark Console asset？ | 不必须。公开 URL 是官方支持路径；`asset://` 是另一条素材库路径，真人素材另有合规限制。 |
| Shot 1 的 Provider output URL 能否直接给 Shot 2？ | 官方文档组合起来支持这一做法：output 是 24 小时预签名 URL，而临时公开 URL可作输入，只要任务期间有效。这是基于两条官方契约的推论，本文未做 live submit 验证。 |
| 两段 15 秒如何最贴近“连续、流畅”？ | Shot 2 使用 Shot 1 整段作为 `reference_video`，prompt 明确要求延长其结尾；这比 generic R2V 更准确，也比单尾帧 I2V 保留更多运动、运镜与音频上下文。 |
| `video_url` 是不是 Shot 1 的 durable remote identity？ | 不是。它是 24 小时预签名 locator；Provider task ID 当前保留 7 天，exact local bytes/receipt 才能形成更稳定的项目 identity。 |
| Ark `Active asset` + human confirmation 是不是官方普通 R2V 硬限制？ | 不是。`asset://` 是官方可选输入路径；human-observed `Active` receipt 是当前 AI-VIDEO 的本地证据 contract。真人可信素材另有官方授权/入库要求。 |

## What R2V Means On Official Surfaces

`R2V` 是常用简称，但官方 Seedance 2.0 prompt guide 使用更细的分类。官方把 reference-based generation 分成三类：[Dreamina Seedance 2.0 series prompt guide](https://docs.byteplus.com/api/docs/ModelArk/2222480)

- `multimodal reference`：从视频抽取动作、运镜、风格、音效等维度，生成新的内容；prompt 应写“参考视频 1 的某个维度”。
- `video editing`：基于原视频做局部或全局修改，未提及部分默认尽量保持；prompt 应写“严格编辑视频 1”。
- `video extension`：沿时间轴续接原视频，保持视听风格、主体和叙事连续；prompt 应直接写“延长视频 1”。

官方特别警告：edit/extend 任务中不要写“参考视频 1”，否则可能被识别成 generic reference task。也就是说，`R2V` 在 transport 上是 reference video 输入，在 authoring 上还必须区分“借动作/风格”“改原片”“从边界继续”。

### I2V Versus R2V Extension

| Mode | Input retained | Best use | Limitation for this task |
| --- | --- | --- | --- |
| I2V first frame | 一张精确起始图 | 锁定 Shot 2 的开场构图；官方 `return_last_frame=true` 也专门支持尾帧串接 | 不包含 Shot 1 的速度、动作趋势、镜头惯性、节奏和音频状态 |
| Generic R2V | 整段视频可作为动作、运镜、风格或声音 donor | 迁移动作、镜头语言、质感 | 如果 prompt 只写“参考”，模型可能生成相似新片而不是续拍 |
| R2V video extension | 原视频的时序上下文 + 明确续接 intent | 同一场景、动作或摄影运动从结尾继续 | 仍是模型质量问题；不能保证边界像素完全相同，需逐帧/音频验收 |

官方把 `return_last_frame=true` 描述为可把上一条视频尾帧用于连续视频生成；这证明 I2V chaining 是一条合法、轻量的路径，但不等于它在运动连续性上总优于 full-video extension。[Volcengine official API Explorer](https://api.volcengine.com/api-explorer/?action=CreateContentsGenerationsTasks&groupName=%E8%A7%86%E9%A2%91%E7%94%9F%E6%88%90API&serviceCode=ark&version=2024-01-01)

## Official Request Form

Volcengine 官方 API Explorer 的 current example 使用公开 MP4 URL，并以 `role="reference_video"` 提交；BytePlus 官方文档展示相同的 `content[]` 结构。[Volcengine official API documentation view](https://api.volcengine.com/api-docs/view?action=CreateContentsGenerationsTasks&serviceCode=ark&version=2024-01-01) [BytePlus official operator documentation](https://docs.byteplus.com/en/docs/byteplus_las/video_gen_enhanced)

一个最小化的 Shot 2 request shape 是：

```json
{
  "model": "<current Seedance 2.0 Mini model ID or endpoint for this surface>",
  "content": [
    {
      "type": "text",
      "text": "延长视频1的结尾，紧接最后一帧和现有运动方向，继续生成新的15秒；保持主体、场景空间、镜头轴线、光线、色调、运动速度与声音环境连续，不要重放视频1。"
    },
    {
      "type": "video_url",
      "video_url": {
        "url": "https://<provider-or-object-storage>/shot-1.mp4?<temporary-signature>"
      },
      "role": "reference_video"
    }
  ],
  "resolution": "720p",
  "ratio": "adaptive",
  "duration": 15,
  "generate_audio": true,
  "watermark": false
}
```

注意：

- BytePlus LAS 当前列出的 Mini ID 是 `dreamina-seedance-2-0-mini-260615`；Volcengine、BytePlus ModelArk 和 LAS 的 model ID/endpoint namespace 不应互相猜测，实际调用前必须在所用 surface 重新解析。
- Mini 官方输出范围为 4–15 秒、480p/720p、24 fps；单个 Seedance 2.0 reference video 允许 2–15 秒，最多 3 段，总 reference-video duration 不超过 15 秒。因此“15 秒 Shot 1 -> 15 秒 Shot 2”正好落在 reference input ceiling 上。[BytePlus LAS official model and input matrix](https://docs.byteplus.com/en/docs/byteplus_las/video_gen_enhanced)
- 官方 `ratio=adaptive` 会在 edit/extend intent 下优先按输入视频选择接近的比例。
- 文档没有承诺 output 边界零重叠或像素级无缝。最终拼接前仍需检查 Shot 2 开头是否重演 Shot 1 尾部、是否出现动作跳变、音量突变或环境声相位断裂。

## Input Transport: URL, Asset, And Local Bytes

### Public URL

官方允许可公开访问的 `http(s)` URL；不能依赖登录态或额外 auth header，临时 URL 必须在任务执行期间保持有效。对本任务最直接的做法是：

1. Shot 1 成功后立即查询任务；
2. 保存 exact MP4 bytes，同时保留 Provider 返回的短期 `video_url`；
3. 在该 URL 仍有效时，将它放入 Shot 2 的 `reference_video`。

官方同页说明生成结果是 24 小时有效的预签名 `video_url`。因此把这个 URL 立即用于下一任务，不需要先通过 Console 物化为 Asset；这是从“output URL contract”与“temporary public input URL contract”推导出的可行路径，而不是本文实际付费调用后的 live proof。[BytePlus LAS output contract](https://docs.byteplus.com/en/docs/byteplus_las/video_gen_enhanced)

这个 URL 不能被持久化为长期 production truth。官方 query task 的 ID 当前只保留 7 天，output URL 则为 24 小时；二者都是 Provider lifecycle identity/locator，不等于 exact media identity。Production record 应持久化 task/model binding、URL 的 expiry/host 等非敏感 transport metadata、下载 receipt 与 exact MP4 SHA-256，而不保存可重放的完整 signed query string。需要紧邻 Shot 2 时，可在受控 transient execution context 消费该 URL；需要跨窗口或长期复用时，应把 exact bytes materialize 到 project-controlled storage 或 Ark Asset，并重新形成可验证 locator receipt。

### Asset ID

`asset://<ASSET_ID>` 也是官方支持输入，但属于启用了素材库后的路径。它适合长期复用、私域素材管理以及有真人肖像合规要求的输入。官方真人素材说明要求先入 trusted asset library 并使用 Asset ID；这不能反推所有普通 reference video 都必须先变成 Asset。[Volcengine trusted real-person asset guide](https://www.volcengine.com/docs/82379/2315856?lang=zh)

### Local MP4 And Data URL

raw API 无法读取 `/local/path/shot-1.mp4`。BytePlus 官方输入说明把 Base64 写成 image/audio 支持项，没有列 video；一方 BytePlus-SA implementation 也将 video reference 定义为 URL-only。因此：

- 不能把 local path 当作 `video_url.url`；
- 不应把 `data:video/mp4;base64,...` 当作已获官方支持；
- 可以由 wrapper 先把本机 MP4 上传到对象存储，再把预签名 HTTPS GET URL 交给 Seedance。

## How Existing Implementations Use It

### Volcengine Ark CLI

Volcengine 自己的 `ark-cli` Skill 对用户暴露了本地文件形式：

```bash
arkcli +gen \
  --model <current-versioned-seedance-model-or-endpoint> \
  --input ref:@reference.mp4 \
  "保持参考视频的运动轨迹，替换主角为机器人"
```

该一方 interface 证明“用户侧可以从 local MP4 发起 R2V”；但公开 Skill 没有说明 CLI 最终是上传、预签名还是使用其他中间 transport，所以不能据此宣称 raw Ark API 接受 local path 或 video Base64。[Volcengine ark-cli pinned Skill](https://github.com/volcengine/ark-cli/blob/a048ff8096a577e79e2dce9f9e00472b93bacc6f/skills/arkcli-gen/references/arkcli-gen.md)

### BytePlus-SA ModelArk MCP

BytePlus-SA 的一方开源 MCP 把边界做得很明确：`seedance_create_task` 的 video 是 URL-only；如果输入是 Base64 或本地文件，先调用 `media_upload` 上传到 TOS/S3，拿到 presigned HTTPS GET URL，再作为 `reference_video` 提交。[BytePlus-SA modelark-mcp pinned README](https://github.com/byteplus-sa/modelark-mcp/blob/f0339d50d3d29d8fd90b701ccf24f220a25c4073/README.md#supported-input-modalities) [pinned API reference](https://github.com/byteplus-sa/modelark-mcp/blob/f0339d50d3d29d8fd90b701ccf24f220a25c4073/docs/api-reference.md#5-seedance_create_task)

这是最清楚、也最适合 production borrowing 的公开 pattern：local bytes 不伪装成 Provider asset，而是显式 materialize 到 object storage，生成有时效的 read URL。

### Community Workbench

一个可审计的社区实现会直接拒绝 `data:video/...`，把粘贴的本地视频先上传到临时公共 host，然后把返回的 URL 作为 `reference_video` 发送。其 source 中的 exact payload 为 `{"type":"video_url","video_url":{"url":videoUrl},"role":"reference_video"}`。[seedance_console pinned source](https://github.com/doldol22312/seedance_console/blob/8fd14a069db16d7cb1309b09d606bec0b7259633/server/index.js#L462-L500) [upload implementation](https://github.com/doldol22312/seedance_console/blob/8fd14a069db16d7cb1309b09d606bec0b7259633/server/index.js#L1103-L1129)

这个实现说明公开 URL 路线在真实工具中很常见，但它使用第三方临时 host，不适合私密、版权敏感或需要 durable provenance 的 production media。AI-VIDEO 若引入类似能力，应使用受控 TOS/object storage 与 exact-byte receipt，而不是复制这个具体 host。

## Repository Contract At Investigation Start

当前 repository 的行为必须与外部 API capability 分开陈述：

- [`SeedanceAssetMaterializationReceipt`](../../src/ai_video/production/seedance_asset.py) 要求 `source_surface="ark_console"`、human actor、`observed_status="Active"`，并把 local asset SHA/MIME/size 与 provider confirmation bytes 封入 receipt。
- `SeedanceAssetReferenceResolver` 只从上述 receipt 返回 `asset://<provider_asset_id>`。
- [`SeedanceVideoProvider`](../../src/ai_video/production/seedance.py) 的 `_asset_reference()` 只接受 `_SAFE_ASSET_REFERENCE`，因此 public HTTPS reference video 会在 Provider POST 前被本地拒绝。
- [`seedance_capabilities.py`](../../src/ai_video/production/seedance_capabilities.py) 已声明 `doubao-seedance-2-0-mini-260615` 支持 `REFERENCE_TO_VIDEO`、`VIDEO_EDIT`、`VIDEO_EXTEND`，以及最多 3 个、总长 15 秒的 reference videos。

所以当前真实 blocker 是：

> model/capability 已支持 R2V；repository 的 canonical input-reference resolver 尚未允许 exact provider output URL 或 object-storage URL。

这项 restriction 有真实安全价值：它避免把 local Registry ID 伪装成 Ark Asset、避免 URL drift/expiry/SSRF/未绑定 exact bytes。但它不应被描述成 Ark 平台要求。若继续走现有 production seam，只能使用 `Active asset` receipt；若要复用 Shot 1 的短期 output URL，需要另行批准并实现一条受控 URL materialization contract，而不是绕过 adapter 直接 POST。

## Candidate Continuity Transport Assessment

### Seedance Output To Next-Shot R2V

候选方案“Seedance 生成的 Shot 保留 Provider remote identity/video URL，直接给下一 Shot R2V”应接受，但 contract 应写成：

- durable：Provider task ID、request/model binding、exact fetched MP4 SHA-256、size、MIME/container、fetch receipt；
- transient：Provider `video_url`、expiry、expected origin、一次性/限时 R2V consumption context；
- pre-submit：重新验证 URL origin/expiry，必要时用 bounded GET 验证 exact bytes，确保与已记录 SHA-256 一致；
- post-submit：URL 不升级为 activated asset，也不作为长期 replay source；unknown outcome 仍 fail closed。

这条路径能消除“刚由 Seedance 产出的 Shot 还要人工下载再上传 Console”的无意义往返，同时保留 exact-byte provenance。它仍不能仅凭 URL 字符串宣称 input identity；预签名 URL 可过期、轮换或泄漏 capability。

### Local H3/T8 To Seedance R2V

候选方案“local H3/T8 输出自动上传 object storage，并生成 machine-verifiable materialization proof”技术上合理，也有一方 prior art：BytePlus-SA `modelark-mcp` 的 `media_upload` 接受 local file/Base64，上传 TOS/S3 后返回 presigned HTTPS GET URL。[BytePlus-SA media upload contract](https://github.com/byteplus-sa/modelark-mcp/blob/f0339d50d3d29d8fd90b701ccf24f220a25c4073/docs/api-reference.md#10-media_upload)

AI-VIDEO 若实现，最小 receipt 至少应绑定：

- source local asset ID、SHA-256、size、MIME/container；
- storage provider、bucket/account scope、object key/version、upload response identity/ETag（不能单独把 ETag 当 content hash）；
- presigned URL 的 expected origin、expiry 与生成 actor/tool；
- bounded provider-fetch preflight 或 exact downloaded bytes verification；
- cloud-egress decision、credential reference 与一次性 submit intent。

“自动上传”只能表示在用户已批准的 task scope 和既有 egress/budget/secret gates 内由 canonical materializer 自动执行；它不能成为默认隐式 cloud egress，也不能把第三方匿名临时 host 引入 production。该设计对普通非真人素材可以替代 AI-VIDEO 当前的 manual Console-only lane；真人 reference 仍受官方 trusted asset authorization/asset-library policy 约束。

### Continuity Mode Selection Contract

候选方案“continuity contract 选择 last-frame I2V 或 reference-video R2V”应接受，并应避免把 I2V 写成固定 fallback：

| Continuity intent | Select | Why |
| --- | --- | --- |
| 精确锁定下一段第一帧；前一段动作已结束或允许重新起势 | last-frame I2V | 起始构图最强，input 最小，官方 `return_last_frame` 就是为串接提供的机制 |
| 同一动作、运镜、表演、环境声从 Shot 1 结尾持续 | reference-video R2V + extension prompt | 保留完整 temporal context；本任务默认应走这一分支 |
| 借用 Shot 1 的镜头语言/节奏，但生成不同事件或主体 | generic reference-video R2V | 明确只 transfer 指定维度，避免被误判为 extension |
| 对 Shot 1 做局部替换、风格化或修补 | video edit | Prompt 使用“严格编辑视频 1”，未提及部分保持 |
| Provider/account/transport 无法得到可验证 video reference | `NOT_EVALUATED` / stop | 不静默降级到 I2V；只有 accepted continuity policy 明确允许时才选择 I2V |

官方把 first/last-frame generation、multimodal reference、edit 和 extend 作为不同 intent；因此 contract 应先由 Shot continuity requirement 选 mode，再解析所需 transport，不能因当前 materializer 只会做图片就把所有 continuity 自动改成 I2V。

## Practical Recommendation For Two Connected 15s Segments

对于“电影感、恢宏、两个生成段连成同一段连续动作”的目标：

1. Shot 1 生成 15 秒，并请求 `return_last_frame=true` 作为 fallback evidence；不要把尾帧 fallback 误当作唯一 continuity path。
2. Shot 1 落盘后，先完成 repository 要求的 exact-byte per-Shot analysis Gate。Gate 通过前不得提交 Shot 2。
3. Shot 2 首选 full-video `reference_video` + `video extension` prompt，不使用泛泛的“参考视频 1”。
4. Prompt 明确冻结主体、服装、空间、镜头轴线、光位、色调、运动趋势与声音环境，并说明“从视频 1 结尾继续，不重放”。
5. Shot 2 落盘后重新做 exact-byte Gate；再检查拼接边界的 decoded frames、运动方向、音频波形/响度与叙事推进。必要的 trim/crossfade 是 post-production 决策，不能提前声称模型天然无缝。

如果目标其实是“有明确剪辑点的两个电影 Shot”，则不必追求同一长镜头的像素连续：可以设计一个有动机的 whip pan、遮挡、闪光、尘雾或声画桥作为 Shot 1 尾部和 Shot 2 开头的共同 transition。R2V 仍用于继承摄影和表演状态，但 acceptance 应看 cut motivation 与 continuity，而不是只看首尾帧相似度。

## Remaining Verification Boundary

本文没有执行任何 paid Provider call、媒体上传或生成，因此以下仍未验证：

- 当前账号/region 对 Mini 的 exact Model ID、entitlement 和可用 transport；
- Shot 1 provider-hosted 24h URL 在同一账号下作为 Shot 2 input 的 live fetch 成功率；
- Mini 对 15 秒 full-video extension 的实际边界重叠、主体一致性、镜头惯性和音频连续性；
- 当前 AI-VIDEO 是否应扩展 canonical resolver 支持 signed HTTPS references。

这些是 execution/architecture 后续问题，不影响本研究的核心结论：`R2V` 本身可用，`Active asset` 不是官方普通 reference-video 的唯一通路；它只是调查开始时repository唯一已实现且获约束的通路。

## Implemented Vertical Slice

本轮调查后获准先实现Seedance provider-output垂直切片。Current runtime现已把Seedance exact fetch产生的task/model、opaque provider file identity、remote origin、完整locator的SHA-256以及exact MP4 SHA-256/bytes/MIME封入`RemoteMediaMaterializationReceipt`；完整signed URL仍不进入durable receipt、Manifest、repr或log。Canonical `VideoGenerationService.refresh_remote_reference_lease_once()`先验证source attempt仍对应Manifest current active pointers，再重开submit/status/fetch evidence并签发process-local one-use refresh permit；Seedance helper只有消费该permit后才能在同一task重新查询到同一locator，并再次完整GET验证exact bytes不变，才签发最长5分钟的in-memory `SeedanceRemoteReferenceLease`。`SeedanceRemoteReferenceResolver`再把exact matching video binding投影为`reference_video` HTTPS输入，并在每次resolve时重新验证source仍是current active。stale source、另行mint、lease过期、locator轮换或bytes变化都会在新POST前fail closed，不会退化到I2V。

旧的`SeedanceAssetMaterializationReceipt -> SeedanceAssetReferenceResolver -> asset://`没有删除，继续作为already-materialized Ark/trusted asset lane。Local H3/T8 object-storage upload、presign refresh、rotated locator re-verification与paid live chaining仍未实现或验证。
