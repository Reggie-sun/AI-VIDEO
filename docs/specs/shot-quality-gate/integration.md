# Shot Quality Gate + Video Quality Gate — Integration Guide (v2)

Audience: Main Agent / Codex authors and `ProductionStateCommitter` maintainers who want a cheap, typed safety net before / after Provider calls without changing canonical ownership.

Status: paired with `requirements.md` + `design.md` + `tasks.md`.

## 1. Why this module exists

AI-VIDEO Production is canonical owner of Manifest, Asset Registry, Timeline, Provider selection, and Review. Gates do **not** replace any of those. They exist to:

- **Save Provider budget** by rejecting structurally flawed Shots before any Provider call.
- **Save reviewer attention** by surfacing obvious deliverable defects right after fetch, before P6 Review.
- **Surface structural sanity** of fetched Provider receipts (hash + content type), independent of Provider's own claims.

A gate produces a typed `*QualityReceipt` that callers own. The committer may accept the receipt as an optional handoff parameter and store its `content_hash` on the attempt state — losing the receipt loses no canonical truth (committer only stores the hash; the full receipt stays with the caller).

## 2. Scope (revised after Codex review)

v2 ships only:

| Gate | Checks |
|---|---|
| `ShotQualityGate` | `IDENTITY_ANCHOR`, `STRATEGY`, `COMPLEXITY` |
| `VideoQualityGate` | `RECEIPT_INTEGRITY`, `CONTENT_TYPE_BINDING` |

Continuity, capability binding, multi-usage reference detection, scene reference warning, and VLM `IDENTITY_DRIFT` are deferred to D1–D5 in [tasks.md](tasks.md#out-of-scope-tasks-deferred).

## 3. When to call

| Gate | Call site | Skip when |
|---|---|---|
| `ShotQualityGate.evaluate` | After `VideoPlanner.plan(...)` returns `PROPOSED`, before any `commit_video_generation` / Provider submission | Shot's `visual_strategy` is `EXISTING_VIDEO` or `STATIC_IMAGE` |
| `VideoQualityGate.evaluate` | After `FetchedVideoCandidate` is in hand, before `commit_video_activation` | Shot's `visual_strategy` is `STATIC_IMAGE` |

Skipping a gate is allowed. The committer accepts `None` for both handoff parameters.

## 4. Public surface

```python
from ai_video.quality_gates import (
    ShotQualityGate,
    VideoQualityGate,
    ShotQualityGateRequest,
    ShotQualityReceipt,
    VideoQualityGateRequest,
    VideoQualityReceipt,
    GateStatus,
    ShotCheckId,
    VideoCheckId,
    BlockedReason,
    GateWarning,
)
```

Only `ShotQualityGate.evaluate` and `VideoQualityGate.evaluate` are callable. Everything else is data.

## 5. Call pattern

```python
from ai_video.quality_gates import ShotQualityGate, VideoQualityGate

# pre-generation
shot_receipt = ShotQualityGate().evaluate(shot_request, receipt_id="sq-shot-7-attempt-1")
# → ShotQualityReceipt (sealed VersionedArtifact, content-hashed)

# post-fetch
video_receipt = VideoQualityGate().evaluate(video_request, receipt_id="vq-shot-7-fetched")
# → VideoQualityReceipt (sealed VersionedArtifact, content-hashed)
```

No constructor arguments. No async. Sync only. `receipt_id` is required (or auto-derived as `f"{gate_name}-{request_content_hash[:16]}"`).

## 6. Shot Quality Gate integration

### 6.1 Minimal example

```python
from ai_video.quality_gates import ShotQualityGate, ShotQualityGateRequest

request = ShotQualityGateRequest.create(
    request_id="sqg-shot-7-attempt-1",
    target_shot=project.shots["shot-7"],
    character_context=tuple(
        project.characters[c] for c in project.shots["shot-7"].character_ids
    ),
    scene_context=project.scenes[project.shots["shot-7"].scene_id],
    available_assets=tuple(
        AvailableAsset(
            role=asset.role,
            asset_id=asset.asset_id,
            asset_sha256=asset.sha256,
            canonical_owner_id=asset.canonical_owner_id,
            mime_type=asset.mime_type,
        )
        for asset in registry.assets_for_shot("shot-7")
    ),
    video_generation_plan=planner_plan,  # may be None
    contract_version="shot-quality-gate/1",
)

receipt = ShotQualityGate().evaluate(request, receipt_id="sq-shot-7-attempt-1")
```

### 6.2 Reading the receipt

```python
match receipt.status:
    case GateStatus.PASS:
        # proceed to committer; attach receipt as handoff if desired
        ...
    case GateStatus.WARNING:
        # proceed but record GateWarning items as receipt-side evidence
        ...
    case GateStatus.BLOCKED:
        # do NOT proceed; inspect BlockedReason and either
        #   (a) re-author Shot intent, (b) gather missing assets, or (c) escalate
        ...
    case GateStatus.NOT_EVALUATED:
        # proceed only if caller policy allows un-evaluated evidence; record gap
        ...
```

`receipt.content_hash` is stable per `request_content_hash` + `receipt_id`; use it to dedupe re-evaluations.

### 6.3 What callers MUST NOT do

- Do **not** write the receipt into Manifest, Asset Registry, or Timeline.
- Do **not** assume a `PASS` proves the Video is good (P6 Review still owns acceptance).
- Do **not** retry the gate with mutated inputs to "force" a different status.
- Do **not** treat `NOT_EVALUATED` as `PASS` silently — the gap must be recorded.

## 7. Video Quality Gate integration

### 7.1 Minimal example

```python
from ai_video.quality_gates import VideoQualityGate, VideoQualityGateRequest

request = VideoQualityGateRequest.create(
    request_id="vqg-shot-7-fetched",
    target_shot=project.shots["shot-7"],
    video_generation_plan=planner_plan,
    fetched_candidate=fetched_candidate,  # from video_generation.VideoGenerationService
    contract_version="video-quality-gate/1",
)

receipt = VideoQualityGate().evaluate(request, receipt_id="vq-shot-7-fetched")
```

### 7.2 Reading the receipt

Same `match` pattern as Shot Quality Gate. Key behaviors:

- `RECEIPT_INTEGRITY` failures are deterministic and should be treated as fatal for this candidate.
- `CONTENT_TYPE_BINDING` BLOCKED is fatal only if the Provider declared an expected type and broke it.

### 7.3 What callers MUST NOT do

- Do **not** mark the candidate `activated` when `status == BLOCKED`.
- Do **not** write the receipt into Manifest or any durable artifact.
- Do **not** call the gate from inside `ProductionStateCommitter` writes (gates are caller-side; committer reads the receipt, never invokes the gate).

## 8. Comitter handoff

The committer accepts `*QualityReceipt` as **optional** parameters on existing methods.

### 8.1 Passing a PASS receipt

```python
committer.begin_video_generation(
    attempt_id="va-shot-7",
    request=resolved_request,
    pre_submit_gate_receipt=shot_receipt,   # receipt with status != BLOCKED
)

# ... fetch happens ...

committer.commit_video_activation(
    attempt_id="va-shot-7",
    post_fetch_gate_receipt=video_receipt,  # receipt with status != BLOCKED
)
```

After successful handoff:

- `attempt.pre_submit_gate_receipt_hash == shot_receipt.content_hash`
- `attempt.post_fetch_gate_receipt_hash == video_receipt.content_hash`

### 8.2 Passing a BLOCKED receipt

```python
blocked_receipt = VideoQualityGate().evaluate(request_with_bad_receipt, receipt_id="vq-1")
assert blocked_receipt.status == GateStatus.BLOCKED

with pytest.raises(AiVideoError) as exc:
    committer.commit_video_activation(
        attempt_id="va-shot-7",
        post_fetch_gate_receipt=blocked_receipt,
)
assert exc.value.code == ErrorCode.PRODUCTION_STATE_INVALID
```

The committer refuses to activate. Caller must fix root cause and retry from a fresh receipt.

### 8.3 Omitting the receipt

```python
committer.begin_video_generation(
    attempt_id="va-shot-7",
    request=resolved_request,
    # pre_submit_gate_receipt omitted → defaults to None
)
```

Comitter proceeds exactly as today. `pre_submit_gate_receipt_hash` stays `None` on the attempt state.

## 9. Worked example: Alice walks out of cafe, missing reference

### Setup

- `shot-7`, intent `"Alice walks out of cafe."`, `visual_strategy=GENERATED_VIDEO`, `character_ids=("alice",)`.
- Asset Registry has `ref-cafe` (SCENE_REFERENCE) but **no** `ref-alice`.

### Request

```python
request = ShotQualityGateRequest.create(
    request_id="sqg-shot-7",
    target_shot=project.shots["shot-7"],
    character_context=(project.characters["alice"],),
    scene_context=project.scenes["scene-cafe"],
    available_assets=(
        AvailableAsset(role=AssetRole.SCENE_REFERENCE, asset_id="ref-cafe", asset_sha256=HASH_A, canonical_owner_id=None, mime_type="image/png"),
    ),
    video_generation_plan=planner_plan,
    contract_version="shot-quality-gate/1",
)
```

### Expected receipt (illustrative JSON)

```json
{
  "artifact_id": "sq-shot-7",
  "revision": 1,
  "content_hash": "8b7c...64hex",
  "creation_receipt_id": "sq-shot-7",
  "receipt_id": "sq-shot-7",
  "gate_name": "shot_quality_gate",
  "gate_version": "shot-quality-gate/1",
  "status": "blocked",
  "checks": [
    {
      "check_id": "identity_anchor",
      "severity": "blocked",
      "reason_codes": ["missing_identity_anchor"],
      "payload": {
        "character_ids": ["alice"],
        "character_reference_asset_ids": [],
        "matched_owner_ids": []
      },
      "message": "Important character 'alice' has no approved character reference asset whose canonical_owner_id matches the target character."
    },
    {
      "check_id": "strategy",
      "severity": "pass",
      "reason_codes": [],
      "payload": {"plan_outcome": "proposed", "generation_mode": "reference_to_video", "has_important_character": true},
      "message": "Strategy check passed."
    },
    {
      "check_id": "complexity",
      "severity": "pass",
      "reason_codes": [],
      "payload": {"intent_word_count": 5, "directive_count": 0, "intent_limit": 24, "directive_limit": 4},
      "message": "Complexity within limits."
    }
  ],
  "blocked_reasons": ["missing_identity_anchor"],
  "warnings": []
}
```

### Caller interpretation

- `status == BLOCKED` → **do not** submit to Provider.
- `MISSING_IDENTITY_ANCHOR` is the actionable reason; trigger Asset import workflow or re-author the Shot intent.
- Optionally hand the BLOCKED receipt to committer — committer will refuse and raise `AiVideoError(PRODUCTION_STATE_INVALID)`.

## 10. Worked example: fetched video with bad receipt hash

### Setup

`FetchedVideoCandidate` whose `VideoFetchReceipt.fetch_fingerprint` was tampered or doesn't match the canonical payload.

### Expected receipt (illustrative JSON)

```json
{
  "artifact_id": "vq-shot-7-fetched",
  "revision": 1,
  "content_hash": "fe29...64hex",
  "creation_receipt_id": "vq-shot-7-fetched",
  "receipt_id": "vq-shot-7-fetched",
  "gate_name": "video_quality_gate",
  "gate_version": "video-quality-gate/1",
  "status": "blocked",
  "checks": [
    {
      "check_id": "receipt_integrity",
      "severity": "blocked",
      "reason_codes": ["receipt_hash_mismatch"],
      "payload": {
        "receipt_kind": "video",
        "fetch_fingerprint_matches": false,
        "submission_observation_linked": true,
        "artifact_sha256_well_formed": true
      },
      "message": "Video fetch receipt seal does not match canonical payload; possible tampering."
    }
  ],
  "blocked_reasons": ["receipt_hash_mismatch"],
  "warnings": []
}
```

### Caller interpretation

- `status == BLOCKED` → **do not** call `commit_video_activation`.
- Caller may retry the Provider call (subject to budget/policy gates) or escalate.
- If caller accidentally hands this receipt to committer, committer raises `AiVideoError(PRODUCTION_STATE_INVALID)`.

## 11. Failure modes callers must handle

| Failure | Source | What caller does |
|---|---|---|
| `pydantic.ValidationError` on request | Caller passed malformed inputs | Fix inputs; do not retry |
| `receipt.status == BLOCKED` | Gate detected a hard failure | Do not proceed; fix root cause |
| `receipt.status == NOT_EVALUATED` | Required input was missing | Record gap; advance only if policy allows |
| `receipt.content_hash` changes between attempts | Inputs changed | Re-evaluate with new request; do not assume determinism across content edits |
| `AiVideoError(PRODUCTION_STATE_INVALID)` from committer | Handed a BLOCKED receipt | Fix root cause; do not retry with same receipt |
| Forbidden field rejection | Caller code tried to inject forbidden keys | Fix caller code; gates are read-only types |

## 12. Ordering relative to other AI-VIDEO components

```
Main Agent
  ├─ hell-grind-aigc-skill   (creative intent, continuity state)
  ├─ higgsfield              (model-specific prompt adaptation; advisory)
  ├─ VideoPlanner.plan       (generation strategy; provider-neutral)
  ├─ ShotQualityGate.evaluate  ◀── NEW (before gen)
  ├─ ProductionStateCommitter.begin_video_generation(..., pre_submit_gate_receipt=?)
  ├─ VideoProvider
  ├─ VideoQualityGate.evaluate  ◀── NEW (after fetch)
  ├─ ProductionStateCommitter.commit_video_activation(..., post_fetch_gate_receipt=?)
  └─ production.review (P6)
```

Gates do not import Production; committer may optionally import gate types for the handoff.

## 13. Migration & rollout

- Slice is additive; no existing module breaks.
- Land as a single PR per the two-PR plan in [tasks.md](tasks.md) (T1–T12 + T13 → PR1; T14–T18 → PR2).
- Old flow remains valid: callers may skip gates; committer may receive `None` for both handoff parameters.

## 14. References

- `requirements.md` — acceptance criteria
- `design.md` — module design, schemas, algorithm
- `tasks.md` — staged implementation plan
- `test-spec.md` — full test cases
- `src/ai_video/quality_gates/` — module (post-merge)
- `tests/test_quality_gates.py` and `tests/test_state_commit_gate_receipt.py` — tests (post-merge)