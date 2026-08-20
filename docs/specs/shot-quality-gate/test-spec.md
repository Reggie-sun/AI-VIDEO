# Shot Quality Gate + Video Quality Gate — Test Spec (v2)

Status: paired with `requirements.md` (AC list), `design.md` (algorithm), `tasks.md` (delivery plan)

## Layer overview

| Layer | Tool | What it covers | Count |
|---|---|---|---|
| Unit | pytest | Per-check algorithm branches, status aggregation, hash stability | ~22 |
| Contract | pytest | Forbidden-field rejection on receipts, outcomes, payloads | ~10 |
| Architecture | pytest AST scan | Import blacklist incl. `production.video_generation` | ~3 |
| Comitter seam | pytest | BLOCKED refusal, PASS round-trip, None fallback | ~4 |
| End-to-end | pytest | Main Agent / Committer full call path | ~3 |
| **Total** | | | **~42** |

## Fixture helpers (`tests/fixtures/quality_gates_factory.py`)

```python
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64

def make_shot(*, shot_id="shot-target", character_ids=("alice",), visual_strategy=GENERATED_VIDEO, intent="Alice walks.", ...) -> Shot
def make_character(character_id="alice", content_hash=HASH_A) -> Character
def make_scene(scene_id="cafe", content_hash=HASH_B) -> Scene
def make_available_asset(*, role, asset_id, sha256, canonical_owner_id=None, mime_type="image/png") -> AvailableAsset
def make_video_generation_plan(*, outcome=PlanOutcome.PROPOSED, generation_mode=GenerationMode.TEXT_TO_VIDEO) -> VideoGenerationPlan
def make_video_fetch_receipt(*, content_type="video/mp4", artifact_sha256=HASH_C, fetch_fingerprint=None) -> VideoFetchReceipt
def make_fetched_video_candidate(*, receipt=None) -> FetchedVideoCandidate
def make_shot_quality_request(**overrides) -> ShotQualityGateRequest
def make_video_quality_request(**overrides) -> VideoQualityGateRequest
```

Each helper applies `seal_artifact()` (existing) to give `content_hash` to the models.

## Required test cases

### Case 1 — important character + no reference asset → BLOCKED `MISSING_IDENTITY_ANCHOR`

```python
def test_case_1_shot_gate_blocks_missing_identity_anchor():
    request = make_shot_quality_request(
        target_shot=make_shot(character_ids=("alice",)),
        available_assets=(),
    )
    receipt = ShotQualityGate().evaluate(request)
    assert receipt.status == GateStatus.BLOCKED
    assert BlockedReason.MISSING_IDENTITY_ANCHOR in receipt.blocked_reasons
    anchor = _find_check(receipt.checks, ShotCheckId.IDENTITY_ANCHOR)
    assert anchor.severity == CheckSeverity.BLOCKED
    assert isinstance(anchor.payload, IdentityAnchorPayload)
    assert anchor.payload.character_ids == ("alice",)
    assert anchor.payload.character_reference_asset_ids == ()
    assert anchor.payload.matched_owner_ids == ()
```

### Case 2 — important character + reference with mismatched owner → BLOCKED

```python
def test_case_2_shot_gate_blocks_mismatched_canonical_owner():
    request = make_shot_quality_request(
        target_shot=make_shot(character_ids=("alice",)),
        available_assets=(
            make_available_asset(
                role=AssetRole.CHARACTER_REFERENCE,
                asset_id="ref-bob",
                canonical_owner_id="bob",   # wrong owner
            ),
        ),
    )
    receipt = ShotQualityGate().evaluate(request)
    assert receipt.status == GateStatus.BLOCKED
    assert BlockedReason.MISSING_IDENTITY_ANCHOR in receipt.blocked_reasons
    anchor = _find_check(receipt.checks, ShotCheckId.IDENTITY_ANCHOR)
    assert anchor.payload.matched_owner_ids == ()
```

### Case 3 — environment shot + no plan → NOT_EVALUATED

```python
def test_case_3_shot_gate_not_evaluated_for_environment_no_plan():
    request = make_shot_quality_request(
        target_shot=make_shot(character_ids=()),
        video_generation_plan=None,
    )
    receipt = ShotQualityGate().evaluate(request)
    assert receipt.status == GateStatus.NOT_EVALUATED
    strategy = _find_check(receipt.checks, ShotCheckId.STRATEGY)
    assert strategy.severity == CheckSeverity.NOT_EVALUATED
    assert GateWarning.STRATEGY_PLAN_MISSING in receipt.warnings
```

### Case 4 — important character + plan BLOCKED → BLOCKED `STRATEGY_CONTRADICTS_SHOT`

```python
def test_case_4_shot_gate_blocks_plan_blocked():
    plan = make_video_generation_plan(outcome=PlanOutcome.BLOCKED)
    request = make_shot_quality_request(
        target_shot=make_shot(character_ids=("alice",)),
        video_generation_plan=plan,
    )
    receipt = ShotQualityGate().evaluate(request)
    assert receipt.status == GateStatus.BLOCKED
    assert BlockedReason.STRATEGY_CONTRADICTS_SHOT in receipt.blocked_reasons
```

### Case 5 — important character + plan T2V → BLOCKED

```python
def test_case_5_shot_gate_blocks_t2v_with_important_character():
    plan = make_video_generation_plan(
        outcome=PlanOutcome.PROPOSED,
        generation_mode=GenerationMode.TEXT_TO_VIDEO,
    )
    request = make_shot_quality_request(
        target_shot=make_shot(character_ids=("alice",)),
        video_generation_plan=plan,
    )
    receipt = ShotQualityGate().evaluate(request)
    assert receipt.status == GateStatus.BLOCKED
    assert BlockedReason.STRATEGY_CONTRADICTS_SHOT in receipt.blocked_reasons
```

### Case 6 — fetched video with `fetch_fingerprint` not matching payload → BLOCKED `RECEIPT_HASH_MISMATCH`

```python
def test_case_6_video_gate_blocks_receipt_hash_mismatch():
    receipt = make_video_fetch_receipt()
    tampered = receipt.model_copy(update={"fetch_fingerprint": "f" * 64})
    candidate = FetchedVideoCandidate(relative_path=Path("video.mp4"), receipt=tampered)
    request = make_video_quality_request(fetched_candidate=candidate)
    gate_receipt = VideoQualityGate().evaluate(request)
    assert gate_receipt.status == GateStatus.BLOCKED
    assert BlockedReason.RECEIPT_HASH_MISMATCH in gate_receipt.blocked_reasons
    integ = _find_video_check(gate_receipt.checks, VideoCheckId.RECEIPT_INTEGRITY)
    assert integ.severity == CheckSeverity.BLOCKED
    assert integ.payload.fetch_fingerprint_matches is False
```

### Case 7 — fetched video whose `content_type` does not match expected → BLOCKED `CONTENT_TYPE_MISMATCH`

```python
def test_case_7_video_gate_blocks_content_type_mismatch():
    submission = make_video_submission(expected_content_type="video/mp4")
    observation = make_video_task_observation()
    fetched_receipt = make_video_fetch_receipt(content_type="video/quicktime")
    fetched_receipt = fetched_receipt.model_copy(update={
        "submission_fingerprint": submission.submission_fingerprint,
        "observation_fingerprint": observation.observation_fingerprint,
    })
    candidate = FetchedVideoCandidate(relative_path=Path("video.mp4"), receipt=fetched_receipt)
    request = make_video_quality_request(fetched_candidate=candidate)
    gate_receipt = VideoQualityGate().evaluate(request)
    assert gate_receipt.status == GateStatus.BLOCKED
    assert BlockedReason.CONTENT_TYPE_MISMATCH in gate_receipt.blocked_reasons
```

### Extra — pure-function determinism (Shot Gate)

```python
def test_shot_gate_pure_function_same_request_same_receipt():
    request = make_shot_quality_request()
    r1 = ShotQualityGate().evaluate(request, receipt_id="sq-1")
    r2 = ShotQualityGate().evaluate(request, receipt_id="sq-1")
    assert r1.content_hash == r2.content_hash
    assert r1.model_dump() == r2.model_dump()


def test_shot_gate_different_receipt_id_yields_different_hash():
    request = make_shot_quality_request()
    r1 = ShotQualityGate().evaluate(request, receipt_id="sq-1")
    r2 = ShotQualityGate().evaluate(request, receipt_id="sq-2")
    assert r1.content_hash != r2.content_hash
```

### Extra — pure-function determinism (Video Gate)

Same shape as above, applied to `VideoQualityGate`.

### Extra — status aggregation rule

```python
@pytest.mark.parametrize("severities, expected", [
    ((CheckSeverity.PASS,), GateStatus.PASS),
    ((CheckSeverity.WARNING,), GateStatus.WARNING),
    ((CheckSeverity.BLOCKED,), GateStatus.BLOCKED),
    ((CheckSeverity.NOT_EVALUATED,), GateStatus.NOT_EVALUATED),
    ((CheckSeverity.PASS, CheckSeverity.NOT_EVALUATED), GateStatus.NOT_EVALUATED),
    ((CheckSeverity.WARNING, CheckSeverity.BLOCKED), GateStatus.BLOCKED),
    ((CheckSeverity.PASS, CheckSeverity.WARNING, CheckSeverity.NOT_EVALUATED), GateStatus.NOT_EVALUATED),
])
def test_status_aggregation(severities, expected):
    assert _aggregate_status(severities) == expected
```

### Extra — forbidden-field guard

```python
@pytest.mark.parametrize("forbidden_key", [
    "provider_name",
    "selected_capability_id",
    "manifest_revision",
    "timeline_position",
    "asset_path",
    "output_asset_id",
    "accepted",
    "next_action",
])
def test_shot_receipt_rejects_forbidden_field(forbidden_key):
    base = ShotQualityGate().evaluate(make_shot_quality_request(), receipt_id="sq-1").model_dump()
    base[forbidden_key] = "leak"
    with pytest.raises(ValidationError):
        ShotQualityReceipt.model_validate(base)
```

Same shape for `VideoQualityReceipt`. Plus parametrized test on each payload class to inject forbidden keys.

### Extra — committer seam (BLOCKED refusal)

```python
def test_committer_refuses_blocked_video_receipt(...):
    blocked = VideoQualityGate().evaluate(request_with_mismatched_hash, receipt_id="vq-1")
    assert blocked.status == GateStatus.BLOCKED
    with pytest.raises(AiVideoError) as exc:
        committer.commit_video_activation(attempt_id=..., post_fetch_gate_receipt=blocked)
    assert exc.value.code == ErrorCode.PRODUCTION_STATE_INVALID
```

### Extra — committer seam (PASS round-trip)

```python
def test_committer_persists_pass_receipt_hash(...):
    passed = VideoQualityGate().evaluate(request_with_valid_receipt, receipt_id="vq-1")
    assert passed.status in {GateStatus.PASS, GateStatus.NOT_EVALUATED}
    committer.commit_video_activation(attempt_id=..., post_fetch_gate_receipt=passed)
    attempt = committer._read_attempt(...)
    assert attempt.post_fetch_gate_receipt_hash == passed.content_hash


def test_committer_skips_receipt_when_none(...):
    committer.commit_video_activation(attempt_id=..., post_fetch_gate_receipt=None)
    attempt = committer._read_attempt(...)
    assert attempt.post_fetch_gate_receipt_hash is None
```

### Extra — architecture gate (import blacklist)

```python
def test_quality_gates_module_forbids_production_writer_imports():
    forbidden = [
        "ai_video.production.state_commit",
        "ai_video.production.dependency",
        "ai_video.production.composition",
        "ai_video.production.hyperframes",
        "ai_video.production.manifest",
        "ai_video.production.registry",
        "ai_video.production.shot_router",
        "ai_video.production.video",
        "ai_video.production.video_generation",
        "ai_video.production.seedance",
        "ai_video.production.minimax_h3",
        "ai_video.production.minimax_hailuo",
        "ai_video.production.paid_provider",
        "ai_video.comfy_client",
        "ai_video.ffmpeg_tools",
        "ai_video.cli",
    ]
    quality_root = Path("src/ai_video/quality_gates")
    for path in quality_root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [f"{node.module}.{alias.name}" for alias in node.names]
            else:
                continue
            for name in names:
                assert not any(name.startswith(m) for m in forbidden), (
                    f"{path} imports forbidden module {name}"
                )
```

## Negative tests

| Test | Expectation |
|---|---|
| Empty `available_assets` + important character Shot → BLOCKED | `MISSING_IDENTITY_ANCHOR` |
| Reference with `canonical_owner_id=None` + important character → BLOCKED | `MISSING_IDENTITY_ANCHOR` (no owner match) |
| Plan None → NOT_EVALUATED | `STRATEGY_PLAN_MISSING` warning |
| Fetched candidate missing `artifact_sha256` → BLOCKED | `RECEIPT_HASH_MALFORMED` |
| Comitter with `pre_submit_gate_receipt_hash` malformed (not 64 hex) | Pydantic `ValidationError` at field validation |
| Receipt with mismatched `gate_name` passed to committer | `AiVideoError(PRODUCTION_STATE_INVALID)` |
| Receipt with `content_hash` not matching payload passed to committer | `AiVideoError(PRODUCTION_STATE_INVALID)` |

## Coverage targets

- `src/ai_video/quality_gates/_gate_models.py`: ≥ 95% lines
- `src/ai_video/quality_gates/shot_quality_gate.py`: ≥ 95% lines
- `src/ai_video/quality_gates/video_quality_gate.py`: ≥ 95% lines
- `src/ai_video/quality_gates/__init__.py`: ≥ 100% lines (re-export only)
- `src/ai_video/production/_state_commit_gate_receipt.py`: ≥ 95% lines

## CI integration

The new test files are auto-picked up by `pytest tests/`. No conftest changes required. Existing conftest fixtures remain untouched.

## Manual smoke (out of CI)

The integration doc provides copy-paste caller examples. Manual smoke is optional and reads gate JSON to confirm intent — not a CI gate.