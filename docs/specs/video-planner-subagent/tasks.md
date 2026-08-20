# Video Planner Subagent — Tasks

Status: implementation plan v1 (paired with `requirements.md` + `design.md`)
Approach: TDD-first, staged by risk / dependency.

Each task is small enough to land in one PR (≤1 day of focused work). Tests are written first.

## Sequencing rationale

```
T1 schema baseline ─┬─ T2 reason codes & warnings ─┐
                    ├─ T3 continuity decision ─────┤
                    └─ T4 motion override ─────────┤
                                                   ├─ T5 decision table ─┬─ T6 capability flags
                                                   │                      ├─ T7 confidence calc
                                                   │                      ├─ T8 forbidden-field guard
                                                   │                      └─ T9 determinism test
                                                   ├─ T10 architecture import gate
                                                   ├─ T11 derive_previous_shot_state helper
                                                   └─ T12 integration doc + example
                                                                            │
                                                                            ▼
                                                            T13 end-to-end Main Agent example
                                                            T14 final review + acceptance
```

Foundation (T1–T4) is small and unblocks parallel work on T5–T9. T10 hardens the boundary so no later task can leak imports. T11–T14 close out.

## Tasks

### T1 — Schema baseline (foundational)

Deliverables:

- `src/ai_video/planning/__init__.py` (empty stub, just docstring)
- `src/ai_video/planning/_planner_models.py`
- Enums: `GenerationMode`, `ContinuityMode`, `MotionRequirement`, `AssetRole`, `ReasonCode`, `PlanWarning`, `PlanOutcome`
- Models: `AvailableAsset`, `PreviousShotState`, `ProductionPolicyInput`, `CapabilityRequirements`, `RequiredAssetRole`, `VideoPlanningRequest`, `VideoGenerationPlan`
- All models `extra="forbid"`, `frozen=True`, `StrictModel` base
- `VideoPlanningRequest.create()` and `VideoGenerationPlan.create()` sealed classmethods
- `plan_hash` and `request_content_hash` computed via `canonical_sha256`

Tests: schema round-trip + `extra="forbid"` rejection.

Acceptance: pytest passes for `test_planning_video_planner.py::test_schemas_baseline`.

Effort: human ~3h, CC ~10min.

### T2 — Reason codes & warnings

Deliverables:

- `ReasonCode` enum finalised with all values from design §4.10
- `PlanWarning` enum finalised with all values from design §4.11
- Helper `_append_reason(codes, code)` and `_append_warning(warnings, warning)` in `video_planner.py` (private, no IO)
- Empty `VideoPlanner.plan()` skeleton that returns BLOCKED with single reason `MOTION_HERO_REQUIRES_POLICY` (so other tests have something to assert against)

Tests: AC-1..AC-5 reason-code assertions only (full algorithm comes in T5).

Acceptance: reason code invariants documented; helper tested in isolation.

Effort: human ~1h, CC ~5min.

### T3 — Continuity decision

Deliverables:

- `_decide_continuity(request) -> ContinuityMode` private method
- Implements design §5 stage 2 logic
- Returns enum, not string
- Pinned tests:
  - first shot → NONE
  - semantic jump → SEMANTIC
  - same action + no angle change → EXACT_TERMINAL
  - angle change → REFERENCE
  - default (second shot, no flags) → REFERENCE

Tests: full continuity matrix (8 cases).

Acceptance: tests pinned to enum value, not string.

Effort: human ~1h, CC ~5min.

### T4 — Motion override branches

Deliverables:

- `_decide_motion(target_shot) -> MotionRequirement` private method
- Implements design §5 stage 3 logic
- Returns enum

Tests:

- `STATIC_IMAGE` Shot → `NONE`
- `IMAGE_MOTION` Shot → `LIGHT_TRANSFORM`
- `MOTION_GRAPHICS` Shot → `GRAPHIC`
- `GENERATED_VIDEO` Shot with no directives → `FREE_COMPLEX`
- `GENERATED_VIDEO` Shot with only pan/zoom/parallax → `LIGHT_TRANSFORM`
- `GENERATED_VIDEO` Shot with composite directives → `CHARACTER_ACTION`

Effort: human ~1h, CC ~5min.

### T5 — Generation mode decision table

Deliverables:

- `_decide_generation_mode(request, continuity, motion) -> GenerationMode | BLOCKED` private method
- Implements design §5 stage 4 decision table
- Returns `None` sentinel when blocked (not a string)

Tests:

- 9-row decision table → expect exact mode or BLOCKED
- Override branches (motion NONE / LIGHT / GRAPHIC / HERO_OR_REPAIR) override decision table

Effort: human ~3h, CC ~15min.

### T6 — Required assets & capability flags

Deliverables:

- `_build_required_asset_roles(mode, request) -> tuple[RequiredAssetRole, ...]`
- `_build_capability_requirements(mode, continuity, policy) -> CapabilityRequirements`
- Implements design §5 stage 5

Tests:

- Each generation mode produces the right required_asset_roles
- Capability flags match design §5 stage 5 rules
- `accepts_remote_execution = False` when `policy.remote_authorized=False`

Effort: human ~2h, CC ~10min.

### T7 — Confidence calculation & warnings

Deliverables:

- `_compute_confidence(mode, request, refs_present) -> float`
- `_compute_warnings(mode, request, confidence, refs_present) -> tuple[PlanWarning, ...]`
- Implements design §5 stage 6

Tests:

- Override path → 1.0
- Decision-table single match with all refs → 0.9
- Multiple plausible alternatives → 0.6
- Multiple blocked reasons → 0.5
- Warning list contains expected warnings

Effort: human ~2h, CC ~10min.

### T8 — Forbidden-field guard

Deliverables:

- `VideoGenerationPlan` schema uses `extra="forbid"` (already in T1)
- Test injects forbidden fields via `model_construct` and asserts `ValidationError`
- Forbidden list enforced in `tests/test_planning_video_planner.py::test_forbidden_fields_rejected`

Tests: 6 forbidden-field rejections (one per forbidden key).

Effort: human ~30min, CC ~3min.

### T9 — Determinism test

Deliverables:

- Helper `assert_plan_hash_stable(plan_factory)` in tests
- Two-call determinism: same request → identical `plan_hash`
- Three sequential calls → identical hash
- Different `target_shot_content_hash` → different `plan_hash`

Tests: 3 cases.

Effort: human ~30min, CC ~3min.

### T10 — Architecture import gate

Deliverables:

- `tests/test_architecture_gate.py` extension (or new `tests/test_planning_architecture_gate.py`)
- AST scan of `src/ai_video/planning/` for forbidden imports
- Forbidden list: see design §3 blacklist
- Whitelist: see design §3 whitelist
- Each forbidden import in `src/ai_video/planning/**` causes test failure with file:line

Tests: 1 AST-scan test covering each forbidden module name.

Effort: human ~2h, CC ~10min.

### T11 — `derive_previous_shot_state` helper

Deliverables:

- `VideoPlanner.derive_previous_shot_state(previous_shot, target_shot) -> PreviousShotState`
- Pure: same inputs → same `content_hash`
- Heuristics:
  - `previous_shot is None` → all None/False except `semantic_jump=True` (treat as reset)
  - same `scene_id` → `is_same_scene=True`
  - same `storyboard_beat_id` → `is_same_story_beat=True`
  - equal `intent` → `is_same_action=True`
  - `is_angle_change` heuristic: same scene + same beat + same action → not angle change; otherwise → True

Tests: 3 cases (first shot / same scene / angle change).

Effort: human ~1h, CC ~5min.

### T12 — Integration doc + example

Deliverables:

- `docs/specs/video-planner-subagent/integration.md` (see deliverable file)
- One Main Agent call example with full Python snippet
- One plan JSON output example
- One discussion of "what Main Agent does after plan"

Effort: human ~2h, CC ~10min.

### T13 — End-to-end Main Agent example test

Deliverables:

- `tests/test_planning_video_planner.py::test_end_to_end_main_agent_flow`
- Constructs a full `VideoPlanningRequest` from a fixture `Shot`
- Runs `VideoPlanner.plan()`
- Asserts plan shape, hash, and key reason codes

Tests: 1 case.

Effort: human ~1h, CC ~5min.

### T14 — Final review & acceptance

Deliverables:

- All AC-1..AC-10 verified
- `pytest tests/test_planning_video_planner.py` passes
- `pytest tests/test_architecture_gate.py` passes (including new gate)
- `pytest tests/` (full suite) passes — no regression
- README mention of new module (one line) — optional, only if user wants
- Final completion report

Effort: human ~1h, CC ~10min.

## Total effort

| Bucket | Human | CC |
|---|---|---|
| T1–T9 (core) | ~13.5h | ~60min |
| T10 (gate) | ~2h | ~10min |
| T11 (helper) | ~1h | ~5min |
| T12 (docs) | ~2h | ~10min |
| T13 (e2e) | ~1h | ~5min |
| T14 (review) | ~1h | ~10min |
| **Total** | **~20.5h** | **~100min** |

Single PR scope if sliced aggressively (T1–T7 alone would already be a useful MVP). Recommend landing T1–T9 first as PR1, T10–T14 as PR2.

## Definition of done (per task)

1. Test written and failing (or accepted as new) before implementation.
2. Implementation passes the test.
3. No new warnings from ruff/mypy (project default).
4. No drive-by changes to unrelated files.
5. Commit message references task id (e.g. `T5: implement decision table`).
6. `git diff` reviewed against the ownership boundary before commit.

## Out-of-scope tasks (deferred)

These will be tracked as separate slices later:

- D1 — `planner→router bridge`: convert `VideoGenerationPlan` into `ShotRoutingContext` hints for `ShotVisualResolver`
- D2 — LangGraph-style plan/craft/validate/judge/refine loop using planner output
- D3 — Multi-Shot planning (single Shot is the only current call shape)
- D4 — Cost & latency estimation fields in plan
- D5 — Plan history / replan heuristics across Shots

## Risk register per task

| Task | Risk | Mitigation |
|---|---|---|
| T5 | Decision-table branches mis-classify edge cases | Pinned tests cover 9 rows + override branches |
| T7 | Confidence floats non-deterministic | Pure function — only inputs drive confidence |
| T10 | AST scan brittle under refactor | Blacklist stored as constant list; readable failure |
| T12 | Doc example drifts from code | Example is part of T13 e2e test |