---
surface_id: quality_gate_architecture
canonical: true
spec_status: accepted
implementation_status: foundation_only
live_status: not_applicable
quality_status: not_evaluated
release_status: unreleased
runtime_status_owner: docs/v0.2-runtime-baseline.md
roadmap_owner: docs/v0.2-agentic-production-roadmap.md
contract_version: quality-gate-architecture/1
---

# AI-VIDEO Quality Gate Architecture Specification

## Status

Accepted architecture contract；boundary documentation与current-output contract tests已实现，
two-stage Product Runtime orchestration尚未实现、未live验证、未release。本Spec不授权Provider、
媒体生成、Manifest/schema migration、automatic repair、candidate activation或Final Acceptance。

配套implementation plan：
`docs/superpowers/plans/2026-08-25-ai-video-quality-gate-architecture-separation.md`。

## Problem Boundary

AI-VIDEO现有quality-related checks分散在Planning preflight、Registry/media/timeline/render
validators、P6 Review/Repair与domain authoring workflows中。名称中包含`Gate`、`QA`、
`Review`或`ready`不表示它们属于同一个post-media acceptance层，也不表示存在自动caller。

本Spec只定义两个top-level post-media quality gates：

```text
Rendered Media
    |
    v
Gate 1: Universal Production QA
    | PASS
    v
Gate 2: Domain-Specific Acceptance
    | PASS
    v
Final Acceptance rollup
```

Ecommerce、Drama、AI Comic与future domains不是额外top-level gates；它们是Gate 2下互斥、
显式选择的domain profiles。`Final Acceptance`不是第三个quality evaluator gate，而是现有
`ProductionStateCommitter`对exact current evidence的durable rollup。

## Goals

- 固定只有两个top-level post-media quality gates；
- 复用现有hard validators、P6 evidence/adjudication与single committer lifecycle；
- 让Universal与selected Domain verdict均fail closed且绑定exact current media identity；
- 区分“进入owner API后校验必执行”与“Product Runtime自动调度下一阶段”；
- 为future one-shot orchestration规定顺序、停止条件与禁止副作用；
- 保持domain truth/rubric独立，不把Ecommerce或Drama提升成新的lifecycle owner。

## Non-Goals

- 不把`TECHNICAL/LAYOUT/STRATEGY/SEMANTIC/FINAL_ACCEPTANCE`声明为五个top-level gates；
- 不把`ShotReadinessGate`、Ecommerce G0-G7或`AdCreativeReviewReport`纳入两个post-media gates；
- 不新增Format Gate、第二QA lifecycle、第二Final Acceptance owner或background watcher；
- 不在本Spec中定义Ecommerce、Drama或AI Comic的完整runtime rubric/schema；
- 不授权automatic repair、rerender、Provider retry、fallback、activation或recovery；
- 不从quality PASS推导CTR、CVR、ROAS、retention或其他market outcome。

## Gate 1: Universal Production QA

Gate 1适用于所有domains。它由现有owners共同实现，不是一个新的God Module或第五层
taxonomy。至少覆盖：

- registered bytes、content identity、path containment与provenance；
- media decode、container/codec、geometry、fps、frame count、duration与stream identity；
- canonical `ResolvedTimeline` order、frame/sample timing、source trim与span binding；
- composition/render identity、audio/caption structural correctness；
- 可适用的P6 `TECHNICAL`维度：black、silence、clipping、required-motion freeze与frame diversity；
- 可适用的P6 `LAYOUT`维度：caption overflow、safe area、layer collision与transition boundary；
- accepted Universal profile声明适用且selected policy要求的shared physical/perceptual continuity evidence。

Universal hard validation在显式进入其owner action后必须内嵌执行并fail closed。例如
load、resolve、render、import或candidate `validate_once()`仍由caller显式发起；成功fetch
本身不得被解释为自动validate或activate。

Gate 1 PASS必须绑定exact current Project/Registry/graph/render/output/timeline/policy identity。
缺失、stale、tampered、`FAIL`或required `NOT_EVALUATED`都不能进入Gate 2。

### Universal Minimum Coverage

Future coordinator不能仅相信任意`QaPolicy.required_layers`就是完整Gate 1。它必须在analyzer
effect前选择一个content-addressed Universal profile，声明本项目/DeliveryProfile适用的hard
checks与required shared review layers，并验证selected `QaPolicy.required_layers`是该集合的
superset：

- hard media/timeline/provenance/render validation始终required，不能由policy删除；
- `TECHNICAL`对final rendered media required；
- `LAYOUT`在存在caption、graphic layer、safe-area或transition requirement时required；
- applicable physical/perceptual continuity必须显式列为required evidence；
- missing profile、empty/invalid profile、applicability无法判定或policy coverage不完整均在Gate 2
  前fail closed为`NOT_EVALUATED`。

Current Runtime尚无该Universal profile schema或coverage validator；current
`QaPolicy.required_layers`仍可选择任意层。以上是future two-stage orchestration的accepted target
contract，不得从现有Base AI Comic layout-only policy推断已实现。

## Gate 2: Domain-Specific Acceptance

Gate 2只运行一个preselected domain profile。Profile必须在analyzer effect前选择并
content-addressed，不能由evaluator根据媒体内容自行猜测domain或rubric。

```text
Domain-Specific Acceptance
  |- Ecommerce profile
  |- Drama profile
  |- AI Comic profile
  `- Future explicitly accepted profile
```

每个profile至少必须绑定：

- exact domain/profile identity与rubric ID/version；
- sealed authoring truth及其content hash；
- stable requirement IDs、required/optional semantics与exact target coverage；
- current graph/render/output/timeline/policy/media identity；
- deterministic、explicit evaluator或human evidence authority；
- requirement-level `PASS` / `FAIL` / `NOT_EVALUATED`与aggregation rule。

任何required requirement的`FAIL`或`NOT_EVALUATED`必须使Gate 2 fail closed；aggregate
score不得抵消。Gate 2的evidence必须进入existing P6 binding/adjudication lifecycle，Domain
Skill或evaluator不得直接创建active Manifest state或签发Final Acceptance。

Ecommerce、Drama与AI Comic只是profile examples：

- Ecommerce可检查商品/包装/Logo identity、physical interaction、claim delivery、Hook、CTA
  与brand closure；
- Drama可检查motivation、causality、relationship logic、emotional progression、dialogue、
  setup/payoff与cliffhanger；
- AI Comic必须由其正式accepted authoring/rubric contract定义，不得由Base AI Comic E2E的
  layout-only policy推断。

当前committed runtime没有完整typed Domain-Specific Acceptance profile/seam。Ecommerce
`AdQCReport.ready`仅为authoring readiness；`AdCreativeReviewReport.is_ready`仅为handoff
integrity且`production_verdict=None`。当前也没有formal Drama或AI Comic domain acceptance。

## Final Acceptance Rollup

`ProductionStateCommitter.record_final_acceptance()`继续是唯一durable rollup owner。
Final Acceptance不是第三个quality gate，也不重新运行evaluator。在target two-gate
orchestration落地后，只有以下条件同时满足时才能声称two-gate Final Acceptance：

1. Gate 1的所有selected required evidence均为exact current fresh PASS；
2. selected Domain profile存在，且Gate 2完整coverage为exact current fresh PASS；
3. graph、render、output、timeline、policy与receipt identities仍然current；
4. render dependency state仍fresh。

Current committer只强制selected `QaPolicy.required_layers`对应的fresh receipts，尚未type-bind
Gate 2 profile/rubric/coverage；Base AI Comic的layout-only closure正是该current contract的例子。
因此typed Domain seam落地前，现有Final Acceptance不得被扩大解释为two-gate acceptance。

本Spec不授权自动调用`record_final_acceptance()`。即使future coordinator报告
`eligible_for_final_acceptance`，durable Final Acceptance仍保持显式action，除非后续独立
spec/plan明确改变该trigger contract。

## Preflight Gates Outside This Taxonomy

下列checks重要但不属于两个post-media gates：

| Preflight | Meaning | Excluded claim |
| --- | --- | --- |
| `ShotReadinessGate` | pre-submit request/plan binding、eligibility与required assets | 不证明media quality、P6、activation或Final Acceptance |
| Ecommerce G0-G7 / `AdQCReport.ready` | authoring truth、claims、Hook、presentation、copy/audio、traceability与handoff readiness | 不证明whole-ad post-media acceptance |
| `AdCreativeReviewReport.is_ready` | sealed plan到composition的pure handoff integrity | `production_verdict`必须保持`None` |

这些preflight可以阻止错误输入进入Production，但其PASS不能替代Gate 1或Gate 2。

## Trigger And Automation Contract

### Current Trigger Truth

| Surface | Current trigger | Automatic scope |
| --- | --- | --- |
| hard load/resolve/render/import validators | caller显式进入owner API | API内部强制；无background scheduling |
| video candidate validation | caller显式调用`validate_once()` | fetch不自动validate/activate |
| `ShotReadinessGate` | `require_current_video_plan()` façade显式调用 | façade内部自动；无全局Production caller |
| Ecommerce contract validation | Skill CLI显式调用 | 无Runtime caller |
| P6 review lifecycle | orchestration显式调用`begin_review()`、`run_review_analysis()`、`record_review_receipt()` | committer内部重新adjudicate；无product-level automatic caller |
| Final Acceptance | orchestration显式调用`record_final_acceptance()` | 不因最后一层PASS自动触发 |

“Gate存在”不得被报告为“标准Runtime自动调用”。Base AI Comic E2E中显式串联的layout-only
review/repair/final-acceptance是test orchestration evidence，不是Product Runtime background
automation。

### Future One-Shot Orchestration

后续独立implementation slice MAY实现显式one-shot two-stage coordinator。API名称由该slice
决定，但behavior必须等价于：

```text
exact current render + selected QaPolicy + selected Domain profile
  -> validate preselected Universal profile minimum
  -> require QaPolicy coverage of every applicable Gate 1 review layer
  -> run Gate 1 required checks
  -> STOP on FAIL / NOT_EVALUATED / stale
  -> run exactly one selected Gate 2 profile
  -> STOP on FAIL / NOT_EVALUATED / missing profile
  -> return eligible_for_final_acceptance
```

第一版coordinator必须：

- 只由显式caller调用，不watch filesystem、Manifest或render completion event；
- missing/invalid Universal profile或incomplete `QaPolicy` coverage时在任何Gate 2 effect前fail closed；
- 不默认选择Ecommerce、Drama、AI Comic或任意fallback profile；
- 没有applicable selected Domain profile时fail closed；
- 继续通过`ProductionStateCommitter`持久化review intent/evidence/receipt；
- exact replay不重复analyzer或Manifest effects；unknown outcome不blind retry；
- 不自动repair、rerender、Provider submit/retry、candidate activation或Final Acceptance。

## Ownership

| Concern | Canonical owner |
| --- | --- |
| Universal hard correctness | Existing Registry、media、timeline、composition、render、audio/caption owners |
| Shared review evidence/adjudication | Existing P6 `review.py` contracts |
| Domain authoring truth/rubric | Selected accepted Domain workflow/spec |
| Durable review/repair/final-acceptance state | `ProductionStateCommitter` |
| Timing/order/frame/sample truth | `ResolvedTimeline` |
| Market outcome | Future separately authorized analytics/experiment owner |

## Compatibility And Migration

本architecture spec不改变`QaLayer`、`QaPolicy`、Review/Repair/Final Acceptance schema、Manifest、
Registry、artifact layout或historical hashes。Current boundary implementation不需要data/runtime
migration。Future typed Domain seam或coordinator若需要schema、active-review indexing或public API
变化，必须由独立spec/plan定义compatibility、migration、rollback与focused tests。

## Acceptance Criteria

- 文档只描述两个top-level post-media gates；
- Domain names只作为Gate 2 profiles，不成为额外lifecycle owner；
- Final Acceptance明确为rollup而不是第三个evaluator gate；
- preflight gates与post-media gates明确分离；
- current automatic-trigger claims与真实callers一致；
- future one-shot coordinator在missing profile、missing evidence、`FAIL`、`NOT_EVALUATED`、stale
  或unknown outcome时fail closed；
- 无background automation、automatic repair/activation/Final Acceptance授权；
- current code/tests仍是implementation truth，baseline/roadmap仍是runtime/status owners。
