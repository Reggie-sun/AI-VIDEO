# AI-VIDEO Shot Readiness Gate Implementation Plan

## Status

Proposed implementation plan；current task is documentation-only。No runtime、Provider、media、
seed fix、quality acceptance、push或release is authorized by this artifact。

本 Plan 只实现配套 canonical Spec
`docs/superpowers/specs/2026-08-21-ai-video-shot-readiness-gate-v3.md` 的未来工作；仓库中不
存在需要保留、迁移或并行执行的第二份“旧 QA Gate Spec”。后续实现必须原地更新这一份
Spec 的 status/evidence，不得另建竞争的 gate truth。

**Goal:** 实现一个 pure、deterministic、provider-neutral 的
`ShotReadinessGate`，对 current `video-planner/3` request、plan、内嵌 requirement 与
verified projection执行唯一 pre-submit structural readiness decision，并保持所有
Production、Provider与quality owners不变。

**Scope:** Planning freshness seam、strict readiness models、three-check Gate、shared required-
asset helper、`require_current_video_plan()` compatibility migration、historical v2 new-attempt
STOP、focused tests、Harness routing与canonical runtime docs。

**Contract Surfaces:** `VideoPlanningRequest`、`VideoGenerationPlan`、
`ProviderNeutralVideoRequirement`、`VerifiedGenerationRequirementProjection`、
`require_current_video_plan()`、`prepare_shot_for_existing_production()`、
`AiVideoError(ErrorCode.PLANNING_PREFLIGHT_BLOCKED)`、`.agent/harness/policy.yaml`。

**Invariants:** Gate不重建Planner semantics、不选择Provider、不读写Production state；Router、
compiler、Manifest、Registry、committer、recovery、P5、`ResolvedTimeline`、HyperFrames、P6
Review/Pilot owners不变；BLOCKED后downstream side effects为0；READY只返回verified
requirement projection。

**Current / Target Behavior:** 当前 `require_current_video_plan()`同时验证freshness并决定
eligibility/assets。目标把current structural verifier保留为Planning-owned projection seam，
把唯一 `READY/BLOCKED` 与 STOP decision移到 `ShotReadinessGate`；existing façade继续返回
`VerifiedGenerationRequirementProjection`，handoff继续使用`generation_requirement`且不出现
`plan_hint`。

**Compatibility:** Historical `video-planner/2` request/plan bytes、hash fixtures与reopen保持
不变，但new-attempt readiness永远typed STOP；v3 projection没有自动v2 conversion。No schema、
Manifest、Registry、artifact-layout或durable-state migration。

**Out of Scope:** `/5 effective_seed=None`、ComfyUI/Provider fixes、Local H3 rerun、Candidate 2/3、
post-fetch `VideoQualityGate`、subjective quality、P6 acceptance、live/paid execution、new dependency、
CLI或publication。

**Acceptance Criteria:** Spec R-01–R-10全部有executable evidence；one readiness decision body；
v3 exact lineage and v2 STOP tests pass；BLOCKED spies remain zero；Harness routing matches exact
changed paths；independent review has no blocker；fresh exact-snapshot receipt self-verifies。

**Verification:** repository-standard `python -m pytest -p no:cacheprovider` focused/integration
commands、Architecture Gate、`git diff --check`、`make harness-inspect`、`make harness-verify`、
`make harness-receipt RECEIPT=<fresh-receipt-path>`；不运行live/media/browser verification。

**Spec / ADR:**
`docs/superpowers/specs/2026-08-21-ai-video-shot-readiness-gate-v3.md`。

## Problem Boundary Checkpoint

Implementation开始前，parent必须重新核对current `main`、working tree、live ownership与以下
固定边界：

- **Problem boundary:** current Planning freshness与readiness policy耦合在
  `require_current_video_plan()`；本slice只拆清这两个pure responsibilities。
- **Single owner:** `VideoPlanner` derives；Planning verifier signs freshness；
  `ShotReadinessGate` decides readiness；Router selects；adapter compiles；committer persists。
- **Old path to retire:** façade内重复的plan outcome、human review和required-asset decision body；
  所有 `plan_hint` handoff示例/kwargs；任何v2 new-attempt exception。
- **Historical path to preserve:** v2 parsing、serialization、hash fixtures和reopen-only evidence。
- **Unchanged contracts:** request `/5`、resolved `/6`、activation scope `/4` generation lineage；
  historical lifecycle hashes；P5 invalidation；Provider/Paid Gate；recovery；timeline；P6。
- **Focused first command:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_shot_readiness_gate.py \
  tests/test_planning_video_planner.py \
  tests/test_production_video_requirement.py \
  tests/test_errors.py -q
```

If another writer owns any target file, apply the repository same-file ownership rule before edits。
No worktree is created unless the user explicitly requests one。

## File and Ownership Map

| Area | Files | Responsibility |
| --- | --- | --- |
| Shared asset semantics | Create `src/ai_video/planning/_asset_readiness.py` | sole cycle-safe role/owner/final-visual/media-selection readiness logic |
| Planning verification diagnostics | Modify `src/ai_video/planning/_planner_models.py` | internal frozen failure model and exact reason vocabulary；no readiness verdict |
| Planning freshness and façade | Modify `src/ai_video/planning/video_planner.py` | typed projection verification；delegate readiness；no parallel decision body |
| Readiness models | Create `src/ai_video/quality_gates/_readiness_models.py` | strict request/result/check payloads、reason enums、hashes、validators |
| Gate behavior | Create `src/ai_video/quality_gates/shot_readiness_gate.py` | three-check evaluation、aggregation、`require_ready()` |
| Gate package | Create `src/ai_video/quality_gates/__init__.py` | export only approved Gate request/result/evaluator API |
| Focused tests | Create `tests/test_shot_readiness_gate.py` | exact lineage、diagnostics、asset matrix、STOP、purity/import boundary |
| Compatibility tests | Modify `tests/test_planning_video_planner.py` | façade return/handoff、v2 boundary、old-body retirement、no `plan_hint` |
| Harness | Modify `.agent/harness/policy.yaml`, `tests/test_agent_harness.py` | changed-path category、focused check、overlap routing |
| Canonical docs after executable proof | Modify `docs/agent-primary-contract-matrix.md`, `docs/v0.2-runtime-baseline.md`, `docs/v0.2-agentic-production-roadmap.md`, this Spec/Plan status only as current evidence supports | report implemented behavior without live/quality claims |

Do not modify Router、Provider adapters、compiler、Manifest/Registry/committer、Dependency Graph、
timeline、P6 Review/Pilot、workflow profiles或media files in this implementation slice。

## Milestone 1: RED Contract Tests and Shared Asset Owner

**Files:**

- Create: `tests/test_shot_readiness_gate.py`
- Create: `src/ai_video/planning/_asset_readiness.py`
- Modify: `src/ai_video/planning/video_planner.py`
- Modify: `tests/test_planning_video_planner.py`

**Contract:** Freeze the external behavior before moving ownership。The helper is the only
implementation of current role readiness semantics；Planner and future Gate both consume it。

**Implementation Notes:**

- First add failing tests for exact Character owner set、Scene owner、previous terminal id/owner、
  target final-visual role/binding、reusable-plate Review approval、selected video/audio identity、
  ambiguous selection和last-frame current semantics。
- Move `_current_review`、final-visual binding、role matching、role availability、media-selection
  completeness与required-role availability into `_asset_readiness.py` without changing behavior。
- Keep helper imports limited to planning models、read-only Production models and pure hashing/schema
  types；no Gate、Router、Provider、writer or IO imports。
- Existing planner tests must remain byte/behavior compatible after extraction, including v2 fixtures。

**Acceptance:** Existing planner outputs/hashes are unchanged；one helper owns all required-asset
decisions；tests demonstrate wrong-owner/binding and missing/ambiguous roles fail closed。

**Verification:** First capture expected RED failures for the new readiness cases，then require the
extraction regression seam to pass：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_planning_video_planner.py \
  tests/test_production_video_requirement.py \
  tests/test_errors.py -q
```

## Milestone 2: Strict Models and Typed Complete Diagnostics

**Files:**

- Create: `src/ai_video/quality_gates/_readiness_models.py`
- Create: `src/ai_video/quality_gates/__init__.py`
- Modify: `src/ai_video/planning/_planner_models.py`
- Modify: `tests/test_shot_readiness_gate.py`

**Contract:** Implement `ShotReadinessRequest`、ordered discriminated check outcomes、
`ShotReadinessResult` and stable reason codes exactly as the Spec。No model carries Provider、quality、
lifecycle or durable receipt state。

**Implementation Notes:**

- Request semantic projection contains only Gate contract version、current request hash、plan hash
  and optional embedded requirement hash；both request ids remain diagnostic-only。
- Add required reason enum values：`READINESS_REQUEST_SEAL_INVALID`、
  `LEGACY_PLANNER_REOPEN_ONLY`、`CURRENT_PLAN_PROJECTION_INVALID`、
  `VERIFIED_PROJECTION_BINDING_INVALID`、`PLAN_BLOCKED`、
  `HUMAN_REVIEW_UNRESOLVED`、`REQUIRED_ASSET_MISSING`。
- Enforce exactly three ordered checks with `check_id` discriminator；reject duplicate/missing checks、
  wrong payloads、status/check contradictions、READY without projection、BLOCKED with projection and
  invalid result hash。
- Recompute all semantic seals during evaluation/validation so `model_copy()` or low-level forged
  instances do not bypass the contract。

**Acceptance:** Same semantic request/result bytes produce identical hashes；diagnostic request-id
changes do not；all contradiction/tamper tests fail validation or become BLOCKED as specified。

**Verification:** Focused first command；add a direct import test proving package import has zero IO and
no Provider/lifecycle side effect。

## Milestone 3: Planning Projection Verification and Gate Evaluation

**Files:**

- Modify: `src/ai_video/planning/video_planner.py`
- Create: `src/ai_video/quality_gates/shot_readiness_gate.py`
- Modify: `tests/test_shot_readiness_gate.py`

**Contract:** Preserve current request→plan→embedded requirement verification in one Planning-owned
pure seam。Gate consumes its typed success/failure, emits all three diagnostics, and is the only
`READY/BLOCKED` owner。

**Implementation Notes:**

- Extract current seal、deterministic plan derivation/id、source/Shot、requirement intent/Scene/
  Character/asset/Review evidence and projection checks from the façade into a typed Planning
  verifier。It returns either the exact `VerifiedGenerationRequirementProjection` or a typed failure；
  it does not inspect plan outcome/warnings or required-role readiness。
- The failure model carries ordered reason codes fixed by the Spec and ordered field paths；collect
  every independently evaluable failure，with dependent binding flags explicitly false。Do not
  reduce this to free-form first-error text。
- Do not export a public production bypass that returns a verified projection without Gate readiness。
- Gate invokes the verifier once, validates exact equality among request、plan、embedded requirement
  and projection, then independently evaluates eligibility and the plan-declared roles through the
  shared helper。It does not call a second Planner builder or reconstruct requirement fields。
- Always emit binding、eligibility and asset outcomes in that order。Only all-PASS returns the exact
  verifier projection；any BLOCKED path returns no top-level projection。
- Convert v2 to `LEGACY_PLANNER_REOPEN_ONLY` without modifying or converting v2 models。

**Acceptance:** Mutation matrix covers outer/request/plan/requirement/projection seals、unique current
derivation、source and Shot identity、intent/Scene/Character/asset/Review evidence。v2 parse/reopen
fixtures stay byte-identical but Gate never returns READY for v2。

**Verification:** Focused first command plus deterministic repeat tests。No network、Provider、media or
Production state command is permitted。

## Milestone 4: Compatibility Façade, STOP, and Old-Path Retirement

**Files:**

- Modify: `src/ai_video/planning/video_planner.py`
- Modify: `tests/test_planning_video_planner.py`
- Modify: `tests/test_shot_readiness_gate.py`

**Contract:** `require_current_video_plan()` keeps its signature、typed error and projection return；
`prepare_shot_for_existing_production()` keeps `current_shot` + `generation_requirement` handoff。
Only Gate decides readiness。

**Implementation Notes:**

- Replace the façade's eligibility、warning and required-asset body with
  `ShotReadinessRequest.create()` → `ShotReadinessGate.evaluate()` → `require_ready()`。
- Use a function-local Gate import if needed for cycle-safe module initialization；add tests for both
  import orders。
- `require_ready()` maps ordered typed reason codes to
  `PLANNING_PREFLIGHT_BLOCKED`, `retryable=False` without raw traceback。
- Preserve zero-call spies for Router、compiler、Provider、materializer、composition、render、
  Manifest/Registry writer and committer on every blocked family。
- Search production source/tests/examples for `plan_hint` and remove only readiness integration uses；
  architecture test pins exact handoff kwargs and prevents reintroduction。
- Keep resolved non-blocking audit warnings visible and eligible exactly as current behavior。

**Acceptance:** Existing callers observe the same public return/error types；ready handoff occurs once
with exact projection；blocked paths hand off zero times；no second readiness algorithm or `plan_hint`
path remains。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_shot_readiness_gate.py \
  tests/test_planning_video_planner.py \
  tests/test_production_shot_router.py \
  tests/test_production_video_requirement.py \
  tests/test_production_video.py \
  tests/test_errors.py -q
```

## Milestone 5: Harness Routing, Architecture Review, and Canonical Docs

**Files:**

- Modify: `.agent/harness/policy.yaml`
- Modify: `tests/test_agent_harness.py`
- Modify: `docs/agent-primary-contract-matrix.md`
- Modify: `docs/v0.2-runtime-baseline.md`
- Modify: `docs/v0.2-agentic-production-roadmap.md`
- Modify: `docs/superpowers/specs/2026-08-21-ai-video-shot-readiness-gate-v3.md`
- Modify: `docs/superpowers/plans/2026-08-21-ai-video-shot-readiness-gate-v3.md`

**Contract:** Every implementation path maps to focused readiness and architecture checks；docs report
only executable offline truth and retain explicit live/quality non-authorization。

**Implementation Notes:**

- Add `shot_readiness_gate_tests` exactly as specified。
- Add `shot_readiness_gate` category for `src/ai_video/quality_gates/**`、
  `src/ai_video/planning/_asset_readiness.py` and `tests/test_shot_readiness_gate.py`，routing to the
  focused check plus `task_architecture_gate`。
- Add the focused check to `video_planning.check_ids` because the façade/shared helper change；retain
  existing `video_planner_tests`、shared requirement tests and Architecture Gate checks。
- Harness tests must assert exact path→category→check IDs, overlapping category de-duplication and
  no weakening of fallback/full-test behavior。
- Architecture/import tests reject Provider/lifecycle/IO imports、duplicate role-readiness helpers、
  direct production projection bypass and `plan_hint` readiness handoff。
- Update canonical docs only after focused tests pass。State explicitly that seed fix、Local H3 rerun、
  media quality and Final Acceptance remain incomplete。

**Acceptance:** `make harness-inspect` shows the intended focused/overlap checks for exact staged
paths；canonical docs distinguish implemented offline Gate behavior from all deferred runtime work。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_agent_harness.py \
  tests/test_architecture_gate.py \
  tests/test_architecture_gate_cli.py -q
python -m scripts.architecture_gate check
git diff --check
```

## Milestone 6: Independent Review and Exact-Snapshot Acceptance

**Files:** All task-owned files above；no additional product surface。

**Owner / Dependencies:** Parent owns final decision and verification。Because core pre-submit behavior
changes, use native named `reviewer` after implementation and before final acceptance；reviewer is
read-only and must not rewrite the solution。

**Contract:** Review checks the stated bug、scope isolation、single owner、v2 compatibility、zero
side effects、test realism and no quality/lifecycle drift。Parent verifies every blocking claim and the
final diff。

**Implementation Notes:**

- Reviewer output must contain `Verdict`、`Blocking issues`、`Non-blocking concerns`、file/test
  evidence and minimal follow-up。
- Parent reviews every changed line, confirms task ownership, stages only exact task files, then runs
  Harness against the non-empty staged snapshot in its detached temporary worktree。
- Do not commit a generated Harness receipt unless policy explicitly treats it as task-owned tracked
  content；report its repository-relative path from `.agent/harness/runs/`。

**Acceptance:** Reviewer has no blocking issue；fresh receipt is passing、integrity-valid、policy-valid
and snapshot-valid；final staged/commit diff contains no unrelated changes。

**Verification:**

```bash
make harness-inspect
make harness-verify
make harness-receipt RECEIPT=<fresh-receipt-path>
git diff --cached --check
```

After the task commit, verify the exact commit range when completion policy requires it：

```bash
make harness-verify-range BASE_REF=<verified-base-commit>
make harness-receipt RECEIPT=<fresh-range-receipt-path>
```

## Requirements-to-Milestones Traceability

| Spec requirement | Milestones | Primary executable evidence |
| --- | --- | --- |
| R-01 exact v3 lineage | 2–3 | seal/equality/unique-derivation mutation matrix |
| R-02 no Planner re-derivation | 3, 5 | one verifier call and architecture import/call search |
| R-03 one readiness owner | 3–4 | façade AST/call tests and blocked/ready behavior |
| R-04 v2 compatibility | 3–4 | historical hash/reopen fixtures plus typed new-attempt STOP |
| R-05 no `plan_hint` | 4–5 | exact kwargs and source/test/example search |
| R-06 shared asset owner | 1, 3 | role matrix and single-helper architecture test |
| R-07 typed complete diagnostics | 2–3 | discriminator/order/contradiction/result-hash tests |
| R-08 zero side effects | 3–4 | downstream spy matrix |
| R-09 lifecycle/quality isolation | 4–5 | import audit and focused Router/P8 regression tests |
| R-10 Harness truth | 5–6 | routing tests and self-verified exact-snapshot receipt |

## Rollback

No data migration exists。Before merge/commit acceptance, revert the task-owned code/docs as one
unit。After acceptance, rollback must restore the previous façade and remove Gate models/evaluator/
tests/Harness category together；the shared asset helper may move back only if both Planner and Gate
consumers are reverted in the same change。Do not alter Manifest/Registry bytes、run recovery、convert
v2 evidence、restore `plan_hint` or reopen v2 new-attempt creation。

If a downstream `/5` attempt exists for unrelated reasons, this pure Gate rollback does not touch it；
existing explicit recovery remains the only owner。

## Deferred Sequencing

Only after this implementation is complete、reviewed、committed and exact-snapshot verified may a
separate slice diagnose/fix `VideoGenerationRequest /5 effective_seed=None` for Local H3。After that
separate fix is accepted, a newly authorized Local H3 experiment may run against the existing
Candidate 1 oracle。

The later experiment belongs to P6 Review/Pilot perceptual evidence。Its result cannot modify this
Gate's structural contract, create a post-fetch `VideoQualityGate`, or retroactively prove readiness、
generation、activation、quality acceptance or Final Acceptance。

The later experiment's preserved oracle is
`runs/c2-alice-local-h3-quality-candidate-1-20260821/output/alice-c2-local-h3-quality-candidate-1.mp4`
with SHA-256
`2b02881d81b1226ab90e9791a472be7b6f02ef1b8584e5b2e1fe7d4050773de8`。It must not be copied into
Gate fixtures or treated as current acceptance evidence。
