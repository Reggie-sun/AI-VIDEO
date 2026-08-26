# AI-VIDEO Provider-Minimal Execution And Media Evidence Boundary Specification

## Status

Offline implementation complete。Exact implementation range
`0f73c53..9e999d1` 已通过 focused executable verification、native `reviewer_xhigh` 与 fresh
exact-range Harness；一个只返回 `job_id + status + re-queryable output_url` 的offline fake Provider
已沿 canonical lifecycle 到达 fetched/probed `CANDIDATE`，且没有自动activation。

本文不是 Provider live proof、quality PASS、Gate 2、P6、Final Acceptance、release或publication
evidence。Canonical contract matrix、runtime baseline与roadmap已同步该offline proof；
`.agent/harness/policy.yaml`无需变化，因为全部implementation paths已由现有Provider/neutral-requirement
categories映射到focused suites与Architecture Gate，exact-range receipt没有unmapped或fallback path。

本Spec扩展而不替代以下现有 owner：

- `2026-08-21-ai-video-provider-neutral-generation-requirement.md` 独占 pre-submit neutral
  requirement、Router 与 compiler boundary；
- `2026-08-25-ai-video-quality-gate-architecture-separation.md` 独占 Gate 1、Gate 2 与 Final
  Acceptance taxonomy；
- Paid Provider Gate 独占 budget、egress、secret、durable intent、permit 与 unknown-outcome
  safety；
- `ProductionStateCommitter` 继续独占 mutable lifecycle、activation、recovery 与 Final
  Acceptance write。

## Problem Boundary

AI-VIDEO 当前 canonical post-fetch path 已经主要依赖 exact output bytes 与 AI-VIDEO-owned
lineage：fetch receipt计算artifact SHA，probe重新测量container、codec、geometry、fps、duration、
frame count与audio stream，Review/Gate再绑定current Project、Registry、graph、timeline、render、
policy与evaluator evidence。

但cloud adapter仍有两个会妨碍future Provider接入的边界问题：

1. 一些adapter在status/fetch前要求Provider回显`model`、`resolution`、`duration`或`ratio`。
   这些字段缺失时，最终媒体甚至无法进入AI-VIDEO-owned probe。
2. Generic lifecycle把成功输出命名为`provider_file_id`，但Seedance与MiniMax H3实际使用synthetic
   handle并重新查询signed URL。该schema没有明确表达stable file ID、re-queryable URL与one-shot
   ephemeral URL的恢复差异。

另外，`VideoProvenanceReceipt.model_id`与`profile_sha256`来自AI-VIDEO selected/resolved request。
它们能证明“AI-VIDEO请求了什么”，不能单独证明“cloud Provider内部实际运行了什么”。如果把这类
字段解释为verified actual execution，就会把requested lineage误写成Provider-observed truth。

## Architecture Decision

采用以下原则：

> Provider负责生成与交付输出；AI-VIDEO负责绑定请求、保存lineage、验证exact bytes，并据此完成
> acceptance。

Canonical Gate主要验证：

```text
observable final media outcome
  + AI-VIDEO-owned request / Shot / plan / policy / attempt lineage
  + required evaluator or human evidence
```

Canonical Gate不得普遍依赖：

```text
Provider-owned hidden seed / scheduler / model revision / workflow / runtime internals
```

Provider-native metadata可以作为adapter-specific observation或capability-specific policy evidence，
但不得自动升级为所有Providers的Gate 1、Gate 2、P6或Final Acceptance prerequisite。

## Goals

- 允许一个只提供 `job_id + status + output_url` 的 cloud Provider进入canonical fetch/probe lifecycle，
  并让其evidence可被现有或后续accepted Gate owner消费；
- 明确AI-VIDEO-owned、Provider-owned、AI-measured与evaluator-owned evidence的不同证明力；
- 让unavailable、unknown与not-applicable Provider internals保持truthful，不伪造default；
- 让output bytes落地后只由AI-VIDEO计算exact SHA、probe、decode与measurement；
- 保持Gate 1、selected Gate 2、P6 adjudication与Final Acceptance rollup依赖current media和
  canonical lineage；
- 保留Local T8/ComfyUI对workflow、model bytes、scheduler、sampler与node topology的严格seal，
  但不把local-known facts提升成cloud Provider universal contract；
- 保持unknown outcome、no blind retry、no fallback、budget、egress、permit、activation与recovery
  safety不变。

## Non-Goals

- 不新增Provider ranking、automatic selection、fallback、retry、candidate iteration或repair；
- 不让Provider adapter、analyzer、Skill或Gate直接写Manifest或激活candidate；
- 不从最终媒体反推hidden seed、scheduler、model revision、workflow或Provider hardware；
- 不把Provider status success解释为media quality PASS；
- 不让hash/probe代替continuity、semantic、product fidelity、dialogue或human visual verdict；
- 不改变`ResolvedTimeline`、HyperFrames、Asset Registry、Dependency Graph或P4 audio/caption owner；
- 不在本Spec授权Provider live call、credential lookup、paid submit、media generation或benchmark；
- 不在MVP中持久化raw signed URL、credential-bearing URL或其他secret-like locator；
- 不声明Veo或任何尚未实现的adapter已经通过runtime、media或quality acceptance。
- 不在本slice实现或验收Gate 2、two-stage coordinator、P6 closure或Final Acceptance E2E；这些继续
  由Quality Gate architecture及其独立accepted implementation slice拥有。

## Evidence Authority Model

每个字段必须按其真实来源分类。字段名称不得暗示超出该来源的证明力。

| Evidence class | Owner | Can prove | Cannot prove |
| --- | --- | --- | --- |
| `AI_VIDEO_INTENT` | Planning / Router / compiler / committer | exact requested Shot、assets、policy、selected Provider/model/profile与attempt | Provider内部实际执行配置 |
| `PROVIDER_OBSERVATION` | selected adapter封装的Provider response | job/status/output locator与Provider明确回显的native claim | bytes质量、claim真实性、hidden internals |
| `AI_VIDEO_MEASUREMENT` | fetch/probe/media validators | exact fetched bytes、SHA、container、codec、geometry、fps、duration、frames、streams | semantic correctness或Provider hidden execution |
| `EVALUATOR_EVIDENCE` | accepted evaluator或human | requirement-level continuity、semantic、domain或visual findings | Manifest mutation、activation或Final Acceptance |
| `DURABLE_ACCEPTANCE` | P6 + `ProductionStateCommitter` | current review rollup、candidate lifecycle与Final Acceptance state | 未运行的Provider、媒体或human验证 |

### Availability Semantics

当capability-specific policy确实需要记录Provider-native事实时，observation必须使用explicit
availability。没有accepted consumer时不得仅为“完整 provenance”新增第二套durable claim subsystem：

| State | Meaning | Gate behavior |
| --- | --- | --- |
| `AVAILABLE` | Provider明确返回且adapter完成typed validation | 只能满足显式选择的capability-specific requirement |
| `UNAVAILABLE` | Provider/API合同不暴露该字段 | universal Gate不得因此失败；显式policy可返回`NOT_EVALUATED` |
| `UNKNOWN` | 应答缺失、冲突、无法可信绑定或outcome unknown | fail closed于相关lifecycle/policy，不得猜测 |
| `NOT_APPLICABLE` | 该Provider/lane不存在该概念 | 不进入该requirement coverage |

`UNAVAILABLE`不能被写成随机seed、默认scheduler、configured model revision或workflow hash。
`UNKNOWN`不能被`AI_VIDEO_INTENT`字段替代。

## End-To-End Contract

```text
Canonical Shot / Plan / Policy / Assets
        |
        v
ProviderNeutralVideoRequirement
        |
        v
Router exact Provider/profile/capability selection
        |
        v
Compiled + Resolved AI-VIDEO request lineage
        |
        v
Provider submit -> job_id
        |
        v
Provider status -> state + opaque output handle
        |
        v
Provider fetch -> bytes into committer-owned sink
        |
        v
AI-VIDEO SHA + probe + decode + measured metadata
        |
        v
Shot continuity / commercial evidence / candidate activation
        |
        `-> existing or separately accepted quality-gate owners
            may consume exact current media/lineage evidence
```

任何Provider response字段都不得绕过fetch、probe、Review、Gate或committer直接推进durable state。

## AI-VIDEO-Owned Lineage Contract

以下identity由AI-VIDEO生成、seal或从canonical owner读取：

- source request、Planning request、plan与provider-neutral requirement hashes；
- target Shot ID、revision、content hash与Scene/Character identities；
- selected Asset Registry revision、asset IDs、input SHA与semantic role bindings；
- Router decision、selected capability fingerprint与provider-bound request hash；
- compiler identity、compiled request hash与resolved generation hash；
- generation ID、attempt ID、durable submit intent、authorization与permit binding；
- dependency graph revision、timeline fingerprint、render state与output identity；
- selected QA policy、Universal profile、Domain profile与Review request identities。

`requested_provider_name`、`requested_model_id`与`selected_profile_sha256`属于这一层。它们必须被
描述为selected/requested identity，而不是Provider-observed actual execution。

## Minimal Provider Adapter Contract

### Submit

最小成功输出只要求：

| Field | Requirement |
| --- | --- |
| `external_effect_id` | non-empty opaque job/task identity；绑定exact resolved request与one-use submit receipt |
| `submitted_at` | AI-VIDEO observed timestamp |

Provider可返回其他native metadata，但canonical submit success不得要求seed、scheduler、workflow、
model revision或output profile回显，除非selected capability policy在submit前明确声明其为required。

### Status

最小observation只要求：

| Field | Requirement |
| --- | --- |
| effect binding | response必须属于同一`external_effect_id`；无法绑定时fail closed |
| state | typed `QUEUED | RUNNING | SUCCEEDED | FAILED`；unknown state不得映射为success |
| output handle | `SUCCEEDED`时提供可恢复的opaque handle strategy |

Status可以带progress或native metadata，但这些字段不影响media acceptance，除非preselected policy
明确要求。

### Opaque Output Handle Semantics

MVP保留serialized `provider_file_id`与全部historical fingerprints不变，并把该字段的durable语义明确为
opaque output-handle identity，而不是“Provider必然拥有一个file object”。不新增
`ProviderOutputHandle` wrapper或Manifest migration。

实现必须支持以下两种sealed adapter recovery strategy：

| Strategy | Contract |
| --- | --- |
| `DURABLE_FILE_ID` | Provider返回stable file ID，fetch可通过该ID重新取得bytes |
| `REQUERY_BY_EFFECT_ID` | adapter从exact `external_effect_id`确定性构造handle，并用job ID重新查询current output URL；Seedance/H3现有task-derived handle属于此类 |

`REQUERY_BY_EFFECT_ID`的identity是exact effect ID及其deterministic handle；signed URL可以合法轮换，
不得比较或持久化URL SHA来决定result identity。`DURABLE_FILE_ID`则必须在status/fetch之间保持同一
stable file ID。

Raw signed URL不得进入Manifest、normal logs、receipts、errors或artifact metadata。

若Provider只在一次status response返回不可重取的ephemeral URL，selected adapter的pure
resolve/compile/preflight必须基于sealed capability/profile在`VideoGenerationService.start()`之前返回
typed `OUTPUT_LOCATOR_NOT_RECOVERABLE`。该denial不得创建attempt、Paid Provider intent、permit或
Provider effect。Recovery guarantee必须进入selected profile/capability fingerprint及
provider-bound request identity；若current hashes无法表达，implementation必须先提出独立
compatibility/migration decision，不能在`submit()`后才发现unsupported。

支持secret-safe durable locator或combined observe-and-fetch transaction需要独立spec，不得靠
process-local cache或未记录URL绕过recovery contract。

### Fetch

Adapter只负责：

- 用same submit/observation/output-handle lineage取得bytes；
- enforce URL scheme/origin、content-type与download byte ceiling等transport safety；
- 将bytes写入committer提供的sink；
- 在stream过程中计算size与SHA，并返回`VideoFetchReceipt`。

Provider声明的SHA、duration、geometry或codec不能替代AI-VIDEO对落地bytes的重新计算与probe。

## Post-Fetch Media Proof Contract

AI-VIDEO必须对held exact artifact执行：

1. 重新读取并计算artifact SHA；
2. 与fetch receipt的size/SHA identity比较；
3. decode/probe container、video stream、codec、geometry、fps、duration、frame count与audio streams；
4. 与exact resolved output contract比较；
5. 产生content-addressed `VideoProbeReceipt`与measured metadata；
6. 按applicability运行continuity、commercial或其他Shot-level evaluator；
7. 只有required findings全部PASS后才允许现有candidate activation owner继续。

Provider status、URL可访问、HTTP 200、content-type header或submit success都不能代替上述proof。

## Gate And Acceptance Contract

### Gate 1

Universal Gate只消费AI-VIDEO current context、hard-check outcomes与accepted shared Review evidence：

- asset provenance和exact registered bytes；
- media decode与measured output contract；
- timeline/render/output binding；
- applicable audio/caption、layout与continuity evidence；
- selected policy要求的fresh technical receipts。

Gate 1不得要求Provider seed、scheduler、workflow hash、hidden model revision或native response profile。

### Gate 2

Selected Domain Gate只消费exact final-media identity、AI-VIDEO upstream lineage、sealed Domain profile
及requirement-level evaluator/human evidence。任何required finding为`FAIL`或`NOT_EVALUATED`都必须
fail closed。Aggregate score、Provider status或native metadata不得抵消。

### P6 And Final Acceptance

P6继续是Review evidence/adjudication owner。`ProductionStateCommitter.record_final_acceptance()`
继续只roll up current graph、render、output SHA、timeline、policy与fresh PASS receipts；它不重新
查询Provider，也不把Provider metadata升级为acceptance truth。

## Facts Final Media Cannot Prove

以下事实不能仅由最终媒体与AI-VIDEO lineage证明：

- Provider内部实际seed、scheduler、sampler、workflow graph/hash；
- hidden model revision、weight hash、runtime patch或Provider-side fallback；
- Provider使用的hardware、region或内部processing chain；
- Provider是否完全诚实地执行requested model，而不是只回显requested value；
- billing settlement、account entitlement、license/terms compliance；
- semantic intent、identity continuity、product fidelity、dialogue correctness或human watchability。

处理规则：

- hidden execution facts默认`UNAVAILABLE`或`UNKNOWN`，不进入universal acceptance；
- billing、authorization、egress与license由各自existing policy/lifecycle owner验证；
- semantic与visual facts由accepted evaluator/human evidence验证，缺失时`NOT_EVALUATED`；
- 如果某个regulated capability确实要求actual model revision或region proof，该requirement必须由
  preselected capability/acceptance policy显式声明，并只影响该capability，不得污染所有Providers。

## Current Source Audit

| Surface | Current boundary | Assessment | Required target change |
| --- | --- | --- | --- |
| `video_requirement.py` | recursively forbids Provider/model/workflow/payload fields | correct | keep unchanged |
| `shot_router.py` | introduces exact Provider/profile only after verified neutral requirement | correct | keep selection ownership |
| `video_compiler.py` | deterministic native expression of approved requirement | correct | keep unsupported/no-fallback behavior |
| `video.py` | submit/status/fetch protocol is small, but SUCCESS requires `provider_file_id` | mostly correct | document existing serialized field as opaque output handle |
| `video_generation.py` | durable status, fetch, validate, candidate and activation phases remain separate | correct | preserve replay/recovery ordering |
| `video_artifact.py` | recomputes SHA/probe and rejects Provider-claimed output facts | correct | keep as media proof owner |
| `quality_gate_coordinator.py` | Gate 1 contract has no Provider metadata fields | correct contract | ensure concrete runners remain media/lineage based |
| `ecommerce_media_acceptance.py` / `review.py` | typed requirement evidence; missing authority becomes `NOT_EVALUATED` | correct | preserve evaluator boundary |
| `_state_commit_review.py` | Final Acceptance binds current render/timeline/policy/reviews | correct | no Provider query or metadata dependency |
| `seedance.py` | query requires echoed `model` before status/fetch | coupled | make echo optional or explicitly capability-policy scoped |
| `minimax_h3.py` | query requires echoed model/resolution/duration/ratio | coupled | remove output-profile echo as universal prerequisite; trust local probe for outcome |
| `minimax_hailuo.py` | task/status/file ID then local download SHA | reference pattern | preserve minimal native response dependency |
| `comfy_t8_video.py` | local workflow/model/node/sampler/scheduler are AI-verifiable | correctly local-specific | keep out of canonical cloud acceptance |

## Old-Path Retirement

Implementation of this Spec must retire or constrain the following paths:

1. Seedance status/fetch cannot fail solely because optional response `model` is absent；mismatch may remain
   adapter-specific evidence only when the official selected API contract guarantees the field and policy
   explicitly requires it。
2. MiniMax H3 status/fetch cannot use echoed resolution/duration/ratio as substitute or prerequisite for
   local probe；task ID/status/output locator remain required。
3. `VideoProvenanceReceipt.model_id` must not be documented or exposed as verified actual execution。MVP将其
   明确解释为requested/selected identity；只有accepted capability-specific consumer存在时，才由独立
   contract定义Provider-observed claim carrier。
4. `provider_file_id` must not imply every Provider owns a durable file object。MVP保留serialized field，
   并把其语义固定为opaque output handle。
5. Process-local cached output URL、blind re-query fallback、raw signed URL persistence、伪造的
   Provider-native claim与没有exact effect lineage的synthetic locator是forbidden alternate recovery
   paths。Exact effect ID派生的deterministic handle保持允许。

## Unchanged Contracts

- `ProviderNeutralVideoRequirement` remains the single neutral generation requirement；
- Shot Router remains the sole Provider/profile/capability selector and preserves no-fallback behavior；
- Provider Registry remains exact lookup, not ranking or fallback owner；
- Paid Provider preview、budget、egress、secret、durable intent、permit and unknown-outcome handling remain unchanged；
- `ProductionStateCommitter` remains the sole v2 writer、activation and recovery owner；
- Artifact Registry、Dependency Graph、`ResolvedTimeline`、HyperFrames and P4 audio/caption ownership remain unchanged；
- Gate 1 / Gate 2 taxonomy、P6 adjudication and Final Acceptance rollup ownership remain unchanged；
- Legacy `0.1.x` CLI、Manifest、artifact layout and local-first default remain unchanged。

## Compatibility And Migration

- Historical `VideoGenerationRequest`、resolved request、submit/status/fetch/provenance receipts and
  activation hashes must reopen byte-identically。
- MVP不修改serialized `provider_file_id`、observation/fetch/provenance schema或historical hashes；只收窄
  adapter response dependency并固定其opaque semantics。
- 只有future evidence证明existing field无法表达accepted behavior时，才由独立spec定义additive
  schema/version branches；implementation不得在本slice静默迁移historical serialized fields。
- Adapter migration is incremental。Seedance and MiniMax H3 can adopt minimal status semantics independently；
  each change must preserve exact current request/observation/fetch/provenance hash and reopen tests。
- No Manifest/layout migration is authorized unless implementation evidence proves additive request/receipt
  fields cannot travel through existing envelopes。Any required migration needs separate approval。
- A Provider whose locator is not replay-safe remains typed unsupported；do not weaken recovery merely to claim
  compatibility。

## Acceptance Criteria

1. A fake cloud Provider returning only `job_id + status + re-queryable output_url` completes the offline
   submit -> status -> fetch -> local SHA/probe -> fetched/probed candidate path with zero network calls。
2. The same fake Provider returns no model、seed、scheduler、revision、workflow、resolution、duration or
   ratio metadata；absence does not block fetch、local probe or candidate preparation。
3. A task ID change、unknown status、missing successful output handle or mismatched fetch lineage fails closed
   before candidate preparation。For `DURABLE_FILE_ID`，changed file ID also fails closed；for
   `REQUERY_BY_EFFECT_ID`，signed URL rotation does not change output identity。
4. Non-requeryable one-shot output URL capability returns typed
   `OUTPUT_LOCATOR_NOT_RECOVERABLE` before `VideoGenerationService.start()`，with zero Manifest、permit、
   network or Provider side effects。Its sealed recovery guarantee contributes to the selected profile/capability
   and provider-bound identities。
5. Mutated、truncated or substituted output bytes fail exact size/SHA/probe binding even when Provider status is
   SUCCESS。
6. Provider-declared duration、geometry、codec or SHA never overrides local measured metadata。
7. Existing Gate schemas and adjudicators continue returning `NOT_EVALUATED` for missing required evaluator or
   human evidence；Provider success cannot override it。本slice不实现Gate 2/P6/Final Acceptance closure。
8. `VideoProvenanceReceipt.model_id` tests and canonical docs prove requested/selected semantics。若没有
   accepted capability-specific consumer，不新增Provider-observed claim fields；任何unavailable/unknown
   native claim都不合成。
9. Local T8/ComfyUI profile seals continue validating exact workflow、components、scheduler、sampler and node
   topology without adding those fields to neutral requirement or universal Gate schemas。
10. Seedance and MiniMax H3 focused tests prove minimal status responses can reach fetch and local probe；
    explicit task/model mismatch tests remain fail closed where the selected adapter policy requires them。
11. All historical hash/reopen fixtures remain byte-identical。
12. Architecture tests reject Provider-native fields in neutral requirement、Gate 1 context、accepted Gate 2
    target and Final Acceptance receipt。对于尚未committed/accepted的Gate 2 implementation，只验证owner
    boundary，不把它纳入本slice completion。
13. No new writer、fallback、retry、automatic activation、automatic Final Acceptance or raw URL persistence
    path exists。
14. Exact staged snapshot or exact commit range produces a fresh passing Harness receipt with policy、scope、
    artifact hashes、freshness and snapshot validity verified。

## Verification Contract

Implementation verification must include at least：

| Layer | Required coverage |
| --- | --- |
| Pure model | opaque-handle semantics、selected profile/capability recovery guarantee、requested identity、forbidden Gate fields |
| Adapter unit | minimal response、missing optional metadata、task mismatch、unknown status、URL recovery strategy |
| Fetch/artifact | exact bytes/SHA、probe、decode、output contract、tamper/truncation/substitution |
| Lifecycle integration | durable submit/status/fetch/restart/replay、unknown outcome、candidate/activation ownership |
| Gate boundary | current Gate schemas/adjudicators accept only media/lineage/evaluator evidence and no Provider-native prerequisite |
| Compatibility | historical request/receipt/provenance hashes and loader reopen |
| Architecture | no alternate writer、raw URL persistence、Provider field leakage or fallback |

Focused suites should cover：

```text
tests/test_production_video.py
tests/test_production_generated_video_e2e.py
tests/test_production_provider_neutral_adapters.py
tests/test_production_seedance.py
tests/test_production_minimax_h3.py
tests/test_production_minimax_hailuo.py
tests/test_production_quality_gate_coordinator.py
tests/test_production_review.py
tests/test_production_project.py
```

Final proof must use `.agent/harness/policy.yaml` against an exact non-empty staged snapshot or exact commit
range。Offline tests cannot prove Provider account、API grammar、network、billing、media quality or human
acceptance；those remain separately authorized evidence lanes。

## Rollback

- Documentation-only rollback reverts this Spec and does not change runtime truth。
- Runtime implementation must be reversible adapter-by-adapter while preserving historical schema/hash reopen。
- If a new Provider attempt has begun durably，rollback must use existing explicit recovery；不得 downgrade
  receipt、delete complete orphan evidence or blind retry。
- Rollback不得重新引入 Provider metadata as universal Gate prerequisite、raw URL persistence、second writer、
  fallback or Provider-claimed media measurements。

## Definition Of Done

本Spec只有在以下条件全部满足后才可从 `Proposed` 升级：

1. Minimal cloud Provider offline fetch/probe E2E满足全部Acceptance Criteria；
2. Seedance、MiniMax H3、MiniMax Hailuo与Local T8边界有focused executable evidence；
3. Current Gate schemas与adjudicators没有Provider-native prerequisite；Gate 2/P6/Final Acceptance closure
   仍由Quality Gate owner的独立accepted implementation slice验收；
4. historical compatibility与old-path retirement均由tests保护；
5. fresh exact-snapshot Harness receipt通过并验证；
6. runtime baseline与roadmap只在implementation evidence成立后同步，且不把offline PASS写成live或
   quality acceptance。
