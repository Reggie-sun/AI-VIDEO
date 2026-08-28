---
name: distill-ai-video-learning
description: Use automatically after a stable AI-VIDEO evidence record to distill repeated real experiments into a scoped advisory Learning Claim, require exact user confirmation before adoption, and route confirmed action to the existing Skill, Provider Policy, Preflight, Contract, or Gate owner.
---

# Distill AI-VIDEO Learning

This Skill is the single Development Governance owner for cross-experiment
`Learning Claim` synthesis, user confirmation, and adoption lineage. It turns
verified history into a current, revisable claim without creating a Product
Runtime learning engine or a second Production truth owner.

## Trigger Automatically At Stable Evidence Boundaries

Run this Skill without waiting for a separate user request when
`record-ai-video-session` has created or materially updated a durable record at
a stable checkpoint. Also run it when the user explicitly asks to distill,
learn from, confirm, reject, revise, adopt, or retire a prior Learning Claim.

The automatic evaluation has two valid outcomes:

- `no_candidate`: no claim meets the evidence threshold; do not create a
  placeholder artifact and do not ask for ceremonial confirmation.
- `pending_candidate`: create or update exactly one most-relevant Learning
  Claim under `docs/record_for_agent/learning/<claim-id>.md`, preserve any
  adopted active version, commit an exact candidate checkpoint, then stop
  adoption work and request user confirmation of its exact commit and hash.

Automatic evaluation is advisory work. It does not authorize adoption.

## Reopen Evidence Before Synthesis

1. Use `retrieve-ai-video-memory` with `experience` scope for discovery.
2. Reopen every exact source used by the claim. RAG excerpts and scores are not
   source evidence; RAG score is not evidence confidence.
3. Search the exact topic family in current `docs/record_for_agent/`, eligible
   `runs/*/SUMMARY.md`, Q0 pointers when available, and existing learning claims.
4. Separate current code/contracts, structured Q0 evidence, human-authored
   records, and auto-generated run summaries by authority.
5. Explicitly search for counter evidence, later supersession, held constants,
   confounders, and cases outside the proposed scope.

Do not fabricate missing Q0 fields or infer human acceptance from technical
metrics, tool success, scores, Provider completion, or playback success.

## Candidate Admission Threshold

A new claim is eligible only when at least one condition is true:

- two independent attempts support the same bounded pattern;
- one controlled comparison with multiple arms isolates the relevant variable;
- new exact evidence materially supports, counters, narrows, or reopens an existing claim.

Multiple versions of the same artifact chain are not automatically independent.
If provenance, controls, outcome identity, or counter-evidence coverage is too
weak, return `no_candidate` or update an existing claim to `CONTESTED`; do not
inflate a single anecdote into a general rule.

## Learning Claim Contract

Start from [`templates/learning-claim.md`](templates/learning-claim.md). Every
claim must contain these semantic fields:

- `failure_pattern`
- `hypothesis`
- `supporting_evidence`
- `counter_evidence`
- `scope`
- `exclusions`
- `active_evidence_status` and `pending_evidence_status`
- `recommended_action`
- `adoption_target`
- `pending_approval_status`
- `active_adoption_status` and `pending_adoption_status`

### Writing Language Contract

Generated Learning Claim artifacts use English section titles and Chinese
narrative. Keep `command`, repository `path`, filename, config key, API, schema,
field name, enum, hash, model/Provider identity, and Skill name in their
original form, normally wrapped in backticks when embedded in prose. Do not
translate machine-readable frontmatter keys or enum values. Use English prose
only when it is exact evidence or a necessary technical term; do not produce
English-only narrative by default.

Use categorical evidence state rather than fake numeric confidence:

- `SINGLE_CASE`: useful observation that cannot support a new adoption proposal;
- `SUPPORTED`: admitted evidence supports the bounded claim;
- `CONTESTED`: material support and counter evidence remain unresolved;
- `REFUTED`: current evidence rejects the claim;
- `RETIRED`: a previously useful claim is no longer current.

`NONE` is allowed only as the sentinel for an empty
`active_claim_version: 0` lane. It is forbidden for any real active or pending
claim version.

Keep active and pending lanes, approval, and adoption independent:

```text
active_adoption_status: NOT_ADOPTED | ADOPTED | RETIRED
pending_approval_status: PENDING_CONFIRMATION | CONFIRMED | REJECTED
pending_adoption_status: NOT_ADOPTED | APPLYING
```

`CONFIRMED` means the user accepted the exact scoped claim and proposed target.
It is not Product truth, Provider qualification, P6, Final Acceptance, or proof
that the target changed. `ADOPTED` requires target owner verification and exact
adoption evidence.

## Preserve Active State And Write A Pending Candidate

For a new claim, choose a stable, topic-specific `claim_id`; do not use an Agent
name, date-only identity, or vague word such as `lesson`. Reuse the same file
only for the same semantic claim and only when no writer owns that path.

The file has two explicit lanes:

- `Active Claim` is the version currently adopted by a target. A new pending
  revision does not replace the active claim. Preserve the active claim,
  `active_candidate_sha256`, `active_candidate_commit`, target, and adoption
  evidence byte-for-byte until a replacement finishes target verification or
  the active version is explicitly retired.
- `Pending Candidate` is the proposed revision. It owns independent pending
  evidence, approval, and adoption state. First-version claims use
  `active_claim_version: 0` and an explicit empty active section.

Before confirmation:

1. Write `pending_approval_status: PENDING_CONFIRMATION` and
   `pending_adoption_status: NOT_ADOPTED`; do not change the active lane.
2. Preserve exact repository-relative evidence paths plus verified content,
   artifact, record, or summary hashes when available.
3. State scope and exclusions narrowly enough that a target owner can apply the
   rule without Provider-wide or model-wide extrapolation.
4. Stage only this Learning Claim path and create a candidate checkpoint commit
   containing its exact completed bytes. Do not include an adoption target or
   unrelated path in that commit. Repository Git rules remain authoritative.
5. Compute the exact candidate bytes SHA-256 from the committed preimage, using
   `git show <candidate-commit>:<repository-relative-claim-path>` rather than
   trusting mutable working-tree bytes. The candidate checkpoint commit and
   SHA-256 together are the confirmation identity.
6. Present the user with the claim, support/counter evidence, scope, exclusions,
   evidence status, recommended action, exact adoption target paths, planned
   verification, candidate checkpoint commit, and exact candidate bytes
   SHA-256.
7. Ask for `Confirm`, `Revise`, or `Reject`. Do not continue adoption in the
   same turn without that response.

The preview may bundle confirmation of the claim and one bounded adoption
action only when it names the exact target owner, target paths, behavior change,
and verification. A vague confirmation cannot authorize a broader target.

## Handle User Confirmation

Reopen the candidate checkpoint before acting. Recompute the SHA-256 of
`git show <candidate-commit>:<claim-path>` and require the current pending file
to match that same committed preimage before target mutation.

- `Confirm`: valid only when commit, committed bytes, current pending bytes, and
  previewed hash all match. Record the hash and commit in
  `confirmed_candidate_sha256` and `confirmed_candidate_commit`, set
  `pending_approval_status: CONFIRMED`, and record sanitized `confirmed_by`,
  `confirmed_at`, and a durable `confirmation_evidence` pointer without raw
  transcript or secret content. Then execute the exact previewed adoption
  through the existing target owner and repository workflow. Changed bytes
  require a new confirmation.
- `Revise`: update the candidate, keep `PENDING_CONFIRMATION`, compute a new
  candidate checkpoint commit and hash, and show a new preview. The old
  confirmation request is stale.
- `Reject`: set `pending_approval_status: REJECTED`, keep
  `pending_adoption_status: NOT_ADOPTED`, record the bounded rejection reason,
  preserve the active claim and its adoption evidence unchanged, and do not
  modify the target.

If the user response is ambiguous, evidence changed, target scope expanded, or
the exact candidate cannot be reopened, stop fail closed and request a fresh
confirmation.

## Apply A Confirmed Claim

After exact confirmation, use the target's existing canonical owner, tests,
review tier, and Harness routing. Do not build a generic patch executor.

- `Skill`: update only the matching advisory knowledge owner and its tests.
- `Provider Policy`: update the existing policy owner; never select or call the
  Provider as part of learning adoption.
- `Preflight`: preserve fail-closed readiness and authorization boundaries.
- `Contract`: update code, tests, and canonical docs together when behavior
  changes.
- `Gate`: require evidence that the rule is measurable at that Gate's proof
  layer; human-only or uncalibrated findings remain advisory or
  `NOT_EVALUATED`.

Set `pending_adoption_status: APPLYING` only while the confirmed bounded change
is in progress. The pending candidate does not replace the active claim while
application is incomplete. Only after target owner verification passes may the
pending version become `Active Claim`, record `active_adoption_status: ADOPTED`
with candidate hash/commit, target paths, adoption commit, tests, and Harness
receipt, and clear the pending lane. On failure or blocker, keep the prior
active claim unchanged and the pending lane truthful; never claim adoption from
a patch, test plan, or historical receipt alone.

## Supersession And Reopen

New evidence that changes a claim must create or replace only the pending lane,
preserve the active lane, and preserve earlier candidate preimages through
their candidate checkpoint commits and explicit source references. A claim
must be reconfirmed when its failure pattern, hypothesis, evidence set, scope,
exclusions, recommended action, or adoption target changes.

Use `RETIRED` when the target no longer consumes the rule or newer evidence
supersedes it. A prior `ADOPTED` claim can become `CONTESTED` or `RETIRED`; do
not leave stale advice current merely because it was once implemented.

## Hard Safety Boundaries

- MUST NOT call a Provider.
- MUST NOT generate media.
- MUST NOT write Manifest, Registry, P6, or Final Acceptance state.
- MUST NOT automatically retry, activate, push, or release.
- MUST NOT commit an adoption target before user confirmation. The only
  pre-confirmation commit is the path-limited candidate checkpoint required to
  preserve the exact confirmation preimage.
- MUST NOT modify an adoption target before user confirmation.
- MUST NOT treat Memory/RAG, a Learning Claim, or user confirmation as a paid
  call permit, Production acceptance, activation, recovery, or release receipt.
- MUST NOT place ordinary operating guidance or speculative risk into
  `.agent/bug-memory/`; that owner remains limited to real reproducible
  regressions/incidents.

When no claim qualifies, report `no_candidate` and continue the parent session
completion. When a candidate qualifies, the confirmation request is the
natural stopping point until the user responds.
