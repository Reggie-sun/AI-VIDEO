# Video Planner Subagent — Design

Status: proposed v2 (paired with `requirements.md`)
Owner: AI-VIDEO planning intelligence layer
Module path: `src/ai_video/planning/`

## 1. Position in the architecture

```text
approved AI-VIDEO Shot / Asset / Review truth
  -> Main Agent builds sealed per-Shot request projections
  -> VideoPlanner.plan()                         # pure, provider-neutral
  -> Main Agent current-plan consumer / STOP    # executable preflight seam
  -> existing AI-VIDEO Provider / Asset execution
  -> Composition -> Review -> human Pilot Reality Gate
```

The planner sits outside Production. Production modules MUST NOT import `ai_video.planning`. The Main Agent calls planner and consumes its result before invoking existing Production entry points. `Shot.visual_strategy` is a declared strategy to validate, not the source of motion truth.

## 2. Package layout

```text
src/ai_video/planning/
├── __init__.py
├── _planner_models.py
└── video_planner.py

tests/
├── fixtures/planning_factory.py
└── test_planning_video_planner.py
```

This is planned layout only. This docs slice does not create runtime files.

## 3. Import boundary

Allowed imports:

- `ai_video.production.models`: read-only `Shot`, `Character`, `Scene`, `StrictModel`, `VisualStrategy`, `AssetType`, `AssetRoleRequirement`, `MotionDirective`;
- `ai_video.production.hashing`: canonical hashing/sealing helpers;
- `ai_video.errors`: typed error definitions;
- standard library and pydantic.

Forbidden imports:

- Production state writers, Manifest, Registry, dependency, composition, HyperFrames, timeline, Provider adapters, CLI, ComfyUI/ffmpeg transports;
- `os.environ`, network clients, subprocess, keyring or other secret surfaces.

An Architecture Gate also asserts that Production does not import `ai_video.planning`.

## 4. Request projections

All models are frozen and `extra="forbid"`. Every semantic request projection participates in `request_content_hash`; they are immutable projections of existing AI-VIDEO truth, not new durable owners.

`request_content_hash` excludes only `request_id` and the hash field itself; `request_id` is diagnostic correlation, not semantic input. Rebuilding an otherwise identical request with a new diagnostic id must not change the plan.

### 4.1 `VideoPlanningRequest`

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

`target_shot` must be the current activated/selected canonical Shot revision supplied by the caller. The planner itself does not read Production state.

### 4.2 `ShotIntentEvidence`

```python
class ShotIntentEvidence(StrictModel):
    target_shot_id: str
    target_shot_content_hash: str
    open_state_ref: str | None = None
    close_state_ref: str | None = None
    character_action_required: bool = False
    continuous_action_required: bool = False
    spatial_change_required: bool = False
    state_change_required: bool = False
    subject_motion_directive_present: bool = False
    evidence_unresolved: bool = False
```

Main Agent derives this projection from approved Shot intent, Storyboard/continuity constraints, open/close state, and typed motion directives. `open_state_ref` / `close_state_ref` identify existing evidence; they do not duplicate full creative state. Natural-language keyword matching MUST NOT set the action booleans. If approved typed evidence cannot resolve a prose intent, set `evidence_unresolved=True` and require review.

`requires_subject_motion` is true when any action/change boolean or `subject_motion_directive_present` is true.

### 4.3 `AvailableAsset`

```python
class AssetRole(str, Enum):
    CHARACTER_REFERENCE = "character_reference"
    SCENE_REFERENCE = "scene_reference"
    PREVIOUS_SHOT_TERMINAL = "previous_shot_terminal"
    APPROVED_KEYFRAME = "approved_keyframe"
    APPROVED_REUSABLE_PLATE = "approved_reusable_plate"
    EXISTING_VIDEO = "existing_video"

class AvailableAsset(StrictModel):
    role: AssetRole
    asset_id: str
    asset_sha256: str
    canonical_owner_id: str | None
    mime_type: str
    width: int | None = None
    height: int | None = None
    size_bytes: int | None = None
```

Role semantics:

- `CHARACTER_REFERENCE` / `SCENE_REFERENCE`: identity/state/space/style guidance only; never Final Shot Visual readiness.
- `APPROVED_KEYFRAME`: satisfies Final Shot Visual only when `canonical_owner_id == target_shot.shot_id` and target Shot canonical `required_asset_roles` binds the exact asset id to its final-visual role.
- `APPROVED_REUSABLE_PLATE`: satisfies Final Shot Visual only with the same exact target-Shot binding plus a matching current `ReviewDecisionProjection` that allows reuse and provides rationale.
- `PREVIOUS_SHOT_TERMINAL`: continuity input for `EXACT_TERMINAL`, not a generic final visual for unrelated Shots.

### 4.4 `ReviewDecisionProjection`

```python
class ReviewDecisionProjection(StrictModel):
    evidence_ref: str
    target_shot_id: str
    target_shot_content_hash: str
    rationale: str
    allows_intentional_static: bool = False
    allows_static_fallback: bool = False
    allows_reusable_plate: bool = False
```

`evidence_ref` must identify the exact current canonical AI-VIDEO Review/director evidence used by Main Agent. This is an ephemeral pointer/summary; planner neither creates nor persists approval. It is current only when the evidence identity and Shot id/hash match the freshly built request. Missing, revoked, replaced or mismatched evidence changes `request_content_hash` and invalidates the old plan.

### 4.5 `PreviousShotState`

```python
class PreviousShotState(StrictModel):
    previous_shot_id: str | None
    previous_shot_content_hash: str | None
    is_same_scene: bool
    is_same_story_beat: bool
    is_same_action: bool
    is_angle_change: bool
    has_terminal_frame_asset_id: str | None
    semantic_jump: bool
```

### 4.6 `ProductionPolicyInput`

```python
class ProductionPolicyInput(StrictModel):
    local_resources_available: bool = True
    remote_authorized: bool = False
    budget_authorized: bool = False
    quality_preference: Literal["draft", "preview", "production", "hero"] = "production"
    accept_static_image_fallback: bool = False
```

`accept_static_image_fallback` is an algorithm input, not a comment or Production override hint.

## 5. Plan schemas

### 5.1 Strategy enums

```python
class GenerationMode(str, Enum):
    STATIC_IMAGE = "static_image"
    IMAGE_MOTION = "image_motion"
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"
    FIRST_LAST_FRAME_VIDEO = "first_last_frame_video"
    REFERENCE_TO_VIDEO = "reference_to_video"
    HYBRID = "hybrid"

class ContinuityMode(str, Enum):
    EXACT_TERMINAL = "exact_terminal"
    REFERENCE = "reference"
    SEMANTIC = "semantic"
    NONE = "none"

class MotionRequirement(str, Enum):
    NONE = "none"
    LIGHT_TRANSFORM = "light_transform"
    GRAPHIC = "graphic"
    CHARACTER_ACTION = "character_action"
    FREE_COMPLEX = "free_complex"
    HERO_OR_REPAIR = "hero_or_repair"
```

`pan`, `zoom`, `zoompan`, and `parallax` are camera/image transforms. By themselves they can support `LIGHT_TRANSFORM`, but can never satisfy `CHARACTER_ACTION` or a required open→close subject-state transition.

### 5.2 Typed audit values

Keep v1 reason/warning values and add:

```python
class ReasonCode(str, Enum):
    # v1 identity / continuity / availability values omitted here for brevity
    ACTION_INTENT_REQUIRED = "action_intent_required"
    STRATEGY_MOTION_MISMATCH = "strategy_motion_mismatch"
    CAMERA_MOTION_ONLY = "camera_motion_only"
    FINAL_SHOT_VISUAL_REQUIRED = "final_shot_visual_required"
    FINAL_SHOT_VISUAL_AVAILABLE = "final_shot_visual_available"
    REUSABLE_PLATE_APPROVED = "reusable_plate_approved"
    INTENTIONAL_STATIC = "intentional_static"
    STATIC_FALLBACK_ACCEPTED = "static_fallback_accepted"

class PlanWarning(str, Enum):
    # v1 missing-reference / terminal / low-confidence values omitted
    FINAL_SHOT_VISUAL_MISSING = "final_shot_visual_missing"
    CAMERA_MOTION_NOT_SUBJECT_MOTION = "camera_motion_not_subject_motion"
    STATIC_FALLBACK_REQUIRES_REVIEW = "static_fallback_requires_review"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"
```

### 5.3 `VideoGenerationPlan`

```python
class PlanOutcome(str, Enum):
    PROPOSED = "proposed"
    BLOCKED = "blocked"

class RequiredAssetRole(StrictModel):
    role: AssetRole
    reason_code: ReasonCode

class VideoGenerationPlan(StrictModel):
    plan_id: str  # deterministic: f"plan-{request_content_hash[:24]}"
    source_request_content_hash: str
    target_shot_id: str
    target_shot_revision: int
    target_shot_content_hash: str
    generation_mode: GenerationMode
    continuity_mode: ContinuityMode
    motion_requirement: MotionRequirement
    required_asset_roles: tuple[RequiredAssetRole, ...]
    capability_requirements: CapabilityRequirements
    reason_codes: tuple[ReasonCode, ...]
    confidence: float
    warnings: tuple[PlanWarning, ...]
    outcome: PlanOutcome
    rationale: str
    planning_contract_version: Literal["video-planner/2"]
    plan_hash: str
```

No third outcome is needed. `BLOCKED` plus typed warnings expresses unresolved mismatch/review. `PROPOSED` remains deliberately narrow and is not a creative PASS.

Forbidden fields include Provider selection, paths, Manifest/timeline state, generated/reviewed/selected/locked/activated/final-acceptance flags, and Review receipt payloads.

## 6. Algorithm

`VideoPlanner.plan()` runs in this order. Reordering these stages is a contract violation because it can recreate the static-first self-certification loop.

### Stage 1 — Validate current evidence

- `ShotIntentEvidence.target_shot_id/content_hash` must match target Shot; otherwise `BLOCKED`.
- Review projection counts only when its Shot id/hash match.
- Classify available assets by role, owner, exact target-Shot canonical binding, and current reuse approval.
- If `evidence_unresolved=True`, add `REQUIRES_HUMAN_REVIEW`; do not keyword-guess motion.

### Stage 2 — Derive continuity

```text
first Shot                         -> NONE
semantic jump / explicit reset    -> SEMANTIC
same action, no angle change      -> EXACT_TERMINAL
angle change                      -> REFERENCE
otherwise                         -> REFERENCE
```

Only `EXACT_TERMINAL` requires terminal reference capability.

### Stage 3 — Derive required motion independently

1. If typed intent evidence requires subject motion, return `CHARACTER_ACTION` (or `HERO_OR_REPAIR` when explicitly classified upstream).
2. Else if `Shot.motion_directives` contain subject animation/non-transform motion, return `CHARACTER_ACTION`.
3. Else if directives contain only pan/zoom/zoompan/parallax, return `LIGHT_TRANSFORM` and record `CAMERA_MOTION_ONLY`.
4. Else `MOTION_GRAPHICS` maps to `GRAPHIC`; coherent explicit static maps to `NONE`; otherwise generated/hybrid intent maps to `FREE_COMPLEX`.

`Shot.visual_strategy` may constrain the declared lane, but cannot erase a motion requirement derived in steps 1–2.

### Stage 4 — Coherence and fallback gate

Let `declared_static_lane` mean `STATIC_IMAGE` or `IMAGE_MOTION` whose directives are camera-only.

| Required intent/motion | Declared lane | Policy/evidence | Result |
|---|---|---|---|
| subject action/change | static lane | `accept_static_image_fallback=False` | `BLOCKED`, mismatch + review |
| subject action/change | static lane | fallback true but no matching Review decision/final visual/rationale | `BLOCKED` |
| subject action/change | static lane | fallback true + matching Review allows fallback + final visual ready + rationale | `PROPOSED`, fallback reasons/warning; never creative PASS |
| no subject action/change | `STATIC_IMAGE` | Shot-specific keyframe + intentional-static rationale | `PROPOSED` |
| no subject action/change | `IMAGE_MOTION` | Shot-specific keyframe or approved reusable plate + rationale | `PROPOSED` |
| any static/image-motion | no Final Shot Visual | any | `BLOCKED`, `FINAL_SHOT_VISUAL_MISSING` |

The action-fallback proposal includes `STATIC_FALLBACK_REQUIRES_REVIEW` even when matching review evidence is present, preserving audit visibility. Add unresolved `REQUIRES_HUMAN_REVIEW` only when current approval is absent/invalid, which forces the Main Agent STOP seam.

### Stage 5 — Dynamic generation decision

After the coherence/fallback gate, use identity × continuity × available reference/terminal evidence:

| Continuity | Important character? | Evidence | Mode |
|---|---|---|---|
| `NONE` | no | no explicit motion contradiction | `TEXT_TO_VIDEO` |
| `NONE` | yes | character + scene refs | `REFERENCE_TO_VIDEO` |
| `NONE` | yes | no visual anchor | `BLOCKED` |
| `EXACT_TERMINAL` | any | current upstream terminal | `IMAGE_TO_VIDEO` or `FIRST_LAST_FRAME_VIDEO` |
| `EXACT_TERMINAL` | any | terminal missing | `BLOCKED` |
| `REFERENCE` / `SEMANTIC` | yes | character + scene refs | `REFERENCE_TO_VIDEO` |
| `REFERENCE` / `SEMANTIC` | yes | required refs missing | `BLOCKED` |
| `SEMANTIC` | no | no explicit identity anchor required | `TEXT_TO_VIDEO` |

`GRAPHIC` maps to `HYBRID`. `HERO_OR_REPAIR` is `BLOCKED` with human review. Dynamic mode selection never names a Provider.

### Stage 6 — Required assets and capability

- `REFERENCE_TO_VIDEO`: required Character/Scene reference roles.
- `IMAGE_TO_VIDEO` / `FIRST_LAST_FRAME_VIDEO`: exact terminal for `EXACT_TERMINAL`, otherwise Shot-specific `APPROVED_KEYFRAME`.
- `STATIC_IMAGE` / `IMAGE_MOTION`: `APPROVED_KEYFRAME` or `APPROVED_REUSABLE_PLATE`; reference roles alone never satisfy this requirement.
- `TEXT_TO_VIDEO`: no asset role unless canonical Shot bindings require one.
- `HYBRID`: derive existing layer/visual requirements without creating a second composition schema.

The plan records required roles. Main Agent consumer separately verifies exact assets are still present/current before execution.

### Stage 7 — Reasons, warnings, confidence

- Every branch emits typed reasons consistent with chosen mode/outcome.
- `rationale` is assembled from deterministic templates keyed by typed reasons; it is not LLM/free-form output.
- Clear dynamic table match with all evidence may be high confidence.
- Intentional-static or action-fallback paths are never assigned automatic `1.0` merely because `visual_strategy` declared static.
- `confidence` never overrides `BLOCKED`, missing assets, stale identity, or a human-review warning.

## 7. Main Agent consumer contract

The minimum executable seam is a pure/locally testable Main Agent function, conceptually:

```python
def require_current_video_plan(*, current_request: VideoPlanningRequest,
                               plan: VideoGenerationPlan) -> None:
    """Return only when downstream Production invocation is eligible; otherwise raise typed STOP."""
```

It must fail closed on:

- `plan.source_request_content_hash != current_request.request_content_hash`; the caller must freshly rebuild `current_request` from current Shot, asset binding, Review decision and policy projections before consumption;
- Shot id/revision/content hash mismatch;
- `PlanOutcome.BLOCKED`;
- missing required asset, wrong owner, or missing exact canonical binding;
- unresolved `REQUIRES_HUMAN_REVIEW`.

On failure, router/Provider/placeholder/materializer/composition/render must not be called. On success, it only authorizes handoff to existing Production gates; it does not activate or accept anything. The consumer stays on the Main Agent/planning side, so Production does not gain a reverse dependency.

## 8. API and public surface

`VideoPlanner` is stateless:

```python
class VideoPlanner:
    CONTRACT_VERSION = "video-planner/2"

    def plan(self, request: VideoPlanningRequest) -> VideoGenerationPlan: ...

    @staticmethod
    def derive_previous_shot_state(*, previous_shot: Shot | None,
                                   target_shot: Shot) -> PreviousShotState: ...
```

Public exports may include the request/plan projection models and enums defined above. No Provider converter is called by planner. A future D1 hint projection may live outside Production, but is not the STOP gate.

## 9. Failure handling

- malformed request → pydantic `ValidationError`;
- stale/mismatched intent/review evidence → `BLOCKED`;
- `EXISTING_VIDEO` outside accepted planning path → `BLOCKED`, explicit rationale;
- conflicting or unresolved evidence → `BLOCKED` + `LOW_CONFIDENCE`/`REQUIRES_HUMAN_REVIEW`;
- never invent a strategy, mutate Shot, render placeholder, or auto-fallback.

## 10. Compatibility and ownership

- No existing Production public API, schema, Manifest, Registry, timeline, renderer or Provider change.
- No new dependency or CLI flag.
- Planner consumes one Shot at a time; D3 multi-Shot planning remains out of scope.
- Repetition/frame-diversity/Pilot/full-watch/Final Acceptance remain Review/Pilot concerns.

## 11. Testing

Tests must cover AC-1～AC-18, especially the real static-first mismatch, camera-only zoompan boundary, fallback policy, reference-vs-final role, and Main Agent zero-call STOP seam. See `test-spec.md`; delivery ordering and traceability are in `tasks.md`.

## 12. Risk controls

| Risk | Control |
|---|---|
| `visual_strategy` self-certifies wrong bootstrap | derive motion first from typed intent/open-close/directives, then check coherence |
| reference is reused as final image | exact target-Shot final-role binding + owner/reuse rationale checks |
| fallback true becomes automatic downgrade | matching Review projection and final visual required; audit warning retained |
| `BLOCKED` is ignored | mandatory Main Agent consumer + zero-call spies |
| planner grows into quality gate | single-Shot scope; Review/Pilot explicitly retain aggregate/final quality |
| planner becomes Production owner | import gate, no IO, no durable state, no reverse Production import |
