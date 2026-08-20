# Video Planner Subagent — Test Spec

Status: paired with `requirements.md` (AC list), `design.md` (algorithm), `tasks.md` (delivery plan)

## Layer overview

| Layer | Tool | What it covers | Count |
|---|---|---|---|
| Unit | pytest | Algorithm branches, schema seals, hash stability | ~30 |
| Contract | pytest | Forbidden-field rejection, schema isolation | ~7 |
| Architecture | pytest AST scan | Import blacklist, no IO | ~3 |
| End-to-end example | pytest | Main Agent full call path | ~2 |
| **Total** | | | **~42** |

## Fixture helpers (`tests/fixtures/planning_factory.py`)

```python
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64

def make_shot(*, visual_strategy=..., character_ids=("hero",), motion_directives=..., ...) -> Shot
def make_character(character_id="hero", content_hash=HASH_A) -> Character
def make_scene(scene_id="cafe", content_hash=HASH_B) -> Scene
def make_available_asset(role=..., asset_id=..., sha256=...) -> AvailableAsset
def make_previous_shot_state(**overrides) -> PreviousShotState
def make_policy(**overrides) -> ProductionPolicyInput
def make_request(**overrides) -> VideoPlanningRequest
```

Each helper applies `seal_artifact()` (existing) to give `content_hash` to the models.

## Required test cases

### Case 1 — important character + character reference + scene reference → `REFERENCE_TO_VIDEO`

```python
def test_case_1_important_character_with_references_uses_reference_to_video():
    request = make_request(
        target_shot=make_shot(character_ids=("alice",), visual_strategy=GENERATED_VIDEO),
        character_context=(make_character("alice"),),
        scene_context=make_scene("cafe"),
        available_assets=(
            make_available_asset(role=CHARACTER_REFERENCE, asset_id="ref-alice"),
            make_available_asset(role=SCENE_REFERENCE, asset_id="ref-cafe"),
        ),
        previous_shot_state=make_previous_shot_state(
            previous_shot_id="shot-1",
            is_same_scene=False,
            is_same_action=False,
            is_angle_change=True,
            semantic_jump=True,
        ),
    )
    plan = VideoPlanner().plan(request)
    assert plan.outcome == PlanOutcome.PROPOSED
    assert plan.generation_mode == GenerationMode.REFERENCE_TO_VIDEO
    assert plan.continuity_mode == ContinuityMode.SEMANTIC  # because semantic_jump=True
    assert plan.capability_requirements.needs_character_reference is True
    assert plan.capability_requirements.needs_scene_reference is True
    assert ReasonCode.IMPORTANT_CHARACTER in plan.reason_codes
    assert ReasonCode.REFERENCE_AVAILABLE in plan.reason_codes
    assert plan.confidence >= 0.7
```

### Case 2 — important character + previous terminal frame, no character reference → `IMAGE_TO_VIDEO` / `FIRST_LAST_FRAME_VIDEO`

```python
def test_case_2_important_character_with_only_terminal_uses_image_to_video():
    request = make_request(
        target_shot=make_shot(character_ids=("alice",)),
        available_assets=(
            make_available_asset(role=PREVIOUS_SHOT_TERMINAL, asset_id="terminal-1"),
        ),
        previous_shot_state=make_previous_shot_state(
            previous_shot_id="shot-1",
            is_same_scene=True,
            is_same_action=True,
            is_angle_change=False,
            has_terminal_frame_asset_id="terminal-1",
        ),
    )
    plan = VideoPlanner().plan(request)
    assert plan.outcome == PlanOutcome.PROPOSED
    assert plan.generation_mode in (
        GenerationMode.IMAGE_TO_VIDEO,
        GenerationMode.FIRST_LAST_FRAME_VIDEO,
    )
    assert plan.continuity_mode == ContinuityMode.EXACT_TERMINAL
    assert plan.capability_requirements.needs_first_frame is True
    assert ReasonCode.TERMINAL_AVAILABLE in plan.reason_codes
    assert PlanWarning.MISSING_CHARACTER_REFERENCE not in plan.warnings
```

### Case 3 — environment shot (no characters) → `TEXT_TO_VIDEO`

```python
def test_case_3_environment_shot_uses_text_to_video():
    request = make_request(
        target_shot=make_shot(character_ids=()),
        scene_context=make_scene("city-aerial"),
        available_assets=(),
        previous_shot_state=make_previous_shot_state(),
    )
    plan = VideoPlanner().plan(request)
    assert plan.outcome == PlanOutcome.PROPOSED
    assert plan.generation_mode == GenerationMode.TEXT_TO_VIDEO
    assert plan.continuity_mode == ContinuityMode.NONE
    assert plan.capability_requirements.needs_character_reference is False
    assert plan.capability_requirements.needs_scene_reference is False
    assert ReasonCode.FREE_ENVIRONMENT in plan.reason_codes
```

### Case 4 — important character, no visual anchor at all → BLOCKED (no silent T2V downgrade)

```python
def test_case_4_important_character_with_no_anchor_is_blocked():
    request = make_request(
        target_shot=make_shot(character_ids=("alice",)),
        available_assets=(),
        previous_shot_state=make_previous_shot_state(),
    )
    plan = VideoPlanner().plan(request)
    assert plan.outcome == PlanOutcome.BLOCKED
    assert plan.generation_mode != GenerationMode.TEXT_TO_VIDEO
    assert (
        ReasonCode.MISSING_REFERENCES in plan.reason_codes
        or ReasonCode.NO_CHARACTER_REFERENCE in plan.reason_codes
    )
    assert PlanWarning.MISSING_CHARACTER_REFERENCE in plan.warnings
    assert plan.confidence <= 0.9
```

### Case 5 — has references but only angle change → REFERENCE continuity, not exact terminal

```python
def test_case_5_angle_change_uses_reference_continuity_not_exact_terminal():
    request = make_request(
        target_shot=make_shot(character_ids=("alice",)),
        character_context=(make_character("alice"),),
        scene_context=make_scene("cafe"),
        available_assets=(
            make_available_asset(role=CHARACTER_REFERENCE, asset_id="ref-alice"),
            make_available_asset(role=SCENE_REFERENCE, asset_id="ref-cafe"),
            make_available_asset(role=PREVIOUS_SHOT_TERMINAL, asset_id="terminal-1"),
        ),
        previous_shot_state=make_previous_shot_state(
            previous_shot_id="shot-1",
            is_same_scene=True,
            is_same_story_beat=True,
            is_same_action=False,
            is_angle_change=True,
            has_terminal_frame_asset_id="terminal-1",
        ),
    )
    plan = VideoPlanner().plan(request)
    assert plan.outcome == PlanOutcome.PROPOSED
    assert plan.continuity_mode == ContinuityMode.REFERENCE
    assert plan.continuity_mode != ContinuityMode.EXACT_TERMINAL
    assert plan.generation_mode == GenerationMode.REFERENCE_TO_VIDEO
    assert ReasonCode.CONTINUITY_ANGLE_CHANGE in plan.reason_codes
    assert plan.capability_requirements.needs_terminal_reference is True  # OK if available
```

### Extra — pure-function determinism

```python
def test_pure_function_same_request_same_plan():
    request = make_request()
    p1 = VideoPlanner().plan(request)
    p2 = VideoPlanner().plan(request)
    assert p1.plan_hash == p2.plan_hash
    assert p1.model_dump() == p2.model_dump()


def test_different_shot_content_hash_yields_different_plan():
    r1 = make_request(target_shot=make_shot(content_hash=HASH_A))
    r2 = make_request(target_shot=make_shot(content_hash=HASH_B))
    p1 = VideoPlanner().plan(r1)
    p2 = VideoPlanner().plan(r2)
    assert p1.plan_hash != p2.plan_hash
```

### Extra — forbidden-field guard

```python
@pytest.mark.parametrize("forbidden_key", [
    "provider_name",
    "selected_capability_id",
    "manifest_revision",
    "timeline_position",
    "asset_path",
    "output_asset_id",
])
def test_plan_rejects_forbidden_field(forbidden_key):
    base = VideoPlanner().plan(make_request()).model_dump()
    base[forbidden_key] = "leak"
    with pytest.raises(ValidationError):
        VideoGenerationPlan.model_validate(base)
```

### Extra — architecture gate (import blacklist)

```python
def test_planning_module_forbids_production_writer_imports():
    forbidden = [
        "ai_video.production.state_commit",
        "ai_video.production.dependency",
        "ai_video.production.composition",
        "ai_video.production.hyperframes",
        "ai_video.production.manifest",
        "ai_video.production.video",
        "ai_video.production.seedance",
        "ai_video.production.minimax_h3",
        "ai_video.production.minimax_hailuo",
        "ai_video.comfy_client",
        "ai_video.ffmpeg_tools",
    ]
    planning_root = Path("src/ai_video/planning")
    for path in planning_root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [f"{node.module}.{alias.name}" for alias in node.names]
            else:
                continue
            for name in names:
                assert not any(name.startswith(m) for m in forbidden), (
                    f"{path} imports forbidden module {name}"
                )
```

## Negative tests

| Test | Expectation |
|---|---|
| Empty `available_assets` for character Shot → BLOCKED | outcome BLOCKED, MISSING_REFERENCES in reason_codes |
| `production_policy.local_resources_available=False`, mode `IMAGE_TO_VIDEO` | `accepts_local_execution=False`, mode unchanged |
| `motion_requirement=HERO_OR_REPAIR` | outcome BLOCKED, `REQUIRES_HUMAN_REVIEW` warning |
| `Shot.visual_strategy=EXISTING_VIDEO` | outcome BLOCKED with rationale pointing to existing-video path |

## Coverage targets

- `src/ai_video/planning/_planner_models.py`: ≥ 95% lines
- `src/ai_video/planning/video_planner.py`: ≥ 95% lines
- `src/ai_video/planning/__init__.py`: ≥ 100% lines (re-export only)

## CI integration

The new test file is auto-picked up by `pytest tests/`. No conftest changes required. Existing conftest fixtures remain untouched.

## Manual smoke (out of CI)

The integration doc provides a copy-paste Main Agent example. Manual smoke is optional and reads plan JSON to confirm intent — not a CI gate.