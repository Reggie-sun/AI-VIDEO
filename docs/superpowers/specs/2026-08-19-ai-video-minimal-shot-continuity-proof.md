# AI-VIDEO Minimal Shot Continuity Proof Specification

## Status

本规范是独立的 proposed acceptance slice。它把已完成的 continuous-take chaining proof 与尚未完成的 editorial hard-cut continuity proof 分开，避免把“尾帧原样续拍”误报为 AI 漫剧镜头连续性已经解决。

截至 2026-08-19，`runs/h3-shot-continuity-live-20260819-v3/` 已完成 Local MiniMax H3 `fl2va` 两镜 technical live-local proof：Shot A activated terminal PNG 的 SHA-256 与 Shot B workflow 消费的 `first_frame` bytes 完全相等，两个 MP4 均可解码并进入 durable activation/reopen，exact replay 增加零次 submit。该证据定义为 `C1_CONTINUATION_I2V` accepted technical evidence。

该 proof 使用背对镜头的小机器人沿暗巷直线前进，两个 clip 基本保持同一构图。它没有有效压测人脸、服装、角色表演、遮挡、独立 keyframe、镜头尺度变化或对话空间关系，因此不得算作 `C2_HARD_CUT_KEYFRAME_I2V` subjective acceptance，也不得解锁 Shot Router runtime implementation。

本规范定义下一步最小但有代表性的 C2 闭环。C2 provider-neutral request/reference、additive local image profile、active-lineage validation、historical hash compatibility与P5 typed closure现已完成offline technical implementation；representative GPU live与subjective acceptance尚未执行。本文不授权cloud、remote或paid Provider调用。

## Goal

用两个短 Shot 证明 AI 漫剧真正需要的 hard-cut continuity：Shot 2 使用独立构图的 keyframe，而不是把 Shot 1 terminal PNG 原样当成 Shot 2 首帧；该 keyframe 必须由 exact upstream terminal state、canonical character reference 和冻结的 continuity constraints 显式生成并 seal，随后再由 I2V 产生 Shot 2 视频。

闭环必须同时证明：

- Shot 1 terminal evidence 是 Shot 2 keyframe generation 的真实 image input，不是 audit-only 字段或 prompt 文案；
- Shot 2 keyframe 有新的 framing，但保持 scene、character、camera axis、lighting/color、motion direction 与 exit/entrance state；
- Shot 2 video 的 exact first frame 绑定该 keyframe，并保留 keyframe 对 upstream terminal 的 lineage；
- upstream terminal、keyframe request/output 或 continuity constraints 变化时，P5 只 stale 真实 downstream closure；
- technical、local live 与 subjective acceptance 分别报告。

## Continuity Levels

| Level | Meaning | Current State | Router Gate |
| --- | --- | --- | --- |
| `C1_CONTINUATION_I2V` | Shot N terminal PNG 直接成为 Shot N+1 first frame，接近一个连续镜头被切成两段 | 已有 technical live-local evidence；subjective quality只适用于该简单 fixture | 不足以解锁 Router |
| `C2_HARD_CUT_KEYFRAME_I2V` | Shot N+1 先生成独立构图 keyframe；keyframe generation 消费 Shot N terminal + canonical references，再由 I2V 动起来 | offline technical implementation完成；尚无representative live/subjective evidence | 必须通过 representative proof |
| `C3_REFERENCE_TO_VIDEO` | Provider 原生同时消费多角色/场景/视频 references | future optional capability | 不是本闭环前置条件 |

Crossfade、插帧、optical flow、prompt-only continuity 与后期修图不构成上述任何 conditioning level。

## Scope

本 slice 固定为：

1. 两个 Shot，一个有清晰正脸的成年主角、同一发型、同一深色外套、同一明亮咖啡厅、同一叙事时间。
2. Shot 1 使用现有 Local MiniMax H3 `fl2va` path；Shot 2 keyframe 使用现有 local P7.1 image path 的 sealed reference mechanism；Shot 2 video 使用 Local MiniMax H3 `fl2va`。
3. local endpoint 只能是 literal loopback；禁止 MiniMax cloud、Hailuo、Seedance 或任何 remote fallback。
4. 两个 video clip 各 4 至 6 秒、24fps，并符合 sealed H3 frame-grid。
5. Shot 2 keyframe generation 固定消费两个 image inputs：`character` canonical reference 与 `continuity_terminal`。`continuity_terminal` 同时携带当前 scene/pose/spatial state，因此本 slice 不增加第三个 image reference，也不放宽现有 local image profile 的 two-reference resource bound。
6. Shot 2 video 只消费 activated hard-cut keyframe 作为 `first_frame`；不得声称 H3 `fl2va` 直接消费了 upstream terminal。
7. 第一轮不要求 dialogue lip-sync、narration、BGM、captions 或 final mux；这些 P4 invariants 只做回归验证。

## Representative Story Fixture

### Character and Scene

- 主角 Alice：可见正脸、稳定发型、黑色外套、醒目的红色围巾；canonical character reference 必须能清楚判断这些 identity anchors。
- 场景：日间咖啡厅；玻璃门、靠窗木桌、绿色椅子和右侧暖色吊灯是固定 spatial anchors。
- 光线：左侧窗户为主光，neutral-warm white balance，正常曝光；不得用暗场掩盖 identity drift。

### Shot 1

- medium-wide framing；camera 位于门到桌运动轴线的同一侧。
- Alice 从画面左侧推门进入，门框造成一次短暂 partial occlusion。
- 她向靠窗木桌移动并伸手触碰绿色椅背。
- terminal state 冻结：右手已接触椅背、身体仍向右运动、视线朝桌面、红围巾与黑外套清晰可见。

### Shot 2

- hard cut 到 medium framing；是独立 keyframe，不与 terminal frame pixel-identical。
- camera 仍在同一轴线侧，Alice 保持 screen-left-to-right 的动作方向。
- initial state 从“手在椅背、身体向右、视线朝桌面”继续，完成拉椅、坐下并抬眼看向桌对面。
- 玻璃门、窗、木桌、绿色椅子和暖色吊灯的空间关系保持可解释；允许 framing 收紧导致部分 anchor 出画，但不得重排或镜像场景。

这个 fixture 比小机器人直线运动更难，但仍然保持单角色、单场景和简单动作，能隔离 continuity failure，不把群像、口型或复杂摄影同时引入。

## Ownership

### Timing Owner

`ResolvedTimeline` 仍是唯一 Shot order、frame/sample、trim 与 boundary timing owner。P7 keyframe generation 和 Router 都不得建立 canonical timeline。

### Durable State Owner

`ProductionStateCommitter` 仍是唯一 durable writer、Project/Registry/graph activation 与 recovery owner。P7 adapter、H3 adapter、extractor 和 analyzer 只产生验证材料，不能直接切换 active state。

### Dependency Owner

继续使用唯一 P5 graph builder/resolver/selective rebuild。hard-cut lineage 必须形成真实 typed closure：

```text
Shot 1 activated video candidate
            |
            v
Shot 1 terminal PNG evidence
            |
            v
Shot 2 generated keyframe asset
            |
            v
Shot 2 generated video asset
            |
            v
existing composition/render closure
```

不得依据 Shot 顺序创建 blanket edges，也不得在 graph 中另造 timeline。

### Render Owner

如需合成，只能走现有 `CompositionSpec -> ResolvedTimeline -> HyperFrames`。硬切是 timeline 中的表现方式，不是 continuity conditioning 的替代品。

## Hard-Cut Keyframe Contract

### Provider-Neutral Reference Role

新增provider-neutral `ContinuityTerminalImageReferenceBinding`，与既有`ImageReferenceBinding`组成strict discriminated reference union；不得把terminal伪装成需要creative artifact ownership的ordinary scene reference。新binding的role固定为`continuity_terminal`，并必须绑定：

- exact source Shot revision/content hash；
- exact activated source video asset/candidate/generation identity；
- exact `TerminalFrameEvidence` identity、PNG SHA-256、byte size、dimensions 与 extraction receipt；
- Registry revision 与 provenance；
- exact target Shot revision/content hash；
- canonical `ContinuityConstraintSet` hash。

该 role 不是任意 scene image。它只能由已验证、已激活、与 source Shot 匹配的 terminal evidence构造；wrong source、inactive candidate、tampered bytes、unreadable PNG、dimension mismatch 或 symlink escape 必须在 image Provider submit 前拒绝。

### Image Request Semantics

当前 P7 image request 要求 `character + scene`。C2 的最小扩展是允许以下两种互斥 reference set：

- ordinary keyframe：`character + scene`；
- hard-cut keyframe：`character + continuity_terminal`。

`continuity_terminal` 在 hard-cut request 中承担 exact current scene/pose/spatial state input，但不能替代 canonical character identity。hard-cut request使用新的fingerprint schema tag并覆盖terminal binding和continuity constraints；ordinary P7 request继续使用既有schema tag与fingerprint。相同exact request才可replay；任一semantic input改变都必须产生新request identity。

P7 local adapter 必须把 terminal PNG exact bytes 送入 workflow 的第二 reference slot。新增additive hard-cut execution profile，复用已sealed workflow/binding和model components，但使用新的profile content hash并声明`character + continuity_terminal` roles；既有accepted Qwen/FLUX profile files与hash不得原地改写。若 selected image profile不支持该 role 或 exact two-reference shape，必须 capability-gated、submit count为零；不得删除 terminal 改回普通 `character + scene`，也不得 fallback remote。

### Keyframe Artifact and Provenance

生成的 Shot 2 keyframe继续作为 P7 generated PNG进入 Registry。其graph-addressable `input_artifact_ids`必须包含canonical character asset/artifact ID与upstream terminal asset ID；extraction receipt、terminal evidence hash、request hash和provenance hash作为sealed evidence contributions保存，不能被伪装成不存在的graph node。临时文件不得绕过Registry、hash validation或committer。

keyframe必须有独立 asset id/SHA-256，且不能与 upstream terminal PNG bytes相同。它必须通过 local image measured metadata validation并可被reader reopen。

## Video Request Binding

Shot 2 `VideoGenerationRequest` 必须：

- `mode == image_to_video`；
- `target_visual_strategy == generated_video`；
- `image_bindings.first_frame` 精确绑定 activated hard-cut keyframe；
- 通过 provider-neutral hard-cut lineage binding seal upstream terminal evidence、keyframe request/output provenance、target Shot 与 continuity constraints；
- resolved H3 capability明确支持该 `first_frame` MIME、dimensions、output和frame-grid；
- rendered workflow实际读取的 first-frame bytes SHA-256等于 activated keyframe SHA-256。

该 lineage binding证明“H3 first frame来自一个真实消费 upstream terminal的P7 keyframe request”，不得伪装成“H3直接消费terminal”。如果现有request/evidence无法无歧义承载这条链，允许新增最小strict binding model；该field缺失时必须沿用历史P8/T2V/I2V/C1的omission与schema selection semantics，使serialized receipts、`request_input_hash`、activation-scope fingerprint、desired request fingerprint和`resolved_generation_hash`逐字节不变并可reopen。默认不修改Manifest schema、Registry schema、CLI或artifact layout。

## P5 Precise Invalidation

- Shot 1 video candidate、terminal bytes/extraction evidence或continuity constraints变化：stale Shot 2 keyframe、Shot 2 video及真实composition/render closure。
- Character reference变化：stale Shot 2 keyframe、Shot 2 video及真实closure。
- Shot 2 keyframe request/output变化：stale Shot 2 video及真实closure，但不stale Shot 1。
- Shot 2 motion/output/profile变化：只stale Shot 2 video及真实closure，不重复生成keyframe，除非keyframe semantic request也改变。
- unlinked later Shot、voice、captions、BGM与无关asset保持fresh。
- N+2只有存在显式continuity/reference edge时才transitive stale。
- exact replay不重复image submit、video submit、fetch、extract、activation或render。

## P3 and P4 Invariants

- narration、ambience、SFX、BGM、captions、resolved timing与final mux semantics不变。
- Provider native audio不得绕过P4 audio ownership。
- Static Image、Image Motion、Legacy CLI/layout、default no-network和generated-MP4 composition compatibility不变。
- hard cut、crossfade或其他transition只影响presentation，不能替代reference conditioning。

## Acceptance Tiers

### Technical Acceptance

Executable contract tests通过：reference/request binding、tamper/unreadable rejection、capability denial、P7 keyframe activation/reopen/recovery、P8 video activation/reopen/recovery、exact replay与P5 precise invalidation。该层不证明GPU live或画面质量。

### Local Live Proof

在单独、bounded local authorization下完成 representative fixture。必须记录exact profiles、workflow/component hashes、loopback submits、resource report、keyframe与MP4 measured metadata、activation/reopen及zero-call replay。文件存在不等于quality通过。

### Subjective Continuity Acceptance

对以下证据分别执行local `video-analysis`与blinded human review：

1. Shot 1 terminal frame；
2. Shot 2 independently generated keyframe；
3. Shot 2 first decoded frame；
4. 两段无转场连续播放素材。

每项按1至5分评估：character face/hair/clothing、scene anchors、camera axis、framing change是否有意、motion direction、exit/entrance action、lighting/color和spatial storytelling。每个blocking dimension的human median必须`>= 4`，且不得出现different character、different scene、axis reversal、motion reset、unreadable exposure或keyframe与terminal pixel-copy。

Technical acceptance、local live proof与subjective acceptance必须分别报告。只有三层都通过，才可称“representative hard-cut continuity最小闭环已证明”。

## Executable Acceptance Criteria

1. P7 rendered workflow消费的第二reference bytes SHA-256等于Shot 1 activated terminal PNG SHA-256。
2. Shot 2 keyframe request同时绑定canonical character与continuity terminal；缺任一项都fail closed。
3. Shot 2 H3 workflow消费的first-frame SHA-256等于activated keyframe SHA-256，而不等于被误传的任意terminal path。
4. wrong source/candidate/revision、tampered/unreadable PNG、wrong dimensions、duplicate role与unsupported profile在external effect前拒绝。
5. keyframe与两个MP4均可decode并通过measured metadata/exposure gate；主角正脸、红围巾、黑外套和至少两个可见场景anchor可判断。
6. exact replay的image/video submit、fetch、extract、activation和render增量均为零。
7. defined crash points可显式recovery；unknown submit outcome永不blind retry。
8. P5 affected nodes精确符合本规范的typed closure。
9. `ResolvedTimeline`、P4、Static/Image Motion、Legacy和no-network contracts无回归。
10. fresh Harness receipt验证exact staged/commit snapshot。

## Authorization Boundary

本规范只定义允许的设计边界，不能自行授予implementation authority。当前用户已在本任务中明确要求“执行plan”并选择“升级Hard-cut”，因此本次authority覆盖C2 technical implementation及其offline verification；它不覆盖GPU live generation、Router runtime implementation或remote Provider。live proof开始前必须获得新的bounded authorization，并记录exact local image/H3 profiles、最多一次Shot 2 keyframe submit、最多一次Shot 2 video submit，以及是否复用已激活的Shot 1 input。任何额外重试都需要新的明确授权。

MiniMax cloud、Hailuo 2.3、Seedance 2.0 Mini、remote Provider、免费quota与paid call均不在本slice内；`.env`中存在key不构成授权。

## Scope-Expansion Stop Gate

若实现证明必须新增Manifest/Registry schema version、公共artifact layout、CLI、第三个image reference、第二writer或第二dependency resolver，立即停止并请求独立scope authorization。允许新增strict request/evidence binding和typed P5 edge，但必须保持旧snapshot/reopen compatibility。

## Exit Gate for Shot Router

Shot Router runtime implementation只可在以下条件全部满足后开始：

- C2 technical acceptance通过；
- representative local live proof通过；
- subjective continuity acceptance通过；
- recovery/replay/P5 evidence归档；
- 用户另行明确授权Router implementation。

C1 proof继续保留为continuous-take evidence，但不能替代C2 gate。
