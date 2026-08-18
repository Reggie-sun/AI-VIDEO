# AI-VIDEO P8 Seedance Cloud Provider Implementation Plan

Status: Conditional plan. The 2026-08-19 official compatibility matrix triggered the user-defined provider-neutral scope-expansion stop gate. Tasks after Task 1 are not authorized until that core extension is explicitly approved.

**Spec:** `docs/superpowers/specs/2026-08-19-ai-video-p8-seedance-cloud-provider.md`

## Goal

在不污染 Seedance-specific fields 到 Production schema 的前提下，以一个 deletable `SeedanceVideoProvider`、strict typed profile 和 declarative variants 覆盖执行日全部 included Seedance Model IDs，并复用 P8 Paid Provider Gate 与 stepwise submit/poll/fetch。

## Problem Boundary

- Single runtime owner: future `src/ai_video/production/seedance.py` owns Ark mapping/transport only.
- Durable owner remains `ProductionStateCommitter`.
- Provider-neutral request/capability owner remains `src/ai_video/production/video.py`.
- Old path to remove: none; no existing Seedance runtime adapter exists.
- Unchanged boundary: fetched candidate only. No Registry/Project/Graph activation, renderer MP4 support, CLI, schema writer, automatic selection or fallback.
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

**Status:** complete; blocker found.

The current P8 core lacks `last_frame`, reference video/audio, reference/edit/extend modes, adaptive dimensions, `duration=-1`/frames/fractional timing, and `mov`. These are semantic request/output capabilities. Hiding them in provider profile data would bypass capability resolution and exact request identity.

**Decision:** stop before runtime implementation. Request explicit authorization for a separate backward-compatible P8 core contract extension.

## Task 2: Extend P8 Core Contracts

**Status:** blocked; not authorized by this plan.

If separately authorized, first write a dedicated core-extension spec/plan and use strict red-green tests. The minimal candidate scope is:

- extend provider-neutral input bindings to typed image/video/audio references and exact roles;
- extend generation modes for reference/edit/extend without Seedance names;
- represent exact dimensions versus provider-adaptive output;
- represent integer duration, model-selected duration or explicit frame count without weakening existing invariants;
- add an accepted container set that can represent `mov` while keeping existing MP4 requests unchanged;
- keep canonical hashes backward compatible and update Fake/H3/Hailuo contract tests.

If this work requires Manifest/schema/activation/renderer changes, stop again; those remain out of scope.

## Task 3: Implement Offline Seedance Adapter

**Status:** blocked on Task 2.

**Create:**

- `src/ai_video/production/seedance.py`
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

Focused verification:

```bash
.venv/bin/python -m pytest -q \
  tests/test_production_seedance.py \
  tests/test_production_video.py \
  tests/test_production_paid_provider.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_state_recovery.py
```

The exact existing test filenames must be rechecked at execution time; no command in this conditional task is evidence of a current pass.

## Task 4: Harness Mapping

**Status:** blocked on Task 3.

Modify `.agent/harness/policy.yaml` so `src/ai_video/production/seedance.py` and `tests/test_production_seedance.py` map to `production_video_provider_tests`, add the Seedance test command to that check, and update `tests/test_agent_harness.py` with fail-safe mapping assertions.

Do not broaden unrelated categories or refresh Architecture Gate baselines.

## Task 5: Independent Safety Review

**Status:** blocked on Task 3.

Use a native named `reviewer` after core/safety behavior exists. Required verdict covers permit adjacency, POST non-retry, outcome-unknown recovery, task binding, redirect/origin/size/container checks, exact allowlist coverage and secret/raw-response non-persistence.

Parent verifies every blocking claim and owns the final diff.

## Task 6: Runtime Truth Documentation

**Status:** blocked on verified Tasks 3–5.

Only after executable acceptance, update:

- `docs/agent-primary-contract-matrix.md`
- `docs/v0.2-runtime-baseline.md`
- `docs/v0.2-agentic-production-roadmap.md`
- `README.md`

State offline adapter acceptance and exact capability coverage. Do not claim Registry/Project/Graph activation, renderer support or cloud-live connectivity.

## Task 7: Harness Receipt and Commit

**Status:** blocked on implementation.

Parent stages only task-owned files with explicit paths, generates a fresh staged-snapshot Harness receipt, commits a stable checkpoint, then generates and validates a commit-range receipt for the exact commit. Architecture Gate must pass. Unrelated dirty files remain unstaged and untouched.

## Live Gate

Live is not part of this plan. A future single submit requires all of:

- rotated `ARK_API_KEY` injected through process environment or secret store;
- exact account Model/Endpoint access;
- current dated pricing snapshot and finite one-call budget;
- input egress authorization;
- explicit authorization for exactly one paid submit.

Without a real succeeded task and validated fetched artifact, delivery must say offline-only and cloud live unverified.
