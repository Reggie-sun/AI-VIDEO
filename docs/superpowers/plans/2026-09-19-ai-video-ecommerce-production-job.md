# AI-VIDEO Ecommerce Production Job Implementation Plan

## Status

M0–M7 offline implementation and deterministic scenarios are committed on local `main` through `f07d7de`. Governing design：`docs/superpowers/specs/2026-09-19-ai-video-ecommerce-production-job.md`。Contracts、pure Skill-side exporter、canonical compiler/bootstrap、read-only projection/resume、bounded ordered Shot execution、composition/render、whole-video QC and delivery all use existing Production owners. M7 now includes a full canonical two-Shot Job through render、review、delivery and exact replay, plus a separate CAPTION timing `FAIL` → newly sealed composition → rerender → fresh review → delivery path. The M7 focused suite passed `133` tests. Final closure evidence must still be checked against the exact later Harness receipt and independent review recorded for that snapshot.

`c24ef92` 的历史 exact-range Harness receipt（`.agent/harness/runs/ecommerce-production-job-cta-repair-20260924-01/receipt.json`）只证明该 snapshot。后续 `b404e91`、`c5ec8e0` 修正 P6 CAPTION per-group evidence/coverage，`8c72763` 加入与封存要求一致的 1080×1920、3 秒 Shot 和 6 秒 final offline MP4 fixture，`f07d7de` 证明 CAPTION 局部修复跨完整 Job 后仍保留已接受 Shot。Fixture runner/evaluator 为确定性替身，未产生真实商品广告或人工视觉验收。详细 evidence 与当前 final gate 见 `docs/record_for_agent/2026-09-19-ecommerce-production-job-m7-offline-code.md`。

本文不授权 live Provider/media execution，也不改变 current Production、release 或 Final Acceptance truth；未运行真实 Provider submit、真实 render、Production activation 或人工观看验收。

## Goal

在不重写 AI-VIDEO Production SDK 的前提下，新增一个 Python-first `EcommerceProductionJob` application layer，把 `ecommerce-ad-workflow/package/2` 经 runtime-neutral handoff 连接到 canonical Project、逐 Shot generation / gate / repair、composition、whole-video QC、Final Acceptance 与 delivery bundle，并具备 precise resume 和 no-silent-fallback semantics。

## Scope

### In Scope

- versioned runtime-neutral handoff contract and Skill-side pure exporter；
- handoff to existing Production artifact proposal compiler；
- immutable Job request、read-only projection、typed blocker and next-action contracts；
- application service that invokes existing canonical owners；
- sequential Shot execution and bounded local repair integration；
- composition/final-render orchestration over `ResolvedTimeline` and HyperFrames；
- strong whole-video evidence enforcement and accepted delivery packaging；
- offline deterministic integration tests、failure/replay/recovery tests、docs and Harness routing。

### Out Of Scope

- Product URL crawler / Product Truth extraction；
- new public CLI、API server、queue、database or UI；
- new Provider or renderer；
- campaign variants、batch scheduling or platform multi-export；
- live/paid Provider submit、media generation or production qualification；
- automatic publishing、spend、ROAS or attribution；
- schema migration of existing projects。

## Invariants

- `ProductionStateCommitter` remains the only Production writer / activation / recovery owner.
- Manifest remains the only mutable lifecycle truth; Job projection is derived and never persisted as a parallel state machine.
- Runtime source must not import or invoke `.agents/skills/**`.
- `ResolvedTimeline` remains the only order/frame/sample/trim owner.
- HyperFrames remains the default Production renderer; no fallback.
- Every external side effect is exact-identity, finite, replay-safe and evidence-bound.
- Per-Shot Gate blocks the next Shot; whole-video Gate blocks delivery.
- `FAIL`、`NOT_EVALUATED` and unknown outcome remain distinct.
- No local score or callback `PASS` substitutes for required final-output evidence.
- Existing public CLI and Production APIs remain behavior-compatible.

## Delivery Strategy

实现按 contract dependency 顺序分为八个 milestones。每个 milestone 先建立 failing contract tests，再做最小 implementation，再运行 focused verification。Milestone 之间不以 prose 状态推进：只有前一 milestone 的 executable acceptance criteria 通过，下一层才可依赖其 public surface。

```text
M0 Baseline / Contract Guards
  -> M1 Runtime-Neutral Handoff
  -> M2 Canonical Artifact Compiler
  -> M3 Job Projection / Resume
  -> M4 Shot Execution / Repair
  -> M5 Composition / Render
  -> M6 Final QC / Delivery
  -> M7 End-to-End Verification / Docs
```

## File Map

### New Production Modules

- `src/ai_video/production/ecommerce_job_contracts.py`
  - `EcommerceProductionHandoff`
  - `EcommerceProductionJobRequest`
  - `EcommerceProductionJobProjection`
  - `EcommerceJobNextAction`
  - `EcommerceJobBlocker`
  - `EcommerceDeliveryProfile`
  - `EcommerceVisualSystemProfile`
  - `EcommerceLayoutPlan`
  - `EcommerceProductionCompileProfile`
  - delivery bundle inventory contracts
- `src/ai_video/production/ecommerce_job_compiler.py`
  - pure handoff validation and compilation into existing artifact proposals / prepared artifacts
- `src/ai_video/production/ecommerce_job.py`
  - `EcommerceProductionJobService.inspect()`、`advance_once()` and optional finite `run_until_blocked()`
- `src/ai_video/production/ecommerce_job_repair.py`
  - bounded repair decision and exact-attempt preparation; only if extraction remains a cohesive distinct responsibility
- `src/ai_video/production/ecommerce_job_assembly.py`
  - pure composition preparation and invocation boundary for existing timeline/render owners
- `src/ai_video/production/delivery_packager.py`
  - exact Final Accepted output bundle assembly and verification

`ecommerce_job.py` MUST NOT absorb compiler、repair algorithms、composition construction or bundle I/O into one oversized module. Existing `ecommerce_ad_coordinator.py` is already large and MUST NOT receive the new Job responsibility.

### Skill-Side Handoff

- Create `.agents/skills/ecommerce-ad-workflow/scripts/export_runtime_handoff.py`
- Create `.agents/skills/ecommerce-ad-workflow/schemas/ecommerce-production-handoff.schema.json`
- Export requires caller-authored exact delivery / visual system / per-ad layout / compile profile inputs; the exporter does not generate generic visual defaults.
- Update `.agents/skills/ecommerce-ad-workflow/SKILL.md` only to document the explicit export seam and its non-runtime authority
- Update `.agents/skills/ecommerce-ad-workflow/scripts/contract_models.py` only if package/2 validation must expose a stable projection helper; canonical runtime handoff models remain under `src/`

### Existing Integration Surfaces

- Update `src/ai_video/production/__init__.py` with the minimal approved public exports.
- Reuse `src/ai_video/production/ad_creative.py` and `ad_creative_types.py`; do not fork `AdCreativePlan` semantics.
- Reuse `src/ai_video/production/ecommerce_ad_coordinator.py` as lower-level ordered Shot / closure execution.
- Reuse `src/ai_video/production/generation_feedback.py` and existing decision/diagnosis contracts.
- Reuse `src/ai_video/production/state_commit.py` and its existing public bootstrap/recovery methods.
- Reuse `src/ai_video/production/composition.py`、`composition_contracts.py`、`timeline.py` and HyperFrames adapter.
- Reuse `src/ai_video/production/ecommerce_quality_gate.py`、P6 review and Final Acceptance owners.

### Tests

- Create `tests/test_production_ecommerce_job_contracts.py`
- Create `tests/test_production_ecommerce_job_compiler.py`
- Create `tests/test_production_ecommerce_job_projection.py`
- Create `tests/test_production_ecommerce_job.py`
- Create `tests/test_production_ecommerce_job_repair.py`
- Create `tests/test_production_ecommerce_job_assembly.py`
- Create `tests/test_production_delivery_packager.py`
- Update `tests/test_ecommerce_ad_workflow_skill.py`
- Update `tests/test_runtime_skill_boundary.py`
- Update `tests/test_production_ecommerce_post_media_e2e.py`
- Update `tests/test_agent_harness.py` only when changed-path routing or required checks change

### Canonical Documentation And Routing

- Update `docs/agent-primary-contract-matrix.md` with one owner row for the Job application surface and forbidden parallel lifecycle.
- Update `docs/v0.2-runtime-baseline.md` only after executable behavior exists.
- Update `docs/v0.2-agentic-production-roadmap.md` with actual milestone status, not planned status.
- Update `.agent/harness/policy.yaml` if the new modules require focused check routing; keep it synchronized with matrix and Harness tests.
- Add a stable session record under `docs/record_for_agent/` at implementation checkpoint.

Before execution, re-check file ownership because several canonical files may contain unrelated in-progress changes. Same-file overlap requires user ownership/sequence resolution before writing.

## Milestone 0: Freeze Baseline And Contract Guards

### Objective

Establish executable boundaries before adding behavior so the implementation cannot create a second lifecycle, import Skills into Runtime or weaken current closure.

### Changes

1. Add contract tests that assert:
   - all new request/projection objects are immutable strict models；
   - no status field is writable as durable state；
   - Runtime-to-Skill dependency remains forbidden；
   - existing `run_ecommerce_ad_production()` public semantics do not regress；
   - Legacy CLI command set and exit behavior remain unchanged。
2. Extend Architecture/Harness routing only where new owned paths would otherwise be unmapped.
3. Capture current focused suite results before implementation; classify pre-existing failures separately.

### Verification

```bash
python -m pytest -q \
  tests/test_runtime_skill_boundary.py \
  tests/test_production_ecommerce_ad_coordinator.py \
  tests/test_production_ecommerce_post_media_e2e.py

python scripts/agent_harness.py inspect \
  --path src/ai_video/production/ecommerce_job_contracts.py \
  --path src/ai_video/production/ecommerce_job.py
```

### Exit Criteria

- New source paths have explicit owner and Harness routing.
- Boundary tests fail for an intentional Skill dependency or second mutable lifecycle.
- Existing ecommerce closure suite baseline is known.

## Milestone 1: Runtime-Neutral Handoff

### Objective

Create a deterministic, machine-readable boundary from authoring `package/2` to Production Runtime without importing Skill code from `src/`.

### Contract

- Schema: `ecommerce-production-handoff/1`.
- Identity: canonical SHA-256 excluding `handoff_id`.
- Exporter: pure/no-network/no-write.
- Runtime parser: strict, rejects extra fields and unsupported gaps.
- Package blockers remain blockers; they are never dropped to make export succeed.
- Technical delivery、visual system、per-ad layout and compile binding are distinct content-addressed contracts.
- Layout must resolve every package Shot、copy graphic and product presentation exactly once; typography and safe-area values must match the reviewed visual system.
- Current talent-free forms remain explicit blockers until the canonical `AdCreativePlan` owns a truthful no-protagonist representation.

### Implementation

1. Define handoff models in `ecommerce_job_contracts.py` using existing Production types where semantics already exist.
2. Implement canonical serialization/hash helper using existing hashing conventions.
3. Implement Skill-side exporter that validates `package/2`, projects fields explicitly and validates the runtime handoff schema.
4. Check in schema bytes and prove model/schema drift detection in tests.
5. Keep exporter output free of provider、permit、Manifest、timeline and mutable lifecycle fields.
6. Reject stale visual identities、typography drift、safe-area drift、unmapped Shot/copy/presentation and generic fallback placement.

### Required Tests

- same package bytes -> identical handoff bytes/hash；
- one semantic package change -> different identity；
- package blocker/unresolved capability -> explicit handoff blocker；
- unknown/extra/missing fields -> deterministic validation error；
- no Runtime import/path/identity references to Skill；
- example package/2 round-trip validates。
- exact reviewed visual contracts produce deterministic handoff bytes；visual drift changes identity or fails validation；
- a technically valid but still unresolved physical/product integration requirement remains a blocker。

### Verification

```bash
python -m pytest -q \
  tests/test_ecommerce_ad_workflow_skill.py \
  tests/test_runtime_skill_boundary.py \
  tests/test_production_ecommerce_job_contracts.py
```

## Milestone 2: Canonical Artifact Compiler

### Objective

Compile handoff data into existing AI-VIDEO Production artifact proposals and bootstrap payloads without direct mutation.

### Contract

```text
EcommerceProductionHandoff
  -> ProductionBrief proposal
  -> Story / Character / Scene proposals
  -> Storyboard / ordered Shot proposals
  -> AdCreativePlanProposal
  -> asset/audio/caption requirements
  -> PreparedArtifact set
```

### Implementation

1. Add pure `compile_ecommerce_production_handoff()`.
2. Produce current schema versions only; do not create ecommerce-specific duplicates of generic artifact models.
3. Bind Product Truth / claims / CTA / Hook / beats / product presentation / graphics / sound cues to exact existing proposal fields.
4. Return explicit unmapped-capability blockers instead of prose warnings.
5. Add a bootstrap adapter that passes compiler output to the public canonical committer surface.
6. Reopen the project after commit and verify exact selected revisions and artifact hashes.

### Required Tests

- every package Shot maps once and preserves order；
- every claim/graphic/presentation/sound reference resolves；
- compiler rejects dangling references and unsupported executable requirements；
- initial bootstrap creates one valid canonical Project / Registry / Manifest set；
- exact replay is a no-op；
- divergent existing project fails or enters explicit reconciliation, never overwrites；
- injected replace interruption yields typed unknown outcome and recovery route。

### Verification

```bash
python -m pytest -q \
  tests/test_production_ecommerce_job_compiler.py \
  tests/test_production_state_commit.py \
  tests/test_production_project.py \
  tests/test_production_registry.py
```

## Milestone 3: Read-Only Projection And Resume

### Objective

Make every invocation begin with a strict reopen and derive exactly one safe next action from canonical state.

### Implementation

1. Define `EcommerceProductionJobRequest`、`EcommerceProductionJobProjection`、`EcommerceJobNextAction` and `EcommerceJobBlocker`.
2. Implement `EcommerceProductionJobService.inspect()` as strict/read-only/no-network.
3. Resolve state only through standard Project/Registry/Manifest/Dependency/Review readers.
4. Derive smallest invalid frontier and the next ordered Shot.
5. Reject mismatched job/project/handoff/policy identities and stale evidence.
6. Expose explicit `RECOVER_UNKNOWN_OUTCOME` rather than inferring success/failure.

### Required Tests

- empty root -> `BOOTSTRAP_PROJECT`；
- exact bootstrapped state -> reference or first-Shot action；
- partially completed Shots -> next incomplete Shot only；
- audio/composition invalidation -> no Shot regeneration；
- final-review invalidation -> `REVIEW_FINAL` unless diagnosis invalidates upstream；
- hash/revision mismatch -> typed blocker；
- unknown outcome -> recovery action；
- repeated `inspect()` changes no files, network or state。

### Verification

```bash
python -m pytest -q \
  tests/test_production_ecommerce_job_projection.py \
  tests/test_production_dependency.py \
  tests/test_production_project_read_only.py
```

Use the repository's actual test filenames discovered at implementation time; do not create aliases merely to satisfy this example command.

## Milestone 4: Shot Execution And Bounded Repair

### Objective

Connect the application service to existing Shot readiness、generation feedback、Provider execution、per-Shot gate and canonical activation while preserving hard barriers.

### Implementation

1. `advance_once(GENERATE_SHOT)` builds the exact existing execution facade from request, selected project state and sealed policies.
2. Delegate ordered execution to the current ecommerce coordinator rather than duplicating its algorithm.
3. Convert gate outcomes into typed next actions:
   - `PASS` -> canonical activation and next Shot；
   - `FAIL` -> diagnosis then bounded media repair；
   - `NOT_EVALUATED` -> evidence repair first；
   - unknown -> explicit recovery stop。
4. Implement repair controller only as a small owner around existing decision/diagnosis contracts.
5. Enforce per-Shot and job-level finite ceilings.
6. A provider switch creates new routing/binding/permit/attempt identity and invalidates provider-specific evidence.

### Required Tests

- Shot N+1 submit is impossible before Shot N exact Gate `PASS`；
- Provider success without valid media evidence does not activate；
- evidence repair does not submit new media；
- media repair changes one diagnosed variable and creates new attempt identity；
- exhausted ceiling returns `BLOCKED`；
- unknown outcome performs no retry；
- accepted prior Shots remain active during local repair；
- provider switch cannot reuse old permit/evidence；
- exact replay has no external side effect。

### Verification

```bash
python -m pytest -q \
  tests/test_production_ecommerce_job.py \
  tests/test_production_ecommerce_job_repair.py \
  tests/test_production_ecommerce_ad_coordinator.py \
  tests/test_production_ecommerce_quality_gate.py \
  tests/test_generation_feedback.py
```

## Milestone 5: Composition And Final Render

### Objective

Build a complete ad composition from accepted assets using the existing single timeline and renderer.

### Implementation

1. Add a pure composition preparation function that binds exact `AdCreativePlan`, accepted Shot assets, commercial graphics, CTA/end card and audio/caption requirements.
2. Resolve voice/TTS、dialogue、captions、BGM、SFX、ducking and intentional silence through existing audio/caption contracts.
3. Fail before render when a required track, caption evidence, commercial source or timing binding is missing.
4. Invoke existing `resolve_composition()` and HyperFrames adapter.
5. Materialize and hash exact render bytes before any review.
6. On replay, reuse the exact accepted/current render only when every desired fingerprint still matches.

### Required Tests

- one canonical timeline drives video/audio/captions/graphics；
- CTA and end card are present and correctly bound；
- missing VO/caption/BGM/SFX requirement blocks render；
- advertising graphics are not silently converted to dialogue captions；
- no renderer fallback；
- stale plan/asset/timeline identity invalidates render；
- composition-only change does not regenerate Shots；
- renderer unknown outcome routes to explicit recovery。

### Verification

```bash
python -m pytest -q \
  tests/test_production_ecommerce_job_assembly.py \
  tests/test_production_composition.py \
  tests/test_production_audio.py \
  tests/test_production_captions.py \
  tests/test_hyperframes_adapter.py
```

## Milestone 6: Whole-Video QC And Delivery Bundle

### Objective

Close the gap between render success and user-visible accepted ecommerce ad.

### Implementation

1. Require the exact current render hash across universal、ecommerce、caption and final-output evidence.
2. Reject bare callback/model `PASS` when required observations/evidence are absent.
3. Route known whole-video failures to the smallest repair frontier; do not default to full pipeline rerun.
4. Record Final Acceptance only via existing canonical owner.
5. Implement delivery packager with temporary staging, inventory hash verification and atomic publish.
6. Delivery bundle includes full lineage pointers but no secrets or mutable permits.

### Required Tests

- technical success + visual failure cannot pass；
- ecommerce pass + missing final-output observation cannot pass；
- stale render evidence cannot pass；
- partial rubric coverage cannot be averaged into pass；
- caption-applicable output requires caption evidence；
- exact Final Accepted render packages successfully；
- non-accepted/hash-mismatched output is refused；
- packaging never re-encodes or mutates Production state；
- interrupted bundle publish leaves no active partial bundle。

### Verification

```bash
python -m pytest -q \
  tests/test_production_ecommerce_post_media_e2e.py \
  tests/test_production_final_output.py \
  tests/test_production_review.py \
  tests/test_production_delivery_packager.py
```

## Milestone 7: Offline End-To-End Closure

### Objective

Prove the application path against deterministic fakes and exact artifacts, then update canonical truth documents.

### Scenarios

1. Fresh project -> bootstrap -> two Shots -> per-Shot pass -> composition -> final pass -> delivery.
2. Interruption after first Shot activation -> reopen -> second Shot only.
3. First Shot `NOT_EVALUATED` -> evidence repair -> re-evaluate without Provider resubmit.
4. Second Shot known failure -> one repair -> full revalidation -> continue.
5. Provider submit outcome unknown -> stop -> explicit recovery -> resume.
6. Final CAPTION failure whose exact evidence identifies cue timing or layout readability, with a corrected, newly sealed composition revision -> composition-local repair -> re-render -> final review; accepted Shots unchanged. CAPTION `UNINTENDED_TEXT` and plan-bound CTA text, position or color failure -> `BLOCKED` for diagnosis and, where plan-bound, explicit authoring handoff plus immutable Project revision reconciliation; they must not be presented as composition-only repair. Persisted CAPTION `NOT_EVALUATED` requires evidence repair through the canonical review owner before retry.
7. Exact completed replay -> zero external effects and same bundle identity.

### Documentation

Only after executable tests pass:

- record implemented surfaces in runtime baseline；
- update roadmap status with completed/deferred boundaries；
- add matrix owner/routing references；
- document Python API and explicit absence of public CLI；
- record no-live-media boundary unless an independently authorized empirical run exists。

### Verification

Run focused suites first, then repository policy-selected checks over the exact staged snapshot or exact commit range:

```bash
python -m pytest -q \
  tests/test_production_ecommerce_job_contracts.py \
  tests/test_production_ecommerce_job_compiler.py \
  tests/test_production_ecommerce_job_projection.py \
  tests/test_production_ecommerce_job.py \
  tests/test_production_ecommerce_job_repair.py \
  tests/test_production_ecommerce_job_assembly.py \
  tests/test_production_delivery_packager.py \
  tests/test_production_ecommerce_post_media_e2e.py \
  tests/test_runtime_skill_boundary.py

python scripts/agent_harness.py inspect --staged

python scripts/agent_harness.py verify \
  --staged \
  --run-id ecommerce-production-job-v1

python scripts/agent_harness.py verify-receipt \
  .agent/harness/runs/ecommerce-production-job-v1/receipt.json
```

Before this command, stage only the task-owned implementation paths with explicit `git add <path>` calls. The final Harness invocation MUST run against that exact non-empty staged snapshot; if the run ID already exists, choose a new concrete unique ID and use its returned receipt path.

## Failure Taxonomy Mapping

| Condition | Existing owner / classification | Job response |
| --- | --- | --- |
| invalid package/handoff | validation + `AiVideoError` | `BLOCKED` |
| missing capability | `BLOCKED_CAPABILITY` | `BLOCKED` or explicit provider re-route |
| stale/missing Gate evidence | `NOT_EVALUATED` | `REPAIR_SHOT_EVIDENCE` |
| known media defect | generation diagnosis / QA failure | `REPAIR_SHOT_MEDIA` if bounded |
| side-effect result unknown | existing unknown-outcome error | `RECOVER_UNKNOWN_OUTCOME` |
| renderer/composition input missing | validation/dependency | `PREPARE_COMPOSITION` or `BLOCKED` |
| final-output evidence incomplete | P6/final gate | `REVIEW_FINAL` |
| accepted bytes mismatch | provenance/hash failure | `BLOCKED` |

No new generic `FAILED` bucket should erase these distinctions.

## Compatibility And Rollback

- All additions are opt-in Python APIs and versioned `/1` schemas.
- Existing projects do not migrate until explicitly invoked with a valid handoff.
- Existing low-level coordinators remain callable.
- No new dependency or public CLI surface.
- Rollback removes new modules/exports/exporter/schema and docs while leaving existing canonical state readable.
- If a partially bootstrapped project exists, rollback does not delete evidence; existing explicit recovery/reader surfaces remain authoritative.

## Review Gates

### Architecture Review

Must confirm:

- no duplicate lifecycle、timeline、renderer、Registry or QA owner；
- no runtime-to-Skill dependency；
- no caller-supplied callback can bypass evidence requirements；
- no oversized responsibility added to `ecommerce_ad_coordinator.py`；
- resume and invalidation use canonical state rather than Job-local flags。

### Safety Review

Must confirm:

- secret/permit/budget/egress boundaries unchanged；
- finite attempt ceilings；
- unknown outcome fail-closed；
- no silent provider/renderer/rubric fallback；
- bundle contains no secret-bearing receipts。

### Quality Review

Must confirm:

- final-output evidence is mandatory, not a bare verdict；
- local metrics cannot satisfy unrelated requirements；
- repair preserves already accepted ad invariants；
- final MP4, not intermediate artifacts, is the delivery decision object。

## Definition Of Done

Implementation is complete only when:

1. All acceptance criteria in the governing spec have executable coverage.
2. The deterministic offline end-to-end scenarios pass.
3. Exact replay and every unknown-outcome boundary are tested.
4. Canonical docs describe only behavior proven in the current tree.
5. Exact-snapshot Harness receipt is passing, fresh and scope-valid.
6. Independent risk-based review has no unresolved P0/P1 finding.
7. No unrelated dirty work is included in the commit.
8. Live Provider/media quality is either separately proven against exact bytes or explicitly reported as unverified.

## Recommended Execution Boundary

The first implementation task includes Milestones 0–3 only: contracts、exporter、compiler and read-only projection/resume. This checkpoint creates the stable application boundary without authorizing Provider/media effects. Milestones 4–6 remain separately reviewable slices because they cross paid/local execution、repair、render and Final Acceptance gates.
