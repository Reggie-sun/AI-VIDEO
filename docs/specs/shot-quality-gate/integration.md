# Shot Readiness Gate — Integration v3

Status: proposed integration contract; no runtime implementation in this docs slice

Audience: Main Agent/planning maintainers

## INT-01 — Ready Current Plan

The Main Agent freshly rebuilds the current `VideoPlanningRequest` from canonical Shot, asset binding, Review decision, and policy projections, then asks the accepted Video Planner for a plan.

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
```

Illustrative result:

```json
{
  "source_readiness_request_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "status": "ready",
  "checks": [
    {
      "check_id": "request_plan_binding",
      "severity": "pass",
      "reasons": [],
      "payload": {
        "readiness_request_seal_valid": true,
        "request_seal_valid": true,
        "plan_seal_valid": true,
        "plan_id_valid": true,
        "source_request_matches": true,
        "target_shot_id_matches": true,
        "target_shot_revision_matches": true,
        "target_shot_content_hash_matches": true,
        "contract_versions_supported": true
      }
    },
    {
      "check_id": "plan_eligibility",
      "severity": "pass",
      "reasons": [],
      "payload": {
        "plan_outcome": "proposed",
        "unresolved_human_review": false,
        "warnings": []
      }
    },
    {
      "check_id": "required_asset_readiness",
      "severity": "pass",
      "reasons": [],
      "payload": {
        "required_roles": ["character_reference", "scene_reference"],
        "ready_roles": ["character_reference", "scene_reference"],
        "missing_roles": []
      }
    }
  ],
  "blocked_reasons": [],
  "contract_version": "shot-readiness-gate/1",
  "result_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
}
```

`READY` authorizes only entry into existing Production gates. It is not generation, selection, activation, Review PASS, human creative PASS, or Final Acceptance.

## INT-02 — Stale or Blocked Plan Stops

If current asset binding, Review decision, policy, Shot revision, or any other semantic input changes, the Main Agent rebuilds `current_request`. An old plan then fails source binding.

```python
result = ShotReadinessGate().evaluate(
    ShotReadinessRequest.create(
        request_id="readiness-shot-7-after-edit",
        current_request=fresh_current_request,
        plan=old_plan,
        contract_version="shot-readiness-gate/1",
    )
)

assert result.status is ReadinessStatus.BLOCKED
assert ReadinessBlockedReason.PLAN_SOURCE_STALE in result.blocked_reasons
require_ready(result)  # raises PLANNING_PREFLIGHT_BLOCKED
```

The same STOP applies when the planner itself returned `BLOCKED` or still carries `REQUIRES_HUMAN_REVIEW`. The readiness gate reports that fact; it does not reinterpret or repair it.

Illustrative blocked fragment:

```json
{
  "status": "blocked",
  "blocked_reasons": ["plan_source_stale"],
  "checks": [
    {
      "check_id": "request_plan_binding",
      "severity": "blocked",
      "reasons": ["plan_source_stale"],
      "payload": {
        "readiness_request_seal_valid": true,
        "request_seal_valid": true,
        "plan_seal_valid": true,
        "plan_id_valid": true,
        "source_request_matches": false,
        "target_shot_id_matches": true,
        "target_shot_revision_matches": true,
        "target_shot_content_hash_matches": true,
        "contract_versions_supported": true
      }
    }
  ]
}
```

The fragment omits the other required checks and hash only for readability; a valid result always contains all three canonical outcomes.

## INT-03 — Missing Current Asset Stops

The gate checks only roles already declared by the plan. It does not decide that a role should have been required.

```python
plan.required_asset_roles
# -> CHARACTER_REFERENCE, SCENE_REFERENCE

current_request.available_assets
# -> current SCENE_REFERENCE only

result = ShotReadinessGate().evaluate(readiness_request)
assert result.status is ReadinessStatus.BLOCKED

assets = next(
    check
    for check in result.checks
    if check.check_id is ShotReadinessCheckId.REQUIRED_ASSET_READINESS
)
assert assets.payload.missing_roles == (AssetRole.CHARACTER_REFERENCE,)
```

Wrong owners and wrong final-visual bindings are treated as missing readiness. The caller must fix canonical assets/Review evidence and rebuild a fresh planning request; it must not mutate the ephemeral result.

## INT-04 — Compatibility and Downstream Route

Existing callers may keep using:

```python
prepare_shot_for_existing_production(
    current_request=current_request,
    plan=plan,
    production_handoff=existing_handoff,
)
```

After the future implementation, the internal route is:

```text
prepare_shot_for_existing_production
  -> require_current_video_plan                # compatibility wrapper
  -> ShotReadinessRequest.create
  -> ShotReadinessGate.evaluate
  -> require_ready
  -> existing_handoff only when READY
```

On any block, Router, Provider, placeholder/materializer, composition, and render are not invoked.

After handoff, existing owners remain unchanged:

```text
existing Router / Provider
  -> VideoGenerationService submit/poll/fetch
  -> typed fetch receipt + committer durable linkage
  -> prepare_video_activation_candidate
  -> activate_video_candidate
  -> composition/render when selected by existing flow
  -> P6 Review / Repair
  -> human Pilot Reality Gate / Final Acceptance
```

There is no post-fetch `VideoQualityGate`, `commit_video_activation()`, readiness receipt handoff, or Manifest readiness hash in v3.

## Caller Rules

- MUST rebuild current planning projections from canonical owners before evaluation.
- MUST use the exact plan paired with the current request hash.
- MUST stop on `BLOCKED`; changing only diagnostic `request_id` cannot make a result ready.
- MUST NOT treat a result as Registry, Manifest, Review, activation, provenance, or delivery evidence.
- MUST NOT call a Provider, retry, repair, or persist state from inside gate evaluation.
- MUST send subjective/semantic/media-quality questions to existing P6 Review/Pilot owners.

## No Migration in v3

The runtime slice described here is a pure Main Agent/planning-side compatibility migration. It changes no Production schema, Manifest version, committer API, recovery path, Provider request, artifact layout, CLI, timeline, renderer, or Review contract.
