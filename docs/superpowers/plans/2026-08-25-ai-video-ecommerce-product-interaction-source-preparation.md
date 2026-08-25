# AI-VIDEO Ecommerce Product Interaction Source Preparation Implementation Plan

## Status

Implemented in current local `main`；offline structural verification complete，exact immutable commit-range Harness与final independent re-review收口中，未push/release，未执行Provider/media/network/paid effects。

本计划基于 `main@3c9dc852969ac0bc3ae3cb6427d31fc1ba4d580b` 的 current source、tests、canonical docs 与 fresh AI-VIDEO RAG 结果编写。它只授权后续实现一个 P0 vertical slice；本文档本身不证明 Runtime 已实现、不授权 Provider submit、不生成媒体、不读取 credential、不产生付费调用，也不构成 P6 PASS、Final Acceptance、release 或 production readiness。

## Goal

把当前“`IN_SCENE_PROVIDER` 必须由 caller 预先带来 `source_generation_evidence`”的被动消费契约，演进为一个 product-aware Production path：

```text
sealed AdCreativePlan product-interaction intent
  -> pure Commercial Shot execution projection
  -> exact ProductReferenceSet + Character / Scene constraints
  -> registered interaction-keyframe candidate
  -> product / character / physical-interaction semantic review
  -> committer-selected ApprovedCommercialSourceBinding
  -> current VideoPlanningRequest
  -> ProviderNeutralVideoRequirement with typed product fidelity
  -> exact first-frame I2V routing
```

第一个可交付结果不是“自动生成整支广告”，而是：青颜 Shot 03 / Shot 04 能从真实商品参考图和同一主人公约束，获得一个可审计、经过语义批准、可作为 I2V first frame 的 interaction keyframe，并且失败只失效对应 source/keyframe/Shot closure。

## Problem Boundary

### Current Behavior

- `ProductPresentationMode.IN_SCENE_PROVIDER` 在 `src/ai_video/production/ad_creative_types.py` 中要求 caller 预先提供 `source_evidence_id`；`SourceGenerationEvidencePointer` 只有 artifact/revision/hash/Shot/asset pointer，没有 producer 或 visual acceptance semantics。
- `compile_ad_creative_plan()` 在 `src/ai_video/production/ad_creative.py` 中只确认 base `CompositionSpec` 已有相同 Shot / asset layer，然后跳过 overlay projection；它不会创建 source request、materialize keyframe、调用 QA 或注册 approved reference。
- `CompiledAdCreativeHandoff` 只有 beat / presentation / graphic / sound IDs 和 composition requirements，没有 commercial execution class、reference requirements、approved source binding 或 `VideoPlanningRequest`。
- `AssetRole`、`SemanticReferenceRole` 和 Router context 只认识 Character、Scene、frame、video/audio reference；Provider-neutral requirement 不知道“这是青颜商品 identity”。
- P7 Image 和 image import 已有 content-addressed asset、Registry、Dependency Graph、`ProductionStateCommitter`、replay/recovery primitives，但 current reference roles/targets没有 Product 或 commercial interaction source。
- P6 的 current render review lifecycle和 continuity evaluator不具备 product-packaging、wardrobe/accessory、hand-object interaction的 typed evidence；`review_ad_creative_plan().is_ready` 只表示 authoring/composition contract ready。
- P5 Repair 可以安全执行 caller 已选定的 exact closure，但没有 commercial failure type 到 owner / node 的 deterministic mapping。

### Target Behavior

- `AdCreativePlan` 表达 product-interaction intent和 Product identity requirement，不再要求 authoring caller伪装成 source-evidence producer。
- 一个 pure `CommercialExecutionProjection` 区分 product interaction、character performance、product hero、proof graphics 和 end card；只有 `PRODUCT_INTERACTION` 进入本 slice 的 source-preparation path。
- `ProductReferenceSet` 是独立于 Character、Scene、Wardrobe、Accessory 和 continuity state 的 semantic dimension，并绑定 Registry 中的 exact bytes。
- `CommercialSourcePreparationCoordinator` 是唯一 E2 orchestration owner；它不拥有 Registry、Manifest、Provider、QA verdict、timeline、renderer或 repair lifecycle。
- Product reference和 interaction keyframe candidate由现有 Asset Registry与唯一 `ProductionStateCommitter` 持久化；candidate存在不等于 approved。
- P6 增加 source-image semantic target，但保留唯一 policy、authority、verdict、freshness和 receipt owner；PASS 才产生 `ApprovedCommercialSourceBinding`。
- VideoPlanner获得 product-aware requirement和 approved first frame；Router只允许满足 exact first-frame I2V 的单一 capability，禁止 T2V、generic reference或 flat overlay降级。
- Product/Character/Interaction failure 先分类，再委托现有 Dependency Graph / P5 Repair计算并执行 exact closure。

## Scope

### In Scope

- `CommercialShotClass` 和 deterministic per-Shot execution projection；
- single-SKU `ProductReferenceSet`，支持多张 exact product reference images；
- Product、Character、Scene、Wardrobe、Accessory 五个互相独立的 reference requirement dimensions；
- local/imported product reference registration；
- imported interaction-keyframe candidate的 canonical materialization和 provenance；
- capability-gated source-generation seam；没有 exact product-aware Image Provider capability时必须在 effect 前 BLOCKED；
- source-image semantic review：Character identity、hair、wardrobe、accessory、product presence、packaging、silhouette、dominant color、logo/label、scale、perspective、lighting、hand-object contact、occlusion、interaction plausibility和 flat-overlay detection；
- committer-owned candidate / evidence / approval / explicit recovery / exact replay state；
- product-aware `VideoPlanningRequest`、provider-neutral requirement、neutral prompt projection和 exact I2V Router validation；
- source/keyframe/product/character/interaction failure 到 existing P5 target-node proposal的 deterministic classification；
- Qingyan Shot 03 / Shot 04 offline fake/import end-to-end tests；
- backward compatibility、Harness routing与 canonical docs closure。

### Out Of Scope

- live MiniMax H3、Local H3、T8、Seedance、ComfyUI或任何其他 Provider execution；
- image、video、audio、voice或graphics媒体生成；
- credential、remote egress、paid permit、budget reservation或 cloud smoke；
- 把当前 concrete Image Provider profile宣称为 product-aware；
- direct product multi-reference R2V、Provider-native product control或跨 Provider benchmark；
- temporal spray-action QA、完整 generated-video commercial QA、whole-ad QA或 Final Acceptance；
- 自动 OCR、Logo detector、face recognition、wardrobe/accessory model selection或 calibration；
- 自动执行 repair；本 slice只产生 typed failure和 exact repair proposal；
- 通用 `ProductionProject.products` schema migration；Product identity在本 slice由 sealed commercial contracts拥有，Registry继续拥有 bytes；
- 建立完整 Wardrobe / Accessory master artifact subsystem；本 slice只保持它们为独立 requirement和 QA dimensions；
- Product Hero、Proof Graphic、CTA 的新 renderer path；它们继续使用 current controlled asset / deterministic composition能力；
- 第二 Asset Registry、Manifest writer、Dependency Graph、Timeline、Renderer、Router、QA lifecycle或 Repair engine；
- Legacy `0.1.x` CLI、Manifest、flat artifact layout与 workflow templates。

## Architectural Decisions

### Decision 1: Add Product Semantics Without Creating A Second Product Runtime

新增 `ProductReferenceSet`，但 first slice不向 `ProductionProject` 增加通用 `products` collection。其 identity由 sealed `AdCreativePlan` / `CommercialExecutionProjection` 绑定，image bytes仍由现有 Asset Registry拥有，mutable selection仍由 Production Manifest拥有。

`ProductReferenceSet` 至少包含：

- stable `product_id`、`sku_id`、formal product name；
- exact Product Truth reference IDs；
- canonical ordered `ProductReferenceAssetBinding`：`asset_id`、SHA-256、MIME、width、height、view/purpose；
- packaging form、bottle silhouette、dominant color、cap color、Logo/label identity与 protected text-zone requirements；
- exact Registry revision/hash；
- self-sealing content hash。

它不得继承或嵌入 `CharacterReference`，也不得借 `Scene` 或 opaque `prop_state_hash` 表达商品 identity。

### Decision 2: Commercial Classification Is Pure Projection

`CommercialShotClass` 不是第二 Planner。它只从 sealed ad semantics纯派生一个 primary execution responsibility和 reference/materialization requirements：

| Commercial intent | Primary class | Execution disposition |
| --- | --- | --- |
| Problem / payoff with protagonist, no product interaction | `CHARACTER_PERFORMANCE` | existing Character/Scene planning |
| Lifestyle context with no exact product manipulation | `LIFESTYLE` | existing Character/Scene planning |
| Product in hand, take-out, spray or other physical use | `PRODUCT_INTERACTION` | approved commercial source first，then I2V |
| Controlled pack/bottle beauty shot | `PRODUCT_HERO` | controlled product asset / deterministic composition；not forced to video Provider |
| Claim, percentage or benefit copy | `PROOF_GRAPHIC` | compositor only |
| CTA / brand closure | `END_CARD` | compositor only |

一个 Shot 可以带 secondary graphics/audio responsibilities，但只能有一个 primary class。Ambiguous or contradictory primary responsibilities必须 fail closed，不能按 enum precedence静默猜测。

### Decision 3: Approved First Frame Is The Initial Product Delivery Strategy

本 slice把 Product identity送入 Provider-neutral requirement，但不把 product image伪装成当前 Router的 generic `reference`：

- 新增 typed `ProductFidelityRequirement`；
- satisfaction strategy固定为 `APPROVED_FIRST_FRAME`；
- exact `FIRST_FRAME` evidence必须等于 approved interaction keyframe；
- requirement同时绑定 `ProductReferenceSet` hash和 commercial source approval receipt；
- neutral prompt compiler输出独立 product preservation fields；
- Router只允许 exact `IMAGE_TO_VIDEO` first-frame capability；
- direct `PRODUCT_REFERENCE` Provider binding留给后续独立 slice，直到具体 capability能诚实消费该 role。

这样 VideoPlanner明确知道“必须保护青颜商品”，同时不声称所有 Provider已经能接收额外 Product reference image。

### Decision 4: Source Review Extends P6 Instead Of Duplicating It

新增 source-image-specific request/evidence/receipt contracts，但它们复用 P6 的：

- `QaPolicy` 和 policy-selected semantic authorities；
- `QaLayer.SEMANTIC`、`QaVerdict`、evidence strength和 freshness semantics；
- durable intent、one-use permit、content-addressed evidence和 committer selection；
- fail-closed `NOT_EVALUATED`；
- repair/final-acceptance distinction。

`CommercialVisualEvidence` 不是另一个 acceptance system；它是 P6 对 `SOURCE_IMAGE` target kind 的 typed measurement contract。Source PASS只表示该 keyframe可作为 generation anchor，不表示 generated Shot或最终广告通过。

### Decision 5: Import Is The First Supported Materialization Lane

first implementation必须支持 exact local/human-observed import：

- product reference images先注册为 Registry assets；
- interaction keyframe import receipt绑定 exact Character、Scene、ProductReferenceSet和 target Shot；
- imported candidate必须经过 source semantic review；
- browser/image-tool来源必须诚实记录 tool/actor/provenance，不能伪造 durable Provider submit。

`P7_GENERATION` 只建立 orchestration seam和 BLOCKED contract。除非后续 concrete Image Provider profile显式支持 exact Product binding并通过独立 empirical qualification，本计划不得让现有 Qwen/Comfy image adapter忽略 Product reference后继续执行。

## Ownership Matrix

| Concern | Single owner after this slice | This slice must not do |
| --- | --- | --- |
| Ad intent and product requirement | sealed `AdCreativePlan` | 把 Runtime result写回 authoring truth |
| Commercial class/reference projection | `commercial_execution.py` pure projector | 选择 Provider、读取 mutable state |
| Product/reference bytes and provenance | existing Asset Registry | 建第二 Product Registry或 mutable latest pointer |
| Source-preparation sequencing | `CommercialSourcePreparationCoordinator` | 直接写 Manifest/Registry或签发 QA verdict |
| Durable request/candidate/approval state | existing `ProductionStateCommitter` | 新建 writer、自动 recovery、auto-approve |
| Source semantic verdict | P6 policy/adjudication with commercial target contract | 让 importer/materializer自证 PASS |
| Generation plan and capability selection | existing VideoPlanner / Readiness Gate / Router | commercial coordinator排序或 fallback Provider |
| Failure closure and repair execution | existing Dependency Graph / P5 / P6 | classifier自算 arbitrary closure或自动执行 repair |
| Timing, graphics, audio, captions and render | existing `ResolvedTimeline` / HyperFrames / P4 | 建第二 timeline、renderer或 typography path |

## Core Contracts

### `AdCreativePlan /2`

Current creation API emits `ad-creative-plan/2`：

- `ProductPresentation` 增加 `product_id`、`product_reference_requirement_id`和 `source_requirement_id`；
- `IN_SCENE_PROVIDER` 表达 intent时不再要求 `source_evidence_id`；
- current plan拒绝 caller-supplied `SourceGenerationEvidencePointer` 作为 readiness proof；
- `product_reference_requirements` 绑定 product identity、truth IDs、expected source views和 fidelity dimensions；
- `source_generation_evidence` 只属于 legacy `/1` reopen model。

Historical `/1` bytes必须 strict reopen且 hash不变。Legacy pointer可以用于历史审计/Composition reopen，但不能为 new `PRODUCT_INTERACTION` generation attempt签发 readiness。

### `CommercialExecutionProjection /1`

Pure、self-sealing projection，至少包含：

- exact AdCreativePlan id/revision/hash；
- target Shot id及 commercial primary class；
- product/character/scene/wardrobe/accessory requirements；
- recommended disposition；
- `requires_source_materialization`、`requires_source_review`、`invoke_video_provider`；
- deterministic graphics/audio responsibilities；
- projection hash。

相同 input必须产生相同 bytes/hash；projection不得读取 Registry、Manifest、Provider或 filesystem。

### `CommercialSourcePreparationRequest /1`

Immutable request绑定：

- current `CommercialExecutionProjection`；
- exact target Shot revision/hash；
- exact base Project/Registry/Dependency Graph pointers；
- `ProductReferenceSet`；
- canonical Character/Scene assets；
- independent wardrobe/accessory requirement fingerprints；
- acquisition kind：`REGISTERED_IMPORT` 或 `P7_GENERATION`；
- expected output role `commercial_interaction_keyframe`；
- request fingerprint和 attempt identity。

Only `PRODUCT_INTERACTION` may create this request。`P7_GENERATION` 在没有 explicit product-aware capability时必须在 durable submit intent和 Provider effect前返回 typed BLOCKED。

### `CommercialVisualEvidence /1`

每个 required dimension使用 `match | mismatch | not_evaluated`，并绑定 expected、observed、confidence、rationale和 exact target SHA-256。Required dimensions为：

- `character_identity`；
- `hairstyle`；
- `wardrobe`；
- `accessory`；
- `product_presence`；
- `packaging_identity`；
- `bottle_silhouette`；
- `dominant_color`；
- `cap_color`；
- `logo_label_identity`；
- `label_text_zone_integrity`；
- `product_scale`；
- `perspective_match`；
- `lighting_match`；
- `hand_object_contact`；
- `occlusion_plausibility`；
- `interaction_plausibility`；
- `flat_overlay_absent`。

任何 required `mismatch` 产生 FAIL；任何 required `not_evaluated` 产生 NOT_EVALUATED。只有 policy-selected authority的 exact-bound evidence可产生 PASS。自动 evaluator不是 V1 acceptance prerequisite；合规 human evidence是允许的正式 lane。

### `ApprovedCommercialSourceBinding /1`

只有唯一 `ProductionStateCommitter` 能选择该 pointer。它绑定：

- source request hash；
- AdCreativePlan和 execution projection hash；
- target Shot revision/hash；
- keyframe Registry asset id/SHA-256；
- ProductReferenceSet id/hash及 product source asset hashes；
- Character/Scene reference identities；
- wardrobe/accessory requirement hashes；
- exact P6 commercial source review receipt；
- approval content/file hashes。

Raw import receipt、generated candidate、`source_evidence_id`、matching Composition layer或 caller boolean均不能替代它。

### `ProviderNeutralVideoRequirement /3`

`/3` additive fields：

- `commercial_execution_class`；
- `product_fidelity_requirement`；
- `approved_commercial_source` link；
- `capability_need.needs_product_fidelity = true`；
- `source_strategy = approved_first_frame`。

Validation必须证明：

- class是 `PRODUCT_INTERACTION`；
- generation mode是 `IMAGE_TO_VIDEO`；
- `FIRST_FRAME` asset evidence与 approved keyframe exact相同；
- product/approval/Shot hashes互相一致；
- Product identity、Character identity和 Scene identity没有相互替代；
- direct Product reference不是 Provider input。

Historical `/1`、`/2` hashes和 non-commercial planning behavior保持不变。

### `CommercialFailureClassification /1`

Pure classifier至少映射：

| Failure type | Root owner | Proposed repair boundary |
| --- | --- | --- |
| invalid/missing product reference | ProductReferenceSet / Registry import | product reference + dependent source/keyframe/Shot |
| product fidelity mismatch | source materialization | interaction keyframe + generated Shot |
| character identity / hair mismatch | source materialization with Character refs | interaction keyframe + generated Shot |
| wardrobe / accessory mismatch | source materialization requirement | interaction keyframe + generated Shot |
| hand/occlusion/perspective/flat-overlay mismatch | source materialization | interaction keyframe + generated Shot |
| post-generation spray action mismatch | generated Shot | Shot only；temporal evaluator is follow-up |
| commercial typography | Composition/graphics | Composition closure only |
| audio | P4 audio | audio/mix closure only |
| pacing | ResolvedTimeline / Composition input | timeline/composition closure；never Registry rewrite |

Classifier只提出 exact root artifact/node IDs和 failure semantics。Existing P5 resolver计算 downstream closure；existing P5/P6 authorization和 committer执行 repair。Classifier不得自己写 state或自动运行 repair。

## Lifecycle And Replay Contract

Manifest current version增加为 `2.12`，以 additive `active_commercial_source_approvals` 和 attempt-local `CommercialSourceAttemptState` 保存 mutable selection；historical `2.0`–`2.11`保持 strict-readable。

```text
REQUESTED
  -> MATERIALIZED_CANDIDATE
  -> EVIDENCED
  -> APPROVED

MATERIALIZED_CANDIDATE / EVIDENCED
  -> REJECTED | NOT_EVALUATED

any uncertain external or durability boundary
  -> OUTCOME_UNKNOWN
```

Required behavior：

- Candidate bytes必须先 content-address、probe并注册，再提交 review；
- Candidate registration不等于 Shot source approval，也不等于 generated-video candidate activation；
- PASS approval与 Registry/Manifest/Dependency Graph exact tuple在同一个 final Manifest replace commit point选择；
- exact replay在任何 materializer、reviewer、committer或 Provider effect前 strict reopen全部证据并返回当前 approval；
- interrupted/unknown outcome只允许 explicit recovery；不得 blind retry、duplicate import、remint permit或自动选择 orphan；
- ProductReferenceSet或任一 source asset bytes变化，使 approval和 downstream product-interaction Shot stale；
- unrelated Character、Shot、graphics、audio和 composition nodes保持 fresh；
- source review FAIL保留 immutable candidate/evidence，但不产生 approved binding。

## Compatibility And Old-Path Retirement

- Legacy `AdCreativePlan /1`、`ProviderNeutralVideoRequirement /1`/`/2`、Manifest `2.0`–`2.11` 保持 exact reopen；existing hashes不得重算。
- `create_ad_creative_plan()` 的 current output升级到 `/2`；新增 explicit legacy reopen adapter，不让 historical model偷偷成为 current producer。
- `SourceGenerationEvidencePointer` 保留为 legacy audit type；new product-interaction attempt遇到它时返回 typed `PLANNING_PREFLIGHT_BLOCKED`，不能继续 Router。
- `compile_ad_creative_handoff()` current path必须携带 `CommercialExecutionProjection` 和 exact approved source link；只匹配 Shot / asset layer不再足够。
- Generic non-ecommerce caller仍可直接构造 existing `VideoPlanningRequest`；但从 `AdCreativePlan` 投影出的 product-interaction Shot只能通过 canonical commercial handoff进入 Planner。
- Flat product overlay继续只能用于 declared `GRAPHIC_REVEAL` / `HERO_ASSET`，并且不得满足 physical-interaction requirement。
- Router保持 exact single-capability、no-union、no-fallback；不得因新 commercial semantics增加 provider ranking或 fallback order。
- HyperFrames、`ResolvedTimeline`、commercial graphics、voice/captions和 P4 audio public contracts保持不变。

## Acceptance Criteria

1. Qingyan Shot 03 / Shot 04 从 `AdCreativePlan /2` 被 deterministic分类为 `PRODUCT_INTERACTION`；Shot 06 为 `PRODUCT_HERO`，Shot 07 为 `PROOF_GRAPHIC`，Shot 08 为 `END_CARD`。
2. ProductReferenceSet明确绑定青颜 SKU、黄色包装盒、黄色标签喷雾瓶、白色瓶盖、Logo/label和多张 exact Registry images；Character/Scene/Wardrobe/Accessory不承载这些 product fields。
3. Missing/tampered/unregistered product image、wrong Registry revision或 changed asset bytes在 candidate materialization前 BLOCKED。
4. Imported keyframe receipt绑定 exact ProductReferenceSet、Character、Scene和 target Shot；仅有 PNG、Composition layer或 legacy evidence pointer不能 qualify。
5. Candidate没有 current semantic PASS时 Planner handoff为 BLOCKED；`NOT_EVALUATED`不能降级为 manual PASS。
6. Product packaging、silhouette、dominant color、cap、Logo/label、scale、perspective、lighting、hand contact、occlusion或 flat-overlay任一 required mismatch均阻止 approval。
7. Approved source exact replay产生零 additional import/materializer/reviewer/committer/Provider effects和零 Manifest revision变化。
8. Crash/unknown-outcome tests证明 recovery不会 blind retry、auto-approve或删除完整 orphan evidence。
9. Current Planner生成 `ProviderNeutralVideoRequirement /3`，其中 Product identity独立存在，first-frame evidence与 approved keyframe exact相同。
10. Router对 T2V、generic R2V、wrong first frame、unknown capability、insufficient role/cardinality全部 BLOCKED；exact I2V capability才可 SELECTED。
11. Neutral compiler把 product preservation要求投影进 deterministic prompt，并保持 requirement hash / provider-bound lineage；Provider adapter仍不得选择或猜测 Product role。
12. Product/Character/Interaction source failure产生不同 typed failure codes和 exact P5 root-node proposal；commercial graphics/audio/pacing不被一并 invalidated。
13. Shot 07 / Shot 08 classifier明确 `invoke_video_provider = false`，继续由 deterministic compositor处理中文功效文字、百分比和 CTA。
14. Existing ad creative、P7 image、P6 review/repair、Planner、Shot Router、video compiler、Manifest migration和 Legacy tests全部通过。
15. Exact immutable commit range通过 Harness mandatory checks；fresh receipt可验证且 scope仅包含 task-owned files。
16. Engineering acceptance明确不声称真实苗家女孩/青颜媒体质量、喷雾动作成功、Provider live readiness、P6 generated-video PASS或 Final Acceptance。

## File Map

### CREATE

- `src/ai_video/production/commercial_execution.py`：pure commercial class和 per-Shot execution/reference projection。
- `src/ai_video/production/commercial_reference.py`：ProductReferenceSet、exact product asset binding和 source requirement contracts。
- `src/ai_video/production/commercial_source_preparation.py`：thin E2 coordinator、request/candidate/approved binding与 canonical handoff builder。
- `src/ai_video/production/commercial_visual_review.py`：typed source-image measurements、adjudication和 semantic failure classification。
- `src/ai_video/production/_state_commit_commercial_source.py`：唯一 committer下的 request/candidate/evidence/approval state transitions。
- `src/ai_video/production/_state_commit_commercial_source_recovery.py`：commercial source explicit recovery和 exact replay reopen。
- `tests/test_production_commercial_execution.py`。
- `tests/test_production_commercial_reference.py`。
- `tests/test_production_commercial_source_preparation.py`。
- `tests/test_production_commercial_visual_review.py`。
- `tests/test_production_ecommerce_product_interaction_e2e.py`：offline Qingyan Shot 03 / 04 vertical slice；只用 synthetic metadata/tiny test PNG和 fake consumers。

### MODIFY

- `src/ai_video/production/ad_creative_types.py`：current `/2` intent、product/reference requirement IDs和 legacy `/1` reopen boundary。
- `src/ai_video/production/ad_creative.py`：execution projection、approved-source-aware handoff和 legacy path retirement。
- `src/ai_video/production/ad_creative_review.py`：区分 authoring contract readiness、source readiness和 Production acceptance。
- `src/ai_video/planning/_planner_models.py`：commercial execution / approved source input binding。
- `src/ai_video/planning/_asset_readiness.py`：exact ProductReferenceSet、approval receipt和 first-frame readiness。
- `src/ai_video/planning/video_planner.py`：product-interaction current request到 provider-neutral `/3` projection。
- `src/ai_video/production/video_requirement.py`：`ProductFidelityRequirement`、`/3` hashing/validation和 independent semantic dimension。
- `src/ai_video/production/_video_requirement_routing.py`：approved-first-frame satisfaction和 product lineage checks；不增加 generic product binding。
- `src/ai_video/production/shot_router.py`：current requirement guard和 typed BLOCKED reason；不改变 exact selection algorithm。
- `src/ai_video/production/video_compiler.py`：deterministic product-preservation prompt projection和 unsupported-field reporting。
- `src/ai_video/production/image_import.py`：product-reference / commercial-interaction-keyframe import validation和 exact source lineage；不调用 Provider。
- `src/ai_video/production/models.py`：Manifest `2.12` pointers、attempt state和 legacy serializer/reopen rules；不得加入第二 lifecycle owner。
- `src/ai_video/production/paths.py`：canonical content-addressed commercial source paths。
- `src/ai_video/production/project.py`：strict reopen/validation of selected commercial source approvals。
- `src/ai_video/production/dependency.py`：ProductReferenceSet/product assets -> keyframe -> generated Shot typed edges和 precise invalidation。
- `src/ai_video/production/state_commit.py`：只组合新 private mixins和 injected collaborators。
- `src/ai_video/production/review.py`：复用 P6 policy/verdict/freshness utilities；source-specific domain logic留在新 module。
- `src/ai_video/production/__init__.py`：export approved public contracts。
- `tests/test_production_ad_creative.py`、`tests/test_planning_video_planner.py`、`tests/test_shot_readiness_gate.py`。
- `tests/test_production_video_requirement.py`、`tests/test_production_shot_router.py`、`tests/test_production_provider_neutral_adapters.py`。
- `tests/test_production_image_import.py`、`tests/test_production_review.py`、`tests/test_production_repair.py`。
- `tests/test_production_state_commit.py`、`tests/test_production_state_recovery.py`、`tests/test_production_state_commit_structure.py`。
- `.agent/harness/policy.yaml`、`tests/test_agent_harness.py`：new focused test route和 mandatory closure。
- `docs/agent-primary-contract-matrix.md`：new source-preparation owner、forbidden bypass和 focused verification。
- `docs/v0.2-runtime-baseline.md`：只在 implementation + fresh Harness PASS后记录 exact implemented boundary。
- `docs/v0.2-agentic-production-roadmap.md`：记录 P0 slice状态和仍未完成的 temporal commercial QA / empirical gate。

### REUSE

- Asset Registry asset identity、provenance和 registered bytes validation；
- `ProductionStateCommitter` lock、atomic replace、durable intent、one-use permit、replay和 explicit recovery patterns；
- P7 image measurement/import evidence primitives；
- Dependency Graph desired fingerprint、precise invalidation和 rebuild frontier；
- P6 `QaPolicy`、semantic authority、verdict、freshness和 receipt semantics；
- existing `VideoPlanner`、`ShotReadinessGate`、`VideoGenerationResolver`和 no-fallback Router；
- existing P5 `RepairRequest`、approved repair、repair outcome和 fresh review requirements；
- existing `ResolvedTimeline`、HyperFrames、commercial graphics、voice、audio和 captions。

### DO NOT TOUCH

- Legacy `src/ai_video/cli.py`、Legacy pipeline/Manifest/configs/workflows；
- HyperFrames renderer implementation和 canonical timeline math；
- current commercial graphics/composition/audio/caption render behavior；
- MiniMax H3、Hailuo、Local H3/T8、Seedance adapter payloads或 capability declarations；
- paid-provider gate、credentials、budget/egress/permit contracts；
- `.workflow/**`、`runs/**`、generated media和 external model/workflow stores；
- `.codex/config.toml`、`artifacts/`或其他 unrelated dirty/untracked paths。

## Major Milestones

### Milestone 0: Freeze Compatibility And Establish RED Contracts

**Files:** create the five new test modules；modify `.agent/harness/policy.yaml`、`tests/test_agent_harness.py` only for exact test routing。

**Contract:** 固定 `AdCreativePlan /1` reopen、current `/2` intent、provider-neutral `/1`/`/2` reopen、new `/3` product binding、Manifest `2.12` migration、commercial source state machine、no-overlay/no-fallback和 exact repair boundary。

**Implementation Notes:**

- 先写 failing tests，failure只允许来自 planned missing symbols/behavior；
- fixture使用 synthetic Qingyan metadata和 in-memory tiny PNG，不加入真实商品、人物或 generated media；
- old hashes使用 current checked-in fixtures固定，不能通过刷新 expected hash掩盖 migration regression；
- test证明 legacy evidence pointer不能满足 new attempt；
- Harness category只路由 new commercial source files和 relevant existing suites，不吞并所有 Production tests。

**Acceptance:** RED test matrix覆盖 success、tamper、missing input、NOT_EVALUATED、mismatch、replay、crash、legacy reopen、Router denial和 scoped repair；没有 unresolved public contract。

**Verification:**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_production_commercial_execution.py \
  tests/test_production_commercial_reference.py \
  tests/test_production_commercial_source_preparation.py \
  tests/test_production_commercial_visual_review.py \
  tests/test_production_ecommerce_product_interaction_e2e.py \
  tests/test_agent_harness.py -q
```

### Milestone 1: Implement Ad Intent, Product Reference, And Execution Projection

**Files:** create `commercial_execution.py`、`commercial_reference.py`；modify `ad_creative_types.py`、`ad_creative.py`、`ad_creative_review.py`、`production/__init__.py` and focused tests。

**Contract:** Current AdCreativePlan表达 product identity/reference requirements和 unresolved source intent；pure projection产生 one primary commercial class以及 independent Product/Character/Scene/Wardrobe/Accessory requirements。

**Implementation Notes:**

- 使用 explicit current/legacy models或 discriminated reopen helper；禁止一个 permissive union让 v1/v2 semantic混淆；
- `ProductReferenceSet` canonical order按 purpose/view/asset ID固定；duplicate asset、hash mismatch、missing required front/label view fail closed；
- classifier只消费 sealed plan；不读取 prompt keywords、filesystem或 Provider capabilities；
- `review_ad_creative_plan().is_ready` 保留“authoring/composition contract ready”含义，并新增明确 source-preparation status，不把它提升为 visual ready；
- Shot 06/07/08投影到 current deterministic lanes，证明 classifier不会让所有广告 Shot进入 video generation。

**Acceptance:** 同一 plan重复投影 bytes/hash完全一致；Qingyan eight-Shot role mapping符合 Acceptance 1；product semantics未进入 Character或 Scene；legacy `/1` strict reopen通过。

**Verification:**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_production_ad_creative.py \
  tests/test_production_commercial_execution.py \
  tests/test_production_commercial_reference.py -q
```

### Milestone 2: Materialize Registered Product References And Interaction Candidate

**Files:** create `commercial_source_preparation.py`、`_state_commit_commercial_source.py`、`_state_commit_commercial_source_recovery.py`；modify `image_import.py`、`models.py`、`paths.py`、`project.py`、`dependency.py`、`state_commit.py`、`production/__init__.py` and state/import tests。

**Contract:** 唯一 coordinator编排 request；唯一 committer注册 product refs和 interaction candidate，并保存 exact state/evidence。Import是 first supported lane；unsupported generated lane在任何 Provider effect前 BLOCKED。

**Implementation Notes:**

- Product reference assets只追加到 existing Registry；不创建 Product Registry；
- ProductReferenceSet、request、import receipt、candidate bytes和 dependency edges均 content-addressed；
- Candidate不得直接成为 `shot_keyframe` readiness input；只有 approval pointer可以解锁；
- `ProductionStateCommitter` façade只组合 private mixins，commercial source module各自保持低于 800 effective LOC；
- Manifest 2.12 serialization只在相关 pointers存在时写 new fields；historical manifests bytes不变；
- new attempt / recovery建立 exact replay tests，覆盖 crash before/after artifact promotion和 final Manifest replace；
- generated acquisition kind只接受 injected exact capability result；current concrete adapters一律 typed BLOCKED，不能 silently ignore ProductReferenceSet。

**Acceptance:** registered product pack和 candidate可 strict reopen；wrong product bytes或 base tuple变化阻止 materialization；candidate不产生 approval；exact replay/recovery符合 Lifecycle contract。

**Verification:**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_production_commercial_reference.py \
  tests/test_production_commercial_source_preparation.py \
  tests/test_production_image_import.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_state_commit_structure.py -q
```

### Milestone 3: Add P6 Commercial Source Visual Review And Approval

**Files:** create `commercial_visual_review.py`；complete `_state_commit_commercial_source.py`；modify `review.py`、`models.py`、`project.py` and review/repair/source tests。

**Contract:** Source candidate需要 current policy-selected semantic evidence；P6 pure adjudication签发 PASS/FAIL/NOT_EVALUATED；只有 PASS可由 committer选择 `ApprovedCommercialSourceBinding`。

**Implementation Notes:**

- 不复用 render-only hashes或 synthetic timeline欺骗 existing `ReviewRequest`；source request明确绑定 image target和 product/character expectations；
- human evidence必须绑定 actor/tool identity、candidate SHA、reference set hash、Shot hash、policy hash和 rationale；
- automatic evidence若没有 calibrated authority只能 FAIL或 NOT_EVALUATED，不能自报 PASS；
- approval选择与 current Registry/graph tuple一致；stale review receipt不能重用；
- FAIL/NOT_EVALUATED保留 candidate和 evidence，生成 typed finding，不写 approved pointer；
- `AdCreativeReviewReport.is_ready`和 commercial source approval继续是两个不同 proof levels。

**Acceptance:** full dimension mutation matrix分别产生正确 verdict/failure type；only exact PASS unlocks approval；tamper/stale/wrong-authority evidence fail closed。

**Verification:**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_production_commercial_visual_review.py \
  tests/test_production_commercial_source_preparation.py \
  tests/test_production_review.py \
  tests/test_production_repair.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
```

### Milestone 4: Connect Approved Source To VideoPlanner And Exact I2V Routing

**Files:** modify `_planner_models.py`、`_asset_readiness.py`、`video_planner.py`、`video_requirement.py`、`_video_requirement_routing.py`、`shot_router.py`、`video_compiler.py`、`production/__init__.py` and focused planner/router/compiler tests。

**Contract:** Canonical commercial handoff把 approved source转换为 current `VideoPlanningRequest`；Planner产生 provider-neutral `/3` product requirement；Router和 compiler验证 exact approved first frame且不调用 Provider。

**Implementation Notes:**

- approved source由 handoff传入，不从 latest文件、asset role名称或 prompt猜测；
- `_asset_readiness.py` strict reopen ProductReferenceSet、source approval、review receipt和 Registry bytes；
- product requirement进入 requirement hash和 neutral prompt，但 product reference images不进入 current provider binding roles；
- Router必须在 selected capability检查前先验证 product/approval/first-frame lineage；
- T2V、generic R2V、wrong first frame、missing approval、stale approval均返回 typed BLOCKED和 zero downstream calls；
- existing non-commercial Planner `/3` request和 requirement `/1`/`/2` behavior、hash fixtures与 adapter compilers保持兼容；
- no Provider adapter file change；selected exact I2V capability只证明structural compatibility。

**Acceptance:** Qingyan Shot 03/04得到 I2V-only ready projection；Hailuo/Local H3等 profile只有在 caller显式选择 exact I2V capability时可 structurally SELECTED；T2V providers必然 BLOCKED；compile result保留 product requirement hash。

**Verification:**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_planning_video_planner.py \
  tests/test_shot_readiness_gate.py \
  tests/test_production_video_requirement.py \
  tests/test_production_shot_router.py \
  tests/test_production_provider_neutral_adapters.py \
  tests/test_production_commercial_source_preparation.py -q
```

### Milestone 5: Map Commercial Failures To Existing Scoped Repair

**Files:** complete `commercial_visual_review.py`、`commercial_execution.py`；modify `dependency.py` only as required；extend `test_production_repair.py` and commercial tests。

**Contract:** Pure classification chooses root owner/node proposal；P5 resolver remains唯一 invalidation/closure owner；P6/committer remains approval/execution owner。

**Implementation Notes:**

- product reference failure和 product fidelity failure必须不同：前者重建 reference pack及其 dependents，后者保留 valid pack只重做 keyframe/Shot；
- character/wardrobe/accessory failure保留 ProductReferenceSet；
- physical-interaction source failure重做 interaction keyframe/Shot，不触碰 graphics/audio；
- typography/audio/pacing mappings只验证现有 owners，禁止在本 slice新增 writer；
- expected closure必须由 current graph计算，classifier不能接受 caller提供的 arbitrary downstream set；
- no automatic repair invocation。

**Acceptance:** mutation matrix证明每种 failure只提出正确 roots；existing `validate_repair_scope()`拒绝过宽/过窄 closure；composition-only/audio-only regression继续不重做 P7/P8 media。

**Verification:**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_production_commercial_visual_review.py \
  tests/test_production_commercial_source_preparation.py \
  tests/test_production_repair.py \
  tests/test_production_state_commit.py -q
```

### Milestone 6: Close The Offline Qingyan Vertical Slice And Documentation

**Files:** complete `test_production_ecommerce_product_interaction_e2e.py`；modify contract matrix、runtime baseline、roadmap、Harness policy/tests and only implementation-owned source/tests from prior milestones。

**Contract:** One offline path proves：Ad intent -> execution projection -> product references -> imported candidate -> semantic PASS -> approved source -> Planner `/3` -> Router SELECTED -> compiler output；parallel negative paths prove wrong product、identity mismatch、flat overlay、NOT_EVALUATED和 T2V denial。

**Implementation Notes:**

- fake compiler/provider只记录 downstream call count；不得 submit、poll、fetch、render或 create media；
- E2E必须证明 Shot 07/08不进入 video Provider path；
- runtime baseline只陈述 implemented structural path和 import/manual boundary；不得写“stable visual quality”或“spray action supported”；
- roadmap把 temporal interaction QA、post-video product fidelity、concrete product-aware image materializer和 empirical Provider proof保留为未完成 gates；
- 运行 `reviewer_xhigh` 做一次 independent architecture review，因为 change跨 Ad contract、Manifest/P6 lifecycle、Planner、Router和 Repair semantics；review不能替代 tests/Harness。

**Acceptance:** all targeted and policy-routed tests pass；independent review无 blocking issue；exact immutable commit-range Harness receipt fresh且可验证；没有 Provider/media/network/paid effects。

**Verification:**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_production_ad_creative.py \
  tests/test_production_commercial_execution.py \
  tests/test_production_commercial_reference.py \
  tests/test_production_commercial_source_preparation.py \
  tests/test_production_commercial_visual_review.py \
  tests/test_production_ecommerce_product_interaction_e2e.py \
  tests/test_planning_video_planner.py \
  tests/test_shot_readiness_gate.py \
  tests/test_production_video_requirement.py \
  tests/test_production_shot_router.py \
  tests/test_production_provider_neutral_adapters.py \
  tests/test_production_image_import.py \
  tests/test_production_review.py \
  tests/test_production_repair.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_state_commit_structure.py \
  tests/test_agent_harness.py -q

PYTHONDONTWRITEBYTECODE=1 python -m scripts.docs_contract_gate check
PYTHONDONTWRITEBYTECODE=1 python -m scripts.agent_harness policy-audit
PYTHONDONTWRITEBYTECODE=1 python -m scripts.architecture_gate check

git add \
  src/ai_video/production/commercial_execution.py \
  src/ai_video/production/commercial_reference.py \
  src/ai_video/production/commercial_source_preparation.py \
  src/ai_video/production/commercial_visual_review.py \
  src/ai_video/production/_state_commit_commercial_source.py \
  src/ai_video/production/_state_commit_commercial_source_recovery.py \
  src/ai_video/production/ad_creative_types.py \
  src/ai_video/production/ad_creative.py \
  src/ai_video/production/ad_creative_review.py \
  src/ai_video/planning/_planner_models.py \
  src/ai_video/planning/_asset_readiness.py \
  src/ai_video/planning/video_planner.py \
  src/ai_video/production/video_requirement.py \
  src/ai_video/production/_video_requirement_routing.py \
  src/ai_video/production/shot_router.py \
  src/ai_video/production/video_compiler.py \
  src/ai_video/production/image_import.py \
  src/ai_video/production/models.py \
  src/ai_video/production/paths.py \
  src/ai_video/production/project.py \
  src/ai_video/production/dependency.py \
  src/ai_video/production/state_commit.py \
  src/ai_video/production/review.py \
  src/ai_video/production/__init__.py \
  tests/test_production_ad_creative.py \
  tests/test_production_commercial_execution.py \
  tests/test_production_commercial_reference.py \
  tests/test_production_commercial_source_preparation.py \
  tests/test_production_commercial_visual_review.py \
  tests/test_production_ecommerce_product_interaction_e2e.py \
  tests/test_planning_video_planner.py \
  tests/test_shot_readiness_gate.py \
  tests/test_production_video_requirement.py \
  tests/test_production_shot_router.py \
  tests/test_production_provider_neutral_adapters.py \
  tests/test_production_image_import.py \
  tests/test_production_review.py \
  tests/test_production_repair.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_state_commit_structure.py \
  .agent/harness/policy.yaml \
  tests/test_agent_harness.py \
  docs/agent-primary-contract-matrix.md \
  docs/v0.2-runtime-baseline.md \
  docs/v0.2-agentic-production-roadmap.md

PYTHONDONTWRITEBYTECODE=1 python scripts/agent_harness.py inspect \
  --base-ref <final-task-commit-parent> --head-ref <final-task-commit>
PYTHONDONTWRITEBYTECODE=1 python scripts/agent_harness.py verify \
  --base-ref <final-task-commit-parent> --head-ref <final-task-commit> \
  --run-id ecommerce-product-interaction-source-preparation-final-20260825
PYTHONDONTWRITEBYTECODE=1 python scripts/agent_harness.py verify-receipt \
  .agent/harness/runs/ecommerce-product-interaction-source-preparation-final-20260825/receipt.json
```

## Delivery Boundary

该 implementation完成后，可以声明：

- AI-VIDEO拥有 product-aware commercial source preparation contract；
- exact product reference pack和 interaction keyframe可以被注册、review、批准并交给 current VideoPlanner；
- Router能结构性地选择 exact first-frame I2V capability；
- source/keyframe failure可以映射到 existing scoped repair boundary。

仍然不能声明：

- 真实青颜商品在任何 concrete Provider中已经稳定保持 Logo、label或瓶型；
- 苗家女孩身份、苗服和银饰已通过 calibrated automatic evaluator；
- “拿出并喷” temporal action已通过 generated-video commercial QA；
- Local H3、T8、Seedance或其他 Provider已完成这一路径的 empirical qualification；
- 整支 20–30 秒广告已通过 P6或 Final Acceptance。

实现完成后的下一独立 gate应是：在用户明确授权、exact product/reference/keyframe已经通过本 slice且 Provider capability匹配时，执行最小真实 Shot 04 empirical experiment；不得在此之前用更强 Prompt或更换模型掩盖 workflow evidence缺失。

## Stop Conditions

后续 implementer遇到以下任一情况必须停止本 slice并请求新的 scope decision，不得自行扩张：

- 需要给 `ProductionProject` 增加通用 Product collection或迁移 artifact layout；
- 需要修改任何 concrete Image/Video Provider adapter、workflow template或 capability declaration；
- 需要自动下载/选择 OCR、Logo、face、wardrobe或 interaction evaluator；
- 需要运行真实媒体、ComfyUI、remote/paid Provider、credential lookup或 empirical quality acceptance；
- source-image review无法在 existing P6 authority/verdict/freshness contract下实现，必须建立第二 lifecycle；
- Product identity只能通过复用 Character/Scene/generic reference role才能继续；
- Manifest migration无法保持 historical exact reopen、replay或 explicit recovery；
- repair mapping无法让 existing Dependency Graph独占 exact downstream closure。
