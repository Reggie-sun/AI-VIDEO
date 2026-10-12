# Grok All-Shot Video Capabilities

## Goal And Authority

用户要求“所有需要shot的类型都接入,所有grok视频生成能力都要接入”。在已授权的
`AI-VIDEO-supergrok-media` worktree 扩展已发布的 `153bd4f`；Parent self-review 后实现。
订阅优先、零额外现金、无 implicit fallback 和原 paid/egress/permit/unknown/QA gates 保持。
本 slice 不执行真实登录、生成、上传或 partner 资格申请。

## Verified Protocol

2026-10-12 重新读取 xAI 官方页面；OpenClaw 当前的 image-only 1.5 描述落后于 xAI
2026-10-08 的能力说明，以 xAI 当前协议为准，不把文档存在视为 OAuth proxy/account admission。

- [Generation](https://docs.x.ai/developers/model-capabilities/video/generation)：T2V/I2V、
  1–15s、480p/720p/1080p、native audio 或 `generate_audio=false`、异步 request_id。
- [Overview](https://docs.x.ai/developers/model-capabilities/video/overview)：
  `grok-imagine-video-1.5`、`grok-imagine-video-1.5-lite`、`grok-imagine-video`。
  Lite 1080p 为 upscale，不能证明 native 1080p；Lite 无 references/voices/pins。
- [Reference](https://docs.x.ai/developers/model-capabilities/video/reference-to-video)：
  full 1.5 最多 14 references、15s、720p；classic 最多 7 references、10s、720p。
  full 1.5 支持首尾帧、最多 4 interior keyframes、最多 3 preset `voice_id`。
  自定义音频文件仅 trusted partners；不声明普通订阅支持该控制。
- [Editing](https://docs.x.ai/developers/model-capabilities/video/editing)：classic
  `/v1/videos/edits`，MP4 source ≤8700ms；output 继承 source duration/geometry，上限 720p；
  不传 duration/aspect_ratio/resolution。
- [Extension](https://docs.x.ai/developers/model-capabilities/video/extension)：classic
  `/v1/videos/extensions`，source 2–15s，added duration 2–10s，output 为 source + added；
  不传 aspect_ratio/resolution。官方接受 data URI，使用 exact Registry bytes 避免新上传/URL owner。

## Contracts And Ownership

现有五种 `VideoGenerationMode` 均实现：T2V、I2V、R2V、VIDEO_EDIT、VIDEO_EXTEND。
`FIRST_LAST_FRAME_VIDEO` 继续投影 I2V；last-only 可由 R2V 的 last_frame 输入表达。
Grok-specific keyframe/voice hard controls 归 immutable `GrokProviderProfile`，符合现有
GenerationRecipe 的 profile ownership；不新增第二 mutable native control map。
每 keyframe 封存 asset_id、SHA256、正整数 `timestamp_ticks`（每秒三 tick），最多四个，
时间排序且严格在输出 duration 内；素材必须是 request 中既有 exact `reference` image。
同一 exact image 可出现在不同首尾/时间位置；同 asset_id 必须同 SHA/metadata，按位置保留
wire frame，按唯一 asset bytes 核验 egress，不将重复位置当隐藏新素材。
这些素材仍由现有 Planner/Router/compiler 的 Registry reference inventory 纳入 request，
不得从 profile 偷渡未绑定素材。Pinned images 从 `reference_images` 排除、按时间发 `keyframes`。
Preset voices 按 profile 顺序形成 `<AUDIO_n>`；不是 voice identity qualification。
没有图片的 voice-only 请求可保持 T2V authoring，但只在 full 1.5 的 reference 输出限制下执行。
IMAGE/AUDIO 的位置标签由已批准 intent/prompt 显式表达；adapter 不猜角色到位置的对应关系，
不改写 compiler 已封存的 prompt。Preset voice 不绕过独立 voice identity qualification。

所有 profile controls 必须在 resolve 前完整验证；没有合适 model/mode、资产 hash/count/timing
或 native audio 时拒绝，不能忽略控制。空 controls 的旧 profile dump/hash 保持；旧已封存
capability 是否仍 current 由原 fingerprint gate 判定，不冒充新能力可重放旧 POST。
新增 wire payload/input validation 归叶模块；`grok.py` 保持 canonical orchestration adapter。
Fixed OAuth origin 仅新增三个明确 POST paths，不接受任意路径、redirect 或 secret-bearing download。
source video 从 injected exact byte supplier 读取并验 size/hash/MP4 envelope；最大 128MiB 是本地
内存/egress 上限，不称为官方上限。图片仍每张 20MiB，aggregate body ≤400MiB。
编辑/延长的输出 timing 是总时长；编辑允许 provider_selected 以保持 fractional source duration，
延长只在 source duration 与总时长能表达 exact integer added seconds 时执行。
输入 >720p 的自动 downsizing 不用于本项目 no-regression 编辑/延长；明确拒绝。

## Shot Coverage

无条件的 Provider 选择仍归 Router。角色/生活场景/产品交互、character_action/free_complex、
semantic/reference/exact_terminal continuity、首尾帧、多锚点 static boundary、hero repair 的
generated-video lane 和 edit/extend 均提供相应 exact capability 与 common-caller evidence。
图表/End Card/controlled product Hero、NONE/LIGHT_TRANSFORM/GRAPHIC 继续合成器的既有路径。
Grok 无公开 motion-tail input 或 native camera enforcement；对应 required control 保留 BLOCKED，
不能借“全部接入”取消 obligation、把 motion boundary 当 static 或破坏确定性素材。
Commercial source handoff 已有完整意图时采用既有 requirement v4，保留 conditioning compatibility、
产品血缘与 approved-first-frame；历史不完整 v3 的 dump/hash 不变。Router 接受经过同等核验的
v3/v4 commercial lineage；共享 remote native grammar 显式表达现有 product fidelity 字段。
C4 专用 variant 要求 exact_seconds，FPS 仍未请求；实际毫秒严格核验，不宣称 exact frame count。
adaptive raster 可请求命名 ratio；canonical artifact/reader 重验比例、Grok resolution 和继承的
源视频 raster/duration，pure I2V 重验首图比例。未知输出不得激活。
既有 exact raster 请求以封存宽高验收；其命名 ratio 不再解释为新的像素等式，保留原
Provider 的合法 rounded raster。只有 adaptive raster 的命名 ratio 执行精确比例核验。

## Acceptance And Verification

覆盖三个模型的所有适用模式、首尾/last-only/14 references/4 keyframes/3 voices、全部官方 ratio；
支持与拒绝路径验证实际 payload、endpoint、source total/added duration、exact bytes、zero POST、
subscription authority、one-use permit、unknown no-retry。测试经过既有 common caller 和 canonical
service loading seam；纯 adapter tests 不代替 integration。
保留旧 image/auth/remote Provider suites、Registry replay、request/profile hashes 和 Renderer。
运行 changed-path 完整 Harness、fresh receipt、stable Risk Gate 与必要的单一受管 Kimi review；
owned commit push `main` 并核验 remote SHA。Live account/proxy/zero-cash/quality 均 `NOT_EVALUATED`。

## Parent Self-Review

本 scope 由用户扩展指令授权。复用已有 mode、profile、reference、committer 和 subscription owners；
无新 dependency、上传 endpoint、writer、renderer 或 blind retry。文档能力与账号资格分开；
不支持的 partner/native/motion obligations 有明确拒绝证据。剩余实现细节由 Plan 稳定。
