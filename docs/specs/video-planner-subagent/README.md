# Video Planner Subagent — Slice

Status: repaired specification v2 (docs only; no accepted runtime implementation)

This slice specifies a **provider-neutral**, **plan-only** per-Shot preflight. It checks whether the declared `Shot.visual_strategy` is coherent with approved Shot intent before AI-VIDEO generation or composition. It does not own Production state, choose a Provider, render media, or accept creative quality.

## Documents (read in order)

1. [requirements.md](requirements.md) — scope, contracts, acceptance criteria.
2. [design.md](design.md) — request projection, algorithm, typed reasons/warnings, boundaries.
3. [tasks.md](tasks.md) — RED-first implementation and integration plan with traceability.
4. [test-spec.md](test-spec.md) — legacy cases plus the static-first incident regressions.
5. [integration.md](integration.md) — mandatory Main Agent consumer/STOP contract.

## Planned code (not runtime truth)

- `src/ai_video/planning/__init__.py`
- `src/ai_video/planning/_planner_models.py`
- `src/ai_video/planning/video_planner.py`
- `tests/fixtures/planning_factory.py`
- `tests/test_planning_video_planner.py`

No implementation or test path is accepted merely because it is named in this specification. Runtime truth requires a later implementation task, executable tests, policy-routed Harness evidence, and the existing AI-VIDEO owners.

## Boundary at a glance

| Concern | Owner |
|---|---|
| Creative intent and canonical Shot fields | Codex + approved Character / Scene / Shot artifacts |
| Asset identity, binding, and provenance | Asset Registry + canonical Shot asset roles |
| Manifest lifecycle and durable approval evidence | `ProductionStateCommitter` + AI-VIDEO Review |
| Provider selection and execution | Existing AI-VIDEO Provider path |
| Timeline and composition | `ResolvedTimeline` + HyperFrames |
| Final visual repetition, full-watch, Pilot and Final Acceptance | AI-VIDEO Review + human Pilot Reality Gate |
| Per-Shot intent/strategy coherence proposal | `VideoPlanner` |

`VideoPlanner` owns no durable state. `Shot.visual_strategy` is an input claim to audit, not unquestioned truth. Character/Scene references are guidance only and never become a final Shot visual merely by being available.

## Mandatory preflight summary

Every Shot preparing to enter generation or composition must have a plan sealed against the current request hash, including current Shot, asset binding, Review decision and policy projections. The Main Agent consumer must STOP on `PlanOutcome.BLOCKED`, missing required assets, stale plan/request identity, or unresolved `REQUIRES_HUMAN_REVIEW`. A run-local script may not ignore the plan and continue with a placeholder.

`PROPOSED` means only “this strategy is eligible to enter existing Production gates.” It does not mean generated, reviewed, selected, locked, activated, human-approved, or Final Acceptance.

The downstream route remains:

```text
VideoPlanner per-Shot preflight
  -> AI-VIDEO Provider / Asset execution
  -> Composition
  -> Review
  -> human Pilot Reality Gate
```

## Why v1 could not prevent static-first

The old algorithm derived `MotionRequirement.NONE` directly from `Shot.visual_strategy=STATIC_IMAGE`, then unconditionally selected `STATIC_IMAGE`, required no final visual asset, and assigned override confidence `1.0`. It never compared the declaration with character action, continuous action, spatial change, motion directives, continuity, or open/close state. Because the planner was only advisory and its router bridge was deferred, even `BLOCKED` had no executable STOP semantics. A bootstrap mistake was therefore certified instead of diagnosed.

## Status of this slice

- Specification and implementation plan: repaired around the real static-first failure mode.
- Runtime implementation and executable tests: not part of this docs-only task and not claimed complete.
- Provider calls, media generation, Production runtime changes, and Router refactors: explicitly absent.
