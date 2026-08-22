---
surface_id: shot_continuity
canonical: true
spec_status: accepted
implementation_status: implemented_offline
live_status: partial
quality_status: partial
release_status: unreleased
runtime_status_owner: docs/v0.2-runtime-baseline.md
roadmap_owner: docs/v0.2-agentic-production-roadmap.md
---

# AI-VIDEO Shot Continuity Specification

## Status

Accepted with implemented offline foundations and partial live/quality evidence。Provider-neutral
request/evidence、activation/recovery、P5 precise invalidation、offline adapter mapping及local continuity
seams已有实现；具体live attempts、human decisions与dynamic branch状态由runtime baseline和exact records/
receipts记录，不由本normative spec固定。既有P8 remote/Paid Provider contract不被改写。

当前已实现frame-accurate composition与显式Local H3 terminal-to-first-frame continuity lane：generated MP4仍进入唯一的`CompositionSpec -> ResolvedTimeline -> HyperFrames`路径并保持P4 audio/caption/final mux语义。该lane不会让任意三个独立生成的Shot自动共享场景、角色、镜头轴线、光线或运动状态；只有带exact continuity binding并逐Shot生成的edge获得技术保证，语义质量仍需独立人工验收。

本规范继续作为唯一Shot Continuity canonical owner，并冻结
`C4_MULTI_ANCHOR_MOTION_CONTINUITY`与boundary-aware controlled multi-provider transition target
contract；不创建
平行spec。C4 provider-neutral binding、requirement/request/resolved hashing、exact cardinality grammar与
Router fail-closed gate已实现offline；但当前仍没有一个concrete Provider child完成四锚点capability seal、
full local smoke、continuity/identity quality acceptance和P6 Final Acceptance。因此当前只能声明
`C4 core contract implemented offline`，不能声明`four-anchor Production support`或“任意Provider无缝切换”。
具体失败run、artifact hashes、automatic metrics与human decisions只进入runtime baseline、exact receipts或
`docs/record_for_agent/`；任何单次review或similarity metric都不得升级为Final Acceptance。

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

对于`C4_MULTI_ANCHOR_MOTION_CONTINUITY`，成功标准进一步要求同一个resolved capability在同一次generation中同时消费exact terminal、独立canonical identity reference、approved exact future endpoint与exact upstream motion tail。静态frame anchors只能证明边界像素、identity和目标姿态约束；只有motion tail才能携带upstream gait phase、subject velocity、camera direction与camera velocity。Prompt不得代替上述任一binding。

多Provider能力的成功标准是boundary-aware portability，而不是任意位置换模型。没有visible editorial cut的
`WITHIN_CONTINUOUS_TAKE`必须锁定exact provider/model/profile/capability，并由single generation或该exact
identity正式支持的native extension完成；adapter不得把另一个Provider接到take中间。只有显式
`HARD_CUT` continuity edge才允许使用已经对exact grade与directed pair完成认证的destination capability。
`SCENE_BOUNDARY`只表示叙事或剪辑结构已经换场，不能自动推导continuity reset：若新场景仍延续同一主角、
服装、道具或强视觉风格，policy必须保留exact identity/style carryover references并通过普通QA；只有
scene/time/state已经由approved intent显著重置、且没有残余carryover义务的boundary，才可标记为
`SUBSTANTIAL_RESET`并获得近似自由的显式Provider portability。一个方向、一个boundary kind、一个reset
classification或一个destination通过，不得外推为反向、其他model/profile或全局“无缝切换”。

## Current Runtime Truth

当前代码已经提供以下可复用边界：

- `VideoGenerationRequest.image_bindings` 与 `VideoImageReferenceBinding` 能表达 `first_frame`、`last_frame` 或普通 `reference` 图像，并将图像 bytes hash、MIME、尺寸和大小纳入 request fingerprint。
- `VideoCapabilityVariant` 能声明 allowed image roles、required first frame、数量、格式、大小和尺寸限制；`ResolvedVideoGenerationRequest` 会在 Provider submit 前 fail closed。
- `ProductionStateCommitter` 能对 fetched video candidate 执行 measured probe、provenance sealing、Project/Registry/graph atomic activation、exact replay 和 explicit recovery。
- P5 resolver 能基于 immutable typed graph 做 precise transitive invalidation，且 `Shot.continuity_constraints` 已进入 Shot visual projection fingerprint。
- P3/P4 仍由唯一的 `ResolvedTimeline` 和唯一的 HyperFrames renderer 负责 frame/sample/timing/render。

当前实现进一步提供：

- `ContinuityReferenceBinding`把普通`first_frame`扩展为source Shot/candidate/generation、terminal extraction receipt、exact PNG bytes和continuity constraint snapshot的sealed lineage；fetched MP4 provenance可共同激活derived terminal PNG。
- P5 graph只在显式terminal-image input存在时建立typed asset-to-generation edge，并沿真实closure做precise invalidation。
- `LocalVideoSubmitIntent`、submit/status/fetch receipts与one-use local permit形成独立于Paid Provider Gate的durable local evidence chain；local与remote evidence不得混合。
- `ComfyUIVideoProvider`只接受sealed profile列出的literal loopback endpoint，在R+1前验证ComfyUI commit、四个model components、native node inventory、template/binding/profile hashes与output bounds；任何mismatch均在上传或submit前fail closed，且无remote fallback。
- `C4MultiAnchorBinding`、`ContinuityMode.MULTI_ANCHOR`、C4 requirement contract v2、request/resolved
  C4 fields与activation scope已把exact terminal、identity、approved endpoint和optional/exact motion tail
  纳入canonical hash、Registry lineage与reopen validation。
- C4 Router已将`continuity_terminal`、`approved_endpoint`、`identity`、
  `continuity_motion_tail`分别投影为`first_frame`、`last_frame`、`reference`、
  `reference_video`，并要求同一个selected capability满足static三角色或motion四角色exact grammar；
  不允许组合FL2VA与Ref2VA子能力。
- Hailuo 2.3 continuity payload现已有Alice C2 adaptive one-submit canonical technical acceptance；Seedance
  2.0 Mini已有一次first-frame I2V paid attempt，但结果被用户因identity与camera continuity拒绝并保持
  unactivated。任一结果都不能外推为C4、其他Provider或multi-provider transition acceptance。

当前C4缺口集中在Provider implementation与live/quality evidence：

- Local T8-native V2只提供互斥的`T2VA`、`I2VA`、`FL2VA`与`Ref2VA`children；没有独立
  `Hybrid` C4 child、workflow/binding/profile或Production capability seal。
- T8 Hybrid conditioning能够在packing层同时表达first、last、reference image与reference video，但
  尚无AI-VIDEO full four-anchor local generation、decoded boundary、identity、motion或P6 evidence。
- stock Ref2VA能否可靠消费first/last conditioning尚未证明；existing Hybrid artifact builder验证的是
  exact pruned FL2VA/Ref2VA pair，而当前本机库存为non-pruned pair且没有sealed Hybrid artifact。
- 当前pinned ComfyUI没有upstream `MiniMaxH3AddGuide`；即使未来受控升级，conditioning placement也不
  证明selected checkpoint同时遵循四类anchors。
- Seedance 2.0、2.0 Fast与2.0 Mini分别声明frame I2V和multimodal reference task family，但啊
本次增量冻结以下target scope：

1. 建立`C4_NATIVE_BOUNDARY_MOTION`与`C4_SEMANTIC_MULTI_REFERENCE`两个不可互换的产品等级。
2. 为Local T8 Hybrid定义独立C4 destination child、exact four-role grammar、profile/artifact seals和
   Stock20 qualification gates；不扩宽现有FL2VA或Ref2VA identity。
3. 建立provider-neutral `ContinuityTransitionPolicy`逻辑合同，区分`WITHIN_CONTINUOUS_TAKE`、
   `HARD_CUT`与`SCENE_BOUNDARY`，再独立绑定`FULL_CONTINUITY`、`IDENTITY_STYLE_CARRYOVER`或
   `SUBSTANTIAL_RESET`义务，冻结每种有效组合的Provider affinity、reference、QA与failure behavior。
4. 定义有向pair certification，使任意已P6接受、可派生exact terminal/motion evidence的source lane，
   只有在destination capability通过对应grade时才可进入该destination。
5. 保留Hailuo 2.3 first-frame continuity和Seedance 2.0 family的model-specific边界；当前accepted
   Seedance target只包含已购买的base `doubao-seedance-2-0-260128`。Fast/Mini只保留compatibility
   comparison，除非fresh entitlement/inventory明确纳入，不得进入active capability snapshot。在formal
   cross-mode evidence缺失时全部继续fail closed。
6. 允许未来优先为已购买的base `doubao-seedance-2-0-260128`建立独立semantic multi-reference
   capability，但不得把semantic opening/ending references描述为native first/last boundary，也不得
   作为C4失败后的自动降级。

Provider-specific payload、model naming、duration/resolution 限制不得进入 provider-neutral core model。

## Non-Goals

本 slice 不做以下事情：

- 不新增第二 timeline、第二 renderer、第二 state writer 或通用 Agent runtime。
- 不把 crossfade、插帧、optical flow、prompt 文案复用或剪辑遮挡描述为完整 continuity solution。
- 不改变 Legacy CLI、Legacy layout、public CLI commands、default no-network 或 local-first policy。
- 本spec task不实施runtime、不调用local/cloud video Provider、不产生付费行为、不mint/consume permit，
  也不增加local失败后的cloud fallback。
- 不把“多Provider切换”实现为runtime ranking、automatic retry、model substitution或best-effort fallback。
- 不声称任意source/destination组合、反向组合或未认证profile已经可流畅切换。
- 不把adapter的field mapping、codec/FPS normalization或shared transport描述为不同模型的identity、motion、
  camera dynamics、style或latent-state等价。
- 不允许在`WITHIN_CONTINUOUS_TAKE`中途替换Provider；失败时只能显式重生成整个take，或先由authoring
  revision增加visible hard cut再按新boundary contract创建attempt。
- 不把`SCENE_BOUNDARY`本身解释为continuity清零；仍延续的主角、服装、道具、palette或强style必须携带
  exact references并过普通QA，只有显式`SUBSTANTIAL_RESET`才允许近似自由Provider portability。
- 不升级ComfyUI、不安装/融合checkpoint、不构建Hybrid artifact，也不在第一版启用Turbo LoRA。
- 不修改P8 provider contract，不把target Provider child、transition certification或semantic capability写成
  已实现runtime truth。
- 默认不增加 dependency、CLI、Manifest schema 或 artifact layout。
- 不把三张静态图、prompt中的identity/camera描述、adapter可序列化字段、另一个mode的reference能力或多个capability的并集伪装成C4 motion continuity。
- 不把v7历史reviewer verdict、SSIM、Provider success或fetched artifact重新解释为C4 acceptance。

## Ownership and Invariants

### Timing Ownership

`ResolvedTimeline` 继续是唯一 order、frame、sample 和 Shot-boundary timing owner。Terminal-frame extraction 使用已测量 video metadata 和 resolved source span，但不得建立另一套 canonical timing、Shot order 或 duration 推导。

### Durable State Ownership

`ProductionStateCommitter` 继续是唯一 durable writer、candidate activation 和 recovery owner。Terminal-frame evidence、下游 request binding 与相应 Project/Registry/graph activation 必须通过这一 façade 所拥有的 transaction boundary 持久化；reader、Registry、dependency resolver、Provider adapter 和临时 extraction helper 均不得成为第二 writer。

### Dependency Ownership

继续使用唯一 P5 dependency graph builder、resolver 和 selective rebuild decision。Continuity 只能增加必要的 typed dependency input，不能在 graph 中复制 timeline 或维护另一份 mutable lifecycle truth。

### Render Ownership

继续使用唯一 HyperFrames renderer。Continuity conditioning 在 Provider generation 之前完成；renderer 只消费已激活 visual assets 和唯一 `ResolvedTimeline`，不负责修补生成素材的语义跳变。

### Transition Boundary Ownership

Approved Shot/sequence intent定义是否要求unbroken take或visible editorial cut，并逐项声明跨边界仍需保留
或已经显著重置的identity、wardrobe、props、style、scene/time/state与motion义务；`ResolvedTimeline`继续
独占actual Shot boundary timing。Planner只把该approved intent投影为provider-neutral
`ContinuityTransitionPolicy`，Router只执行其中的provider affinity、carryover reference与certification
gate。Provider adapter、family aggregator、analyzer与renderer不得推断、放宽或改写boundary kind、
continuity obligation或reset classification，也不得因为某个Provider失败而自行插入cut、重分Shot、改变
take范围或宣称换场已经清零continuity。

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

## C4 Multi-Anchor Motion Continuity Contract

`C4_MULTI_ANCHOR_MOTION_CONTINUITY`是现有C1 terminal continuation、C2 hard-cut keyframe和future C3 reference-to-video之上的additive continuity tier。C1/C2/C3历史request、hash、reopen与acceptance边界保持不变；只有显式声明C4的new attempt使用本节contract。

### Static and Motion Tiers

C4必须分别通过两个不可合并的验收层：

1. `C4_STATIC_BOUNDARY`：同一次generation严格包含exact upstream terminal `first_frame`、独立canonical identity `reference`与approved exact future `last_frame`。该层约束切点像素/站位、人物/发型/服装/关键prop identity以及目标停止姿态，但不证明motion continuity。
2. `C4_MOTION_BOUNDARY`：在完整`C4_STATIC_BOUNDARY`上再增加exact upstream motion tail `reference_video`。只有该层通过才可称`C4_MULTI_ANCHOR_MOTION_CONTINUITY`完成；三张静态图即使都存在也不能满足该层。

任一anchor缺失、重复、role错误、排序非canonical、bytes tampered、lineage stale、materialization不完整或capability无法同时表达全部bindings时，resolution必须fail closed且external-effect count为零。

### Semantic Boundary State

C4 attempt只有在target Shot已达到`contract_ready`时才可构造。其semantic continuity snapshot必须明确：

- `open_state`：exact terminal pixels/站位，加motion tail末段的gait/action phase、subject velocity、camera direction与camera velocity；
- `must_hold`：canonical face/hair/body identity、服装、关键prop（本lane包括red satchel）、scene/light/color、camera axis与screen direction；
- `changes_here`：只允许Shot contract批准的继续运动、可见减速与停止，不得以frame reset、无因果转身或camera jump完成；
- `close_state`：approved endpoint中的主体姿态、接触关系、screen position/scale、camera endpoint、FOV与停止后的inertia/prop state。

v7应按`F-ID-DRIFT`、`F-CAMERA-PATH`/`F-CONTINUITY`归因到asset/reference、Shot contract、platform capability与motion conditioning layers；不得默认通过堆叠prompt同义词修复。Skill建议只帮助形成上述semantic snapshot，不能成为anchor或acceptance evidence。

### Exact Anchor Set

每个C4 input必须由一个strict anchor binding同时记录semantic role与provider-native role：

| Semantic role | Native binding role | Required identity |
| --- | --- | --- |
| `continuity_terminal` | `first_frame` | accepted upstream video的exact `TerminalFrameEvidence`与extracted PNG |
| `identity` | `reference` | 独立canonical Character identity asset，不能由terminal、endpoint或scene plate兼任 |
| `approved_endpoint` | `last_frame` | exact target-Shot future stop-pose asset与human approval/feasibility evidence |
| `continuity_motion_tail` | `reference_video` | 从同一accepted upstream video精确派生的content-addressed尾段MP4/MOV |

每个anchor都必须seal：

- exact Asset Registry `asset_id`、selected Registry revision/pointer、asset SHA-256、MIME、byte size与measured dimensions；video tail另含duration、FPS与frame count；
- semantic role、native role、target Shot revision/content hash与canonical ordering position；
- source provenance receipt identity/hash；identity anchor另含canonical Character ID/revision/content hash；
- provider materialization receipt identity/hash，绑定exact provider/profile/capability、local asset identity与provider materialized identity；不得持久化signed URL或raw credential；
- anchor binding schema/version与canonical content hash，并进入requirement、provider-bound request、egress preview、one-use permit和resolved generation fingerprint。

Remote Provider必须为四个inputs分别提供exact materialization receipt；Seedance只能通过`SeedanceAssetMaterializationReceipt`和`SeedanceAssetReferenceResolver`或后续同等严格、单一canonical owner的compatible extension导出`asset://`identity。Local Registry ID、filename、prompt handle或adapter-local path不得伪装成Provider materialization。

### Motion Tail Evidence

`continuity_motion_tail`必须从已经activated且由P6接受的upstream generated-video artifact派生，不能来自review derivative、unactivated fetch、prompt preview或另一个take。其content-addressed evidence至少绑定：

- exact source Shot revision/content hash、source video asset ID/SHA-256、Registry revision、generation/resolved/provenance identity与P6 acceptance evidence；
- selection rule/version、start/end rational timestamps、inclusive start/end frame indices、source FPS与selected frame count；
- tail必须以`TerminalFrameEvidence.frame_index`结束，并与terminal anchor共享同一source video SHA-256；
- deterministic extractor/tool identity、canonical arguments、extraction receipt hash；
- extracted tail bytes SHA-256、MIME、size、measured width/height/FPS/duration/frame count；
- target Shot、continuity constraint snapshot与motion-tail evidence canonical hash。

Tail duration不由Skill heuristic固定；它必须在selected Provider正式duration bounds内，并长到足以包含至少两个连续motion transitions。Selection range任何变化都必须改变requirement/permit fingerprints并触发真实P5 downstream closure；exact replay不得重复tail extraction、materialization或Provider effect。

### Approved Endpoint Feasibility

`approved_endpoint`不是普通storyboard still。它必须绑定target Shot、exact output duration、C4 terminal/identity/motion-tail identities和一个content-addressed feasibility receipt，并在Provider preview前逐项通过：

- `camera axis`：endpoint保持accepted axis/camera side，或显式声明由Shot contract批准的可见轴线变化；不得镜像或猜测；
- `screen direction`：subject displacement与upstream motion tail的signed direction一致，除非Shot contract明确要求可见减速、转身或反向；
- `subject scale`与`FOV`：endpoint occupancy、camera distance/angle与sealed FOV policy相容，不能通过无解释的scale jump实现构图；
- `reachable displacement`：根据tail末段measured subject/camera velocity envelope、target duration与sealed acceleration/deceleration bounds，endpoint位置可达；
- `no teleport`：不存在单帧位置跳变、unmotivated camera translation/zoom或超出reachable envelope的姿态切换。

自动backend无法可信评估axis、identity、FOV或reachable displacement时必须返回`NOT_EVALUATED`并要求exact-bound human feasibility evidence；不得把prompt、bounding-box相似或SSIM猜成PASS。只有全部required checks有`PASS`或policy-allowed human conclusion时，endpoint才可成为C4 input。

### Provider Capability and Router Gate

Router只能选择一个exact capability variant；不得把I2V、FL2VA、Ref2VA或V2V几个variants的能力做并集。完整C4 motion variant至少必须同时声明：

- selected mode可以在一个native request中同时表达`first_frame`、`last_frame`、`reference`与`reference_video`；
- `allowed_image_roles`包含上述三个image roles，`VideoMediaCapability`显式允许一个motion-tail video；
- static boundary capability的`VideoBindingCardinalityConstraint`必须对`first_frame=1`、`last_frame=1`、`reference=1`、`reference_video=0`、`reference_audio=0`和all-role total `=3`形成exact grammar；motion boundary capability必须在同一semantic contract上要求`reference_video=1`和all-role total `=4`；
- capability seal明确证明native `reference_video`在该mode中承载continuity motion tail，而不是仅style/reference advisory；
- image/video MIME、size、geometry、duration、output、audio与materialization bounds全部满足。

`requirement_bindings()`必须保持semantic role与exact asset的一一对应，Router provider-bound projection必须deterministic且prompt-free；`VideoGenerationRequest`仍按唯一canonical image/media ordering序列化。缺失/重复/错序或capability cardinality mismatch必须在adapter compiler、paid preview、permit mint/consume和POST之前拒绝，不允许T2V fallback、prompt fallback、Provider fallback或伪造mixed capability。

当前Seedance 2.0 family model-specific profiles只分别证明I2V的`first_frame + last_frame`和
reference-mode的reference/media surfaces，尚未证明一个native request中的完整C4组合。
`SeedanceVideoProvider._payload()`能输出`reference_image`不构成formal evidence。只有exact
model/profile的dated official API contract、request schema/example与offline compiler tests共同证明完整
组合后，才可新增独立C4 capability seal；若formal contract不能证明，必须保留现有seal并在Paid
Provider preview/POST前fail closed。

### Ownership and Compatibility

- Skill只提供continuity/prompt/camera advisory；AI-VIDEO继续独占Character/Shot artifacts、capability、Registry identity、materialization、paid lifecycle、review/repair与acceptance truth，`runtime_skill_calls = 0`保持不变。
- `ProductionStateCommitter`、Production Manifest、Asset Registry、Dependency Graph、`ResolvedTimeline`、HyperFrames与existing Paid Provider recovery ownership保持不变；C4不得新增writer、timeline、activation owner、automatic recovery或Provider fallback。
- New C4 requirement/request/evidence schema必须additive；C1/C2/C3与legacy T2V/I2V/R2V requests在C4 fields缺失时保持bit-for-bit historical hash/reopen semantics。
- P5只沿四个exact input asset/evidence edges传播到target generation与真实composition/render closure；unlinked Shots、voice、captions与无关assets保持fresh。

## Controlled Multi-Provider Transition Contract

### Adapter Boundary and Model Non-Equivalence

Provider adapter只负责把provider-neutral requirement deterministic投影到一个exact native capability，并
统一transport、lifecycle、provenance、output probe/normalization与typed failure。它不能证明两个模型共享
conditioning interpretation、identity representation、motion/camera priors、color/style distribution或
hidden generation state。即使provider/model/profile相同，独立generation attempts也必须通过exact media
bindings与P6 evidence重新证明continuity；provider affinity只能减少一个drift来源，不能单独产生quality
PASS。

公开Provider API目前交换的是text、image、video、audio、task/profile与encoded output等observable
artifacts。Native last-frame chaining或video extension可以把observable upstream state交给同一exact model，
但不得描述为跨模型latent-state transfer。Output resolution、FPS、codec、color或audio normalization只能解决
composition compatibility，不能修复identity、pose、camera velocity或style discontinuity。

### Boundary Kinds and Provider Affinity

每个可能改变Provider的edge必须由immutable、provider-neutral `ContinuityTransitionPolicy`绑定approved
authoring intent、exact source/target Shots、resolved boundary identity、一个结构性`boundary_kind`与一个
独立的`continuity_obligation`。结构换场和连续性重置是两个不同事实：

| Boundary kind | Required continuity obligation | Provider rule | Allowed strategy and claim |
| --- | --- | --- | --- |
| `WITHIN_CONTINUOUS_TAKE` | `FULL_CONTINUITY` | exact provider/model/profile/capability锁定 | single generation，或该exact identity formal capability支持的native extension；不得cross-provider |
| `HARD_CUT` | 通常为`FULL_CONTINUITY`；若approved intent只保留较弱义务，必须显式降为`IDENTITY_STYLE_CARRYOVER` | full continuity的cross-provider必须有fresh directed pair certification；carryover仍需exact references与普通QA | C4 handoff只声明该exact cut与direction；较弱carryover不得冒充C4 |
| `SCENE_BOUNDARY` | 必须显式选择`IDENTITY_STYLE_CARRYOVER`或`SUBSTANTIAL_RESET` | 不能因换场自动解除affinity；carryover必须验证destination reference能力，reset才允许ordinary explicit selection | carryover只声明identity/style continuity；reset只声明近似Provider portability，不产生motion continuity claim |

`IDENTITY_STYLE_CARRYOVER`必须列出非空`required_carryover_dimensions`，其允许值至少覆盖
`character_identity`、`wardrobe`、`hero_props`、`visual_style`与`palette`，并为每个维度绑定exact Registry
reference/materialization identity及普通QA rubric。它不要求C4 motion tail，但不得只靠prompt复述替代
reference binding。`SUBSTANTIAL_RESET`必须绑定approved scene/time/state reset evidence，并要求
`required_carryover_dimensions`为空；只要同一主角、同一服装、hero prop、强style或其他显著状态仍被要求
延续，就不能使用该classification。

Logical policy至少绑定`boundary_kind`、`continuity_obligation`、`required_carryover_dimensions`、对应exact
reference identities、source/target Shot与revision、source exact provider identity、requested destination
identity、continuity grade、visible-cut/reset authoring evidence、allowed continuation strategy、QA policy、
policy version与canonical content hash。`WITHIN_CONTINUOUS_TAKE`还必须绑定整个take的exact Shot/span
membership；只修改take membership、visible-cut/reset decision、carryover dimension/reference、
provider/model/profile/capability、QA policy或strategy任一项都必须改变hash。

Router enforcement必须发生在adapter compiler、preview、permit mint/consume与Provider effect之前：

- `WITHIN_CONTINUOUS_TAKE`收到不同destination identity时zero-effect denial；
- `HARD_CUT + FULL_CONTINUITY`跨Provider但缺fresh exact pair certification时zero-effect denial；
- `SCENE_BOUNDARY + IDENTITY_STYLE_CARRYOVER`缺少任一required exact reference、destination不支持对应role或
  普通QA未通过时不得activation，也不得伪造C4 transition certification；
- `SCENE_BOUNDARY + SUBSTANTIAL_RESET`仍有非空carryover dimension、缺reset evidence或与approved
  Character/Scene/Shot intent冲突时zero-effect denial；
- boundary kind、continuity obligation或reset classification缺失、组合无效、与approved Shot/timeline
  evidence冲突或被tamper时fail closed。

### Source and Destination Responsibilities

`HARD_CUT` multi-provider continuity transition是有向关系，不是Provider名称列表。Source lane只负责产出已经activated、
由P6接受且可派生exact `TerminalFrameEvidence`与`C4MotionTailEvidence`的upstream video；它不需要原生
支持C4 input grammar。Destination lane必须由一个selected capability在同一次native generation中完整
消费所选continuity grade的全部bindings，并独立完成自身output、lifecycle与quality gates。

因此首个Local T8 C4 child完成后，可以认证：

```text
accepted H3 / Hailuo / Seedance / future source
    -> exact terminal + motion-tail derivation
    -> Local T8 C4 destination
```

这只适用于approved `HARD_CUT`。它不会自动认证`Local T8 -> Seedance`、`Local T8 -> Hailuo`、任意反向
路径、`WITHIN_CONTINUOUS_TAKE`或任意provider-to-provider组合。只有destination自身拥有相同grade的
sealed capability并通过独立证据时，对应hard-cut direction才成立。

### Continuity Product Grades

Provider切换必须显式选择以下grade之一：

| Grade | Required native request semantics | Allowed claim |
| --- | --- | --- |
| Grade E — `C4_NATIVE_BOUNDARY_MOTION` | exact `first_frame=1`、`last_frame=1`、`reference=1`、`reference_video=1`，由同一selected capability消费 | native exact-role boundary + identity/motion reference，仍需decoded output与P6 evidence |
| Grade S — `C4_SEMANTIC_MULTI_REFERENCE` | opening、ending、identity与motion作为semantic reference roles；Provider可以把它们映射为多个reference images/video | semantic opening/ending/identity/motion guidance，不保证native first/last roles或pixel-exact boundary |

`native exact-role boundary`只证明exact input bytes进入Provider的native boundary role，不等于decoded
frame 0或terminal frame与输入pixel-identical。Pixel similarity、identity adherence和motion adherence必须
分别测量并由P6/human evidence裁决。Grade E失败时不得自动改为Grade S；二者必须使用不同capability
ID、request contract、UI/product label、acceptance rubric与quality record。

### Pairwise Certification

每个可声明的有向transition必须拥有immutable、content-addressed
`ProviderTransitionCertification` evidence。其逻辑内容至少绑定：

- exact source provider、model、profile、capability与accepted output provenance；
- exact destination provider、model、profile、capability、workflow/binding及artifact identities；
- exact `ContinuityTransitionPolicy`、`boundary_kind=HARD_CUT`、
  `continuity_obligation=FULL_CONTINUITY`、visible-cut authoring evidence与source/target real Shot identities；
- source/destination continuation strategies；`WITHIN_CONTINUOUS_TAKE`与`SCENE_BOUNDARY`不得使用该
  certification冒充hard-cut continuity；
- selected continuity grade、canonical anchor contract/version与exact cardinality；
- input derivation/materialization policy、output normalization/probe contract与composition compatibility；
- technical、live smoke、boundary、identity、motion、human/P6 rubric和evidence identities；
- certification status、actor/policy identity、created time与canonical content hash。

该evidence只证明一个directed pair和一个exact profile snapshot。它不是Provider router、mutable lifecycle、
capability registry或第二acceptance owner；Production Manifest、`ProductionStateCommitter`、selected
capability snapshot和P6继续拥有各自canonical truth。Model、workflow、binding、artifact、node schema、
sampler、output contract或rubric任一identity变化，都必须生成新的certification，不得原地改写。

在没有全部directed pairs的独立certification前，产品只能显示具体已认证路径，例如
`Seedance 2.0 -> Local T8 C4`，不得显示笼统的“All Providers Seamless”。

### Selection, Downgrade, and Failure

- Planner/Router必须显式接收destination capability或由已批准policy做deterministic selection；selected
  provider/model/profile/capability与grade必须进入resolved identity。
- Router只能从fresh capability snapshot中选择单个、完整满足当前grade的variant。它不得根据OOM、
  latency、artifact缺失、previous success或quality score在attempt中换child。
- capability denial、profile drift、materialization failure、unknown outcome或quality rejection都保持当前
  attempt blocked/failed；不得自动选择另一个Provider、较低grade、Turbo/Stock alternative或cloud lane。
- 用户或Planner可以创建一个新的显式attempt选择其他已认证lane；新attempt必须拥有自己的intent、
  budget/egress（如适用）、permit、provenance与acceptance evidence，不能复用失败attempt的effect token。
- 若失败发生在`WITHIN_CONTINUOUS_TAKE`，new attempt只能使用一个exact identity重生成整个sealed take，
  或先由approved authoring revision把take拆出visible `HARD_CUT`再创建新attempt；不得从失败frame开始换
  Provider续接，也不得由runtime自动改变take membership。
- “boundary-aware portability”只表示provider-neutral semantics、exact evidence、deterministic routing、
  durable lifecycle、recovery与composition contract在approved boundary上保持稳定；它不承诺零等待、
  零成本、跨模型视觉等价或未经真实Shot/P6验收的主观连续性。

## Provider-Specific Profiles

### Official Upstream Workflow Baseline

Local H3 `fl2va` lane 的 reviewed upstream baseline 是 Comfy-Org 官方 I2V workflow，而不是本机 raw smoke 时临时拼装的节点图：

- repository：`Comfy-Org/workflow_templates`；
- pinned commit：`0e0f4577453136eaa1c0e9d4b700e3e5ce5bb416`；
- path：`templates/video_minimax_h3_i2v.json`；
- pinned URL：`https://github.com/Comfy-Org/workflow_templates/blob/0e0f4577453136eaa1c0e9d4b700e3e5ce5bb416/templates/video_minimax_h3_i2v.json`；
- raw JSON SHA-256：`313b029321a8be303e827dad471bff3022ca564c8bf8c6198a3e70b65c599671`；
- upstream repository license：MIT；
- official core node：ComfyUI core `MiniMaxH3ImageToVideo`，接受必需的 `first_frame` 和 optional `last_frame`；
- model components：`minimax_h3_fl2va_pruned_int8_convrot.safetensors`、`qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`、`minimax_h3_video_vae_fp16.safetensors` 与 `minimax_h3_audio_vae_fp32.safetensors`。

该官方文件是 UI/subgraph workflow，只证明reviewed节点图与上述model components的compatibility baseline；它不能原样进入AI-VIDEO production loader，也不拥有或替代AI-VIDEO的Manifest、Registry、`TerminalFrameEvidence`、P5 invalidation、candidate activation/recovery或exact replay lifecycle。

项目派生版本必须保留可reopen的upstream provenance，并以结构化清单记录相对pinned raw JSON的全部有意修改。派生规则如下：

- reviewed/export为deterministic API-format JSON；
- 删除UI-only notes、demo input asset与非必需的subgraph/UI metadata；
- optional LoRA、remote refiner与任何cloud fallback默认关闭，且不得隐藏在profile外被自动启用；
- 保留官方native H3 conditioning、sampling、video/audio decode与MP4 output contract；
- 将exact terminal PNG bytes绑定为`MiniMaxH3ImageToVideo.first_frame`；只有request与sealed profile都显式要求时才绑定`last_frame`，不得静默增加或删除；
- `fl2va`与`ref2va`保持不同workflow/profile identity，不得合并成一个profile或共享checkpoint identity。

官方workflow后续更新不会自动改变sealed production profile。任何upgrade必须选择新的exact upstream commit/path/hash/license，重新review并记录derived diff，重新seal derived workflow、binding与profile hashes，并重新通过offline及后续单独授权的acceptance gates；未完成resealing时继续使用当前pinned baseline或fail closed。

### Local Continuity Lane

Local H3 `fl2va` production lane现由`workflows/templates/minimax_h3_fl2va_api.json`、`workflows/bindings/minimax_h3_fl2va_binding.yaml`与`workflows/profiles/minimax_h3_fl2va.json`固定。Profile seal official upstream provenance、derived workflow SHA-256 `c736a12f35fd89f10a8db86f0769a85ca7bceb80d16feab62a1666cfd078737b`、binding SHA-256 `e0ae28bdaaa81ac70578b11e97f95cacab826273ec09f82bfcf430176fb05a4c`、ComfyUI commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`、四个model component hashes、native node inventory、literal loopback endpoint、24fps、17k+5 frame-grid、124-362 trained frame boundary、native audio与MP4 output bounds；profile content hash为`456b59c7a907d4b07c7d951d63ec03cbd0fb5c64638dbc8dad870aca09e2b604`。

Local live proof的exact run path、artifact hashes、probe measurements、Manifest revision与replay receipt
由runtime baseline和durable records拥有。本normative spec只保留约束：Shot B必须消费Shot A exact
terminal bytes，candidate/terminal activation与reopen必须成功，exact replay不得增加submit，失败的
diagnostic attempt不得计入accepted proof或blind retry。

Local H3的profile边界如下：

- 已实现的`fl2va` continuity profile：将exact upstream terminal PNG绑定到`MiniMaxH3ImageToVideo.first_frame`；只有request显式提供时才在deterministic节点图中保留`last_frame`。它是多Shot terminal-to-entrance continuity的最小本地闭环。
- 尚未实现的optional `ref2va` identity profile：未来可通过`MiniMaxH3ReferenceToVideo`消费显式reference image/video/audio，用于角色、场景、服装或表演参考。它不能替代exact terminal-frame lineage，也不能与`fl2va`共用checkpoint identity。

仅提高现有smoke workflow的`length`只会生成一个更长的单Shot，不构成跨Shot continuity。H3 node虽然允许更长frame count，但其文档训练区间约为124-362 frames；超出该范围必须作为独立quality/performance risk报告，不能因为schema允许而宣称已支持。

### Local T8 Hybrid C4 Destination

首个`C4_NATIVE_BOUNDARY_MOTION` destination必须作为Local H3 provider family下的独立child实现，不能
扩宽现有`FL2VA`或`Ref2VA`capability。Provider-neutral request继续使用：

```text
generation_mode = IMAGE_TO_VIDEO
continuity_mode = MULTI_ANCHOR
```

`task_type = Hybrid`只属于T8 provider-native compiler/profile，不得新增模糊的通用`HYBRID`
generation mode。Family只聚合capabilities并按exact selected child dispatch，不拥有durable state、quality
selection或runtime fallback；`VideoGenerationService`与`ProductionStateCommitter`继续拥有intent、
permit、submit/status/fetch、candidate、activation、recovery与replay。

第一版motion child的binding grammar固定为：

| Role | Cardinality | T8 native mapping |
| --- | ---: | --- |
| `first_frame` | exactly 1 | Hybrid conditioning `first_frame` |
| `last_frame` | exactly 1 | Hybrid conditioning `last_frame` |
| `reference` | exactly 1 | `ref_images.ref_image_0` |
| `reference_video` | exactly 1 | `ref_videos.ref_video_0` |
| `reference_audio` | exactly 0 | absent |
| all roles | exactly 4 | one selected capability |

第一版`reference_video`只承载visual motion/action reference，不隐式携带soundtrack；
`ref_video_audios`与`ref_audios`必须为空。Static C4如未来需要，必须使用独立capability ID和exact
three-role grammar，不能让同一个variant同时接受模糊的三/四角色shape。

#### Model Qualification Gates

Model strategy必须以两个sequential、offline qualification gates收敛；它们不是production runtime
fallback，也不能同时出现在一个active capability snapshot：

1. `M0 — stock Ref2VA control`：以stock Ref2VA、T8 Hybrid conditioning、Stock20、
   `dual_clock_euler`、`native_flow`、Turbo off执行完整四锚点control，回答stock checkpoint是否能在
   保留reference adherence时可靠消费first/last conditioning。
2. `M1 — sealed FL2VA×Ref2VA Hybrid artifact`：只有M0未通过预先冻结的technical/boundary/identity/
   motion gates时才进入。Artifact必须由exact validated model pair和content-addressed recipe构建；现有
   builder的validated pruned-pair边界不得静默扩宽到当前non-pruned inventory。

只有一个candidate通过full local smoke与quality gates后，才可进入Production capability snapshot。
Candidate identity必须揭示真实model treatment，例如：

```text
minimax-h3-t8-c4-motion-ref2va-stock20-v1
minimax-h3-t8-c4-motion-hybrid-stock20-v1
```

不得在同一capability ID下从stock Ref2VA替换为Hybrid artifact。第一版固定Stock20并关闭Turbo LoRA；
Turbo只能在Stock20完整通过后以独立profile、独立capability ID和same-input controlled comparison重新
验收，不能静默改变sampling trajectory或quality variable。

#### Profile and Artifact Seals

Production profile至少seal exact T8/ComfyUI commit与license、required node inventory/input schema、
source model pair、selected checkpoint或Hybrid artifact及sidecar/recipe identity、CLIP/text encoder、
video/audio VAE、workflow/binding/profile hashes、Stock20 sampler/shift/frame grid、resolution、frame count、
FPS、native audio/output node/final filename rule、literal loopback endpoint，以及
`remote_provider_enabled=false`、`cloud_fallback_enabled=false`。

Hybrid artifact build属于显式Provider inventory preparation，不属于每次generation attempt。Build
receipt必须绑定source model hashes、builder/recipe/version、tensor contract、output artifact/sidecar hashes
与license/provenance；runtime只允许reopen、rehash、verify和consume。Missing/tampered artifact不得触发
auto-build、auto-repair、stock substitution、cloud fallback或第二套Production recovery。Artifact recovery
不改变`ProductionStateCommitter`对attempt lifecycle的唯一ownership。

以下任一条件必须在permit consumption与ComfyUI POST之前fail closed：role缺失/重复/多余或错序、
anchor/Registry/provenance/materialization mismatch、endpoint approval/feasibility不完整、motion tail没有以
exact terminal结束、task type不是literal `Hybrid`、reference audio意外连接、model/artifact/node schema/
workflow/binding/profile drift、Stock20参数漂移、output ambiguity、非loopback endpoint或任何remote/cloud/
fallback配置。

### Cost Control and Provider Portability

Shot Continuity必须保持“一个provider-neutral lifecycle，多个显式provider lanes”。以下contract在Local H3、Hailuo、Seedance与未来Provider之间复用，不得在adapter内复制：

- `ContinuityConstraintSet`、`TerminalFrameEvidence`与`ContinuityReferenceBinding`；
- exact request/resolved fingerprints、candidate provenance与terminal artifact identity；
- Manifest 2.8 activation/recovery、exact replay与same-desired failure rules；
- P5 continuity dependency、precise downstream invalidation；
- P3/P4唯一composition/timeline/audio/caption/final mux ownership。

切换Provider不是只替换`model_id`。每个lane仍必须提供并独立验收：

- concrete adapter/transport；
- exact capability variant，例如`first_frame`、`last_frame`、reference、native audio、duration、resolution与container；
- provider-specific workflow/profile或cloud payload mapping；
- local resource policy或remote Paid Provider Gate/Cloud Egress；
- output parsing、measured validation、error normalization与live/quality evidence。

任何lane不支持当前continuity request时必须在submit前fail closed；不得删除`last_frame`/reference、退化为T2V、改用另一个model或fallback到cloud。Provider selection必须显式并进入resolved identity。

Local H3的成本控制角色是低边际成本draft lane，而不是自动替代最终cloud lane。推荐production policy：

1. 在本地H3上迭代prompt、continuity constraints、terminal-to-first-frame binding、camera/motion entrance与reference选择。
2. 使用本地technical/visual gate淘汰明显断裂的候选；失败不消耗remote quota。
3. 只有显式选中的Shot才进入Hailuo/Seedance等付费lane，并继续使用exact budget reservation、egress authorization与one-use submit permit。
4. Remote lane必须重新完成自身live artifact和subjective quality gate；Local H3成功不能证明另一个model会产生相同构图、动作、身份一致性或音频。

这一路由可以减少付费prompt/reference调试和无效重试，但不能把本地GPU时间、电力、RAM/VRAM占用记作零成本，也不能让自动router在未授权时选择remote Provider。是否从local draft升级到paid final必须是显式production decision，并保留两个generation identities与各自provenance。

### MiniMax Cloud Hailuo 2.3

MiniMax 官方 I2V contract当前列出`MiniMax-Hailuo-2.3`，以`first_frame_image`接收首帧；
adapter已offline验证独立I2V mapping且不声明`last_frame`。Representative adaptive request的task ID、
artifact hash、probe、similarity metric与human review结论只记录在runtime baseline、exact receipts和
experiment records；本spec只约束exact activated keyframe consumption、canonical
activation/reopen/recovery与zero-effect replay。其它model的first/last-frame示例不得外推为Hailuo
2.3支持未声明的`last_frame`。

References:

- [MiniMax Image-to-Video API](https://platform.minimax.io/docs/api-reference/video-generation-i2v)
- [MiniMax Video Generation Guide](https://platform.minimax.io/docs/guides/video-generation)
- [MiniMax Models](https://platform.minimax.io/docs/guides/models-intro)

### Seedance 2.0 Family

当前capability table分别覆盖`doubao-seedance-2-0-260128`、
`doubao-seedance-2-0-fast-260128`与`doubao-seedance-2-0-mini-260615`的model-specific modes。官方
capability matrix分别声明first/last-frame
I2V和image/video/audio multimodal reference，但没有给出一个exact model-specific schema/example/receipt
证明frame roles与reference roles可在同一native request中cross-mode union。因此三个型号当前均不得注册
`C4_NATIVE_BOUNDARY_MOTION` capability：

Code中的default capability matrix表示adapter理解的provider maximum，不证明当前account已购买、已部署
或已授权全部model。当前accepted inventory只包含base `doubao-seedance-2-0-260128`；Fast与Mini即使
接口文档存在，也必须在fresh entitlement、pricing与exact endpoint/profile evidence齐全后才可进入active
capability snapshot。Capability discovery不得把“官方支持”或“代码中有entry”误写成“本账户可用”。

#### Shared Transport, Separate Model Contracts

三者可以复用同一类Ark async task transport和AI-VIDEO `SeedanceVideoProvider` adapter：相同的submit/
status/fetch lifecycle、`model + content[]` request envelope、image/video/audio role serialization、Paid
Provider Gate、materialization与unknown-outcome recovery seam。这里的“shared interface”只表示transport
shape和adapter code path可以复用，不表示三个model是drop-in interchangeable capability。

每个model/mode必须拥有独立`SeedanceCapabilityProfile`与capability ID，至少分别seal：

- exact logical `model_id`、actual `api_model_id`或endpoint deployment identity、expected response model；
- exact mode与allowed role grammar，不能使用`seedance-2.0`family wildcard；
- output resolution/ratio/raster、duration/timing mode、FPS、container与native audio bounds；
- reference image/video/audio counts、individual/aggregate duration与materialization bounds；
- profile version、pricing snapshot/upper bound、egress preview、one-use permit与resolved request hash；
- model-specific offline compiler tests、live receipt和quality/P6 evidence。

当前代码与官方matrix显示的主要差异如下；future provider drift必须通过fresh matrix/profile update重新seal，
不能静默沿用本表：

| Exact model | Service class | Output contract | Reference bounds in current profile | Interchange rule |
| --- | --- | --- | --- | --- |
| `doubao-seedance-2-0-260128` | enhanced/base | 480p/720p/1080p/4k, 4–15s, 24fps, MP4 | up to 9 images, 3 videos, 3 audios, 15s family media limit | primary purchased 2.0 target; owns independent profile/pricing/evidence |
| `doubao-seedance-2-0-fast-260128` | basic/fast | 480p/720p, 4–15s, 24fps, MP4 | up to 9 images, 3 videos, 3 audios, 15s family media limit | cannot inherit base output, price, capability or quality acceptance |
| `doubao-seedance-2-0-mini-260615` | basic/mini | 480p/720p, 4–15s, 24fps, MP4 | up to 9 images, 3 videos, 3 audios, 15s family media limit | cannot inherit base/Fast acceptance; historical rejection remains model-specific |

Provider selection切换这三个model时必须创建新的resolved identity和attempt。Request若不满足selected exact
profile，必须在paid preview/permit/POST前拒绝；adapter不得因为另一个2.0 family profile接受该shape就
改写model ID、删减roles、改变resolution/duration或使用另一份pricing。Response返回的model identity必须
与submission binding一致，否则按provider mismatch fail closed。

Model isolation acceptance至少覆盖：

- capability snapshot在entitlement不包含Fast/Mini时只暴露base 2.0 target；discovery不得因default
  matrix存在而自动启用其他models；
- base、Fast与Mini的capability/profile/request hashes互不相同，family alias和cross-model profile reuse
  必须拒绝；
- base-only 1080p/4k request绑定Fast/Mini时在preview/permit/POST前拒绝，effect count为零；
- missing/stale model-specific pricing、wrong endpoint deployment或response model mismatch均fail closed；
- 一个model的offline/live/quality acceptance不能满足另一个model的certification或transition matrix entry；
- 切换exact model必须创建新attempt，重新完成pricing、egress、permit、provenance与P6 evidence。

| Model | Native first+last task | Image+video reference task | Exact four-role union | Semantic grade |
| --- | --- | --- | --- | --- |
| Seedance 2.0 | separately declared | separately declared | not proven; fail closed | future explicit capability |
| Seedance 2.0 Fast | separately declared | separately declared | not proven; fail closed | future explicit capability |
| Seedance 2.0 Mini | separately declared | separately declared | not proven; fail closed | future explicit capability |

Adapter能够序列化`first_frame`、`last_frame`、`reference_image`或`reference_video`只证明字段mapping，
不证明selected model/mode接受它们的union。现有I2V profiles继续保持`first_frame + optional last_frame`且
`max_reference_count=0`；reference/edit/extend profiles继续保持reference media contract，不得由Router
拼接成虚假的combined capability。

已购买的base Seedance 2.0可以未来新增独立`C4_SEMANTIC_MULTI_REFERENCE` capability，将opening
composition、ending composition和canonical identity分别作为semantic image references，将motion作为
`reference_video`。该contract必须明确opening/ending不是native `first_frame`/`last_frame`，不得宣称
pixel-exact boundary，也不得作为Grade E失败后的fallback。Seedance 2.0 Fast与2.0 Mini只有在各自exact
profile被显式纳入available inventory并完成相同formal evidence与quality gates后，才可获得独立semantic
capability；Fast或Mini identity本身不扩大binding grammar。

`SeedanceAssetMaterializationReceipt`与`SeedanceAssetReferenceResolver`继续独占already-materialized
Ark identity导出并拒绝local Registry ID伪装`asset://`；缺少exact active materialization evidence时
必须在authorization/permit/submit前fail closed。此前Seedance 2.0 Mini paid attempt只证明一次
first-frame I2V submit/fetch lifecycle，且用户因identity与camera continuity拒绝、candidate保持
unactivated；它不能外推为四锚点technical或quality proof。

任何bounded cross-mode discovery probe必须是未来独立授权的single POST、lowest valid cost、no retry、
no fallback attempt。HTTP/schema acceptance最多证明transport/schema reachability；仍需检查roles是否被
实际遵循，并重新完成boundary、identity、motion与P6 gates后才能seal capability。

References:

- [BytePlus LAS Enhanced Video Generation](https://docs.byteplus.com/en/docs/Byteplus_LAS/video_gen_enhanced)
- [Volcengine Doubao Seedance 2.0 Series Tutorial](https://www.volcengine.com/docs/82379/2291680?lang=zh&sessionid=)

## Artifact and Provenance Lifecycle

1. Source video candidate 必须先通过现有 measured validation 和 provenance sealing。
2. Terminal extraction 必须读取由 committer transaction 持有并重新验证的 exact source bytes；路径 reopen 后必须再次验证 containment、type、size 和 hash。
3. Extraction 输出必须先进入 immutable, content-addressed candidate evidence，再与 source candidate identity 和 downstream binding 一起由 `ProductionStateCommitter` durable commit/activate。
4. 临时文件只可作为 transaction-local scratch；不得被 request、Registry、Manifest 或 Provider receipt 直接引用，成功或恢复后也不得成为唯一 evidence。
5. reopen/recovery 必须从 durable evidence 验证 image hash、metadata、source candidate 和 downstream binding；tampered、unreadable、symlink escape、wrong source Shot 或 wrong Registry revision 全部 fail closed。
6. 相同 source candidate、selection rule、extractor contract 和 continuity constraints 的 exact replay 必须返回相同 evidence，不重复 extraction 或 durable writes。

已授权并实现的Manifest 2.8 compatible extension允许candidate activation在同一`ProductionStateCommitter` transaction中共同append generated video与derived terminal PNG Registry assets，并保存terminal extraction/evidence pointer。Local evidence pointer只在local attempt中出现，remote 2.8 serialization保持原有shape；reader与recovery拒绝local/remote evidence混合、tampered pointer或不一致的Project/Registry/graph tuple。该extension没有新增第二writer、Registry schema version、公共CLI或artifact layout。

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

当前实现与后续lane必须持续覆盖：

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

Local H3 measured evidence必须证明terminal extraction与next-Shot input exact binding，并保留probe、
frame-integrity和side-by-side artifacts。具体PSNR/SSIM、resolution、frame count与analyzer output进入
runtime baseline或exact record，不在本normative spec固化；任何该类evidence都只满足technical
live-local proof，不能替代blinded human rubric或宣称subjective quality accepted。

### Acceptance Tiers

1. `technical acceptance`：Fake/offline executable contracts、local artifact verification、replay/recovery/P5 tests 和 composition invariants 全部通过。
2. `provider live proof`：每个明确 provider/model/profile 通过 separately authorized 的真实 submit/fetch/activation/replay proof；成功只证明该 lane 的 connectivity、payload 和 durable lifecycle，不自动外推到其他 provider。
3. `subjective continuity/quality acceptance`：对 terminal/initial pairs 与最终序列完成 blinded human review，并满足预先定义的 scene、character、camera、motion、lighting/color 和 spatial-storytelling rubric。

三层必须分别报告。Technical acceptance 不等于 live proof，live proof 也不等于 subjective quality acceptance。

C4在上述三层之外还必须把static boundary与motion boundary拆开报告：

1. `static boundary acceptance`逐项检查exact terminal-to-first-frame、canonical identity、approved endpoint、axis、screen direction、subject scale/FOV与stop-pose feasibility；
2. `motion boundary acceptance`逐项检查upstream gait/action phase、subject velocity、camera direction、camera velocity、deceleration/stop behavior以及cut前后full-speed playback。

SSIM/PSNR只可作为边界像素相似度evidence，不能替代identity或motion视觉判断。Reviewer verdict、automatic analyzer与human/user review必须保留各自来源；用户对identity或camera continuity的明确rejection使对应C4 subjective dimension失败，即使technical tests、Provider lifecycle或其他reviewer通过。

### Real Shot Generation Verification

Fixture/unit tests、fake transport、synthetic color cards、isolated calibration anchors、workflow load与一次
single-boundary smoke只能关闭各自technical gate，不能关闭live、continuity quality、destination promotion或
multi-provider claim。`C4_DESTINATION_READY`及其以上层级必须消费真实项目Shot generation evidence：

- 使用一个明确selected的`ProductionProject` revision及其中canonical Character、Scene、Shot artifacts；每个
  input必须来自exact Asset Registry revision、materialization/provenance receipt与approved Shot intent，不能
  用临时未登记图片、prompt-only角色描述或合成占位素材代替；
- destination promotion至少生成3–4个叙事连续的真实Shots和至少2个continuity edges，固定同一canonical
  主角与场景，并至少覆盖一个可见subject-motion handoff和一个camera-motion handoff；单个四锚点smoke不
  足以证明跨Shot累计稳定性；
- 每个generation只使用一个exact selected provider/model/profile/capability、一次submit、no blind retry、
  no fallback；生成结果在P6/human acceptance前保持candidate/unactivated；
- 每个edge分别绑定exact terminal、identity、endpoint、motion-tail、decoded output与policy hashes；逐edge
  评估后还必须以原速连续播放整段，检查identity、wardrobe、style、camera velocity、action phase与空间关系的
  累积漂移；
- review素材必须保留raw hard cuts，不得用crossfade、optical flow、frame interpolation、速度变化、重构图或
  其他后期处理隐藏generation discontinuity；可另行制作comparison derivative，但不能替代raw evidence；
- `SCENE_BOUNDARY + IDENTITY_STYLE_CARRYOVER`必须在真实换场Shot上证明所有required dimensions均有exact
  references且通过普通QA；`SUBSTANTIAL_RESET`必须由真实scene/time/state变化与approved intent证明，而不是
  因为换了Provider或模型效果差而事后标记；
- 首个`ProviderTransitionCertification`必须来自两个canonical real Shots之间的visible `HARD_CUT +
  FULL_CONTINUITY`，并使用真实accepted source output派生anchors；synthetic-only pair、历史rejected或
  unactivated output不能满足；
- `SAME_GRADE_MULTI_DESTINATION_READY`必须让各destination消费同一real-Shot validation set与同一frozen
  rubric；不同故事、不同角色或更容易的fixture不能用于横向替代。

Implementation、Provider media与P6 evidence必须绑定同一或可证明byte-identical的sealed
`validation_snapshot`。任何model/artifact、workflow、binding、profile、policy、reference set、fixture或
rubric变化都会使受影响的真实Shot evidence失去promotion资格并要求重跑；Harness receipt不能替代该gate。

### Multi-Provider Claim Levels

Completion与产品声明必须按以下层级报告，不能用较低层替代较高层：

1. `C4_CORE_READY`：provider-neutral binding/request/resolved/hash/Router exact grammar与negative tests通过。
   当前代码已达到该offline层级。
2. `C4_DESTINATION_READY`：一个exact destination child通过profile preflight、fake lifecycle、full
   four-anchor local/live smoke、activation/reopen/replay，并对同一sealed snapshot完成3–4个canonical real
   Shots、至少2个edges的原速Pilot、boundary/identity/motion和P6/human acceptance。Local T8 Hybrid是首个
   target，但当前尚未达到。
3. `DIRECTED_TRANSITION_READY`：一个source与一个不同destination provider的exact pair拥有fresh
   `ProviderTransitionCertification`，且证据来自canonical real Shots之间的visible
   `HARD_CUT + FULL_CONTINUITY`；可声明该具体方向，例如`Seedance 2.0 -> Local T8 C4`。
4. `SAME_GRADE_MULTI_DESTINATION_READY`：同一provider-neutral grade至少有两个不同destination
   providers的sealed capabilities，使用同一real-Shot validation set与frozen rubric分别通过，并完成
   deterministic selection、denial、reopen与no-fallback tests。只有达到此层才能声称“在已认证visible
   hard-cut directions上具备同等级boundary-aware Provider portability”。
5. `FULL_MATRIX_READY`：每个对外声称支持的directed pair都拥有独立certification。没有完整矩阵时不得
   声称“任意Provider双向无缝切换”；即使完整矩阵通过，`WITHIN_CONTINUOUS_TAKE`仍禁止cross-provider，
   `SCENE_BOUNDARY`仍必须根据carryover或reset classification执行对应reference与QA合同。

Local T8 C4 child完成只会把系统推进到`C4_DESTINATION_READY`；加入至少一个不同source pair后可达到
`DIRECTED_TRANSITION_READY`。它不会单独达到`SAME_GRADE_MULTI_DESTINATION_READY`，因为Seedance
2.0 family和Hailuo当前都没有已证明的Grade E destination capability。

### C4 Destination Verification Matrix

首个destination至少必须完成以下gates：

| Gate | Required evidence |
| --- | --- |
| Inventory | exact plugin/ComfyUI/model/artifact/node/profile hashes与license/provenance |
| Cardinality | exact 1 first + 1 last + 1 identity image + 1 motion video；缺失、重复、多余、错序和sub-capability union全部拒绝且effect count为零 |
| Workflow/compiler | literal `Hybrid`、exact node bindings、empty reference audio、deterministic payload order与output mapping |
| Lifecycle | one-use local permit、submit/status/fetch、unknown-outcome recovery、candidate activation、reopen与exact replay zero effects |
| Four-anchor smoke | one request、one selected model/profile、one submit、no retry、no fallback，记录全部input/output/request/profile/artifact hashes |
| Boundary policy | `WITHIN_CONTINUOUS_TAKE`跨Providerzero-effect denial；hard-cut full continuity缺pair certification拒绝；scene carryover缺reference/QA拒绝；scene reset缺approved reset evidence拒绝 |
| Real Shot Pilot | selected ProductionProject revision中的3–4个canonical Shots、至少2 edges、同一sealed snapshot、逐edge evidence与raw full-speed cumulative-drift review |
| Boundary | decoded frame 0与terminal frame分别对比native first/last；报告measurement，不把native role夸大为pixel identity |
| Identity | first/middle/last windows检查face/subject、hair、clothes、props、body scale与multi-frame drift；不足时`NOT_EVALUATED` |
| Motion | subject/camera direction与velocity、action phase、entrance/exit、unexpected stop/re-entry；单帧SSIM不得代替 |
| P6/Human | exact request/output/anchors、technical/strategy/semantic evidence与human verdict共同形成Final Acceptance |
| Harness | task-owned exact staged snapshot或commit range的fresh passing receipt；Harness不替代live media或P6 |

所有阈值、fixture、rubric与candidate identities必须在观看结果前冻结。同一candidate未通过full matrix时
保持`experimental / unavailable`；quality rejection不得因transport success、hash closure或单一metric
改写为accepted。

## Bounded Hybrid Continuity Evaluator V1

2026-08-22 的 Option A 授权增加一个 local/no-network evaluator slice。该 slice 可以把
`numpy>=1.26,<3` 与 `onnxruntime>=1.20,<2` 提升为 Production runtime dependency，并允许
Manifest-compatible durable validation checkpoint；授权不包含网络访问、模型下载、媒体生成、
Provider 调用或 quality-acceptance claim。

### Visual Backend Profile

自动判定 motion direction、entrance、exit 与 unexpected re-entry 必须建立在 exact sampled
RGB frames、subject detections 和跨帧 track identity 上。Production adapter 只接受 sealed
`continuity-visual-profile/1`，其中至少固定 evaluator/config hash、sampler identity与sample geometry、
exact NumPy/ONNX Runtime identity、detector 与
ReID ONNX bytes hash/size、明确的 tensor I/O contract、detector class allowlist、tracker algorithm/
threshold version，以及 CPU-only `onnxruntime` execution provider。模型 path 是 local resolution，
不得进入 semantic hash；runtime 必须在建立 session 前重算 exact bytes hash/size。MCP、remote
Provider、credential、implicit model discovery 与 network fallback 全部禁止。

当前仓库和本机 ComfyUI model inventory 没有可直接验收的 general subject detector + ReID asset
pair；现有 face-only ONNX 不能替代通用 subject tracking。因此 implementation 可以 executable-test
profile、adapter、track measurements 与 fail-closed behavior，但在真实模型文件按许可、来源、exact
hash/profile 提供并单独验证前，不得声明 live automatic visual capability。

### Measurement and Verdict Contract

- evaluator 输出 exact artifact/frame/profile-bound raw measurements，不包含 verdict；最终 verdict
  仍只由 `adjudicate_generated_shot_continuity()` 派生。
- motion/entrance/exit/re-entry 只有在单一 dominant track、连续 coverage、confidence 和稳定性均
  达到 sealed profile gate 后才可 `match` 或 `mismatch`；低 coverage、遮挡、ambiguous tracks、
  unsupported constraint grammar 或不可信 model output 必须 `not_evaluated`。
- entrance 与 exit 必须由 signed subject occupancy/track state 推导；absolute frame difference、edge
  activity 或单一 centroid 不能作为 action direction 证据。
- unexpected re-entry 必须证明同一 track identity 已 exit 后再次出现；没有可信 ReID continuity 时
  必须 `not_evaluated`。
- identity、camera axis 与 framing 在没有各自可信 reference/pose/geometry backend 时保持
  `not_evaluated` 并转 human fallback；不得根据 detector label、bounding box 或 prompt 猜测通过。
- human fallback 是独立 authorized evidence source。Automatic incomplete evidence 本身不能 PASS，
  也不能把 human conclusion 伪装成 model observation。

### Durable Validation Checkpoint

`ProductionStateCommitter` 仍是唯一 writer。Continuity evaluator 完成并通过 exact request/policy/
artifact/constraints/evaluator binding 后，其 content-addressed evidence 必须在 candidate preparation
之前写入 immutable artifact，并由 Manifest attempt 保存 canonical pointer。`VALIDATE` retry/recovery
只能 reopen、rehash 和 re-adjudicate该 exact evidence；不得再次运行 frame sampler、ONNX evaluator
或 human fallback。Tampered、wrong-request、wrong-policy、wrong-profile、wrong-artifact 或 stale evidence
全部 fail closed。历史 Manifest 2.8 与历史无 raw-measurement evidence 必须保持可读；只有包含新 pointer
的 attempt 才要求下一 compatible Manifest schema。

## Assumptions and Unresolved Decisions

- C4 provider-neutral contract、Router grammar与canonical lifecycle owners视为本实现slice的unchanged
  contract；只有concrete child接入测试证明真实缺口时，才允许最小core修正。
- M0 stock Ref2VA与M1 Hybrid artifact谁成为Production candidate尚未决定，只能由同一fixture、预先冻结
  rubric和full four-anchor evidence决定，不能由payload unit tests或主观预期决定。
- `ProviderTransitionCertification`的exact persisted schema/layout尚未决定。Implementation plan必须先
  证明它能复用现有immutable evidence与Manifest pointer patterns；若需要Manifest/artifact layout migration，
  必须单独通过对应Decision Gate，不得由本spec暗含授权。
- `ContinuityTransitionPolicy`当前冻结的是logical contract；exact persisted schema/layout尚未决定。实现必须
  首先证明可由现有approved Shot/sequence intent、ResolvedTimeline identity与immutable evidence seam表达。
  若需要Project、Manifest或artifact migration，必须另过Decision Gate。实现不得把`SCENE_BOUNDARY`硬编码成
  `SUBSTANTIAL_RESET`，也不得在policy缺失时由Router或adapter猜测carryover dimensions。
- Seedance frame/reference cross-mode union仍是unknown/unsupported-for-seal。只有formal Provider
  evidence或未来bounded probe能改变该model/profile结论；一次2xx不能直接改变grade。
- T8 `MiniMaxH3AddGuide`迁移、non-pruned Hybrid builder研究与Turbo qualification均属于后续独立
  scope；它们不是首个Stock20 C4 destination的隐含dependency。
- Boundary、identity与motion的numerical thresholds、fixture和human rubric必须在live smoke前由
  implementation plan/QA policy冻结；本spec不允许看到candidate后再降低门槛。

## Authorization Boundary

2026-08-19 Local MiniMax H3 `fl2va` two-Shot proof由当时任务单独授权并完成。2026-08-20用户先对Alice C2 Hailuo 2.3与Seedance 2.0 Mini各最多一次remote submit作出独立task-scoped authorization，随后以“全部授权继续”批准解决已报告blocker所需的新bounded adaptive Hailuo request。该request已消费一次submit并完成canonical lifecycle；Seedance fresh budget已满足但仍因egress materialization gate保持零submit。两项lane都不扩展为blind retry、其他model/provider、`ref2va`、Shot Router或额外benchmark；任何后续live execution仍必须重新满足exact provider/model、预算、Cloud Egress与Paid Provider one-use permit。

2026-08-22 v7 Seedance paid submit已经被该attempt消费，且result被用户拒绝并保持unactivated。本轮只授权
canonical spec与plan更新，不授权runtime implementation、local/cloud generation、paid preview/POST、permit
mint/consume或media quality claim。未来loopback local ComfyUI C4 smoke按repository local-unmetered
execution contract无需重复请求task-scoped authorization，但仍必须通过sealed profile、preflight、local
permit、唯一committer、recovery与media verification gates；任何remote/paid C4 probe仍必须在
implementation、tests、formal capability evidence、fresh Harness与native independent review完成后，取得
新的task-scoped authorization、fresh budget/egress decision和新的one-use permit。旧v7 authorization/
permit/receipt不得复用。

## Rollback

未来 continuity implementation 必须可按 provider lane 删除：移除continuity-specific child capability/
payload mapping与active pair certification后，旧P8 T2V/I2V/R2V request、candidate activation、
static-image path、generated-MP4 composition和P3/P4/P5 ownership必须恢复到当前行为。移除一个
destination child不得改变其他lane identity、自动选择replacement或把Grade E request降为Grade S。
已存在的terminal/motion/transition/provider artifacts应保持immutable、可审计但不再被active graph/
capability snapshot选择；不得通过删除历史receipts完成rollback。
