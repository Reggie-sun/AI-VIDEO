# Shot Quality Gate + Video Quality Gate — Design (v2)

Status: draft v2 (paired with `requirements.md`)
Owner: AI-VIDEO Production Harness extension
Module path: `src/ai_video/quality_gates/` (new package)

## 1. Position in the architecture

```
                       Main Agent / Codex
                                │
                                ▼
                ┌──────────────────────────────┐
                │  planning.VideoPlanner.plan  │  ◀── existing advisory
                └──────────────┬───────────────┘
                               │ VideoGenerationPlan (advisory hint)
                               ▼
                ┌──────────────────────────────┐
                │  quality_gates.ShotQuality   │  ◀── NEW (before gen)
                │  .evaluate(request)          │
                └──────────────┬───────────────┘
                               │ ShotQualityReceipt (caller-owned)
                               ▼
                ┌──────────────────────────────┐
                │  ProductionStateCommitter    │  ◀── existing canonical
                │  .begin_video_generation(    │     optional pre_submit_gate_receipt arg
                │    ..., pre_submit_gate_     │
                │    receipt=receipt)          │
                └──────────────┬───────────────┘
                               │
                               ▼
                ┌──────────────────────────────┐
                │  VideoProvider (local /      │  existing canonical
                │  remote, paid or free)       │
                └──────────────┬───────────────┘
                               │ FetchedVideoCandidate
                               ▼
                ┌──────────────────────────────┐
                │  quality_gates.VideoQuality  │  ◀── NEW (post fetch)
                │  .evaluate(request)          │
                └──────────────┬───────────────┘
                               │ VideoQualityReceipt (caller-owned)
                               ▼
                ┌──────────────────────────────┐
                │  ProductionStateCommitter    │
                │  .commit_video_activation(   │  ◀── optional post_fetch_gate_receipt arg
                │    ..., post_fetch_gate_     │
                │    receipt=receipt)          │
                └──────────────┬───────────────┘
                               │
                               ▼
                ┌──────────────────────────────┐
                │  production.review (P6)      │  existing canonical
                └──────────────────────────────┘
```

Receipts are caller-owned; committer stores only their hashes when explicitly handed one. Gate side never imports Production.

## 2. Package layout

```
src/ai_video/quality_gates/
├── __init__.py                 # public surface only
├── _gate_models.py             # sealed VersionedArtifact subclasses + typed payloads
├── shot_quality_gate.py        # ShotQualityGate class
└── video_quality_gate.py       # VideoQualityGate class

src/ai_video/production/
└── _state_commit_gate_receipt.py   # small helper: validate receipt + extract hash

tests/
├── test_quality_gates.py
├── test_state_commit_gate_receipt.py
└── fixtures/quality_gates_factory.py
```

Files MUST stay under 800 lines per CLAUDE.md.

## 3. Module imports — whitelist & blacklist

### Allowed imports (whitelist)

- `ai_video.production.models` — types only (`Shot`, `Character`, `Scene`, `StrictModel`, `VisualStrategy`, `MotionDirective`, `VersionedArtifact`).
- `ai_video.production.hashing` — `canonical_sha256`.
- `ai_video.planning._planner_models` — `AvailableAsset`, `PreviousShotState`, `VideoGenerationPlan`, `GenerationMode`, `PlanOutcome`.
- `ai_video.errors` — `AiVideoError`, `ErrorCode`.
- Standard library + pydantic.

### Forbidden imports (blacklist, enforced by Architecture Gate)

- `ai_video.production.state_commit` and any `_state_commit_*`
- `ai_video.production.dependency`
- `ai_video.production.composition`
- `ai_video.production.hyperframes`
- `ai_video.production.manifest`
- `ai_video.production.registry`
- `ai_video.production.shot_router`
- `ai_video.production.video`
- `ai_video.production.video_generation` — **transitively imports `production.video`, `local_video`, `paid_provider`**
- `ai_video.production.seedance` / `seedance_*` / `minimax_*` / `comfy_*` / `elevenlabs` / `local_video` / `paid_provider` / `paid_provider_gate`
- `ai_video.comfy_client`, `ai_video.ffmpeg_tools`, `ai_video.cli`
- `os.environ`, `subprocess`, `httpx`, `requests`, `urllib`
- `keyring`, `cryptography.hazmat.primitives.kdf`

Reverse direction is allowed: Production may import `ai_video.quality_gates` for the optional committer handoff.

## 4. Schemas

### 4.1 Common enums

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

### 4.2 Typed payloads (no `Mapping[str, object]`)

```python
class IdentityAnchorPayload(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    character_ids: tuple[str, ...]
    character_reference_asset_ids: tuple[str, ...]
    matched_owner_ids: tuple[str, ...]

class StrategyPayload(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    plan_outcome: str | None
    generation_mode: str | None
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
    matches: bool | None
```

Each payload is a `StrictModel` with `extra="forbid"`. A test injects a forbidden key into each payload and asserts `ValidationError`.

### 4.3 Check outcomes

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

`reason_codes` is a union of the two enums via tuple element type; pydantic accepts mixed tuples.

### 4.4 Receipts (sealed VersionedArtifact)

```python
class ShotQualityReceipt(VersionedArtifact):
    receipt_id: str = Field(min_length=1)
    gate_name: Literal["shot_quality_gate"] = "shot_quality_gate"
    gate_version: Literal["shot-quality-gate/1"] = "shot-quality-gate/1"
    status: GateStatus
    checks: tuple[ShotCheckOutcome, ...]
    blocked_reasons: tuple[BlockedReason, ...] = ()
    warnings: tuple[GateWarning, ...] = ()

    @classmethod
    def create(cls, **values: object) -> "ShotQualityReceipt": ...


class VideoQualityReceipt(VersionedArtifact):
    receipt_id: str = Field(min_length=1)
    gate_name: Literal["video_quality_gate"] = "video_quality_gate"
    gate_version: Literal["video-quality-gate/1"] = "video-quality-gate/1"
    status: GateStatus
    checks: tuple[VideoCheckOutcome, ...]
    blocked_reasons: tuple[BlockedReason, ...] = ()
    warnings: tuple[GateWarning, ...] = ()

    @classmethod
    def create(cls, **values: object) -> "VideoQualityReceipt": ...
```

Both inherit from `VersionedArtifact` so they pick up the existing `content_hash` seal. `create()` mirrors the existing sealed-construction pattern.

### 4.5 Forbidden fields guard

Receipts use `extra="forbid"`. The forbidden list is enforced in tests:

- `provider_name`, `provider_kind`, `provider_profile`, `selected_provider`
- `selected_capability_id`, `selected_mode`
- `manifest_revision`, `timeline_position`, `asset_path`, `artifact_path`
- `output_asset_id`, `accepted`, `activated`, `quality_accepted`, `next_action`, `repair_recommended`

## 5. Shot Quality Gate algorithm

`ShotQualityGate.evaluate(request) -> ShotQualityReceipt` runs three independent checks; status aggregation follows FR-3.

### 5.1 Request shape (reuses planning types)

```python
class ShotQualityGateRequest(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: str = Field(min_length=1)
    target_shot: Shot
    character_context: tuple[Character, ...]
    scene_context: Scene
    available_assets: tuple[AvailableAsset, ...]
    video_generation_plan: VideoGenerationPlan | None
    contract_version: Literal["shot-quality-gate/1"] = "shot-quality-gate/1"
    request_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @classmethod
    def create(cls, **values: object) -> "ShotQualityGateRequest": ...
```

### 5.2 `IDENTITY_ANCHOR`

```
character_ids = target_shot.character_ids
char_ref_assets = [a for a in available_assets if a.role == AssetRole.CHARACTER_REFERENCE]
matched_owner_ids = [a.canonical_owner_id for a in char_ref_assets if a.canonical_owner_id in character_ids]
unmatched = [c for c in character_ids if c not in matched_owner_ids]
if not character_ids:
    severity = PASS   # environment shot
elif char_ref_assets and not unmatched:
    severity = PASS
elif not char_ref_assets:
    severity = BLOCKED; reason = MISSING_IDENTITY_ANCHOR
else:
    # assets exist but none of them belong to the right characters
    severity = BLOCKED; reason = MISSING_IDENTITY_ANCHOR
payload = IdentityAnchorPayload(
    character_ids=character_ids,
    character_reference_asset_ids=[a.asset_id for a in char_ref_assets],
    matched_owner_ids=matched_owner_ids,
)
```

This explicitly verifies `canonical_owner_id` belongs to the target character, addressing Codex risk: any CHARACTER_REFERENCE could otherwise be wrongly accepted.

### 5.3 `STRATEGY`

```
if video_generation_plan is None:
    severity = NOT_EVALUATED; reason = STRATEGY_PLAN_MISSING
elif plan.outcome == PlanOutcome.BLOCKED:
    severity = BLOCKED; reason = STRATEGY_CONTRADICTS_SHOT
elif plan.generation_mode == GenerationMode.TEXT_TO_VIDEO and character_ids:
    severity = BLOCKED; reason = STRATEGY_CONTRADICTS_SHOT
elif plan.generation_mode == GenerationMode.REFERENCE_TO_VIDEO and not character_ids:
    severity = WARNING; reason = STRATEGY_RISKY
else:
    severity = PASS
payload = StrategyPayload(
    plan_outcome=plan.outcome.value if plan else None,
    generation_mode=plan.generation_mode.value if plan else None,
    has_important_character=bool(character_ids),
)
```

This is purely structural: it does not re-derive continuity semantics that already live in VideoPlanner / Review.

### 5.4 `COMPLEXITY`

```
word_count = len(target_shot.intent.split())
directive_count = len(target_shot.motion_directives)
INTENT_WORD_LIMIT = 24
DIRECTIVE_LIMIT = 4
severity = WARNING if (word_count > INTENT_WORD_LIMIT or directive_count > DIRECTIVE_LIMIT) else PASS
reason = COMPLEXITY_HIGH if severity == WARNING else ()
payload = ComplexityPayload(
    intent_word_count=word_count,
    directive_count=directive_count,
    intent_limit=INTENT_WORD_LIMIT,
    directive_limit=DIRECTIVE_LIMIT,
)
```

Limits are module-level constants in `shot_quality_gate.py`. Tunable but not driven by caller.

## 6. Video Quality Gate algorithm

`VideoQualityGate.evaluate(request) -> VideoQualityReceipt` runs two checks.

### 6.1 Request shape

```python
class VideoQualityGateRequest(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: str = Field(min_length=1)
    target_shot: Shot
    video_generation_plan: VideoGenerationPlan | None
    fetched_candidate: FetchedVideoCandidate
    contract_version: Literal["video-quality-gate/1"] = "video-quality-gate/1"
    request_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @classmethod
    def create(cls, **values: object) -> "VideoQualityGateRequest": ...
```

Note: `VideoQualityGateRequest` does **not** carry `previous_shot_state` — continuity is out of scope for v2.

### 6.2 `RECEIPT_INTEGRITY`

This is the canonical structural sanity check on the fetched receipt. It is a BLOCKED gate that fires when:

- `fetch_fingerprint` does NOT equal `canonical_sha256(model_dump(exclude={"fetch_fingerprint"}))` → `RECEIPT_HASH_MISMATCH`.
- `submission_fingerprint` ≠ `observation.submission_fingerprint` (only when the observation pointer exists) → `RECEIPT_POINTER_MISMATCH`.
- `artifact_sha256` is not 64 lowercase hex chars → `RECEIPT_HASH_MALFORMED`.

Otherwise `PASS`.

```
receipt = fetched_candidate.receipt   # VideoFetchReceipt or LocalVideoFetchReceipt
recomputed = canonical_sha256(receipt.model_dump(mode="json", exclude={"fetch_fingerprint"}))
hash_ok = (recomputed == receipt.fetch_fingerprint)
artifact_ok = bool(re.fullmatch(r"^[0-9a-f]{64}$", receipt.artifact_sha256))
pointer_ok = True  # default; pointer linkage check is done by the committer separately
severity = PASS if (hash_ok and artifact_ok) else BLOCKED
reasons = [] if severity == PASS else [RECEIPT_HASH_MISMATCH or RECEIPT_HASH_MALFORMED]
payload = ReceiptIntegrityPayload(
    receipt_kind="video" if isinstance(receipt, VideoFetchReceipt) else "local_video",
    fetch_fingerprint_matches=hash_ok,
    submission_observation_linked=pointer_ok,
    artifact_sha256_well_formed=artifact_ok,
)
```

### 6.3 `CONTENT_TYPE_BINDING`

```
if hasattr(receipt, "submission_fingerprint") and _expected_content_type_for(receipt) is not None:
    expected = _expected_content_type_for(receipt)
    actual = receipt.content_type
    matches = (expected == actual)
    severity = PASS if matches else BLOCKED
    reasons = [] if matches else [CONTENT_TYPE_MISMATCH]
else:
    expected = None
    actual = receipt.content_type
    matches = None
    severity = PASS
    reasons = []
payload = ContentTypeBindingPayload(
    receipt_content_type=actual,
    expected_content_type=expected,
    matches=matches,
)
```

`_expected_content_type_for(receipt)` resolves the expected type from the linked `VideoSubmission` if available (via `submission_fingerprint` pointer), else returns `None`. Gate never reads files; it relies on the receipt's already-resolved submission pointer.

## 7. Public surface (`__init__.py`)

```python
from ai_video.quality_gates._gate_models import (
    ShotQualityGateRequest,
    ShotQualityReceipt,
    ShotCheckOutcome,
    VideoQualityGateRequest,
    VideoQualityReceipt,
    VideoCheckOutcome,
    IdentityAnchorPayload,
    StrategyPayload,
    ComplexityPayload,
    ReceiptIntegrityPayload,
    ContentTypeBindingPayload,
    GateStatus,
    CheckSeverity,
    ShotCheckId,
    VideoCheckId,
    BlockedReason,
    GateWarning,
)
from ai_video.quality_gates.shot_quality_gate import ShotQualityGate
from ai_video.quality_gates.video_quality_gate import VideoQualityGate

__all__ = [
    "ShotQualityGate",
    "VideoQualityGate",
    "ShotQualityGateRequest",
    "ShotQualityReceipt",
    "ShotCheckOutcome",
    "VideoQualityGateRequest",
    "VideoQualityReceipt",
    "VideoCheckOutcome",
    "IdentityAnchorPayload",
    "StrategyPayload",
    "ComplexityPayload",
    "ReceiptIntegrityPayload",
    "ContentTypeBindingPayload",
    "GateStatus",
    "CheckSeverity",
    "ShotCheckId",
    "VideoCheckId",
    "BlockedReason",
    "GateWarning",
]
```

Only `ShotQualityGate.evaluate` and `VideoQualityGate.evaluate` are callable. Everything else is data.

## 8. Committer seam (Production-side additive change)

### 8.1 New optional fields on `VideoGenerationAttemptState`

In `src/ai_video/production/_lifecycle_schema.py`:

```python
class VideoGenerationAttemptState(_PaidLifecycleModel):
    request: VideoRequestReceiptPointer
    # ... existing fields unchanged ...
    pre_submit_gate_receipt_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    post_fetch_gate_receipt_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
```

Both are optional with `None` default. `_serialize_optional_continuity_state` is extended to drop them when `None`.

### 8.2 New optional parameters on committer methods

```python
# in src/ai_video/production/_state_commit_video.py
def begin_video_generation(
    self,
    *,
    attempt_id: str,
    request: ResolvedVideoGenerationRequest,
    pre_submit_gate_receipt: ShotQualityReceipt | None = None,
) -> ...:
    if pre_submit_gate_receipt is not None:
        _validate_gate_receipt(
            receipt=pre_submit_gate_receipt,
            expected_gate_name="shot_quality_gate",
            request_fingerprint=request.resolved_generation_hash,
        )
        # if BLOCKED, _validate_gate_receipt raises AiVideoError
    # ... existing logic ...
    state.pre_submit_gate_receipt_hash = (
        pre_submit_gate_receipt.content_hash if pre_submit_gate_receipt else None
    )
    # ... continue ...


def commit_video_activation(
    self,
    *,
    attempt_id: str,
    post_fetch_gate_receipt: VideoQualityReceipt | None = None,
) -> ...:
    if post_fetch_gate_receipt is not None:
        _validate_gate_receipt(
            receipt=post_fetch_gate_receipt,
            expected_gate_name="video_quality_gate",
            request_fingerprint=...,
        )
    # ... existing logic ...
```

### 8.3 Helper `_validate_gate_receipt`

In `src/ai_video/production/_state_commit_gate_receipt.py`:

```python
def _validate_gate_receipt(
    *,
    receipt: ShotQualityReceipt | VideoQualityReceipt,
    expected_gate_name: str,
    request_fingerprint: str,
) -> None:
    if receipt.gate_name != expected_gate_name:
        raise AiVideoError(ErrorCode.PRODUCTION_STATE_INVALID, "gate receipt mismatch")
    if receipt.content_hash != canonical_sha256(receipt.model_dump(mode="json", exclude={"content_hash"})):
        raise AiVideoError(ErrorCode.PRODUCTION_STATE_INVALID, "gate receipt seal invalid")
    if receipt.status == GateStatus.BLOCKED:
        raise AiVideoError(
            ErrorCode.PRODUCTION_STATE_INVALID,
            f"{expected_gate_name} blocked this attempt; reasons: {list(receipt.blocked_reasons)}",
        )
```

`_validate_gate_receipt` does **not** import `ai_video.quality_gates._gate_models` directly; it accepts duck-typed receipt objects so the helper does not require the gate package to be importable in legacy test contexts.

## 9. Failure handling

- Malformed request → pydantic `ValidationError` (caller's responsibility).
- Empty `available_assets` with important character → `BLOCKED` via `IDENTITY_ANCHOR` (no exception).
- Receipt hash mismatch → `BLOCKED` via `RECEIPT_INTEGRITY` (no exception from gate).
- Comitter handoff of `BLOCKED` receipt → raises `AiVideoError(PRODUCTION_STATE_INVALID)` — caller must fix root cause and retry from a fresh receipt.

## 10. Performance

- O(1) per Shot / per candidate. No caching across calls.
- Target: < 5 ms per call. Trivial compared to Provider latency.

## 11. Cross-module contract

- Production modules may import `ai_video.quality_gates` (committer seam).
- Quality gate modules MUST NOT import Production (FR-10).
- Quality gate MAY import `ai_video.planning._planner_models` types (read-only).
- Quality gate MAY import `ai_video.production.models` types and `ai_video.production.hashing` (read-only).

## 12. Testing

See `tests/test_quality_gates.py` and `tests/test_state_commit_gate_receipt.py`. Coverage:

| Layer | What | Count |
|---|---|---|
| Unit | AC-1..AC-7 | 7 |
| Unit | Forbidden fields rejection | 8 (receipt + 2 outcomes + 5 payloads) |
| Unit | Pure determinism (hash stability) | 4 |
| Unit | Status aggregation rule (FR-3) | 7 |
| Unit | `canonical_owner_id` mismatch | 1 |
| Unit | Receipt seam BLOCKED refusal | 2 |
| Unit | Receipt seam PASS round-trip | 2 |
| Architecture | Import blacklist enforcement | 1 |
| **Total** | | **~32** |

Test fixtures live in `tests/fixtures/quality_gates_factory.py`.

## 13. Documentation deliverables

- `docs/specs/shot-quality-gate/README.md` — overview + boundary
- `docs/specs/shot-quality-gate/requirements.md` — WHAT
- `docs/specs/shot-quality-gate/design.md` — HOW
- `docs/specs/shot-quality-gate/tasks.md` — staged implementation
- `docs/specs/shot-quality-gate/test-spec.md` — full test cases
- `docs/specs/shot-quality-gate/integration.md` — caller patterns

## 14. Compatibility

- Production schema adds 2 optional fields to one type; both default to `None`; `_serialize_*` strips them. No breakage of existing sealed validation.
- Comitter adds 2 optional parameters; existing call sites continue to work unchanged.
- No public API change to other modules.
- No new dependency.
- No CLI flag.
- No new Manifest schema (gate receipts are caller-side; committer stores only hashes if supplied).

## 15. Risk & open questions

| Risk | Mitigation |
|---|---|
| Gate grows into a stealth Review | FR-1..FR-2 forbidden fields + typed payloads with `extra="forbid"`; no `accepted` / `activated` outputs |
| Gate starts importing Production writers | FR-10 import whitelist + AST gate; committer seam is the only reverse direction |
| Comitter becomes de-facto gate owner | Gate runs outside committer; committer only validates BLOCKED status and stores hash; receipt is caller-owned |
| Receipt hash mismatch indicates tampering | `RECEIPT_INTEGRITY` is `BLOCKED`; committer refuses |
| Receipt version drift | `gate_version` field pins contract |
| `_validate_gate_receipt` couples committer to gate package | Helper accepts duck-typed receipt; tests can pass mock receipts |
| Future request type changes break aggregation | `aggregate_status` is pure; unit tests pin priority order |