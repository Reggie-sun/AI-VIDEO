# SuperGrok Media Provider Spec

Date: 2026-10-12
Status: authorized task scope; Parent self-reviewed; implementation in authorized worktree

## Goal And Authority

为 AI-VIDEO 接入 Grok 图片与视频生成，优先消费用户已经购买的 SuperGrok 订阅权益。
用户明确选择媒体 Provider 和订阅优先；后来明确要求“开workree实现”，取代先等共享文件的顺序。
实现使用 `/home/reggie/vscode_folder/AI-VIDEO-supergrok-media`，base `75849c7`；原工作区不接管。
本 Spec 不新增用户批准步骤；账号登录仍由用户完成，真实生成仍需满足当前项目的显式 inputs、
有限 submit count、egress、budget、durable intent 和 one-use permit。没有授权额外充值、
Auto Top Up、按次计费 API fallback、网页 Cookie 提取或 Provider 自动切换。

## Verified Base Behavior

下述是 implementation base 的缺口；current target 与证据由本任务实现、Plan 和 baseline 描述。

- `production/video.py::VideoProviderRegistry` 是注入式精确查找，Provider 名称没有硬编码枚举。
  独立 adapter 可以实现现有 `VideoProvider` protocol，不能让 registry 变成第二 Router。
- `BillingKind` 目前只有 `LOCAL_UNMETERED` 和 `METERED`；
  `build_video_paid_permit_binding()` 要求 `REMOTE + METERED`，绑定 exact preview、
  currency、monetary upper bound、egress 和 secret reference。
- `production/paid_provider.py::PaidProviderCallPreview` 尚未表达订阅权益绑定，
  operation 尚不支持 `image_generation`。不能用零金额或伪造收费上限绕过此缺口。
- `production/image.py` 的 preview、authorization、provenance 和 activation 当前均声明
  local-only / remote false。图像要求测量 exact PNG、保留 references、seed 与 geometry；
  必须扩展实际契约，不能直接注入 remote adapter 后继续签发 local provenance。
- `VideoGenerationService` 与 `ProductionStateCommitter` 已拥有远端 submit、unknown、
  polling、fetch、candidate 和 activation lifecycle；Grok 不得另建 writer 或状态账本。

## Official Integration Evidence

xAI 已公开支持在外部工具中用 SuperGrok OAuth，包含 device-code 登录：
[xAI OpenClaw announcement](https://x.ai/news/grok-openclaw)。
其链接的 [OpenClaw xAI documentation](https://docs.openclaw.ai/providers/xai) 明确说明
OAuth credential 也用于图片和视频接口，并区分订阅 quota 与 Console API credits。
[Grok FAQ](https://docs.x.ai/grok/faq) 已将 API 列入订阅 usage breakdown，同时说明
Extra Usage Credits / Auto Top Up；因此 OAuth 登录成功不能单独证明零额外扣费。

[Video API](https://docs.x.ai/developers/model-capabilities/video/generation) 的 create 返回
`request_id`，随后 GET status，再取得 temporary media URL。
[Image API](https://docs.x.ai/developers/model-capabilities/images/generation) 提供图像生成和编辑。
公开文档证明协议存在，不证明本账号 eligible、支持某个模型、quota 足够或真实媒体质量。

参考 [OpenClaw OAuth source](https://github.com/openclaw/openclaw/blob/46fe51413407bdba71ceb3114b9e7f0079c82a7e/extensions/xai/xai-oauth.ts)
和 [usage source](https://github.com/openclaw/openclaw/blob/46fe51413407bdba71ceb3114b9e7f0079c82a7e/extensions/xai/usage.ts)
的接口与错误处理思路；不移植其 Gateway、Provider fallback、retry、state 或 acceptance。
共享 public OAuth client 的可用性和适用授权必须在登录前核对；不得冒称本项目有独立注册 client。

## Target Contracts

### Authentication And Effects

登录走官方 device-code OAuth；用户只在官方页面授权。一个独立认证 owner 负责
account identity、expires_at、refresh rotation 与 private credential reference。
adapter 只接收 injected supplier，不持 token persistence authority。
token、refresh token、device_code、signed URL 不进入 repo、prompt、argv、logs 或 receipts；
receipt 仅保留 public reference、account fingerprint 和安全的 evidence identity。
无可用 token 时零 generation。Refresh lost response 属于未知 rotation outcome，停止并显式恢复，
不得自动重试；401/403 不触发 Console key 或其他账号 fallback。
同一 private item 的登录和 refresh 必须跨进程互斥；busy 在 lookup/HTTP 前停止，
不能由较早读取的 ready record 覆盖另一调用的 unknown。Coordination lock 不保存凭据。
auth、billing、generation、result-download origins 分开固定并验证，下载不向 CDN 转发 Bearer token。

### Subscription Billing

在原远端预算/intent/permit owner 内添加可识别的 subscription binding；保留原 API-key
metered 路径和历史 receipt/hash。绑定 exact account fingerprint、credential reference、
selected model、included quota 的真实观察时间/重置窗口、有限 submit count 和 overage policy。
订阅调用是 `REMOTE`，不能声明 `LOCAL_UNMETERED`。

本任务新增现金支出上限为零。只有取得适用于 exact media endpoint 的可验证 included-only
执行边界后，才允许零金额上限；usage percentage、余额存在、用户已购买订阅和客户端预检查
都不能替代服务端扣费边界。若只能观察 quota、无法限制 overage，状态为 `BLOCKED`，
不得宣称接入已启用或执行 smoke。需要新的用户费用授权时明确报告这个最小条件。
quota 缺失/陈旧/耗尽、account mismatch 或无法重验 overage 均在 POST 前拒绝。
保留同任务既有计数、reservation 和 unknown records，不重置消费或恢复已消费 permit。

### Video Adapter

新 adapter 仅拥有 Grok profile、原生 payload、status mapping 和 bounded download。
经现有 Planner → Router → compiler → `VideoGenerationService` → committer 链执行。
尽量复用既有 remote prompt grammar；不能为了接入改写 approved intent 或丢弃 continuity。
官方 profile、精确模型和 mode 在 authenticated capability admission 后才可选，
未证明的 fps、output geometry、seed、audio-disable、reference 或 frame control 均不声明支持。
首次实现包含已证明可表达的 text-to-video 和 image-to-video；reference-to-video 只在
当前 API/model/profile 能完整表达原 required controls 时开放。Unsupported 明确返回原因。
POST 超时、lost response、成功状态但缺合法 request identity 均为 unknown；不再 submit。
status/fetch 只恢复同一 durable request_id；未知 status 不猜成功，failed 不转成可盲重试。
下载验证 exact task/model、允许 origin、HTTPS/redirect、byte ceiling 和 measured MP4。

### Remote Image Adapter

在现有 image owner 扩展 remote preview、authorization、paid/subscription binding、
image submit outcome、provenance 和 candidate verification；local-only 路径保持旧 bytes/hash。
remote image 仍由 committer 写 intent/receipt/Registry/Manifest，不走 import 伪装生成。
Provider 不支持 seed、negative prompt 或 geometry 时必须拒绝这些控制；不能忽略后签成功。
参考图片必须来自原 Registry 的 exact bytes/roles，数目和模式符合 selected profile。
PNG 是当前内部素材边界；若 wire output 不是 PNG，单独保存原 wire identity，使用已安装
可验证 decoder 做保尺寸 conversion，测量转换后的 exact PNG，并记录转换 lineage。
conversion 不 resize、不去水印、不改变 declared composition；格式或尺寸不符合则失败。
第一版使用同步多图 editing；unknown 封存，不重新 POST。API 未承诺同步 job ID，因此以
request + wire 派生的 `grok-content:<digest>` 表达已收到的 output content identity。
POST 消费现有 paid permit；submit 后 activation proof 只证明 accepted paid/image joins，不能再 POST。
remote wire 使用独立 content-addressed 路径，避免 identity PNG 与 canonical PNG 路径冲突。

### Compatibility And Ownership

不增加 dependency，不安装整套 OpenClaw/Gateway，不更改 HyperFrames、ResolvedTimeline、
creative state、QA acceptance、local ComfyUI exemption 或现有 paid Provider 默认选择。
给 oversized 模块的新责任建立叶模块；仅在既有 model/serializer/service seam 做必要适配。
历史缺省 subscription 字段保持省略；旧 Manifest、request、receipt 和 local image replay
必须逐字节兼容。实际 schema version/admission 由当前 Manifest/Registry owner 决定，
不在本 Spec 发明第二 schema catalog。

## Acceptance And Verification

1. Offline：fake transport 经真实 service/committer loading seam 覆盖 auth expiry/rotation、
   account/quota/overage、zero-POST rejection、unknown/no-retry、remote image provenance、
   exact request/task/media identity 和 legacy replay/hash compatibility。
2. Integration：Grok 可由既有 Router 选择并经统一 service 执行；没有 adapter-only 旁路。
3. Security：不打印 secret；malformed response、redirect、private-network、oversize、
   cross-account 和 expired authority 均 fail closed。
4. Delivery：exact owned commit range 的 Harness receipt；Parent final diff 和 Risk Gate。
   只有触发 Risk Gate 才增加一个受管 read-only Kimi implementation reviewer。
5. Live：用户完成 official login、账号/model/扣费资格明确后，只执行获授权的最少有界
   image/video smoke；逐 Shot exact MP4 后执行 project-local `video-analysis`。
   Offline PASS 不等于登录成功、live generation、质量 PASS 或 Final Acceptance。

## Execution Boundary And Self-Review

用户后续明确要求 dedicated worktree，已按新的顺序执行；原工作区 dirty/staged 内容保持。
新 worktree 的 auth、video、image bounded writers target files 不相交，Parent 独占共享契约和整合。
compiler 是否需要编辑以实际 grammar seam 为准；独立 video registry 不需为名称注册而修改。
Parent self-review：媒体范围、订阅优先、零额外现金、两个 Provider lifecycle、兼容、
no-fallback/no-retry、真实验收与新的 worktree 顺序均有对应契约；未验证的登录、capability 和扣费资格
保留为 admission blockers，没有转换成 READY。
