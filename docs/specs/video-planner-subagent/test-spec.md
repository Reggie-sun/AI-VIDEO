# Video Planner Subagent — Test Spec

Status: paired with requirements AC-1～AC-18, design algorithm, and tasks T1～T14

## Test layers

| Layer | Purpose |
|---|---|
| Unit | intent/motion/continuity classification, decision branches, asset readiness, reasons/warnings |
| Contract | strict schemas, hashes, forbidden fields, current evidence identity |
| Architecture | no Production writer/Provider/IO import and no Production reverse import |
| Integration | mandatory Main Agent STOP seam and downstream zero-call proof |

All behavioral cases are future executable pytest tests in `tests/test_planning_video_planner.py`. This document does not claim those tests currently exist or pass.

## Fixture contract

Fixtures must create sealed existing `Shot` / `Character` / `Scene` models plus immutable planner projections:

```python
def make_shot(*, visual_strategy=..., character_ids=..., motion_directives=...,
              required_asset_roles=..., review_policy=...) -> Shot: ...
def make_intent_evidence(*, character_action_required=False,
                         continuous_action_required=False,
                         spatial_change_required=False,
                         state_change_required=False,
                         subject_motion_directive_present=False,
                         evidence_unresolved=False, ...) -> ShotIntentEvidence: ...
def make_available_asset(*, role, asset_id, canonical_owner_id, ...) -> AvailableAsset: ...
def make_review_decision(*, target_shot_id, target_shot_content_hash,
                         rationale, allows_intentional_static=False,
                         allows_static_fallback=False,
                         allows_reusable_plate=False) -> ReviewDecisionProjection: ...
def make_request(**overrides) -> VideoPlanningRequest: ...
```

Helpers must use real model validation/sealing. Tests must not patch planner internals to manufacture an outcome.

## Legacy behavior cases

These cases preserve AC-1～AC-5 after the coherence gate. Each generated-video case supplies coherent typed intent evidence; otherwise the expected dynamic mode would be under-specified.

### Case 1 — important character with references

Input:

- generated-video Shot with important character;
- coherent subject-motion intent;
- current Character and Scene references;
- typed angle-change/reference continuity, with no semantic jump.

Assert:

```python
assert plan.outcome is PlanOutcome.PROPOSED
assert plan.generation_mode is GenerationMode.REFERENCE_TO_VIDEO
assert plan.continuity_mode is ContinuityMode.REFERENCE
assert plan.capability_requirements.needs_character_reference is True
assert ReasonCode.IMPORTANT_CHARACTER in plan.reason_codes
assert ReasonCode.REFERENCE_AVAILABLE in plan.reason_codes
```

### Case 2 — exact continuation with terminal evidence

Input: same-action generated-video continuation, no character reference, exact previous terminal asset available.

Assert `IMAGE_TO_VIDEO` or `FIRST_LAST_FRAME_VIDEO`, continuity `EXACT_TERMINAL`, `needs_terminal_reference=True`, and terminal reason present.

### Case 3 — independent environment Shot

Input: declared `GENERATED_VIDEO`, no character, no subject action/change requirement, no continuity dependency.

Assert `PROPOSED`, `TEXT_TO_VIDEO`, continuity `NONE`, and no character-reference requirement.

### Case 4 — important character without visual anchor

Assert `BLOCKED`, never `TEXT_TO_VIDEO`, with typed missing-character/visual-anchor reason and warning.

### Case 5 — angle change uses reference continuity

Input: important character, Character/Scene references and an available terminal, but typed continuity says angle change rather than exact action continuation.

Assert:

```python
assert plan.outcome is PlanOutcome.PROPOSED
assert plan.continuity_mode is ContinuityMode.REFERENCE
assert plan.generation_mode is GenerationMode.REFERENCE_TO_VIDEO
assert plan.capability_requirements.needs_terminal_reference is False
```

The available terminal must not force `EXACT_TERMINAL`.

## Static-first incident RED cases

These tests must be authored and observed RED before implementation. They are T14 completion gates, not optional negative-test notes.

### Case 6 — action Shot bootstrapped as `STATIC_IMAGE`

```python
def test_action_shot_bootstrapped_static_is_blocked_not_certified():
    request = make_request(
        target_shot=make_shot(visual_strategy=VisualStrategy.STATIC_IMAGE),
        shot_intent_evidence=make_intent_evidence(
            character_action_required=True,
            open_state_ref="alice-inside-cafe",
            close_state_ref="alice-outside-cafe",
            state_change_required=True,
        ),
        production_policy=make_policy(accept_static_image_fallback=False),
    )
    plan = VideoPlanner().plan(request)

    assert plan.outcome is PlanOutcome.BLOCKED
    assert plan.motion_requirement is MotionRequirement.CHARACTER_ACTION
    assert ReasonCode.STRATEGY_MOTION_MISMATCH in plan.reason_codes
    assert PlanWarning.REQUIRES_HUMAN_REVIEW in plan.warnings
    assert not (
        plan.generation_mode is GenerationMode.STATIC_IMAGE
        and plan.confidence == 1.0
    )
```

This is the direct regression for the five-minute rough-cut static-first incident.

### Case 7 — zoompan is not character motion

Input: action-required Shot whose only directives are `pan`, `zoom`, `zoompan` or `parallax`, declared `IMAGE_MOTION`.

Assert:

```python
assert plan.outcome is PlanOutcome.BLOCKED
assert ReasonCode.CAMERA_MOTION_ONLY in plan.reason_codes
assert ReasonCode.STRATEGY_MOTION_MISMATCH in plan.reason_codes
assert PlanWarning.CAMERA_MOTION_NOT_SUBJECT_MOTION in plan.warnings
assert plan.motion_requirement is MotionRequirement.CHARACTER_ACTION
```

The test must fail any implementation that treats a still-image transform as completed subject action.

### Case 8 — fallback false prohibits downgrade

Parametrize declared strategy over `STATIC_IMAGE` and camera-only `IMAGE_MOTION`. With action intent and `accept_static_image_fallback=False`, assert `BLOCKED` even when a Shot-specific keyframe is available. Asset readiness cannot override a prohibited fallback.

### Case 9 — references do not satisfy final visual readiness

Input: intentional static/image-motion Shot with Character and Scene references only; no Shot-specific keyframe or approved reusable plate.

Assert `BLOCKED`, `FINAL_SHOT_VISUAL_MISSING`, and required role includes `APPROVED_KEYFRAME` or `APPROVED_REUSABLE_PLATE`. Never accept the reference assets as the final visual.

Also parametrize:

- keyframe with `canonical_owner_id != target_shot.shot_id`;
- keyframe not bound by target Shot final-visual `required_asset_roles`;
- reusable plate without current reuse review/rationale.

All remain `BLOCKED`.

### Case 10 — intentional static with Shot-specific keyframe

Input:

- no character/continuous/spatial/state-change requirement;
- `STATIC_IMAGE`;
- approved keyframe owned by and canonically final-role-bound to target Shot;
- current explicit director rationale allowing intentional static.

Assert:

```python
assert plan.outcome is PlanOutcome.PROPOSED
assert plan.generation_mode is GenerationMode.STATIC_IMAGE
assert ReasonCode.INTENTIONAL_STATIC in plan.reason_codes
assert ReasonCode.FINAL_SHOT_VISUAL_AVAILABLE in plan.reason_codes
assert PlanWarning.FINAL_SHOT_VISUAL_MISSING not in plan.warnings
```

This proposal remains subject to downstream Review/Pilot.

### Case 11 — fallback true is reviewed and auditable

Two branches are mandatory:

1. fallback true but missing any of exact final asset, rationale, matching Shot/hash Review decision, or `allows_static_fallback=True` → `BLOCKED` + unresolved human-review warning;
2. all evidence present → `PROPOSED`, `STATIC_FALLBACK_ACCEPTED`, `STATIC_FALLBACK_REQUIRES_REVIEW`, and confidence not auto-`1.0`.

The success branch must not contain generated/reviewed/selected/locked/activated/final-acceptance state.

### Case 12 — `BLOCKED` is an executable STOP

```python
@pytest.mark.parametrize("stop_reason", [
    "blocked_outcome",
    "stale_source_request_hash",
    "stale_shot_id",
    "stale_shot_revision",
    "stale_shot_hash",
    "changed_review_same_shot_hash",
    "changed_policy_same_shot_hash",
    "changed_asset_binding_same_shot_hash",
    "missing_required_asset",
    "wrong_asset_owner_or_binding",
    "unresolved_human_review",
])
def test_main_agent_preflight_stops_before_execution(stop_reason):
    router = Mock()
    provider = Mock()
    materializer = Mock()
    composition = Mock()
    render = Mock()

    with pytest.raises(AiVideoError) as exc:
        main_agent_prepare_shot(
            current_request=make_current_request_for(stop_reason),
            plan=make_plan_for(stop_reason),
            router=router,
            provider=provider,
            materializer=materializer,
            composition=composition,
            render=render,
        )

    assert exc.value.code is ErrorCode.PLANNING_PREFLIGHT_BLOCKED
    router.assert_not_called()
    provider.assert_not_called()
    materializer.assert_not_called()
    composition.assert_not_called()
    render.assert_not_called()
```

A run-local placeholder/render path is also a downstream call and must remain unused.

### Case 13 — `PROPOSED` is not creative PASS

For a current plan with satisfied assets, assert the consumer may invoke only the existing Production handoff spy. It must not create or mutate Review acceptance, selection, lock, activation or Final Acceptance state. The plan schema must reject such fields.

## Contract tests

### Determinism

- same request twice and three times → identical payload/hash;
- changing only diagnostic `request_id` → identical semantic request hash and plan;
- changing target Shot hash, typed intent evidence, Review decision, asset owner/binding or fallback policy → different request/plan hash.

### Forbidden fields

Parametrize at least:

```text
provider_name, provider_profile, selected_capability_id,
manifest_revision, timeline_position, asset_path, output_asset_id,
generated, reviewed, selected, locked, activated, creative_pass,
final_acceptance
```

Every field must raise `ValidationError` under `extra="forbid"`.

### Architecture gates

- AST scan rejects Production state/Manifest/Registry/dependency/composition/timeline/renderer/Provider/CLI/IO/secret imports from `src/ai_video/planning/**`;
- AST scan rejects `ai_video.planning` imports from `src/ai_video/production/**`;
- planner runtime Skill call count is zero.

## Negative matrix

| Input defect | Expected result |
|---|---|
| intent evidence Shot id/hash mismatch | `BLOCKED` / stale evidence reason |
| prose intent unresolved | `BLOCKED` + `REQUIRES_HUMAN_REVIEW`; no keyword-selected mode |
| exact continuation without terminal | `BLOCKED` + missing terminal |
| important character without anchors | `BLOCKED`; no T2V downgrade |
| `EXISTING_VIDEO` outside accepted path | `BLOCKED` with explicit rationale |
| fallback Review projection for old Shot hash | treated absent; `BLOCKED` |
| reusable plate without target-Shot binding | `BLOCKED` + final visual missing |

## Coverage and completion

- planning model and algorithm line coverage target: ≥95%;
- AC-1～AC-18 each map to at least one executable assertion;
- T14 may not pass on determinism/hash/import tests alone;
- no live Provider, media generation, render, Pilot or quality claim is part of this test suite;
- exact implementation snapshot must pass policy-routed Harness checks after task-only staging.
