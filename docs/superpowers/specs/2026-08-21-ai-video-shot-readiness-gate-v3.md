# AI-VIDEO Shot Readiness Gate Specification

## Status

Proposed v3 contract repair；documentation-only。本文件对齐当前已实现的
`video-planner/3`、plan 内嵌 `ProviderNeutralVideoRequirement` 与
`VerifiedGenerationRequirementProjection` truth。本 slice 不实现 runtime、不运行
Provider、不生成或分析媒体，也不构成 generation、activation、Review、quality 或
Final Acceptance evidence。

本 repository 只有这一份 canonical `ShotReadinessGate` Spec。本次修改是在该文件中
原地修订 contract，不存在另一份“旧 QA Gate Spec”、并行 gate spec 或基于实验失败新建
Spec 的路径；“QA Gate”仅是对本 pre-submit structural gate 的口语称呼。

配套 implementation plan：
`docs/superpowers/plans/2026-08-21-ai-video-shot-readiness-gate-v3.md`。

## Problem Boundary

当前 `require_current_video_plan()` 已经同时承担两类责任：

1. 验证 current `VideoPlanningRequest`、`VideoGenerationPlan`、内嵌 requirement 与
   `VerifiedGenerationRequirementProjection` 的 exact freshness lineage；
2. 决定 plan eligibility、required-asset readiness 与 downstream STOP。

前者属于 Planning freshness boundary，后者应收敛为一个明确的 pre-submit readiness
owner。本 canonical Spec 的先前内容仍固定 `video-planner/2` 并把 plan 作为
`plan_hint` 交给下游；这与 current v3 code 和 tests 冲突。本次原地修订的目标不是新增
另一份 Spec、另一套 Planner 或 post-fetch QA，而是保留 Planning freshness
verifier/issuer，并把唯一 `READY/BLOCKED` decision 移交 `ShotReadinessGate`。

## Goal

定义一个 pure、deterministic、provider-neutral 的 pre-submit
`ShotReadinessGate`：

- 只消费 current planning inputs及 Planning-owned verified freshness outcome，不独立
  推导 generation mode、continuity、motion、required roles、capabilities 或 requirement；
- exact 绑定 v3 request、plan、plan 内嵌 requirement 与
  `VerifiedGenerationRequirementProjection`；
- 对 plan eligibility 与 plan-declared required assets 产生完整 typed diagnostics；
- 在 Router、compiler、Provider、materializer、composition 或 render 之前执行 STOP；
- `READY` 仅返回 existing downstream 所需的 verified requirement projection，不返回
  plan hint，也不改变任何 Production lifecycle owner。

Gate 只回答“这个 current v3 plan 是否具备进入既有下游 gates 的结构条件”。它不检测
identity drift、motion naturalness、continuity quality、blur、sharpness、分辨率偏好、
subjective picture quality 或 Final Acceptance。

## Scope

### In Scope

- one-Shot、new-attempt、pre-submit structural readiness；
- current v3 request/plan/requirement/projection exact binding与freshness；
- plan outcome、unresolved human review与plan-declared required assets；
- frozen strict models、deterministic hashes、discriminated diagnostics与typed STOP；
- `require_current_video_plan()` compatibility façade migration；
- historical v2 reopen compatibility与new-attempt rejection boundary；
- cycle-safe single required-asset readiness owner；
- import/no-IO/no-writer boundaries、focused tests、Harness routing与rollback。

### Out of Scope

- 在 Gate 内重新实现、直接运行或复制 Planner semantic derivation；Planning freshness
  verifier为验证unique current derivation而复用current `VideoPlanner`的既有行为保持不变；
- Router capability matching、Provider/profile selection、compiler expression或fallback；
- submit、poll、fetch、retry、media validation、candidate activation或repair；
- Manifest、Registry、Dependency Graph、committer、recovery、timeline或renderer changes；
- P6 Review/Repair、human Pilot Reality Gate、Final Acceptance或post-fetch
  `VideoQualityGate`；
- `seed=None` compiler/ComfyUI fix、Local H3 rerun、Candidate 2/3或任何 live experiment；
- new dependency、CLI、schema、artifact layout、durable readiness receipt或第二 writer。

## Runtime Truth to Preserve

- `VideoPlanner.CONTRACT_VERSION == "video-planner/3"`。
- New v3 plan必须内嵌一个 `ProviderNeutralVideoRequirement`，并禁止 serialized
  `generation_mode`、`continuity_mode`、`motion_requirement`、
  `required_asset_roles` 与 `capability_requirements` duplicate truth。
- Current Planning boundary验证 request seal、plan seal、unique current derivation、
  plan/source/Shot lineage、embedded requirement evidence，并返回
  `VerifiedGenerationRequirementProjection`。
- `prepare_shot_for_existing_production()` currently hands off
  `current_shot` 与 `generation_requirement`；`plan_hint` 已退休且不得恢复。
- Router只消费 verified requirement projection，独占 exact Provider/profile/capability
  selection；compiler只做 deterministic native expression。
- Historical `video-planner/2` request/plan仍可按原 bytes parse/reopen，但不能签发 v3
  verified projection，也不能创建 new attempt。

## Ownership and Invariants

| Concern | Sole owner | Gate rule |
| --- | --- | --- |
| Character / Scene / Shot truth | `ProductionProject` creative artifacts | read projected identities only |
| Plan and embedded requirement derivation | `VideoPlanner` | do not reconstruct or reinterpret |
| Current plan/requirement freshness projection | Planning pure verifier | emit verified projection or typed verification failure；no readiness verdict |
| Required-asset role semantics | one cycle-safe pure Planning helper | Planner and Gate reuse the same implementation |
| Pre-submit readiness and STOP | `ShotReadinessGate` | sole `READY/BLOCKED` decision owner |
| Provider/profile/capability selection | Shot Router | unchanged；no fallback |
| Submit/fetch/activation/recovery | existing Provider lifecycle and `ProductionStateCommitter` | zero calls on BLOCKED |
| Timing/render | `ResolvedTimeline` and HyperFrames | unchanged |
| Semantic/perceptual QA and acceptance | P6 Review/Repair and human Pilot Reality Gate | forbidden Gate scope |

The Gate and shared helpers must remain pure：no filesystem、network、environment、secret、
clock、randomness、Provider、Registry lookup、Manifest write或media access。Production modules
must not reverse-import readiness models to decide lifecycle state。

## Planning Freshness Seam

Implementation extracts the existing structural verifier from
`require_current_video_plan()` into one Planning-owned pure function. Logical result：

```text
CurrentPlanProjectionVerification
  = VerifiedGenerationRequirementProjection
  | CurrentPlanProjectionFailure
```

`CurrentPlanProjectionFailure`是Planning-internal、frozen、strict typed diagnostic，包含
ordered `reason_codes`与ordered `field_paths`。Its reason vocabulary is fixed to：

```text
LEGACY_CONTRACT
REQUEST_SEAL_INVALID
PLAN_SEAL_INVALID
PLAN_NOT_UNIQUE_CURRENT_DERIVATION
PLAN_ID_INVALID
SOURCE_REQUEST_STALE
TARGET_SHOT_STALE
EMBEDDED_REQUIREMENT_MISSING
EMBEDDED_REQUIREMENT_STALE
VERIFIED_PROJECTION_INVALID
```

The verifier collects every independently evaluable failure rather than returning free-form
first-error text；dependent checks that cannot be evaluated remain explicitly false in the Gate's
binding payload。The failure object is not exported as a production handoff and cannot authorize
Router entry。

This verifier preserves the current checks：

1. request and plan are both `video-planner/3`；
2. request semantic seal is valid；
3. plan semantic seal and deterministic `plan_id` are valid；
4. the plan is the unique current `VideoPlanner` derivation for the request；
5. source request and target Shot id/revision/content hash match exactly；
6. the embedded requirement exists and its seal、source request、intent evidence、typed
   generation intent、Scene、Character、asset evidence与Review evidence are current；
7. the resulting projection seal and request/plan/requirement/Shot lineage are exact。

The verifier does not decide `READY`、plan eligibility或required-asset readiness。The Gate
does not implement a second derivation algorithm；it consumes this Planning-owned result and
turns verification failure into binding diagnostics。Only `READY` may expose the verified
projection to downstream code。

## Request Contract

```python
class ShotReadinessRequest(StrictModel):
    request_id: str  # diagnostic only
    current_request: VideoPlanningRequest
    plan: VideoGenerationPlan
    contract_version: Literal["shot-readiness-gate/1"]
    request_content_hash: str
```

All models are frozen、strict、`extra="forbid"`。`create()` computes
`request_content_hash` from exactly：

```python
{
    "contract_version": "shot-readiness-gate/1",
    "current_request_content_hash": current_request.request_content_hash,
    "plan_hash": plan.plan_hash,
    "embedded_requirement_hash": (
        plan.generation_requirement.requirement_hash
        if plan.generation_requirement is not None
        else None
    ),
}
```

Outer `request_id` 与 nested `VideoPlanningRequest.request_id`不参与 hash。Evaluation必须
重算 outer seal，即使对象由 `model_copy()` 或低层构造绕过 validation。

`VerifiedGenerationRequirementProjection`不是 caller-supplied hint。它只能由上述 Planning
freshness verifier产生，并在 Gate `READY` result中返回；这样不存在 plan 与 projection
分别替换或 independently trusted 的双输入路径。

## Result and Diagnostics Contract

```text
ShotReadinessResult
  status: READY | BLOCKED
  checks: exactly three ordered discriminated outcomes
  verified_generation_requirement: VerifiedGenerationRequirementProjection | None
  result_hash: SHA-256
```

Checks始终按下列顺序出现：

1. `request_plan_binding`；
2. `plan_eligibility`；
3. `required_asset_readiness`。

Each check id has its own frozen payload and `Literal`-bound outcome model。Union使用
`Field(discriminator="check_id")`；wrong check/payload组合必须 validation fail。每个
outcome包含 ordered typed reason codes，不依赖自由文本匹配。Required codes：

| Code | Meaning |
| --- | --- |
| `READINESS_REQUEST_SEAL_INVALID` | outer readiness seal无效 |
| `LEGACY_PLANNER_REOPEN_ONLY` | v2只允许historical reopen，不能进入new attempt |
| `CURRENT_PLAN_PROJECTION_INVALID` | Planning freshness verifier拒绝request/plan/requirement lineage |
| `VERIFIED_PROJECTION_BINDING_INVALID` | emitted projection seal或request/plan/requirement/Shot binding不一致 |
| `PLAN_BLOCKED` | Planner outcome为`BLOCKED` |
| `HUMAN_REVIEW_UNRESOLVED` | `REQUIRES_HUMAN_REVIEW`仍存在 |
| `REQUIRED_ASSET_MISSING` | 一个或多个plan-declared roles不满足current exact binding |

Binding payload必须显式报告 outer seal、request seal、plan seal、current v3 contract、
unique derivation、source request、target Shot、embedded requirement和verified projection
binding status。Eligibility payload原样报告 `plan.outcome`、warnings和unresolved review，
不重解释 Planner reasons/confidence。Asset payload报告 ordered required、ready与missing
roles，只检查 `plan.required_asset_roles` compatibility property投影的角色。

`verified_generation_requirement`仅在 `status == READY` 时存在，并且必须同时等于
Planning verifier output、绑定 `plan.plan_hash`、包含与
`plan.generation_requirement`相同的 requirement、绑定 current request hash与exact Shot
identity。`BLOCKED` result中该字段必须为 `None`，防止 diagnostic result成为下游 bypass。

`result_hash`覆盖除自身外的完整 result。Result不保存 diagnostic request id、Provider
identity、receipt path、lifecycle phase或quality verdict。

## Deterministic Evaluation

`ShotReadinessGate.evaluate()` always emits all three checks and does not short-circuit
diagnostics。Untrusted plan fields may be reported for diagnostics, but cannot yield a top-level
verified projection unless binding check passes。

### 1. Request/Plan/Requirement/Projection Binding

- recompute outer readiness seal；
- invoke the sole Planning freshness verifier；
- reject v2 with `LEGACY_PLANNER_REOPEN_ONLY` and do not auto-convert it；
- when verification succeeds, independently validate projection seal and exact equality among
  request hash、plan hash、embedded requirement hash、projection requirement、target Shot
  id/revision/content hash；
- never call Router、compiler、Provider或Production lifecycle。

### 2. Plan Eligibility

```text
plan.outcome == BLOCKED                 -> BLOCKED / PLAN_BLOCKED
REQUIRES_HUMAN_REVIEW remains present  -> BLOCKED / HUMAN_REVIEW_UNRESOLVED
otherwise                              -> PASS
```

Resolved audit warnings remain visible but do not create a second policy。

### 3. Required-Asset Readiness

Gate只检查 plan-declared roles，并复用 Planner同一个cycle-safe pure helper：

- Character reference owner集合exact匹配target Shot Character集合；
- Scene reference owner exact匹配target Scene；
- previous terminal exact匹配previous Shot identity与declared terminal asset id；
- approved keyframe/reusable plate exact匹配target Shot final-visual binding与current Review
  projection；
- selected existing video/audio reference exact匹配typed media selection；
- last-frame role遵循current Planner semantics。

Wrong owner、wrong content binding、ambiguous selection、missing role或missing current Review
均为 `REQUIRED_ASSET_MISSING`。Gate不得新增隐式角色，不得读取 Registry，也不得把
Character/Scene reference当成Final Shot Visual。

### Aggregation and STOP

```text
any check BLOCKED -> result BLOCKED, verified projection None
all checks PASS   -> result READY, exact verified projection present
```

`require_ready(result)` returns `VerifiedGenerationRequirementProjection` only for a valid
`READY` result。Otherwise it raises
`AiVideoError(ErrorCode.PLANNING_PREFLIGHT_BLOCKED, retryable=False)`，并在
`technical_detail`中使用stable typed reason codes。

On `BLOCKED`，Router、compiler、Provider、placeholder/materializer、composition、render、
Manifest、Registry与committer call counts必须为0。`READY`仅允许进入已有Router及后续
gates；它不等于routing selection、generation、fetch、activation、Review PASS、human
creative PASS或Final Acceptance。

## Compatibility Migration

### `require_current_video_plan()`

Public signature and return type remain：

```python
def require_current_video_plan(
    *, current_request: VideoPlanningRequest, plan: VideoGenerationPlan
) -> VerifiedGenerationRequirementProjection: ...
```

Its old decision body is retired。The façade creates/evaluates
`ShotReadinessRequest`，calls `require_ready()`，and returns that exact projection。It must not
retain parallel plan-outcome、warning或required-asset checks。

`prepare_shot_for_existing_production()` keeps its public route and handoff：

```python
projection = require_current_video_plan(
    current_request=current_request,
    plan=plan,
)
return production_handoff(
    current_shot=current_request.target_shot,
    generation_requirement=projection,
)
```

`plan_hint` is forbidden in implementation、tests、examples和handoff kwargs。

### Historical `video-planner/2`

- Preserve byte-identical v2 request/plan parse、hash fixture与historical reopen behavior。
- Do not add generation requirement or verified projection fields to v2 serialization。
- The readiness/new-attempt boundary always emits `LEGACY_PLANNER_REOPEN_ONLY` and STOP for
  v2；caller must rebuild a current v3 request from canonical inputs。
- No automatic v2→v3 conversion、hash rewrite、dual-readiness path或legacy new-attempt
  exception is allowed。

## Import and Module Boundary

Planned cohesive layout：

```text
src/ai_video/planning/_asset_readiness.py
src/ai_video/quality_gates/__init__.py
src/ai_video/quality_gates/_readiness_models.py
src/ai_video/quality_gates/shot_readiness_gate.py
```

`_asset_readiness.py` becomes the sole owner of current role/owner/final-visual/media-selection
semantics and is consumed by both `VideoPlanner` and the Gate。It imports no Gate、Router、
Provider、writer或lifecycle module。

The Gate may import planning contracts、the Planning freshness verifier、the shared asset helper、
cycle-neutral requirement projection models、canonical hashing、`ai_video.errors`、pydantic and
the standard library。Forbidden imports include Router、Provider adapters、
`production.video_generation`、local/cloud video adapters、committer/lifecycle、Manifest、
Registry、dependency、timeline、renderer、Review、CLI/transports、filesystem/network/environment/
secret/media APIs。

`video_planner.py` uses a function-local import for the compatibility façade if needed to avoid
module initialization cycles；architecture/import tests must prove importing either package does
not execute IO or create a reverse Production dependency。

## Harness Routing and Test Contract

Future implementation adds a focused check：

```yaml
shot_readiness_gate_tests:
  argv: [python, -m, pytest, -p, no:cacheprovider,
         tests/test_shot_readiness_gate.py,
         tests/test_planning_video_planner.py,
         tests/test_production_video_requirement.py,
         tests/test_errors.py, -q]
```

Future category `shot_readiness_gate` maps `src/ai_video/quality_gates/**`、
`src/ai_video/planning/_asset_readiness.py`与`tests/test_shot_readiness_gate.py` to
`shot_readiness_gate_tests` + `task_architecture_gate`。Because the compatibility façade and
Planning helper change, existing `video_planning.check_ids` must also include
`shot_readiness_gate_tests`。`.agent/harness/policy.yaml` and Harness routing tests change in the
same implementation commit；this docs slice does not edit runtime policy。

Focused future command：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_shot_readiness_gate.py \
  tests/test_planning_video_planner.py \
  tests/test_production_video_requirement.py \
  tests/test_errors.py -q
```

Integration STOP seam：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_shot_readiness_gate.py \
  tests/test_planning_video_planner.py \
  tests/test_production_shot_router.py \
  tests/test_production_video_requirement.py \
  tests/test_production_video.py \
  tests/test_errors.py -q
```

Final implementation acceptance must use the policy-routed exact staged snapshot or exact commit
range and a fresh self-verified Harness receipt。No Provider、ComfyUI、network、secret、media、
ffmpeg quality analysis or browser test belongs to this pure backend slice。

## Requirements and Acceptance

| Requirement | Acceptance evidence |
| --- | --- |
| R-01 exact v3 lineage | request/plan/requirement/projection seal and mutation matrix |
| R-02 no Planner re-derivation | one Planning verifier call；no second semantic builder |
| R-03 one readiness owner | compatibility façade has no parallel eligibility/asset body |
| R-04 v2 compatibility | historical hashes/reopen unchanged；new-attempt typed STOP |
| R-05 no `plan_hint` | source/test/example search and exact handoff kwargs |
| R-06 shared asset owner | Planner and Gate import one cycle-safe helper；wrong-binding matrix |
| R-07 typed complete diagnostics | ordered discriminated checks、stable reasons、result hash |
| R-08 zero side effects | BLOCKED spies for Router through committer all remain zero |
| R-09 lifecycle/quality isolation | import audit and unchanged focused P6/P8 contracts |
| R-10 Harness truth | exact routing tests and fresh staged/commit-range receipt |

Implementation acceptance requires all ten requirements, independent review with no blocking
issue, final parent diff review, and exact-snapshot Harness verification。Passing this gate proves
only structural readiness。

## Rollback

This docs repair has no runtime rollback beyond reverting the two docs files。

Future runtime rollback is one atomic code-unit revert：restore the previous
`require_current_video_plan()` body、remove the Gate package/tests/policy category、and move the
shared asset helper back only if all consumers are reverted together。There is no schema、Manifest、
Registry、artifact-layout或durable-state migration，so no data conversion or recovery action is
permitted。Rollback must preserve v2 reopen fixtures and must not restore `plan_hint` or open a v2
new-attempt path。

## Deferred Work and Experiment Boundary

After this runtime Gate is separately implemented、reviewed、committed and verified, the independent
`VideoGenerationRequest /5 effective_seed=None` compiler/Local H3 blocker may be diagnosed and
fixed in its own code slice。Only after that fix is accepted may a separately authorized Local H3
experiment be attempted。

That experiment may contribute P6 Review/Pilot perceptual evidence。Its success or failure must not
redesign ShotReadinessGate, change readiness reasons, add post-fetch quality logic, or be interpreted
as this Gate's acceptance。Candidate 1 remains an external regression oracle for that later task；
Candidate 2/3 and live generation are not authorized by this Spec。

The preserved oracle is
`runs/c2-alice-local-h3-quality-candidate-1-20260821/output/alice-c2-local-h3-quality-candidate-1.mp4`
with SHA-256
`2b02881d81b1226ab90e9791a472be7b6f02ef1b8584e5b2e1fe7d4050773de8`。This path/hash is a
later experiment input identity only，不是readiness、quality或current media acceptance evidence。
