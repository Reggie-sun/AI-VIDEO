# AI-VIDEO Quality Gate Architecture Separation Implementation Plan

## Status

Implemented in documentation/contract-test scope；final completion仍以本任务的exact-snapshot Harness receipt为准。后续 Runtime seam 与 Drama integration必须各自创建新的active spec/plan并获得独立授权。

本计划基于 `main@2500bbb7254ed5fb2ca936437f636df9e626e44f` 的 tracked source、tests、canonical docs、`ecommerce-ad-workflow` contracts 与 fresh AI-VIDEO memory retrieval 编写。它只规划 Quality Gate architecture separation；本文档不证明 Runtime 已实现，不授权 Provider、媒体生成、Runtime mutation、P6 PASS、Final Acceptance、market-performance prediction、commit、push 或 release。

共享 checkout 中与 commercial source preparation 有关的 dirty/untracked paths 不属于本计划证据，也不在本计划的 current-state assertions 中。

## Goal

建立一个不重复 Production QA、也不混淆业务 acceptance 的 Quality architecture：

```text
Universal Production QA
  + Ecommerce Advertising Domain Gate
  + future AI Drama / Short Drama Domain Gate
  -> existing P6 Review / Repair / Final Acceptance lifecycle
```

目标是先把 boundary 固定为 durable contract：Ecommerce 与 future Drama 使用各自的 authoring、semantic、creative 和 media-acceptance rubric，同时继续复用 AI-VIDEO 对 media、timeline、composition、continuity evidence、provenance、review freshness、repair 和 durable Final Acceptance 的唯一 owner。本 slice 不实现 Runtime-facing domain evidence schema。

## Non-Goals

- 不实现完整 AI Drama / Short Drama workflow、story authoring、episode generator 或 dialogue generator；
- 不在本计划中实现 Gate、evaluator、review analyzer、repair 或 Runtime state mutation；
- 不增加新的 Manifest、Timeline、Dependency Graph、renderer、QA lifecycle、repair lifecycle 或 Final Acceptance owner；
- 不新增 `ECOMMERCE`、`DRAMA` 或 `FORMAT` 类型的 `QaLayer`；
- 不把现有 generic `SEMANTIC` 直接改名后当作完整 domain framework；
- 不实现 campaign、publishing、analytics、attribution、ROAS optimization 或 audience-retention prediction；
- 不调用 Provider，不生成或修改图片、视频、音频，不读取 credential；
- 不改变 Legacy `0.1.x` CLI、Manifest、artifact layout 或 local-first contracts。

## Problem Boundary

### Current Behavior

当前质量 architecture 不是单一“五层 Gate”，而是三个不同阶段的 contract 组合：

1. pre-submit `ShotReadinessGate`；
2. render/candidate/timeline/audio/caption hard validation；
3. P6 policy-selected review、repair 与 Final Acceptance lifecycle。

`src/ai_video/quality_gates/**` 中的 `ShotReadinessGate` 只检查 request-plan binding、plan eligibility 和 required assets，并返回 `READY` / `BLOCKED`。它不是 post-media quality、P6、activation 或 Final Acceptance。

`src/ai_video/production/models.py` 当前定义：

- `QaLayer.TECHNICAL`
- `QaLayer.LAYOUT`
- `QaLayer.STRATEGY`
- `QaLayer.SEMANTIC`
- `QaLayer.FINAL_ACCEPTANCE`

这些名称不能被当作完整业务 taxonomy。真实行为由 `src/ai_video/production/review.py` 和 state committer 决定：

| Current layer | Current executable responsibility | Boundary |
| --- | --- | --- |
| `TECHNICAL` | black、silence、clipping、required-motion freeze、video frame diversity | Universal post-render evidence，但 codec/container/resolution/fps/duration/decode 等已在更早的 hard validators 中检查 |
| `LAYOUT` | caption overflow、safe area、layer collision、transition boundary | Universal capability；threshold 和 applicability 可 policy-driven |
| `STRATEGY` | evaluator-reported `evaluated_strategy_ids` 与 `strategy_mismatch` | 当前只表示 reported Shot visual-strategy result；adjudicator 尚未证明 exact expected strategy-set coverage，更不是 advertising strategy 或 drama strategy |
| `SEMANTIC` | policy-selected evaluator/human identity 加 generic `semantic_match` | 是 evidence envelope，不含 domain identity、rubric、requirement taxonomy 或逐项 verdict |
| `FINAL_ACCEPTANCE` | 不可生成普通 `ReviewReceipt`；由 committer 汇总 required fresh receipts | durable lifecycle/rollup marker，不是第五个 evaluator |

`QaPolicy.required_layers` 当前可选择任意 review layers，并未编码固定 universal minimum。现有 Base AI Comic E2E policy 只要求 `LAYOUT`；因此该 E2E 证明的是 selected policy 下的 lifecycle closure，不是完整 Drama quality acceptance。

### Existing Hard Production Validation

下列 correctness 已由 Production Runtime 的现有 owners 在 P6 review 之前或之中负责，不应由 Domain Workflow 重复实现：

- `ResolvedTimeline`：Shot order、frame/sample timing、source trim、visual/audio/caption spans；
- render/candidate validation：artifact bytes、container/stream、codec profile、geometry、fps、frame count、duration、audio stream；
- audio import/probe：format、sample count、channels、decoded identity、duration/loudness evidence；
- caption binding：canonical audio transform、frame/sample timing、structured caption identity；
- composition/render output identity 与 exact graph/render/timeline binding；
- immutable review request/evidence/receipt、freshness、repair 和 Final Acceptance state。

### Existing Ecommerce Boundary

`.agents/skills/ecommerce-ad-workflow/` 的 `G7 Ad QC` 当前属于 **Authoring Gate**：

- `AdQCReport.ready` 表示 authoring package 通过 structured preflight；
- `PASS` / `BLOCKER` findings 检查 Product Truth、rights、claim lineage、planned Hook/beat/presentation/copy/audio/CTA/variant/traceability；
- Runtime handoff 只允许 requirements、proposals 和 capability gaps；
- contract 显式禁止 Provider execution、Manifest fields、P6 PASS、Final Acceptance 和 performance claims。

`src/ai_video/production/ad_creative_review.py` 是另一个 pure projection-integrity review。`AdCreativeReviewReport.is_ready` 只表示 sealed `AdCreativePlan -> CompositionSpec` handoff 一致；`production_verdict` 固定为 `None`。当前仓库没有真实媒体上的 whole-ad Ecommerce Domain Acceptance。

### Existing Drama Boundary

当前仓库没有正式 `ai-short-drama-workflow`、Drama QC 或 typed Drama acceptance contract。`Story` 只有 logline、synopsis 和 beats；Character/Scene/Storyboard models 支持 identity、appearance、wardrobe 和 `narrative_intent`，但没有 motivation、conflict、escalation、dialogue quality、emotional arc、payoff、episode closure 或 cliffhanger rubric。

Production continuity 与 narrative continuity 必须保持不同 owner：

- wardrobe、identity、object state、scene、action、screen direction、space、lighting 和 cross-shot perceptual consistency 属于 Production continuity；
- motivation、causality、relationship logic、decision consistency、emotional progression、setup/payoff 属于 future Drama domain continuity。

## Architecture Decision

### Selected Option: B — Universal Production QA + Domain-Specific Acceptance Gate

这是本计划唯一主推荐。

| Option | Decision | Reason |
| --- | --- | --- |
| A. shared `TECHNICAL/LAYOUT/STRATEGY/SEMANTIC/FINAL_ACCEPTANCE` with parameters | Reject | `STRATEGY` 和 `SEMANTIC` 当前只是 generic envelopes；把广告与剧情 rubric 塞入同一 boolean contract 会隐藏 requirement coverage、domain identity 和不同 failure semantics |
| B. Universal Production QA + Domain-specific Acceptance Gate | Select | 复用既有 hard validators 和唯一 P6 lifecycle，同时让 Ecommerce 与 Drama 保持业务 truth、rubric 和 creative acceptance ownership |
| C. Universal + Format + Domain | Defer | `DeliveryProfile`、`CompositionSpec`、`ResolvedTimeline` 和 policy 已能表达当前 format/timing/layout 约束；没有证据支持新增独立 Format lifecycle 或 owner |

若未来多个 domain 出现稳定、重复且不属于 delivery profile 的 format-specific acceptance requirements，应先以 policy/profile contract 证明复用价值，再单独决定是否引入 Format taxonomy。当前不得预建第三层。

## Target Architecture

```text
Domain Authoring
  Ecommerce Ad QC                       future Drama Authoring QC
  truth / claims / hook / CTA           causality / motivation / conflict / payoff
              \                         /
               sealed intent and requirements
                            |
                            v
AI-VIDEO Production Runtime
  hard media + timeline + composition validation
  universal/policy-driven review evidence
  physical/perceptual continuity evidence
                            |
                            v
Domain Media Acceptance
  Ecommerce media rubric                future Drama media rubric
  product/claim/hook/CTA presentation   acting/emotion/pacing/dialogue/payoff
              \                         /
               typed evidence for current P6 lifecycle
                            |
                            v
ProductionStateCommitter
  ReviewReceipt -> Repair -> FinalAcceptanceReceipt
```

Domain Workflow 可以拥有 authoring verdict、rubric 和 evidence proposal，但不得直接写 Manifest、激活 candidate、签发 Production PASS 或创建 durable Final Acceptance。AI-VIDEO 必须重新绑定 exact selected project/graph/render/output/timeline/policy/evaluator evidence，并由现有 committer adjudicate 和持久化。

## Gate Taxonomy

### Must Remain Universal

- artifact existence、registered bytes、content identity、path containment 和 provenance；
- media decode、container/codec、resolution、fps、frame count、duration 和 render-output validity；
- canonical `ResolvedTimeline`、frame/sample timing、source trim 和 composition correctness；
- exact selected graph/render/output/timeline/policy binding；
- black/corrupt/frozen-frame evidence、clipping 和 required audio validity；
- caption timing/binding 和 deterministic layout geometry；
- immutable request/evidence/receipt、freshness、one-use analysis、repair invalidation/review 和 Final Acceptance lifecycle；
- physical/perceptual continuity evidence contract；candidate-specific activation safety继续由其现有独立 lifecycle负责，不得与 Final Acceptance合并。

### Shared But Policy-Driven

- silence 和 loudness thresholds，因为 intentional silence 与内容类型有关；
- caption safe area、readability、important-subject occlusion 和 transition tolerances；
- character identity、wardrobe、object/product state、scene、action、screen direction、spatial、lighting 和 cross-shot continuity dimensions；
- evaluator/human authority、minimum evidence strength、required subject/Shot coverage；
- vertical、dialogue-heavy、motion-graphics、cinematic 或 episodic delivery constraints，作为 existing profile/policy input，而非独立 acceptance owner。

“Shared”表示共享 evidence schema、evaluator primitive 或 lifecycle；不表示所有 dimensions 对所有项目都 required，也不表示 Domain Workflow 可以重新拥有 Production state。

### Must Not Be Universal

- Ecommerce：Product Truth、rights、claim correctness/lineage、prohibited claims、commercial Hook、product intro/demo/proof/hero presentation、commercial graphics intent、CTA、end card、brand closure 和 creative variant isolation；
- Drama：premise/story coherence、motivation、goal、relationship causality、conflict、stakes、escalation、reversal、dialogue semantics、emotional progression、reveal/payoff、episode closure、cliffhanger 和 continuation intent；
- CTR、CVR、CPA、ROAS、hold rate、retention、completion、continuation、follow、share、comment；
- 一个跨 Ecommerce 与 Drama 的 `Quality Score`。

## Ownership Matrix

| Concern | Single owner | Shared? | Blocking? |
| --- | --- | --- | --- |
| media/container/decode/render validity | AI-VIDEO Production Runtime | universal | hard fail；始终阻塞对应 candidate/acceptance |
| timeline/frame/sample/source trim/composition | `ResolvedTimeline` and existing composition/render owners | universal | hard fail；始终阻塞 |
| audio/caption structural validity | existing Production audio/caption owners | universal | hard fail；layout/perceptual thresholds由 policy决定 |
| physical/perceptual continuity evidence | AI-VIDEO continuity/review contracts | shared, policy-driven | applicable 且 required 时阻塞 |
| immutable QA evidence, receipt freshness, repair | `ProductionStateCommitter` and existing P6 lifecycle | universal | required evidence missing/fail/stale 时阻塞 |
| durable Final Acceptance | `ProductionStateCommitter.record_final_acceptance()` and existing P6 state | not shared | 唯一 quality blocking rollup owner；不自动激活 candidate |
| candidate activation | `ProductionStateCommitter` façade + existing candidate-specific private committer paths | shared infrastructure, separate lifecycle | 只激活 exact qualified candidate；不得由 Final Acceptance或 Domain PASS隐式推进 |
| Product Truth, rights, claims | `ecommerce-ad-workflow` | Ecommerce only | authoring blocker；进入 P6 后 exact required evidence也可阻塞 final acceptance |
| commercial Hook/product presentation/proof/CTA/brand closure | `ecommerce-ad-workflow` rubric | Ecommerce only | selected requirement 在 authoring/media stage 可分别阻塞 |
| story/motivation/conflict/dialogue/payoff/cliffhanger | future `ai-short-drama-workflow` | Drama only | future selected authoring/media requirements可阻塞 |
| narrative continuity | future Drama workflow/rubric | Drama only | required 时阻塞；不得由 physical continuity receipt替代 |
| market metrics | future analytics/empirical feedback owner, outside this plan | outcome evidence only | 默认不得阻塞 Production Final Acceptance，也不得反推 Gate PASS |

## Pre-Generation And Post-Generation Gates

### Ecommerce

Pre-generation authoring checks：

- Product Truth、rights、claim lineage、prohibited claims；
- audience/objective/angle/promise/proof binding；
- first-second Hook intent、required AdBeat roles 和 product presentation plan；
- CTA/end-card/brand-closure intent；
- planned commercial graphics/audio coverage；
- exact traceability、capability-gap honesty 和 one-variable variant isolation。

Post-generation media checks：

- actual product presence、identity、packaging、demonstration 和 interaction；
- Hook 是否在 intended time window 真正呈现；
- claim/proof/CTA/end card 是否在 exact media 中存在、清晰且对应 approved truth；
- commercial typography/readability、product occlusion、audio/graphics synchronization；
- product integration、hero presentation、brand closure、pacing 和 delivery quality。

### Future Drama

Pre-generation authoring checks：

- premise clarity、causal structure、setup/payoff 和 reveal order；
- character goal、motivation、relationship logic 和 emotional-state transitions；
- conflict、stakes、escalation、reversal、resolution；
- dialogue function/voice/redundancy/exposition；
- episode opening、pacing intent、closure、cliffhanger 和 next-episode motivation。

Post-generation media checks：

- acting/performance、visual emotion 和 emotional progression；
- delivered dialogue naturalness、voice consistency 和 timing；
- actual pacing、tension、reversal/payoff 和 cliffhanger effectiveness；
- perceptual narrative causality across scenes/episodes。

## Deterministic And Empirical Evidence

| Requirement kind | Preferred evidence | Example | Verdict use |
| --- | --- | --- | --- |
| deterministic structure/identity | typed validator against sealed artifacts/exact bytes | missing CTA、prohibited claim、duration mismatch、missing asset、subtitle overflow | 可直接产生 requirement-level blocking finding |
| measured media property | deterministic analyzer with versioned measurement contract | black frame、clipping、safe-area geometry、caption overlap | threshold由 policy决定；required 时阻塞 |
| evaluator-dependent semantics | explicit versioned model evaluator | product naturalness、Hook salience、acting、emotion、story tension | 必须记录 evaluator authority、rubric/version、target、coverage和 uncertainty；不得自报 Final Acceptance |
| subjective/high-impact judgment | human review | claim interpretation、dialogue quality、emotional payoff | 可作为 policy-selected strong evidence；必须绑定 exact media和rubric |
| audience/business outcome | measured market metrics | ROAS、retention、continuation | 仅 empirical feedback；不等同 quality verdict |

Engineering/deterministic PASS 不能替代 empirical/model-quality evidence。反之，单个模型 score 或 audience metric 也不能覆盖 artifact identity、timeline correctness、provenance 或 lifecycle safety。

## Verdict And Score Contract

- Production review 继续使用 `PASS` / `FAIL` / `NOT_EVALUATED`；required `NOT_EVALUATED` 必须 fail closed。
- Authoring readiness 可以继续使用 `PASS` / `BLOCKER`，但 `BLOCKER` 不是新的 P6 `QaVerdict`。
- score 可以存在于 raw/advisory evidence 中，但必须携带 domain、rubric/version、dimension、threshold/calibration 和 exact target identity。
- 不得把 score 作为跨 domain 总分，不得用平均分抵消 required requirement 的 `FAIL` 或 `NOT_EVALUATED`。
- 只有 selected `QaPolicy` 明确要求、且被 exact fresh P6 receipt 覆盖的 universal/domain requirements 才能参与 durable Final Acceptance。
- 必须显式禁止 `Ad QC PASS -> predicts ROAS` 与 `Drama QC PASS -> predicts audience success`；除非未来另有经过真实数据校准、验证和独立批准的 empirical model contract。

## Contract Changes

### Authorized Slice: Boundary Contract Only

本 plan 唯一授权的 implementation slice 不修改 Production Runtime schema。durable boundary 由现有 `docs/agent-primary-contract-matrix.md` 继续拥有；不新建 active canonical spec，因此不新增 `.agent/harness/docs-contracts.yaml` surface。该 slice 把以下边界变为可验证 invariant：

- `ShotReadinessGate.READY` 不等于 post-media quality/P6/activation；
- `AdQCReport.ready` 只等于 Ecommerce authoring readiness；
- `AdCreativeReviewReport.is_ready` 只等于 deterministic handoff integrity；
- `AdCreativeReviewReport.production_verdict` 继续为 `None`；
- Base AI Comic Final Acceptance 只表示 exact selected policy 的 durable closure，不表示 Drama semantic acceptance；
- domain authoring result 不得写 Manifest 或产生 `FinalAcceptanceReceipt`。

本 slice 的 contract changes 限定为：

- 在 contract matrix 中登记 Universal Production QA、Domain Authoring/Media Acceptance、Market Performance 的唯一 owner和禁止旁路；
- 在 runtime baseline中记录 current layer真实语义、Ecommerce authoring/handoff boundary和 Drama-not-implemented boundary；
- 在 roadmap中登记后续 Runtime-facing domain review只能作为独立 future slice；
- 在 Ecommerce skill boundary docs中保持 `AdQCReport.ready` / Runtime handoff 不产生 Production verdict；
- 加入 focused contract/regression tests，证明 existing outputs不创建第二 QA lifecycle或 Final Acceptance。

### Future Runtime Seam Requirements — Not Authorized By This Plan

只有本 slice 完成且另有 accepted active spec/plan 后，才可以在现有 P6 lifecycle 内增加 typed domain requirement coverage。最终名称由 future implementation slice 决定，本计划不预设 `DomainReviewProposal` 等 API 名称，也不授权修改 `QaPolicy`、review artifacts、Manifest 或 committer。

future contract 至少必须表达：

- exact domain/profile identity；
- rubric ID 和 version；
- authoring/media stage 与 target kind；
- stable requirement IDs、required/optional semantics 和 subject/Shot coverage；
- deterministic/model/human evidence authority 与 strength；
- exact project/graph/render/output/timeline/policy/media identity；
- requirement-level finding、rationale 和 measured payload；
- aggregation rule：任何 required `FAIL` / `NOT_EVALUATED` 均不得被 score 抵消。

AI-VIDEO 必须在 analyzer effect 前选择 content-addressed Domain acceptance profile，不能让 evaluator自选 domain、rubric或 requirement subset。该 profile 必须：

- 由 current `QaPolicy` 精确内嵌或引用；
- hash-bind exact sealed authoring truth，例如 accepted Ecommerce package、Product Truth/claim ledger references和 exact `AdCreativePlan`；
- 进入 `ReviewRequest`，并由 `ReviewEvidence`、`ReviewReceipt` 和 committer strict reopen/re-adjudication逐级验证；
- 在 authoring truth、rubric、policy或 selected media改变时按 current freshness/invalidation contract失效；
- 只允许 Domain Workflow提出 sealed profile/artifact，最终 Production policy选择权仍属于 AI-VIDEO。

future seam 应复用 current `ReviewRequest -> ReviewEvidence -> ReviewReceipt -> FinalAcceptanceReceipt` lifecycle。由于 active reviews 当前按 `QaLayer` 管理，future Runtime slice 应优先让单个 `SEMANTIC` receipt聚合并证明完整 typed requirement coverage，而不是未经 migration 就创建多个相互覆盖的 same-layer active receipts。

`STRATEGY` 继续表示 current evaluator-reported visual-strategy result；不得复用其名称承载 advertising strategy 或 narrative strategy。`SEMANTIC` 继续作为 generic lifecycle envelope，但 domain requirement profile 不得再退化为裸 `semantic_match` boolean。

future Drama 只有在正式 workflow/spec、owner、authoring artifact 和 rubric 被接受后，才可以通过另一个独立 plan 接入同一 typed domain evidence seam。本 plan 不创建 Drama schemas、evaluator 或 runtime enums。

## Exact Owner And Old Path

### Exact Owner

- durable quality boundary：`docs/agent-primary-contract-matrix.md`；
- current implementation truth：`docs/v0.2-runtime-baseline.md`；
- future slice routing：`docs/v0.2-agentic-production-roadmap.md`；
- Ecommerce authoring truth/rubric：`.agents/skills/ecommerce-ad-workflow/`；
- executable lifecycle truth：existing source/tests，保持不变。

### Old Path To Retire

`none`。本 slice 不删除或替换 Runtime path，也不迁移 artifact。它只禁止未来把 generic `STRATEGY` / `SEMANTIC` 名称、`AdQCReport.ready` 或 `AdCreativeReviewReport.is_ready` 误解释为 complete cross-domain Production acceptance。

### Unchanged Contracts

- `QaLayer`、`QaVerdict`、`QaPolicy`、`ReviewRequest`、`ReviewEvidence`、`ReviewReceipt`、`FinalAcceptanceReceipt` bytes和schema不变；
- `ProductionStateCommitter`、`ResolvedTimeline`、Dependency Graph、Registry、renderer、repair和candidate activation ownership不变；
- Ecommerce skill schemas、`AdQCReport.ready` 和 `AdCreativeReviewReport.production_verdict=None` 不变；
- Legacy `0.1.x`、Provider、paid/cloud、media和market-metric paths不变。

## Migration And Rollback

### Schema Migration

`none`。

### Data And Runtime Migration

`none`。不重写 historical policy、review、receipt、Manifest、Registry或media artifacts。

### Rollback

回退本 slice 的 exact task-owned docs和focused tests即可；不需要 state recovery、artifact conversion或 Runtime rollback。Rollback 后 current executable behavior和所有 historical hashes必须保持不变。不得借 rollback修改或清理 concurrent dirty/untracked commercial work。

未来 Runtime seam若需要改变 active-review indexing、Manifest schema、receipt identity或 authoring-artifact persistence，必须由独立 migration spec/plan定义 forward migration、strict reopen和 rollback；本 plan 不授权。

## Compatibility

- 本 plan 是 docs/tests compatibility slice，无 Runtime artifact migration。
- 现有 Ecommerce skill schema、`AdQCReport.ready` 和 package validation semantics保持兼容；加强的是“不等于 Production acceptance”的 contract。
- 现有 `AdCreativeReviewReport` API 保持 pure，`production_verdict=None` 不变。
- historical `QaPolicy`、`ReviewRequest`、`ReviewEvidence`、`ReviewReceipt` 和 `FinalAcceptanceReceipt` bytes 必须 strict reopen，hash 不变。
- domain requirements 只能 additive 于 applicable universal minimum，不能替换 media/timeline/provenance/lifecycle checks。

## Runtime Impact

无 Production Runtime behavior 或 schema change。只稳定 architecture/ownership contract 和 executable boundary tests。

future Runtime slice 即使被另行批准，也只能扩展 P6 semantic evidence qualification，不得改变：

- `ProductionStateCommitter` 的唯一 write/activation/recovery/final-acceptance ownership；
- `ResolvedTimeline` 的唯一 timing/order/frame/sample ownership；
- current renderer、Dependency Graph、Registry 和 repair lifecycle；
- analyzer 只能产 raw evidence、committer重新 adjudicate 的规则；
- exact replay、freshness、provenance 和 fail-closed semantics。

Domain Skill 不执行 Runtime review，不持久化 Production verdict；它只提供 sealed authoring artifacts、rubric/requirement definitions 或 review proposals，供 AI-VIDEO 在 accepted Runtime slice 中验证和消费。

## Implementation File Map

以下只列本 plan 唯一授权 slice 的 expected paths：

- `docs/agent-primary-contract-matrix.md`；
- `docs/v0.2-runtime-baseline.md`；
- `docs/v0.2-agentic-production-roadmap.md`；
- `.agents/skills/ecommerce-ad-workflow/SKILL.md`；
- `.agents/skills/ecommerce-ad-workflow/references/ad-qc.md`；
- `.agents/skills/ecommerce-ad-workflow/references/runtime-handoff.md`。

现有 `tests/test_ecommerce_ad_workflow_skill.py`、`tests/test_production_ad_creative.py`、`tests/test_shot_readiness_gate.py`、`tests/test_production_review.py` 和 `tests/test_production_base_ai_comic_e2e.py` 是 verification owners。只有发现当前 boundary 缺少 executable assertion 时，才在同一授权 slice 内最小补充对应现有 test file；不得顺带改变 Production behavior。所有列出的 paths 已有 policy route，本 slice 不预期修改 `.agent/harness/policy.yaml`。

### Must Not Create Or Modify For This Architecture

- any `src/ai_video/**` Runtime file in this slice；
- a new active canonical spec or docs-contract registry surface；
- a second Manifest or state directory；
- a second timeline/composition engine；
- a domain-owned Final Acceptance writer；
- a generic market-score field on `FinalAcceptanceReceipt`；
- a formal Drama workflow before its own accepted spec；
- Provider adapters, credentials, live media or paid-execution paths。

## Test Strategy

### Universal Gate Regression

- existing hard media/timeline/audio/caption/render validators仍阻塞 invalid artifacts；
- P6 required `FAIL`、`NOT_EVALUATED`、missing 或 stale receipt仍阻塞 Final Acceptance；
- exact graph/render/output/timeline/policy/evidence identity仍被重新验证；
- repair后必须 fresh review；replay不得重复 analyzer/committer side effects。

### Ecommerce-Specific Gate

- Product Truth、rights、claim lineage、prohibited claim、Hook/beat/product presentation/CTA/brand/variant failures只由 Ecommerce authoring rubric解释；
- `AdQCReport.ready` 和 `AdCreativeReviewReport.is_ready` 永远不生成 Production verdict、Manifest mutation 或 Final Acceptance；
- current Runtime bridge继续保持 `production_verdict=None`，不引入 post-media Ecommerce verdict。

### Domain Boundary Regression

- Current Ecommerce authoring/handoff models不直接编码Production verdict、`ReviewReceipt`或`FinalAcceptanceReceipt`，且当前没有把这些outputs转换为P6 evidence的canonical bridge。现有generic `SEMANTIC` envelope尚未type-bind domain/rubric/requirement coverage；禁止错误转换是contract boundary，完整Runtime enforcement属于future typed seam；
- 本 slice不引入 Drama domain model、Ecommerce/Drama `QaLayer` 或 Format lifecycle；
- `STRATEGY` reported visual-strategy result不能被文档或 API重新声明为 advertising/narrative acceptance；
- physical continuity receipt不能满足 narrative continuity；
- selected policy中的 universal required checks不能被 authoring readiness替换。

### Ownership And Lifecycle

- Domain Skill/adapter不能直接修改 Manifest、active pointers、repair state或 Final Acceptance；
- 只有 current `ProductionStateCommitter` 可持久化 review/final-acceptance state；
- 不创建第二 timeline、renderer、Registry、Dependency Graph 或 receipt lifecycle；
- Final Acceptance只消费 exact fresh required receipts；
- historical artifacts strict reopen，且本 slice不改变 active pointers或 artifact hashes。

### Focused Verification Commands

本授权 slice 至少运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_ecommerce_ad_workflow_skill.py \
  tests/test_production_ad_creative.py \
  tests/test_shot_readiness_gate.py \
  tests/test_production_review.py \
  tests/test_production_base_ai_comic_e2e.py -q
python -m scripts.docs_contract_gate check
python -m scripts.agent_harness policy-audit
```

最终必须执行 changed-path policy要求；若修改 executable tests/tooling，按 policy 对 exact staged snapshot 或 exact commit range 生成 fresh passing Harness receipt。所有测试默认 offline、fake/local、no-provider。

## Execution Sequence

以下 milestones 属于同一个可独立验收 slice，不是多个 implementation slices。

### Milestone 1 — Canonical Ownership Text

- 在现有 contract matrix、baseline和roadmap中明确 hard universal validation、policy-driven universal review、domain authoring/media acceptance和 market metrics四个 truth planes；
- 固定 Ecommerce authoring/handoff contracts不等于 P6/Final Acceptance；
- 固定 Base AI Comic E2E不等于 Drama QC。

### Milestone 2 — Executable Boundary Evidence

- 加入/加强focused tests，证明`ShotReadinessGate.READY`、`AdQCReport.ready`和`AdCreativeReviewReport.is_ready`的current output schemas不直接编码P6/Final Acceptance，且没有canonical bridge；不得把这项evidence扩大为generic `SEMANTIC` payload已经具备domain/rubric/coverage enforcement；
- 保持 current Final Acceptance、candidate activation、timeline和 Manifest owner不变；
- 不新增 source/runtime contract，只验证 current boundary。

### Milestone 3 — Exact-Snapshot Verification

- 运行 focused offline tests、Documentation Contract Gate和policy audit；
- 按 changed-path policy验证 exact staged snapshot或 exact commit range；
- 确认 diff只有 task-owned docs/tests，无 Runtime schema或artifact变化。

Convergence criteria：tests、contract matrix、baseline、roadmap和 Ecommerce skill文档对上述 owner/边界只有一套表述；current Runtime behavior和 artifact hashes保持不变。

## Future Follow-Ups — Non-Authorizing

以下只是 sequencing direction，均不属于本 plan 的 executable scope：

1. Runtime-facing typed domain profile/evidence seam：先为 Ecommerce post-media acceptance创建独立 active spec/plan，包含 exact preselected profile和 authoring-truth hash binding、migration、rollback及 full P6 tests。
2. Future Drama adapter：只有 formal Drama workflow/spec存在后，再创建另一份独立 plan；复用 approved seam，但保持 narrative rubric与 Ecommerce rubric不可互换。

## Risks And Mitigations

| Risk | Failure mode | Mitigation |
| --- | --- | --- |
| duplicated ownership | Domain Skill写 Manifest或自行签发 Production PASS | typed proposal/evidence only；committer重新绑定和 adjudicate；ownership tests |
| evaluator nondeterminism | 同一媒体在模型 evaluator中漂移 | versioned evaluator/rubric、raw evidence、uncertainty、human authority、no blind retry |
| domain leakage | Ecommerce rubric被 Drama复用或 generic `semantic_match`掩盖差异 | explicit domain/profile/requirement IDs和 routing-negative tests |
| score misuse | 总分掩盖 required failure，或被解释为 ROAS/retention predictor | requirement-level fail closed；score advisory only；market plane独立 |
| lifecycle duplication | future多个 same-layer receipts相互覆盖，或新增第二 Final Acceptance | future seam聚合完整 coverage；若需 indexing migration则单独 stop/spec |
| universal bypass | Domain PASS替换 technical/timeline/provenance checks | universal minimum additive invariant和 Final Acceptance tests |
| overengineering | 在没有 Drama owner或 format缺口时预建 framework | 本 slice无 Runtime schema；不加 Format Gate；Drama只留 non-authorizing extension criteria |
| evidence overclaim | deterministic PASS被解释为 creative/market success | 明确 proof levels和 empirical evidence strength；final delivery报告未验证边界 |

## Acceptance Criteria

- existing canonical owner明确选择 Option B，并说明拒绝 A、暂缓 C 的 current-code理由；
- `TECHNICAL`、`LAYOUT`、`STRATEGY`、`SEMANTIC`、`FINAL_ACCEPTANCE` 的 current executable semantics有源码/测试依据；
- Universal、shared-policy、Ecommerce、future Drama和 market metrics分类无 duplicate owner；
- `AdQCReport.ready`、`AdCreativeReviewReport.is_ready`、`ShotReadinessGate.READY`均有executable evidence证明current outputs不直接编码P6/Final Acceptance；current generic `SEMANTIC` envelope的domain/rubric/coverage gap已明确记录并留给future Runtime seam；
- Production continuity与 narrative continuity owner分开；
- score只允许作为 advisory evidence，required `FAIL`/`NOT_EVALUATED`不可被抵消；
- 本 slice无 Production Runtime schema/artifact hash变化；
- schema migration、data migration和old path retirement均为 `none`；rollback只涉及 exact task-owned docs/tests；
- policy-required docs/tests/Harness checks对 exact snapshot或commit range通过。

## Stop Conditions

后续 implementation 遇到以下任一情况必须停止当前 slice并重新决策：

- 需要改变 Manifest schema、active review indexing或 historical receipt bytes；
- 需要新增第二 writer、automatic activation/recovery或 Final Acceptance owner；
- domain requirement无法在 exact current render/timeline/policy identity上归因；
- evaluator输出只有 aggregate score，无法证明 required requirement coverage；
- Ecommerce接入要求修改 Drama或预建不存在的 Drama workflow；
- Format layer没有独立、重复、可验证的 contract价值，只是 taxonomy美化；
- 需要 Provider、媒体、credential、paid execution或新的 external authorization。

## Delivery Boundary

完成本计划文件只表示 architecture analysis 与 implementation sequencing 已稳定。它不表示 Quality Gate separation 已实现，不表示 Ecommerce media acceptance 或 Drama QC 已存在，也不表示任何项目、Shot、广告或剧集通过 P6、Final Acceptance 或市场验证。
