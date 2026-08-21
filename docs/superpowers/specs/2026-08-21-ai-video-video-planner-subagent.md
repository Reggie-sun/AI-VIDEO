# AI-VIDEO Video Planner Subagent Specification

## Status

Implemented and offline-accepted。Initial provider-neutral Planner runtime由commit
`779d40d9f7426f82d2dac72a73adee3b22d283bb`引入，Harness/architecture closure由
`a232d151f0ca3d1b33588e05db4c2dc2545aeaf5`完成；passing completion receipt为
`.agent/harness/runs/video-planner-complete-20aeeff-a232d15/receipt.json`。Commit `007e99c`
将new-attempt contract升级到`video-planner/3`并内嵌provider-neutral requirement；commit
`404facd`再把current projection verification与structural readiness decision分别收敛到Planning
verifier和`ShotReadinessGate`。Planner v3 core已进入current cached `origin/main`，后续Gate
compatibility refinement仍只在local `main`；均尚未release。

本spec没有独立同名`docs/superpowers/plans/`文件；这是保留的documentation organization gap，
不是runtime未实现证据。本status不证明Provider调用、media generation、activation、creative
quality、Review或Final Acceptance。

The planner is a provider-neutral, plan-only per-Shot preflight. It audits the coherence of approved Shot intent, continuity evidence, motion requirements, available references, and the declared visual strategy before AI-VIDEO generation or composition. It does not own Production state, select a Provider, render media, or accept creative quality.

## Goal

Given canonical Character / Scene / Shot artifacts, current Asset Registry projections, approved Review evidence, and explicit production policy, produce a deterministic `VideoGenerationPlan` for one Shot:

- select a provider-neutral generation mode and continuity mode;
- state required asset roles and capability requirements;
- identify static-first strategy mismatches before any Provider call;
- preserve a Main Agent STOP boundary for stale, blocked, or incomplete plans;
- keep Provider, Manifest, Registry, timeline, renderer, Review, and Final Acceptance ownership unchanged.

The planner must prevent the old self-certifying path `STATIC_IMAGE -> MotionRequirement.NONE -> STATIC_IMAGE -> confidence=1.0` when typed intent evidence requires subject motion.

## Current Runtime Truth

The accepted source surface is `src/ai_video/planning/`:

- `VideoPlanningRequest`, `ShotIntentEvidence`, `AvailableAsset`, `ReviewDecisionProjection`, `PreviousShotState`, and `ProductionPolicyInput` are immutable request projections.
- `VideoPlanner.plan()` returns a sealed `VideoGenerationPlan` with deterministic `plan_id` and `plan_hash`.
- `VideoPlanner` is pure and does not read Production state.
- `require_current_video_plan()` is the Main Agent consumer. It validates request/plan seals, source request hash, Shot identity, outcome, human-review warnings, and required current assets before invoking a handoff.
- `prepare_shot_for_existing_production()` is a compatibility handoff wrapper; it does not create durable state.

The planner is implemented and offline-accepted. Named modules or tests alone仍不构成acceptance；
上述commits、policy-routed Harness receipts、current source/tests与verified runtime evidence共同定义
current truth。

## Scope

### In scope

- one-Shot planning and provider-neutral proposal output;
- exact identity and continuity projections;
- intent-first motion classification;
- coherent handling of static/image-motion declarations and explicit fallback policy;
- distinction between reference assets and Shot-specific Final Shot Visual assets;
- deterministic reason, warning, rationale, confidence, and hash semantics;
- Main Agent current-plan consumer and zero-call STOP semantics;
- import, no-IO, determinism, forbidden-field, and Harness routing contracts.

### Non-goals

- Provider selection, ranking, model/profile prompt adaptation, capability lookup, upload/download, secret, budget, permit, or network execution;
- Manifest, Registry, Dependency Graph, timeline, renderer, or Review writes;
- multi-Shot aggregate planning, repetition detection, frame diversity, long-static analysis, full-watch, Pilot Reality Gate, or Final Acceptance;
- VLM/human identity drift evaluation, automatic repair, retry, placeholder generation, or fallback execution;
- new CLI, dependency, schema migration, MCP runtime, LangGraph runtime, or Studio UI.

## Ownership Model

| Concern | Owner |
| --- | --- |
| Canonical creative intent and Shot identity | AI-VIDEO Character / Scene / Shot artifacts |
| Asset identity and provenance | Asset Registry and canonical Shot roles |
| Proposal strategy and continuity classification | `VideoPlanner` |
| Current-plan STOP consumption | Main Agent / `require_current_video_plan()` |
| Provider selection and execution | Existing AI-VIDEO Provider path |
| Durable lifecycle and activation | `ProductionStateCommitter` |
| Timing and composition | `ResolvedTimeline` and HyperFrames |
| Semantic/perceptual QA and Final Acceptance | P6 Review / Repair and human Pilot Reality Gate |
| External creative Skills | Advisory knowledge only |

Production MUST NOT import `ai_video.planning`; the planner MUST NOT import writers, Manifest, Registry, dependency, composition, timeline, HyperFrames, Provider adapters, CLI, transports, secrets, or filesystem/network APIs.

## Request Contract

All request and plan models are frozen, `extra="forbid"`, and sealed with canonical hashes. `request_content_hash` excludes only diagnostic `request_id` and the hash field itself; changing diagnostic identity must not change semantic planning.

### `VideoPlanningRequest`

```python
class VideoPlanningRequest(StrictModel):
    request_id: str
    target_shot: Shot
    character_context: tuple[Character, ...]
    scene_context: Scene
    available_assets: tuple[AvailableAsset, ...]
    previous_shot_state: PreviousShotState | None
    shot_intent_evidence: ShotIntentEvidence
    review_decision: ReviewDecisionProjection | None
    production_policy: ProductionPolicyInput
    planning_contract_version: Literal["video-planner/2"]
    request_content_hash: str
```

`ShotIntentEvidence` is a typed, ephemeral projection. It may identify open/close state, character action, continuous action, spatial change, state change, subject-motion directives, and unresolved evidence. Natural-language keyword matching MUST NOT set motion booleans; unresolved prose is a human-review condition.

`AvailableAsset` roles are `CHARACTER_REFERENCE`, `SCENE_REFERENCE`, `PREVIOUS_SHOT_TERMINAL`, `APPROVED_KEYFRAME`, `APPROVED_REUSABLE_PLATE`, and `EXISTING_VIDEO`. Character/Scene references guide identity, state, space, or style; they never become Final Shot Visual readiness by availability alone.

`ReviewDecisionProjection` is an ephemeral pointer/summary of current canonical Review/director evidence. It may allow intentional static, static fallback, or reusable plates, but the planner neither creates nor persists approval.

`PreviousShotState` carries exact previous Shot identity, same-scene/story/action flags, angle-change and semantic-jump flags, and an optional terminal asset id. `ProductionPolicyInput` carries local/remote eligibility, budget authorization, quality preference, and `accept_static_image_fallback`.

## Plan Contract

`VideoGenerationPlan` contains:

- deterministic `plan_id`, `source_request_content_hash`, and `plan_hash`;
- target Shot id, revision, and content hash;
- `GenerationMode`: `STATIC_IMAGE`, `IMAGE_MOTION`, `TEXT_TO_VIDEO`, `IMAGE_TO_VIDEO`, `FIRST_LAST_FRAME_VIDEO`, `REFERENCE_TO_VIDEO`, or `HYBRID`;
- `ContinuityMode`: `EXACT_TERMINAL`, `REFERENCE`, `SEMANTIC`, or `NONE`;
- `MotionRequirement`: `NONE`, `LIGHT_TRANSFORM`, `GRAPHIC`, `CHARACTER_ACTION`, `FREE_COMPLEX`, or `HERO_OR_REPAIR`;
- ordered `RequiredAssetRole` entries and provider-neutral `CapabilityRequirements`;
- typed reason codes, warnings, bounded confidence, deterministic rationale, outcome, and contract version.

`PlanOutcome` is only `PROPOSED | BLOCKED`. `PROPOSED` means eligible to enter existing Production gates; it does not mean generated, reviewed, selected, locked, activated, human creative PASS, or Final Acceptance. Forbidden fields include Provider/profile selection, paths, Manifest/timeline state, output assets, activation, repair, acceptance, or Review receipt payloads.

## Deterministic Planning Algorithm

### 1. Validate current evidence

Validate the request seal, ShotIntentEvidence identity, current Review projection, exact asset owners/bindings, and unresolved evidence. Any stale or unresolved identity produces typed reasons/warnings and ultimately `BLOCKED`.

### 2. Derive continuity

```text
first / independent Shot       -> NONE
semantic jump / explicit reset -> SEMANTIC
same action, no angle change   -> EXACT_TERMINAL
angle change                   -> REFERENCE
otherwise                      -> REFERENCE
```

Only `EXACT_TERMINAL` requires terminal reference capability. `REFERENCE` preserves identity/state guidance while allowing a new composition.

### 3. Derive motion independently

Typed intent evidence has priority. Subject action, continuous action, spatial/state change, or subject animation yields `CHARACTER_ACTION`. Only `pan`, `zoom`, `zoompan`, and `parallax` are camera/image transforms and may yield `LIGHT_TRANSFORM`; they cannot satisfy subject action or open-to-close state change. `MOTION_GRAPHICS` yields `GRAPHIC`; coherent static yields `NONE`; otherwise generated/hybrid intent yields `FREE_COMPLEX`.

`Shot.visual_strategy` is an authoring declaration to audit. It cannot erase motion requirements derived from typed evidence.

### 4. Enforce coherence and fallback

- Static or camera-only image-motion plus required subject action: default `BLOCKED` with mismatch and human-review warning.
- Static fallback is `PROPOSED` only when policy allows it, a current Review projection allows it, explicit rationale exists, and a target-Shot Final Shot Visual is ready; the result retains an audit warning.
- Intentional static requires explicit rationale, a target-Shot Final Shot Visual, and current Review evidence.
- Any static/image-motion plan without Final Shot Visual is `BLOCKED`.

### 5. Select dynamic provider-neutral mode

- `EXACT_TERMINAL` with current terminal → `IMAGE_TO_VIDEO` or `FIRST_LAST_FRAME_VIDEO`.
- Character/Scene references with important identity and non-terminal continuity → `REFERENCE_TO_VIDEO`.
- Identity-free independent environment → `TEXT_TO_VIDEO`.
- Graphic motion → `HYBRID`.
- Missing character/scene/terminal anchor or hero/repair evidence → `BLOCKED`.

No branch names or selects a Provider.

### 6. Declare required roles and capabilities

Required roles are recorded, not materialized. Character/Scene roles are required for reference generation; terminal is required for exact continuation; target-Shot keyframe/reusable plate is required for static/image-motion; text-to-video has no implicit identity role. Main Agent current-plan consumption rechecks exact role availability.

### 7. Emit typed audit data

Every branch emits consistent reason codes and warnings. Rationale is assembled from deterministic templates; confidence cannot override `BLOCKED`, missing evidence, stale identity, or human review.

## Main Agent STOP Contract

Before any Provider/Asset execution or composition, the Main Agent MUST rebuild a current request and call the consumer. It stops on:

- invalid request or plan seal;
- non-deterministic plan id;
- stale source request hash or target Shot id/revision/content hash;
- `PlanOutcome.BLOCKED`;
- unresolved `REQUIRES_HUMAN_REVIEW`;
- missing, wrong-owner, or wrong-binding required assets.

After STOP, Router, Provider, placeholder/materializer, composition, and render call counts must be zero. On success, the handoff only enters existing Production gates and does not activate or accept anything.

## Integration Example

```python
request = VideoPlanningRequest.create(
    request_id="planner-shot-7",
    target_shot=current_shot,
    character_context=current_characters,
    scene_context=current_scene,
    available_assets=current_assets,
    previous_shot_state=previous_state,
    shot_intent_evidence=intent_evidence,
    review_decision=current_review,
    production_policy=policy,
    planning_contract_version="video-planner/3",
    generation_intent=current_generation_intent,
)
plan = VideoPlanner().plan(request)
projection = require_current_video_plan(current_request=request, plan=plan)
existing_production_handoff(
    current_shot=request.target_shot,
    generation_requirement=projection,
)
```

When the plan is `BLOCKED`, `require_current_video_plan()` raises typed `ErrorCode.PLANNING_PREFLIGHT_BLOCKED` and the handoff is not called. When `PROPOSED` and current, the existing handoff is called once.

## Acceptance

The implementation must provide executable coverage for:

1. Character + Character/Scene references → `REFERENCE_TO_VIDEO`;
2. exact same-action continuation + terminal → image-to-video with terminal capability;
3. independent environment → text-to-video with `NONE` continuity;
4. important character without visual anchor → `BLOCKED`, never silent T2V;
5. angle change → `REFERENCE`, not forced `EXACT_TERMINAL`;
6. same sealed request → identical plan/hash;
7. forbidden fields rejected;
8. planner import boundary and no runtime Skill calls;
9. static-first action mismatch regression;
10. camera-only transform does not count as subject motion;
11. fallback false blocks downgrade;
12. Character/Scene references do not satisfy Final Shot Visual;
13. intentional static requires target-Shot keyframe/rationale/Review;
14. approved fallback remains auditable;
15. blocked, stale, missing, or unresolved plans produce zero downstream calls;
16. `PROPOSED` is not creative PASS, Review acceptance, activation, or Final Acceptance;
17. current request/plan consumer and integration route are documented and tested;
18. exact staged/commit-range Harness verification is fresh and passing.

## Implementation Plan and Traceability

The source task plan is T1–T14: schema/projections; typed reasons; continuity; intent-first motion; coherence/fallback; reference vs Final Shot Visual; confidence/review semantics; forbidden fields; determinism/current identity; architecture import gate; previous-Shot helper; integration examples; executable Main Agent consumer; final regression/acceptance.

The source test contract covers legacy cases, static-first RED cases, determinism, forbidden fields, architecture gates, STOP spies, and `PROPOSED` semantics. Harness routing is through the `video_planning` category and `video_planner_tests` plus the repository Architecture Gate.

Every implementation task must map to at least one requirement, test case, integration example, and exact verification command. Deferred work includes multi-Shot planning, richer typed continuity evidence, Provider-specific adapters, VLM identity drift, Review/Repair integration, and runtime Skill integration.

## Risks and Rollback

| Risk | Control |
| --- | --- |
| Planner and Router overlap | Planner proposes; existing Main Agent consumer owns STOP; Production owns execution |
| Static strategy self-certifies | Derive intent/motion first, then audit declared strategy |
| Reference becomes final visual | Exact target-Shot role binding and owner/reuse Review evidence |
| Fallback becomes automatic | Policy plus current Review/rationale gates; audit warning retained |
| Planner becomes Production owner | Import blacklist, no IO, no durable state, no reverse Production import |

The planner can be removed with its package/tests without a Production schema or Manifest migration. Runtime rollback restores explicit caller behavior and leaves existing Production owners unchanged.
