# Shot Quality Gate + Video Quality Gate — Tasks (v2)

Status: implementation plan v2 (paired with `requirements.md` + `design.md`)
Approach: TDD-first, staged by risk / dependency. Scope reduced to 3 + 2 deterministic checks per Codex review.

Each task is small enough to land in one PR (≤ 1 day of focused work). Tests are written first.

## Sequencing rationale

```
T1 schema baseline ─┬─ T2 typed payload classes ─┐
                    ├─ T3 receipt classes (VersionedArtifact) ──┐
                    ├─ T4 forbidden-field guards ──────────────┤
                                                              ├─ T5 status aggregation helper
                                                              ├─ T6 Shot IDENTITY_ANCHOR
                                                              ├─ T7 Shot STRATEGY
                                                              └─ T8 Shot COMPLEXITY
                                                                                  │
                                                                                  ├─ T9 Video RECEIPT_INTEGRITY
                                                                                  └─ T10 Video CONTENT_TYPE_BINDING
                                                                                                  │
                                                                                                  ▼
                                                                       T11 determinism tests
                                                                       T12 architecture import gate
                                                                       T13 committer seam helper
                                                                       T14 optional fields on attempt state
                                                                       T15 optional params on committer methods
                                                                       T16 integration doc + example
                                                                       T17 end-to-end test
                                                                       T18 final review + acceptance
```

Foundation (T1–T4) unblocks parallel work on T5–T10. T11–T12 close the determinism and import surface. T13–T15 land the committer seam. T16–T18 land docs and full-suite verification.

## Tasks

### T1 — Schema baseline (foundational)

Deliverables:

- `src/ai_video/quality_gates/__init__.py` (stub with docstring)
- `src/ai_video/quality_gates/_gate_models.py`
- Enums: `GateStatus`, `CheckSeverity`, `ShotCheckId`, `VideoCheckId`, `BlockedReason`, `GateWarning`
- Models: `ShotQualityGateRequest`, `VideoQualityGateRequest`
- All models `extra="forbid"`, `frozen=True`, `StrictModel` base
- `request_content_hash` computed via `canonical_sha256`

Tests: schema round-trip + `extra="forbid"` rejection.

Acceptance: pytest passes for `test_quality_gates.py::test_schemas_baseline`.

Effort: human ~2h, CC ~10min.

### T2 — Typed payload classes

Deliverables:

- `IdentityAnchorPayload`, `StrategyPayload`, `ComplexityPayload`
- `ReceiptIntegrityPayload`, `ContentTypeBindingPayload`
- All `extra="forbid"`, `frozen=True`, `StrictModel`

Tests: each payload rejects a forbidden key via `ValidationError`.

Effort: human ~1h, CC ~5min.

### T3 — Receipt classes (VersionedArtifact)

Deliverables:

- `ShotCheckOutcome`, `VideoCheckOutcome` (with discriminated `payload` typed correctly)
- `ShotQualityReceipt(VersionedArtifact)`, `VideoQualityReceipt(VersionedArtifact)`
- `create()` sealed classmethods
- `content_hash` sealing via existing `seal_artifact` pattern

Tests: receipt `model_validate` round-trip; `create()` produces stable `content_hash`.

Effort: human ~2h, CC ~10min.

### T4 — Forbidden-field guard tests

Deliverables:

- `test_quality_gates.py::test_*_rejects_forbidden_field` parameterized
- Forbidden list enforced (see design §4.5)
- Tests cover both receipts + both outcomes + all 5 payloads

Tests: 8 forbidden-field rejections.

Effort: human ~30min, CC ~3min.

### T5 — Status aggregation helper

Deliverables:

- `_aggregate_status(severities: tuple[CheckSeverity, ...]) -> GateStatus` implementing FR-3
- Priority: BLOCKED > NOT_EVALUATED > WARNING > PASS

Tests: 7 cases (all single-severity + mixed).

Effort: human ~30min, CC ~3min.

### T6 — Shot check `IDENTITY_ANCHOR`

Deliverables:

- `_check_identity_anchor(target_shot, available_assets) -> ShotCheckOutcome`
- Verifies `canonical_owner_id` matches target character (FR-4, design §5.2)
- Environment shot (no characters) → `PASS`
- Missing references OR mismatched owner → `BLOCKED`

Tests: 4 cases (env, all-match, missing-ref, mismatched-owner).

Effort: human ~1h, CC ~5min.

### T7 — Shot check `STRATEGY`

Deliverables:

- `_check_strategy(target_shot, video_generation_plan) -> ShotCheckOutcome`
- Plan None → `NOT_EVALUATED, STRATEGY_PLAN_MISSING`
- Plan BLOCKED → `BLOCKED, STRATEGY_CONTRADICTS_SHOT`
- T2V + important character → `BLOCKED`
- R2V + no character → `WARNING, STRATEGY_RISKY`
- Otherwise → `PASS`

Tests: 5 cases.

Effort: human ~1h, CC ~5min.

### T8 — Shot check `COMPLEXITY`

Deliverables:

- `_check_complexity(target_shot) -> ShotCheckOutcome`
- Module-level constants `INTENT_WORD_LIMIT=24`, `DIRECTIVE_LIMIT=4`
- Heuristic only — text + directive count

Tests: 3 cases (low, high intent, many directives).

Effort: human ~30min, CC ~3min.

### T9 — Video check `RECEIPT_INTEGRITY`

Deliverables:

- `_check_receipt_integrity(fetched_candidate) -> VideoCheckOutcome`
- Re-verify `fetch_fingerprint` matches `canonical_sha256(payload)`
- Validate `artifact_sha256` is 64 lowercase hex

Tests: 3 cases (valid, hash-mismatch, malformed-sha).

Effort: human ~1h, CC ~5min.

### T10 — Video check `CONTENT_TYPE_BINDING`

Deliverables:

- `_check_content_type_binding(fetched_candidate) -> VideoCheckOutcome`
- Resolve expected type from receipt pointer when available
- `PASS` if no expected declared; `BLOCKED` if declared and differs

Tests: 3 cases (no expected, match, mismatch).

Effort: human ~1h, CC ~5min.

### T11 — Determinism tests

Deliverables:

- Two-call determinism: same request + receipt_id → identical `content_hash`
- Three sequential calls → identical hash
- Different `target_shot_content_hash` → different receipt `content_hash`
- Different `receipt_id` → different receipt `content_hash`

Tests: 4 cases per gate (8 total).

Effort: human ~30min, CC ~3min.

### T12 — Architecture import gate

Deliverables:

- AST scan of `src/ai_video/quality_gates/**` for forbidden imports
- Forbidden list: see design §3 blacklist (incl. `production.video_generation`)
- Each forbidden import causes test failure with file:line

Tests: 1 AST-scan test covering each forbidden module name.

Effort: human ~2h, CC ~10min.

### T13 — Comitter seam helper

Deliverables:

- `src/ai_video/production/_state_commit_gate_receipt.py`
- `_validate_gate_receipt(receipt, expected_gate_name, request_fingerprint)` raises on:
  - mismatched gate_name
  - invalid content_hash seal
  - status == BLOCKED
- Accepts duck-typed receipt (no `ai_video.quality_gates` import in the helper module itself; only type checks via attribute access)

Tests: 3 cases (mismatch, invalid seal, BLOCKED refusal).

Effort: human ~1h, CC ~5min.

### T14 — Optional fields on `VideoGenerationAttemptState`

Deliverables:

- Add `pre_submit_gate_receipt_hash` and `post_fetch_gate_receipt_hash` to `VideoGenerationAttemptState`
- Extend `_serialize_optional_continuity_state` to strip them when `None`
- All fields default `None`; existing test fixtures unchanged

Tests: schema-level round-trip; serializer strips None fields; pattern rejects malformed hash.

Effort: human ~1h, CC ~5min.

### T15 — Optional parameters on committer methods

Deliverables:

- `ProductionStateCommitter.begin_video_generation` accepts `pre_submit_gate_receipt: ShotQualityReceipt | None = None`
- `ProductionStateCommitter.commit_video_activation` accepts `post_fetch_gate_receipt: VideoQualityReceipt | None = None`
- Both methods: when supplied, call `_validate_gate_receipt`; on pass, persist `receipt.content_hash` into attempt state
- When `None`, proceed exactly as today

Tests: AC-11, AC-12 — BLOCKED refuses, PASS persists hash, None leaves hash None.

Effort: human ~2h, CC ~10min.

### T16 — Integration doc + example

Deliverables:

- `docs/specs/shot-quality-gate/integration.md`
- Two worked examples: Shot Gate `BLOCKED` and Video Gate `BLOCKED`
- One committer handoff example (PASS receipt persisted as hash)
- One committer refusal example (BLOCKED receipt raises `AiVideoError`)
- JSON output samples for both gates

Effort: human ~2h, CC ~10min.

### T17 — End-to-end test

Deliverables:

- `tests/test_quality_gates.py::test_end_to_end_shot_gate_blocks_missing_identity`
- `tests/test_quality_gates.py::test_end_to_end_video_gate_blocks_receipt_hash_mismatch`
- `tests/test_state_commit_gate_receipt.py::test_end_to_end_committer_persists_pass_hash`
- Construct full request, run gate, assert result shape / hash / reasons
- Then hand receipt to committer (in-memory fixture), assert hash is stored

Tests: 3 cases.

Effort: human ~2h, CC ~10min.

### T18 — Final review & acceptance

Deliverables:

- All AC-1..AC-12 verified
- `pytest tests/test_quality_gates.py` passes
- `pytest tests/test_state_commit_gate_receipt.py` passes
- `pytest tests/test_architecture_gate.py` passes (with new gate)
- `pytest tests/` (full suite) passes — no regression
- Final completion report

Effort: human ~1h, CC ~10min.

## Total effort

| Bucket | Human | CC |
|---|---|---|
| T1–T5 (schemas + aggregation) | ~6h | ~30min |
| T6–T8 (Shot checks) | ~2.5h | ~15min |
| T9–T10 (Video checks) | ~2h | ~10min |
| T11–T12 (determinism + gate) | ~2.5h | ~15min |
| T13–T15 (committer seam) | ~4h | ~20min |
| T16–T17 (docs + e2e) | ~4h | ~20min |
| T18 (review) | ~1h | ~10min |
| **Total** | **~22h** | **~120min** |

Single PR scope if sliced aggressively (T1–T8 + T12 would be useful Shot-only MVP). Recommend landing T1–T12 + T13 as PR1, T14–T18 as PR2.

## Definition of done (per task)

1. Test written and failing (or accepted as new) before implementation.
2. Implementation passes the test.
3. No new warnings from ruff/mypy (project default).
4. No drive-by changes to unrelated files.
5. Commit message references task id (e.g. `T6: implement IDENTITY_ANCHOR check`).
7. `git diff` reviewed against the ownership boundary before commit.

## Out-of-scope tasks (deferred)

These will be tracked as separate slices later:

- D1 — Continuity checks (CONTINUITY_TERMINAL, CONTINUITY_LOCATION) — requires extending `PreviousShotState` with wardrobe/props or accepting `Shot.continuity_constraints` as the source.
- D2 — Capability binding check (CAPABILITY_BINDING) — requires typed seam to selected `VideoProviderCapabilities`; will need committer to expose capabilities or for `_state_commit_video_candidate` to carry them.
- D3 — Multi-usage reference detection (REFERENCE_VS_FINAL_VISUAL) — requires a canonical usage index owned by Manifest, not a parallel snapshot.
- D4 — VLM-backed `IDENTITY_DRIFT` evaluation — requires VLM adapter; out of scope until Provider adapter selection is approved.
- D5 — Scene reference warning (SCENE_BINDING) — soft warning only; defer until a canonical scene-reference snapshot exists.
- D6 — Story alignment VLM check.
- D7 — Cross-Shot batch evaluation.
- D8 — Repair-loop integration: P6 Review consuming gate results and emitting `RepairRequest`.

## Risk register per task

| Task | Risk | Mitigation |
|---|---|---|
| T6 | Wrong asset passes IDENTITY_ANCHOR if `canonical_owner_id` not checked | Test pinned: mismatched-owner → BLOCKED |
| T9 | Receipt seal re-verification drifts from production seal pattern | Use existing `canonical_sha256` helper exactly; covered by test |
| T12 | AST blacklist misses transitive leak via `production.video_generation` | Explicitly listed in blacklist; AST test fails if anyone imports it |
| T13 | Helper couples committer to gate package | Helper is duck-typed; no `ai_video.quality_gates` import in helper module |
| T14 | New fields break sealed-validation of existing fixtures | Defaults `None`; existing tests still pass |
| T15 | Existing call sites accidentally lose optional arg | All call sites pre-existing; new param defaults `None`; tests pin current call paths |