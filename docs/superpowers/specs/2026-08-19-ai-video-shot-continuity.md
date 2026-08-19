# AI-VIDEO Shot Continuity Specification

## Status

本文档最初是独立的 docs-only proposed contract。2026-08-19后续task-scoped implementation已完成provider-neutral request/evidence、Manifest 2.8 activation/recovery、P5 precise invalidation，以及Hailuo 2.3和Seedance 2.0 Mini offline adapter mapping；下文“当前尚未实现”等陈述保留为implementation前baseline。Local MiniMax H3 sealed workflow/profile、任何新Provider live proof、重新生成Shot 2/3与subjective quality acceptance仍未完成，也未由本次technical implementation授权或证明。既有P8 Provider contract仍不被改写。

当前已实现的是 frame-accurate composition：generated MP4 已能进入唯一的 `CompositionSpec -> ResolvedTimeline -> HyperFrames` 路径，并保持 P4 audio/caption/final mux 语义。当前尚未实现的是 semantic/visual continuity：三个独立生成的 Shot 不会因为精确硬切而自动共享场景、角色、镜头轴线、光线或运动状态。

## Goal

Shot Continuity 的目标是让 Shot N 已 sealed 的 terminal-frame/reference state 成为 Shot N+1 的显式 generation input，而不是隐含 prompt 约定。该输入必须同时绑定：

- scene identity；
- character identity；
- camera axis 与 camera direction；
- framing、镜头尺度与主体屏幕位置；
- lighting 与 color state；
- motion direction、速度趋势与姿态；
- Shot N 的 exit state 与 Shot N+1 的 entrance state。

成功标准不是“切点准确”或“转场平滑”，而是下一 Shot 的生成请求可证明消费了 exact upstream continuity state，并能由 executable evidence、local visual evidence 和人工 review 分层验收。

## Current Runtime Truth

当前代码已经提供以下可复用边界：

- `VideoGenerationRequest.image_bindings` 与 `VideoImageReferenceBinding` 能表达 `first_frame`、`last_frame` 或普通 `reference` 图像，并将图像 bytes hash、MIME、尺寸和大小纳入 request fingerprint。
- `VideoCapabilityVariant` 能声明 allowed image roles、required first frame、数量、格式、大小和尺寸限制；`ResolvedVideoGenerationRequest` 会在 Provider submit 前 fail closed。
- `ProductionStateCommitter` 能对 fetched video candidate 执行 measured probe、provenance sealing、Project/Registry/graph atomic activation、exact replay 和 explicit recovery。
- P5 resolver 能基于 immutable typed graph 做 precise transitive invalidation，且 `Shot.continuity_constraints` 已进入 Shot visual projection fingerprint。
- P3/P4 仍由唯一的 `ResolvedTimeline` 和唯一的 HyperFrames renderer 负责 frame/sample/timing/render。

这些能力尚不足以实现本规范：

- 普通 `first_frame` binding 没有绑定 source Shot、source candidate、source generation、terminal-frame extraction receipt 或 continuity constraint snapshot。
- fetched MP4 provenance 没有 terminal-frame evidence。
- P5 graph 没有从 Shot N 的 activated candidate/terminal evidence 指向 Shot N+1 generation input 的 typed edge。
- 当前 MiniMax Hailuo adapter 只声明 T2V；Seedance capability table 虽已声明特定 I2V/last-frame 能力，但 continuity payload、activation 和 live proof 尚未验收。
- 当前仓库没有已验收的 “MiniMax local video Provider” runtime。Local Wan + ComfyUI 仍是 local-first optional capability，但不得在缺少 exact runtime/model/profile 证据时被重命名或推断为 MiniMax local。

## Scope

本规范覆盖 provider-neutral continuity request、terminal-frame artifact/provenance、capability denial、durable activation/recovery、P5 precise invalidation，以及 technical/provider/subjective acceptance 的分层边界。

未来实现可面向三个彼此隔离的 provider lane：

1. `local continuity lane`：用户称为“MiniMax 本地”的目标必须先解析为 exact local engine、model、workflow/profile 和 loopback endpoint。若实际执行器是 Wan + ComfyUI，应按其真实 identity 命名；若仍调用 MiniMax cloud，则它不是 local lane。未完成 identity resolution 前不得 submit。
2. `MiniMax cloud Hailuo 2.3 lane`：目标 model 为 `MiniMax-Hailuo-2.3`，只在 adapter 显式支持并验证 I2V `first_frame` 后进入 continuity flow。
3. `Seedance 2.0 Mini lane`：目标 model 为 `doubao-seedance-2-0-mini-260615`，继续受 exact model/profile capability 和 paid Provider gates 约束。

Provider-specific payload、model naming、duration/resolution 限制不得进入 provider-neutral core model。

## Non-Goals

本 slice 不做以下事情：

- 不新增第二 timeline、第二 renderer、第二 state writer 或通用 Agent runtime。
- 不把 crossfade、插帧、optical flow、prompt 文案复用或剪辑遮挡描述为完整 continuity solution。
- 不改变 Legacy CLI、Legacy layout、public CLI commands、default no-network 或 local-first policy。
- 不重新生成 Shot 2/3，不调用本地或云端 video Provider，不产生新的付费行为。
- 不修改 P8 provider spec，不把 proposed continuity fields 写成已实现 runtime truth。
- 默认不增加 dependency、CLI、Manifest schema 或 artifact layout。

## Ownership and Invariants

### Timing Ownership

`ResolvedTimeline` 继续是唯一 order、frame、sample 和 Shot-boundary timing owner。Terminal-frame extraction 使用已测量 video metadata 和 resolved source span，但不得建立另一套 canonical timing、Shot order 或 duration 推导。

### Durable State Ownership

`ProductionStateCommitter` 继续是唯一 durable writer、candidate activation 和 recovery owner。Terminal-frame evidence、下游 request binding 与相应 Project/Registry/graph activation 必须通过这一 façade 所拥有的 transaction boundary 持久化；reader、Registry、dependency resolver、Provider adapter 和临时 extraction helper 均不得成为第二 writer。

### Dependency Ownership

继续使用唯一 P5 dependency graph builder、resolver 和 selective rebuild decision。Continuity 只能增加必要的 typed dependency input，不能在 graph 中复制 timeline 或维护另一份 mutable lifecycle truth。

### Render Ownership

继续使用唯一 HyperFrames renderer。Continuity conditioning 在 Provider generation 之前完成；renderer 只消费已激活 visual assets 和唯一 `ResolvedTimeline`，不负责修补生成素材的语义跳变。

## Provider-Neutral Continuity Contract

### Continuity Constraint Set

未来 contract 应把当前自由文本 `continuity_constraints` 稳定为可 seal 的、provider-neutral constraint snapshot；在不改变 schema 的可行方案被证明前，本规范不预先决定它是新 model、现有 artifact 的结构化 payload，还是向后兼容 extension。其 canonical content 至少包含：

- `scene_identity`: exact Scene/reference artifact identities；
- `character_identities`: 有序的 exact Character/reference artifact identities；
- `camera_axis`: 轴线 identity、camera side、view direction；
- `framing`: shot scale、subject placement、camera height/angle；
- `lighting`: key direction、contrast、time-of-day 与 motivated sources；
- `color`: white balance、palette 与 exposure intent；
- `motion`: subject/camera direction、speed trend 与 pose/action phase；
- `boundary_state`: upstream exit state 与 downstream required entrance state。

该 snapshot 必须有 canonical content hash，并进入 Shot N+1 的 desired generation fingerprint。仅修改文字但不改变 canonical continuity semantics 不应产生漂移；任何 semantic field 变化必须改变 fingerprint。

### Terminal Frame Evidence

对每个作为 continuity source 的 activated video candidate，必须生成可验证、可重放的 `TerminalFrameEvidence`。逻辑 contract 至少包含：

- exact `source_shot_id`、Shot revision 和 Shot content hash；
- exact source video `asset_id`、asset SHA-256、Registry revision/pointer；
- exact source `generation_id`、request fingerprint、resolved generation hash 和 provenance receipt identity；
- measured source metadata：container、codec、width、height、rational FPS、duration 和 frame count；
- terminal selection：frame index、对应 source timestamp/rational position，以及 selection rule/version；
- extraction identity：extractor/tool version、canonical arguments 和 extraction receipt hash；
- extracted image SHA-256、MIME、byte size、width、height、pixel/color metadata；
- evidence schema version 与 canonical evidence hash。

Terminal frame 默认是已激活 source candidate 的最后一个可解码 presentation frame，而不是 MP4 文件的任意最后 packet，也不是 composition 之后的 crossfade frame。若 Shot N 在 composition 中有 explicit trim，则 continuity source 是 generation candidate 的 terminal state 还是 resolved trim-out state，必须由 continuity contract 显式选择并进入 hash；不得靠 helper 猜测。

### Downstream Request Binding

Shot N+1 的 continuity-enabled `VideoGenerationRequest` 必须包含或引用一个 sealed `ContinuityReferenceBinding`，其逻辑内容至少绑定：

- role 为 `first_frame`；
- exact `TerminalFrameEvidence` identity/hash；
- exact upstream Shot/candidate/video asset identities；
- exact extracted image bytes hash 与 measured metadata；
- exact downstream Shot identity/revision；
- exact continuity constraint snapshot hash。

现有 `VideoImageReferenceBinding` 可承载 Provider 所需的图像 bytes metadata，但不能单独证明 upstream lineage。实现必须扩展或组合现有 binding，而不是只把一个临时 PNG path 塞入 Provider adapter。该选择必须保持 canonical request hashing、strict validation 和旧 request hash compatibility。

### Capability Resolution

Continuity request 必须在 submit 前完成 provider-neutral capability resolution：

- Provider variant 必须显式允许 `IMAGE_TO_VIDEO` 和 `first_frame`，且 `required_first_frame`/format/size/dimension/output coupling 全部满足。
- 若 contract 要求 `last_frame`、multi-reference、character reference 或其他 role，variant 也必须逐项声明。
- capability 不满足时返回 typed `VIDEO_CAPABILITY_UNSUPPORTED`，Provider submit call count 必须为零。
- 不得从 continuity-enabled I2V 静默退化为 T2V、独立生成、仅 prompt conditioning 或远程 fallback。
- Provider adapter 只能翻译已经 resolved 的 request；不得自行删除 continuity binding、替换 reference 或降低 constraint。

## Provider-Specific Profiles

### Local Continuity Lane

当前 local runtime truth 只有 Legacy/local-first ComfyUI 边界与 optional Wan capability，没有 production `ComfyUIVideoProvider` continuity adapter，也没有可证实的 “MiniMax local” model/profile。未来实现前必须取得并 seal：exact local engine、model checkpoint/hash、workflow/profile、input node contract、loopback endpoint 和 output capability。不能解析这些 identity 时必须 fail closed，且不得切换到 MiniMax cloud。

### MiniMax Cloud Hailuo 2.3

MiniMax 官方 I2V contract 当前列出 `MiniMax-Hailuo-2.3`，以 `first_frame_image` 接收首帧图像；官方 model guide 同时把 Hailuo 2.3列为 T2V/I2V model。当前仓库 adapter 仍只声明 T2V，因此未来实现必须新增独立、tested 的 I2V capability/payload mapping，不能仅修改 prompt。官方 first/last-frame 示例属于其他明确 model 时，不得推断 Hailuo 2.3 支持未声明的 `last_frame`。

References:

- [MiniMax Image-to-Video API](https://platform.minimax.io/docs/api-reference/video-generation-i2v)
- [MiniMax Video Generation Guide](https://platform.minimax.io/docs/guides/video-generation)
- [MiniMax Models](https://platform.minimax.io/docs/guides/models-intro)

### Seedance 2.0 Mini

当前仓库 capability table 对 `doubao-seedance-2-0-mini-260615` 声明了 I2V first/last-frame 能力，但这只是当前 tracked contract，不等于 continuity live acceptance。未来实现必须以 exact official profile snapshot 重新核对 model/mode/input roles，并为 first-frame payload、optional last-frame payload、audio opt-out、response parsing、fetch、activation 和 replay 建立 executable evidence。

此前 Seedance Mini diagnostic 只证明一次 cloud connectivity 和 fetched MP4；它不证明 tracked continuity payload、billing settlement、activation 或 quality acceptance。

Reference: [Volcengine Doubao Seedance 2.0 Series Tutorial](https://www.volcengine.com/docs/82379/2291680?lang=zh&sessionid=)

## Artifact and Provenance Lifecycle

1. Source video candidate 必须先通过现有 measured validation 和 provenance sealing。
2. Terminal extraction 必须读取由 committer transaction 持有并重新验证的 exact source bytes；路径 reopen 后必须再次验证 containment、type、size 和 hash。
3. Extraction 输出必须先进入 immutable, content-addressed candidate evidence，再与 source candidate identity 和 downstream binding 一起由 `ProductionStateCommitter` durable commit/activate。
4. 临时文件只可作为 transaction-local scratch；不得被 request、Registry、Manifest 或 Provider receipt 直接引用，成功或恢复后也不得成为唯一 evidence。
5. reopen/recovery 必须从 durable evidence 验证 image hash、metadata、source candidate 和 downstream binding；tampered、unreadable、symlink escape、wrong source Shot 或 wrong Registry revision 全部 fail closed。
6. 相同 source candidate、selection rule、extractor contract 和 continuity constraints 的 exact replay 必须返回相同 evidence，不重复 extraction 或 durable writes。

当前 P8 activation 假设只 append 一个 generated video Registry asset。若 terminal image 必须作为第二个 active Registry asset 才能满足 durable reopen，或若 request/Manifest 必须保存新 pointer，则这会触发 schema/layout/activation protocol expansion。实现者必须先用 executable spike 证明无法通过现有 immutable provenance/evidence seam 达成；确认不可避免后，只能提交独立 scope-expansion spec 和授权请求。本 docs-only slice 不预先批准该 mutation。

## P5 Precise Invalidation

### Required Dependency Meaning

P5 graph 必须表达一个 typed continuity dependency：Shot N 的 exact activated video/terminal evidence 是 Shot N+1 generated-video asset 的 generation input。推荐的语义方向是：

`source terminal evidence N -> generated visual asset N+1`

这样 upstream bytes/evidence 变化会 stale 真正需要重新生成的下游 asset，而不会篡改 Shot N+1 的 authoring artifact 或另造 timeline。具体 node representation 和 edge enum 由实现 plan 的 RED tests 决定，但必须保留 typed allowlist 和 immutable graph inputs。

### Closure Rules

- Shot N candidate、source video bytes、terminal-frame evidence、selection rule或 Shot N+1 continuity constraints 变化时，首先 stale Shot N+1 的 generation input/output node。
- 只沿现有 P5 graph 的真实 dependent closure 传播到 composition/source/render，以及显式以 Shot N+1 terminal evidence 为输入的 Shot N+2。
- 没有 continuity edge 的后续 Shot 不得 blanket stale；unrelated assets、voice、captions 和其他 Shot 必须保持原 state/evidence。
- Shot N 自身只是换 active candidate 时，其上游无关节点不得重建。
- P5 graph 不计算 frame number、Shot order 或 duration；这些仍来自现有 project bindings 与 opaque timeline fingerprint。

### Replay and Failure Rules

- continuity binding 和 terminal evidence 必须进入 desired generation fingerprint。
- exact replay 不得重复 Provider submit、status/fetch、terminal extraction、candidate activation、dependency resolution side effect 或 render。
- same-desired terminal failure 不得 auto-retry；continuity-dependent nodes保持 blocked，直到 desired input 真实变化或显式 recovery 完成。
- crash recovery 必须区分 provider effect 已发生、video 已 fetched、terminal evidence 已持久化、candidate 已准备和 activation 已提交等阶段，复用已有 attempt/receipt，而不是重新 submit。

## P4 and P3 Invariants

- narration、ambience、SFX、BGM、captions、resolved timing、source trim 和 final mux semantics 不变。
- generated MP4 继续通过既有 `CompositionSpec -> ResolvedTimeline -> HyperFrames` 路径；static-image 和 `EXISTING_VIDEO` path 不变。
- Shot boundary 仍由唯一 timeline 精确落在 frame/sample boundary。
- Provider 原生音轨的现有 policy 不因 continuity 改变；不得借 continuity 重新定义 P4 audio ownership。
- transition 仅是表现手段。crossfade、插帧或遮挡可以在已连续素材上使用，但不能作为缺失 reference conditioning 的替代品，也不能使 technical continuity acceptance 通过。

## Acceptance

### Executable Contract Acceptance

未来实现必须至少覆盖：

- terminal evidence 与 exact source Shot/candidate/Registry/provenance binding；
- request hash 对 terminal bytes/evidence/constraint 变化敏感，对 generation instance identity 的既有 replay 语义保持兼容；
- tampered、unreadable、wrong-dimension、wrong-source、wrong-revision 和 symlink-escape rejection；
- unsupported mode/role/model/output 的 capability denial，且 submit 为零；
- exact replay 的 submit/fetch/extract/activate/render 都为零；
- fetched、extracted、prepared、partially activated 各 crash point 的 explicit recovery；
- Shot N input 改变只 stale Shot N+1 及真实 downstream closure，unrelated/future-unlinked Shot 保持 fresh；
- static-image、Legacy、composition、audio/caption 和 default no-network regressions 不发生。

### Local Visual Evidence

每个 continuity edge 必须产出可重放的 pair evidence：

- Shot N terminal frame；
- Shot N+1 initial decoded frame；
- 两者各自的 source asset/hash/frame index/timestamp；
- 无美化、无 crossfade 的 side-by-side 或 deterministic comparison artifact。

自动 `video-analysis` 与人工 review 是不同 gate。两者分别检查 scene/character identity、camera axis/direction、motion direction、lighting/color、entrance/exit state和叙事空间关系；任何单一 similarity score 不得替代逐项 verdict。

### Acceptance Tiers

1. `technical acceptance`：Fake/offline executable contracts、local artifact verification、replay/recovery/P5 tests 和 composition invariants 全部通过。
2. `provider live proof`：每个明确 provider/model/profile 通过 separately authorized 的真实 submit/fetch/activation/replay proof；成功只证明该 lane 的 connectivity、payload 和 durable lifecycle，不自动外推到其他 provider。
3. `subjective continuity/quality acceptance`：对 terminal/initial pairs 与最终序列完成 blinded human review，并满足预先定义的 scene、character、camera、motion、lighting/color 和 spatial-storytelling rubric。

三层必须分别报告。Technical acceptance 不等于 live proof，live proof 也不等于 subjective quality acceptance。

## Authorization Boundary

重新生成 Shot 2/3、调用 MiniMax cloud Hailuo 2.3、Seedance 2.0 Mini 或任何所谓 local MiniMax runtime 都是新的执行行为；远程 lane 还可能产生付费。Live execution 必须取得明确列出 provider/model、预算和调用边界的 task-scoped authorization、Budget Guard、Cloud Egress 和 bounded-call plan；同一条明确执行请求可以同时授权其中列明的多个 lane，不要求为每个 lane重复询问。本 docs-only task 不授予这些权限，schema/layout scope expansion 仍必须独立授权。

## Rollback

未来 continuity implementation 必须可按 provider lane 删除：移除 continuity-specific adapter capability/payload mapping、terminal evidence reader/writer seam 和 typed P5 edge后，旧 P8 T2V/I2V request、candidate activation、static-image path、generated-MP4 composition和 P3/P4/P5 ownership必须恢复到当前行为。已存在的 continuity artifacts 应保持 immutable、可审计但不再被 active graph 选择；不得通过删除历史 receipts 完成 rollback。
