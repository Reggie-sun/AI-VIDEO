# Video Planner Subagent — Integration Guide

Audience: Main Agent / Codex authors who need to ask "what generation strategy should this Shot use?" before invoking AI-VIDEO Production.

Status: paired with `requirements.md` + `design.md` + `tasks.md`.

## 1. When Main Agent should call this module

Call the planner **before** any of:

- `ProductionStateCommitter.commit_video_intent(...)`
- `ShotVisualResolver.resolve(...)` inside Production
- Any decision about whether to invoke a Provider
- Any prompt engineering that branches on Shot identity / continuity

If Main Agent is **purely** reasoning about Story / Scene / Storyboard (no Shot yet), no call is needed.

## 2. Why this module exists

AI-VIDEO Production is canonical owner of Manifest, Asset Registry, Timeline, Provider selection, and review. Main Agent does not (and must not) duplicate those decisions. But Main Agent needs a structured way to say:

> "Given this Shot's intent, characters, scene, available references, and previous Shot state — what generation strategy should I steer the system toward?"

The planner answers that question with a `VideoGenerationPlan`. It is:

- **Provider-neutral** — never names a Provider
- **Pure** — same input → same `plan_hash`
- **Stateless** — no DB, no cache, no IO
- **Advisory** — Production still owns final selection

## 3. Public surface

```python
from ai_video.planning import (
    VideoPlanner,
    VideoPlanningRequest,
    VideoGenerationPlan,
    # enums (rarely needed by Main Agent, but useful for switch logic):
    GenerationMode,
    ContinuityMode,
    MotionRequirement,
    PlanOutcome,
    PlanWarning,
    ReasonCode,
)
```

Only `VideoPlanner.plan(request)` is callable. Everything else is data.

## 4. Call pattern

```python
from ai_video.planning import VideoPlanner

planner = VideoPlanner()  # stateless; safe to construct per-call or once
plan = planner.plan(request)
# → VideoGenerationPlan (frozen, sealed, hash-stable)
```

No constructor arguments. No context manager. No async. Sync call only.

## 5. Building `VideoPlanningRequest`

Main Agent already has the following from `ProductionProject`:

- The activated `Shot` (one of `project.shots`)
- The `Scene` (`project.scenes[shot.scene_id]`)
- The `Character` list (filter `shot.character_ids`)
- The asset registry snapshot

Main Agent **derives** `PreviousShotState` from upstream Shot context (the planner exposes `VideoPlanner.derive_previous_shot_state` for this).

### 5.1 Minimal example

```python
from ai_video.planning import (
    AvailableAsset,
    AssetRole,
    PreviousShotState,
    ProductionPolicyInput,
    VideoPlanningRequest,
)

request = VideoPlanningRequest.create(
    request_id="plan-shot-7-attempt-1",
    target_shot=project.shots["shot-7"],
    character_context=tuple(
        project.characters[c] for c in project.shots["shot-7"].character_ids
    ),
    scene_context=project.scenes[project.shots["shot-7"].scene_id],
    available_assets=(
        AvailableAsset(
            role=AssetRole.CHARACTER_REFERENCE,
            asset_id=registry.assets["ref-alice"].asset_id,
            asset_sha256=registry.assets["ref-alice"].sha256,
            mime_type="image/png",
            width=1024, height=576, size_bytes=200_000,
        ),
        AvailableAsset(
            role=AssetRole.SCENE_REFERENCE,
            asset_id=registry.assets["ref-cafe"].asset_id,
            asset_sha256=registry.assets["ref-cafe"].sha256,
            mime_type="image/png",
            width=1920, height=1080, size_bytes=800_000,
        ),
    ),
    previous_shot_state=VideoPlanner.derive_previous_shot_state(
        previous_shot=previous_shot,  # None for first Shot
        target_shot=project.shots["shot-7"],
    ),
    production_policy=ProductionPolicyInput(
        local_resources_available=True,
        remote_authorized=False,            # task-scoped only
        budget_authorized=False,
        quality_preference="production",
        accept_static_image_fallback=False,
    ),
    planning_contract_version="video-planner/1",
)

plan = VideoPlanner().plan(request)
```

### 5.2 Fields Main Agent must fill

| Field | Source |
|---|---|
| `request_id` | Main Agent's own identifier (uuid, monotonic, or `f"plan-{shot_id}-{attempt}"`) |
| `target_shot` | activated `Shot` from `ProductionProject` (no new schema) |
| `character_context` | `tuple` of `Character` matching `target_shot.character_ids` |
| `scene_context` | the single `Scene` matching `target_shot.scene_id` |
| `available_assets` | filter Asset Registry by role; project-local registry snapshot only |
| `previous_shot_state` | `VideoPlanner.derive_previous_shot_state(...)` is the canonical helper |
| `production_policy` | Main Agent task-scoped policy (do not invent) |
| `planning_contract_version` | literal `"video-planner/1"` |

## 6. Reading the plan

```python
match plan.outcome:
    case PlanOutcome.PROPOSED:
        # Plan is a hint; Production still resolves the exact capability.
        # Main Agent should:
        #   1. ensure all required_asset_roles exist in the registry;
        #      if MISSING_* warnings are present, fall back to BLOCKED handling.
        #   2. surface the capability_requirements to Production as advisory input.
        ...
    case PlanOutcome.BLOCKED:
        # Planner says: do not auto-route this Shot to a Provider.
        # Common reasons:
        #   - missing character / scene reference
        #   - missing terminal frame for EXACT_TERMINAL
        #   - hero/repair policy needed
        # Main Agent should:
        #   1. inspect plan.reason_codes and plan.warnings
        #   2. decide whether to (a) re-author Shot intent, (b) gather missing
        #      assets, or (c) escalate to user.
        ...
```

`plan.plan_hash` is stable per `target_shot_content_hash` + context; use it to dedupe replans.

## 7. What Main Agent does NOT do with the plan

- Does **not** call any Provider based on `generation_mode` alone.
- Does **not** assume any provider is available (planner is provider-neutral).
- Does **not** write plan into Manifest, Asset Registry, or any durable artifact.
- Does **not** retry the planner with mutated inputs to "force" a different mode.
- Does **not** use `plan_hash` as a Manifest receipt.

The plan is a hint passed to Production (e.g. via the future planner→router bridge). Production may accept, partially accept, or override the hint.

## 8. Worked example: Alice walks out of cafe

### Setup

- `target_shot`: `shot-7`, intent `"Alice walks out of cafe."`, visual_strategy `GENERATED_VIDEO`, character_ids `("alice",)`, scene_id `"scene-cafe"`.
- `previous_shot`: `shot-6`, same storyboard beat, intent `"Alice sits in cafe window."`, same scene, no angle change flagged by upstream.
- Asset Registry has `ref-alice` (CHARACTER_REFERENCE) and `ref-cafe` (SCENE_REFERENCE); no terminal asset for shot-6 yet (it has not been activated).

### Request

```python
request = VideoPlanningRequest.create(
    request_id="plan-shot-7",
    target_shot=project.shots["shot-7"],
    character_context=(project.characters["alice"],),
    scene_context=project.scenes["scene-cafe"],
    available_assets=(
        AvailableAsset(
            role=AssetRole.CHARACTER_REFERENCE,
            asset_id="ref-alice",
            asset_sha256=registry.assets["ref-alice"].sha256,
            mime_type="image/png",
            width=1024, height=576, size_bytes=200_000,
        ),
        AvailableAsset(
            role=AssetRole.SCENE_REFERENCE,
            asset_id="ref-cafe",
            asset_sha256=registry.assets["ref-cafe"].sha256,
            mime_type="image/png",
            width=1920, height=1080, size_bytes=800_000,
        ),
    ),
    previous_shot_state=VideoPlanner.derive_previous_shot_state(
        previous_shot=project.shots["shot-6"],
        target_shot=project.shots["shot-7"],
    ),
    production_policy=ProductionPolicyInput(),
    planning_contract_version="video-planner/1",
)
```

### Expected plan (illustrative JSON)

```json
{
  "plan_id": "3f5b2b7c-9b6f-4a8d-8c0c-4a2f7c5b3e1d",
  "target_shot_id": "shot-7",
  "target_shot_revision": 3,
  "target_shot_content_hash": "ab12...64hex",
  "generation_mode": "reference_to_video",
  "continuity_mode": "reference",
  "motion_requirement": "character_action",
  "required_asset_roles": [
    {
      "role": "character_reference",
      "reason_code": "reference_available"
    },
    {
      "role": "scene_reference",
      "reason_code": "reference_available"
    }
  ],
  "capability_requirements": {
    "needs_character_reference": true,
    "needs_scene_reference": true,
    "needs_first_frame": false,
    "needs_last_frame": false,
    "needs_terminal_reference": false,
    "needs_audio_native": false,
    "needs_continuity_state": true,
    "max_reference_count": 4,
    "min_output_duration_seconds": 3,
    "accepts_local_execution": true,
    "accepts_remote_execution": false
  },
  "reason_codes": [
    "important_character",
    "identity_required",
    "continuity_required",
    "reference_available",
    "continuity_angle_change"
  ],
  "confidence": 0.85,
  "warnings": [],
  "outcome": "proposed",
  "rationale": "Important character with references and a same-scene angle change from shot-6; reference continuity is sufficient.",
  "planning_contract_version": "video-planner/1",
  "plan_hash": "9f2e...64hex"
}
```

### Main Agent interpretation

- `outcome = proposed` and `generation_mode = reference_to_video` → proceed.
- `required_asset_roles` are both present in the registry → no asset gap.
- `warnings` is empty → no escalation needed.
- Hand off to Production with the plan attached as advisory; Production still chooses the exact Provider / capability.

### Worked example: no references for important character

#### Setup

Same `shot-7`, but Registry has no `ref-alice` yet (Alice's reference pack is not yet imported).

#### Expected plan

```json
{
  "plan_id": "9e8a...uuid",
  "target_shot_id": "shot-7",
  "generation_mode": "reference_to_video",
  "continuity_mode": "reference",
  "outcome": "blocked",
  "reason_codes": ["missing_references", "no_character_reference"],
  "warnings": ["missing_character_reference"],
  "confidence": 0.6,
  "rationale": "Important character requires a character reference; none is available in the registry.",
  "plan_hash": "..."
}
```

#### Main Agent interpretation

- `outcome = blocked` → do **not** invoke Provider with T2V fallback.
- `warnings = ["missing_character_reference"]` → escalate to user or trigger the Asset import workflow before retrying.
- `plan_hash` is stable: a re-plan after importing `ref-alice` will produce a different plan_hash.

## 9. Failure modes Main Agent must handle

| Failure | Source | What Main Agent does |
|---|---|---|
| `pydantic.ValidationError` on `VideoPlanningRequest.create(...)` | Caller passed malformed `Shot` / asset / scene | Fix inputs; do not retry |
| `plan.outcome = BLOCKED` with `MISSING_*` warnings | Planner detected missing anchors | Run Asset import / re-author intent / escalate |
| `plan.confidence < 0.6` | Planner sees ambiguous state | Inspect `reason_codes` and `warnings`; consider re-asking user |
| Plan hash changes between attempts | Underlying inputs changed | Re-route with new plan; do not assume determinism across content edits |
| Provider cannot satisfy `capability_requirements` | Production reports BLOCKED_CAPABILITY | Main Agent decides: relax constraints (e.g. drop `accepts_remote_execution`), switch Shot, or accept degraded mode |

## 10. Ordering relative to other AI-VIDEO components

```
Main Agent
  ├─ hell-grind-aigc-skill   (creative intent, continuity state)
  ├─ higgsfield              (model-specific prompt adaptation; advisory)
  ├─ VideoPlanner.plan       (generation strategy; provider-neutral)
  ├─ AI-VIDEO Production
  │    ├─ ShotVisualResolver (provider-aware routing, uses VideoProviderCapabilities)
  │    ├─ VideoProvider      (local / remote execution)
  │    ├─ ProductionStateCommitter (canonical write)
  │    └─ HyperFrames        (default render)
  └─ video-shotcraft         (motion design, beat sync; advisory)
```

The planner sits **after** hell-grind (semantic intent established) and **before** AI-VIDEO Production. It does not import higgsfield or video-shotcraft; those remain advisory and are invoked separately.

## 11. Migration & rollout

- Slice is additive; no existing module changes.
- Land as a single PR per the two-PR plan in `tasks.md` (T1–T9 → PR1; T10–T14 → PR2).
- Old routing path is untouched; Production continues to use `ShotVisualResolver` without the planner.
- Optional Main Agent integration: enable `planner → router` bridge after D1 lands.

## 12. References

- `requirements.md` — acceptance criteria
- `design.md` — module design, schema, algorithm
- `tasks.md` — staged implementation plan
- `test-spec.md` — test cases
- `src/ai_video/planning/` — module (post-merge)
- `tests/test_planning_video_planner.py` — tests (post-merge)