# AI-VIDEO Paid Provider Gate Implementation Plan

> Approved for offline implementation on local `main` by the user's 2026-08-18 choice `A`. No real Provider, network, secret, quota, paid call, push, release or publish is authorized.

**Goal:** 在 P8 前实现 provider-neutral、Manifest-selected、crash-safe 的 Paid Provider Gate，阻止任何缺少 exact opt-in、budget reservation、egress authorization、live authorization 和 durable submit intent 的 remote metered call。

**Architecture:** `paid_provider.py` owns pure immutable safety contracts；Manifest 2.6 owns budget pointer and per-attempt paid lifecycle；`ProductionStateCommitter` plus `_state_commit_paid_provider.py` remains the only writer/recovery owner；concrete transports accept only a shared one-use committer permit。P8 later reuses the Gate-owned billable-effect identity and must not duplicate task IDs。

**Spec:** `docs/superpowers/specs/2026-08-18-ai-video-paid-provider-gate.md`

## Global Constraints

- `PAID_PROVIDER_MANIFEST_SCHEMA = "2.6"`；Registry remains `2.1`。
- P8 Task 0 must select Manifest `2.7` / Registry `2.2` after Gate acceptance。
- Manifest `2.0`-`2.5` remain readable；no migration、downgrade or compatibility rewrite。
- `ProductionStateCommitter` is the sole writer/recovery owner。
- No global live authorization singleton or ambient boolean authority。
- No secret value、Authorization header、cookie、signed URL or raw Provider response in models/receipts/logs/tests。
- No new dependency、CLI、Legacy layout、renderer、timeline、dependency or Registry change。
- No P8 video request/task/poll/fetch implementation in this slice。
- All verification is deterministic fake/no-network/no-charge。
- Avoid current unrelated dirty files: `scripts/smoke_p7_1_local_image.py`、`tests/production_project_factory.py`、`tests/test_production_p7_1_local_image_e2e.py`。

## Problem Boundary

### Single owner

- Pure contract: `src/ai_video/production/paid_provider.py`。
- Durable owner: `src/ai_video/production/state_commit.py::ProductionStateCommitter`。
- Private cohesive lifecycle: `src/ai_video/production/_state_commit_paid_provider.py`。
- Mutable truth: Manifest 2.6 attempt state + active budget pointer。

### Old path to replace

Caller-provided `VoiceCallAuthorization` receipt IDs、`ElevenLabsProviderPolicy.provider_enabled` and `_DurableVoiceSubmitPermit` alone cease to authorize a metered remote transport。They remain readable compatibility evidence for accepted Manifest 2.2-2.5 fixtures and offline fake behavior。

### Unchanged contracts

- P2 reader no-write/no-network；P5 graph immutable；P6/P7 lifecycle preserved。
- Local/default/no-Video-Provider paths do not depend on Gate state。
- Exact replay remains zero transport and zero state advance。

## Exact File Map

### Create

- `src/ai_video/production/paid_provider.py`
- `src/ai_video/production/_state_commit_paid_provider.py`
- `tests/paid_provider_support.py`
- `tests/test_production_paid_provider.py`
- `tests/test_production_paid_provider_state.py`
- `tests/test_production_paid_provider_e2e.py`

### Modify

- `src/ai_video/errors.py`
- `src/ai_video/production/models.py`
- `src/ai_video/production/_lifecycle_schema.py`
- `src/ai_video/production/paths.py`
- `src/ai_video/production/_state_commit_contracts.py`
- `src/ai_video/production/state_commit.py`
- `src/ai_video/production/_state_commit_voice_intent.py`
- `src/ai_video/production/_state_commit_voice_activation.py`
- `src/ai_video/production/_state_commit_recovery_attempts.py`
- `src/ai_video/production/_voice_project_reader.py`
- `src/ai_video/production/project.py`
- `src/ai_video/production/elevenlabs.py`
- `src/ai_video/production/__init__.py`
- focused existing model/state/recovery/audio/ElevenLabs tests
- `AGENTS.md`、README/runtime baseline/roadmap/contract matrix only after executable acceptance

### Do not modify

- the three unrelated dirty P7.1 files listed above
- `src/ai_video/cli.py`、`config.py`、`pipeline.py`、Legacy `manifest.py`
- Registry/composition/timeline/renderer/dependency modules
- P8 provider files
- `.workflow/**`、`runs/**`、credentials or generated live output

## Task 0: Freeze Boundary and Baseline

**Dependencies:** user choice `A`、clean Gate-owned paths、accepted P7/Base E2E/P7.1 offline base。

Record:

- base `main@4b93681f2632b854630821f5f1b71ffc53484778`；
- Manifest base `2.5`、Registry base `2.1`；
- Gate Manifest `2.6`、P8 future Manifest `2.7` / Registry `2.2`；
- exact dirty-file avoidance list；
- no live/network/secret/charge authority。

Focused baseline:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_models.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_audio.py \
  tests/test_production_elevenlabs.py \
  tests/test_production_voice_captions_e2e.py -q
```

**Acceptance:** known explainable base；Gate-owned files unmodified；baseline GREEN or exact blocker recorded。

## Task 1: Pure Safety Contracts — Strict RED/GREEN

**Create:** `paid_provider.py`、`test_production_paid_provider.py`。

Implement:

- `SecretReference`
- `PaidProviderEgressItem`
- `PaidProviderCallPreview.create(...)`
- `PaidProviderAuthorizationDecision.create(...)`
- `PaidProviderBudgetReservation`
- `PaidProviderBudgetSnapshot.create(...)`
- `PaidProviderGateReceipt.create(...)`
- `PaidProviderSubmitReceipt.create(...)`
- `DurablePaidProviderSubmitPermit` nominal Protocol
- `ScriptedFakePaidProviderTransport` in test support only

RED cases first:

- float/negative/unbounded/mixed-currency money rejected；
- preview changes for provider/model/request/destination/payload/upper bound；
- raw payload or secret-bearing fields rejected；
- authorization must bind exact preview/attempt/actor/expiry/max call count；
- budget sums settled + reserved + unsettled；
- outcome unknown cannot release as zero；
- external effect ID exact round-trip and bounded validation；
- fake transport call count remains zero without a valid permit。

Verification:

```bash
python -m pytest -p no:cacheprovider tests/test_production_paid_provider.py -q
```

## Task 2: Manifest 2.6 and Read-Only Reopen — Strict RED/GREEN

**Modify:** models、lifecycle schema、paths、project/voice reader。

Add:

- `PaidProviderBudgetSnapshotPointer`
- `PaidProviderGateReceiptPointer`
- `PaidProviderSubmitReceiptPointer`
- `PaidProviderAttemptState`
- `ProductionManifest.active_paid_provider_budget`
- canonical content-addressed budget/Gate/submit paths
- Manifest 2.6 validators and compatibility serializers
- reader no-follow/hash/content-identity reopen

Rules:

- paid fields rejected before 2.6；
- paid attempt requires active budget + Gate pointer；
- submit phases require exact submit pointer；
- no duplicate/ambiguous receipt ownership；
- tamper、missing file、symlink、path escape and wrong content hash fail closed。

Verification:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_paid_provider.py \
  tests/test_production_models.py \
  tests/test_production_project.py -q
```

## Task 3: Atomic Reservation, Submit Intent and One-Use Permit — Strict RED/GREEN

**Create/modify:** `_state_commit_paid_provider.py`、contracts、state facade、voice intent、state tests。

Implement committer-owned transition:

1. reopen current operation R+1 and exact request fingerprint；
2. invoke injected trusted authorizer；
3. validate decision against preview/current time；
4. reopen or initialize exact budget snapshot；
5. reject if per-call/project ceiling unavailable；
6. append reservation and write next budget snapshot；
7. write Gate receipt + operation submit intent；
8. atomically replace Manifest 2.6 with exact pointers/state；
9. reopen all evidence；
10. mint one `_DurablePaidProviderSubmitPermit` bound to Manifest revision/file SHA and one-use current-state validator。

Retrofit `ElevenLabsVoiceProvider` to require the shared permit。Historical fake voice flow may keep the old permit only when no concrete metered remote adapter is invoked。

Crash windows cover temp write/fsync/promotion/directory fsync/final replace/reopen。Restart never remints a permit for an existing submit intent。

Verification:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_paid_provider_state.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_elevenlabs.py -q
```

## Task 4: Billable-Effect Receipt, Budget Settlement and Recovery — Strict RED/GREEN

Persist the exact submit result immediately:

- `accepted`: exact effect ID selected, reservation retained；
- `known_no_effect`: terminal typed failure + released reservation + actual zero；
- `outcome_unknown`: terminal outcome unknown + unsettled reservation；
- later settlement records actual usage and releases unused upper bound；
- actual overrun is recorded truthfully、blocks later paid submits and never truncates cost。

Recovery rules:

- submit intent without receipt -> outcome unknown、unsettled、no remint；
- accepted receipt -> exact effect identity remains available to the operation-specific lifecycle；
- mixed budget/Gate/submit tuples fail closed；
- orphan complete evidence preserved/reported, never auto-selected。

Verification:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_paid_provider_state.py \
  tests/test_production_state_recovery.py -q
```

## Task 5: Default-Zero Fake E2E and Old-Path Retirement

Build a deterministic fake/no-network E2E:

```text
voice R+1
 -> exact paid preview
 -> fake trusted authorizer
 -> budget reservation + Gate receipt + submit intent
 -> one-use shared permit
 -> scripted fake transport returns exact effect ID
 -> durable submit receipt
 -> settlement
 -> restart reopens exact evidence
 -> replay call count stays zero
```

Tests prove:

- arbitrary budget/egress IDs and provider-enabled booleans cannot invoke ElevenLabs transport；
- credential presence alone cannot authorize；
- malformed/expired/reused receipt yields zero calls；
- secret marker absent from `str`/`repr`/durable JSON；
- no P8/video/Registry/renderer behavior appears。

Verification:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_paid_provider_e2e.py \
  tests/test_production_audio.py \
  tests/test_production_elevenlabs.py \
  tests/test_production_voice_captions_e2e.py -q
```

## Task 6: Independent Review, Full Gate and Runtime Truth

Run:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_paid_provider.py \
  tests/test_production_paid_provider_state.py \
  tests/test_production_paid_provider_e2e.py \
  tests/test_production_models.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_audio.py \
  tests/test_production_elevenlabs.py \
  tests/test_production_voice_captions_e2e.py \
  tests/test_production_image.py \
  tests/test_production_image_e2e.py \
  tests/test_production_base_ai_comic_e2e.py -q
python -m pytest -p no:cacheprovider -q
python -m scripts.architecture_gate check
```

Independent native reviewer must return `accept` with no blocking issue after checking budget arithmetic、authorization binding、secret surfaces、crash windows、exact replay、old-path retirement and P8 boundary。

Only after GREEN/review:

- update `AGENTS.md`、README、contract matrix、runtime baseline and roadmap from runtime truth；
- mark Paid Provider Gate accepted；
- update P8 Task 0 exact base and choose Manifest 2.7 / Registry 2.2；
- commit only Gate-owned files with explicit `git add <files>`。

## Acceptance Criteria

- all seven roadmap requirements have executable evidence；
- Manifest 2.6 is the sole mutable owner；
- no ambient live authority or caller-only boolean/ID bypass；
- no duplicate P8 task ID or lifecycle；
- default submit count/network/secret/charge are zero；
- existing contracts/tests remain GREEN；
- reviewer has no blocker；
- unrelated P7.1 dirty work remains untouched；
- checkpoint commit exists before returning to P8 Task 0。

## Rollback

Disable the new metered submit entrypoint and adapter integration while retaining Manifest 2.6 reader/recovery and immutable budget/Gate/submit evidence。No schema downgrade、history rewrite、reservation deletion or remote fallback。
