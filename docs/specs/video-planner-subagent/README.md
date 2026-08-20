# Video Planner Subagent — Slice

Status: draft v1 (specs only; implementation pending T1–T14)

This slice adds a **provider-neutral** planning intelligence layer that the Main Agent can call **before** AI-VIDEO Production. It answers "what generation strategy should this Shot use?" without owning any production state.

## Documents (read in order)

1. [requirements.md](requirements.md) — WHAT and WHY. Acceptance criteria, scope, forbidden responsibilities.
2. [design.md](design.md) — HOW. Package layout, schemas, algorithm, public surface, test plan.
3. [tasks.md](tasks.md) — Phased implementation plan (T1–T14). TDD-first.
4. [test-spec.md](test-spec.md) — Full test cases (Cases 1–5 + determinism + forbidden-field + architecture gate).
5. [integration.md](integration.md) — How Main Agent calls the planner; worked JSON examples.

## Code (already drafted)

- [`tests/test_planning_video_planner.py`](../../../tests/test_planning_video_planner.py) — 30+ unit tests pinning Cases 1–5, determinism, forbidden fields, and architecture gate.

## Planned code (post-merge)

- `src/ai_video/planning/__init__.py`
- `src/ai_video/planning/_planner_models.py`
- `src/ai_video/planning/video_planner.py`
- `tests/fixtures/planning_factory.py`

## Boundary at a glance

| Concern | Owner |
|---|---|
| Creative intent | Codex + Character / Scene / Shot |
| Project schema | `ProductionProject` |
| Asset identity | Asset Registry |
| Manifest lifecycle | `ProductionStateCommitter` |
| Provider selection | AI-VIDEO Provider Router (existing) |
| Default render | HyperFrames (existing) |
| QA / Repair | AI-VIDEO Review / Repair |
| **Generation strategy hint** | **`VideoPlanner` (NEW)** |

`VideoPlanner` is the only NEW owner and it owns **no** durable state — it returns a `VideoGenerationPlan` to the Main Agent.

## Status of this slice

- Specs: written and reviewed in this PR.
- Tests: written and would currently skip with a clear message because the planning module does not exist yet (`AST scan test` skips via `pytest.skip`).
- Implementation: not started. Run T1–T14 per `tasks.md` after spec approval.