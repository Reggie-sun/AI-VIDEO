# Video Planner Subagent — Design

Status: draft v1 (paired with `requirements.md`)
Owner: AI-VIDEO planning intelligence layer
Module path: `src/ai_video/planning/` (new package)

## 1. Position in the architecture

```
                ┌──────────────────────────────┐
                │       Main Agent / Codex     │
                └──────────────┬───────────────┘
                               │ planning call
                               ▼
        ┌──────────────────────────────────────────┐
        │   planning.video_planner.VideoPlanner    │  ◀── NEW
        │   pure function, no IO, no Provider      │
        │   returns VideoGenerationPlan            │
        └──────────────┬───────────────────────────┘
                       │ hint (not binding)
                       ▼
        ┌──────────────────────────────────────────┐
        │   production.shot_router.ShotVisualResolver │
        │   + VideoGenerationResolver              │  (existing, untouched)
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │   production.video.VideoProvider         │
        │   HyperFrames / state_commit / timeline   │  (canonical owners)
        └──────────────────────────────────────────┘
```

**This module sits OUTSIDE production** and **BEFORE** `ShotVisualResolver`. Its output is advisory; Production retains final authority.

## 2. Package layout

```
src/ai_video/planning/
├── __init__.py                 # public surface only
├── video_planner.py            # VideoPlanner, plan(), dataclasses
└── _planner_models.py          # pydantic StrictModel subclasses (sealed)

tests/
└── test_planning_video_planner.py
```

Files MUST stay under 800 lines (per AGENTS.md coding standards). Each file under 400 lines.

## 3. Module imports — whitelist & blacklist

### Allowed imports (whitelist)

- `ai_video.production.models` — `Shot`, `Character`, `Scene`, `StrictModel`, `VisualStrategy`, `AssetType`, `AssetRoleRequirement`, `MotionDirective`, `VersionedArtifact`
- `ai_video.production.hashing` — `canonical_sha256`, `seal_artifact`, `verify_artifact_hash`
- `ai_video.errors` — `AiVideoError`, `ErrorCode`
- Standard library + pydantic

### Forbidden imports (blacklist, enforced by Architecture Gate)

- `ai_video.production.state_commit` and any `_state_commit_*`
- `ai_video.production.dependency`
- `ai_video.production.composition`
- `ai_video.production.hyperframes`
- `ai_video.production.manifest`
- `ai_video.production.registry` (read paths allowed only inside `ProductionProject`; planner receives snapshots via `VideoPlanningRequest`)
- `ai_video.production.video` (the producer, not the schema)
- `ai_video.production.seedance` / `seedance_capabilities` / `seedance_profile` / `seedance_asset`
- `ai_video.production.minimax_h3` / `minimax_hailuo` / `minimax_speech` / `elevenlabs`
- `ai_video.comfy_client`
- `ai_video.ffmpeg_tools`
- `ai_video.cli`
- `os.environ`, `subprocess`, `httpx`, `requests`, `urllib`
- `keyring`, `cryptography.hazmat.primitives.kdf` (anything secret-shaped)

> The blacklist is enforced by `tests/test_architecture_gate.py` through AST inspection of `src/ai_video/planning/`. Any new import requires an explicit extension in that test.

## 4. Schemas

### 4.1 `VideoPlanningRequest`

A sealed wrapper that bundles inputs the Main Agent already has access to. **No new schema for Shot / Character / Scene** — reuse.

```python
class VideoPlanningRequest(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str                       # uuid or content-hash-prefixed id
    target_shot: Shot                     # the activated Shot
    character_context: tuple[Character, ...]    # only important characters
    scene_context: Scene                          # exact scene of the Shot
    available_assets: tuple[AvailableAsset, ...]  # see 4.2
    previous_shot_state: PreviousShotState | None  # see 4.3
    production_policy: ProductionPolicyInput       # see 4.4
    planning_contract_version: Literal["video-planner/1"]
    request_content_hash: str                     # sha256 of sealed payload

    @classmethod
    def create(cls, **values) -> "VideoPlanningRequest": ...
```

### 4.2 `AvailableAsset`

```python
class AssetRole(str, Enum):
    CHARACTER_REFERENCE = "character_reference"
    SCENE_REFERENCE = "scene_reference"
    PREVIOUS_SHOT_TERMINAL = "previous_shot_terminal"
    APPROVED_KEYFRAME = "approved_keyframe"
    EXISTING_VIDEO = "existing_video"

class AvailableAsset(StrictModel):
    role: AssetRole
    asset_id: str                        # pattern _SAFE_ID
    asset_sha256: str                    # 64-hex
    canonical_owner_id: str | None       # character / scene id if applicable
    mime_type: str
    width: int | None = None
    height: int | None = None
    size_bytes: int | None = None
```

### 4.3 `PreviousShotState`

```python
class PreviousShotState(StrictModel):
    previous_shot_id: str | None         # None = first shot in project
    previous_shot_content_hash: str | None
    is_same_scene: bool
    is_same_story_beat: bool
    is_same_action: bool                 # True → continuity candidate
    is_angle_change: bool                # True → reference continuity candidate
    has_terminal_frame_asset_id: str | None
    semantic_jump: bool                  # True → semantic continuity
```

All bool flags are mutually compatible (the planner uses them, doesn't enforce exclusivity).

### 4.4 `ProductionPolicyInput`

```python
class ProductionPolicyInput(StrictModel):
    local_resources_available: bool = True
    remote_authorized: bool = False       # task-scoped only
    budget_authorized: bool = False
    quality_preference: Literal[
        "draft", "preview", "production", "hero"
    ] = "production"
    accept_static_image_fallback: bool = False   # production owner may override
```

### 4.5 `GenerationMode`

```python
class GenerationMode(str, Enum):
    STATIC_IMAGE = "static_image"
    IMAGE_MOTION = "image_motion"
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"
    FIRST_LAST_FRAME_VIDEO = "first_last_frame_video"
    REFERENCE_TO_VIDEO = "reference_to_video"
    HYBRID = "hybrid"
```

Note: the 7th "hybrid" covers `motion_graphics` + planned overlays. The planner emits `hybrid` when motion is graphic and Shot says `VisualStrategy.MOTION_GRAPHICS`.

### 4.6 `ContinuityMode`

```python
class ContinuityMode(str, Enum):
    EXACT_TERMINAL = "exact_terminal"
    REFERENCE = "reference"
    SEMANTIC = "semantic"
    NONE = "none"
```

Mirrors `production.shot_router.ContinuityMode` semantically but **is a distinct enum** — different module, different owner. A converter helper lives next to the planner (`def to_router_continuity_mode(p: PlannerContinuityMode) -> RouterContinuityMode`) but is not invoked inside the planner.

### 4.7 `MotionRequirement`

```python
class MotionRequirement(str, Enum):
    NONE = "none"
    LIGHT_TRANSFORM = "light_transform"
    GRAPHIC = "graphic"
    CHARACTER_ACTION = "character_action"
    FREE_COMPLEX = "free_complex"
    HERO_OR_REPAIR = "hero_or_repair"
```

### 4.8 `AssetRole` (in plan)

```python
class RequiredAssetRole(StrictModel):
    role: AssetRole
    reason_code: ReasonCode
```

### 4.9 `CapabilityRequirements`

```python
class CapabilityRequirements(StrictModel):
    needs_character_reference: bool = False
    needs_scene_reference: bool = False
    needs_first_frame: bool = False
    needs_last_frame: bool = False
    needs_terminal_reference: bool = False
    needs_audio_native: bool = False
    needs_continuity_state: bool = False
    max_reference_count: int | None = Field(default=None, ge=0, le=8)
    min_output_duration_seconds: int | None = Field(default=None, ge=1, le=600)
    accepts_local_execution: bool = True
    accepts_remote_execution: bool = True
```

### 4.10 `ReasonCode`

```python
class ReasonCode(str, Enum):
    IMPORTANT_CHARACTER = "important_character"
    IDENTITY_REQUIRED = "identity_required"
    CONTINUITY_REQUIRED = "continuity_required"
    REFERENCE_AVAILABLE = "reference_available"
    TERMINAL_AVAILABLE = "terminal_available"
    NO_CHARACTER_REFERENCE = "no_character_reference"
    NO_SCENE_REFERENCE = "no_scene_reference"
    NO_VISUAL_ANCHOR = "no_visual_anchor"
    FREE_ENVIRONMENT = "free_environment"
    FIRST_SHOT = "first_shot"
    SEMANTIC_JUMP = "semantic_jump"
    MOTION_NONE = "motion_none"
    MOTION_LIGHT = "motion_light"
    MOTION_GRAPHIC = "motion_graphic"
    MOTION_HERO_REQUIRES_POLICY = "motion_hero_requires_policy"
    MISSING_TERMINAL = "missing_terminal"
    MISSING_REFERENCES = "missing_references"
    CONTINUITY_ANGLE_CHANGE = "continuity_angle_change"
    CONTINUITY_SAME_ACTION = "continuity_same_action"
```

### 4.11 `PlanWarning`

```python
class PlanWarning(str, Enum):
    MISSING_CHARACTER_REFERENCE = "missing_character_reference"
    MISSING_SCENE_REFERENCE = "missing_scene_reference"
    MISSING_TERMINAL_FRAME = "missing_terminal_frame"
    LOW_CONFIDENCE = "low_confidence"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"
```

### 4.12 `VideoGenerationPlan`

```python
class PlanOutcome(str, Enum):
    PROPOSED = "proposed"
    BLOCKED = "blocked"

class VideoGenerationPlan(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    plan_id: str                          # uuid
    target_shot_id: str
    target_shot_revision: int
    target_shot_content_hash: str
    generation_mode: GenerationMode
    continuity_mode: ContinuityMode
    motion_requirement: MotionRequirement
    required_asset_roles: tuple[RequiredAssetRole, ...]
    capability_requirements: CapabilityRequirements
    reason_codes: tuple[ReasonCode, ...] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: tuple[PlanWarning, ...] = ()
    outcome: PlanOutcome
    rationale: str                        # min_length=1
    planning_contract_version: Literal["video-planner/1"]
    plan_hash: str                        # sha256 over canonical payload

    @classmethod
    def create(cls, **values) -> "VideoGenerationPlan": ...
```

### 4.13 Forbidden fields guard

`VideoGenerationPlan` uses `extra="forbid"`. A separate test injects a forbidden field via `model_construct` to verify rejection. The forbidden list (in tests/test_architecture_gate.py):

- `provider_name`, `provider_kind`, `provider_profile`, `selected_provider`
- `selected_capability_id`, `selected_mode`, `selected_provider_profile`
- `manifest_revision`, `timeline_position`, `asset_path`, `artifact_path`
- `output_asset_id`, `input_artifact_ids`

## 5. Algorithm

The planner is a single pure function `VideoPlanner.plan(request) -> VideoGenerationPlan`. It runs in 6 stages:

### Stage 1 — Identity & scene classification

```
is_character_important   = len(target_shot.character_ids) > 0
is_environment_shot      = not is_character_important
is_first_shot            = previous_shot_state is None
is_semantic_jump         = previous_shot_state.semantic_jump
```

### Stage 2 — Continuity decision

```
if is_first_shot:
    continuity_mode = NONE
elif is_semantic_jump:
    continuity_mode = SEMANTIC
elif previous_shot_state.is_same_action and not previous_shot_state.is_angle_change:
    continuity_mode = EXACT_TERMINAL
elif previous_shot_state.is_angle_change:
    continuity_mode = REFERENCE
else:
    continuity_mode = REFERENCE   # default safe choice for non-first Shot
```

### Stage 3 — Motion classification

Mapped from `Shot.motion_directives` + `Shot.visual_strategy`:

| `Shot.visual_strategy` | motion_requirement |
|---|---|
| `STATIC_IMAGE` | `NONE` |
| `IMAGE_MOTION` | `LIGHT_TRANSFORM` |
| `MOTION_GRAPHICS` | `GRAPHIC` |
| `EXISTING_VIDEO` | `NONE` (returns EXISTING_VIDEO outcome; not in this slice) |
| `GENERATED_VIDEO` | derive from `motion_directives` |
| `HYBRID` | derive per directive mix |

For `GENERATED_VIDEO` heuristic:

- 0 directives → `FREE_COMPLEX`
- only `pan` / `zoom` / `parallax` → `LIGHT_TRANSFORM`
- otherwise → `CHARACTER_ACTION`

If `motion_requirement = HERO_OR_REPAIR` → blocked outcome by default.

### Stage 4 — Generation mode decision

The decision table combines identity × continuity × motion × available assets:

| Continuity | Important char? | has_char_ref | has_scene_ref | has_terminal | Mode |
|---|---|---|---|---|---|
| `NONE` | no | n/a | n/a | n/a | `TEXT_TO_VIDEO` (free environment) |
| `NONE` | yes | yes | yes | n/a | `REFERENCE_TO_VIDEO` |
| `NONE` | yes | no | n/a | n/a | **BLOCKED** (no visual anchor) |
| `EXACT_TERMINAL` | yes | n/a | n/a | yes | `IMAGE_TO_VIDEO` (use terminal as first frame) |
| `EXACT_TERMINAL` | yes | n/a | n/a | no | **BLOCKED** (missing terminal) |
| `REFERENCE` | yes | yes | yes | n/a | `REFERENCE_TO_VIDEO` |
| `REFERENCE` | yes | no | n/a | n/a | **BLOCKED** (MISSING_REFERENCES) |
| `SEMANTIC` | yes | yes | yes | n/a | `REFERENCE_TO_VIDEO` |
| `SEMANTIC` | no | n/a | n/a | n/a | `TEXT_TO_VIDEO` |

Overrides:

- `motion_requirement = NONE` → `STATIC_IMAGE` regardless of continuity
- `motion_requirement = LIGHT_TRANSFORM` → `IMAGE_MOTION` regardless
- `motion_requirement = GRAPHIC` → `HYBRID` (or planner returns `MOTION_GRAPHICS` in rationale)
- `motion_requirement = HERO_OR_REPAIR` → **BLOCKED** with `REQUIRES_HUMAN_REVIEW` warning

The override branches run before the decision table; the override path is itself a valid generation_mode selection.

### Stage 5 — Required assets & capability

`required_asset_roles` is built from the chosen mode:

- `REFERENCE_TO_VIDEO`: `(CHARACTER_REFERENCE, SCENE_REFERENCE)` — one each
- `IMAGE_TO_VIDEO` / `FIRST_LAST_FRAME_VIDEO`: `PREVIOUS_SHOT_TERMINAL` (if `EXACT_TERMINAL`) or `APPROVED_KEYFRAME`
- `TEXT_TO_VIDEO`: empty (no assets required)
- `IMAGE_MOTION`: `APPROVED_KEYFRAME`
- `STATIC_IMAGE`: empty (caller can still add references if Shot says so)

`capability_requirements` flags:

- `needs_character_reference` = `any(role == CHARACTER_REFERENCE for role in required_asset_roles)`
- `needs_scene_reference` = `any(role == SCENE_REFERENCE for role in required_asset_roles)`
- `needs_terminal_reference` = `continuity_mode == EXACT_TERMINAL and outcome == PROPOSED`
- `needs_first_frame` = `generation_mode in {IMAGE_TO_VIDEO, FIRST_LAST_FRAME_VIDEO}`
- `needs_last_frame` = `generation_mode == FIRST_LAST_FRAME_VIDEO`
- `needs_continuity_state` = `continuity_mode in {REFERENCE, SEMANTIC}`
- `accepts_local_execution` = `production_policy.local_resources_available`
- `accepts_remote_execution` = `production_policy.remote_authorized and production_policy.budget_authorized`

### Stage 6 — Reason codes, confidence, warnings

- `reason_codes` is built incrementally as overrides + decision + capability flags fire.
- `confidence`:

| Condition | confidence |
|---|---|
| Override path (NONE / LIGHT) | 1.0 |
| Decision table single match, all required refs present | 0.9 |
| Decision table single match, refs inferred from policy | 0.75 |
| Multiple alternatives plausible (e.g. ref + terminal both available) | 0.6 |
| Blocked with one clear cause | 0.9 |
| Blocked with multiple reasons | 0.5 |

- `warnings` additively:

  - `MISSING_CHARACTER_REFERENCE` if `IMPORTANT_CHARACTER` is in reason_codes and no character asset is in `required_asset_roles`
  - `MISSING_SCENE_REFERENCE` analogously
  - `MISSING_TERMINAL_FRAME` if `EXACT_TERMINAL` and no terminal available
  - `LOW_CONFIDENCE` if `confidence < 0.6`
  - `REQUIRES_HUMAN_REVIEW` if outcome is BLOCKED or motion is HERO_OR_REPAIR

## 6. `VideoPlanner` API

```python
class VideoPlanner:
    """Provider-neutral Video Planning Intelligence Layer."""

    CONTRACT_VERSION: Literal["video-planner/1"] = "video-planner/1"

    def plan(self, request: VideoPlanningRequest) -> VideoGenerationPlan:
        """Pure function. Same request → same plan_hash."""

    @staticmethod
    def derive_previous_shot_state(
        *,
        previous_shot: Shot | None,
        target_shot: Shot,
    ) -> PreviousShotState:
        """Helper for Main Agent. Pure, deterministic."""
```

No constructor arguments; no DI; no state.

## 7. Failure handling

- If `request` is malformed → pydantic `ValidationError` (caller's responsibility).
- If `Shot.visual_strategy == EXISTING_VIDEO` → plan returns `outcome = BLOCKED` with rationale pointing to existing video path (out-of-slice; Main Agent should pick EXISTING_VIDEO outcome directly).
- If decision cannot be made cleanly (e.g. multiple conflicting overrides) → returns BLOCKED with `LOW_CONFIDENCE` warning; never invents a mode.

## 8. Performance

- O(1) wrt Shot count (single Shot per call).
- `plan_hash` computed once at end; no caching across calls.
- Target: < 5 ms per call on a single Shot. Trivial compared to Production.

## 9. Public surface (`__init__.py`)

```python
from ai_video.planning._planner_models import (
    VideoPlanningRequest,
    VideoGenerationPlan,
    AvailableAsset,
    PreviousShotState,
    ProductionPolicyInput,
    GenerationMode,
    ContinuityMode,
    MotionRequirement,
    AssetRole,
    RequiredAssetRole,
    CapabilityRequirements,
    ReasonCode,
    PlanWarning,
    PlanOutcome,
)
from ai_video.planning.video_planner import VideoPlanner

__all__ = [
    "VideoPlanner",
    "VideoPlanningRequest",
    "VideoGenerationPlan",
    "AvailableAsset",
    "PreviousShotState",
    "ProductionPolicyInput",
    "GenerationMode",
    "ContinuityMode",
    "MotionRequirement",
    "AssetRole",
    "RequiredAssetRole",
    "CapabilityRequirements",
    "ReasonCode",
    "PlanWarning",
    "PlanOutcome",
]
```

No other symbols exported. `VideoPlanner` is the only callable.

## 10. Cross-module contract

- `production.shot_router.ShotVisualResolver` may consume `VideoGenerationPlan` as advisory input — out of slice scope (a future "planner→router bridge" task).
- `production` modules MUST NOT import `ai_video.planning` (preserves ownership direction).
- `planning` modules MAY import `production.models` and `production.hashing` (read-only types & utilities).

## 11. Testing

See `tests/test_planning_video_planner.py` (in repo) for the full test suite. Coverage:

| Layer | What | Count |
|---|---|---|
| Unit | AC-1..AC-5 | 5 |
| Unit | Forbidden fields rejection | 6 |
| Unit | Pure determinism (hash stability) | 3 |
| Unit | Continuity mode matrix | 8 |
| Unit | Motion override branches | 4 |
| Unit | Schema sealing (`create()` round-trip) | 2 |
| Unit | `derive_previous_shot_state` helper | 3 |
| Architecture | import blacklist enforcement | 1 |
| Architecture | `extra="forbid"` rejection | 1 |
| **Total** | | **33** |

Test fixtures live in `tests/fixtures/planning_factory.py` (new helper module).

## 12. Documentation deliverables

- `docs/specs/video-planner-subagent/requirements.md` — this slice's WHAT
- `docs/specs/video-planner-subagent/design.md` — this file (HOW)
- `docs/specs/video-planner-subagent/tasks.md` — staged implementation plan
- `docs/specs/video-planner-subagent/test-spec.md` — full test spec
- `docs/specs/video-planner-subagent/integration.md` — Main Agent call pattern + example

## 13. Compatibility

- No public API change to existing modules.
- No new dependency.
- No CLI flag added.
- No new schema migration. `Shot` / `Character` / `Scene` untouched.
- Tests: adds one new test file; existing tests unchanged.

## 14. Risk & open questions

| Risk | Mitigation |
|---|---|
| `VideoPlanner` may grow into a Provider selector | Blacklist enforced; forbidden field guard in plan |
| Reason codes drift from router codes | Distinct enum; no semantic equality claim; bridge not required for this slice |
| `derive_previous_shot_state` overlaps with shot_router helpers | Helper is read-only and lives outside production; router may consume its output later |
| Future LLMs could be tempted to call planner from production | Module is import-whitelisted; production modules cannot import planning |