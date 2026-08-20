# Shot Readiness Gate — Design v3

Status: proposed v3; paired with `requirements.md`

Owner: Main Agent planning-side pre-submit readiness

## D-01 — Architecture Position

```text
canonical Shot / Asset / Review / policy projections
  -> VideoPlanningRequest.create()
  -> VideoPlanner.plan()                         # owns proposal truth
  -> ShotReadinessGate.evaluate()                # owns current-plan eligibility
  -> require_ready() / compatibility STOP seam
  -> existing Router / Provider / materializer / composition / render
  -> candidate validation / activation
  -> P6 Review / Repair -> human Pilot Reality Gate
```

The gate is outside Production lifecycle ownership. It never selects a Provider, reads canonical stores, writes evidence, activates a candidate, or accepts quality. The Main Agent must rebuild the current `VideoPlanningRequest` from canonical owners before evaluation.

## D-02 — Request Schema and Semantic Hash

```python
class ShotReadinessRequest(StrictModel):
    request_id: str = Field(pattern=SAFE_ID)  # diagnostic only
    current_request: VideoPlanningRequest
    plan: VideoGenerationPlan
    contract_version: Literal["shot-readiness-gate/1"]
    request_content_hash: str = Field(pattern=SHA256)

    @classmethod
    def create(cls, **values: object) -> "ShotReadinessRequest": ...
```

`create()` computes the hash from this exact semantic projection:

```python
{
    "contract_version": "shot-readiness-gate/1",
    "current_request_content_hash": current_request.request_content_hash,
    "plan_hash": plan.plan_hash,
}
```

Neither the outer `request_id` nor nested `current_request.request_id` participates. Evaluation separately verifies both nested semantic seals; hashing pointers alone does not make forged nested models valid.

## D-03 — Result and Discriminated Outcomes

### Common enums

```python
class ReadinessStatus(str, Enum):
    READY = "ready"
    BLOCKED = "blocked"

class CheckSeverity(str, Enum):
    PASS = "pass"
    BLOCKED = "blocked"

class ShotReadinessCheckId(str, Enum):
    REQUEST_PLAN_BINDING = "request_plan_binding"
    PLAN_ELIGIBILITY = "plan_eligibility"
    REQUIRED_ASSET_READINESS = "required_asset_readiness"

class ReadinessBlockedReason(str, Enum):
    READINESS_REQUEST_SEAL_INVALID = "readiness_request_seal_invalid"
    REQUEST_SEAL_INVALID = "request_seal_invalid"
    PLAN_SEAL_INVALID = "plan_seal_invalid"
    PLAN_ID_INVALID = "plan_id_invalid"
    PLAN_SOURCE_STALE = "plan_source_stale"
    TARGET_SHOT_STALE = "target_shot_stale"
    CONTRACT_VERSION_UNSUPPORTED = "contract_version_unsupported"
    PLAN_BLOCKED = "plan_blocked"
    HUMAN_REVIEW_UNRESOLVED = "human_review_unresolved"
    REQUIRED_ASSET_MISSING = "required_asset_missing"
```

### Payloads

```python
class RequestPlanBindingPayload(StrictModel):
    readiness_request_seal_valid: bool
    request_seal_valid: bool
    plan_seal_valid: bool
    plan_id_valid: bool
    source_request_matches: bool
    target_shot_id_matches: bool
    target_shot_revision_matches: bool
    target_shot_content_hash_matches: bool
    contract_versions_supported: bool

class PlanEligibilityPayload(StrictModel):
    plan_outcome: PlanOutcome
    unresolved_human_review: bool
    warnings: tuple[PlanWarning, ...]

class RequiredAssetReadinessPayload(StrictModel):
    required_roles: tuple[AssetRole, ...]
    ready_roles: tuple[AssetRole, ...]
    missing_roles: tuple[AssetRole, ...]
```

Role tuples preserve the plan's canonical order. If the plan repeats a role, result normalization keeps the first occurrence only; no set iteration may enter the hash.

### True discriminator binding

```python
class RequestPlanBindingOutcome(StrictModel):
    check_id: Literal[ShotReadinessCheckId.REQUEST_PLAN_BINDING]
    severity: CheckSeverity
    reasons: tuple[ReadinessBlockedReason, ...] = ()
    payload: RequestPlanBindingPayload

class PlanEligibilityOutcome(StrictModel):
    check_id: Literal[ShotReadinessCheckId.PLAN_ELIGIBILITY]
    severity: CheckSeverity
    reasons: tuple[ReadinessBlockedReason, ...] = ()
    payload: PlanEligibilityPayload

class RequiredAssetReadinessOutcome(StrictModel):
    check_id: Literal[ShotReadinessCheckId.REQUIRED_ASSET_READINESS]
    severity: CheckSeverity
    reasons: tuple[ReadinessBlockedReason, ...] = ()
    payload: RequiredAssetReadinessPayload

ShotReadinessOutcome = Annotated[
    RequestPlanBindingOutcome
    | PlanEligibilityOutcome
    | RequiredAssetReadinessOutcome,
    Field(discriminator="check_id"),
]
```

All payload/outcome/result models inherit frozen `StrictModel` and reject extras. Outcome validators bind severity and reason codes to their payload booleans; a caller cannot label a failed payload `PASS`.

### Result

```python
class ShotReadinessResult(StrictModel):
    source_readiness_request_hash: str
    status: ReadinessStatus
    checks: tuple[ShotReadinessOutcome, ...]
    blocked_reasons: tuple[ReadinessBlockedReason, ...]
    contract_version: Literal["shot-readiness-gate/1"]
    result_hash: str

    @classmethod
    def create(cls, **values: object) -> "ShotReadinessResult": ...
```

Validation requires exactly three checks in the D-04 order, no duplicates, aggregate status equality, and the ordered de-duplicated union of check reasons. `result_hash` is `canonical_sha256(model_dump(exclude={"result_hash"}))`. The result omits diagnostic `request_id`.

`source_readiness_request_hash` must equal the evaluated `ShotReadinessRequest.request_content_hash`; it is not another copy of the nested planner request hash.

## D-04 — Evaluation Algorithm

`ShotReadinessGate.evaluate(request)` always returns all three outcomes. It does not short-circuit diagnostics, but a caller must not execute downstream work before `require_ready(result)` succeeds.

### D-04.1 `REQUEST_PLAN_BINDING`

Compute independently:

1. outer readiness request hash equals the exact D-02 semantic projection;
2. current request hash equals the accepted Video Planner semantic hash, which excludes its diagnostic id and hash field;
3. plan hash equals the accepted plan semantic hash;
4. `plan_id == f"plan-{plan.source_request_content_hash[:24]}"`;
5. plan source hash equals current request hash;
6. Shot id/revision/content hash match current request target Shot;
7. request/plan versions are both `video-planner/2`.

Any false value blocks. `ShotReadinessGate.evaluate()` must perform this recomputation even for an existing model instance so `model_copy(update={"request_content_hash": ...})` cannot bypass the seal. This check consumes hashes/identities only; it never calls `VideoPlanner.plan()`.

### D-04.2 `PLAN_ELIGIBILITY`

```text
plan.outcome == BLOCKED                   -> BLOCKED / PLAN_BLOCKED
REQUIRES_HUMAN_REVIEW in plan.warnings   -> BLOCKED / HUMAN_REVIEW_UNRESOLVED
otherwise                                -> PASS
```

The payload carries the plan warnings for audit. The gate does not change their meaning, recompute confidence, or interpret strategy/capability/reason codes.

### D-04.3 `REQUIRED_ASSET_READINESS`

For each role already present in `plan.required_asset_roles`, invoke one shared pure role-readiness seam against `current_request`.

The implementation must preserve the existing semantics currently used by `require_current_video_plan()`:

- exact Character/Scene owner match;
- exact previous Shot terminal id and owner match;
- exact target-Shot final-visual role binding;
- current Review projection for reusable plate.

Any missing role blocks with `REQUIRED_ASSET_MISSING`. The gate must not add roles based on generation mode, continuity, character ids, or its own heuristics.

### D-04.4 Aggregation

```text
any check BLOCKED -> ReadinessStatus.BLOCKED
all checks PASS   -> ReadinessStatus.READY
```

No `WARNING`, `NOT_EVALUATED`, confidence score, recommendation, repair instruction, or next action exists.

## D-05 — STOP API and Single-Owner Migration

```python
class ShotReadinessGate:
    CONTRACT_VERSION = "shot-readiness-gate/1"

    def evaluate(self, request: ShotReadinessRequest) -> ShotReadinessResult: ...


def require_ready(result: ShotReadinessResult) -> None:
    """Raise PLANNING_PREFLIGHT_BLOCKED unless result is sealed and READY."""
```

Future implementation sequence:

1. Add the typed gate and tests.
2. Move `_current_review`, exact final-visual binding helpers, `_available_role`, and `_required_role_is_available` from `video_planner.py` into `src/ai_video/planning/_asset_readiness.py`. That module is the single cycle-safe pure owner imported by both planner and gate; no compatibility-only duplicate remains.
3. Replace the body of `require_current_video_plan()` with construction/evaluation plus `require_ready()`.
4. Keep `prepare_shot_for_existing_production()` delegating through the compatibility function.
5. Delete old duplicated seal/binding/eligibility/asset checks from the compatibility wrapper.

The compatibility function must preserve the current public signature and `AiVideoError` code/message class. It may report the gate's ordered blocked reasons in `technical_detail`, but must not expose secrets or raw traceback.

## D-06 — Import and Side-Effect Boundary

Planned package:

```text
src/ai_video/quality_gates/
├── __init__.py
├── _readiness_models.py
└── shot_readiness_gate.py
```

Forbidden imports include:

- `ai_video.production.state_commit` and every `_state_commit_*`;
- `production.video`, `video_generation`, `local_video`, `paid_provider`, Provider adapters, `shot_router`, Registry, dependency, composition, HyperFrames, Review, Manifest, paths, and project readers;
- CLI, ComfyUI/ffmpeg transports, `os.environ`, subprocess, network clients, keyring, and crypto KDFs.

Production code must not import `ai_video.quality_gates`. The planning compatibility wrapper is the only permitted higher-level consumer.

## D-07 — Harness Routing Contract

The runtime implementation change must add `shot_readiness_gate_tests` and a `shot_readiness_gate` category to `.agent/harness/policy.yaml`, plus routing tests in `tests/test_agent_harness.py`.

```yaml
shot_readiness_gate:
  patterns:
    - src/ai_video/quality_gates/**
    - tests/fixtures/shot_readiness_factory.py
    - tests/test_shot_readiness_gate.py
  check_ids:
    - shot_readiness_gate_tests
    - task_architecture_gate

video_planning:
  # existing patterns remain unchanged
  check_ids:
    - video_planner_tests
    - shot_readiness_gate_tests
    - task_architecture_gate
```

Because T6 changes `src/ai_video/planning/video_planner.py`, the existing `video_planning` category must explicitly add `shot_readiness_gate_tests`; an overlapping path claim in prose is not enough. Harness tests must prove that both a quality-gate path and a planning compatibility path resolve to their exact combined check sets. A policy change itself also routes through `harness_tests` as existing control-plane truth requires.

## D-08 — No Persistence

`ShotReadinessResult` is not a `VersionedArtifact`. It has no artifact id, receipt id, path, pointer, lifecycle phase, activation flag, or committer handoff. It may remain in Main Agent memory/logging under caller policy, but no v3 code writes it.

Adding a hash field to `VideoGenerationAttemptState` would change Manifest serialization, schema compatibility, reopen validation, recovery, and writer inputs. That is explicitly D2, not an additive optional detail.

## D-09 — Post-Fetch Owner Audit

No `VideoQualityGate` class or request exists in v3.

| Proposed v2 check | Existing owner | v3 decision |
| --- | --- | --- |
| fetch fingerprint | `VideoFetchReceipt` / `LocalVideoFetchReceipt` validators and reopen | remove |
| submission/observation linkage | receipt constructor + `record_*_video_fetch_result()` | remove |
| artifact SHA/size linkage | typed fields + committer-held bytes verification | remove |
| expected content type | `VideoSubmission` + `VideoFetchReceipt.create()` | remove |
| identity/continuity/motion/visual quality | P6 Review / Pilot and relevant typed continuity owners | forbidden scope |

The remote receipt contains only `submission_fingerprint`, not a submission projection. A pure gate cannot recover `expected_content_type` from that hash without IO or a new projection. Local receipt content type is already constrained to `video/mp4`.

## D-10 — Compatibility and Unchanged Contracts

- No Manifest or Registry schema change.
- No committer, activation, recovery, Provider, timeline, renderer, dependency, Review, CLI, or artifact-layout change.
- Actual activation remains `prepare_video_activation_candidate()` then `activate_video_candidate()`.
- `READY` means only pre-submit eligibility.
- Gate package routing is planned but policy remains unchanged in this docs-only revision.
