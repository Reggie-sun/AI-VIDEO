# AI-VIDEO Shot Continuity Implementation Plan

## Status

Active canonical implementation plan，governed by
[Shot Continuity Specification](../specs/2026-08-19-ai-video-shot-continuity.md)。

本计划不拥有当前implementation/live/quality状态。每次执行必须先从
`docs/v0.2-runtime-baseline.md`、active capability/profile snapshot、exact inventory/build receipts与
Production records加载fresh truth，再决定哪些milestones已满足、仍需执行或必须重验；不得把本计划中的
候选顺序解释为当前库存或readiness证明。

Plan本身不授权runtime implementation、模型安装/融合、ComfyUI升级、local live generation、remote/paid
preview/POST、permit、activation、push或release。

已接受“验证与实现同时推进”的execution strategy，但并行只发生在明确分离的
Implementation lane与Validation lane。Validation必须绑定immutable checkpoint，不得在同一次attempt期间
读取正在变化的source/workflow/profile；并行执行不会放宽Provider、permit、P6或same-file ownership gates。

## Goal

按一个可验证、无 fallback 的顺序交付：

1. 保持现有 provider-neutral C4 core 为唯一四锚点合同；
2. 资格判定并实现一个 Local T8 `C4_NATIVE_BOUNDARY_MOTION` destination child；
3. 为每个selected generation建立`GenerationExecutionStackIdentity`，使checkpoint、LoRA、sampler、
   workflow、compiler与plugin drift都改变`execution_stack_hash`；
4. 保持Seedance 2.0 base/Fast/Mini exact model contracts隔离；本计划的Seedance implementation target仅为
   base 2.0，是否可用仍由execution-time entitlement/profile snapshot决定；
5. 用`ProviderTransitionQualification`表达可复用、bounded的directed stack-pair能力，用
   `TransitionAttemptEvidence`表达某一次真实Shot edge；
6. 用`ContinuityTransitionPolicy`把结构边界与残余连续性义务分开：continuous take锁定exact stack，
   full-continuity hard cut只走applicable qualification，scene boundary仍按identity/style carryover或显著
   reset执行；
7. 只有至少两个不同`provider_kind/deployment`的destination stacks在同一grade、同一
   real-Shot validation set上分别通过全部gates，才允许声明`SAME_GRADE_MULTI_DESTINATION_READY`。

目标不是 runtime 自动选模、失败降级或“任意 Provider 一键互换”。Planner/Router 只可显式选择已经
sealed 且对 exact grade、execution stacks、boundary policy与applicability envelope完成qualification的
destination。Adapter只解决
协议、lifecycle与composition compatibility，不承诺跨模型identity、motion、camera或style等价。

## Scope

### Included

- C4 core regression/tamper closure，不重复实现已存在的 owner；
- Local T8 C4 model qualification：M0 stock Ref2VA，必要时 M1 sealed Hybrid artifact；
- winner-specific workflow、binding、profile、capability 与 local child adapter；
- `LocalH3VideoProviderFamily` additive child registration 与 exact dispatch；
- local lifecycle、recovery、activation、reopen、replay 与 P5 closure；
- four-anchor technical smoke、decoded boundary、identity、motion 与 P6/human evidence；
- `ContinuityTransitionPolicy` logical contract、boundary/obligation组合与zero-effect Router gates；
- `GenerationExecutionStackIdentity` canonical hashing、resolved/provenance/replay binding与drift denial；
- 真实`ProductionProject`中的3–4 Shot Pilot、逐edge evidence、raw full-speed sequence review与累计漂移验收；
- directed `ProviderTransitionQualification` persistence/applicability seam与per-edge
  `TransitionAttemptEvidence`；
- Seedance 2.0 base/Fast/Mini 的 catalog、active inventory、profile、pricing、endpoint 与 response identity
  isolation；
- 可选的 base Seedance 2.0 `C4_SEMANTIC_MULTI_REFERENCE` lane，前提是 separate formal evidence、
  authorization 与 quality gates 均满足；
- canonical docs、tests、Architecture Gate、exact-snapshot Harness 与 independent review。

### Out of Scope

- 不新增 timeline、renderer、state writer、automatic recovery 或 Provider fallback；
- 不扩宽现有 T8 `T2VA`、`I2VA`、`FL2VA`、`Ref2VA` capability identity；
- 不把多个 capability 的并集描述为一个 C4 capability；
- 不把 Seedance frame mode 与 reference mode 的 serializer 字段共存当作 official cross-mode support；
- 不把计划target解释为entitlement；任何未被fresh active profile允许的model不得进入snapshot；
- 不在第一版启用 Turbo LoRA；
- 不自动构建、修复或替换 Hybrid artifact；
- 不在本计划内升级ComfyUI或引入新的conditioning subsystem；
- 不引入 remote/cloud fallback，不进行 blind retry；
- 不改变 Legacy CLI、default no-network、HyperFrames 或 `ResolvedTimeline` ownership；
- 不把 transport success、hash closure、SSIM、reviewer verdict 或 fetched artifact当作 P6 Final
  Acceptance；
- 不允许在`WITHIN_CONTINUOUS_TAKE`中途切换execution stack；失败后只能以一个exact stack重生成整个take，或由
  approved authoring revision先插入visible hard cut；
- 不把`SCENE_BOUNDARY`自动解释为continuity reset。仍延续主角、服装、hero props、palette或强style时，
  必须携带exact references并过普通QA；只有approved `SUBSTANTIAL_RESET`才允许近似自由portability；
- 不用synthetic fixture、fake transport、single-boundary smoke或Harness receipt替代真实Shot generation、
  full-speed human review与P6 acceptance；
- 不让automatic detector/ReID/evaluator阻塞首个destination或directed qualification；Human/P6是Critical，
  automatic evaluator是High/experimental；
- 不承诺 `FULL_MATRIX_READY`，除非所有对外声明的有向stack pair和content/risk classes都有独立
  qualification。

## Contract Surfaces

### C4 Provider-Neutral Contract

现有 `C4MultiAnchorBinding`、`ProviderNeutralVideoRequirement`、`VideoGenerationRequest`、
`ResolvedVideoGenerationRequest`、activation scope 与 Router gate 是 stable contract。Motion grade 的 exact
shape 保持：

| Semantic anchor | Native role | Cardinality |
| --- | --- | ---: |
| exact upstream terminal | `first_frame` | 1 |
| approved future endpoint | `last_frame` | 1 |
| canonical identity image | `reference` | 1 |
| exact upstream motion tail | `reference_video` | 1 |
| audio reference | `reference_audio` | 0 |
| all roles | — | 4 |

Public neutral identity 保持 `IMAGE_TO_VIDEO + MULTI_ANCHOR`；T8 `task_type=Hybrid` 只存在于
provider-native compiler/workflow。

### Product Grades

| Grade | Contract | Allowed claim |
| --- | --- | --- |
| `C4_NATIVE_BOUNDARY_MOTION` | same native request 中 exact first/last/reference/reference_video | native exact-role input binding；decoded boundary、identity、motion仍需独立证据 |
| `C4_SEMANTIC_MULTI_REFERENCE` | opening/ending/identity/motion 均作为 semantic references | semantic guidance；不得宣称 native first/last 或 pixel-exact boundary |

Grade E 失败不得自动改成 Grade S。两者必须使用不同 capability ID、request contract、product label、
acceptance rubric 与 quality evidence。

### Generation Execution Stack Contract

新增immutable `GenerationExecutionStackIdentity` logical model并生成`execution_stack_hash`。Canonical fields
至少覆盖：

- `provider_kind`与deployment identity；
- `model_id`、`capability_id`与`profile_hash`；
- `compiler_hash`与optional `workflow_hash`；
- ordered checkpoint、artifact与LoRA identities；
- applicable sampler/scheduler identity；
- runtime/plugin seals与output contract hash；
- stack contract version与canonical content hash。

不适用字段使用versioned canonical empty representation；secret与local path不得进入hash。Remote opaque
service只seal可验证deployment/model/profile/API contract，并在qualification limitations中记录不可见drift。
Resolved request、intent、provenance、qualification、attempt evidence与replay必须绑定同一hash。任一有效
component变化都形成新stack，不允许因`provider_kind`或`model_id`相同而复用旧qualification。

### Boundary-Aware Provider Portability Contract

`ContinuityTransitionPolicy`必须把`boundary_kind`与`continuity_obligation`作为正交字段封存，不能用“换场”
推断“连续性清零”：

| Boundary kind | Continuity obligation | Execution rule |
| --- | --- | --- |
| `WITHIN_CONTINUOUS_TAKE` | only `FULL_CONTINUITY` | exact `execution_stack_hash`锁定；single generation或该stack正式支持的native extension；cross-stack effect为零 |
| `HARD_CUT` | `FULL_CONTINUITY`或approved `IDENTITY_STYLE_CARRYOVER` | full continuity跨stack要求fresh applicable qualification与C4；carryover要求exact references与普通QA，不得冒充C4 |
| `SCENE_BOUNDARY` | explicit `IDENTITY_STYLE_CARRYOVER`或`SUBSTANTIAL_RESET` | carryover仍验证identity/wardrobe/props/style/palette references；只有显著scene/time/state reset才回到ordinary explicit selection |

Policy至少绑定exact source/target Shots与revisions、resolved boundary identity、take membership（如适用）、
source/destination exact `execution_stack_hash`、continuity grade、visible-cut/reset authoring evidence、
`required_carryover_dimensions`及其Registry/materialization references、QA policy、allowed strategy、version与
canonical hash。`IDENTITY_STYLE_CARRYOVER`的dimensions必须非空；`SUBSTANTIAL_RESET`的dimensions必须为空，
且必须有approved reset evidence。任何字段漂移都产生新policy identity。

Router必须在compiler/preview/permit/POST前拒绝：continuous-take cross-stack、unqualified full-continuity
hard cut、缺reference或destination role的scene carryover、仍有carryover却标记reset、无效组合、tamper或与
approved Shot/Timeline evidence冲突。`SUBSTANTIAL_RESET`只表示continuity obligation显著降低，不跳过普通
capability、materialization、budget/egress（如适用）、output probe与QA。

### Local T8 Qualification Contract

资格顺序固定为：

```text
M0: stock Ref2VA + T8 Hybrid conditioning + Stock20
    sampler=dual_clock_euler
    flow=native_flow
    Turbo LoRA=off

       only if M0 fails frozen gates

M1: exact validated pruned FL2VA/Ref2VA pair
    + sealed T8 Hybrid artifact
    + same Stock20 baseline
```

M0 与 M1 是 offline qualification candidates，不是 runtime fallback。最终 active snapshot 只能注册一个
winner；失败时不得自动切换 candidate。候选 identities 固定为：

- `minimax-h3-t8-c4-motion-ref2va-stock20-v1`；
- `minimax-h3-t8-c4-motion-hybrid-stock20-v1`。

同一 capability ID 后续不得替换 model bytes、artifact recipe 或 sampling profile。

### Real Shot Generation Verification Contract

Technical smoke之外，promotion必须选择一个exact `ProductionProject` revision和其中canonical Character、
Scene、Shot artifacts，冻结`RealShotValidationSet`：

- 3–4个叙事连续Shots、至少2个continuity edges；固定同一canonical主角与场景；
- 至少一个subject-motion handoff和一个camera-motion handoff；
- 每个input来自exact Registry revision及provenance/materialization receipt；
- 每个generation为one exact `execution_stack_hash`、one submit、no retry、no fallback；
- raw cuts原速整段观看，不用crossfade、optical flow、interpolation、retime或重构图隐藏跳变；
- 逐edge保存terminal/identity/endpoint/motion-tail/policy/output hashes，再审查sequence-level identity、
  wardrobe、style、camera velocity、action phase与spatial-storytelling累计漂移；
- Implementation、media与P6 evidence绑定同一或byte-identical sealed `validation_snapshot`。

Synthetic fixture、fake transport和single-boundary smoke可以在RED/technical gate中使用，但不能关闭
`C4_DESTINATION_READY`。Directed qualification必须由canonical real Shots之间的visible
`HARD_CUT + FULL_CONTINUITY` validation set支持；same-grade destinations必须使用同一real-Shot set与
frozen rubric。Qualification后的每个Production edge仍需独立`TransitionAttemptEvidence`。

### Seedance 2.0 Model Isolation Contract

base、Fast 与 Mini 复用 Ark async task transport 和 `SeedanceVideoProvider` submit/status/fetch lifecycle，
但绝不是 drop-in interchangeable capabilities。每个 model 必须独立 seal：

- exact `model_id`、API deployment/endpoint identity 与 expected response model；
- exact mode 与 allowed role/cardinality grammar；
- resolution、duration、FPS、container、reference bounds 与 audio behavior；
- profile version、pricing snapshot、egress preview、permit 与 resolved request hash；
- offline compiler、live receipt、quality 与 P6 evidence。

本计划只实现base 2.0 target；Fast/Mini保留catalog与compatibility isolation，不在本计划中启用。Execution
仍必须读取fresh entitlement、pricing与exact profile evidence；target scope不能替代active availability。

### Transition Qualification and Attempt Contracts

每个可复用direction必须拥有immutable、content-addressed `ProviderTransitionQualification`，至少绑定：

- source与destination `execution_stack_hash`；
- `boundary_kind=HARD_CUT`、continuity grade与anchor contract hash；
- versioned content/risk applicability predicate；
- frozen rubric、real-Shot validation-set evidence与P6 evidence identities；
- terminal/motion-tail derivation与materialization receipts；
- output normalization contract；
- technical/live/boundary/identity/motion/P6 validation evidence；
- limitations、unsupported conditions、staleness rules与schema/version/content hash。

每次普通Production transition必须产生独立`TransitionAttemptEvidence`，绑定exact source/target Shots与
revisions、accepted source output、source/destination stack hashes、policy、anchors、request/resolved、exact
qualification ID及applicability proof、output/provenance、QA measurements、human evidence与P6 verdict。

Qualification回答“该stack pair在bounded class下是否有资格”；attempt evidence回答“本次edge实际发生了
什么”。两者都不是第二lifecycle或acceptance owner。Active pointer、candidate、activation与recovery仍只由
`ProductionStateCommitter`/Production Manifest拥有，P6仍是verdict owner。

## Invariants

- `ResolvedTimeline` 是唯一 order/frame/sample/timing owner。
- `ProductionStateCommitter` 是唯一 durable write、activation 与 recovery owner。
- Dependency Graph 独占 dependency、fingerprint、invalidation 与 rebuild frontier。
- HyperFrames 是唯一默认 Production renderer。
- Router 只选择一个 exact capability；family 只聚合和 exact dispatch，不保存 last-selected state。
- 每个selected generation都必须解析并绑定一个exact `execution_stack_hash`；同Provider下的checkpoint、
  LoRA、workflow、compiler、sampler或plugin drift仍是stack change。
- `WITHIN_CONTINUOUS_TAKE`锁定一个exact `execution_stack_hash`；runtime不得中途替换或从失败frame
  续接其他stack。
- `SCENE_BOUNDARY`不是reset证明；identity/style carryover必须有exact references与普通QA，只有approved
  `SUBSTANTIAL_RESET`才允许近似自由的显式Provider selection。
- Missing、duplicate、extra、wrong-order、tampered、stale 或 unsupported inputs必须在 compiler、preview、
  permit consume 与 Provider POST 前 fail closed，effect count 为零。
- Local/paid attempt lifecycle、permit 与 evidence不得混合。
- Hybrid artifact build 是 explicit inventory preparation；runtime只能 reopen、rehash、verify、consume。
- Exact replay 不重复 Provider、artifact build、motion-tail extraction、activation 或 render effects。
- C1/C2/C3、Legacy T2V/I2V/R2V、historical request/resolved hashes在 C4 fields缺失时保持兼容。
- Technical PASS、live connectivity、quality acceptance 与 P6 Final Acceptance 分层报告。
- Fixture、fake transport、synthetic anchors、single-edge smoke与Harness receipt不能替代canonical real-Shot
  Pilot、raw full-speed review或P6/human acceptance。
- Human/P6是Critical path；automatic evaluator缺失或`NOT_EVALUATED`时由完整exact human evidence补足，
  detector/ReID工程不得阻塞首个destination或qualification。

## Baseline-Gated Target Behavior

`Current` truth不由本计划复制。每次执行使用runtime baseline、active profiles与exact preflight填充第二列；若
与下表assumption不一致，以fresh evidence为准并调整milestone状态，不修改normative contract。

| Surface | Execution-time input | Planned target |
| --- | --- | --- |
| C4 core | fresh baseline + regression tests | preserve existing owner，只修复可复现缺口 |
| Local T8 candidate | fresh inventory/profile/build receipts | additive winner-specific C4 child与new stack hash |
| Four-anchor live | exact selected stack snapshot | one request / one submit / no retry / no fallback + real-Shot evidence |
| Seedance availability | fresh entitlement/profile/pricing snapshot | base-only plan target；Fast/Mini保持isolated/unselected |
| Seedance exact C4 | fresh formal model/mode evidence | evidence不足继续fail closed；不由serializer推断 |
| Execution identity | selected runtime/profile seals | one canonical stack hash贯穿resolve/effect/provenance/replay |
| Transition reuse | fresh validation evidence | bounded `ProviderTransitionQualification` |
| Per-edge truth | exact Production attempt | independent `TransitionAttemptEvidence` + P6/human verdict |
| Boundary policy | approved Shot/Timeline intent | continuous-take stack lock、carryover references、reset evidence均fail closed |
| Real Shot verification | frozen project/revision/rubric | canonical 3–4 Shot Pilot、至少2 edges、raw full-speed累计漂移与P6 evidence |

## Compatibility

- `default_seedance_capabilities()` 继续表示 adapter 能理解的 authoritative provider catalog；active account
  inventory通过 explicit profile subset表达，不通过删除catalog或family wildcard表达。
- `SeedanceProviderProfile.create_default()` 若保留，只可用于 complete catalog fixtures/diagnostics；
  Production assembly必须显式传入 entitled capabilities 与 matching pricing subset。
- Existing `SeedanceVideoProvider` transport envelope保持；model isolation发生在 profile construction、
  capability selection、pricing、permit fingerprint与response validation。
- Existing local child APIs 与 `LocalH3VideoProviderFamily` protocol保持；新child additive注册。
- `ContinuityTransitionPolicy`先作为logical contract验证现有approved Shot/sequence intent、Timeline identity与
  immutable evidence seam；不得把scene boundary默认映射为reset，也不得由adapter猜测carryover。
- Schema/layout默认不变。若 stack identity、transition policy/qualification/attempt evidence无法复用现有 immutable evidence + Manifest
  pointer seam，必须触发 Decision Gate，先更新 spec/plan并取得 migration authorization。

## File and Ownership Map

### Stable C4 Core — Audit/Test First

- `src/ai_video/production/_video_continuity.py`
- `src/ai_video/production/video_requirement.py`
- `src/ai_video/production/video.py`
- `src/ai_video/production/_video_capability_fingerprint.py`
- `src/ai_video/production/_video_requirement_routing.py`
- `src/ai_video/production/shot_router.py`

这些文件只在 RED test证明真实缺口时做最小修正；不得为了接 Provider 再建一套 C4 contract。

### Local T8 Destination

- Create `src/ai_video/production/comfy_t8_hybrid_c4_profile.py`：winner-specific sealed profile、node/model/
  workflow/output preflight。
- Create `src/ai_video/production/comfy_t8_hybrid_c4_video.py`：capability、compiler、resolve/preview、exact
  local transport delegation。
- Modify `src/ai_video/production/local_h3_provider_family.py`：仅 additive exact child aggregation/dispatch。
- Modify `src/ai_video/production/__init__.py`：public exports。
- Conditional create `src/ai_video/production/h3_hybrid_artifact.py`：仅 M1 胜出时实现 build receipt model 与
  runtime reopen/verify seam；不拥有 Production lifecycle。
- Create `tests/test_production_comfy_t8_hybrid_c4_video.py`。
- Conditional create `tests/test_production_h3_hybrid_artifact.py`。
- Modify `tests/test_production_local_h3_provider_family.py`。
- Modify closest Router/request/provider-neutral/lifecycle/P5 E2E tests only when RED requires。

Winner确定后，workflow files必须把 candidate identity写入文件名，不使用模糊 generic identity：

- M0 winner：`workflows/{templates,bindings,profiles}/minimax_h3_t8_c4_motion_ref2va_stock20_v1.*`；
- M1 winner：`workflows/{templates,bindings,profiles}/minimax_h3_t8_c4_motion_hybrid_stock20_v1.*`。

Template为`*_api.json`，binding为`*_binding.yaml`，profile为`.json`。不得同时把两个candidate发布为
Production child。

### Seedance 2.0 Isolation

- Modify `src/ai_video/production/seedance_capabilities.py`：保持official catalog与exact per-model matrix；新增
  deterministic subset selection/validation seam，不引入family wildcard。
- Modify `src/ai_video/production/seedance_profile.py`：pricing models必须与selected capability models exact
  match，并允许official catalog的non-empty entitled subset；默认Production assembly为base only。
- Modify `src/ai_video/production/seedance.py` only if active-profile compiler/response validation RED证明需要。
- Modify `tests/test_production_seedance.py`：base-only active inventory、cross-model denial、bounds、pricing、
  endpoint、response identity 与 zero-effect regression。

### Transition Evidence

- First inspect/reuse `src/ai_video/production/video_artifact.py`、lifecycle schema、Manifest pointer与
  `ProductionStateCommitter` seams。
- If compatible without migration，create `src/ai_video/production/video_execution_stack.py` for immutable
  `GenerationExecutionStackIdentity` construction/hash validation；create
  `src/ai_video/production/video_transition.py` for `ContinuityTransitionPolicy`、
  `ProviderTransitionQualification`、`TransitionAttemptEvidence`、applicability与tamper validation。
- Create `tests/test_production_video_execution_stack.py` and `tests/test_production_video_transition.py`。
- Modify committer/lifecycle tests only for the existing pointer seam proven by RED。
- If persistence requires schema version、Manifest layout或artifact layout migration，stop before production edits；
  this plan does not authorize that branch。

### Canonical Documentation and Harness

- Modify `docs/v0.2-runtime-baseline.md` only after implementation/live truth changes。
- Modify `docs/v0.2-agentic-production-roadmap.md` only for actual gate status。
- Modify `docs/agent-primary-contract-matrix.md` and `.agent/harness/policy.yaml` only if new owned surfaces require
  routing/ownership updates；同步 `tests/test_agent_harness.py`。
- Keep this plan and governing spec as the only Shot Continuity artifact owners。

### Parallel Lane Ownership

- Implementation lane独占repository source、tests、workflow template/binding/profile与canonical docs的写入。
- Validation lane不拥有repository files；它只消费一个已commit、已hash、preflight通过的candidate snapshot，
  并通过canonical Product Runtime写入attempt、receipt、artifact与review evidence。
- Validation发现的问题只能形成immutable failure evidence和bounded change request；不得hot-edit正在验证的
  workflow/profile/model identity，也不得直接修改Implementation lane文件。
- 同一Validation attempt开始后，candidate commit、`execution_stack_hash`、fixture、prompt、policy与rubric
  全部冻结。任一项改变都产生新candidate identity并要求新attempt；旧evidence不得迁移到新snapshot。
- 两个write-capable workers仍不得同时修改同一file。Validation runner不因产生runtime evidence而取得
  repository writer authority。

## Entry Gates

开始任何 implementation milestone 前：

1. 重新读取 repository rules、contract matrix、Harness policy、runtime baseline与本spec/plan。
2. 检查 `git status`、live agents、exact target-file ownership；same-file overlap必须由用户决定顺序。
3. 记录 problem boundary、single owner、old path、unchanged contracts与focused verification command。
4. Local implementation authority不自动授权live generation；计划执行到 live gate 时重新核对当前用户scope。
5. Remote/paid Seedance work必须另有 task-scoped authorization、fresh pricing/budget、Cloud Egress、durable
   intent与one-use permit；不得复用历史authorization或permit。
6. Model/artifact inventory必须记录 exact filename、bytes、SHA-256、license/provenance、ComfyUI/T8 commit、
   node schema与profile hashes；缺项保持unavailable。

## Parallel Execution Model

### Phase P0 — Shared Freeze

Milestone 3先冻结fresh inventory receipt、calibration fixture、exact `RealShotValidationSet`、每个edge的
boundary/continuity obligation、references、prompt、Stock20参数、rubric、candidate stack payloads与effect
budget。P0是
两个lane的共同前置条件；冻结前不得启动M0 generation，也不得创建final Production capability identity。

### Phase P1 — Qualification and Safe Implementation in Parallel

P0完成后并行推进：

| Lane | Allowed work | Forbidden work |
| --- | --- | --- |
| Implementation I1 | Milestone 1 C4 regression；Milestone 2 Seedance base-only isolation；execution-stack RED contract；Milestone 5的candidate-neutral child/family denial tests与fake transport seam | 不确定winner前不得封最终`execution_stack_hash`或active capability；不得修改Validation正在消费的sealed candidate bundle |
| Validation V1 | Milestone 4 M0 single-boundary attempt；M0失败时按gate执行conditional M1；保存exact technical与human evidence | 不修改source/tests/workflow/profile；不重试、不fallback、不边看结果边改阈值 |

I1可以先写winner-independent tests和interfaces，但所有包含`ref2va-stock20`或`hybrid-stock20`的Production
files/exports/active snapshot必须等Join Gate J1。

### Join Gate J1 — Select One Winner

J1只接受M0或M1中一个满足frozen gates的candidate：

- winner `GenerationExecutionStackIdentity`、model-qualification evidence与profile preflight全部sealed；
- loser保持experimental evidence，不进入Production snapshot；
- 两者都失败则停止Local destination implementation，不用Implementation lane的进度倒逼quality PASS；
- unknown outcome先走explicit recovery，J1保持open。

J1关闭后，Implementation lane才可完成Milestone 5 winner-specific child与Production exports。

### Phase P2 — Production Integration and Multi-Shot Pilot in Parallel

Milestone 5形成一个task-only checkpoint，并通过focused tests、preflight与exact Harness后，冻结为
`validation_snapshot`。随后并行推进：

| Lane | Allowed work | Snapshot rule |
| --- | --- | --- |
| Implementation I2 | Milestone 6 fake lifecycle、recovery、replay、P5与documentation preparation | 可在与selected stack components不重叠的files继续；若修改validation snapshot或stack payload中的任何bytes，必须产生新checkpoint并使旧Pilot不具备promotion资格 |
| Validation V2 | Milestone 7先复核single boundary，再用selected ProductionProject中的3–4个canonical real Shots、至少2个continuity edges做single-stack raw full-speed Pilot | 全程固定commit/execution_stack_hash/RealShotValidationSet/policies/rubric；one submit per generation，no retry，no fallback；synthetic-only fixture不得promotion |

Validation V2不得在I2尚未commit的working tree上运行，也不得把later code changes与earlier media receipts拼成
同一acceptance bundle。

### Join Gate J2 — Destination Acceptance

只有I2 lifecycle/replay/P5 evidence与V2 boundary/identity/motion/P6/human evidence同时绑定同一或可证明
byte-identical的validation snapshot，才能达到`C4_DESTINATION_READY`。若I2在Pilot后改变任何semantic或
`execution_stack_hash`或semantic identity，必须重跑受影响的V2 gates。

### Phase P3 — Transition Work

J2关闭后才开始Milestone 8 boundary policy、directed qualification与per-attempt evidence。Milestone 9 Seedance semantic lane可独立
准备formal evidence，但不得作为Local失败fallback，也不得在J2前被用来声称multi-provider readiness。

## Milestone 1: Reconfirm C4 Core Closure

### Work

先运行现有 C4 suites，证明当前 core 已覆盖：

- exact three/four-anchor cardinality；
- Registry revision、target Shot、role/order/hash/materialization tamper；
- one selected capability，禁止sub-capability union；
- C1/C2/C3与legacy hash/reopen compatibility；
- denial发生在compiler/preview/permit/POST之前且effect count为零。

若全部GREEN，不修改stable core；直接保存baseline并进入Milestone 2。只有出现可复现RED时，才在canonical
owner内做最小修正并添加regression test。

### Verification

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_video.py \
  tests/test_production_video_requirement.py \
  tests/test_production_shot_router.py \
  tests/test_production_provider_neutral_adapters.py -q
```

### Exit Criteria

`C4_CORE_READY`保持成立；不得因此升级Provider、live或quality claim。

## Milestone 2: Isolate Seedance 2.0 Active Inventory

### RED

在`tests/test_production_seedance.py`先固定：

1. base-only entitlement生成的active profile只暴露`doubao-seedance-2-0-260128`；
2. pricing model set与selected capability model set必须exact match；缺失或多余均拒绝；
3. Fast/Mini catalog entry存在不能使其进入active snapshot；
4. family alias、cross-model profile reuse、wrong endpoint/deployment与response model mismatch拒绝；
5. base-only 1080p/4k request若绑定Fast/Mini profile，在preview/permit/POST前失败且effect count为零；
6. exact model切换产生新的profile/request/permit/attempt identity，不继承另一model acceptance；
7. existing base/Fast/Mini mode-specific compiler behavior继续通过。

### GREEN

把official catalog与active account profile分开：

- catalog validation继续证明每个selected entry与authoritative matrix一致；
- `SeedanceProviderProfile`接受official catalog的non-empty exact subset；
- pricing只覆盖selected subset，不再要求全局model集合；
- Production profile assembly显式选择base model capabilities，不依赖`create_default()`；
- Provider在compile、preview、submit/status/fetch与response reopen各阶段都绑定same exact model identity。

不得通过删除Fast/Mini catalog tests或把base bounds复制给其他models来达成GREEN。

### Verification

```bash
python -m pytest -p no:cacheprovider tests/test_production_seedance.py -q
```

### Exit Criteria

能够诚实声明“接口transport共用，model contract独立；本计划只组装fresh entitlement允许的base target”。
Actual active inventory仍由runtime baseline/profile snapshot拥有，也不证明任何Seedance 2.0 model支持exact
four-role union。

## Milestone 3: Freeze Local T8 Candidate Qualification

本milestone是Parallel Phase P0，由两个lane共同消费；不得把它分成两份各自漂移的fixture、profile或
rubric。

### Inventory Preflight

生成read-only inventory report，绑定：

- fresh ComfyUI与T8 plugin commit/version/license；
- Hybrid conditioning nodes/input schemas；
- installed stock Ref2VA identity；
- M1所需 exact validated pruned FL2VA/Ref2VA pair是否存在；
- Hybrid artifact/sidecar是否存在；
- CLIP、video/audio VAE、sampler、scheduler与output node identity；
- literal loopback endpoint与remote/fallback disabled flags。

缺失M1 pair/artifact不阻塞M0；不得把任何未被builder/receipt明确支持的model pair扩宽为已验证M1输入。

### Execution Stack Freeze

为M0与M1分别构造candidate `GenerationExecutionStackIdentity` payload，覆盖provider/deployment、model、
capability、profile、compiler、workflow、checkpoint/artifact、LoRA、sampler/scheduler、plugin/runtime与output
contract。验证：

- 任一component变化都会改变`execution_stack_hash`；
- M0与M1即使共享Provider/transport也必须拥有不同hash；
- local path与secret不进入hash；missing component使用canonical empty representation；
- candidate hash在J1前只标记`qualification candidate`，不得进入active capability snapshot。

### Qualification Fixture

在观看结果前冻结一个exact四锚点fixture、prompt、resolution、frame count、FPS、Stock20参数与rubric。
Compiler/workflow tests必须证明：

```text
first_frame      -> Hybrid conditioning first_frame
last_frame       -> Hybrid conditioning last_frame
reference        -> ref_images.ref_image_0
reference_video  -> ref_videos.ref_video_0
ref_video_audios -> empty
ref_audios       -> empty
task_type        -> literal Hybrid
```

### Real Shot Validation Set

Technical fixture之外，同时从一个selected `ProductionProject` revision冻结3–4个canonical narrative Shots，
至少形成2个`FULL_CONTINUITY` edges。记录exact Character、Scene、Shot revisions、Registry/materialization
identities、每个edge的`ContinuityTransitionPolicy`、terminal/identity/endpoint/motion-tail来源、prompt、output
geometry与predeclared rubric。Validation set必须固定同一主角与scene，并分别覆盖subject motion与camera
motion；临时占位图、synthetic-only assets或prompt-only identity不能进入promotion set。

### Exit Criteria

形成content-addressed qualification inputs、`RealShotValidationSet`、boundary policies、两个明确candidate
stack payloads与P0 freeze receipt；尚未生成媒体时只能报告`qualification prepared`。P0关闭后可同时启动
Implementation I1与Validation V1。

## Milestone 4: Execute M0, Then Conditional M1

本milestone属于Validation V1。它只验证单个continuity boundary的model/conditioning feasibility，不等待
完整Production child，也不替代Milestone 7的multi-shot Pilot。

### M0 — Stock Ref2VA Control

在Local live authority仍有效且preflight全通过时，只提交一次M0：

- exact four anchors；
- stock Ref2VA；
- T8 Hybrid conditioning；
- Stock20、`dual_clock_euler`、`native_flow`；
- Turbo off、reference audio empty；
- one local permit、one submit、no retry、no fallback。

记录M0 `execution_stack_hash`、workflow execution、output/probe、decoded boundaries、identity windows、
motion windows与P6/human verdict。

### M0 Decision

- 所有frozen technical、boundary、identity、motion与P6 gates通过：M0是winner，跳过M1。
- 任一gate失败：保留exact failure evidence，不调整阈值、不隐式重试；只有满足M1 inventory gate才进入M1。
- Unknown outcome：走existing explicit recovery，不把它解释为quality failure或重试许可。

### M1 — Sealed Hybrid Artifact

仅当M0未通过且exact validated pruned pair可用时执行：

1. explicit inventory-preparation operation构建artifact与sidecar；
2. build receipt绑定source hashes、builder source/recipe、selected blocks/modalities、tensor keys/shapes/
   dtypes、curve hashes、output bytes/size/hash；
3. runtime只reopen/rehash/verify/consume；missing/tampered artifact保持blocked；
4. 生成独立M1 `execution_stack_hash`，使用与M0相同fixture、Stock20与rubric进行one-submit验证。

不得自动build、quarantine后自动修复、stock fallback、cloud fallback或用Turbo改变归因变量。

### Exit Criteria

最多一个candidate被选为Production implementation winner。两个都失败时本计划在Local destination gate
保持blocked，不注册C4 capability。Winner evidence关闭Join Gate J1；在此之前Implementation I1只能完成
candidate-neutral work。

## Milestone 5: Implement Execution Stack Identity and Winner-Specific Local C4 Child

### RED

在`tests/test_production_comfy_t8_hybrid_c4_video.py`固定：

- `GenerationExecutionStackIdentity` canonical fields/hash与winner exact stack一致；
- 同Provider但不同checkpoint、LoRA、compiler、workflow、sampler/scheduler或plugin产生不同stack hash；
- stack hash进入resolved request、intent、provenance与replay validation，drift在Provider effect前拒绝；
- capability ID/model/profile/task type与winner exact identity一致；
- exact 1/1/1/1 cardinality，audio/missing/duplicate/extra/wrong-order全部拒绝；
- workflow node bindings与payload order deterministic；
- ref video audio与standalone reference audio永远为空；
- model/node/workflow/binding/profile/output hash drift在upload/submit前拒绝；
- request只能使用`IMAGE_TO_VIDEO + MULTI_ANCHOR`；
- compile/resolve/preview纯deterministic，preflight无Provider effect；
- one-use local permit、loopback-only endpoint、no remote/fallback。

上述winner-independent RED cases可在Implementation I1编写。包含winner capability ID、model identity、
artifact requirement或final workflow filename的expected values必须在J1关闭后一次性冻结，不能由I1猜测。

### GREEN

实现`video_execution_stack.py`与winner-specific profile、workflow和child：

- stack module只拥有immutable construction/hash/reopen validation，不拥有selection、lifecycle或quality；
- 不改写existing FL2VA/Ref2VA child identity；
- child拥有workflow rendering、native mapping、profile preflight与ComfyUI transport actions；
- family只聚合capabilities并按capability/resolved identity exact dispatch；
- durable lifecycle继续由service/committer拥有；
- profile seal包含全部model/artifact/node/workflow/sampling/output/locality identities。

### Family Verification

在`tests/test_production_local_h3_provider_family.py`证明：

- capability IDs/identities disjoint；
- deterministic snapshot ordering；
- selected C4 request只到C4 child；
- restart无last-selected state；
- C4 child failure不调用其他local child或remote Provider。

### Verification

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_comfy_t8_hybrid_c4_video.py \
  tests/test_production_video_execution_stack.py \
  tests/test_production_local_h3_provider_family.py \
  tests/test_production_shot_router.py \
  tests/test_production_provider_neutral_adapters.py -q
```

### Validation Snapshot Checkpoint

Milestone 5完成后必须先建立task-only commit，并对exact commit range完成focused tests、profile preflight、
Harness与receipt verification。该commit及其`execution_stack_hash`构成唯一
`validation_snapshot`；Milestone 7不得消费unstaged working tree或later unsealed edits。

## Milestone 6: Close Lifecycle, Replay and P5

### Work

使用fake local transport与sealed fixtures覆盖：

- compile -> resolve -> preview -> preflight -> intent/permit -> submit/status/fetch；
- before-submit、accepted、known-no-effect、outcome-unknown、fetched、validated、candidate与activation crash
  points；
- activation后Project/Registry/graph/Manifest一致；
- reopen重验request/`execution_stack_hash`/input/output hashes；
- exact replay的Provider、extraction、activation与render effect count均为零；
- terminal/identity/endpoint/motion-tail任一变化只stale target generation与真实composition/render closure；
- unlinked Shots、voice、captions与unrelated assets保持fresh；
- local evidence不进入paid lifecycle，paid evidence不进入local attempt。

只有RED证明existing owner有缺口时才修改committer、dependency或lifecycle production files。

### Verification

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_local_video_state.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py -q
```

## Milestone 7: Full Four-Anchor Local Acceptance

本milestone属于Validation V2，可以与Milestone 6中不修改`validation_snapshot` bytes的work并行。

### Technical Smoke

对winner执行一个single request：

```text
one first_frame
one last_frame
one reference image
one reference video
one prompt
one exact execution_stack_hash
one submit
no retry
no fallback
```

保存exact input SHA-256、Registry identities、request/resolved/fingerprint、`execution_stack_hash`、
submit/status/fetch receipts、output/probe、decoded first/last frame hashes与replay counters。

Single-boundary technical smoke通过后，使用同一sealed snapshot和Milestone 3冻结的
`RealShotValidationSet`继续3–4 Shot single-stack Pilot：

- 所有Shots来自同一selected `ProductionProject` revision中的canonical Character/Scene/Shot artifacts；
- 至少3个Shots与2个continuity edges，同一canonical character与scene，包含一次明显subject motion和一次
  明显camera motion；
- inputs全部来自exact Registry revision与provenance/materialization receipts，不接受临时未登记或
  synthetic-only素材；
- 每个generation各自one submit、no retry、no fallback；
- 每个edge分别记录exact anchors、boundary/identity/motion evidence，不用平均分掩盖单edge失败；
- 最终以raw cuts按full-speed sequence review累计identity、wardrobe、style、camera velocity、action phase与
  空间叙事连续性；crossfade、optical flow、interpolation、retime或重构图只能出现在标明用途的derivative，
  不得进入acceptance evidence。

### Quality Gates

- Boundary：decoded frame 0与terminal frame分别计算frozen PSNR/SSIM/perceptual metrics，保存side-by-side与
  crop evidence；native role不夸大为pixel-identical。
- Identity：first/middle/last windows检查face/subject、hair、clothes、props、body scale与drift；backend
  coverage不足时为`NOT_EVALUATED`。
- Motion：检查subject/camera direction与velocity、action phase、entrance/exit、unexpected stop/re-entry；
  单帧metric不得代替motion evidence。
- Automatic evaluator（High/experimental）：若available可保存bounded measurements；缺backend、coverage不足
  或`NOT_EVALUATED`不阻塞本milestone，但必须由同一frozen rubric要求的exact human evidence补足。不得把
  automatic match当作Final Acceptance或扩大qualification envelope。
- P6/Human（Critical）：消费exact request/output/anchors、technical/strategy/semantic evidence与human
  verdict；只有P6是Final Acceptance owner。缺完整human coverage时不得promotion。

### Exit Criteria

只有technical smoke和真实Shot Pilot全部通过后达到`C4_DESTINATION_READY`。任何quality dimension
rejection、`NOT_EVALUATED`缺human fallback、synthetic-only或临时素材、
unknown outcome或incomplete evidence都保持`experimental / unavailable`。Promotion bundle必须同时包含
Milestone 6的I2 evidence与本milestone的V2 evidence，并证明二者绑定same/byte-identical
`validation_snapshot`，从而关闭Join Gate J2。

## Milestone 8: Establish Directed Stack Qualification and Attempt Evidence

### Boundary Policy RED

先固定`ContinuityTransitionPolicy` behavior，所有denial均发生在compiler/preview/permit/POST之前且effect count
为零：

1. `WITHIN_CONTINUOUS_TAKE`只能使用一个exact `execution_stack_hash`；stack或take membership漂移即拒绝；
   失败后从中间frame换stack也拒绝；
2. `HARD_CUT + FULL_CONTINUITY`跨stack但缺fresh applicable qualification时拒绝；
3. `HARD_CUT + IDENTITY_STYLE_CARRYOVER`只消费approved exact references与普通QA，不能获得C4 claim；
4. `SCENE_BOUNDARY + IDENTITY_STYLE_CARRYOVER`必须有非空dimensions、逐项Registry/materialization
   references、destination role capability与QA policy；缺任一项拒绝；
5. `SCENE_BOUNDARY + SUBSTANTIAL_RESET`必须有approved scene/time/state reset evidence且dimensions为空；只凭
   structural scene change、stack change或事后质量失败标记reset时拒绝；
6. policy kind/obligation无效组合、tamper、wrong Shot/Timeline或changed reference/QA hash均拒绝；
7. approved whole-take regeneration或新authoring revision插入visible hard cut会形成新policy/attempt identity，
   不复用失败attempt effect token。

若logical contract无法在现有Project/Shot intent、ResolvedTimeline与immutable evidence seam内表达，必须在
schema/layout edit前触发Decision Gate；不得先把`SCENE_BOUNDARY`硬编码成reset。

### Persistence and Applicability RED

先用tests验证existing immutable evidence + Manifest pointer能否表达stack、qualification与attempt三个不同
artifacts，且不新增writer或mutable lifecycle：

- stack hash覆盖全部execution components；qualification hash覆盖source/destination stack hashes、grade、
  applicability、rubric、validation-set evidence、limitations与normalization，但不把某一Production Shot edge
  当作复用key；
- attempt hash覆盖exact source/target Shots、policy、anchors、qualification ID/applicability proof、selected
  stack、output与P6/human evidence；
- reverse direction、不同stack/grade/applicability/rubric或changed output normalization产生不同qualification；
- out-of-envelope、pointer tamper、missing validation evidence、source未activated/P6未接受、destination未ready
  全部fail closed；
- replay只reopen/revalidate，不重复Provider或committer effect。

若无需schema/layout migration，按File Map实现`video_transition.py`与现有committer pointer seam。若需要
Manifest/artifact migration，在任何production schema edit前停止并触发Decision Gate。

### Qualification Validation Set

只对已有accepted source outputs、exact terminal/motion-tail derivation与ready destination stack建立
qualification。为一个directed stack pair冻结versioned content/risk predicate，至少覆盖subject count/
identity burden、occlusion、wardrobe/style、shot scale、subject/camera motion regime与duration。Validation set
必须来自selected `ProductionProject`中的canonical real Shots与visible
`HARD_CUT + FULL_CONTINUITY`，使用same/byte-identical destination snapshot和frozen rubric；synthetic-only、
rejected或unactivated source不合格。每个validation edge独立运行：

1. source evidence reopen；
2. exact anchor derivation/materialization；
3. explicit qualification-validation intent下的one-submit/no-retry/no-fallback destination generation；
4. raw-cut full-speed normalization、boundary、identity、wardrobe/style、motion与P6；
5. 保存exact validation evidence；在全部required dimensions通过后seal
   `ProviderTransitionQualification`并验证reopen/replay。

Validation runs在qualification seal前不得授权普通Production routing。Reverse direction、out-of-envelope
content与不同stack不自动成立。

### First Qualified Production Attempt

Qualification seal后，以一个新的canonical real Shot edge验证Router查询和attempt evidence seam：

1. exact policy解析source/destination stack hashes与Shot content/risk classification；
2. Router命中qualification并验证applicability，preview/permit/POST前保存qualification identity；
3. one submit、no retry、no fallback；
4. 保存exact source/target Shots、anchors、request/resolved、stack hashes、output/provenance、QA/human/P6；
5. seal并reopen `TransitionAttemptEvidence`；exact replay不重复Provider、human或committer effects。

同一qualification下的后续Shots仍各自产生attempt evidence；首个attempt PASS不能替代它们的P6/human gate。

### Exit Criteria

至少一个source/destination stack pair完成bounded qualification且一个匹配的real Production edge保存
`TransitionAttemptEvidence`后，达到`DIRECTED_TRANSITION_READY`。声明必须写出stack direction、grade、
applicability envelope与limitations；仍不能说“多个destination可流畅切换”，也不能外推到continuous take、
scene carryover、scene reset或out-of-envelope content。

## Milestone 9: Optional Base Seedance 2.0 Semantic Destination

这是独立Grade S lane，不是Local Grade E失败后的fallback。

### Formal Evidence Gate

必须先取得base `doubao-seedance-2-0-260128` exact model-specific、dated contract，证明同一reference
request允许opening image、ending image、identity image与motion video的semantic union，并冻结counts、
duration、resolution、audio、payload与response semantics。Adapter能序列化字段不满足此gate。

### Implementation and Paid Gate

Formal evidence完整时才可新增独立Grade S capability/profile/compiler tests；request必须明确opening/ending
只是semantic references。任何remote live probe还需要fresh entitlement、pricing、budget、Cloud Egress、
durable intent与one-use permit，且最多一次POST、no retry、no fallback。

Formal evidence缺失、profile/materialization不完整或用户未授权时，保持pre-preview/POST fail closed，不修改
exact Grade E seal。

### Exit Criteria

通过transport、lifecycle、semantic boundary/identity/motion与P6后，只能声明base model的
`C4_SEMANTIC_MULTI_REFERENCE` destination ready。它与Local Grade E不是同一grade，不能合并为
`SAME_GRADE_MULTI_DESTINATION_READY`。

## Milestone 10: Same-Grade Boundary-Aware Multi-Destination Gate

达到“在已通过qualification的visible hard-cut directions上具备同等级boundary-aware Provider
portability”前，必须存在至少两个不同`provider_kind/deployment`的destination execution stacks，各自：

- 使用同一provider-neutral grade、同一canonical `RealShotValidationSet`与frozen rubric；
- 拥有独立`GenerationExecutionStackIdentity`、capability/pricing/evidence；
- 通过compile、denial、lifecycle、live、boundary、identity、motion、P6与replay；
- 通过deterministic explicit selection与no-fallback tests；
- 对每个声明的source direction与content/risk class拥有独立real-Shot hard-cut qualification，并保存至少
  一个匹配的`TransitionAttemptEvidence`；
- 保持`WITHIN_CONTINUOUS_TAKE` cross-stack denial，并分别验证scene carryover references/QA与
  `SUBSTANTIAL_RESET` evidence；不得把本milestone解释为任意边界自由切换。

本milestone是hard claim gate，不可由一个destination或不同grade的destination单独关闭。Execution-time
baseline若尚无第二个same-grade stack，保持pending；出现formal evidence后，必须更新本计划的exact stack/
content-risk scope再执行。

## Milestone 11: Documentation, Review and Exact Verification

### Documentation Closure

按实际完成层级同步：

- `docs/v0.2-runtime-baseline.md`：implemented、live、quality、P6与unavailable truth；
- `docs/v0.2-agentic-production-roadmap.md`：remaining gates；
- `docs/agent-primary-contract-matrix.md`：new surface owner与禁止旁路；
- `.agent/harness/policy.yaml`/`tests/test_agent_harness.py`：只有changed-path routing需要时同步。

不得把plan、workflow文件、offline tests或single Provider success写成Production/multi-provider acceptance。

### Independent Review

Core behavior、Provider gating、paid/profile isolation、transition persistence或fallback behavior发生变化后，
使用native named `reviewer`检查：

- one-capability C4 grammar是否真实；
- Seedance catalog与active inventory是否分离且cross-model fail closed；
- Local candidate qualification是否存在隐式fallback或identity substitution；
- execution stack是否覆盖所有distribution-relevant components；
- qualification与attempt evidence是否分层，且都不是第二state owner；
- qualification applicability是否会拒绝unknown/out-of-envelope content；
- replay/recovery/P5与historical compatibility是否保持；
- tests是否覆盖真实failure mode而非只验证serializer。

Parent必须复核blocking claims并关闭问题。

### Exact Verification

每个code checkpoint：

1. 运行focused tests与`git diff --check`；
2. 只`git add <exact-task-files>`；
3. 运行Harness inspection；
4. 对non-empty exact staged snapshot或exact commit range运行Harness；
5. 验证receipt integrity/freshness；
6. 只commit task-owned files，不push/release。

Harness不执行Provider、paid call、media generation或P6；receipt只能证明对应offline code/control-plane gates。

## Acceptance Criteria

### `C4_CORE_READY`

- Existing provider-neutral contract、hash、cardinality与Router tests保持GREEN。

### `C4_DESTINATION_READY`

- 一个winner-specific Local T8 child完成stack/profile preflight、fake lifecycle、full four-anchor local smoke、
  selected ProductionProject中的3–4个canonical real Shots、至少2 edges的raw full-speed single-stack Pilot、
  activation/reopen/replay、boundary/identity/motion与P6/human acceptance；
- Implementation与Validation evidence绑定same/byte-identical sealed snapshot，Join Gate J2关闭。

### `DIRECTED_TRANSITION_READY`

- 至少一个source/destination `execution_stack_hash` direction拥有fresh bounded
  `ProviderTransitionQualification`；其validation set来自canonical real Shots之间的visible
  `HARD_CUT + FULL_CONTINUITY`并覆盖声明的content/risk envelope；
- 至少一个匹配qualification的real Production edge保存PASS `TransitionAttemptEvidence`。

### `SAME_GRADE_MULTI_DESTINATION_READY`

- 同一grade至少两个不同`provider_kind/deployment`的destination stacks使用同一canonical
  `RealShotValidationSet`与frozen rubric完成独立sealed capability与全部acceptance；
- explicit selection、denial、reopen、replay与no-fallback tests通过。

### `FULL_MATRIX_READY`

- 每个对外声明支持的directed stack pair/content-risk class都拥有独立fresh qualification及至少
  一个匹配的PASS `TransitionAttemptEvidence`。
- `WITHIN_CONTINUOUS_TAKE`仍保持cross-stack denial；`SCENE_BOUNDARY`仍分别执行carryover references/QA或
  approved `SUBSTANTIAL_RESET` contract。

低层级不得代替高层级。Local T8 child完成后最多升级到`C4_DESTINATION_READY`；加一个cross-stack
qualification与matching attempt后最多升级到`DIRECTED_TRANSITION_READY`。在第二个same-grade destination
通过前，最终交付必须明确写“尚不能声称在已通过qualification的hard-cut directions上具备同等级
boundary-aware Provider portability”。

## Verification Matrix

| Gate | Minimum executable evidence |
| --- | --- |
| Core/cardinality | missing/duplicate/extra/wrong-order/tamper/sub-capability-union zero-effect tests |
| Seedance isolation | base-only snapshot、pricing/profile exact set、bounds、endpoint、response model与cross-model denial |
| Execution stack | canonical absent fields、all component drift、same-provider/different-checkpoint inequality、resolved/provenance/replay binding |
| Local inventory | fresh ComfyUI/T8/model/artifact/node/workflow/profile hashes与license/provenance，记录于preflight receipt而非spec |
| Workflow/compiler | literal Hybrid、exact four mappings、empty audio、deterministic payload/output |
| Lifecycle | permit、submit/status/fetch、unknown recovery、candidate/activation/reopen/replay |
| P5 | four exact inputs的precise closure；unrelated assets保持fresh |
| Local live | one request、one submit、no retry、no fallback，全部input/output hashes |
| Boundary policy | continuous-take stack lock；unqualified hard-cut denial；scene carryover reference/QA denial；scene reset evidence/tamper denial |
| Real Shot Pilot | selected ProductionProject的3–4 canonical Shots、至少2 edges、same snapshot、raw cuts、逐edge evidence与full-speed cumulative drift review |
| Boundary | decoded frame 0/terminal evidence，native role与pixel equality分开 |
| Identity | multi-window subject/appearance/drift；不足为`NOT_EVALUATED` |
| Motion | direction、velocity、phase、entrance/exit、stop/re-entry |
| P6/Human | Critical exact evidence + human verdict，由P6唯一给Final Acceptance；automatic evaluator可缺失 |
| Qualification | source/destination stack hashes、grade、applicability、rubric、real-Shot validation set、limitations、staleness与out-of-envelope denial |
| Attempt | exact Shots/output/anchors/policy/qualification ID/applicability proof/selected stack/QA/P6 evidence与replay |
| Harness | exact staged snapshot或commit range的fresh passing receipt |

## Execution Order

```text
P0 / Milestone 3
freeze inventory + RealShotValidationSet + policies + stack payloads + rubric
                     |
          +----------+----------+
          |                     |
Implementation I1          Validation V1
Milestone 1               Milestone 4
Milestone 2               M0 single edge
Milestone 5 RED/common     conditional M1
          |                     |
          +----------+----------+
                     |
              Join Gate J1
              select one winner
                     |
              Milestone 5 GREEN
              sealed child checkpoint
                     |
          +----------+----------+
          |                     |
Implementation I2          Validation V2
Milestone 6               Milestone 7
lifecycle/replay/P5       3-4 real Shot Pilot + P6
          |                     |
          +----------+----------+
                     |
              Join Gate J2
              C4_DESTINATION_READY
                     |
              Milestone 8
              stack qualification + matching attempt evidence

Milestone 9  optional base Seedance semantic lane
Milestone 10 same-grade second-destination claim gate
Milestone 11 docs/review/Harness at every checkpoint
```

并行表示wall-clock overlap，不表示dependency消失。Milestone 4必须在P0冻结后进行；Milestone 5不得在
J1前创建final Production stack identity；Milestone 7只消费sealed checkpoint；Milestone 8必须在J2后进行；
Milestone 9不阻塞Local Grade E，也不得成为其fallback。任何same-file writer overlap仍在写入前由用户决定
ownership或顺序。

## Rollback and Failure Policy

- Candidate失败：保留evidence，capability保持unavailable，不改阈值、不替换`execution_stack_hash`。
- Local unknown outcome：existing explicit recovery；不blind retry、不remint permit。
- Hybrid artifact missing/tampered：attempt blocked；runtime不build/repair/fallback。
- Seedance entitlement/profile/pricing不完整：active snapshot不暴露model；preview/POST effect count为零。
- Provider response model mismatch：fail closed，不接受family-compatible替代。
- Grade E quality失败：不自动改为Grade S。
- Continuous-take attempt失败：只允许一个exact stack重生成整个sealed take，或由approved authoring
  revision新增visible hard cut后创建新policy/attempt；不得中途换stack。
- Scene boundary仍有identity/style carryover：保留exact references并过普通QA；不得事后改标
  `SUBSTANTIAL_RESET`逃避失败gate。
- Qualification tamper/stale/out-of-envelope：Router在effect前拒绝；attempt evidence tamper拒绝本次claim，
  两者都不影响canonical source/destination lifecycle truth。
- Persistence需要migration：在schema/layout edit前停止并请求Decision Gate。
- Reviewer/Harness失败：修复并重新验证exact snapshot，不用旧receipt覆盖。

## Final Definition of Done

本计划的第一可交付终点是：

- Seedance 2.0 shared transport与base/Fast/Mini exact model isolation已实现；本计划只组装base target，actual
  active inventory仍严格等于fresh entitlement/profile/pricing subset；
- `GenerationExecutionStackIdentity`贯穿resolve、intent、provenance、qualification、attempt与replay；
- boundary kind与continuity obligation分离，continuous-take lock、scene carryover与substantial-reset gates均有
  executable zero-effect tests；
- Local T8一个winner-specific C4 destination通过canonical 3–4 real Shot Pilot并达到
  `C4_DESTINATION_READY`；
- 至少一个source/destination stack pair完成bounded real-Shot qualification，并由一个matching Production
  edge的`TransitionAttemptEvidence`达到`DIRECTED_TRANSITION_READY`；
- canonical docs、independent review与exact Harness receipts完成；
- 未购买、未授权、未验证或不同grade的routes继续fail closed。

并行执行本身不构成acceptance。Final evidence必须证明Implementation I2与Validation V2绑定同一或
byte-identical `validation_snapshot`；若candidate `execution_stack_hash`、RealShotValidationSet、boundary
policy、references或rubric在Pilot期间漂移，相关Pilot必须重新运行。

这仍不等于“多 Provider destination可以任意流畅切换”。只有Milestone 10的第二个same-grade destination
和对应real-Shot hard-cut qualifications/attempt contracts真正完成后，才能升级为已验证的boundary-aware portability；只有完整
声明矩阵逐项通过qualification和matching attempt后，才能称`FULL_MATRIX_READY`。任何层级都不授权continuous-take cross-stack，换场也
必须先区分carryover与approved reset。
