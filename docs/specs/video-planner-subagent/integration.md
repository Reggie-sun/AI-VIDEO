# Video Planner Subagent — Integration Guide

Audience: Main Agent / run authors preparing an existing AI-VIDEO Shot for generation or composition.

Status: mandatory consumer contract specification; no runtime implementation is claimed by this docs slice.

## 1. Required ordering

Every Shot preparing to enter Provider/Asset execution or composition must obtain a plan for the current Shot revision/hash and pass the Main Agent consumer:

```text
approved AI-VIDEO Shot / Asset / Review truth
  -> VideoPlanner per-Shot preflight
  -> Main Agent current-plan consumer / STOP
  -> AI-VIDEO Provider / Asset execution
  -> Composition
  -> Review
  -> human Pilot Reality Gate
```

Call before router/Provider choice, generation submit, placeholder materialization, composition, render, or any run-local shortcut that could produce a Shot visual.

The planner is not needed before a canonical Shot exists. Provider/model prompt adaptation is outside this slice.

## 2. Ownership and semantics

The planner is provider-neutral, pure and stateless. Its output is advisory as a strategy proposal, but consumption is mandatory:

- Production retains Provider selection/execution and durable state ownership.
- Asset Registry and canonical Shot bindings retain asset truth.
- Review retains creative-quality evidence.
- Human Pilot Reality Gate retains 30～60 second full-watch/reality acceptance.
- Main Agent must enforce planner STOP conditions before calling Production.

“Advisory” means planner does not bind Production selection. It does not mean the caller may ignore `BLOCKED`.

## 3. Building the current request

Main Agent supplies:

| Request field | Canonical source / projection rule |
|---|---|
| `target_shot` | current activated/selected `Shot` from `ProductionProject` |
| Character/Scene context | exact current canonical artifacts referenced by Shot |
| `previous_shot_state` | typed current upstream Shot/continuity evidence |
| `shot_intent_evidence` | sealed projection of approved intent, open/close state, continuity constraints and motion directives |
| `available_assets` | read-only current Registry/Shot-binding snapshot |
| `review_decision` | optional current pointer/summary from existing AI-VIDEO Review/director evidence |
| `production_policy` | task-scoped policy; `accept_static_image_fallback` must not be invented |

`Shot.intent` prose is not sufficient to derive action with keywords. If typed evidence cannot resolve it, set `evidence_unresolved=True`; the plan must require human review.

### Reference and final visual mapping

When constructing `available_assets`:

- Character/Scene reference roles remain reference guidance.
- A keyframe may be labeled `APPROVED_KEYFRAME` only when its `canonical_owner_id` is the target Shot and target Shot canonical `required_asset_roles` binds that exact asset to its final-visual role.
- A reusable plate may be labeled `APPROVED_REUSABLE_PLATE` only with the same target-Shot binding plus current Review/director reuse evidence and rationale.
- Do not relabel a reference-pack image or simple derivative as a final Shot visual merely because the bytes exist.

## 4. Request example

Illustrative API shape only:

```python
request = VideoPlanningRequest.create(
    request_id="plan-shot-7-attempt-1",
    target_shot=current_shot,
    character_context=(project.characters["alice"],),
    scene_context=project.scenes["scene-cafe"],
    available_assets=(
        AvailableAsset(
            role=AssetRole.CHARACTER_REFERENCE,
            asset_id="ref-alice",
            asset_sha256=registry.assets["ref-alice"].sha256,
            canonical_owner_id="alice",
            mime_type="image/png",
        ),
        AvailableAsset(
            role=AssetRole.SCENE_REFERENCE,
            asset_id="ref-cafe",
            asset_sha256=registry.assets["ref-cafe"].sha256,
            canonical_owner_id="scene-cafe",
            mime_type="image/png",
        ),
    ),
    previous_shot_state=VideoPlanner.derive_previous_shot_state(
        previous_shot=previous_shot,
        target_shot=current_shot,
    ),
    shot_intent_evidence=ShotIntentEvidence(
        target_shot_id=current_shot.shot_id,
        target_shot_content_hash=current_shot.content_hash,
        open_state_ref="alice-inside-cafe",
        close_state_ref="alice-outside-cafe",
        character_action_required=True,
        spatial_change_required=True,
    ),
    review_decision=None,
    production_policy=ProductionPolicyInput(
        local_resources_available=True,
        remote_authorized=False,
        budget_authorized=False,
        quality_preference="production",
        accept_static_image_fallback=False,
    ),
    planning_contract_version="video-planner/2",
)

plan = VideoPlanner().plan(request)
```

The example references only existing project/asset truth plus ephemeral projections. It does not write Manifest/Registry/Review state.

## 5. Mandatory Main Agent consumer

The future integration must have an executable seam equivalent to:

```python
def prepare_shot_for_existing_production(*, current_request, plan,
                                         production_handoff):
    require_current_video_plan(
        current_request=current_request,
        plan=plan,
    )
    return production_handoff(
        current_shot=current_request.target_shot,
        plan_hint=plan,
    )
```

`require_current_video_plan(...)` must STOP with typed failure when any condition is true:

1. `plan.source_request_content_hash` differs from a freshly rebuilt current request hash (which includes current Shot, Review evidence identity, policy and asset-binding projections);
2. plan Shot id/revision/content hash is not current;
3. `plan.outcome == PlanOutcome.BLOCKED`;
4. any `required_asset_roles` item is absent, stale, wrong-owner, or lacks exact target-Shot binding;
5. `REQUIRES_HUMAN_REVIEW` is unresolved.

STOP means router, Provider, placeholder/materializer, composition and render are not invoked. A run-local script may not catch the failure and continue with a placeholder.

On success, `production_handoff` only enters existing Production gates. It does not write acceptance or activation state. This seam lives on the Main Agent/planning side; Production modules must not import planner.

## 6. Outcome handling

```python
match plan.outcome:
    case PlanOutcome.BLOCKED:
        raise planning_preflight_blocked(plan.reason_codes, plan.warnings)
    case PlanOutcome.PROPOSED:
        require_current_request_identity(plan, current_request)
        require_current_assets(
            plan.required_asset_roles,
            current_request.available_assets,
            current_request.target_shot,
        )
        require_resolved_review_warnings(plan.warnings)
        # Eligible only to enter existing Production gates.
```

`PROPOSED` does **not** mean:

- generated;
- reviewed or human creative PASS;
- selected or locked;
- activated;
- composition complete;
- Pilot passed;
- Final Acceptance.

`plan_hash` is only a deterministic plan identity. It is not a Manifest receipt, Review receipt, activation pointer or approval token.

## 7. Worked mismatch example: action Shot bootstrapped static

Setup:

- Shot intent/open-close evidence says Alice moves from inside to outside the cafe;
- `Shot.visual_strategy` was incorrectly bootstrapped as `STATIC_IMAGE`;
- only Character/Scene references are available;
- `accept_static_image_fallback=False`.

Illustrative plan:

```json
{
  "target_shot_id": "shot-7",
  "target_shot_revision": 3,
  "target_shot_content_hash": "ab12...64hex",
  "source_request_content_hash": "cd34...64hex",
  "generation_mode": "static_image",
  "continuity_mode": "reference",
  "motion_requirement": "character_action",
  "required_asset_roles": [
    {
      "role": "approved_keyframe",
      "reason_code": "final_shot_visual_required"
    }
  ],
  "reason_codes": [
    "action_intent_required",
    "strategy_motion_mismatch"
  ],
  "warnings": [
    "final_shot_visual_missing",
    "requires_human_review"
  ],
  "confidence": 0.9,
  "outcome": "blocked",
  "rationale": "Subject action and spatial change cannot be satisfied by the declared static strategy; references are not a final Shot visual.",
  "planning_contract_version": "video-planner/2",
  "plan_hash": "9f2e...64hex"
}
```

Main Agent interpretation: STOP. Do not route, call a Provider, generate a placeholder, compose, or render. Re-author the Shot strategy or gather the required current evidence/assets and create a new plan.

The `generation_mode` field remains the audited declared/proposed lane even on `BLOCKED`; downstream code must key eligibility from `outcome` and the mandatory consumer, never from mode alone.

## 8. Worked intentional-static example

Setup:

- typed intent requires no subject action or state/spatial change;
- target Shot canonically binds `keyframe-shot-12` as its final visual;
- asset owner is `shot-12`;
- current director/Review evidence records the intentional-static rationale.

Expected key assertions:

```python
assert plan.outcome is PlanOutcome.PROPOSED
assert plan.generation_mode is GenerationMode.STATIC_IMAGE
assert ReasonCode.INTENTIONAL_STATIC in plan.reason_codes
assert ReasonCode.FINAL_SHOT_VISUAL_AVAILABLE in plan.reason_codes
```

Main Agent may now enter existing Production gates. Review still checks the composed result; the human Pilot Gate still checks real pacing, repetition and watchability.

## 9. Static fallback true

For an action Shot, `accept_static_image_fallback=True` is insufficient by itself. The request must also contain:

- approved Shot-specific keyframe or approved reusable plate with exact target-Shot binding;
- explicit fallback/director rationale;
- matching current Review decision allowing static fallback (and reuse if applicable).

When complete, planner may return `PROPOSED` with `STATIC_FALLBACK_ACCEPTED` and `STATIC_FALLBACK_REQUIRES_REVIEW`. This is auditable degraded intent, not automatic creative PASS. Missing or stale evidence returns `BLOCKED` + unresolved `REQUIRES_HUMAN_REVIEW`.

## 10. Failure table

| Failure | Main Agent action |
|---|---|
| malformed request | fix inputs; do not retry blindly |
| stale plan or evidence identity | rebuild request from current canonical truth; STOP current attempt |
| strategy/motion mismatch | re-author strategy or obtain explicit reviewed fallback evidence; STOP |
| final visual missing | obtain/bind Shot-specific keyframe or approved reusable plate; references alone are insufficient |
| `BLOCKED` | STOP before router/Provider/placeholder-materializer/composition/render |
| unresolved human review | obtain current Review/human decision; STOP |
| downstream capability unavailable | existing Production policy handles it; planner does not rank/select/fallback Providers |

## 11. Review and Pilot responsibilities

Planner solves per-Shot preflight only:

- intent/strategy coherence;
- camera transform vs subject action boundary;
- static fallback eligibility;
- reference vs final visual readiness;
- required capability/assets and typed reasons/warnings.

Review/Pilot still solve:

- repeated final visuals across Shots;
- long static regions and frame diversity;
- final pacing, continuity as watched, audio/visual integration;
- 30～60 second Pilot Reality Gate and human full-watch;
- repair and creative-quality decision evidence; human full-watch and Final Acceptance decision.

Durable selection/lock/activation persistence remains with the existing Production Manifest lifecycle and `ProductionStateCommitter`; Review/Pilot do not become lifecycle writers.

Do not extend `VideoPlanner` into an aggregate repetition scanner or quality owner to satisfy this contract.

## 12. Rollout boundary

- Current slice: repaired docs/spec/plan only.
- Future implementation: T1～T14, including Main Agent consumer in T13.
- D1: optional planner-to-router hint projection only; it may not own or defer STOP semantics and must not refactor Router.
- D3: multi-Shot planning remains deferred.
- No Provider prompt/model adaptation, media generation, Production runtime mutation, or Router change is part of this slice.

## 13. References

- `requirements.md` — AC-1～AC-18
- `design.md` — schemas, evidence precedence, algorithm and consumer contract
- `tasks.md` — RED/GREEN execution plan and traceability matrix
- `test-spec.md` — incident regressions and zero-call STOP proof
- `docs/record_for_agent/2026-08-20-5-minute-rough-cut-editorial-failure-and-recovery.md` — historical failure evidence
