# Shot Readiness Gate — Test Spec v3

Status: paired with requirements R-01–R-12, design D-01–D-10, and tasks T1–T8

Planned runtime tests use `python -m pytest -p no:cacheprovider`. There are exactly twenty named contract cases.

## Fixtures

Planned fixture file: `tests/fixtures/shot_readiness_factory.py`.

It may reuse the accepted planning fixture builders for `Shot`, `AvailableAsset`, `VideoPlanningRequest`, and `VideoGenerationPlan`. Builders must call the accepted constructors/sealing helpers; they must not bypass typed validation with raw JSON parsing.

## Request/Plan Binding

### TC-01 — Current request and plan are ready

Given a valid current request, its valid `PROPOSED` plan, and all plan-required assets, evaluation returns `READY`; all three checks are `PASS`.

### TC-02 — Invalid outer or nested request seal blocks

Parameterize:

- forge only `ShotReadinessRequest.request_content_hash` through `model_copy` → `READINESS_REQUEST_SEAL_INVALID`;
- forge only `current_request.request_content_hash` → `REQUEST_SEAL_INVALID`.

Both return `REQUEST_PLAN_BINDING/BLOCKED`; a well-formed 64-character hash is not accepted merely because pydantic field validation succeeded.

### TC-03 — Invalid plan seal or plan id blocks

Parameterize a forged `plan_hash` and a correctly rehashed but non-deterministic `plan_id`. Expected reasons are `PLAN_SEAL_INVALID` and `PLAN_ID_INVALID` respectively.

### TC-04 — Stale source request blocks

Build a valid plan for request A and evaluate against semantically changed current request B. Expect `PLAN_SOURCE_STALE` even when the Shot id is unchanged.

### TC-05 — Stale target Shot identity blocks

Parameterize target Shot id, revision, and content hash mismatch. Every branch returns `TARGET_SHOT_STALE`; the payload identifies the exact false comparison.

## Plan Eligibility

### TC-06 — Planner-blocked outcome stays blocked

Given a valid sealed plan with `outcome=BLOCKED`, expect `PLAN_ELIGIBILITY/BLOCKED` and `PLAN_BLOCKED`. Do not assert any gate-derived strategy reason.

### TC-07 — Human review boundary

Parameterize:

- `REQUIRES_HUMAN_REVIEW` present → `BLOCKED/HUMAN_REVIEW_UNRESOLVED`;
- only `STATIC_FALLBACK_REQUIRES_REVIEW` present on an otherwise accepted plan → eligibility `PASS` because the accepted planner contract treats it as resolved audit visibility.

## Required Assets

### TC-08 — Missing plan-declared role blocks

Remove one exact role declared in `plan.required_asset_roles`. Expect `REQUIRED_ASSET_MISSING` and ordered `missing_roles`.

### TC-09 — Wrong Character/Scene/final-visual binding blocks

Parameterize:

- Character reference owned by another Character;
- Scene reference owned by another Scene;
- keyframe owned by another Shot;
- keyframe not bound to the target Shot's `final_visual` role;
- reusable plate without matching current Review projection.

Each must block. Reference availability must never be promoted to Final Shot Visual readiness.

### TC-10 — Wrong terminal owner blocks

For an accepted exact-terminal plan, provide the right terminal asset id with an unrelated `canonical_owner_id`. Expect `REQUIRED_ASSET_MISSING`.

## Schema and Determinism

### TC-11 — Discriminator rejects wrong payload type

For each check id, replace its payload with either of the other two payloads. `ShotReadinessResult.model_validate()` must raise `ValidationError` for all six wrong combinations.

### TC-12 — Result structure is exact

Reject missing check, duplicate check, reordered checks, extra fourth check, empty checks, and extra fields. The only accepted order is binding, eligibility, assets.

### TC-13 — Status/reasons cannot contradict payloads

Reject:

- failed payload labeled `PASS`;
- all-pass checks with result `BLOCKED`;
- blocked check with result `READY`;
- `blocked_reasons` missing a check reason;
- extra or reordered `blocked_reasons`.

### TC-14 — Diagnostic identity is non-semantic

Build two readiness requests that differ only in outer `request_id` and nested `VideoPlanningRequest.request_id`, while their semantic hashes remain equal. Assert identical readiness `request_content_hash`, complete result payload, and `result_hash`.

Changing a semantic current-request field must change the current request hash and therefore the readiness request hash.

## STOP and Compatibility

### TC-15 — `require_ready` rejects forged or blocked result

Parameterize invalid result seal and valid sealed `BLOCKED` result. Both raise `AiVideoError` with `ErrorCode.PLANNING_PREFLIGHT_BLOCKED` and `retryable=False`.

### TC-16 — Compatibility blocked path has zero calls

Run the existing `prepare_shot_for_existing_production()` path for each blocked family: binding, plan eligibility, and required asset readiness. Assert handoff, Router, Provider, placeholder/materializer, composition, and render spies all remain zero.

### TC-17 — Compatibility ready path calls once

For a `READY` result, `require_current_video_plan()` returns `None` and `prepare_shot_for_existing_production()` invokes the existing handoff exactly once with `current_shot` and `plan_hint`. Assert no generated/selected/activated/reviewed/final-acceptance field exists on result.

## Architecture, Harness, and Negative Scope

### TC-18 — Import and side-effect boundary

AST tests scan `src/ai_video/quality_gates/**` and reject every forbidden import in D-06. Scan `src/ai_video/production/**` and reject reverse imports. Monkeypatch clock/random/network/filesystem/Provider surfaces where useful and assert gate evaluation touches none.

### TC-19 — Harness routing

Harness tests prove:

- each planned quality-gate source/test path selects `shot_readiness_gate_tests` + `task_architecture_gate`;
- compatibility seam changes also select both Video Planner and readiness checks;
- the exact command uses `python -m pytest` and the three files in R-11;
- an unmapped quality-gate path cannot silently receive documentation-only checks.

### TC-20 — Owner and terminology audit

Static tests/spec assertions reject:

- `VideoQualityGate`, `RECEIPT_INTEGRITY`, `CONTENT_TYPE_BINDING`, `commit_video_activation`, committer gate parameters, or Manifest gate hash fields in v3 runtime surface;
- `VersionedArtifact`, receipt path/id, activation, accepted/final-acceptance fields in readiness models;
- descriptions claiming identity drift, natural motion, continuity quality, subjective visual quality, or P6 replacement.

The test may allow those strings only in explicit owner-audit/forbidden-context documentation, never as runtime claims or exports.

## Coverage and Verification

Planned line coverage target for the new package is at least 95%, but coverage does not replace TC-01–TC-20 semantics.

Focused command:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_shot_readiness_gate.py \
  tests/test_planning_video_planner.py \
  tests/test_errors.py -q
```

Final acceptance must come from the policy-routed exact staged snapshot or exact commit range. No live Provider, ComfyUI, network, secret, media generation, ffmpeg quality analysis, or browser test belongs to this pure backend slice.
