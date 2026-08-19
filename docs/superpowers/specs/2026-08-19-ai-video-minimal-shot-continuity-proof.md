# AI-VIDEO Minimal Shot Continuity Proof Specification

## Status

本规范是独立的 docs-only proposed acceptance slice。它不改变既有 [Shot Continuity specification](./2026-08-19-ai-video-shot-continuity.md)，也不把尚未执行的 Local MiniMax H3 continuity、live Provider 或 subjective quality 写成 runtime truth。

截至 2026-08-19，provider-neutral continuity request/evidence、Manifest 2.8 activation/recovery、P5 precise invalidation、Hailuo 2.3 与 Seedance 2.0 Mini offline mapping 已实现。现有 locally stored Hailuo cloud diagnostic evidence 记录了 exact terminal-frame I2V binding、candidate activation 和 frame-accurate composition，但该 diagnostic 画面严重欠曝，且 canonical runtime baseline 仍只把 Hailuo continuity 记为 offline mapping，不把它升级为 live/quality acceptance。现有 Local MiniMax H3 可见成片只证明一次 15 秒 T2V 单镜头，不是 Shot-to-Shot continuity。当前可接受的跨 Shot continuity proof 数量仍为零。

本规范只定义下一个最小证据闭环。它不授权运行 ComfyUI、重新生成视频、调用 remote Provider 或消耗免费/付费 quota。

## Goal

用两个短 Shot 证明一件具体事情：Shot 1 已激活候选的 exact terminal PNG，经过既有 durable continuity lifecycle，确实成为 Shot 2 的 `first_frame` input，并产生肉眼可见、身份与空间关系可接受的连续视频。

该证明必须同时满足：

- 技术 lineage 可验证，而不是仅在 prompt 中写“保持连续”；
- Shot 1 terminal frame 与 Shot 2 first decoded frame 的 bytes、hash、尺寸和 source identity 可追溯；
- scene、character、camera axis、framing、lighting/color、motion direction 与 exit/entrance state 均有冻结约束；
- 两段素材本身可见，不依赖提亮、crossfade、插帧或剪辑遮挡通过验收；
- exact replay 不重复 local submit、fetch、extraction、activation 或 render。

本 gate 通过之前，Shot Router 可以完成 docs/spec 设计，但不得进入 runtime implementation 或声称自动路由已可用。

## Verified Current State

| Evidence | What It Proves | What It Does Not Prove |
| --- | --- | --- |
| `src/ai_video/production/video.py` 中的 `ContinuityConstraintSet`、`TerminalFrameEvidence`、`ContinuityReferenceBinding` 与 `VideoGenerationRequest` | 核心模型已经能 seal source candidate、terminal PNG、target Shot、structured constraints 和 request fingerprint | 不证明任何 Provider 实际消费这些字段，也不证明视觉质量 |
| `runs/shot-continuity-live-20260819-001/hailuo23-chain/` | Locally stored cloud diagnostic evidence 记录 Hailuo 2.3 chain 消费 terminal first-frame，并进入 Registry/Project/P5 activation 和既有 composition | canonical baseline 未将其列为 Hailuo continuity live acceptance；成片欠曝，不能作为可用 continuity/quality acceptance |
| `runs/minimax-h3-text-only-visible-20260819-001/` | Local ComfyUI + `minimax_h3_fl2va_pruned_int8_convrot.safetensors` 能生成 362 frames、24fps、可见 H.264/AAC 单镜头；execution report 的 average luma 为 74.569，minimum frame average luma 为 46.684 | mode 是 `text_to_video`，没有消费 upstream terminal frame，没有进入 production continuity lifecycle |
| `VideoProviderRegistry` | 只做 exact injected lookup，并对未知 Provider fail closed | 当前没有 automatic Provider selection 或 fallback，这正是 Router 后续 slice 的边界 |

## Scope

最小闭环固定为以下范围：

1. 两个 Shot，记为 Shot 1 与 Shot 2；不增加第三个 Shot。
2. 一个固定主角、同一服装、同一场景、同一叙事时间段。
3. Local ComfyUI + MiniMax H3 `fl2va`，literal loopback endpoint；不调用 MiniMax cloud、Hailuo、Seedance 或其他 remote Provider。
4. 每个 Shot 的目标时长为 4 至 6 秒，24fps；实际 frame count 必须符合 sealed H3 profile 的合法 frame-grid。
5. Shot 1 使用已批准的首帧/keyframe；Shot 2 必须使用 Shot 1 activated candidate 的 exact terminal PNG 作为 `first_frame`。
6. 第一轮验收只看 raw visual clips 与未加转场的 boundary pair；不要求 narration、BGM、captions 或 final mux。

`ref2va` 不属于最小必需路径。若 `fl2va` 在 technical binding 正确的前提下仍无法保持角色或场景 identity，增加独立 `ref2va` profile 属于后续 scope expansion，不能在本 proof 中静默切换 checkpoint/profile。

## Non-Goals

- 不实现 Shot Router、episode batching、自动 Provider 选择或自动 paid upgrade。
- 不新增第二 timeline、renderer、state writer、dependency resolver 或通用 Agent runtime。
- 不改变 Legacy CLI/layout、public CLI、Manifest schema、artifact layout 或 default no-network。
- 不用 T2V、prompt-only continuity、crossfade、插帧、optical flow、V2V 修补或后期提亮替代 first-frame conditioning。
- 不要求两个 Shot 合成完整成片；composition compatibility 已由独立 slice 证明。
- 不把一次成功推广为 Hailuo、Seedance、其他 H3 profile 或所有题材的 quality acceptance。

## Ownership

### Timing Owner

`ResolvedTimeline` 仍是唯一 frame/sample/order/Shot-boundary timing owner。本 proof 的 terminal selection 继续使用已实现的 measured candidate metadata 与 `generated_candidate_terminal` 规则，不另造 storyboard timeline 或以 Router 推导 frame index。

### Durable State Owner

`ProductionStateCommitter` 仍是唯一 durable writer、candidate activation 和 recovery owner。ComfyUI adapter、workflow renderer、terminal extractor、visual analyzer 和 proof runner 均不得直接更新 Registry、Project、graph 或 Manifest。

### Dependency Owner

继续使用既有 P5 graph builder/resolver/selective rebuild。Shot 1 candidate 或 terminal evidence 变化时，只 stale Shot 2 generation 及真实 downstream closure；不得按 Shot 顺序 blanket stale。

### Render Owner

若 proof 后续需要 composition，只能使用既有 `CompositionSpec -> ResolvedTimeline -> HyperFrames`。本 proof 的 raw boundary review 不构成第二 renderer。

## Fixture Contract

### Story Fixture

fixture 必须故意选择明亮、易判断的室内日景，排除“创作上刻意黑暗”对曝光验收的干扰。冻结以下内容：

- 一个有 canonical Character reference 的主角；服装、发型、脸部特征和主要配色固定；
- 一个有 canonical Scene reference 的室内场景；门、桌、窗等空间锚点固定；
- Shot 1：主角从画面左侧进入，沿固定 camera axis 向桌边移动，结束在动作中间态；
- Shot 2：从 exact terminal pose、screen position、gaze 和 motion vector 开始，继续同方向动作并完成一个简单目标动作；
- camera side 不跨轴；Shot 2 可轻微收紧 framing，但不得无理由反打、跳轴或瞬移；
- lighting direction、white balance、exposure intent 和 palette 在两个 Shot 间保持一致。

复杂群像、快速旋转、遮挡换装、强闪光、昼夜变化和大幅镜头运动全部排除。这个 fixture 验证 continuity mechanics，不测试模型能力上限。

### Input Fixture

执行前必须 seal：

- Shot 1 与 Shot 2 exact revisions/content hashes；
- Character Bible 与 canonical character reference identities/hashes；
- Scene reference identity/hash；
- Shot 1 keyframe identity/hash；
- `ContinuityConstraintSet` 的 scene、character、camera、framing、lighting、color、motion、exit 与 entrance fields；
- Local H3 execution profile、workflow template、binding、checkpoint、text encoder、VAE、node inventory 与 ComfyUI commit identities；
- output width、height、fps、frame-grid、native-audio policy、seed policy 和 resource limits。

任一 identity 无法解析、bytes tampered/unreadable、workflow node 缺失、checkpoint hash 漂移或 endpoint 不是 literal loopback 时，submit count 必须为零。

## Generation Contract

### Shot 1

Shot 1 必须通过 sealed Local H3 `fl2va` profile 生成，使用明确的 `first_frame` keyframe 和 motion description。成功后只允许 `ProductionStateCommitter` 完成 candidate validation/activation、terminal extraction、terminal PNG Registry evidence 与 recovery state。

### Shot 2

Shot 2 的 `VideoGenerationRequest` 必须满足：

- `mode == image_to_video`；
- `target_visual_strategy == generated_video`；
- `continuity_binding.role == first_frame`；
- `image_bindings` 中的 `first_frame` asset/hash/size/dimensions 与 `TerminalFrameEvidence` 完全相等；
- `ContinuityReferenceBinding` 绑定 exact Shot 1 candidate、generation、Registry revision、provenance、terminal extraction receipt 与 Shot 2 revision；
- resolved capability 明确允许并要求 `first_frame`；
- workflow rendered input 中 `MiniMaxH3ImageToVideo.first_frame` 读取的 bytes SHA-256 等于 sealed terminal PNG SHA-256。

任何一项不成立都必须 fail closed。禁止删除 binding 后改跑 T2V、使用 Shot 1 authoring keyframe 代替 terminal PNG，或 fallback 到 cloud。

## Exposure and Decodability Gate

下列阈值只适用于本明亮 fixture，不是全局创作限制：

1. 两个 MP4 均可完整 decode，H.264 video stream、24fps、expected frame-grid、尺寸和 duration 与 resolved output 一致。
2. 每个 clip 的全帧平均 8-bit luma 必须 `>= 45`。
3. 不得存在连续 12 frames 或以上、窗口平均 luma `< 30` 的区间。
4. Shot 1 terminal frame 与 Shot 2 initial decoded frame 的平均 luma 均必须 `>= 35`。
5. human review 必须能在正常显示器亮度下看清主角脸部/轮廓、服装主色和至少两个场景锚点；仅数学阈值通过但主体不可辨认仍失败。

不得通过对 proof artifact 做后期曝光补偿来通过 gate。若需要调曝光，应修改并重新 seal generation input/profile，再产生新 generation identity。

## Continuity Quality Gate

对未加 transition 的 Shot 1 terminal frame、Shot 2 first decoded frame和两段连续播放素材，分别执行 local `video-analysis` 与 blinded human review。每个维度使用 1 至 5 分：

| Dimension | Blocking Condition |
| --- | --- |
| Character identity | 脸、发型、服装或主要体态变成另一角色，或无法判断是同一人 |
| Scene identity | 关键空间锚点消失/重排到不可能位置，或明显换到另一场景 |
| Camera axis and framing | 无叙事理由跨轴、screen direction 反转、主体瞬移或尺度突变 |
| Motion and boundary state | Shot 2 没有从 Shot 1 exit pose/vector 开始，动作重置、倒放或跳步 |
| Lighting and color | key light 方向、曝光、white balance 或 palette 出现无动机跳变 |
| Spatial storytelling | 观众无法理解人物从哪里来、往哪里去或动作目标在哪里 |

通过要求：每个 blocking dimension 的 human median score `>= 4`，且无 reviewer 标记“different character”“different scene”“axis reversal”“motion reset”或“unreadable exposure”。`video-analysis` 只提供独立 evidence，不得覆盖 human blocking verdict。

## Replay, Recovery, and Invalidation

- exact replay：Local H3 submit、history/fetch、terminal extraction、activation 和 render 增量全部为零。
- before-submit recovery：无 Provider effect，恢复后保持可显式重试。
- after-submit unknown outcome：不得 blind resubmit；必须保持 typed unknown/blocked state。
- fetched/prepared/partially activated crash：显式 recovery 只能收敛到 exact old/new durable tuple。
- Shot 1 candidate 或 terminal bytes 变化：stale Shot 2 generated visual 与真实 composition/render closure。
- 仅改变无关 Shot、voice、captions 或 BGM：Shot 1/2 visual generation 不得 stale。
- 改回完全相同 desired inputs：复用既有 evidence，不重复 local generation。

## Acceptance Tiers

### Technical Acceptance

contract tests、tamper rejection、capability denial、exact request-to-workflow hash binding、replay/recovery 与 P5 precise invalidation 全部通过。该层可以使用 fake/offline fixtures，不证明 GPU live 或视觉质量。

### Local Live Proof

在单独 task-scoped authorization 下，两个 Shot 各只有一次 bounded loopback submit；两段 MP4、terminal PNG、request/workflow binding、activation/reopen evidence 和 resource report 完整。该层不因文件存在而自动通过 quality gate。

### Subjective Continuity Acceptance

Exposure and Decodability Gate 与 Continuity Quality Gate 都通过，且保留 raw pair、评分和 blocking notes。只有这一层通过后，才能称“最小两镜连续性闭环已证明”。

三层必须分别报告。Technical acceptance 不等于 local live proof；local live proof 不等于 subjective acceptance。

## Executable Acceptance Criteria

1. Shot 2 rendered workflow 所消费的 `first_frame` SHA-256 与 Shot 1 activated terminal PNG SHA-256 完全相等。
2. wrong source Shot/candidate/Registry revision、tampered/unreadable PNG、wrong dimensions 与 symlink escape 均在 submit 前拒绝。
3. unsupported mode/role/profile、non-loopback endpoint 或 incomplete H3 component identity 的 submit count 为零。
4. 两段 MP4 通过 Exposure and Decodability Gate。
5. exact replay 的 submit/fetch/extract/activate/render 增量均为零。
6. defined crash points 可显式 recovery，unknown submit outcome 永不 blind retry。
7. Shot 1 evidence 变化只 stale Shot 2 及其真实 downstream closure；无关 Shot/audio/caption 保持 fresh。
8. raw terminal/initial pair 与连续播放素材通过独立 `video-analysis` 和 blinded human rubric。
9. `ResolvedTimeline`、P4 audio/captions、HyperFrames、Static Image、Legacy CLI/layout 与 default no-network contract 无变化。
10. fresh Harness receipt 验证 exact staged/commit snapshot。

## Authorization Boundary

实现本规范中的 local live proof 会运行 GPU、生成新媒体并可能占用较长时间，因此必须由新的 task-scoped authorization 明确列出 Local MiniMax H3、exact profile、两个 Shot、最大 submit 次数和 resource boundary。本 docs-only task 不授予该权限。

MiniMax cloud Hailuo 2.3、Seedance 2.0 Mini、任何 remote Provider、免费 quota 或付费调用均不属于本 proof。即使 `.env` 中存在 key，也不能视为授权。

## Rollback

如果最小闭环失败，保留 immutable failure evidence 与评分，停在 Local H3 lane；不得自动升级到 remote Provider。任何未来实现都必须可删除 Local H3 adapter/profile 而不影响既有 P8 contracts、Hailuo/Seedance adapters、Manifest 2.8 continuity evidence、P5 resolver、generated-MP4 composition、Static Image 或 Legacy runtime。

## Exit Gate for Shot Router

Shot Router runtime implementation只可在以下条件全部满足后开始：

- 本规范的 technical acceptance 已通过；
- Local H3 两镜 live proof 已通过；
- subjective continuity acceptance 已通过；
- failure/replay/recovery/P5 evidence 已归档；
- 用户另行明确授权 Router implementation。

在此之前，Router spec 只能定义 proposed decision contract，不得自动执行任何 generation mode 或 Provider。
