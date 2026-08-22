# AI-VIDEO Shot Continuity Implementation Plan

## Status

Active canonical implementation plan，governed by
[Shot Continuity Specification](../specs/2026-08-19-ai-video-shot-continuity.md)。

截至 2026-08-22，C1/C2/C3、terminal evidence、provider-neutral C4 binding、request/resolved
hash、exact cardinality grammar 与 Router fail-closed gate 已实现；当前等级为
`C4_CORE_READY`。未完成项集中在 concrete destination capability、完整四锚点 local smoke、
boundary/identity/motion quality evidence、P6 Final Acceptance，以及有向 Provider transition
certification。

本计划替换旧版中“重新实现 C4 core”和“以 Seedance Mini 作为 C4 destination”的过时步骤。历史
Hailuo 与 Seedance Mini attempts 继续作为 runtime record；它们不再决定 future capability target，也不
构成 C4 或多 Provider acceptance。

本轮只更新 plan。Plan 本身不授权 runtime implementation、模型安装/融合、ComfyUI 升级、local live
generation、remote/paid preview/POST、permit、activation、push 或 release。

2026-08-22进一步接受“验证与实现同时推进”的execution strategy，但并行只发生在明确分离的
Implementation lane与Validation lane。Validation必须绑定immutable checkpoint，不得在同一次attempt期间
读取正在变化的source/workflow/profile；并行执行不会放宽Provider、permit、P6或same-file ownership gates。

## Goal

按一个可验证、无 fallback 的顺序交付：

1. 保持现有 provider-neutral C4 core 为唯一四锚点合同；
2. 资格判定并实现一个 Local T8 `C4_NATIVE_BOUNDARY_MOTION` destination child；
3. 把已购买的 base `doubao-seedance-2-0-260128` 与 Fast/Mini 分离为 exact model contracts，active
   inventory 默认只暴露 base；
4. 用 immutable directed certification 表达具体的
   `source provider/model/profile/capability -> destination provider/model/profile/capability` transition；
5. 只有至少两个不同 destination Providers 在同一 grade 上分别通过全部 gates，才允许声明
   `SAME_GRADE_MULTI_DESTINATION_READY`。

目标不是 runtime 自动选模、失败降级或“任意 Provider 一键互换”。Planner/Router 只可显式选择已经
sealed 且对 exact grade、model、profile 与 direction 完成认证的 destination。

## Scope

### Included

- C4 core regression/tamper closure，不重复实现已存在的 owner；
- Local T8 C4 model qualification：M0 stock Ref2VA，必要时 M1 sealed Hybrid artifact；
- winner-specific workflow、binding、profile、capability 与 local child adapter；
- `LocalH3VideoProviderFamily` additive child registration 与 exact dispatch；
- local lifecycle、recovery、activation、reopen、replay 与 P5 closure；
- four-anchor technical smoke、decoded boundary、identity、motion 与 P6/human evidence；
- directed `ProviderTransitionCertification` persistence seam 与 exact pair certification；
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
- 不购买或启用 Fast/Mini；无 fresh entitlement 时它们不得进入 active snapshot；
- 不在第一版启用 Turbo LoRA；
- 不自动构建、修复或替换 Hybrid artifact；
- 不升级 pinned ComfyUI 或引入 `MiniMaxH3AddGuide`；
- 不引入 remote/cloud fallback，不进行 blind retry；
- 不改变 Legacy CLI、default no-network、HyperFrames 或 `ResolvedTimeline` ownership；
- 不把 transport success、hash closure、SSIM、reviewer verdict 或 fetched artifact当作 P6 Final
  Acceptance；
- 不承诺 `FULL_MATRIX_READY`，除非所有对外声明的有向 pair 都有独立 certification。

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

### Seedance 2.0 Model Isolation Contract

base、Fast 与 Mini 复用 Ark async task transport 和 `SeedanceVideoProvider` submit/status/fetch lifecycle，
但绝不是 drop-in interchangeable capabilities。每个 model 必须独立 seal：

- exact `model_id`、API deployment/endpoint identity 与 expected response model；
- exact mode 与 allowed role/cardinality grammar；
- resolution、duration、FPS、container、reference bounds 与 audio behavior；
- profile version、pricing snapshot、egress preview、permit 与 resolved request hash；
- offline compiler、live receipt、quality 与 P6 evidence。

当前 accepted active inventory 只包含 base `doubao-seedance-2-0-260128`。Fast/Mini 仍可保留在 provider
catalog 和 compatibility tests 中，但没有 fresh entitlement、pricing 和 exact profile evidence时不得出现在
active `SeedanceProviderProfile.capabilities` 或 Router snapshot。

### Transition Certification Contract

每个可声明的 direction 必须拥有 immutable、content-addressed
`ProviderTransitionCertification`，至少绑定：

- exact source provider/model/profile/capability、accepted output与P6 evidence；
- exact destination provider/model/profile/capability；
- selected continuity grade 与 exact anchor contract hash；
- terminal/motion-tail derivation与materialization receipts；
- output normalization contract；
- technical/live/boundary/identity/motion/P6 evidence；
- certification schema/version/content hash。

Certification 是 evidence，不是第二 lifecycle owner。Active pointer、candidate、activation 与 recovery 仍只由
`ProductionStateCommitter`/Production Manifest 拥有。

## Invariants

- `ResolvedTimeline` 是唯一 order/frame/sample/timing owner。
- `ProductionStateCommitter` 是唯一 durable write、activation 与 recovery owner。
- Dependency Graph 独占 dependency、fingerprint、invalidation 与 rebuild frontier。
- HyperFrames 是唯一默认 Production renderer。
- Router 只选择一个 exact capability；family 只聚合和 exact dispatch，不保存 last-selected state。
- Missing、duplicate、extra、wrong-order、tampered、stale 或 unsupported inputs必须在 compiler、preview、
  permit consume 与 Provider POST 前 fail closed，effect count 为零。
- Local/paid attempt lifecycle、permit 与 evidence不得混合。
- Hybrid artifact build 是 explicit inventory preparation；runtime只能 reopen、rehash、verify、consume。
- Exact replay 不重复 Provider、artifact build、motion-tail extraction、activation 或 render effects。
- C1/C2/C3、Legacy T2V/I2V/R2V、historical request/resolved hashes在 C4 fields缺失时保持兼容。
- Technical PASS、live connectivity、quality acceptance 与 P6 Final Acceptance 分层报告。

## Current and Target Behavior

| Surface | Current | Target |
| --- | --- | --- |
| C4 core | implemented offline | preserve，补足negative regression，不重复设计 |
| Local T8 V2 | separate T2VA/I2VA/FL2VA/Ref2VA children | additive winner-specific C4 Hybrid child |
| Local four-anchor live | absent | one exact request / one submit / no retry / no fallback，完成全矩阵证据 |
| Seedance active profile | current profile要求覆盖全局model catalog | active capabilities/pricing只覆盖explicit entitled subset，默认base only |
| Seedance model switching | shared adapter，但profile集合过宽 | exact model/profile/price/endpoint/response isolation，新model即新attempt |
| Seedance exact C4 | cross-mode union未证明 | 继续fail closed；formal evidence不足不注册Grade E |
| Seedance semantic C4 | 未注册 | optional base-only Grade S capability，独立授权与验收 |
| Transition truth | provider/lane evidence分散 | immutable directed pair certification + Manifest-owned pointer |
| Multi-provider claim | 不可声称流畅切换 | 达到相应claim level后只声明已认证grade与directions |

## Compatibility

- `default_seedance_capabilities()` 继续表示 adapter 能理解的 authoritative provider catalog；active account
  inventory通过 explicit profile subset表达，不通过删除catalog或family wildcard表达。
- `SeedanceProviderProfile.create_default()` 若保留，只可用于 complete catalog fixtures/diagnostics；
  Production assembly必须显式传入 entitled capabilities 与 matching pricing subset。
- Existing `SeedanceVideoProvider` transport envelope保持；model isolation发生在 profile construction、
  capability selection、pricing、permit fingerprint与response validation。
- Existing local child APIs 与 `LocalH3VideoProviderFamily` protocol保持；新child additive注册。
- Schema/layout默认不变。若 transition certification 无法复用现有 immutable evidence + Manifest pointer seam，
  必须触发 Decision Gate，先更新 spec/plan并取得 migration authorization。

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
- If compatible without migration，create `src/ai_video/production/video_transition.py` for immutable model、
  hash validation与pair adjudication，and create `tests/test_production_video_transition.py`。
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
- 同一Validation attempt开始后，candidate commit、workflow、binding、profile、model/artifact、fixture、
  prompt、sampling参数与rubric全部冻结。任一项改变都产生新candidate identity并要求新attempt；旧evidence
  不得迁移到新snapshot。
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

Milestone 3先冻结inventory、four-anchor fixture、prompt、Stock20参数、rubric、candidate identities与effect
budget。P0是两个lane的共同前置条件；冻结前不得启动M0 generation，也不得创建final Production
capability identity。

### Phase P1 — Qualification and Safe Implementation in Parallel

P0完成后并行推进：

| Lane | Allowed work | Forbidden work |
| --- | --- | --- |
| Implementation I1 | Milestone 1 C4 regression；Milestone 2 Seedance base-only isolation；Milestone 5的candidate-neutral RED contracts、child protocol/family denial tests与fake transport seam | 不确定winner前不得封最终capability/model/profile/workflow identity；不得修改Validation正在消费的sealed candidate bundle |
| Validation V1 | Milestone 4 M0 single-boundary attempt；M0失败时按gate执行conditional M1；保存exact technical与human evidence | 不修改source/tests/workflow/profile；不重试、不fallback、不边看结果边改阈值 |

I1可以先写winner-independent tests和interfaces，但所有包含`ref2va-stock20`或`hybrid-stock20`的Production
files/exports/active snapshot必须等Join Gate J1。

### Join Gate J1 — Select One Winner

J1只接受M0或M1中一个满足frozen gates的candidate：

- winner identity、model/artifact、workflow/binding/profile与qualification evidence全部sealed；
- loser保持experimental evidence，不进入Production snapshot；
- 两者都失败则停止Local destination implementation，不用Implementation lane的进度倒逼quality PASS；
- unknown outcome先走explicit recovery，J1保持open。

J1关闭后，Implementation lane才可完成Milestone 5 winner-specific child与Production exports。

### Phase P2 — Production Integration and Multi-Shot Pilot in Parallel

Milestone 5形成一个task-only checkpoint，并通过focused tests、preflight与exact Harness后，冻结为
`validation_snapshot`。随后并行推进：

| Lane | Allowed work | Snapshot rule |
| --- | --- | --- |
| Implementation I2 | Milestone 6 fake lifecycle、recovery、replay、P5与documentation preparation | 可在与provider/profile/workflow不重叠的files继续；若修改validation snapshot中的任何bytes，必须产生新checkpoint并使旧Pilot不具备promotion资格 |
| Validation V2 | Milestone 7先复核single boundary，再做3–4 Shot、至少2个continuity edges的single-Provider full-speed Pilot | 全程固定commit/profile/workflow/model/artifact/fixture/rubric；one submit per generation，no retry，no fallback |

Validation V2不得在I2尚未commit的working tree上运行，也不得把later code changes与earlier media receipts拼成
同一acceptance bundle。

### Join Gate J2 — Destination Acceptance

只有I2 lifecycle/replay/P5 evidence与V2 boundary/identity/motion/P6/human evidence同时绑定同一或可证明
byte-identical的validation snapshot，才能达到`C4_DESTINATION_READY`。若I2在Pilot后改变任何semantic或
execution identity，必须重跑受影响的V2 gates。

### Phase P3 — Transition Work

J2关闭后才开始Milestone 8 directed certification。Milestone 9 Seedance semantic lane可独立准备formal
evidence，但不得作为Local失败fallback，也不得在J2前被用来声称multi-provider readiness。

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

能够诚实声明“接口transport共用，model contract独立，当前active inventory为base only”。这不证明任何
Seedance 2.0 model支持exact four-role union。

## Milestone 3: Freeze Local T8 Candidate Qualification

本milestone是Parallel Phase P0，由两个lane共同消费；不得把它分成两份各自漂移的fixture、profile或
rubric。

### Inventory Preflight

生成read-only inventory report，绑定：

- pinned ComfyUI与T8 plugin commit/version/license；
- Hybrid conditioning nodes/input schemas；
- installed stock Ref2VA identity；
- M1所需 exact validated pruned FL2VA/Ref2VA pair是否存在；
- Hybrid artifact/sidecar是否存在；
- CLIP、video/audio VAE、sampler、scheduler与output node identity；
- literal loopback endpoint与remote/fallback disabled flags。

缺失M1 pair/artifact不阻塞M0；不得把当前non-pruned pair扩宽为已验证M1输入。

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

### Exit Criteria

形成content-addressed qualification inputs、两个明确candidate states与P0 freeze receipt；尚未生成媒体
时只能报告`qualification prepared`。P0关闭后可同时启动Implementation I1与Validation V1。

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

记录workflow execution、output/probe、decoded boundaries、identity windows、motion windows、P6/human verdict。

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
4. 使用与M0相同fixture、Stock20与rubric进行one-submit验证。

不得自动build、quarantine后自动修复、stock fallback、cloud fallback或用Turbo改变归因变量。

### Exit Criteria

最多一个candidate被选为Production implementation winner。两个都失败时本计划在Local destination gate
保持blocked，不注册C4 capability。Winner evidence关闭Join Gate J1；在此之前Implementation I1只能完成
candidate-neutral work。

## Milestone 5: Implement Winner-Specific Local C4 Child

### RED

在`tests/test_production_comfy_t8_hybrid_c4_video.py`固定：

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

实现winner-specific profile、workflow与child：

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
  tests/test_production_local_h3_provider_family.py \
  tests/test_production_shot_router.py \
  tests/test_production_provider_neutral_adapters.py -q
```

### Validation Snapshot Checkpoint

Milestone 5完成后必须先建立task-only commit，并对exact commit range完成focused tests、profile preflight、
Harness与receipt verification。该commit及其workflow/profile/model/artifact hashes构成唯一
`validation_snapshot`；Milestone 7不得消费unstaged working tree或later unsealed edits。

## Milestone 6: Close Lifecycle, Replay and P5

### Work

使用fake local transport与sealed fixtures覆盖：

- compile -> resolve -> preview -> preflight -> intent/permit -> submit/status/fetch；
- before-submit、accepted、known-no-effect、outcome-unknown、fetched、validated、candidate与activation crash
  points；
- activation后Project/Registry/graph/Manifest一致；
- reopen重验request/profile/model/artifact/workflow/input/output hashes；
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
one exact model/profile
one submit
no retry
no fallback
```

保存exact input SHA-256、Registry identities、request/resolved/fingerprint、workflow/profile/model/artifact
hashes、submit/status/fetch receipts、output/probe、decoded first/last frame hashes与replay counters。

Single-boundary technical smoke通过后，使用同一sealed snapshot继续3–4 Shot single-Provider Pilot：

- 至少3个Shots与2个continuity edges；
- 同一canonical character与scene，包含一次明显subject motion和一次明显camera motion；
- 每个generation各自one submit、no retry、no fallback；
- 每个edge分别记录exact anchors、boundary/identity/motion evidence，不用平均分掩盖单edge失败；
- 最终按full-speed sequence review累计identity drift、camera velocity drift、action phase与空间叙事连续性。

### Quality Gates

- Boundary：decoded frame 0与terminal frame分别计算frozen PSNR/SSIM/perceptual metrics，保存side-by-side与
  crop evidence；native role不夸大为pixel-identical。
- Identity：first/middle/last windows检查face/subject、hair、clothes、props、body scale与drift；backend
  coverage不足时为`NOT_EVALUATED`。
- Motion：检查subject/camera direction与velocity、action phase、entrance/exit、unexpected stop/re-entry；
  单帧metric不得代替motion evidence。
- P6/Human：消费exact request/output/anchors、technical/strategy/semantic evidence与human verdict；只有P6
  是Final Acceptance owner。

### Exit Criteria

全部通过后达到`C4_DESTINATION_READY`。任何quality dimension rejection、`NOT_EVALUATED`缺human fallback、
unknown outcome或incomplete evidence都保持`experimental / unavailable`。Promotion bundle必须同时包含
Milestone 6的I2 evidence与本milestone的V2 evidence，并证明二者绑定same/byte-identical
`validation_snapshot`，从而关闭Join Gate J2。

## Milestone 8: Establish Directed Transition Certification

### Persistence Seam Spike

先用tests验证existing immutable evidence + Manifest pointer能否表达certification，且不新增writer或mutable
lifecycle：

- content hash覆盖source/destination exact identities、grade、anchors、normalization与全部evidence；
- reverse direction、不同model/profile、不同grade或changed output normalization产生不同identity；
- pointer tamper、missing evidence、source未activated/P6未接受、destination未ready全部fail closed；
- replay只reopen/revalidate，不重复Provider或committer effect。

若无需schema/layout migration，按File Map实现`video_transition.py`与现有committer pointer seam。若需要
Manifest/artifact migration，在任何production schema edit前停止并触发Decision Gate。

### First Directed Pairs

只对已有accepted source output、exact terminal/motion-tail derivation与ready Local destination建立pair。
每个direction独立运行：

1. source evidence reopen；
2. exact anchor derivation/materialization；
3. Local C4 destination generation；
4. normalization、boundary、identity、motion与P6；
5. immutable certification seal与reopen/replay。

Reverse direction不自动成立。历史failed/unactivated Seedance result不能作为accepted source。

### Exit Criteria

至少一个不同source Provider到Local T8的pair通过后达到`DIRECTED_TRANSITION_READY`，声明必须写出exact
direction；仍不能说“多个destination可流畅切换”。

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

## Milestone 10: Same-Grade Multi-Destination Gate

达到“同等级多 Provider 可流畅切换”前必须存在至少两个不同destination Providers，各自：

- 使用同一provider-neutral grade、fixture与frozen rubric；
- 拥有独立exact capability/profile/model/pricing/evidence；
- 通过compile、denial、lifecycle、live、boundary、identity、motion、P6与replay；
- 通过deterministic explicit selection与no-fallback tests；
- 对每个声明的source direction拥有独立certification。

当前已知Provider evidence不足以安排第二个Grade E destination，因此本milestone是hard claim gate，不是
可以由Local T8或Seedance Grade S单独关闭的implementation checklist。第二个same-grade destination出现
formal evidence后，必须更新governing spec/plan的exact model/profile scope再执行。

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
- certification是否是immutable evidence而非第二state owner；
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

- 一个winner-specific Local T8 child完成profile/preflight、fake lifecycle、full four-anchor local smoke、
  3–4 Shot single-Provider Pilot、activation/reopen/replay、boundary/identity/motion与P6/human acceptance；
- Implementation与Validation evidence绑定same/byte-identical sealed snapshot，Join Gate J2关闭。

### `DIRECTED_TRANSITION_READY`

- 至少一个source与不同destination Provider的exact direction拥有fresh immutable certification。

### `SAME_GRADE_MULTI_DESTINATION_READY`

- 同一grade至少两个不同destination Providers完成独立sealed capability与全部acceptance；
- explicit selection、denial、reopen、replay与no-fallback tests通过。

### `FULL_MATRIX_READY`

- 每个对外声明支持的directed pair都拥有独立fresh certification。

低层级不得代替高层级。Local T8 child完成后最多升级到`C4_DESTINATION_READY`；加一个跨Provider source
pair后最多升级到`DIRECTED_TRANSITION_READY`。在第二个same-grade destination通过前，最终交付必须明确
写“尚不能声称多 Provider 同等级流畅切换”。

## Verification Matrix

| Gate | Minimum executable evidence |
| --- | --- |
| Core/cardinality | missing/duplicate/extra/wrong-order/tamper/sub-capability-union zero-effect tests |
| Seedance isolation | base-only snapshot、pricing/profile exact set、bounds、endpoint、response model与cross-model denial |
| Local inventory | exact ComfyUI/T8/model/artifact/node/workflow/profile hashes与license/provenance |
| Workflow/compiler | literal Hybrid、exact four mappings、empty audio、deterministic payload/output |
| Lifecycle | permit、submit/status/fetch、unknown recovery、candidate/activation/reopen/replay |
| P5 | four exact inputs的precise closure；unrelated assets保持fresh |
| Local live | one request、one submit、no retry、no fallback，全部input/output hashes |
| Multi-shot Pilot | 3–4 Shots、至少2 edges、same snapshot、逐edge evidence与full-speed cumulative drift review |
| Boundary | decoded frame 0/terminal evidence，native role与pixel equality分开 |
| Identity | multi-window subject/appearance/drift；不足为`NOT_EVALUATED` |
| Motion | direction、velocity、phase、entrance/exit、stop/re-entry |
| P6/Human | exact evidence + human verdict，由P6唯一给Final Acceptance |
| Transition | exact directed pair、grade、normalization、evidence hash、tamper/reverse denial |
| Harness | exact staged snapshot或commit range的fresh passing receipt |

## Execution Order

```text
P0 / Milestone 3
freeze inventory + fixture + candidates + rubric
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
lifecycle/replay/P5       3-4 Shot Pilot + P6
          |                     |
          +----------+----------+
                     |
              Join Gate J2
              C4_DESTINATION_READY
                     |
              Milestone 8
              directed certification

Milestone 9  optional base Seedance semantic lane
Milestone 10 same-grade second-destination claim gate
Milestone 11 docs/review/Harness at every checkpoint
```

并行表示wall-clock overlap，不表示dependency消失。Milestone 4必须在P0冻结后进行；Milestone 5不得在
J1前创建final Production identity；Milestone 7只消费sealed checkpoint；Milestone 8必须在J2后进行；
Milestone 9不阻塞Local Grade E，也不得成为其fallback。任何same-file writer overlap仍在写入前由用户决定
ownership或顺序。

## Rollback and Failure Policy

- Candidate失败：保留evidence，capability保持unavailable，不改阈值、不替换identity。
- Local unknown outcome：existing explicit recovery；不blind retry、不remint permit。
- Hybrid artifact missing/tampered：attempt blocked；runtime不build/repair/fallback。
- Seedance entitlement/profile/pricing不完整：active snapshot不暴露model；preview/POST effect count为零。
- Provider response model mismatch：fail closed，不接受family-compatible替代。
- Grade E quality失败：不自动改为Grade S。
- Certification tamper/stale：拒绝transition claim，不影响canonical source/destination lifecycle truth。
- Persistence需要migration：在schema/layout edit前停止并请求Decision Gate。
- Reviewer/Harness失败：修复并重新验证exact snapshot，不用旧receipt覆盖。

## Final Definition of Done

本计划的第一可交付终点是：

- Seedance 2.0 shared transport与base/Fast/Mini exact model isolation已实现，active inventory为base only；
- Local T8一个winner-specific C4 destination达到`C4_DESTINATION_READY`；
- 至少一个不同source Provider到Local T8的exact direction达到`DIRECTED_TRANSITION_READY`；
- canonical docs、independent review与exact Harness receipts完成；
- 未购买、未授权、未验证或不同grade的routes继续fail closed。

并行执行本身不构成acceptance。Final evidence必须证明Implementation I2与Validation V2绑定同一或
byte-identical `validation_snapshot`；若candidate source、workflow、profile、model/artifact、fixture或
rubric在Pilot期间漂移，相关Pilot必须重新运行。

这仍不等于“多 Provider destination可以同等级流畅切换”。只有Milestone 10的第二个same-grade destination
和对应directed certifications真正完成后，才能升级该产品声明；只有完整声明矩阵逐项认证后，才能称
`FULL_MATRIX_READY`。
