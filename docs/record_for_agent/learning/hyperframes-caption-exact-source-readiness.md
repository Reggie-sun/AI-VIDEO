---
document_kind: learning_claim
claim_id: hyperframes-caption-exact-source-readiness
active_claim_version: 0
active_evidence_status: NONE
active_adoption_status: NOT_ADOPTED
active_candidate_sha256:
active_candidate_commit:
active_adoption_commit:
pending_claim_version: 1
pending_evidence_status: SUPPORTED
pending_approval_status: PENDING_CONFIRMATION
pending_adoption_status: NOT_ADOPTED
confirmed_candidate_sha256:
confirmed_candidate_commit:
confirmed_by:
confirmed_at:
confirmation_evidence:
supersedes:
retired_by:
---

# Exact Production Source Is Required for HyperFrames Caption Readiness

Date: 2026-08-28

## Active Claim

None. This is the first candidate (`active_claim_version: 0`) and no target
currently consumes an adopted version.

## Pending Candidate

### Failure Pattern

`failure_pattern`: A raw pinned-HyperFrames caption capability render can pass
while the exact AI-VIDEO Production source fails before rendering. In the
observed controlled comparison, the raw source used generic `sans-serif`, but
the Production source emitted selected custom `font_family: "Fixture Sans"`
without a matching `@font-face`; HyperFrames lint rejected the exact source as
`font_family_without_font_face`.

Therefore a raw renderer capability PASS, source-string unit assertion, or
successful browser launch is insufficient evidence of Production caption
render readiness. Readiness requires the exact materialized Production source
to pass the selected renderer's current lint/render contract.

### Hypothesis

`hypothesis`: The observed failure is a contract mismatch between AI-VIDEO's
caption-style/source policy and the pinned renderer, not a general failure of
the renderer binary, browser, local audio path, or network isolation.

Held constants were repository checkout, `hyperframes@0.7.103`, Chrome
Headless Shell `152.0.7928.2`, local execution, and a network namespace with
only `lo`. The isolated candidate variable was source/font construction:
generic `sans-serif` in the raw arm versus selected custom `Fixture Sans` in
the Production arm. AI-VIDEO emits the custom family but forbids `@font-face`;
the pinned renderer requires `@font-face` for a non-auto-resolved family.

The comparison does not yet distinguish every possible repair: an explicit
content-addressed local font asset contract, a narrower renderer-resolvable
font policy, or another contract-preserving source representation remain
uncompared.

### Supporting Evidence

`supporting_evidence`:

1. Stable session record
   `docs/record_for_agent/2026-08-28-caption-quality-gate-implementation-plan.md`
   at commit `6bdca35cb6b6e35ddbf1fc60cbd236e64b89aa1b`, committed bytes SHA-256
   `73aa8f64510f00a79df20aa519d29c38220534cef70f2322a0e6502e8e95d205`.
   It records commands, exact artifacts, proof-layer boundaries, and the
   fail-closed Production verdict.
2. Controlled-comparison summary
   `runs/caption-quality-gate-real-validation-20260828-v1/validation-summary.json`,
   SHA-256
   `f4d09142a8dc636f7e23f9a50c5c93eec6085a2ea5cb59236ffe73f71a09247d`.
3. Raw arm PASS artifact
   `runs/caption-quality-gate-real-validation-20260828-v1/media/raw-p4-caption-capability.mp4`,
   SHA-256
   `5e9278b39c3fa52adfb2664423a35aadbe05022ca404385dd6aeb0a9a6df129f`.
   The real renderer test passed, audio was present, and exact half-open caption
   visibility `[15,45)` was observed at frames `14/15/44/45`.
4. Production arm FAIL source
   `runs/caption-quality-gate-real-validation-20260828-v1/production-failure/index.html`,
   SHA-256
   `f721aa805e6a6c034cded08fa6369c18c41252b2ee898b66bfcff916ec0b6dbd`,
   and failed Manifest
   `runs/caption-quality-gate-real-validation-20260828-v1/production-failure/manifest.json`,
   SHA-256
   `d6a3a351cdffff499d4012bf303ea6201df5da1ca77289802cca102b310f4407`.
   The durable attempt stopped at `render_phase=lint` with
   `renderer_source_invalid`; no MP4, active render, or CAPTION P6 receipt was
   produced.
5. Current code evidence at the same checkout:
   `src/ai_video/production/_hyperframes_source.py::_caption_style_css()`
   emits the arbitrary selected family (file SHA-256
   `b225a9476c35616c12411ff01a5b05bab40f9f277fab447d6d308d778a5242b9`),
   while
   `src/ai_video/production/hyperframes.py::_parse_source_document()` marks
   `@font-face` as an external style/font surface (file SHA-256
   `8736a74e4baeef34e3caf3a1524a967a1770e272f80c1130b67062bb4a323754`).

### Counter Evidence

`counter_evidence`:

- The raw generic `sans-serif` arm rendered successfully. This directly
  counters any broader claim that the pinned renderer/browser or all caption
  fonts are broken.
- Only one non-auto-resolved family (`Fixture Sans`) was exercised against the
  exact Production source. No controlled local `@font-face`, known
  renderer-auto-resolved custom family, or cross-platform arm was run.
- Repository records and current tests were searched for an exact successful
  pinned-version Production render using the same custom-font construction;
  none was found. This absence is a coverage limitation, not proof that no
  environment could resolve the family.
- The Qingyan V4 review-only MP4 contains readable burned-in Chinese captions,
  but it is not bound to the current canonical CaptionTrack/ResolvedTimeline
  and does not exercise this Production source path, so it neither supports nor
  refutes custom-font Production readiness.

### Scope And Exclusions

`scope`: AI-VIDEO's current P3/P4 HyperFrames path as observed on 2026-08-28,
with `hyperframes@0.7.103`, Chrome Headless Shell `152.0.7928.2`, exact
materialized caption source, and a caption style selecting a non-auto-resolved
font family without an accepted local font declaration.

`exclusions`: Do not extrapolate this claim to generic CSS families, every
installed font, other HyperFrames versions, other renderers, Provider output,
caption semantic correctness, perceptual readability, CAPTION P6, Final
Acceptance, activation, release, or Qingyan V4 quality. The claim does not
select a font-asset schema or authorize a Product Runtime fix.

### Evidence Assessment

`pending_evidence_status`: `SUPPORTED`.

The threshold is met by one controlled two-arm comparison that held the
renderer/browser/local execution boundary constant and isolated source/font
construction. The claim is intentionally limited to readiness evidence and the
observed source contract. A successful exact Production custom-font render at
the same pinned versions would materially counter it; a controlled local-font
declaration arm would narrow the recommended contract repair.

### Recommended Action

`recommended_action`: Adopt a fail-closed readiness rule: whenever Production
captions select a non-generic font, only the exact materialized Production
source passing the pinned HyperFrames lint and real render gate may establish
renderer readiness. Raw generic-font capability evidence must remain scoped to
the raw arm. Until a separate content-addressed local-font contract is accepted
and verified, a custom-font lint failure must stop before CAPTION P6 and must
not be hidden by silent font substitution, disabled lint, or an alternate
renderer path.

This candidate requests confirmation of the readiness rule only. It does not
authorize choosing or implementing the later font-asset repair.

### Adoption Target

`adoption_target`: `Gate`.

- Canonical owner and target paths:
  `docs/agent-primary-contract-matrix.md` P3/P4 verification contract and
  `.agent/context/control-plane-playbook.md` empirical final-composition
  preflight; the executable seam remains
  `tests/test_production_hyperframes.py::test_p4_production_renderer_gate_renders_resolved_audio_and_captions`.
- Expected behavior change: readiness records must distinguish raw capability
  from exact Production-source lint/render evidence and stop fail closed on the
  latter's custom-font incompatibility.
- Unchanged contracts: `ResolvedTimeline`, HyperFrames selection,
  `ProductionStateCommitter`, caption source truth, activation, CAPTION P6, and
  Final Acceptance ownership remain unchanged; no Provider or network effect.
- Planned verification after confirmation: documentation contract checks,
  policy audit, the raw real-renderer gate, and the exact Production renderer
  gate using pinned binary/browser paths. A Production gate failure remains a
  truthful blocker, not an adopted PASS.

No adoption target has been modified before confirmation.

### Confirmation

`pending_approval_status`: `PENDING_CONFIRMATION`.

The candidate checkpoint commit and SHA-256 of the exact committed claim bytes
will be presented out-of-band after the path-only checkpoint commit. Any change
to this claim, its evidence, scope, recommendation, or target invalidates that
confirmation identity.

### Adoption Evidence

`pending_adoption_status`: `NOT_ADOPTED`.

There is no target mutation, adoption commit, Harness receipt, Production
state change, Provider action, activation, CAPTION P6, or Final Acceptance
evidence.

## Supersession And Reopen Conditions

Reopen or reconfirm this claim if the pinned renderer/browser changes, the
caption-style/source policy accepts a verified content-addressed local font,
the exact Production custom-font arm passes, or new evidence shows that the
failure came from a held-constant runtime component. Mark it `CONTESTED` if an
exact same-version/same-source counterexample appears, `REFUTED` if exact
Production source no longer requires this distinction, and `RETIRED` if the
selected renderer or caption source owner changes. `supersedes` and
`retired_by` remain empty for this first version.
