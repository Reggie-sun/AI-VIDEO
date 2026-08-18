# AI-VIDEO Paid Provider Gate Specification

Status: Approved for offline implementation on local `main` by the user's 2026-08-18 choice `A`. This authorization covers deterministic fake/no-network implementation and acceptance only. It does not authorize a real Provider call, credential use, quota consumption, charge, push, release, or publish.

## 1. Goal

在 P8 runtime implementation 之前建立一个 provider-neutral、durable、fail-closed 的 Paid Provider Gate。任何新的 remote metered submit 必须先有 exact request preview、explicit opt-in、有限预算上界与 reservation、egress authorization、non-secret credential reference、per-attempt live authorization、durable submit intent 和 one-use committer permit。

Gate 只决定“一次 exact paid submit 是否可以发生”以及其 billable-effect/cost-risk truth。它不拥有 Video request resolution、polling、download、media validation、Registry activation 或 renderer behavior。

## 2. Current Gap

P4 voice contracts提供了可复用 pattern，但不是完整 Gate：

- `VoiceCallAuthorization` 只保存 caller-provided budget/egress receipt IDs，没有 reopen 并验证真实 reservation 或 egress receipt；
- `ElevenLabsProviderPolicy.provider_enabled` 是 caller-provided boolean；
- `_DurableVoiceSubmitPermit` 绑定 durable voice submit intent，但不绑定 provider-neutral budget ledger、exact egress manifest、explicit actor opt-in 或 live authorization；
- 当前没有 Manifest-selected aggregate reservation ledger；
- 当前没有 provider-neutral billable-effect receipt。

因此现有 P4 IDs 和 booleans只能继续作为 Manifest 2.2-2.5 compatibility evidence，不能授权新的 remote metered submit。

## 3. Problem Boundary

### Single owner

- Pure safety contract owner: `src/ai_video/production/paid_provider.py`。
- Durable mutation/recovery owner: existing `ProductionStateCommitter` façade plus private `src/ai_video/production/_state_commit_paid_provider.py` implementation。
- Mutable truth owner: Production Manifest `2.6`。
- Aggregate budget truth owner: Manifest-selected immutable `PaidProviderBudgetSnapshot`。

### Old path to retire

- `VoiceCallAuthorization` receipt ID strings and `ElevenLabsProviderPolicy.provider_enabled` alone no longer authorize `ElevenLabsVoiceProvider` transport.
- `_DurableVoiceSubmitPermit` remains readable/testable for historical offline P4 behavior but cannot authorize a new metered remote adapter call.
- New metered adapters accept only the shared committer-issued `DurablePaidProviderSubmitPermit` nominal interface.

### Unchanged contracts

- Manifest `2.0`-`2.5` remain readable and byte-compatible; no bulk migration or downgrade。
- Registry remains `2.1`; this Gate does not register assets or change egress metadata schema。
- `ProductionStateCommitter` remains the only writer/recovery owner。
- P2 reader remains read-only/no-network and must reopen exact Manifest-selected Gate evidence。
- No CLI、Legacy Manifest/layout、Pipeline、Composition、ResolvedTimeline、renderer、dependency resolver、P8 video task or Provider implementation changes。
- Default tests remain deterministic fake/no-network/no-secret/no-charge。

## 4. Version Contract

Paid Provider Gate consumes the next Manifest minor version:

- `PAID_PROVIDER_MANIFEST_SCHEMA = "2.6"`；
- Registry stays `2.1`；
- P8 Task 0 must therefore select Manifest `2.7` and Registry `2.2` from the accepted Gate base。

Manifest `2.6` adds:

- `active_paid_provider_budget: PaidProviderBudgetSnapshotPointer | None`；
- `StateCommitAttempt.paid_provider_state: PaidProviderAttemptState | None`。

Any explicit paid-provider field is rejected before Manifest `2.6`。Manifest `2.6` with a paid attempt must select an exact budget snapshot and content-addressed Gate receipt。Unreferenced JSON is orphan evidence and never runtime truth。

## 5. Pure Gate Contracts

### `PaidProviderCallPreview`

Self-sealed immutable preview binding:

- exact `attempt_id`、operation、provider kind/model and operation request fingerprint；
- `billing_mode="remote_metered"`；
- currency and finite non-negative `estimated_cost_upper_bound_microunits`；
- canonical HTTPS destination and exact method；
- ordered `PaidProviderEgressItem` manifest containing only identity/hash/size/MIME/purpose, never raw payload bytes or text；
- retention and provider-policy snapshot identities；
- `SecretReference` containing only `environment | secret_store` plus a sanitized reference ID；
- preview fingerprint。

Binary float is forbidden for persisted money. V1 uses integer microunits in one exact ISO-4217 currency。

### `PaidProviderAuthorizationDecision`

Immutable trusted-authorizer result binding the exact preview:

- explicit opt-in actor and policy receipt；
- project budget policy ID/currency/total ceiling and per-call ceiling；
- exact egress authorization actor/policy/preview fingerprint；
- exact per-attempt live-test authorization actor、issued/expires time and `max_submit_count=1`；
- authorization fingerprint。

Authorization is per attempt and per preview. There is no global/process-wide mutable live switch。Expired、wrong-actor、wrong-preview、wrong-destination or reused authorization fails closed。

### `PaidProviderBudgetSnapshot`

Immutable content-addressed aggregate ledger containing:

- policy identity、currency、project ceiling and revision；
- append-only reservation entries；
- each reservation's attempt/request/preview identity、reserved upper bound、actual cost if known and `reserved | settled | released | unsettled` state；
- blocked flag when actual cost exceeds a reservation or project ceiling；
- semantic content hash。

Before reservation, the committer sums settled cost plus every `reserved` or `unsettled` amount。Insufficient budget rejects before submit count can increase。`outcome_unknown` remains `unsettled` and cannot be released as zero。A known-no-effect receipt may release with actual zero。Actual cost is never truncated to the reservation。

V1 budget scope is project-total plus per-call ceiling。Run/Take accounting is out of scope because those domains are not accepted v0.2 runtime truth。

### `PaidProviderGateReceipt`

Content-addressed immutable receipt combining the exact preview、authorization decision and reservation identity。It contains no secret、header、cookie、signed URL、raw provider response or raw payload。

### `PaidProviderSubmitReceipt`

Content-addressed billable-effect receipt with exactly one outcome:

- `accepted`: exact opaque external billable-effect/job ID is durable and reservation remains held until settlement；
- `known_no_effect`: Provider definitively created no billable effect and reservation may release with actual zero；
- `outcome_unknown`: acceptance cannot be determined, no blind retry is allowed and reservation becomes `unsettled`。

Opaque external IDs have bounded strict validation and round-trip exactly；they are not truncated、normalized or replaced with a display hash。Logs may derive a separate redacted display identity。

## 6. Durable Lifecycle

```text
operation R+1 request
  -> build exact PaidProviderCallPreview
  -> trusted authorizer returns exact decision
  -> committer reserves budget + writes Gate receipt + writes submit intent
  -> final Manifest 2.6 replace
  -> reopen exact Manifest/budget/Gate/intent evidence
  -> mint one process-local DurablePaidProviderSubmitPermit
  -> consume permit once at transport boundary
  -> persist PaidProviderSubmitReceipt immediately
       accepted        -> keep reservation held; operation continues
       known_no_effect -> release reservation; terminal typed failure
       outcome_unknown -> unsettled reservation; terminal outcome_unknown
  -> later settle actual usage without rewriting history
```

The permit is not authorization by itself。It is a non-serializable one-use capability bound to exact attempt、preview、Gate fingerprint、reservation、Manifest revision/file SHA and a current-state validator。Restart never remints a permit for `submit_intent` or `outcome_unknown`。

Crash after transport side effect but before durable submit receipt converges to `outcome_unknown`。Crash after accepted receipt persists exact effect identity。P8 later uses that identity for provider status/poll/fetch and must not store a second task-ID copy。

## 7. Gate / P8 Ownership Boundary

Gate owns:

- explicit opt-in；
- finite upper bound and aggregate reservation ledger；
- egress preview/authorization；
- non-secret credential references and failure redaction；
- exact per-attempt live authorization；
- durable submit intent、one-use permit and billable-effect receipt；
- reserved/settled/released/unsettled cost risk。

P8 owns:

- `VideoGenerationRequest` and request/resolved generation hashes；
- capability resolution；
- submitted/polling/provider terminal status history；
- deadlines、resume actions、fetch and MP4 validation；
- generated-video provenance、Registry/Project/Graph candidate and activation。

P8 references the Gate-owned external effect identity. It does not duplicate task identity or budget state。

## 8. Secret and Error Contract

- `SecretReference` stores only kind and sanitized reference ID；it never reads environment or secret-store values。
- Secrets are injected only at the concrete transport boundary。
- Runtime models、Manifest、receipts、fixtures and logs reject Authorization headers、cookies、signed URLs and raw response payloads。
- Provider errors are mapped to fixed typed `AiVideoError` messages；raw exception text is never persisted or returned when it may contain credentials。
- `repr()` / Pydantic validation errors hide model inputs。

## 9. Fake and Live-Test Contract

- `ScriptedFakePaidProviderTransport` is deterministic、no-network and exposes exact call counters。
- Missing/mismatched/expired/reused authorization or permit produces zero submit calls。
- Default `pytest` cannot enable live behavior through credential presence。
- A future live harness requires a separately authorized exact attempt receipt plus an explicit test option/env arm and a one-call cap。This slice creates only the immutable authorization contract; it does not add or run a live test。

## 10. Acceptance

The Gate is accepted only when executable evidence proves:

- exact opt-in/preview/egress/live authorization binding；
- finite same-currency upper-bound reservation and aggregate accounting；
- reservation retained for `outcome_unknown` and released only for known no effect；
- exact billable-effect ID durability and tamper rejection；
- one-use attempt-bound permit and zero-call rejection paths；
- crash/restart never remints or blind resubmits；
- secret/raw-response redaction；
- Manifest `2.0`-`2.5` compatibility；
- P2 reader reopens Manifest `2.6` Gate evidence without writes or network；
- existing voice/image/Base E2E behavior remains GREEN；
- independent reviewer returns `accept` with no blocking issue；
- no real Provider、network、secret、quota or charge occurred。

## 11. Rollback

Rollback disables/removes the new metered submit entrypoint and concrete adapter integration while preserving Manifest `2.6` reader/recovery compatibility and immutable Gate/budget/submit receipts。No schema downgrade、receipt deletion、reservation erasure or remote fallback is allowed。
