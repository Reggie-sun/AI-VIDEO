# AI-VIDEO Shot Readiness Gate Specification

## Status

Proposed v3; documentation-only specification. Runtime implementation is not included in this migration.

This document consolidates the former `docs/specs/shot-quality-gate/` v3 bundle. The source bundle is intentionally removed after migration so this file is the single Superpowers-format spec for the slice.

## Goal

Define one pure, deterministic, provider-neutral pre-submit `ShotReadinessGate` that:

- consumes an accepted sealed `VideoPlanningRequest` and its `VideoGenerationPlan` without re-deriving Planner truth;
- verifies current request/plan binding and only the asset roles already declared by the plan;
- returns complete typed diagnostics with true discriminated payload binding;
- enforces Main Agent STOP semantics before Router, Provider, materializer, composition, or render side effects;
- leaves Production, Review, Registry, Manifest, timeline, renderer, Provider, and activation ownership unchanged.

The gate is structural/current-plan readiness only. It does not detect identity drift, continuity quality, motion naturalness, subjective visual quality, or Final Acceptance.

## Current Runtime Truth

The accepted source surface already exposes a sealed `VideoGenerationPlan` and `require_current_video_plan()` consumer. The current consumer validates request/plan seals, deterministic plan identity, source request hash, target Shot identity, plan outcome, unresolved human review, and required asset readiness before the existing Production handoff.

The current production source also establishes the post-fetch owner boundary:

- `VideoFetchReceipt` and `LocalVideoFetchReceipt` validate `fetch_fingerprint` during construction/reopen;
- `VideoFetchReceipt.create()` validates the fetched content type against `VideoSubmission.expected_content_type`;
- `FetchedVideoCandidate` carries only `relative_path` and a typed receipt, not a submission projection or subjective media evidence;
- activation is performed by `prepare_video_activation_candidate()` followed by `activate_video_candidate()`.

Therefore v3 removes the duplicate post-fetch `VideoQualityGate`, does not import Provider/lifecycle modules, and adds no committer or Manifest hash field.

## Scope

### In scope

- one-Shot current-plan readiness;
- exact request/plan/Shot binding;
- plan-declared required-asset readiness;
- frozen strict models, deterministic semantic hashes, and discriminated outcomes;
- Main Agent STOP and compatibility migration from `require_current_video_plan()`;
- import/no-IO/no-Provider/no-writer architecture boundaries;
- future Harness routing contract and requirements-to-tests traceability.

### Non-goals

- Planner strategy, continuity, motion, capability, or fallback re-derivation;
- natural-language complexity or token heuristics;
- identity drift, face/wardrobe similarity, action naturalness, scene consistency, frame diversity, blur, resolution preference, or subjective quality;
- fetch receipt/content-type revalidation already owned by typed constructors and fetch owners;
- Provider selection, ranking, submit, poll, fetch, retry, repair, or fallback execution;
- Manifest/Registry/dependency/timeline/render writes, activation, recovery, or durable readiness evidence;
- new CLI, dependency, Provider, renderer, timeline, writer, automatic repair, or acceptance path;
- changes to P6 Review/Repair or the human Pilot Reality Gate.

## Ownership Model and Invariants

| Concern | Sole owner |
| --- | --- |
| Character / Scene / Shot truth | `ProductionProject` creative artifacts |
| Asset identity, provenance, and active binding | Asset Registry and canonical Shot roles |
| Strategy, continuity, motion, required roles, and capabilities | `VideoPlanner` |
| Current-plan eligibility and pre-submit STOP | `ShotReadinessGate` |
| Provider selection, execution, and fetched candidate lifecycle | Existing AI-VIDEO Router / Provider / `ProductionStateCommitter` |
| Manifest writes, activation, and recovery | `ProductionStateCommitter` |
| Timing and render | `ResolvedTimeline` and HyperFrames |
| Semantic/perceptual QA and Final Acceptance | P6 Review/Repair and human Pilot Reality Gate |

The gate must remain pure and provider-neutral. It must not read canonical stores, write evidence, activate a candidate, or accept quality. Production code must not reverse-import `ai_video.quality_gates`.

## Request Contract

```python
class ShotReadinessRequest(StrictModel):
    request_id: str                 # diagnostic only
    current_request: VideoPlanningRequest
    plan: VideoGenerationPlan
    contract_version: Literal["shot-readiness-gate/1"]
    request_content_hash: str
```

All models are frozen, strict, and `extra="forbid"`. `ShotReadinessRequest.create()` computes `request_content_hash` from exactly:

```python
{
    "contract_version": "shot-readiness-gate/1",
    "current_request_content_hash": current_request.request_content_hash,
    "plan_hash": plan.plan_hash,
}
```

Neither the outer `request_id` nor nested `VideoPlanningRequest.request_id` participates. Evaluation must recompute this outer seal even for an already-constructed model, and must independently validate both nested planner seals.

## Result Contract

The result has only `READY` and `BLOCKED` statuses and exactly three outcomes in this order:

1. `request_plan_binding`;
2. `plan_eligibility`;
3. `required_asset_readiness`.

Each check id has its own frozen payload and `Literal`-bound outcome model. The union uses `Field(discriminator="check_id")`; wrong check/payload combinations must fail validation. The result hash is the canonical hash of the result excluding only `result_hash`, and the result carries no diagnostic request id.

### Binding payload

`RequestPlanBindingPayload` reports validity of the outer readiness seal, nested request seal, plan seal, deterministic plan id, source request match, target Shot id/revision/content hash, and supported contract versions.

### Eligibility payload

`PlanEligibilityPayload` reports `plan_outcome`, unresolved `REQUIRES_HUMAN_REVIEW`, and the original planner warnings. The gate does not reinterpret Planner reasons or confidence.

### Asset payload

`RequiredAssetReadinessPayload` reports the plan's ordered required roles, ready roles, and missing roles. It checks only roles present in `plan.required_asset_roles` and never invents additional roles.

## Deterministic Evaluation

`ShotReadinessGate.evaluate()` always emits all three checks; it does not short-circuit diagnostics. Downstream work is nevertheless forbidden until `require_ready(result)` succeeds.

### Request/plan binding

The gate independently verifies:

1. outer readiness hash against the exact semantic projection above;
2. current planner request semantic seal;
3. plan semantic seal;
4. `plan_id == f"plan-{plan.source_request_content_hash[:24]}"`;
5. `plan.source_request_content_hash == current_request.request_content_hash`;
6. exact target Shot id, revision, and content hash;
7. both contracts are `video-planner/2`.

Any false value blocks with ordered typed reasons. The gate never calls `VideoPlanner.plan()` and never reconstructs strategy, continuity, motion, reasons, or capabilities.

### Plan eligibility

```text
plan.outcome == BLOCKED                 -> BLOCKED / PLAN_BLOCKED
REQUIRES_HUMAN_REVIEW remains present  -> BLOCKED / HUMAN_REVIEW_UNRESOLVED
otherwise                              -> PASS
```

Resolved audit warnings remain visible but do not create a second policy.

### Required asset readiness

Use one shared pure role-readiness seam for the existing semantics:

- Character reference owner matches a current target-Shot Character;
- Scene reference owner matches the target Scene;
- previous terminal matches both current previous-Shot identity and terminal asset id;
- approved keyframe/reusable plate has the exact target-Shot final-visual binding and required current Review projection.

Wrong owner, wrong binding, or missing role is `REQUIRED_ASSET_MISSING`. The gate does not inspect Registry files or treat a Character/Scene reference as a Final Shot Visual.

### Aggregation and STOP

```text
any check BLOCKED -> result BLOCKED
all checks PASS   -> result READY
```

`require_ready()` rejects an invalid or blocked result with `AiVideoError(ErrorCode.PLANNING_PREFLIGHT_BLOCKED, retryable=False)`. The compatibility `require_current_video_plan()` delegates to this single decision owner while preserving its public signature and error behavior. `prepare_shot_for_existing_production()` keeps its public route.

On a block, Router, Provider, placeholder/materializer, composition, and render call counts must remain zero. `READY` authorizes only entry into existing Production gates; it is not generation, selection, activation, Review PASS, human creative PASS, or Final Acceptance.

## Import, Side-Effect, and Lifecycle Boundary

The future package may contain:

```text
src/ai_video/quality_gates/
├── __init__.py
├── _readiness_models.py
└── shot_readiness_gate.py
```

Allowed imports are typed planning contracts, the shared pure planning asset-readiness seam, read-only schema/hash helpers, `ai_video.errors`, the standard library, and pydantic. Forbidden imports include Provider adapters, `production.video_generation`, `local_video`, lifecycle/committer modules, Manifest, Registry, dependency, timeline, renderer, Review, CLI/transports, filesystem/network/environment/secret APIs, and media access.

v3 adds no `VersionedArtifact`, receipt id/path, Manifest pointer, `VideoGenerationAttemptState` field, committer parameter, schema version, activation rule, or recovery behavior. Any durable readiness evidence is a separate migration requiring schema version, reopen, compatibility, recovery, replay, invalidation, and exact writer contracts.

## Post-Fetch Owner Audit

No `VideoQualityGate` exists in v3.

| Rejected v2 check | Existing owner | v3 decision |
| --- | --- | --- |
| fetch fingerprint | typed receipt validators and reopen | remove |
| submission/observation linkage | receipt constructor, fetch owner, committer | remove |
| artifact SHA/size linkage | typed fields and committer byte verification | remove |
| expected content type | `VideoSubmission` + `VideoFetchReceipt.create()` | remove |
| identity/continuity/motion/visual quality | P6 Review / Pilot and typed continuity owners | forbidden scope |

The remote receipt has only `submission_fingerprint`, so a pure gate cannot recover `expected_content_type` without IO or a new projection. A future post-fetch structural projection requires a concrete non-duplicated gap and fully projected provider-neutral input schema.

## Main Agent Integration

```python
current_request = VideoPlanningRequest.create(
    request_id="planner-shot-7-current",
    target_shot=current_shot,
    character_context=current_characters,
    scene_context=current_scene,
    available_assets=current_assets,
    previous_shot_state=current_previous_state,
    shot_intent_evidence=current_intent_evidence,
    review_decision=current_review_projection,
    production_policy=current_policy,
    planning_contract_version="video-planner/2",
)
plan = VideoPlanner().plan(current_request)
readiness_request = ShotReadinessRequest.create(
    request_id="readiness-shot-7-attempt-1",
    current_request=current_request,
    plan=plan,
    contract_version="shot-readiness-gate/1",
)
result = ShotReadinessGate().evaluate(readiness_request)
require_ready(result)
existing_handoff(current_shot=current_request.target_shot, plan_hint=plan)
```

For stale/blocked input, the Main Agent rebuilds the current planning projections and evaluates a fresh request. It must not mutate the ephemeral result, retry a Provider, repair, or persist gate state. Existing downstream ownership remains:

```text
existing Router / Provider
  -> submit / poll / fetch
  -> typed receipt + committer durable linkage
  -> prepare_video_activation_candidate
  -> activate_video_candidate
  -> composition / render
  -> P6 Review / Repair
  -> human Pilot Reality Gate / Final Acceptance
```

## Requirements and Traceability

| Requirement | Design | Task | Tests | Integration |
| --- | --- | --- | --- | --- |
| R-01 request/plan binding | D-02, D-04.1 | T1–T2 | TC-01–TC-05 | INT-01–INT-02 |
| R-02 plan eligibility | D-04.2 | T3 | TC-06–TC-07 | INT-01–INT-02 |
| R-03 required assets | D-04.3 | T4 | TC-08–TC-10 | INT-03 |
| R-04 discriminated outcomes | D-03 | T1, T5 | TC-11–TC-13 | INT-01–INT-03 |
| R-05 deterministic hashing | D-02–D-03 | T1, T5 | TC-14 | INT-01 |
| R-06 binary STOP | D-05 | T5–T6 | TC-15–TC-17 | INT-02, INT-04 |
| R-07 single owner | D-05 | T6 | TC-15–TC-17 | INT-04 |
| R-08 pure boundary | D-06 | T7 | TC-18 | INT-04 |
| R-09 no persistence | D-08 | T7 | TC-20 | INT-04 |
| R-10 post-fetch audit | D-09 | T7 | TC-20 | INT-04 |
| R-11 Harness routing | D-07 | T7–T8 | TC-19 | INT-04 |
| R-12 terminology boundary | D-01, D-10 | T8 | TC-20 | INT-01–INT-04 |

## Implementation Tasks

Exactly eight tasks are planned:

- **T1 — RED models, discrimination, and hashing:** add strict/frozen models, exact semantic projection, discriminated outcomes, and result validation; cover TC-11–TC-14.
- **T2 — Request/plan binding:** implement independent seal, identity, version, and deterministic plan-id checks; cover TC-01–TC-05.
- **T3 — Plan eligibility:** consume only outcome and warnings; cover TC-06–TC-07.
- **T4 — Required asset readiness:** extract the existing pure role-readiness helpers into one cycle-safe shared owner; cover TC-08–TC-10.
- **T5 — Evaluation and `require_ready`:** emit all checks, aggregate binary status, and preserve typed STOP conversion; cover TC-15 and validator branches.
- **T6 — Compatibility migration:** delegate `require_current_video_plan()` and retire the duplicate decision body while preserving handoff behavior; cover TC-16–TC-17.
- **T7 — Architecture and Harness routing:** add import/no-IO tests and the future policy category/check mapping, including the existing `video_planning.check_ids` overlap; cover TC-18–TC-20.
- **T8 — Exact snapshot verification:** run focused tests, exact staged/commit-range Harness verification, receipt validation, link/anchor checks, and final review.

## Test Contract

The future runtime tests use `python -m pytest -p no:cacheprovider` and contain exactly TC-01–TC-20:

| Cases | Contract |
| --- | --- |
| TC-01–TC-05 | current request/plan, outer/nested seal, plan id, stale source, and Shot identity binding |
| TC-06–TC-07 | planner-blocked and unresolved human-review eligibility |
| TC-08–TC-10 | missing, wrong-owner, wrong-final-visual, and wrong-terminal assets |
| TC-11–TC-14 | discriminated payloads, exact result structure, contradiction rejection, diagnostic hash exclusion |
| TC-15–TC-17 | forged/blocked result STOP, zero downstream calls, ready handoff exactly once |
| TC-18–TC-20 | import/no-side-effect boundary, Harness routing, owner/terminology audit |

Focused command for the future runtime slice:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_shot_readiness_gate.py \
  tests/test_planning_video_planner.py \
  tests/test_errors.py -q
```

Final acceptance must use the policy-routed exact staged snapshot or exact commit range. No live Provider, ComfyUI, network, secret, media generation, ffmpeg quality analysis, or browser test belongs to this pure backend slice.

## Harness Routing Contract

The later runtime implementation must update `.agent/harness/policy.yaml` and Harness tests in the same change. The planned focused check is:

```yaml
shot_readiness_gate_tests:
  argv: [python, -m, pytest, -p, no:cacheprovider,
         tests/test_shot_readiness_gate.py,
         tests/test_planning_video_planner.py,
         tests/test_errors.py, -q]
```

The future `shot_readiness_gate` category maps `src/ai_video/quality_gates/**`, its fixture, and its tests to `shot_readiness_gate_tests` plus `task_architecture_gate`. Because T6 changes the planning compatibility seam, the existing `video_planning.check_ids` must also include `shot_readiness_gate_tests`. This v3 documentation migration does not edit runtime policy.

## Acceptance

- one Superpowers-format spec is the sole documentation truth for this slice;
- exactly R-01–R-12, D-01–D-10, T1–T8, TC-01–TC-20, and INT-01–INT-04 remain traceable;
- no post-fetch `VideoQualityGate`, committer hash field, Manifest migration, Provider import, or quality claim is introduced;
- the future implementation has one readiness algorithm and preserves existing STOP/error/handoff contracts;
- independent review has no blocker and exact-snapshot Harness verification is fresh, passed, integrity-valid, policy-valid, and snapshot-valid.

## Deferred Slices

### D1 — Provider-Neutral Post-Fetch Structural Projection

Do not start until a concrete structural fact is demonstrated to be outside typed receipt construction, fetch owner, committer, candidate validation, and P6 Review. The input must be fully projected and provider-neutral; it must not infer a submission from `submission_fingerprint`.

### D2 — Durable Readiness Evidence Migration

Requires explicit approval and a complete Manifest schema/version, writer, path/layout, content-addressing, reopen, compatibility, recovery/crash-window, replay, invalidation, and activation contract. An optional hash field is not migration-free.

Identity drift, continuity quality, motion naturalness, subjective picture quality, Final Acceptance, and automatic repair remain with existing Review/Pilot/Repair owners and are not deferred gate tasks.

## Risks and Rollback

| Risk | Control |
| --- | --- |
| second readiness algorithm | compatibility wrapper delegates; old decision body is retired |
| gate re-derives Planner truth | gate consumes only sealed plan outcome/warnings/required roles |
| `READY` is mistaken for quality acceptance | binary eligibility wording and lifecycle/acceptance field prohibition |
| diagnostic identity changes semantics | explicit three-field request projection |
| future post-fetch scope repeats an owner | D1 requires a demonstrated gap and fully projected schema |

The v3 document migration itself has no runtime rollback. A future implementation rollback restores the existing compatibility consumer and removes the quality-gate package/tests/policy category without changing Production schema or Manifest state.
