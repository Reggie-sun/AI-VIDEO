# AI-VIDEO P8 Seedance Cloud Provider Implementation Plan

Status: Offline implementation accepted on 2026-08-19. Provider-neutral extension、Seedance adapter、Harness mapping、focused/recovery verification和native review均完成；live submit未授权、未运行。

**Spec:** `docs/superpowers/specs/2026-08-19-ai-video-p8-seedance-cloud-provider.md`

## Goal

在不污染 Seedance-specific fields 到 Production schema 的前提下，以一个 deletable `SeedanceVideoProvider`、strict typed profile 和 declarative variants 覆盖执行日全部 included Seedance Model IDs，并复用 P8 Paid Provider Gate 与 stepwise submit/poll/fetch。

## Problem Boundary

- Single runtime owner: `src/ai_video/production/seedance.py` owns Ark mapping/transport only; `seedance_capabilities.py` and `seedance_profile.py` hold declarative matrix/profile data.
- Durable owner remains `ProductionStateCommitter`.
- Provider-neutral request/capability owner remains `src/ai_video/production/video.py`.
- Old path to remove: none; no existing Seedance runtime adapter exists.
- Unchanged boundary: Seedance adapter ownership止于provider lifecycle与fetched candidate；它不自行执行Registry/Project/Graph activation或render。Provider-neutral activation仍由P8 core/`ProductionStateCommitter`独占，MP4 consumption则由独立且已验收的`1362687` compatibility slice提供。无CLI、schema writer、automatic selection或fallback。
- Credential reference is exactly `ARK_API_KEY`, supplied through an injected credential supplier.
- Default verification is fake transport, zero network and zero cost.

## Task 0: Freeze Official Evidence

**Status:** complete.

**Files:**

- Create `docs/superpowers/specs/2026-08-19-ai-video-p8-seedance-cloud-provider.md`.
- Create this plan.

**Acceptance:**

- Matrix includes every current/legacy-but-callable Model ID and excludes terminated/alias IDs.
- Matrix covers Model/Endpoint identity, modes, duration/frames, resolution/ratio, audio, seed, watermark, draft, service tier, input limits, pricing and status semantics.
- Unknown or account-only facts are explicit fail-closed gates, not guessed constants.

**Verification:**

```bash
git add \
  docs/superpowers/specs/2026-08-19-ai-video-p8-seedance-cloud-provider.md \
  docs/superpowers/plans/2026-08-19-ai-video-p8-seedance-cloud-provider.md
git diff --cached --check
```

## Task 1: Evaluate Provider-Neutral Coverage

**Status:** complete; blocker found and reported.

The current P8 core lacked `last_frame`, reference video/audio, reference/edit/extend modes, adaptive dimensions, provider-selected duration/frames, and `mov`. These are semantic request/output capabilities. Hiding them in provider profile data would bypass capability resolution and exact request identity.

**Decision:** implementation stopped at this gate. The user then explicitly authorized the backward-compatible P8 core contract extension.

## Task 2: Extend P8 Core Contracts

**Status:** complete under the user's explicit follow-up authorization.

The implemented minimal scope is:

- extend provider-neutral input bindings to typed image/video/audio references and exact roles;
- extend generation modes for reference/edit/extend without Seedance names;
- represent exact dimensions versus provider-adaptive output;
- represent integer duration, model-selected duration or explicit frame count without weakening existing invariants;
- add an accepted container set that can represent `mov` while keeping existing MP4 requests unchanged;
- keep legacy request/resolved canonical hashes backward compatible and update Fake/H3/Hailuo contract tests.

Implementation files are `src/ai_video/production/video.py` and the distinct provider-neutral contract module `src/ai_video/production/video_contracts.py`. No Manifest/schema/activation/renderer change was needed.

If this work requires Manifest/schema/activation/renderer changes, stop again; those remain out of scope.

## Task 3: Implement Offline Seedance Adapter

**Status:** complete；Tasks 4–7均已完成offline verification、docs、Harness receipt与checkpoint。

**Create:**

- `src/ai_video/production/seedance.py`
- `src/ai_video/production/seedance_capabilities.py`
- `src/ai_video/production/seedance_profile.py`
- `tests/test_production_seedance.py`

**Modify only if required by shared contract coverage:**

- `tests/video_provider_contract.py`

Implementation contracts:

- one adapter, exact Model ID/Endpoint binding, declarative model variants;
- injected `ARK_API_KEY` supplier and injected transport;
- pure resolve/preview, one POST immediately after one-use permit consumption;
- no POST retry; ambiguous outcome becomes `outcome_unknown`;
- same-task poll/fetch; finite status/error normalization;
- short-lived URL redaction, no redirects/cross-origin, size ceiling and MP4/MOV measured validation;
- no raw response or secret-bearing repr/error/fixture;
- fake transport only in default tests.

Focused verification executed in the default no-network/fake-transport environment:

```bash
PYTHONPATH=src python -m pytest -q \
  tests/test_production_seedance.py tests/test_production_video.py \
  tests/test_production_video_fake.py tests/test_production_minimax_h3.py \
  tests/test_production_minimax_hailuo.py tests/test_production_paid_provider.py \
  tests/test_production_paid_provider_state.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_state_recovery.py
```

Current evidence after review fixes: `517 passed in 190.54s` on 2026-08-19. This is offline contract evidence only.

## Task 4: Harness Mapping

**Status:** complete after the other staged task reached its own commit checkpoint.

Modify `.agent/harness/policy.yaml` so all Seedance source/profile/capability files plus `video_contracts.py` and `tests/test_production_seedance.py` map to `production_video_provider_tests`, add the Seedance test command to that check, and update `tests/test_agent_harness.py` with fail-safe mapping assertions.

Do not broaden unrelated categories or refresh Architecture Gate baselines.

## Task 5: Independent Safety Review

**Status:** complete. Native named reviewer final verdict: `accept`, no blocking or non-blocking concerns.

Use a native named `reviewer` after core/safety behavior exists. Required verdict covers permit adjacency, POST non-retry, outcome-unknown recovery, task binding, redirect/origin/size/container checks, exact allowlist coverage and secret/raw-response non-persistence.

Parent verifies every blocking claim and owns the final diff.

## Task 6: Runtime Truth Documentation

**Status:** complete; documents state offline-only runtime truth and preserve activation/live boundaries.

Only after executable acceptance, update:

- `docs/agent-primary-contract-matrix.md`
- `docs/v0.2-runtime-baseline.md`
- `docs/v0.2-agentic-production-roadmap.md`
- `README.md`

State offline adapter acceptance and exact capability coverage. Do not claim that Seedance adapter owns or automatically invokes Registry/Project/Graph activation or rendering；independent MP4 consumption acceptance belongs to `1362687`. Do not claim cloud-live connectivity.

## Task 7: Harness Receipt and Commit

**Status:** complete. Final staged snapshot verification includes `725 passed` plus Architecture Gate PASS；checkpoint为`c54435f feat: add offline Seedance video provider`。Fresh commit-range receipt为`.agent/harness/runs/20260818T180559630328Z/receipt.json`，已通过`make harness-receipt`校验。

Parent stages only task-owned files with explicit paths, generates a fresh staged-snapshot Harness receipt, commits a stable checkpoint, then generates and validates a commit-range receipt for the exact commit. Architecture Gate must pass. Unrelated dirty files remain unstaged and untouched.

## Live Gate

Live is not part of this plan. A future single submit requires all of:

- rotated `ARK_API_KEY` injected through process environment or secret store;
- exact account Model/Endpoint access;
- current dated pricing snapshot and finite one-call budget;
- input egress authorization;
- explicit authorization for exactly one paid submit.

Without a real succeeded task and validated fetched artifact, delivery must say offline-only and cloud live unverified.
