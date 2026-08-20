# AI-VIDEO P8 Seedance Cloud Provider Implementation Plan

Status: Offline implementation accepted on 2026-08-19. A separately authorized Mini diagnostic later reached provider `succeeded` and fetched an MP4. The follow-up tracked payload correction is offline-verified but not live re-submitted; billing settlement、candidate activation、push和release均未完成。2026-08-20新增的synthetic/illustrated inline PNG lane已完成offline runtime和fake-transport验证；没有对应live authorization、remote submit或activation。

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

The 2026-08-19 authorized diagnostic satisfied the gate for one Mini submit only. It used one POST, reached `succeeded`, fetched a 1,278,577-byte H.264 MP4 and did not retry. The diagnostic omitted all optional/default fields and therefore also omitted `generate_audio`; Ark returned an AAC stream, so that run does not verify the tracked `generate_audio:false` correction. The durable reservation remains unsettled and no activation was attempted.

Every future single submit still requires all of:

- rotated `ARK_API_KEY` injected through process environment or secret store;
- exact account Model/Endpoint access;
- current dated pricing snapshot and finite one-call budget;
- input egress authorization;
- explicit authorization for exactly one paid submit.

Without a fresh authorization and an exact successful request matching the tracked payload, delivery must distinguish diagnostic cloud connectivity from production-payload live acceptance.

## Task 8: Live-Evidence Payload Correction

**Status:** implementation and focused offline verification complete; independent review、Harness、commit and exact live re-verification remain pending.

The live sequence progressed from credential failure to account-route failure, then `HTTP 400` with the original default-heavy payload. A single authorized diagnostic using only `model`、`content`、`resolution`、`ratio` and `duration` was accepted and fetched successfully. The production correction therefore:

- always emits `generate_audio` to preserve the resolved `native_audio` contract;
- omits `watermark=false`、`return_last_frame=false`、`service_tier=default`、`output_format=mp4` and `priority=0`;
- continues to emit each non-default field;
- changes no provider-neutral contract、schema、CLI、writer、resolver、renderer or fallback behavior.

The regression test was observed RED against the original payload and GREEN after the minimal adapter change. Focused Seedance/Paid Provider/recovery verification is `108 passed`.

## Task 9: Trusted Ark Asset Identity Import

**Status:** implementation and focused offline verification complete on 2026-08-20; no remote Asset API or video submit was executed.

The missing production owner for already-materialized Ark identities is now `src/ai_video/production/seedance_asset.py`. `SeedanceAssetMaterializationReceipt` seals a human-observed Ark Console `Active` asset, its confirmation-evidence SHA-256, materialization scope and rights note against one exact local asset ID/SHA-256/MIME/size. `SeedanceAssetReferenceResolver` rejects missing, ambiguous, tampered or mismatched receipts and emits only a real `asset://asset-...` URI. `SeedanceVideoProvider` additionally rejects a local Registry ID masquerading as an Ark URI before permit consumption/network.

This task does not automate Ark Console enrollment, add Assets API/AK/SK support, change Manifest/CLI/layout, or claim that the Alice keyframe already has a provider asset. The representative Seedance lane remains zero-submit until the human-controlled Ark materialization and exact receipt evidence exist.

## Task 10: Synthetic / Illustrated Inline Image Lane

**Status:** offline implemented and verified；not authorized for remote execution、live proof or activation.

### Contract Decision

Current official `CreateContentsGenerationsTasks` documentation proves that `content.image_url.url` accepts a public URL、inline `data:image/<format>;base64,...` or `asset://<ASSET_ID>` for the Seedance 2.0 family, including Mini. The first AI-VIDEO transport slice selects inline Base64 with `image/png` only because it can be derived and independently measured from exact local bytes through the existing PNG seam without inventing an uploader、decoder or persisted remote URL. Other officially accepted image formats remain a future measured-input extension, not an implicit transcode. Public HTTPS remains deferred until a separately approved publisher/materializer contract can prove origin、immutability、read-back identity、retention and expiry. General Files API、CreateAsset automation and implicit fallback remain excluded. The lane remains fail closed unless the exact synthetic receipt is bound through the authorization and operation permit as specified below.

The existing trusted owner is unchanged:

```text
real person / protected or ambiguous identity
  -> SeedanceAssetMaterializationReceipt
  -> SeedanceAssetReferenceResolver
  -> asset://<ASSET_ID>
```

The additive implemented lane is:

```text
attested illustrated/anime/non-real or ordinary non-character asset
  -> SeedanceSyntheticImageReferenceReceipt
  -> SeedanceSyntheticImageEgressPolicyReceipt (canonical ordered aggregate)
  -> SeedanceSyntheticImageReferenceResolver
  -> in-memory data:image/...;base64,...
```

`synthetic_photorealistic_person` remains ineligible for this V1 lane and must use an authorized trusted asset or stop. Classification must come from sealed source/tool/rights provenance plus task-scoped human attestation; Agent vision is advisory only.

### Problem Boundary and Ownership

- Source owner: `src/ai_video/production/seedance_asset.py` owns the per-image immutable receipt、request-level immutable aggregate egress-policy receipt、read-only authorizer wrapper and exact-byte inline resolver. It does not write Manifest/Registry state or upload bytes.
- Adapter translation owner: `src/ai_video/production/seedance.py` accepts only the exact trusted resolver or exact synthetic resolver and emits the selected payload after validation. It must not accept an arbitrary caller callable as a bypass.
- Shared permit-binding owners: `src/ai_video/production/_state_commit_paid_provider.py` mints and durability-checks the exact Gate permit; `src/ai_video/production/_state_commit_contracts.py` validates/consumes it; `src/ai_video/production/video.py` projects the exact video binding. Their bounded change is only to carry the already sealed `authorization_fingerprint`; shared voice/video behavior outside that identity strengthening remains unchanged.
- Focused test owner: `tests/test_production_seedance.py`.
- Shared permit regression owners: `tests/test_production_paid_provider_state.py`、`tests/test_production_video.py` and `tests/test_production_video_state_recovery.py`; compatibility checks remain in `tests/test_production_elevenlabs.py` and `tests/test_production_minimax_speech.py`. Do not create a parallel Gate implementation.
- Old path to remove: none. Existing `SeedanceAssetMaterializationReceipt` / `SeedanceAssetReferenceResolver` behavior and tests remain unchanged.
- Schema/layout migration: none. No new writer、Manifest lifecycle、CLI、timeline、renderer、Provider selector or automatic fallback.
- Evidence binding: `SeedanceSyntheticImageEgressPolicyReceipt` canonically binds the ordered tuple of every `(role, asset_id, SeedanceSyntheticImageReferenceReceipt.content_hash)` plus prompt/preview、task、Provider/model/mode、transport、destination and retention. Its exact ID is `seedance-synthetic-egress:<lowercase-64-hex-content_hash>` and each child ID is `seedance-synthetic-image:<lowercase-64-hex-content_hash>`. A caller-injected read-only source returns their exact canonical bytes; `SeedanceSyntheticImageAuthorizer` and the resolver independently reopen and verify the same aggregate/children 1:1. `input_artifact_ids` remains graph-only and unchanged.
- Permit binding: add the existing `authorization_fingerprint` to mint-time binding、`build_video_paid_permit_binding()`、operation permit validate/consume/consumed paths and durability reopen comparison. This pins the submit-time authorization to the authorization persisted in the exact `PaidProviderGateReceipt` without a persisted schema/layout change.
- Approved scope expansion (`2026-08-20`): use an injected read-only canonical evidence source plus injected canonical Registry snapshot bytes. The external source owns durable retention; AI-VIDEO only reads by exact ID and adds no persisted schema/layout/writer. Missing source bytes、Registry semantic/file identity or exact Asset Record fails closed.

### RED 0: Authorization and Permit Identity

Add focused failing contract tests before production code:

- a bare receipt/content hash in `input_artifact_ids` is not accepted as evidence and cannot produce a dangling generated-asset dependency;
- same preview plus durable Gate authorization `A1/R1` and submit-time authorization `A2/R2` fails before POST and leaves the permit unconsumed;
- changing any child receipt、role、asset ID、canonical order or preview/egress setting changes the aggregate `egress_policy_receipt_id` and sealed authorization fingerprint;
- missing or unreopenable egress-policy receipt bytes fail before permit/network;
- the ordered child receipts、aggregate authorization evidence、Paid Provider Gate and consumed permit form one exact chain;
- missing、extra、mismatched or duplicate receipts relative to image bindings fail before egress/permit/network.

### GREEN 0: Minimal Shared Permit Strengthening

Implement only the internal identity projection needed to carry `authorization_fingerprint` through permit mint、durability and the video operation's validation/consumption binding. Reopen the exact Gate and compare its sealed authorization fingerprint. `build_video_paid_permit_binding()` supplies the submit-time fingerprint; existing voice permit callers retain their current operation binding and receive no synthetic-input semantics. Do not add a second permit type、writer、Manifest field、artifact layout or Provider-specific branch in the shared committer, and prove the existing voice providers remain compatible.

### RED 1: Classification, Provenance and Identity

After the binding gate is approved, add failing tests before production code for:

- all four exact classes: real/protected、synthetic photorealistic、clearly illustrated/anime/non-real、ordinary non-character；only the final two may enter the inline lane;
- missing human attestor、task scope、creator/source/tool identity、rights statement、Registry revision、SHA-256、MIME、size or geometry fails closed;
- ambiguous/suspected real-person likeness、unknown source or protected identity fails before egress/permit/network and cannot auto-downgrade;
- receipt content hash or any local selected bytes/metadata mismatch fails closed;
- changing classification/provenance/attestation identity changes the child receipt、aggregate egress-policy receipt and authorization fingerprint bound to the Gate/permit;
- missing、extra、mismatched or duplicate receipt-to-image-binding mappings fail closed 1:1.

Run and preserve the RED evidence:

```bash
PYTHONPATH=src python -m pytest -p no:cacheprovider \
  tests/test_production_seedance.py -q
```

### GREEN 1: Minimal Immutable Receipt and Resolver

Implement only enough in `seedance_asset.py` to make the RED cases pass:

- strict/frozen `SeedanceSyntheticImageReferenceReceipt` with exact local identity、provenance、rights、classification and human/task attestation;
- strict/frozen `SeedanceSyntheticImageEgressPolicyReceipt` with canonical ordered role/asset/child bindings plus exact preview/task/Provider/transport/retention identity;
- `SeedanceSyntheticImageReferenceResolver` that re-reads injected exact PNG bytes、independently measures SHA-256/size/`image/png` MIME/geometry、enforces the per-image `<30 MB` bound, and constructs the data URI in memory;
- raw Base64/body、secret or input bytes never enter durable receipts、Manifest、Registry、logs、errors、repr or fixtures;
- no file/network I/O hidden inside model validation and no upload/materialization behavior.

### RED 2: Payload, Egress, Permit and Failure Semantics

Add failing fake-transport tests proving:

- the request and Paid Provider egress preview bind each image's exact asset ID、SHA-256、MIME and size, while the exact authorization、durable Gate and permit separately bind the matching aggregate synthetic receipt; receipt hashes never enter `input_artifact_ids`;
- protected/ambiguous input、tampered bytes or invalid data-URI MIME produce zero Provider POST and leave the submit permit unconsumed;
- exact `29_999_999` / `30_000_000` per-image boundaries prove strict `<30_000_000` eligibility; compact two-image Base64-shaped JSON bodies cover exact `63_999_999`、`64_000_000` and `64_000_001` byte boundaries, while fake-transport payload tests prove that real adapter serialization passes through the same guard before permit consumption. Multi-image eligibility is determined only from the actual aggregate body, never inferred from per-image sizes;
- payload uses the official `image_url.url` data URI and preserves `role` plus `generate_audio=false` without logging/persisting the Base64;
- existing trusted `asset://` payload remains byte-for-byte compatible and no generic resolver callable can bypass either exact resolver;
- known provider rejection records the existing known failure; transport ambiguity after permit consumption remains `outcome_unknown` with no retry、fallback or permit remint.

### GREEN 2: Minimal Adapter Union

After GREEN 0, modify only `seedance.py`、`seedance_asset.py` and the focused test file for the Provider-specific slice. Before permit issuance, the authorizer independently reopens and validates the exact aggregate/children. Before permit consumption, the adapter accepts the explicit synthetic resolver, revalidates aggregate/children 1:1 and requires the supplied authorization's aggregate receipt ID; it then constructs the final compact JSON body, rejects `len(body) > 64_000_000`, and consumes the one-use permit immediately adjacent to the sole POST. Existing trusted `asset://` resolver behavior remains unchanged. V1 requests must not mix trusted `asset://` and inline Base64 resolvers; mixed transport remains a separate contract decision. Do not add HTTPS、Files API、CreateAsset、AK/SK、uploader、Provider fallback or new profile selection.

### Offline Verification and Independent Review

After all RED/GREEN cycles, run:

```bash
PYTHONPATH=src python -m pytest -p no:cacheprovider \
  tests/test_production_seedance.py \
  tests/test_production_video.py \
  tests/test_production_paid_provider.py \
  tests/test_production_paid_provider_state.py \
  tests/test_production_elevenlabs.py \
  tests/test_production_minimax_speech.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_state_recovery.py -q
```

Use native named `reviewer` for the final safety/contract review. Required verdict covers classification authority、provenance identity、raw Base64 non-persistence、exact egress preview、trusted-path compatibility、permit adjacency、known rejection、outcome-unknown and absence of uploader/fallback paths. Parent verifies every blocking claim and reviews the final diff.

Inspect exact changed paths against `.agent/harness/policy.yaml`; existing owned source/tests should route to `production_video_provider_tests` plus task Architecture Gate. Update Harness mapping only if the actual implementation adds an otherwise unmapped owned path. Stage exact task files, run `make harness-verify`, validate the fresh receipt with `make harness-receipt RECEIPT=<path>`, and create a task-only checkpoint.

### Separate Live Gate

Docs approval、offline fake transport and a passing Harness do not authorize any remote call. A future live proof requires a new task-scoped authorization、current exact model/profile/pricing、finite budget、prompt/image egress approval、rotated injected `ARK_API_KEY` and one-use permit. It must use one already accepted illustrated/anime or ordinary non-character asset, one bounded submit, measured fetch/activation/recovery and zero-effect replay. It must not reuse the earlier diagnostic、Alice photorealistic keyframe or another lane's authorization.
