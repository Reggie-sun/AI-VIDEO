# Shot Readiness Gate — Requirements v3

Status: proposed v3; runtime implementation pending

Owner: Main Agent planning-side pre-submit readiness

Target module: `src/ai_video/quality_gates/`

## Context

The accepted Video Planner already produces a sealed `VideoGenerationPlan` and exposes `require_current_video_plan()`. Current source proves that the consumer validates current request/plan seals, plan id, source request hash, target Shot identity, plan outcome, unresolved human review, and required asset readiness before the existing Production handoff.

v3 must not create a parallel algorithm. It specifies a typed `ShotReadinessGate` as the single evolution of that consumer: the gate returns complete discriminated diagnostics, while `require_current_video_plan()` becomes a compatibility wrapper that delegates to the gate and preserves existing STOP behavior.

Current source also proves:

- `VideoFetchReceipt` and `LocalVideoFetchReceipt` reject an invalid `fetch_fingerprint` during model validation/reopen.
- `VideoFetchReceipt.create()` rejects a fetched content type that differs from `VideoSubmission.expected_content_type`.
- `FetchedVideoCandidate` contains only `relative_path` and a typed fetch receipt; it carries no submission object or subjective media evidence.
- the actual activation API is `activate_video_candidate()`, after `prepare_video_activation_candidate()`.

Therefore v3 contains no post-fetch gate, committer parameter, Manifest field, receipt pointer, Provider import, or media-quality claim.

## Goal

Provide one pure, deterministic, provider-neutral readiness decision that:

1. consumes, but does not re-derive, accepted Video Planner truth;
2. verifies that the request and plan are current and mutually bound;
3. verifies only the asset roles already required by the plan;
4. produces typed all-check diagnostics with true payload discrimination;
5. enforces Main Agent STOP before all downstream side effects;
6. preserves all existing Production, Review, Registry, Manifest, timeline, renderer, and Provider owners.

## Explicitly Out of Scope

- strategy, motion, continuity, capability, or fallback re-derivation;
- natural-language complexity/token/word-count heuristics;
- identity drift, face/wardrobe similarity, action naturalness, scene consistency, frame diversity, blur, resolution preference, or subjective quality;
- fetch receipt seal/content-type revalidation;
- Provider/profile selection, ranking, fallback, call, poll, fetch, retry, or repair;
- Manifest/Registry/dependency/timeline/render writes, activation, recovery, or new durable evidence;
- new CLI, dependency, Provider, renderer, timeline, writer, automatic repair, or acceptance path;
- changes to P6 Review / Repair or human Pilot Reality Gate.

## Functional Requirements

### R-01 — Request and plan binding

`ShotReadinessRequest` must require one `VideoPlanningRequest` and one `VideoGenerationPlan`. Evaluation must block unless all are true:

- outer readiness request hash matches the exact R-05 semantic projection;
- current request semantic seal is valid;
- plan semantic seal and deterministic `plan_id` are valid;
- `plan.source_request_content_hash == current_request.request_content_hash`;
- target Shot id, revision, and content hash match exactly;
- both contracts use the accepted `video-planner/2` version.

The gate reads these fields; it does not reconstruct planner intent, continuity, motion, strategy, reasons, or capabilities.

### R-02 — Plan eligibility

The gate must block when:

- `plan.outcome == PlanOutcome.BLOCKED`; or
- `PlanWarning.REQUIRES_HUMAN_REVIEW` remains in `plan.warnings`.

Other typed planner warnings remain visible but do not independently block unless the Video Planner contract says they are unresolved. `READY` does not upgrade any warning to creative or quality acceptance.

### R-03 — Required asset readiness

For each `plan.required_asset_roles` item, the gate must evaluate availability against the exact current `VideoPlanningRequest` projection and existing role semantics:

- Character reference owner must be one of the target Shot's current Character ids.
- Scene reference owner must match the target Shot's current Scene id.
- Previous terminal must match both the current previous-Shot id and terminal asset id.
- Approved keyframe/reusable plate must keep the existing exact target-Shot final-visual binding and current Review projection requirements.

The gate must not infer additional required roles, inspect Asset Registry files, or treat its projection as a second Registry. Missing/wrong-owner/wrong-binding assets block.

### R-04 — Truly discriminated outcomes

The result must contain exactly one outcome for each check id, in canonical order:

1. `request_plan_binding`;
2. `plan_eligibility`;
3. `required_asset_readiness`.

Each outcome is a distinct model with `check_id: Literal[...]` and its own payload type. The union must use `Field(discriminator="check_id")`. A request-plan outcome cannot carry an asset payload, and model validation must reject every wrong `check_id`/payload combination.

Every model is frozen and `extra="forbid"`.

### R-05 — Deterministic semantic hashing

`request_id` is diagnostic correlation only. It must not change `ShotReadinessRequest.request_content_hash` or `ShotReadinessResult.result_hash`.

The readiness request semantic projection is exactly:

```text
contract_version
current_request.request_content_hash
plan.plan_hash
```

Evaluation must recompute and validate the outer readiness request seal even when the caller supplies an already-constructed model; field shape validation alone is insufficient. The result carries `source_readiness_request_hash == ShotReadinessRequest.request_content_hash`. Its own hash excludes only `result_hash`; the result does not copy diagnostic `request_id`. Rebuilding with a different readiness `request_id` or nested `VideoPlanningRequest.request_id`, while semantic hashes remain identical, must produce the same readiness hashes and result payload.

### R-06 — Binary status and STOP semantics

Statuses are only `READY | BLOCKED`; check severities are only `PASS | BLOCKED`.

- any blocked check → result `BLOCKED`;
- all three checks pass → result `READY`.

There is no `WARNING` or `NOT_EVALUATED` gate status. Missing plan/input is malformed request or `BLOCKED`, never silent pass. A Main Agent handoff must call `require_ready()` (directly or through the compatibility wrapper) before Router, Provider, placeholder/materializer, composition, or render. On `BLOCKED`, all downstream call counts remain zero.

### R-07 — Single owner and compatibility migration

The future implementation must retire the decision body currently in `require_current_video_plan()`:

- `ShotReadinessGate.evaluate()` becomes the only readiness decision owner.
- `require_current_video_plan()` constructs/evaluates the readiness request or accepts the result, delegates to `require_ready()`, and preserves `AiVideoError(ErrorCode.PLANNING_PREFLIGHT_BLOCKED, retryable=False)`.
- `prepare_shot_for_existing_production()` keeps its public behavior and zero-call boundary.
- shared asset-role logic must have one implementation; copying it into both planning and quality-gate modules is forbidden.

### R-08 — Pure and provider-neutral boundary

The gate must perform no filesystem, network, clock, random, environment, subprocess, secret, Provider, Registry, Manifest, committer, dependency, timeline, renderer, Review, or media access.

Allowed imports are limited to:

- `ai_video.planning._planner_models` typed planning contracts;
- `ai_video.planning._asset_readiness` as the single planning-owned pure role-readiness seam;
- `ai_video.production.models` and `ai_video.production.hashing` read-only schema/hash helpers;
- `ai_video.errors` for compatibility STOP conversion;
- standard library and pydantic.

Production modules must not import `ai_video.quality_gates`.

### R-09 — No persistence or lifecycle seam

`ShotReadinessResult` is ephemeral decision data. v3 adds no `VersionedArtifact`, receipt id, receipt file, Manifest pointer, `VideoGenerationAttemptState` field, committer parameter, schema version, activation rule, or recovery behavior.

If persistence is ever required, it is D2 and must be a separately authorized migration slice.

### R-10 — Post-fetch owner audit

v3 defines no `VideoQualityGate`.

- fetch receipt seal belongs to typed receipt constructors/validators and durable reopen;
- observation/submission/file-byte linkage belongs to fetch owner and committer;
- expected content type belongs to `VideoSubmission` + `VideoFetchReceipt.create()`;
- technical/perceptual/semantic quality belongs to candidate validation and P6 Review/Pilot.

A future post-fetch gate is allowed only after a concrete non-duplicated structural gap and a provider-neutral fully projected input schema are accepted.

### R-11 — Harness routing contract

The later runtime implementation must update `.agent/harness/policy.yaml` and Harness tests in the same change. The planned check is:

```yaml
shot_readiness_gate_tests:
  argv: [python, -m, pytest, -p, no:cacheprovider,
         tests/test_shot_readiness_gate.py,
         tests/test_planning_video_planner.py,
         tests/test_errors.py, -q]
```

The planned category maps:

- `src/ai_video/quality_gates/**`;
- `tests/fixtures/shot_readiness_factory.py`;
- `tests/test_shot_readiness_gate.py`.

It routes to `shot_readiness_gate_tests` and `task_architecture_gate`. Changes to `planning/video_planner.py` and its tests continue to route through `video_planner_tests` and must also run the readiness check when they touch the compatibility seam. This docs-only v3 revision does not edit policy.

To make that executable, the later policy change must also add `shot_readiness_gate_tests` to the existing `video_planning.check_ids`; defining only the new quality-gate category is insufficient. Harness routing tests must pin both categories.

### R-12 — Quality terminology boundary

Names, messages, examples, and completion claims must use “readiness”, “structural/current-plan preflight”, or “eligibility”. They must not claim that this gate detects identity drift, continuity quality, motion naturalness, visual defects, or final picture quality.

## Acceptance Criteria

1. AC-01 — valid current request + valid `PROPOSED` plan + all required assets current → `READY`.
2. AC-02 — invalid outer readiness request seal, invalid nested planning request seal, invalid plan seal, or invalid deterministic plan id → `BLOCKED` with binding reason.
3. AC-03 — stale source request hash or stale target Shot id/revision/content hash → `BLOCKED`.
4. AC-04 — `PlanOutcome.BLOCKED` → `BLOCKED`; gate does not reinterpret planner reasons.
5. AC-05 — unresolved `REQUIRES_HUMAN_REVIEW` → `BLOCKED`; resolved audit warnings alone do not create a second policy.
6. AC-06 — missing required asset, wrong owner, wrong Shot final-role binding, or wrong terminal owner → `BLOCKED`.
7. AC-07 — every wrong `check_id`/payload combination fails model validation.
8. AC-08 — different diagnostic ids with identical semantic hashes produce byte-identical result payload/hash.
9. AC-09 — blocked compatibility path raises `PLANNING_PREFLIGHT_BLOCKED` and all downstream spies remain zero.
10. AC-10 — ready compatibility path invokes the existing handoff exactly once and does not claim activation/Review/Final Acceptance.
11. AC-11 — Architecture tests reject forbidden imports and any Production reverse import.
12. AC-12 — exact staged/commit-range Harness receipt is fresh, passed, integrity-valid, policy-valid, and snapshot-valid.

## Traceability Matrix

| Requirement | Design | Tasks | Tests | Integration |
| --- | --- | --- | --- | --- |
| R-01 binding | D-02, D-04.1 | T1, T2 | TC-01–TC-05 | INT-01, INT-02 |
| R-02 eligibility | D-04.2 | T3 | TC-06, TC-07 | INT-01, INT-02 |
| R-03 assets | D-04.3 | T4 | TC-08–TC-10 | INT-03 |
| R-04 discrimination | D-03 | T1, T5 | TC-11–TC-13 | INT-01–INT-03 |
| R-05 hashing | D-02, D-03 | T1, T5 | TC-14 | INT-01 |
| R-06 STOP | D-05 | T5, T6 | TC-15–TC-17 | INT-02, INT-04 |
| R-07 single owner | D-05 | T6 | TC-15–TC-17 | INT-04 |
| R-08 pure boundary | D-06 | T7 | TC-18 | INT-04 |
| R-09 no persistence | D-08 | T7 | TC-20 | INT-04 |
| R-10 post-fetch audit | D-09 | T7 | TC-20 | INT-04 |
| R-11 Harness | D-07 | T7, T8 | TC-19 | INT-04 |
| R-12 terminology | D-01, D-10 | T8 | TC-20 | INT-01–INT-04 |

## Risks and Rollback

| Risk | Control |
| --- | --- |
| second readiness algorithm | compatibility wrapper delegates; duplicated old body is removed |
| gate re-derives planner truth | only plan outcome/warnings/required roles are consumed |
| caller treats `READY` as quality acceptance | binary eligibility wording and forbidden lifecycle/acceptance fields |
| diagnostic id changes semantics | explicit three-field semantic projection |
| future post-fetch scope repeats owners | D1 requires a demonstrated gap and fully projected schema |

Runtime rollback for the future implementation is to restore the existing `require_current_video_plan()` body and remove `src/ai_video/quality_gates/` plus its tests/policy category. v3 itself is docs-only and has no runtime rollback or migration.
