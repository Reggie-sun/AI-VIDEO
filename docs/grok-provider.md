# Grok Media Provider

Date: 2026-10-12

## Status

实现包含 SuperGrok OAuth、只读订阅 usage、image/video adapter，以及现有 Production 的连接。
默认 live generation 为 `BLOCKED`。显式注入 `GrokIncludedOnlyAuthority` 才能核验统一订阅池的
included-only 边界：每次重开固定 credits 与 auto-topup GET，要求 finite current quota、零
on-demand cap / used / prepaid balance，以及官方 schema 的 disabled/no-rule。失败立即停止。
余额、usage percentage、OAuth 登录或客户端次数限制单独不构成该证明。模型资格、creative
preflight、预算、egress、durable intent / one-use permit 仍独立执行；无 Console key fallback、
配置 mutation、自动充值或重发。
来源：[xAI announcement](https://x.ai/news/grok-openclaw)、
[OpenClaw xAI integration](https://docs.openclaw.ai/providers/xai)、
[Grok FAQ](https://docs.x.ai/grok/faq)。

## Authentication

从 repository root 使用现有 Python 环境与 `PYTHONPATH=src:.`：

```bash
python scripts/grok_auth.py login
python scripts/grok_auth.py status
python scripts/grok_auth.py quota
python scripts/grok_auth.py refresh
```

`login` 显示官方 verification URI 与 user code，由用户在官方页面授权。采用 OpenClaw 公开共享
client，项目没有独立注册 client。[当前官方 discovery](https://auth.x.ai/.well-known/openid-configuration)
提供 `/oauth2/device/code`、`/oauth2/token`、`/oauth2/userinfo`；账号资格仍需实际登录验证。
需要已有 `secret-tool` 与 unlocked OS Secret Service；token 仅保存到 exact
`application ai-video / provider grok / credential GROK_OAUTH` item。无文件、`.env`、Cookie 或其他账号 fallback。
`status` 只输出 public account fingerprint、expiry 和状态；`quota` 只做一次固定 billing GET，
输出 usage 和 `generation_state=blocked` 并返回 exit 1，不启用生成。
`refresh` 显式调用，POST 前保存 `refresh_unknown`；丢失响应或保存失败停止，不自动刷新/重试。
这类未知认证状态需重新官方登录恢复。
`login` / `refresh` 对同一 item 使用 Linux 跨进程互斥；另一个 `login` / `refresh` 在凭据读取和 HTTP 前返回 busy。
空的 coordination lock 位于当前 UID 的 private runtime directory，不包含 token，关闭 FD 释放；
缺失或不安全的 runtime directory / lock 直接停止，不切换 credential source。

当前官方 device page 可为 exact `https://accounts.x.ai/oauth2/device`；仅当响应的 complete URI
严格等于可信 base 加本次 public `user_code` 时展示完整链接。其他 complete URI 不展示，
device code 不泄漏；token/device/userinfo 的固定 `auth.x.ai` endpoint authority 保持。

`GrokIncludedOnlyAuthority.observe(model_id=..., operation_path=...)` 返回五分钟内到期、精确
绑定 account/model/operation/period 的 public binding。将同一 authority 注入 selected adapter
的 `subscription_guard`，durable permit 前与 transport 前重开服务端状态；任何 enabled、
nonzero、quota 耗尽、unknown schema、redirect、陈旧/跨账号证据均拒绝。`quota` 仍只观察 usage，
不启用生成。实现依据 xAI [billing schema](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-shell/src/extensions/billing.rs)、
[PAYG handling](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-pager/src/app/dispatch/billing.rs)
与 [known disabled rule](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-pager/src/views/credit_bar.rs)。

## Video Contract

`GrokVideoProvider` 实现原 `VideoProvider` protocol，注入 `VideoProviderRegistry`；选择/编译仍归
Planner/Router/compiler，执行归 `VideoGenerationService` / `ProductionStateCommitter`。
origin 固定 `https://cli-chat-proxy.grok.com`。
模型须在任务 candidate limits 中明确选择；多个模型出现选择平局时不猜默认值。

| Model | Generation | Native Controls | Output Limits |
| --- | --- | --- | --- |
| `grok-imagine-video-1.5` | T2V / I2V / R2V | first/last、14 refs、4 interior keyframes、3 preset voices | 1–15s；普通 T2V/I2V 可请求480p/720p/native1080p；reference controls ≤720p |
| `grok-imagine-video-1.5-lite` | T2V / I2V | first image、native audio | 1–15s、480p/720p/1080p；1080p 是720p upscale |
| `grok-imagine-video` | T2V / I2V / R2V / edit / extend | first image、7 refs、source video | generation ≤15s；R2V ≤10s；≤720p |

Full 支持 last-only R2V、first + refs、first/last + refs；纯 I2V 继承首图比例。
T2V/R2V 可显式请求 `1:1,16:9,9:16,4:3,3:4,3:2,2:3,21:9,5:2`；
`adaptive` raster 的宽高保持未知，命名比例独立封存并在实际 probe 中核验。
既有 exact raster 按封存宽高核验，保留其原 Provider 允许的 rounded geometry。
FPS 保持 `None`，不宣称 frame-count；seed/negative/native camera/motion-tail 不支持。
内容驱动目标使用 nominal duration；static C4 专用 exact_seconds，严格核验输出毫秒。
图表、End Card、controlled product Hero 使用原合成路径；角色/生活场景/产品交互、Hybrid 的
generated-video layer、static multi-anchor 与 exact source hero repair 可选 Grok。
产品交互保留已审核 source、产品血缘与完整意图；native prose 表达包装/标识/文字保护要求。

`GrokProviderProfile.keyframes` 是有序 `GrokTimedKeyframe(asset_id,asset_sha256,timestamp_ticks)`，
每秒3 tick，≤4项，严格位于 duration 内且不得同 tick。asset 必须已作为 exact request
`reference` image 绑定；wire 移至 `keyframes`，不再重复进入 `reference_images`。
同一 exact image 可重复用于首尾或多个时间位置；同 asset ID 的 hash/metadata 必须一致，
egress 按唯一 bytes 验证、wire 保留各位置，不能用重复 ID 偷换素材。
`reference_voices=("eve","leo","rex")` 等 ≤3 preset ID 顺序封存为 `<AUDIO_0..2>`。
approved intent/prompt 需按实际顺序表达 `<IMAGE_n>` / `<AUDIO_n>`：first image 占 IMAGE_0，
其余 reference images 顺次编号；adapter 不补写、猜测或重排标签，不切断 compiler hash。
这不是 actor voice identity qualification；自定义音频仅 trusted partners，普通订阅不声明支持。

编辑仅 Classic `/v1/videos/edits`，source MP4 ≤8700ms，输出继承源尺寸、比例、时长。
延长仅 Classic `/v1/videos/extensions`，source 2–15s、追加2–10s；canonical request duration
表示总时长，wire duration 表示追加时长。小数 source 用 provider_selected edit；extension
必须能表达精确整数追加时长。两者不发送 resolution/aspect/duration override（extend 仅追加）。
输入 >720p 时拒绝，避免自动缩小源片；`resolution_label="source"` 保留实际低于720p的 raster。
exact byte supplier 验 size/hash/MP4 envelope 后发 data URI，无额外上传；128MiB source / 400MiB
aggregate body 是本地保守上限。artifact 与 reader 同时重验继承尺寸/时长及 declared resolution。
POST 返回真实 `request_id`，GET 同一 ID 的 pending/done/failed；done 必须匹配 model 与 moderation。
fetch 重开同一 task，无凭据 public-IP pinned 下载 trusted temporary MP4。
来源：[video generation](https://docs.x.ai/developers/model-capabilities/video/generation)、
[image-to-video](https://docs.x.ai/developers/model-capabilities/video/image-to-video)、
[reference-to-video](https://docs.x.ai/developers/model-capabilities/video/reference-to-video)、
[editing](https://docs.x.ai/developers/model-capabilities/video/editing)、
[extension](https://docs.x.ai/developers/model-capabilities/video/extension)。

## Image Contract

`GrokImageProvider` 经 `ProductionStateCommitter.generate_remote_image_asset()` 执行；local seam
拒绝 remote authority。同步 `/v1/images/edits`，model `grok-imagine-image-2.0`，一张输出，1k/2k。
保留 char/scene 等 2–5 条 ordered exact Registry references，同 asset 不按 ID 去重丢角色。
seed/negative/尺寸要求不能忽略；remote request 使用显式 `None` / empty 来表达未要求这些控制。
`b64_json` 原 PNG/JPEG/WebP 保存到 content-addressed `assets/files/grok-wire/`；PNG identity，
JPEG/WebP 经已安装 Pillow 保尺寸 lossless PNG conversion。Reader 重做转换比较 exact bytes。
同步 API 未承诺 job ID；`grok-content:<digest>` 是 request + wire 派生的 content identity。
完整 remote egress、paid receipt 与 conversion lineage 进入 provenance/Registry；所有 mutable writes
仍归 committer。POST permit 与 submit 后 activation proof 权限不同；unknown 不重发。
来源：[multi-image editing](https://docs.x.ai/developers/model-capabilities/images/multi-image-editing)。

## Subscription And Injection

`GrokSubscriptionBinding` 绑定 exact account/model/origin/operation_path、5 分钟内 quota 观察、period end 与
独立 included-only evidence。构造 model 不构成授权；默认 `subscription_guard` 拒绝未验证边界。
图片入口在 intent 前检查；视频遵循原 service 的 durable intent 后、POST 前检查。
不可配置假 evidence 或 no-op guard 启用 live，真实 guard 必须由授权 owner 重验。
旧未指定 operation_path 的 Full1.5 binding 仅兼容 generation，不授权 Classic/Lite 或 edit/extend。
paid preview 使用 `remote_subscription`、每次现金 upper bound 零和 sealed finite
`subscription_submit_limit`；同币种既有现金 reservations 保留，订阅计数单独识别。
known failure 仍消耗一次；unknown 不释放、不结算、不自动重试。没有第二账本或 writer。
Video credential 注入 `GrokOAuthManager.credential_supplier(profile.account_fingerprint)`；
image 注入 `GrokOAuthManager.credential` 并重验返回 credential 的 account/reference/expiry。
transport 使用 `HttpxGrokTransport` / `HttpxGrokImageTransport`，禁止 redirect、client auth/cookies 注入。

## Verification Boundary

Focused argv/routing 归 Harness `grok_media_provider_tests`。Fake 证明 protocol、finite count、
canonical service、unknown、provenance 和 replay；不证明账号登录、quota/扣费资格、真实媒体或质量。
真实执行仍需账号/扣费 prerequisites、exact inputs、finite permits 与逐 Shot MCP Gate。
