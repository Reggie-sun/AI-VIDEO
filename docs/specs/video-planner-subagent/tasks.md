# Video Planner Subagent — Tasks

Status: implementation plan v2 (contract repair complete; implementation not started)
Approach: strict RED → GREEN for behavioral contracts; provider-neutral and plan-only.

## Problem boundary

- Single owner: `ai_video.planning` proposes per-Shot strategy; Main Agent consumes/STOPs; existing AI-VIDEO owners execute and accept.
- Old path to remove/replace: `visual_strategy -> motion -> unconditional static/image-motion override`, empty static final-asset requirements, unconditional override confidence `1.0`, and comment-only `BLOCKED` handling.
- Unchanged contracts: no Production writer/Provider/timeline/render ownership, no Router refactor, no new Manifest/Registry/schema, no multi-Shot quality subsystem.
- Focused future verification: `pytest tests/test_planning_video_planner.py` plus Architecture Gate and policy-routed exact-snapshot Harness.

## Sequencing

```text
T1 request/plan projections
  -> T2 typed audit vocabulary
  -> T3 continuity
  -> T4 RED: intent/motion evidence and camera-only boundary
  -> T5 RED: coherence + fallback decision
  -> T6 RED: Reference vs Final Shot Visual readiness
  -> T7 confidence/warnings
  -> T8 forbidden-field guard
  -> T9 determinism
  -> T10 architecture gate
  -> T11 previous-state helper
  -> T12 integration contract
  -> T13 executable Main Agent STOP seam
  -> T14 full failure-mode regression acceptance
```

T4–T7 must land from failing behavioral tests. T13 is part of this slice; D1 is no longer allowed to defer executable STOP semantics.

## Tasks

### T1 — Schema baseline and immutable projections

RED:

- schema tests fail until all models are frozen, `extra="forbid"`, and seal/hash correctly;
- request rejects intent/review projections whose Shot identity/hash shape is invalid.

Deliverables:

- planned package `src/ai_video/planning/` and `tests/fixtures/planning_factory.py`;
- enums/models from design §§4–5, including `ShotIntentEvidence`, `ReviewDecisionProjection`, `APPROVED_REUSABLE_PLATE`, and `PlanOutcome.PROPOSED | BLOCKED`;
- `VideoGenerationPlan.source_request_content_hash` binding all current semantic request projections;
- sealed `VideoPlanningRequest.create()` and `VideoGenerationPlan.create()` using existing canonical hashing;
- no new Story/Character/Scene/Shot/Manifest/Registry schema.

Acceptance: schema round-trip, strict-extra, enum, identity/hash, and seal tests pass.

### T2 — Typed reasons and warnings

RED:

- each required mismatch/fallback/final-visual branch initially lacks the expected typed reason/warning.

Deliverables:

- preserve v1 reason/warning values;
- add `ACTION_INTENT_REQUIRED`, `STRATEGY_MOTION_MISMATCH`, `CAMERA_MOTION_ONLY`, `FINAL_SHOT_VISUAL_REQUIRED`, `FINAL_SHOT_VISUAL_AVAILABLE`, `REUSABLE_PLATE_APPROVED`, `INTENTIONAL_STATIC`, `STATIC_FALLBACK_ACCEPTED`;
- add `FINAL_SHOT_VISUAL_MISSING`, `CAMERA_MOTION_NOT_SUBJECT_MOTION`, `STATIC_FALLBACK_REQUIRES_REVIEW`, `REQUIRES_HUMAN_REVIEW`;
- deterministic append helpers with no free-form warning values.

Acceptance: every AC branch has at least one logically consistent reason; warnings are controlled enums.

### T3 — Continuity decision

RED:

- matrix pins first Shot, semantic jump, same-action continuation, angle change, and default reference behavior;
- `REFERENCE` explicitly asserts `needs_terminal_reference is False`.

Deliverables:

- `_decide_continuity(request) -> ContinuityMode` per design Stage 2;
- terminal requirement only for `EXACT_TERMINAL`.

Acceptance: full continuity matrix passes without using natural-language keyword heuristics.

### T4 — Intent-first motion classification

RED:

- character-action Shot declared `STATIC_IMAGE` must not classify as `NONE`;
- continuous/spatial/open→close state change must not classify as static;
- action Shot with only pan/zoom/zoompan/parallax must record camera-only evidence and must not claim character motion;
- unresolved prose-only intent requires human review instead of keyword-selected mode.

Deliverables:

- `_derive_required_motion(request) -> MotionRequirement` consumes `ShotIntentEvidence`, typed motion directives and continuity constraints before declared strategy;
- transform-only directive classifier;
- explicit evidence precedence from design Stage 3.

Acceptance: AC-11 and AC-12 RED cases pass; old `STATIC_IMAGE -> NONE` and `IMAGE_MOTION -> LIGHT_TRANSFORM` assertions are removed as standalone truth claims.

### T5 — Coherence and static fallback decision

RED:

- action + static/image-motion mismatch is `BLOCKED` when fallback false;
- fallback true without final visual/rationale/current Review evidence remains `BLOCKED`;
- fully evidenced fallback returns `PROPOSED` with fallback reason/warning, never creative PASS;
- mismatch path never receives unconditional confidence `1.0`.

Deliverables:

- `_check_strategy_coherence(...)` runs before generation-mode selection;
- `accept_static_image_fallback` is read in the algorithm;
- dynamic decision table runs only after coherence gate;
- no automatic Shot mutation, placeholder, retry or Provider fallback.

Acceptance: AC-13 and AC-16 pass along with legacy dynamic cases AC-1～AC-5.

### T6 — Reference and Final Shot Visual readiness

RED:

- Character/Scene references alone do not satisfy static/image-motion final visual;
- wrong `canonical_owner_id`, missing exact target-Shot final-role binding, or stale review evidence is rejected;
- Shot-specific approved keyframe + intentional-static rationale succeeds;
- reusable plate succeeds only with exact target-Shot binding and current reuse approval/rationale.

Deliverables:

- `_classify_asset_readiness(request)` distinguishes reference guidance, terminal evidence, Shot-specific keyframe and approved reusable plate;
- `_build_required_asset_roles(...)` requires `APPROVED_KEYFRAME` or `APPROVED_REUSABLE_PLATE` for static/image-motion;
- reuse existing `Shot.required_asset_roles` binding semantics; no new durable asset role store.

Acceptance: AC-14 and AC-15 pass; static required assets are never empty by default.

### T7 — Confidence, review and warning semantics

RED:

- declared static override alone cannot yield confidence `1.0`;
- unresolved mismatch/review yields `BLOCKED` + `REQUIRES_HUMAN_REVIEW`;
- evidenced action fallback keeps `STATIC_FALLBACK_REQUIRES_REVIEW` audit warning;
- confidence never changes STOP eligibility.

Deliverables:

- deterministic `_compute_confidence` and `_compute_warnings` after all gates;
- explicit separation of audit warning from unresolved human-review warning.

Acceptance: exact typed warning/reason assertions pass for all static-first cases.

### T8 — Forbidden-field guard

RED:

- plan rejects Provider selection, Manifest/timeline/path/output fields and generated/reviewed/selected/locked/activated/final-acceptance flags.

Deliverables:

- `extra="forbid"` plan model and parametrized forbidden-field tests.

Acceptance: AC-7 passes with precise field-level failures.

### T9 — Determinism and current identity

RED:

- identical sealed request called repeatedly must match exactly;
- changing Shot content hash, intent projection, Review evidence identity/decision, policy or asset binding must change request hash and invalidate an old plan even if Shot hash is unchanged.

Deliverables:

- deterministic plan construction with no clock/UUID entropy in hashed payload;
- diagnostic `request_id` excluded from semantic request hash and deterministic `plan_id` derived from request content hash;
- stable identity tests.

Acceptance: AC-6 passes.

### T10 — Architecture import gate

RED:

- fixture import of any forbidden writer/Provider/IO module fails with file:line;
- fixture Production import of `ai_video.planning` fails.

Deliverables:

- AST gate for design §3 allow/deny boundary;
- no runtime Skill imports or calls.

Acceptance: AC-8 passes; Production dependency direction remains unchanged.

### T11 — `derive_previous_shot_state` helper

RED:

- first Shot/reset, same-action continuation, angle change and semantic jump cases;
- helper must not infer `is_same_action` merely from equal prose strings when typed continuity says otherwise.

Deliverables:

- pure helper that consumes existing Shot/continuity evidence;
- no filesystem/Registry/Manifest read.

Acceptance: output is deterministic and supports T3 without owning continuity truth.

### T12 — Integration contract and examples

Deliverables:

- update `integration.md` with request construction, current plan check, Final Shot Visual rules, illustrative JSON and downstream route;
- explicitly state `PROPOSED != generated/reviewed/selected/locked/activated/PASS/Final Acceptance`;
- explicitly forbid run-local placeholder continuation after any STOP condition.

Acceptance: AC-10 and AC-18 are reviewable and mirrored by executable assertions in T13.

### T13 — Executable Main Agent consumer/STOP seam

RED:

- `BLOCKED`, stale source request hash, stale Shot id/revision/hash, missing required assets, wrong owner/binding, or unresolved `REQUIRES_HUMAN_REVIEW` must raise typed STOP;
- router, Provider, placeholder/materializer, composition and render spies must each remain at 0 calls;
- a current `PROPOSED` plan with satisfied assets may only call an existing Production handoff spy; it must not set acceptance/activation state.

Deliverables:

- minimal Main Agent/planning-side `require_current_video_plan(...)` consumer or equivalent executable seam; caller freshly rebuilds current sealed request and consumer compares `source_request_content_hash`;
- no Production module import of planner and no `ShotVisualResolver` refactor.

Acceptance: AC-17 and AC-18 pass. This task owns stop semantics; future D1 does not.

### T14 — Final regression and acceptance

Deliverables:

- prove AC-1～AC-18 with executable tests;
- explicitly run the real failure-mode suite: static bootstrap mismatch, camera-only zoompan, fallback false/true, reference-vs-final asset, intentional static success, zero-call STOP, and `PROPOSED != PASS`;
- run focused planning tests, Architecture Gate and applicable full suite;
- review requirements/design/tasks/test/integration traceability for contradictions;
- stage only task-owned files and run `.agent/harness/policy.yaml` checks on the exact staged snapshot; verify receipt when policy requires one;
- final completion report distinguishes proposed docs, accepted code, test evidence and runtime truth.

Acceptance: generic hash/import tests alone are insufficient. T14 is incomplete until every incident regression is GREEN and the Main Agent stop seam is executable.

## Traceability matrix

| Contract / AC | Requirements | Design | RED tests | Implementation task | Integration acceptance |
|---|---|---|---|---|---|
| Legacy dynamic strategy AC-1～AC-5 | FR-3/4/8 | Stages 2/3/5/6 | Cases 1～5 | T3～T6 | current proposal may enter Production gates |
| Determinism and isolation AC-6～AC-8 | FR-2/11 | §§3/4/5/8 | hash, forbidden-field, import gates | T8～T10 | plan sealed; no durable/Provider ownership |
| Coverage/docs AC-9～AC-10 | verification plan | §11 | coverage + integration contract tests | T12/T14 | exact examples and STOP route |
| Static bootstrap mismatch AC-11 | FR-4/5 | Stages 3/4/7 | Case 6 | T4/T5/T7 | `BLOCKED` stops all downstream calls |
| Camera-only zoompan AC-12 | FR-4/5 | §5.1 + Stage 3 | Case 7 | T4 | camera transform cannot satisfy subject action |
| Fallback false AC-13 | FR-7 | Stage 4 | Case 8 | T5 | no silent downgrade |
| Reference vs final visual AC-14 | FR-6 | §§4.3/6 Stage 1/6 | Case 9 | T6 | missing final visual STOP |
| Intentional static AC-15 | FR-5/6 | Stage 4 | Case 10 | T5/T6/T7 | eligible proposal only |
| Evidenced fallback true AC-16 | FR-7 | §§4.4/6 Stage 4 | Case 11 | T5/T7 | audit warning retained; no auto PASS |
| Executable STOP AC-17 | FR-12 | §7 | Case 12 spies | T13 | zero router/Provider/placeholder-materializer/composition/render calls |
| `PROPOSED` semantics AC-18 | FR-13/14 | §§5.3/7/10 | Case 13 | T12/T13/T14 | downstream Review/Pilot still mandatory |

## Definition of done

1. RED observed before implementation for T4–T7 and T13 incident behavior.
2. Scoped implementation makes those exact cases GREEN without weakening assertions.
3. No unrelated edits, new Provider/dependency/schema, Production reverse import or durable ownership.
4. Parent reviews final diff and independent reviewer checks semantic consistency.
5. Exact staged snapshot passes policy-routed Harness checks before task-only commit.

## Deferred work

- D1 — optional planner-to-router hint projection. It may translate an already-consumed proposal but does not own STOP semantics and must not refactor Router.
- D2 — plan/craft/validate/judge/refine orchestration.
- D3 — Multi-Shot planning. Remains out of scope; repetition/frame-diversity/Pilot gates stay with Review/Pilot.
- D4 — cost/latency estimation.
- D5 — plan history/replan heuristics.

## Risk register

| Task | Risk | Mitigation |
|---|---|---|
| T4 | prose heuristics silently classify action | typed intent evidence precedence; unresolved prose requires review |
| T5 | policy true becomes automatic fallback | final visual + matching Review projection + rationale required |
| T6 | references masquerade as final visuals | exact target owner/binding checks |
| T7 | confidence hides mismatch | confidence cannot clear STOP/warning |
| T13 | advisory plan is ignored | mandatory consumer plus zero-call spies |
| T14 | pure-function tests pass while incident remains | named real failure regressions are completion criteria |
