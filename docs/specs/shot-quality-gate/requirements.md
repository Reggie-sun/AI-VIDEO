# Shot Quality Gate + Video Quality Gate — Requirements (v2)

Status: revised after Codex review; scope reduced
Owner: AI-VIDEO Production Harness extension
Target module path: `src/ai_video/quality_gates/` (new top-level package)

## 1. Context (revised)

After the v1 spec received SCORE 2/10 from Codex (13 ambiguities, 6 ownership concerns, 10 risks), the v2 spec reduces scope to only what current types allow without schema additions.

Verified facts (read directly from source):

- `FetchedVideoCandidate` ([src/ai_video/production/video_generation.py:36-39](../../src/ai_video/production/video_generation.py)) is `relative_path: Path` + `receipt: VideoFetchReceipt | LocalVideoFetchReceipt`. No duration/fps/dimensions/mime/terminal_frame_asset_id fields.
- `VideoFetchReceipt` ([src/ai_video/production/video.py:1035-1056](../../src/ai_video/production/video.py)) carries `submission_fingerprint`, `observation_fingerprint`, `paid_submit_receipt_fingerprint`, `provider_file_id`, `content_type` (Literal "video/mp4" / "video/quicktime"), `size_bytes`, `artifact_sha256`, `fetched_at`, `fetch_fingerprint`. No duration/fps/dimensions/terminal.
- `PreviousShotState` ([src/ai_video/planning/_planner_models.py:129](../../src/ai_video/planning/_planner_models.py)) has only `previous_shot_id`, `previous_shot_content_hash`, `is_same_scene`, `is_same_story_beat`, `is_same_action`, `is_angle_change`, `has_terminal_frame_asset_id`, `semantic_jump`. No wardrobe/props strings.
- `AvailableAsset` ([src/ai_video/planning/_planner_models.py:118](../../src/ai_video/planning/_planner_models.py)) has `canonical_owner_id: str | None` — usable for identity verification.
- `production.video_generation` transitively imports `production.video`, `production.local_video`, `production.paid_provider` — i.e. importing `video_generation` from gates would break the import boundary.

Therefore the v2 gate surfaces only:

| Gate | Checks |
|---|---|
| Shot | `IDENTITY_ANCHOR`, `STRATEGY`, `COMPLEXITY` |
| Video | `RECEIPT_INTEGRITY`, `CONTENT_TYPE_BINDING` |

All other checks are deferred to D1–D5 in [tasks.md](tasks.md#out-of-scope-tasks-deferred).

## 2. Who is affected

| Role | Pain today | After this slice |
|---|---|---|
| Main Agent / Codex | Cannot cheaply stop a flawed Shot before paying a Provider | Calls `ShotQualityGate.evaluate(request)` and respects `BLOCKED`/`WARNING`/`NOT_EVALUATED` status |
| Production Committer | Activates whatever the Provider returned without structural sanity | Optionally accepts `VideoQualityReceipt` via new optional parameter; hash stored as advisory pointer on `VideoGenerationAttemptState` |
| P6 Review | Receives only post-render evidence | Receives gate receipt hashes via Manifest pointers (P6 may optionally correlate) |
| Provider budget | Wasted on clearly-flawed Shots | Blocked at gate; budget reserved for viable Shots |

## 3. What this slice must deliver

1. `ShotQualityGate.evaluate(request) -> ShotQualityReceipt` — pure, deterministic, no IO, no Production imports.
3. `VideoQualityGate.evaluate(request) -> VideoQualityReceipt` — pure, deterministic, no IO, no Production imports.
4. Typed `GateStatus` enum: `PASS` / `WARNING` / `BLOCKED` / `NOT_EVALUATED`.
5. Typed check IDs (`ShotCheckId` / `VideoCheckId`) for each individual check.
6. Receipts are `VersionedArtifact` with `content_hash` (reusing existing seal pattern).
7. Three deterministic Shot checks and two deterministic Video checks.
8. `NOT_EVALUATED` is a **first-class final status**, not a downgrade to `PASS`.
9. Architecture Gate extension enforcing import blacklist on `src/ai_video/quality_gates/**`.
10. Minimal committer seam: two optional fields on `VideoGenerationAttemptState` + two optional parameters on existing committer methods.

## 4. Explicitly out of scope

- Calling any Provider.
- Selecting a Provider / Profile / Capability.
- Reading `ARK_API_KEY`, `os.environ`, or `keyring`.
- Writing Manifest, Asset Registry, Timeline, dependency graph, or any durable artifact.
- Replacing `production.review.adjudicate_review_evidence` or `evaluate_final_acceptance`.
- Replacing `ShotVisualResolver` / `VideoGenerationResolver` / `VideoPlanner` / `HyperFrames`.
- Continuity checks (dropped; defer to D1).
- Capability binding checks (dropped; defer to D2).
- Multi-usage reference detection (dropped; defer to D3).
- VLM/Human `IDENTITY_DRIFT` evaluation (dropped; defer to D4).
- Scene reference warning (dropped; defer to D5).
- Automatic retry, repair, or remediation.

## 5. Functional requirements

### FR-1 — Receipts are sealed VersionedArtifact

```python
class ShotQualityReceipt(VersionedArtifact):
    receipt_id: str = Field(min_length=1)
    gate_name: Literal["shot_quality_gate"] = "shot_quality_gate"
    gate_version: Literal["shot-quality-gate/1"] = "shot-quality-gate/1"
    status: GateStatus
    checks: tuple[ShotCheckOutcome, ...]
    blocked_reasons: tuple[BlockedReason, ...] = ()
    warnings: tuple[GateWarning, ...] = ()

class VideoQualityReceipt(VersionedArtifact):
    receipt_id: str = Field(min_length=1)
    gate_name: Literal["video_quality_gate"] = "video_quality_gate"
    gate_version: Literal["video-quality-gate/1"] = "video-quality-gate/1"
    status: GateStatus
    checks: tuple[VideoCheckOutcome, ...]
    blocked_reasons: tuple[BlockedReason, ...] = ()
    warnings: tuple[GateWarning, ...] = ()
```

Both use `extra="forbid"` on the receipt itself and on every nested check outcome. Content-hash sealing follows existing `production.hashing.seal_artifact` pattern.

### FR-2 — Typed per-check payloads (no `Mapping[str, object]`)

Each check outcome carries a **typed frozen** payload — not a loose mapping. This addresses Codex risk: payload fields can't smuggle in `provider_*` / `manifest_*` / `accepted` keys.

```python
class IdentityAnchorPayload(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    character_ids: tuple[str, ...]
    character_reference_asset_ids: tuple[str, ...]
    matched_owner_ids: tuple[str, ...]

class StrategyPayload(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    plan_outcome: str | None       # PROPOSED | BLOCKED | None
    generation_mode: str | None    # generation mode value or None
    has_important_character: bool

class ComplexityPayload(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    intent_word_count: int = Field(ge=0)
    directive_count: int = Field(ge=0)
    intent_limit: int = Field(ge=1)
    directive_limit: int = Field(ge=1)

class ReceiptIntegrityPayload(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    receipt_kind: Literal["video", "local_video"]
    fetch_fingerprint_matches: bool
    submission_observation_linked: bool
    artifact_sha256_well_formed: bool

class ContentTypeBindingPayload(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    receipt_content_type: Literal["video/mp4", "video/quicktime"]
    expected_content_type: str | None
    matches: bool | None    # None when no expected type was declared
```

```python
class ShotCheckOutcome(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    check_id: ShotCheckId
    severity: CheckSeverity
    reason_codes: tuple[BlockedReason | GateWarning, ...] = ()
    payload: IdentityAnchorPayload | StrategyPayload | ComplexityPayload
    message: str = Field(min_length=1, max_length=400)

class VideoCheckOutcome(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    check_id: VideoCheckId
    severity: CheckSeverity
    reason_codes: tuple[BlockedReason | GateWarning, ...] = ()
    payload: ReceiptIntegrityPayload | ContentTypeBindingPayload
    message: str = Field(min_length=1, max_length=400)
```

### FR-3 — Status aggregation rule (NOT_EVALUATED is first-class)

Final `status` from per-check severities, in priority order:

1. If any check severity == `BLOCKED` → `BLOCKED`.
2. Else if any check severity == `NOT_EVALUATED` → `NOT_EVALUATED`.
3. Else if any check severity == `WARNING` → `WARNING`.
4. Else → `PASS`.

`PASS` is reached only when every check is `PASS`. This fixes the v1 contradiction where Case 2 (env Shot, no plan) expected `PASS` but produced `NOT_EVALUATED`.

### FR-4 — Three Shot checks

| Check ID | Deterministic input | Severity | Failure case |
|---|---|---|---|
| `IDENTITY_ANCHOR` | `target_shot.character_ids`, `available_assets` filtered by `AssetRole.CHARACTER_REFERENCE` | `BLOCKED` | At least one character in `character_ids` has no character-reference asset whose `canonical_owner_id` matches that character id |
| `STRATEGY` | `target_shot`, `video_generation_plan` | `BLOCKED` (plan is BLOCKED or T2V with important character) / `WARNING` (R2V without character / plan missing required mode) / `NOT_EVALUATED` (plan is None) | See [design.md §5](design.md#5-shot-quality-gate-algorithm) |
| `COMPLEXITY` | `target_shot.intent` (token count), `target_shot.motion_directives` length | `WARNING` if `intent_word_count > INTENT_WORD_LIMIT (24)` or `directive_count > DIRECTIVE_LIMIT (4)`, else `PASS` | Heuristic only |

### FR-5 — Two Video checks

| Check ID | Deterministic input | Severity | Failure case |
|---|---|---|---|
| `RECEIPT_INTEGRITY` | `FetchedVideoCandidate.receipt` | `BLOCKED` if `fetch_fingerprint` does NOT match `canonical_sha256(model_dump(exclude={"fetch_fingerprint"}))`, OR `submission_fingerprint` ≠ `observation_fingerprint`, OR `artifact_sha256` is malformed; else `PASS` | Hash tampering or pointer mismatch |
| `CONTENT_TYPE_BINDING` | `receipt.content_type`, `receipt.submission.expected_content_type` (when available) | `BLOCKED` if expected type was declared and differs from receipt's type; `PASS` if expected type matches or no expected type declared | Provider content type does not match declared intent |

Both checks operate **only** on existing receipt fields. No duration/fps/dimension assertions.

### FR-6 — Pure determinism

- Receipts use `VersionedArtifact.content_hash` (existing seal).
- Same `request_content_hash` → same `receipt.content_hash`.
- Two calls with identical inputs (including `receipt_id`) → byte-identical receipts.
- No filesystem, network, secret, clock, or random state enters the function.
- No transitive import of `os.environ`, `keyring`, `subprocess`, `httpx`, `requests`.

### FR-7 — Reason codes are typed enums

```python
class GateStatus(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    BLOCKED = "blocked"
    NOT_EVALUATED = "not_evaluated"

class CheckSeverity(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    BLOCKED = "blocked"
    NOT_EVALUATED = "not_evaluated"

class ShotCheckId(str, Enum):
    IDENTITY_ANCHOR = "identity_anchor"
    STRATEGY = "strategy"
    COMPLEXITY = "complexity"

class VideoCheckId(str, Enum):
    RECEIPT_INTEGRITY = "receipt_integrity"
    CONTENT_TYPE_BINDING = "content_type_binding"

class BlockedReason(str, Enum):
    MISSING_IDENTITY_ANCHOR = "missing_identity_anchor"
    STRATEGY_CONTRADICTS_SHOT = "strategy_contradicts_shot"
    RECEIPT_HASH_MISMATCH = "receipt_hash_mismatch"
    RECEIPT_POINTER_MISMATCH = "receipt_pointer_mismatch"
    RECEIPT_HASH_MALFORMED = "receipt_hash_malformed"
    CONTENT_TYPE_MISMATCH = "content_type_mismatch"

class GateWarning(str, Enum):
    COMPLEXITY_HIGH = "complexity_high"
    STRATEGY_RISKY = "strategy_risky"
    STRATEGY_PLAN_MISSING = "strategy_plan_missing"
```

### FR-8 — Caller-supplied receipt_id is deterministic

`receipt_id` is caller-supplied (or auto-derived as `f"{gate_name}-{request_content_hash[:16]}"`). It is part of the canonical payload and goes into `content_hash`. Replays with the same `receipt_id` produce identical receipts.

### FR-9 — Reuse AI-VIDEO types; only add minimum schema

Inputs reuse existing types:

- `Shot`, `Character`, `Scene`, `AvailableAsset`, `PreviousShotState`, `VideoGenerationPlan` (from `planning._planner_models`).
- `FetchedVideoCandidate`, `VideoFetchReceipt`, `LocalVideoFetchReceipt`, `VideoSubmission` (from `production.video_generation` and `production.video`).

New types (in `_gate_models.py`):

- Enums in FR-7.
- Typed payloads in FR-2.
- `ShotCheckOutcome`, `VideoCheckOutcome`.
- `ShotQualityReceipt`, `VideoQualityReceipt` (VersionedArtifact subclasses).

New fields on existing Production types (additive, all optional, all `None` default — no breakage of existing call sites):

| File | Field |
|---|---|
| `production/_lifecycle_schema.py` `VideoGenerationAttemptState` | `pre_submit_gate_receipt_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")` |
| `production/_lifecycle_schema.py` `VideoGenerationAttemptState` | `post_fetch_gate_receipt_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")` |

New optional parameters on existing committer methods:

| Method | New optional parameter |
|---|---|
| `ProductionStateCommitter.begin_video_generation(...)` | `pre_submit_gate_receipt: ShotQualityReceipt | None = None` |
| `ProductionStateCommitter.commit_video_activation(...)` | `post_fetch_gate_receipt: VideoQualityReceipt | None = None` |

When supplied, committer validates:

1. `receipt.content_hash` is well-formed.
2. `receipt.gate_name` matches the expected gate.
3. If `BLOCKED`, refuse the operation (`AiVideoError(PRODUCTION_STATE_INVALID, ...)`).

When `None`, committer proceeds exactly as today.

### FR-10 — Production ownership boundary (gate side)

`src/ai_video/quality_gates/**` MUST NOT import:

- `ai_video.production.state_commit` or any `_state_commit_*`
- `ai_video.production.dependency`
- `ai_video.production.composition`
- `ai_video.production.hyperframes`
- `ai_video.production.manifest`
- `ai_video.production.registry`
- `ai_video.production.shot_router`
- `ai_video.production.video` (the producer / request schema)
- `ai_video.production.seedance` / `seedance_*` / `minimax_*` / `comfy_*` / `elevenlabs` / `local_video`
- `ai_video.production.paid_provider` / `paid_provider_gate`
- `ai_video.production.video_generation` (transitively imports `production.video` and `local_video` and `paid_provider`)
- `ai_video.comfy_client`, `ai_video.ffmpeg_tools`, `ai_video.cli`
- `os.environ`, `subprocess`, `httpx`, `requests`, `urllib`
- `keyring`, `cryptography.hazmat.primitives.kdf`

Allowed imports:

- `ai_video.production.models` — read-only types (`Shot`, `Character`, `Scene`, `StrictModel`, `VisualStrategy`, `VersionedArtifact`).
- `ai_video.production.hashing` — `canonical_sha256`.
- `ai_video.planning._planner_models` — `AvailableAsset`, `PreviousShotState`, `VideoGenerationPlan`, `GenerationMode`, `PlanOutcome`.
- `ai_video.errors` — `AiVideoError`, `ErrorCode`.
- Standard library + pydantic.

Enforced by AST scan in `tests/test_architecture_gate.py` (extension).

The reverse direction (Production importing quality_gates) is **allowed** — committer may import receipts for the optional handoff parameter. Direction is asymmetric.

### FR-11 — Receipt hashes flow through committer only if supplied

If caller passes `pre_submit_gate_receipt=` / `post_fetch_gate_receipt=` to committer:

- Validates `gate_name`, `content_hash` shape, and BLOCKED status (FR-9).
- On accept: persists `pre_submit_gate_receipt_hash` / `post_fetch_gate_receipt_hash` on the new attempt state.
- On reject: raises `AiVideoError(PRODUCTION_STATE_INVALID)`.

If caller passes `None`:

- Committer proceeds exactly as today.
- The hash field stays `None`.

The committer NEVER creates a receipt. Receipts are caller-owned; committer only stores their hashes when explicitly handed one.

### FR-12 — Integration evidence

`integration.md` documents at least one worked example for each gate and at least one committer handoff example.

## 6. Acceptance criteria

1. AC-1 — Shot with important character + no reference asset → `BLOCKED`, `MISSING_IDENTITY_ANCHOR` in `blocked_reasons`.
2. AC-2 — Important character + reference asset with mismatched `canonical_owner_id` (asset belongs to a different character) → `BLOCKED` with `MISSING_IDENTITY_ANCHOR`. `matched_owner_ids` is empty.
3. AC-3 — Environment shot (no characters) + no plan → `NOT_EVALUATED` (STRATEGY check returns NOT_EVALUATED because plan is missing).
4. AC-4 — Important character + plan with `outcome=BLOCKED` → Shot Gate `BLOCKED` with `STRATEGY_CONTRADICTS_SHOT`.
5. AC-5 — Important character + plan `generation_mode=TEXT_TO_VIDEO` → `BLOCKED` with `STRATEGY_CONTRADICTS_SHOT`.
6. AC-6 — Fetched video with `fetch_fingerprint` not matching payload → Video Gate `BLOCKED` with `RECEIPT_HASH_MISMATCH`.
7. AC-7 — Fetched video whose `content_type` does not match `submission.expected_content_type` → Video Gate `BLOCKED` with `CONTENT_TYPE_MISMATCH`.
8. AC-8 — Both gates are pure: same `request_content_hash` and `receipt_id` → same `content_hash`; two calls are byte-identical.
9. AC-9 — All receipts and check outcomes reject forbidden fields via `extra="forbid"` (including typed payload classes).
10. AC-10 — Architecture Gate blacklist forbids `state_commit*` / `dependency` / `composition` / `hyperframes` / `registry` / `shot_router` / `video` / `video_generation` / Provider adapters / `paid_provider` / `comfy_client` / `ffmpeg_tools` / `cli` / `os.environ` / `keyring` / `subprocess` / `httpx` / `requests` imports from `src/ai_video/quality_gates/**`.
11. AC-11 — Committing a `BLOCKED` `VideoQualityReceipt` to `commit_video_activation` raises `AiVideoError(PRODUCTION_STATE_INVALID)`.
12. AC-12 — Committing a `PASS` receipt succeeds and persists the receipt hash on the attempt state; calling the same commit without the receipt still succeeds and leaves the hash `None`.

## 7. Verification plan

- Unit tests: `tests/test_quality_gates.py` (Cases 1–7 plus determinism + forbidden fields + architecture gate).
- Comitter seam tests: `tests/test_state_commit_gate_receipt.py` (AC-11, AC-12).
- Pure-function smoke: same request + receipt_id twice → identical receipt.
- Architecture gate: AST scan extension in `tests/test_architecture_gate.py`.
- Negative tests: forbidden fields raise `ValidationError`; forbidden imports raise test failure with file:line.
- Forbidden-call test: monkeypatch the blacklisted modules; gate functions must not trigger import.

## 8. Risk & rollback

| Risk | Mitigation |
|---|---|
| Gate becomes a stealth Review/Repair replacement | Forbidden fields (incl. typed payloads with `extra="forbid"`); no `accepted`/`activated` outputs |
| Gate starts writing Manifest | FR-10 import blacklist + AST gate; committer stores only hashes, never payloads |
| Committer becomes the de-facto gate owner | Gate runs outside committer; committer only validates BLOCKED status and stores hash; receipt lives with caller |
| Receipt hash mismatch indicates tampering | RECEIPT_INTEGRITY is `BLOCKED`; committer refuses; caller must retry from a fresh receipt |
| Receipt v1 vs v2 evolution | `gate_version` field pins the contract; mismatched versions are rejected |
| Production module accidentally imports gate | FR-10 is asymmetric; gate side forbids production imports; reverse direction is allowed but not required |

Rollback: delete `src/ai_video/quality_gates/`, drop the 2 optional fields from `VideoGenerationAttemptState`, drop the 2 optional parameters from committer methods, drop the helper module. No required-schema changes are introduced.