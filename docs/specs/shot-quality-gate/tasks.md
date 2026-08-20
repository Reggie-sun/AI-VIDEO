# Shot Readiness Gate — Tasks v3

Status: implementation plan for the proposed runtime slice

Approach: RED-first, one readiness owner, no Provider or lifecycle writes

There are exactly eight implementation tasks. This docs-only revision executes none of them.

## Problem Boundary Before Implementation

- Problem: the existing `require_current_video_plan()` has correct STOP semantics but returns only first-error exceptions, while v2 proposed duplicate and invalid post-fetch/lifecycle checks.
- Single target owner: `ShotReadinessGate` for typed current-plan eligibility.
- Old path to retire: the decision body inside `require_current_video_plan()`; the public function remains a delegating compatibility wrapper.
- Unchanged contract: Video Planner proposal truth, Product/Registry/Manifest/Review owners, `PLANNING_PREFLIGHT_BLOCKED`, zero-call STOP, and current Production activation path.
- Focused verification: `python -m pytest -p no:cacheprovider tests/test_shot_readiness_gate.py tests/test_planning_video_planner.py tests/test_errors.py -q`.

## Sequence

```text
T1 models + discriminator + hashes
  -> T2 binding check
  -> T3 eligibility check
  -> T4 required asset readiness
  -> T5 result aggregation + require_ready
  -> T6 compatibility migration + old-body retirement
  -> T7 architecture/Harness routing
  -> T8 exact-snapshot verification and acceptance
```

## T1 — RED Models, Discrimination, and Hashing

Deliver:

- future package skeleton and `_readiness_models.py`;
- enums, three payloads, three Literal-bound outcome models, discriminated union;
- `ShotReadinessRequest.create()` exact three-field semantic projection;
- `ShotReadinessResult.create()` seal and cross-field validation.

Tests first: TC-11–TC-14 plus extra-field rejection.

Acceptance: wrong payload combinations fail; diagnostic ids do not affect semantic/result hash.

## T2 — Request/Plan Binding Check

Deliver `_check_request_plan_binding()` for the exact D-04.1 booleans and ordered reasons, including recomputation of the outer readiness request seal. It must reuse accepted hashing helpers and must not call the planner.

Tests first: TC-01–TC-05.

Acceptance: every forged/stale identity is blocked with deterministic reasons.

## T3 — Plan Eligibility Check

Deliver `_check_plan_eligibility()` consuming only `outcome` and `warnings`.

Tests first: TC-06 and TC-07.

Acceptance: planner `BLOCKED` and unresolved human review stop; no strategy/confidence/capability re-derivation exists.

## T4 — Required Asset Readiness Check

Deliver `_check_required_asset_readiness()` and extract the existing `_current_review`, exact final-visual binding, `_available_role`, and `_required_role_is_available` helpers into `src/ai_video/planning/_asset_readiness.py` as the one cycle-safe shared owner.

Tests first: TC-08–TC-10.

Acceptance: Character/Scene/final-visual/terminal ownership stays exact; the gate checks only plan-declared roles; no duplicate helper remains.

## T5 — Gate Evaluation, Result Validation, and `require_ready`

Deliver:

- `ShotReadinessGate.evaluate()` returning all three canonical outcomes;
- binary aggregation;
- `require_ready()` seal/status validation and typed STOP conversion;
- public exports limited to gate/data/require function.

Tests first: TC-15 and result-validator branches from TC-11–TC-13.

Acceptance: complete deterministic diagnostics, no short-circuit side effect, no warning/not-evaluated status.

## T6 — Compatibility Migration and Old-Path Retirement

Change only the planning-side consumer seam needed to establish a single owner:

- convert `require_current_video_plan()` to delegate to `ShotReadinessGate` + `require_ready()`;
- preserve signature, error code, non-retryability, and `prepare_shot_for_existing_production()` behavior;
- remove the old duplicated binding/eligibility/asset decision body;
- adapt current planning tests rather than weakening them.

Tests first: TC-16 and TC-17, including Router/Provider/materializer/composition/render spies.

Acceptance: blocked path has zero downstream calls; ready path calls the existing handoff once.

## T7 — Architecture Boundary and Harness Routing

Deliver in the same runtime commit:

- import/no-IO Architecture tests from TC-18;
- `.agent/harness/policy.yaml` check/category from D-07;
- add `shot_readiness_gate_tests` to the existing `video_planning.check_ids` so T6 compatibility changes route to both suites;
- `tests/test_agent_harness.py` routing proof from TC-19;
- negative owner audit from TC-20 (no VideoQualityGate, committer/Manifest seam, receipt hash fields, or quality claims).

Acceptance: both quality-gate and planning compatibility paths route to the focused checks; policy change itself passes Harness tests.

## T8 — Exact Snapshot Verification and Acceptance

Before staging, review ownership and final diff. Stage only task files. Run:

1. focused tests from the problem boundary;
2. Harness inspection for the exact staged snapshot;
3. Harness verification on the exact non-empty staged snapshot or exact commit range in its detached execution tree;
4. receipt integrity verification;
5. `git diff --check` and scoped link/anchor checks.

Acceptance: AC-01–AC-12 and TC-01–TC-20 are traceable; receipt reports fresh/passed/integrity/policy/snapshot true; independent review has no blocker.

## Deferred Slices

### D1 — Provider-Neutral Post-Fetch Structural Projection

Do not start until a concrete structural fact is found that is not already guaranteed by typed receipt construction, fetch owner, committer, candidate validation, or P6 Review. The accepted design must provide a fully projected input schema and remain no-IO/provider-neutral. D1 must not infer a submission from `submission_fingerprint`.

### D2 — Durable Readiness Evidence Migration

Do not start without explicit approval. A complete proposal must include Manifest schema version, writer API, canonical path/layout, content addressing, reopen, backward/forward compatibility, recovery/crash windows, replay, invalidation, and exact activation semantics. An “optional hash field” is not migration-free.

Identity drift, continuity quality, motion naturalness, subjective picture quality, final acceptance, and automatic repair are not deferred gate tasks; they remain with existing Review/Pilot/Repair owners.

## Definition of Done

- exactly T1–T8 complete;
- no D1/D2 implementation mixed into v3;
- no second readiness algorithm;
- no Product schema/lifecycle/Provider/media changes;
- all TC-01–TC-20 pass;
- independent reviewer verdict is `accept` or `accept with concerns` with no blocking issue;
- fresh exact-snapshot Harness receipt is fully valid.
