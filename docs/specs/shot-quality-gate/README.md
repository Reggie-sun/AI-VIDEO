# Shot Quality Gate + Video Quality Gate — Slice

Status: spec draft v2 (revised after Codex review; scope reduced)
Owner: AI-VIDEO Production Harness extension (provider-neutral, advisory)

This slice adds **two** typed **quality gates** that sit *adjacent* to AI-VIDEO Production — **not inside** it. They are the cheapest reliable way to catch obvious mistakes before/after video generation without changing canonical ownership.

## 1. Why this slice exists (revised scope)

The first draft (v1) tried to cover continuity, capability binding, multi-usage reference detection, and a VLM `IDENTITY_DRIFT` slot. Codex review (SCORE 2/10) showed that several of those checks required schema fields that don't exist on `FetchedVideoCandidate` or `PreviousShotState`, and would have duplicated ownership that already lives in Review/Repair.

This v2 reduces scope to **only what current types allow**:

| Gate | Checks (deterministic only) |
|---|---|
| **Shot Quality Gate** | `IDENTITY_ANCHOR`, `STRATEGY`, `COMPLEXITY` |
| **Video Quality Gate** | `RECEIPT_INTEGRITY`, `CONTENT_TYPE_BINDING` |

The dropped checks (continuity, capability binding, multi-usage reference, VLM `IDENTITY_DRIFT`, scene reference warning, complexity warning) are deferred to D1–D5 in [tasks.md](tasks.md#out-of-scope-tasks-deferred) for when the underlying types are extended or new typed seams exist.

## 2. Documents (read in order)

1. [requirements.md](requirements.md) — WHAT and WHY. Acceptance criteria, scope, forbidden responsibilities.
2. [design.md](design.md) — HOW. Package layout, schemas, algorithm, public surface, test plan.
3. [tasks.md](tasks.md) — Phased implementation plan (T1–T12). TDD-first.
4. [test-spec.md](test-spec.md) — Full test cases (Cases 1–7 + determinism + forbidden-field + architecture gate).
5. [integration.md](integration.md) — How callers consume the gates; worked JSON examples.

## 3. Planned code (post-merge)

- `src/ai_video/quality_gates/__init__.py`
- `src/ai_video/quality_gates/_gate_models.py`
- `src/ai_video/quality_gates/shot_quality_gate.py`
- `src/ai_video/quality_gates/video_quality_gate.py`
- `tests/test_quality_gates.py`
- `tests/fixtures/quality_gates_factory.py`

Plus three minimal Production-side seams (all optional, additive, no breakage of existing call sites):

- `src/ai_video/production/_lifecycle_schema.py` — add two optional fields to `VideoGenerationAttemptState`.
- `src/ai_video/production/_state_commit_video.py` — add two optional parameters to existing committer methods.
- `src/ai_video/production/_state_commit_gate_receipt.py` — small helper to validate gate receipt hashes.

## 4. Boundary at a glance

| Concern | Owner |
|---|---|
| Creative intent | Codex + Character / Scene / Shot |
| Project schema | `ProductionProject` |
| Asset identity | Asset Registry |
| Manifest lifecycle | `ProductionStateCommitter` |
| Provider selection | AI-VIDEO Provider Router |
| Default render | `HyperFrames` |
| QA / Repair | AI-VIDEO Review / Repair |
| Generation strategy hint | `VideoPlanner` |
| **Pre-gen shot validation** | **`ShotQualityGate` (NEW)** |
| **Post-fetch receipt validation** | **`VideoQualityGate` (NEW)** |
| **Optional gate-receipt handoff into committer** | **`committer` (extended; gate receipt stays side-receipt, not Manifest owner)** |

`ShotQualityGate` and `VideoQualityGate` are the only NEW logic owners. They produce **typed receipts** that callers may pass into the committer as advisory inputs; the committer never *requires* a receipt and never *writes* one. Losing a gate receipt loses no canonical truth.

## 5. Relationship to existing Review/Repair

- **P6 Review** (`production.review`) decides *final acceptance* of the rendered timeline based on collected QA evidence.
- **Shot/Video Quality Gates** decide *whether to spend the next call* (pre-gen) and *whether the fetched receipt is structurally consistent* (post-fetch). They are advisory and disposable.
- Gates **never** substitute for Review; they only produce structural pre-checks and may raise a `BLOCKED` status that the caller must respect.
- Gate results **do not flow** into `ReviewEvidence` (which is render-bound). They flow into Manifest as **optional hash pointers** (no payload duplication), and the full receipt is owned by the caller.

## 6. Explicitly out of scope (this slice)

- Creating a second Review system.
- Replacing `production.review.adjudicate_review_evidence` or `evaluate_final_acceptance`.
- Writing Manifest, Asset Registry, Timeline, or any durable artifact (gate receipts are caller-side; committer stores only their hashes if supplied).
- Choosing a Provider, selecting a Profile, fetching Provider capabilities.
- Calling H3 / Hailuo / Seedance / ComfyUI / any video provider.
- VLM/Human evaluator deployments. **No** `IDENTITY_DRIFT` or story-alignment check ships in this slice.
- Continuity or capability binding checks (deferred — require schema additions and ownership clarification).
- Automatic repair, retry, or remediation.
- LangGraph / new Agent Runtime / MCP server.
- New dependency graph schema.

## 7. Status of this slice

- Specs: v2 written after Codex review. Scope reduced to 3 + 2 deterministic checks.
- Implementation: not started. Run T1–T12 per `tasks.md` after spec approval.
- Tests: drafted alongside spec; will execute against the implemented module.