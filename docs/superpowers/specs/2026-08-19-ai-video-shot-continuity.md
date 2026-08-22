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

Accepted normative contract。本规范是Shot Continuity唯一canonical spec，拥有provider-neutral continuity、
C4 multi-anchor、boundary-aware Provider portability、execution-stack identity、transition qualification与
per-attempt evidence的长期语义；不拥有当前实现、live readiness、账户entitlement、模型库存、exact hashes、
历史run或quality verdict。

动态状态必须从`docs/v0.2-runtime-baseline.md`、active Provider profile/capability snapshot、Production
Manifest、exact receipts与`docs/record_for_agent/`读取。Frontmatter中的有限状态字段只用于Documentation
Contract Gate索引，不授权把正文变成runtime dashboard，也不构成Production、quality、push或release证明。

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
`WITHIN_CONTINUOUS_TAKE`必须锁定同一个`execution_stack_hash`，并由single generation或该exact stack
正式支持的native extension完成；adapter不得把另一个execution stack接到take中间。只有显式
`HARD_CUT` continuity edge才允许使用已经对exact grade、source/destination stacks与适用风险范围完成
qualification的destination capability。
`SCENE_BOUNDARY`只表示叙事或剪辑结构已经换场，不能自动推导continuity reset：若新场景仍延续同一主角、
服装、道具或强视觉风格，policy必须保留exact identity/style carryover references并通过普通QA；只有
scene/time/state已经由approved intent显著重置、且没有残余carryover义务的boundary，才可标记为
`SUBSTANTIAL_RESET`并获得近似自由的显式Provider portability。一个方向、一个boundary kind、一个reset
classification、qualification或一个destination通过，不得外推为反向、其他execution stack、其他
content/risk class或全局“无缝切换”。

## Runtime Truth Routing

本规范只定义must/shall contracts。以下易变事实不得写入本规范正文：

- 当前branch/commit、implemented/live/quality/release状态；
- 本机或账户可用的Provider、model、checkpoint、LoRA、plugin、workflow与entitlement；
- exact workflow/binding/profile/model/artifact hashes、node inventory、sampler参数与runtime版本；
- historical attempt、provider task ID、artifact measurement、human verdict与authorization consumption；
- 当前blocker、实验winner、benchmark、pricing与budget snapshot。

这些事实分别由runtime baseline、active capability/profile snapshot、content-addressed inventory/build
receipts、Production Manifest/P6 evidence和exact experiment records拥有。Implementation plan可以规定如何
获取fresh snapshot，但不得把dated observation提升为本规范的长期前提。

## Scope

本规范冻结以下accepted scope：

1. 建立`C4_NATIVE_BOUNDARY_MOTION`与`C4_SEMANTIC_MULTI_REFERENCE`两个不可互换的产品等级。
2. 为任何concrete C4 destination定义独立child、exact role grammar、execution-stack seal与qualification
   gate；不得扩宽另一个mode或拼接多个sub-capabilities。
3. 建立provider-neutral `ContinuityTransitionPolicy`逻辑合同，区分`WITHIN_CONTINUOUS_TAKE`、
   `HARD_CUT`与`SCENE_BOUNDARY`，再独立绑定`FULL_CONTINUITY`、`IDENTITY_STYLE_CARRYOVER`或
   `SUBSTANTIAL_RESET`义务，冻结每种有效组合的Provider affinity、reference、QA与failure behavior。
4. 定义`GenerationExecutionStackIdentity`、可复用`ProviderTransitionQualification`与单次
   `TransitionAttemptEvidence`，让Router能在submit前查询bounded qualification，并在执行后保存exact edge
   evidence。
5. 保持所有Provider/model/mode的capability isolation；shared adapter或transport不得证明model
   interchangeability、cross-mode union或quality acceptance。
6. 把真实Shot generation与Human/P6设为Critical acceptance path；automatic evaluator仅为High/
   experimental evidence source，不阻塞首个destination或directed qualification。

Provider-specific payload、model naming、duration/resolution 限制不得进入 provider-neutral core model。

## Non-Goals

本 slice 不做以下事情：

- 不新增第二 timeline、第二 renderer、第二 state writer 或通用 Agent runtime。
- 不把 crossfade、插帧、optical flow、prompt 文案复用或剪辑遮挡描述为完整 continuity solution。
- 不改变 Legacy CLI、Legacy layout、public CLI commands、default no-network 或 local-first policy。
- 不把“多Provider切换”实现为runtime ranking、automatic retry、model substitution或best-effort fallback。
- 不声称任意source/destination组合、反向组合或未qualification的execution stacks已经可流畅切换。
- 不把adapter的field mapping、codec/FPS normalization或shared transport描述为不同模型的identity、motion、
  camera dynamics、style或latent-state等价。
- 不允许在`WITHIN_CONTINUOUS_TAKE`中途替换Provider；失败时只能显式重生成整个take，或先由authoring
  revision增加visible hard cut再按新boundary contract创建attempt。
- 不把`SCENE_BOUNDARY`本身解释为continuity清零；仍延续的主角、服装、道具、palette或强style必须携带
  exact references并过普通QA，只有显式`SUBSTANTIAL_RESET`才允许近似自由Provider portability。
- 不修改P8 provider contract，不把target Provider child、qualification或semantic capability写成已实现
  runtime truth。
- 除已批准的 P0 qualification-prepared persistence seam 外，不增加 dependency、CLI、Manifest schema 或
  artifact layout；该 seam 只选择 immutable preparation evidence，不表达 winner、capability activation 或 verdict。
- 不把三张静态图、prompt中的identity/camera描述、adapter可序列化字段、另一个mode的reference能力或多个capability的并集伪装成C4 motion continuity。
- 不把historical reviewer verdict、SSIM、Provider success或fetched artifact重新解释为C4 acceptance。

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
`ContinuityTransitionPolicy`，Router只执行其中的provider affinity、carryover reference与qualification
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

Provider分别声明frame task与reference task不证明一个native request中的完整C4 union。Adapter payload能
同时序列化字段也不构成formal capability evidence。只有exact model/deployment/profile的dated official
contract、request schema/example、offline compiler tests及必要的bounded live proof共同覆盖完整组合后，
才可新增独立C4 capability seal；否则必须保留较窄seal并在preview/POST前fail closed。

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

对于只暴露text、image、video、audio、task/profile与encoded output等observable artifacts的
Provider API，native last-frame chaining或video extension可以把observable upstream state交给同一exact model，
但不得描述为跨模型latent-state transfer。Output resolution、FPS、codec、color或audio normalization只能解决
composition compatibility，不能修复identity、pose、camera velocity或style discontinuity。

### Generation Execution Stack Identity

Provider名称、`model_id`或capability ID都不足以定义生成分布。每个selected generation必须解析为一个
immutable、hash-bound `GenerationExecutionStackIdentity`，其canonical payload至少包含：

```text
GenerationExecutionStackIdentity
├── provider_kind / deployment identity
├── model_id
├── capability_id
├── materialization_status        # unmaterialized | materialized
├── profile_hash
├── compiler_hash
├── workflow_hash                 # if applicable
├── checkpoint / artifact hashes # ordered; includes LoRA or fusion artifact
├── sampler / scheduler identity  # if applicable
├── runtime / plugin seals
├── output contract hash
└── execution_stack_hash
```

尚未物化的candidate必须使用`materialization_status=unmaterialized`，并将`profile_hash`、
`compiler_hash`与`workflow_hash`统一记为`none`；这个identity只能封存P0 candidate contract，不得解释为
executable stack。首次真实执行前必须绑定reopenable profile/compiler以及applicable workflow identity，
更新为`materialized`并产生新`execution_stack_hash`，同时重新seal依赖该hash的policy与receipt。
其他不适用字段必须使用versioned canonical empty representation；secret、local path和credential不得进入hash。
Remote Provider无法暴露checkpoint等内部状态时，stack必须绑定可验证的deployment/model/profile/API contract，
并把opaque service drift记录为qualification limitation，而不是伪造内部seal。

`execution_stack_hash`必须进入resolved request、attempt intent、Provider provenance、qualification与replay
validation。Checkpoint、LoRA、artifact、compiler、workflow、sampler/scheduler、plugin/runtime或output
contract任一有效identity变化都产生新stack；“仍是同一个Provider”不得绕过该变化。

### P0 Qualification-Prepared Persistence

P0 使用 Manifest `2.11` 的单一 optional `active_p0_qualification_prepared` pointer 选择一份 immutable、
content-addressed preparation bundle。Bundle 只允许包含 exact Project/Registry pointers、两个有序 candidate
stack identities、`ContinuityTransitionPolicy` 集合、`RealShotValidationSet`、inventory、calibration fixture、
rubric、effect budget、human freeze evidence 与明确 limitations。`ProductionStateCommitter` 是唯一 writer；
exact replay 必须 zero-write，recovery 必须 reopen 全部 selected artifacts，Project 或 Registry identity 变化必须
使 selected pointer 失效。

Calibration fixture 必须封存 source image geometry 与 model-facing tensor contract。当前 Local T8 P0 fixture
固定 exact `7:4` source、`1344x768` canvas、32-pixel dimension multiple、`BHWC [1,768,1344,3]`、normalized
float image tensor与确定性等比 resize semantics；source 与 target aspect ratio 不一致时 fail closed，不得隐式
拉伸或裁切后继续。该 contract 只证明输入可确定性表达，不证明模型输出质量。

H3 prompt必须使用 current OpenVideo/H3 three-field grammar：conditioning instruction（存在 first/last/reference/
reference-video 时）、`integrated_multimodal_description`、`overall_soundscape` 与
`non_diegetic_music`。画面字段必须 style-first，并明确 camera type/amplitude/speed与可见动作；prompt不得替代
任何 exact anchor binding，也不得只用抽象氛围词声称 continuity。

GPT Image 2 MCP/browser output 通过独立 `AutomatedBrowserImageImportReceipt` 记录 automation actor、human approval
actor、exact PNG bytes/dimensions、timestamps 与 prompt fingerprint；未知 backend model/request ID 必须保持
`None`，不得复用 `HumanImageImportReceipt` 或持久化 signed source URL。

### Boundary Kinds and Provider Affinity

每个可能改变Provider的edge必须由immutable、provider-neutral `ContinuityTransitionPolicy`绑定approved
authoring intent、exact source/target Shots、resolved boundary identity、一个结构性`boundary_kind`与一个
独立的`continuity_obligation`。结构换场和连续性重置是两个不同事实：

| Boundary kind | Required continuity obligation | Provider rule | Allowed strategy and claim |
| --- | --- | --- | --- |
| `WITHIN_CONTINUOUS_TAKE` | `FULL_CONTINUITY` | exact `execution_stack_hash`锁定 | single generation，或该exact stack formal capability支持的native extension；不得cross-stack |
| `HARD_CUT` | 通常为`FULL_CONTINUITY`；若approved intent只保留较弱义务，必须显式降为`IDENTITY_STYLE_CARRYOVER` | full continuity的cross-stack transition必须有fresh bounded qualification；carryover仍需exact references与普通QA | C4 handoff只声明该exact cut与direction；较弱carryover不得冒充C4 |
| `SCENE_BOUNDARY` | 必须显式选择`IDENTITY_STYLE_CARRYOVER`或`SUBSTANTIAL_RESET` | 不能因换场自动解除affinity；carryover必须验证destination reference能力，reset才允许ordinary explicit selection | carryover只声明identity/style continuity；reset只声明近似Provider portability，不产生motion continuity claim |

`IDENTITY_STYLE_CARRYOVER`必须列出非空`required_carryover_dimensions`，其允许值至少覆盖
`character_identity`、`wardrobe`、`hero_props`、`visual_style`与`palette`，并为每个维度绑定exact Registry
reference/materialization identity及普通QA rubric。它不要求C4 motion tail，但不得只靠prompt复述替代
reference binding。`SUBSTANTIAL_RESET`必须绑定approved scene/time/state reset evidence，并要求
`required_carryover_dimensions`为空；只要同一主角、同一服装、hero prop、强style或其他显著状态仍被要求
延续，就不能使用该classification。

Logical policy至少绑定`boundary_kind`、`continuity_obligation`、`required_carryover_dimensions`、对应exact
reference identities、source/target Shot与revision、source/requested destination `execution_stack_hash`、
continuity grade、visible-cut/reset authoring evidence、allowed continuation strategy、QA policy、
policy version与canonical content hash。`WITHIN_CONTINUOUS_TAKE`还必须绑定整个take的exact Shot/span
membership；只修改take membership、visible-cut/reset decision、carryover dimension/reference、
execution stack、QA policy或strategy任一项都必须改变hash。

Router enforcement必须发生在adapter compiler、preview、permit mint/consume与Provider effect之前：

- `WITHIN_CONTINUOUS_TAKE`收到不同`execution_stack_hash`时zero-effect denial；
- `HARD_CUT + FULL_CONTINUITY`跨stack但缺fresh applicable qualification时zero-effect denial；
- `SCENE_BOUNDARY + IDENTITY_STYLE_CARRYOVER`缺少任一required exact reference、destination不支持对应role或
  普通QA未通过时不得activation，也不得伪造C4 transition qualification；
- `SCENE_BOUNDARY + SUBSTANTIAL_RESET`仍有非空carryover dimension、缺reset evidence或与approved
  Character/Scene/Shot intent冲突时zero-effect denial；
- boundary kind、continuity obligation或reset classification缺失、组合无效、与approved Shot/timeline
  evidence冲突或被tamper时fail closed。

### Source and Destination Responsibilities

`HARD_CUT` multi-provider continuity transition是有向stack关系，不是Provider名称列表。Source lane只负责产出已经activated、
由P6接受且可派生exact `TerminalFrameEvidence`与`C4MotionTailEvidence`的upstream video；它不需要原生
支持C4 input grammar。Destination lane必须由一个selected capability在同一次native generation中完整
消费所选continuity grade的全部bindings，并独立完成自身output、lifecycle与quality gates。

因此任何directed transition都必须被理解为：

```text
accepted source execution_stack_hash
    -> exact terminal + motion-tail derivation
    -> qualified destination execution_stack_hash
```

这只适用于approved `HARD_CUT`。它不会自动证明反向路径、`WITHIN_CONTINUOUS_TAKE`、同Provider但不同
checkpoint/workflow的stack，或任意provider-to-provider组合。只有destination stack拥有相同grade的sealed
capability并通过独立qualification时，对应hard-cut direction才成立。

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

### Reusable Transition Qualification

`ProviderTransitionQualification`是可复用、bounded的有向stack-pair capability evidence，不是某一个Shot
edge的验收记录。其logical content至少绑定：

- exact source与destination `execution_stack_hash`；
- `boundary_kind=HARD_CUT`、selected continuity grade与anchor contract/version；
- versioned applicable content/risk class或等价machine-readable applicability predicate；
- frozen rubric、validation-set identity与构成该set的technical/live/boundary/identity/motion/P6 evidence；
- input derivation/materialization、output normalization/probe与composition compatibility contracts；
- known limitations、unsupported conditions、validity/staleness rules、actor/policy identity与content hash。

Applicability至少必须能限制subject count/identity burden、occlusion、wardrobe/style obligation、shot scale、
subject/camera motion regime、duration与其他会显著改变continuity risk的维度。Router只能在target Shot落入
qualification envelope时使用；unknown或out-of-envelope必须fail closed，不能把一次简单validation pair外推
到所有内容。

Qualification builder消费explicit qualification-validation intent下产生的exact real-Shot generation与P6
evidence；在qualification seal完成前，这些validation runs不能授权普通Production routing。Stack、grade、
rubric、applicability classifier、normalization或关键limitation任一变化都产生新qualification identity。

### Per-Attempt Transition Evidence

每次真实Production edge必须生成独立、immutable `TransitionAttemptEvidence`，至少绑定：

- exact source Shot/revision、accepted source output与source `execution_stack_hash`；
- exact target Shot/revision与selected destination `execution_stack_hash`；
- exact `ContinuityTransitionPolicy`、anchors、request/resolved hashes与materialization receipts；
- exact `ProviderTransitionQualification` identity及本Shot落入其applicability envelope的proof；
- output/probe/provenance、QA measurements、human evidence与P6 verdict；
- attempt/result identity、created time与canonical content hash。

Qualification回答“这个stack pair在这个bounded class下是否有资格被选”；attempt evidence回答“这一次
Shot A -> Shot B实际发生了什么”。前者不能替代本次QA/P6，后者不能扩大或修改qualification。两者都不是
mutable lifecycle或第二acceptance owner；Production Manifest、`ProductionStateCommitter`、active capability
snapshot与P6继续拥有各自canonical truth。

### Selection, Downgrade, and Failure

- Planner/Router必须显式接收destination capability或由已批准policy做deterministic selection；selected
  `execution_stack_hash`、grade、qualification与applicability proof必须进入resolved identity。
- Router只能从fresh capability snapshot中选择单个、完整满足当前grade的variant。它不得根据OOM、
  latency、artifact缺失、previous success或quality score在attempt中换child。
- capability denial、profile drift、materialization failure、unknown outcome或quality rejection都保持当前
  attempt blocked/failed；不得自动选择另一个Provider、较低grade、Turbo/Stock alternative或cloud lane。
- 用户或Planner可以创建一个新的显式attempt选择其他qualified stack；新attempt必须拥有自己的intent、
  budget/egress（如适用）、permit、provenance与acceptance evidence，不能复用失败attempt的effect token。
- 若失败发生在`WITHIN_CONTINUOUS_TAKE`，new attempt只能使用一个exact `execution_stack_hash`重生成整个sealed take，
  或先由approved authoring revision把take拆出visible `HARD_CUT`再创建新attempt；不得从失败frame开始换
  Provider续接，也不得由runtime自动改变take membership。
- “boundary-aware portability”只表示provider-neutral semantics、exact evidence、deterministic routing、
  durable lifecycle、recovery与composition contract在approved boundary上保持稳定；它不承诺零等待、
  零成本、跨模型视觉等价或未经真实Shot/P6验收的主观连续性。

## Provider Profile Contracts

### Official Upstream Workflow Baseline

Provider-native workflow必须来自reviewed、license-compatible upstream或等价可信source，而不是临时拼装的
未审计节点图。Exact repository、commit、path、raw hash、license、node inventory与model components属于
Provider baseline/profile/build receipt，不写入本规范。

Upstream workflow只能证明一个bounded native graph baseline；它不能原样成为AI-VIDEO Production truth，
也不拥有或替代Manifest、Registry、continuity evidence、P5 invalidation、candidate activation/recovery或
exact replay lifecycle。

项目派生版本必须保留可reopen的upstream provenance，并以结构化清单记录相对reviewed raw source的全部有意修改。派生规则如下：

- reviewed/export为deterministic API-format JSON；
- 删除UI-only notes、demo input asset与非必需的subgraph/UI metadata；
- optional LoRA、remote refiner与任何cloud fallback默认关闭，且不得隐藏在profile外被自动启用；
- 保留官方native H3 conditioning、sampling、video/audio decode与MP4 output contract；
- 将provider-neutral roles deterministic绑定到native inputs；不得静默增加、删除或重解释role；
- 不同native task、checkpoint family或conditioning semantics必须形成不同execution stack。

Upstream更新不会自动改变sealed Production stack。任何upgrade必须选择新的exact provenance，重新review
derived diff、生成新的`execution_stack_hash`并重新通过适用qualification/acceptance gates；未完成时使用
旧sealed stack或fail closed。

### Local Continuity Lane

Local Provider profile必须把workflow、binding、compiler、checkpoint/artifact、sampler/scheduler、plugin/runtime
与output contract全部纳入`GenerationExecutionStackIdentity`。Exact filenames、hashes、frame ranges和live
proof只由runtime baseline、profile及receipts拥有。

Normative continuity要求保持：downstream Shot消费exact upstream evidence；candidate/derived anchor的
activation与reopen必须原子一致；exact replay不得增加Provider effect；失败diagnostic attempt不得计入
accepted proof或blind retry。延长单次generation duration仍只是一个更长的Shot，不能自动证明multi-Shot
continuity。

### Concrete C4 Destination Child

每个`C4_NATIVE_BOUNDARY_MOTION` destination必须作为独立capability child实现，不能扩宽其他native task
或拼接多个children。Provider-neutral request保持：

```text
generation_mode = IMAGE_TO_VIDEO
continuity_mode = MULTI_ANCHOR
```

任何`Hybrid`等mode token只属于provider-native compiler/profile，不得新增模糊的通用generation mode。
Family只聚合capabilities并按exact selected child dispatch，不拥有durable state、quality selection或runtime
fallback；`VideoGenerationService`与`ProductionStateCommitter`继续拥有intent、permit、submit/status/
fetch、candidate、activation、recovery与replay。

第一版motion child的binding grammar固定为：

| Role | Cardinality | Native requirement |
| --- | ---: | --- |
| `first_frame` | exactly 1 | exact native first-boundary role |
| `last_frame` | exactly 1 | exact native last-boundary role |
| `reference` | exactly 1 | exact native identity-reference role |
| `reference_video` | exactly 1 | exact native motion-reference role |
| `reference_audio` | exactly 0 | absent |
| all roles | exactly 4 | one selected capability |

Grade E `reference_video`只承载visual motion/action reference，不隐式携带soundtrack。Static C4如未来
需要，必须使用独立capability ID和exact
three-role grammar，不能让同一个variant同时接受模糊的三/四角色shape。

#### Model Qualification Gates

Model/checkpoint/artifact strategy及候选顺序属于active implementation plan和qualification record。Normative
要求是：候选必须sequential、explicit且content-addressed；它们不是runtime fallback，不能共享同一个
capability或`execution_stack_hash`。只有一个exact stack通过full smoke、real-Shot validation与P6/human
gates后，才可进入active capability snapshot。任何checkpoint、LoRA、fusion artifact、sampler或scheduler
变化都必须形成新的stack identity并独立验收。

#### Profile and Artifact Seals

Production profile至少seal `GenerationExecutionStackIdentity`要求的provider deployment、model/capability、
compiler、workflow、checkpoint/artifact、LoRA、sampler/scheduler、runtime/plugin与output contracts，以及
license/provenance、node/input schema、locality/egress与fallback policy。

任何derived/fused artifact build属于显式Provider inventory preparation，不属于每次generation attempt。Build
receipt必须绑定source model hashes、builder/recipe/version、tensor contract、output artifact/sidecar hashes
与license/provenance；runtime只允许reopen、rehash、verify和consume。Missing/tampered artifact不得触发
auto-build、auto-repair、stock substitution、cloud fallback或第二套Production recovery。Artifact recovery
不改变`ProductionStateCommitter`对attempt lifecycle的唯一ownership。

以下任一条件必须在permit consumption与ComfyUI POST之前fail closed：role缺失/重复/多余或错序、
anchor/Registry/provenance/materialization mismatch、endpoint approval/feasibility不完整、motion tail没有以
exact terminal结束、native role mapping错误、reference audio意外连接、execution stack drift、output
ambiguity或违反selected locality/egress/fallback policy。

### Cost Control and Provider Portability

Shot Continuity必须保持“一个provider-neutral lifecycle，多个显式execution stacks”。以下contract在Local、
remote/paid与未来Provider之间复用，不得在adapter内复制：

- `ContinuityConstraintSet`、`TerminalFrameEvidence`与`ContinuityReferenceBinding`；
- exact request/resolved fingerprints、candidate provenance与terminal artifact identity；
- canonical activation/recovery、exact replay与same-desired failure rules；
- P5 continuity dependency、precise downstream invalidation；
- P3/P4唯一composition/timeline/audio/caption/final mux ownership。

切换Provider不是只替换`model_id`。每个stack仍必须提供并独立验收：

- concrete adapter/transport；
- exact capability variant，例如`first_frame`、`last_frame`、reference、native audio、duration、resolution与container；
- provider-specific workflow/profile或cloud payload mapping；
- local resource policy或remote Paid Provider Gate/Cloud Egress；
- output parsing、measured validation、error normalization与live/quality evidence。

任何stack不支持当前continuity request时必须在submit前fail closed；不得删除required roles、退化mode、改用
另一个stack或fallback到cloud。Selection必须显式并进入resolved identity。

Local与cloud都只是Production candidates，不是预设的draft/final等级：

- Local是低边际成本、仍需计算GPU/电力/RAM/VRAM与时间成本的candidate；它既可用于draft，也可在满足
  Shot requirement、technical/continuity gates与P6/human acceptance后成为Final Production output。
- Cloud是通常具有更高货币、egress与latency成本的candidate；它不天然是final，同样必须完成自身
  capability、live artifact、continuity、quality与P6/human gates。
- Final selection由Shot requirement、qualified execution stack、accepted quality、budget/egress和explicit
  production decision共同决定；local/cloud身份本身不能产生质量优先级或acceptance。

Cost可以影响Planner在多个已qualified stacks之间的显式选择，但不能修改rubric、跳过QA、自动升级
local draft到cloud final，或在失败attempt内触发fallback。每个候选保留独立generation identity、
provenance与P6 evidence。

### Remote Provider Profiles

Remote Provider只能暴露其exact model/deployment正式声明且由active profile验证的roles、counts与output
contract。另一个model的example、family-level marketing、adapter serializer字段或一次HTTP acceptance都不
能扩大selected capability。Exact API evidence、dated model matrix、profile/price/entitlement snapshot与live
attempt属于runtime/provider baseline和receipts。

所有remote stacks仍必须消费exact materialized assets，绑定`GenerationExecutionStackIdentity`，并遵守
budget、Cloud Egress、one-use permit、unknown-outcome recovery、canonical activation/reopen与zero-effect
replay。Remote成功不产生跨model或跨stackqualification。

### Seedance 2.0 Family Isolation

Seedance 2.0 base、Fast与Mini可以复用transport adapter，但必须作为独立exact model/deployment stacks。
Active availability、entitlement、pricing、model IDs、output/reference bounds和当前formal cross-mode evidence
只由runtime/provider baseline与active profiles拥有，本规范不固定其dated values。Capability discovery不得把
“provider catalog存在”或“代码中有entry”解释为“当前账户可用”。

#### Shared Transport, Separate Model Contracts

三者可以复用同一类Ark async task transport和AI-VIDEO `SeedanceVideoProvider` adapter：相同的submit/
status/fetch lifecycle、`model + content[]` request envelope、image/video/audio role serialization、Paid
Provider Gate、materialization与unknown-outcome recovery seam。这里的“shared interface”只表示transport
shape和adapter code path可以复用，不表示三个model是drop-in interchangeable capability。

每个model/mode必须拥有独立`SeedanceCapabilityProfile`、capability ID与
`GenerationExecutionStackIdentity`，至少分别seal：

- exact logical `model_id`、actual `api_model_id`或endpoint deployment identity、expected response model；
- exact mode与allowed role grammar，不能使用`seedance-2.0`family wildcard；
- output resolution/ratio/raster、duration/timing mode、FPS、container与native audio bounds；
- reference image/video/audio counts、individual/aggregate duration与materialization bounds；
- profile/stack version、pricing snapshot/upper bound、egress preview、one-use permit与resolved request hash；
- model-specific offline compiler tests、live receipt和quality/P6 evidence。

Exact model matrix与provider drift由fresh capability/profile snapshot拥有，不在本规范复制。切换任一
Seedance model/deployment必须选择新的`execution_stack_hash`、resolved identity与attempt。Request若不满足
selected exact profile，必须在paid preview/permit/POST前拒绝；adapter不得因为另一个2.0 family profile接受
该shape就改写model ID、删减roles、改变output contract或使用另一份pricing。Response返回的model identity
必须与submission binding一致，否则按provider mismatch fail closed。

Model isolation acceptance至少覆盖：

- capability snapshot只暴露fresh entitlement与profile共同允许的exact models；provider catalog不得自动
  启用任何model；
- base、Fast与Mini的execution stack/request hashes互不相同，family alias和cross-model profile reuse
  必须拒绝；
- 任一request超出selected exact profile bounds时在preview/permit/POST前拒绝，effect count为零；
- missing/stale model-specific pricing、wrong endpoint deployment或response model mismatch均fail closed；
- 一个model的offline/live/quality acceptance不能满足另一个stack的qualification或attempt evidence；
- 切换exact model必须创建新attempt，重新完成pricing、egress、permit、provenance与P6 evidence。

Adapter能够序列化`first_frame`、`last_frame`、`reference_image`或`reference_video`只证明字段mapping，
不证明selected model/mode接受它们的union。每个active profile只能暴露formal Provider evidence覆盖的exact
role grammar；不同task profiles不得由Router拼接成虚假的combined capability。

任一Seedance 2.0 exact stack只有在formal model-specific evidence支持时，才可新增独立
`C4_SEMANTIC_MULTI_REFERENCE` capability，将opening
composition、ending composition和canonical identity分别作为semantic image references，将motion作为
`reference_video`。该contract必须明确opening/ending不是native `first_frame`/`last_frame`，不得宣称
pixel-exact boundary，也不得作为Grade E失败后的fallback。另一个model identity本身不扩大binding
grammar，必须拥有自己的stack、formal evidence与quality gates。

`SeedanceAssetMaterializationReceipt`与`SeedanceAssetReferenceResolver`继续独占already-materialized
Ark identity导出并拒绝local Registry ID伪装`asset://`；缺少exact active materialization evidence时
必须在authorization/permit/submit前fail closed。

任何bounded cross-mode discovery probe必须是未来独立授权的single POST、lowest valid cost、no retry、
no fallback attempt。HTTP/schema acceptance最多证明transport/schema reachability；仍需检查roles是否被
实际遵循，并重新完成boundary、identity、motion与P6 gates后才能seal capability。

## Artifact and Provenance Lifecycle

1. Source video candidate 必须先通过现有 measured validation 和 provenance sealing。
2. Terminal extraction 必须读取由 committer transaction 持有并重新验证的 exact source bytes；路径 reopen 后必须再次验证 containment、type、size 和 hash。
3. Extraction 输出必须先进入 immutable, content-addressed candidate evidence，再与 source candidate identity 和 downstream binding 一起由 `ProductionStateCommitter` durable commit/activate。
4. 临时文件只可作为 transaction-local scratch；不得被 request、Registry、Manifest 或 Provider receipt 直接引用，成功或恢复后也不得成为唯一 evidence。
5. reopen/recovery 必须从 durable evidence 验证 image hash、metadata、source candidate 和 downstream binding；tampered、unreadable、symlink escape、wrong source Shot 或 wrong Registry revision 全部 fail closed。
6. 相同 source candidate、selection rule、extractor contract 和 continuity constraints 的 exact replay 必须返回相同 evidence，不重复 extraction 或 durable writes。
7. `ProviderTransitionQualification`与`TransitionAttemptEvidence`必须作为不同schema、不同content hash的
   immutable artifacts；qualification只引用validation-set evidence，Production attempt必须引用exact
   qualification并保存自己的Shot/output/P6 evidence。
8. Production Manifest只保存canonical lifecycle与active pointers；qualification、attempt evidence、Registry
   record或Dependency Graph不得保存第二套mutable lifecycle。

Exact Manifest/schema version、当前兼容性状态和历史serialization shape属于runtime baseline。任何未来
migration仍必须additive、可reopen，并由`ProductionStateCommitter`维持唯一writer ownership。

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

所有implementation与Provider lanes必须持续覆盖：

- terminal evidence 与 exact source Shot/candidate/Registry/provenance binding；
- request hash 对 terminal bytes/evidence/constraint 变化敏感，对 generation instance identity 的既有 replay 语义保持兼容；
- tampered、unreadable、wrong-dimension、wrong-source、wrong-revision 和 symlink-escape rejection；
- unsupported mode/role/model/output 的 capability denial，且 submit 为零；
- exact replay 的 submit/fetch/extract/activate/render 都为零；
- fetched、extracted、prepared、partially activated 各 crash point 的 explicit recovery；
- Shot N input 改变只 stale Shot N+1 及真实 downstream closure，unrelated/future-unlinked Shot 保持 fresh；
- static-image、Legacy、composition、audio/caption 和 default no-network regressions 不发生。

### Visual Evidence

每个 continuity edge 必须产出可重放的edge-level visual comparison evidence：

- Shot N terminal frame；
- Shot N+1 initial decoded frame；
- 两者各自的 source asset/hash/frame index/timestamp；
- 无美化、无 crossfade 的 side-by-side 或 deterministic comparison artifact。

自动 `video-analysis` 与人工 review 是不同 gate。两者分别检查 scene/character identity、camera axis/direction、motion direction、lighting/color、entrance/exit state和叙事空间关系；任何单一 similarity score 不得替代逐项 verdict。

Measured evidence必须证明terminal extraction与next-Shot input exact binding，并保留probe、
frame-integrity和side-by-side artifacts。具体PSNR/SSIM、resolution、frame count与analyzer output进入
runtime baseline或exact record，不在本normative spec固化；任何该类evidence都只满足technical
live-local proof，不能替代blinded human rubric或宣称subjective quality accepted。

### Acceptance Tiers

1. `technical acceptance`：Fake/offline executable contracts、local artifact verification、replay/recovery/P5 tests 和 composition invariants 全部通过。
2. `provider live proof`：每个明确`execution_stack_hash`通过适用授权与gates的真实submit/fetch/activation/
   replay proof；成功只证明该stack的connectivity、payload和durable lifecycle，不自动外推到其他stack。
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
- 每个generation只使用一个exact selected `execution_stack_hash`、一次submit、no blind retry、
  no fallback；生成结果在P6/human acceptance前保持candidate/unactivated；
- 每个edge分别绑定exact terminal、identity、endpoint、motion-tail、decoded output与policy hashes；逐edge
  评估后还必须以原速连续播放整段，检查identity、wardrobe、style、camera velocity、action phase与空间关系的
  累积漂移；
- review素材必须保留raw hard cuts，不得用crossfade、optical flow、frame interpolation、速度变化、重构图或
  其他后期处理隐藏generation discontinuity；可另行制作comparison derivative，但不能替代raw evidence；
- `SCENE_BOUNDARY + IDENTITY_STYLE_CARRYOVER`必须在真实换场Shot上证明所有required dimensions均有exact
  references且通过普通QA；`SUBSTANTIAL_RESET`必须由真实scene/time/state变化与approved intent证明，而不是
  因为换了Provider或模型效果差而事后标记；
- `ProviderTransitionQualification` validation set必须包含canonical real Shots之间的visible
  `HARD_CUT + FULL_CONTINUITY`，覆盖其声明的content/risk envelope，并使用真实accepted source outputs派生
  anchors；synthetic-only、rejected或unactivated outputs不能满足；
- qualification之后的每个Production edge都必须单独保存`TransitionAttemptEvidence`与本次P6/human
  verdict；qualification不能代替本次验收；
- `SAME_GRADE_MULTI_DESTINATION_READY`必须让各destination消费同一real-Shot validation set与同一frozen
  rubric；不同故事、不同角色或更容易的fixture不能用于横向替代。

Implementation、Provider media与P6 evidence必须绑定同一或可证明byte-identical的sealed
`validation_snapshot`。任何model/artifact、workflow、binding、profile、policy、reference set、fixture或
rubric或`execution_stack_hash`变化都会使受影响的真实Shot evidence失去promotion资格并要求重跑；Harness
receipt不能替代该gate。

### Multi-Provider Claim Levels

Completion与产品声明必须按以下层级报告，不能用较低层替代较高层：

1. `C4_CORE_READY`：provider-neutral binding/request/resolved/hash/Router exact grammar与negative tests通过。
2. `C4_DESTINATION_READY`：一个exact destination child通过profile preflight、fake lifecycle、full
   four-anchor local/live smoke、activation/reopen/replay，并对同一sealed snapshot完成3–4个canonical real
   Shots、至少2个edges的原速Pilot、boundary/identity/motion和P6/human acceptance。
3. `DIRECTED_TRANSITION_READY`：一个source/destination `execution_stack_hash` pair拥有fresh
   `ProviderTransitionQualification`，其real-Shot validation set覆盖声明的visible
   `HARD_CUT + FULL_CONTINUITY` content/risk envelope，且qualification seal后至少一个匹配的真实
   Production edge已产生PASS `TransitionAttemptEvidence`。Qualification只授权匹配envelope的future
   attempts；每个attempt仍必须产生自己的`TransitionAttemptEvidence`。
4. `SAME_GRADE_MULTI_DESTINATION_READY`：同一provider-neutral grade至少有两个不同
   `provider_kind/deployment`的destination stacks与sealed capabilities，使用同一real-Shot validation set
   与frozen rubric分别通过，并完成deterministic selection、denial、reopen与no-fallback tests。
   只有达到此层才能声称“在已通过qualification的visible
   hard-cut directions上具备同等级boundary-aware Provider portability”。
5. `FULL_MATRIX_READY`：每个对外声称支持的directed stack pair和content/risk class都拥有独立
   qualification及至少一个匹配的PASS attempt evidence。没有完整矩阵时不得声称
   “任意Provider双向无缝切换”；即使完整矩阵通过，
   `WITHIN_CONTINUOUS_TAKE`仍禁止cross-stack，
   `SCENE_BOUNDARY`仍必须根据carryover或reset classification执行对应reference与QA合同。

各层级的当前状态只由runtime baseline拥有；本规范不把任何Provider或stack预标为ready。

### C4 Destination Verification Matrix

首个destination至少必须完成以下gates：

| Gate | Required evidence |
| --- | --- |
| Execution stack | exact provider/deployment/model/capability/profile/compiler/workflow/checkpoint/LoRA/sampler/runtime/output seals与license/provenance |
| Cardinality | exact 1 first + 1 last + 1 identity image + 1 motion video；缺失、重复、多余、错序和sub-capability union全部拒绝且effect count为零 |
| Workflow/compiler | exact native role bindings、empty reference audio、deterministic payload/output mapping与compiler/workflow stack seals |
| Lifecycle | applicable permit、submit/status/fetch、unknown-outcome recovery、candidate activation、reopen与exact replay zero effects |
| Four-anchor smoke | one request、one selected execution stack、one submit、no retry、no fallback，记录全部input/output/request/stack hashes |
| Boundary policy | `WITHIN_CONTINUOUS_TAKE`跨stack zero-effect denial；hard-cut full continuity缺applicable qualification拒绝；scene carryover缺reference/QA拒绝；scene reset缺approved reset evidence拒绝 |
| Real Shot Pilot | selected ProductionProject revision中的3–4个canonical Shots、至少2 edges、同一sealed snapshot、逐edge evidence与raw full-speed cumulative-drift review |
| Boundary | decoded frame 0与terminal frame分别对比native first/last；报告measurement，不把native role夸大为pixel identity |
| Identity | first/middle/last windows检查face/subject、hair、clothes、props、body scale与multi-frame drift；不足时`NOT_EVALUATED` |
| Motion | subject/camera direction与velocity、action phase、entrance/exit、unexpected stop/re-entry；单帧SSIM不得代替 |
| Qualification | exact source/destination stack hashes、grade、applicability envelope、frozen rubric、real-Shot validation-set evidence、limitations与staleness tests |
| Attempt | exact source/target Shots、anchors、qualification ID/applicability proof、selected stack、output、QA与P6/human evidence |
| P6/Human | exact request/output/anchors、technical/strategy/semantic evidence与human verdict共同形成Final Acceptance |
| Harness | task-owned exact staged snapshot或commit range的fresh passing receipt；Harness不替代live media或P6 |

所有阈值、fixture、rubric与candidate identities必须在观看结果前冻结。同一candidate未通过full matrix时
保持`experimental / unavailable`；quality rejection不得因transport success、hash closure或单一metric
改写为accepted。

## Optional Automatic Continuity Evaluation

Human/P6 review是首个`C4_DESTINATION_READY`、`ProviderTransitionQualification`与每个
`TransitionAttemptEvidence`的Critical acceptance path。Automatic continuity evaluator属于High/
experimental辅助能力；detector、ReID、tracking或其他自动backend的缺失不得阻塞第一个真实destination或
`DIRECTED_TRANSITION_READY`，只要exact human evidence完整覆盖active rubric并由P6裁决。

### Measurement and Verdict Boundary

- evaluator只输出exact artifact/frame/profile-bound measurements，不自报PASS；最终verdict仍只由P6
  adjudication派生；
- unsupported dimension、低coverage、遮挡、ambiguous tracks或不可信output必须为`NOT_EVALUATED`，不得
  猜测通过；
- automatic `NOT_EVALUATED`不是PASS，必须由rubric要求的human evidence补足；human结论不得伪装成model
  observation；
- automatic evidence可以提供额外fail-closed signal或降低review成本，但不能降低frozen human/P6 gate，
  也不能扩大qualification applicability envelope。

### Backend and Persistence Routing

具体detector/ReID/model、ONNX/runtime、sampler、threshold、GPU/CPU profile、安装状态与calibration结果属于
runtime/provider baseline、sealed evaluator profile、research record或独立implementation plan，不属于本
normative spec。若automatic evidence被使用，仍必须content-addressed并绑定exact request/policy/artifact/
evaluator profile；`ProductionStateCommitter`保持唯一writer，replay/recovery不得重复evaluator或human
effects。若未使用automatic evidence，完整human/P6 evidence可按同一acceptance rubric关闭gate。

## Assumptions and Unresolved Decisions

- C4 provider-neutral contract、Router grammar与canonical lifecycle owners视为本实现slice的unchanged
  contract；只有concrete child接入测试证明真实缺口时，才允许最小core修正。
- P0 已通过单独 Decision Gate，采用 Manifest `2.11` + immutable evidence layout 持久化
  `GenerationExecutionStackIdentity`、P0 `ContinuityTransitionPolicy`、`RealShotValidationSet` 与
  qualification-prepared receipt。`ProviderTransitionQualification`、`TransitionAttemptEvidence` 及它们的
  active routing/persistence仍未决定，也未获 P0 receipt 授权。
- `ContinuityTransitionPolicy`的 P0 logical/persistence contract已冻结；Router applicability、ResolvedTimeline
  boundary binding与普通 Production attempt integration仍待后续 milestones。实现不得把`SCENE_BOUNDARY`
  硬编码成`SUBSTANTIAL_RESET`，也不得在policy缺失时由Router或adapter猜测carryover dimensions。
- 任一Provider的frame/reference cross-mode union只有formal exact model/profile evidence或bounded live
  proof才能进入active capability；serializer field coexistence或一次2xx不能改变grade。
- Boundary、identity与motion的numerical thresholds、fixture和human rubric必须在live smoke前由
  implementation plan/QA policy冻结；本spec不允许看到candidate后再降低门槛。
- Automatic evaluator backend与calibration不是首个destination/qualification的dependency；完整human/P6
  evidence必须始终存在可执行路径。

## Execution Authorization Routing

本规范不保存historical authorization或permit consumption。每次remote/paid execution都必须按
`AGENTS.md`与canonical Provider gates取得fresh task scope、budget/egress decision、durable intent与one-use
permit；旧attempt的authorization、permit或receipt不得复用。Local execution同样不得绕过sealed stack、
preflight、local permit、unique committer、recovery与media verification。Exact authorization状态只存在于
current task context与durable runtime evidence。

## Rollback

未来 continuity implementation 必须可按 provider lane 删除：移除continuity-specific child capability/
payload mapping与active transition qualifications后，旧P8 T2V/I2V/R2V request、candidate activation、
static-image path、generated-MP4 composition和P3/P4/P5 ownership必须恢复到pre-continuity behavior。移除一个
destination child不得改变其他stack identity、自动选择replacement或把Grade E request降为Grade S。
已存在的terminal/motion/qualification/attempt/provider artifacts应保持immutable、可审计但不再被active graph/
capability snapshot选择；不得通过删除历史receipts完成rollback。
