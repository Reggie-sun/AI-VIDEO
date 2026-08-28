---
document_kind: learning_claim
claim_id: hyperframes-caption-exact-source-readiness
evidence_index_version: "1"
admission_basis: MATERIAL_EXISTING_CLAIM_UPDATE
material_update_target_claim: hyperframes-caption-exact-source-readiness
material_update_previous_evidence: docs/record_for_agent/2026-08-29-qingyan-caption-final-acceptance.md#caption-readiness-v2-previous
material_update_delta: V9 exact generic-sans Chinese Production evidence supersedes V4 NOT_EVALUATED and adds CAPTION_P6 plus FINAL_ACCEPTANCE proof
active_claim_version: 3
active_evidence_status: SUPPORTED
active_adoption_status: ADOPTED
active_candidate_sha256: f845f5d1aa589527f6987156cd07f79769220a75c16e372aabca7318574ceb17
active_candidate_commit: 0d01a97f7c340baf350c6681274c0dde9fce5b96
active_adoption_commit: 9fa65248647bcf5ae07ca15edafeb82b0e69d9bd
pending_claim_version: 0
pending_evidence_status: RETIRED
pending_approval_status: CONFIRMED
pending_adoption_status: NOT_ADOPTED
confirmed_candidate_sha256: f845f5d1aa589527f6987156cd07f79769220a75c16e372aabca7318574ceb17
confirmed_candidate_commit: 0d01a97f7c340baf350c6681274c0dde9fce5b96
confirmed_by: user
confirmed_at: 2026-08-29T03:40:12+08:00
confirmation_evidence: conversation-confirmation:2026-08-29:hyperframes-caption-exact-source-readiness-v3
supersedes: 692e8b2fa5eaf3a24d0d288b08eb95dc89bddd79 / e5a9a65aaa6d98a29879f0afaafb0cb392f9b0d1fb562c8cfe6b681af2d008ba
retired_by:
---

# Exact Production Source And Pinned Font Contract Determine HyperFrames Caption Readiness

Date: 2026-08-29

## Active Claim

Active v3 was adopted by the Gate owner after exact user confirmation and target verification.
The earlier unconfirmed v1/v2 preimages remain preserved by their checkpoint commits; they were
never active or adopted.

### Failure Pattern

`failure_pattern`: Raw pinned-HyperFrames caption capability can pass while exact AI-VIDEO
Production source fails before rendering. After replacing a fictional fixture family with a
renderer-bundled canonical family, exact Production source can pass; without an early runtime
font contract, however, arbitrary or alias-substituted families can still reach source lint and
fail after materialization begins.

Therefore renderer readiness cannot be inferred from a raw generic-font arm, a source-string unit
assertion, or browser availability. It requires both a fail-closed pinned font-family preflight and
the exact materialized Production source passing the selected renderer's lint/render gate.

### Hypothesis

`hypothesis`: The observed failure was caused by a fictional `Fixture Sans` family outside the
same-name canonical bundled/generic tables accepted by `hyperframes@0.7.103`, combined with a
missing AI-VIDEO preflight. It was not a general failure of the renderer binary, Chrome, local
audio, caption timing, or network isolation.

Held constants across the fail/pass evidence were the AI-VIDEO P3/P4 source path, pinned
HyperFrames/Chrome runtime, local isolated execution, deterministic audio/timeline inputs, and
the same Production renderer gate. The relevant changes were font identity (`Fixture Sans` to
canonical `Inter`) and the addition of pre-staging validation. A public-seam mutation experiment
isolated the validation behavior: deleting the allowlist check made the unsupported-font
regression fail with `DID NOT RAISE`; restoring it made the test pass.

This does not prove that the hard-coded set will remain correct after a HyperFrames upgrade, that
all bundled families contain every required glyph, or that content-addressed custom font assets
are supported.

### Supporting Evidence

`supporting_evidence`:

| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/record_for_agent/2026-08-29-qingyan-caption-final-acceptance.md#qingyan-v9-exact-media | qingyan-v9-canonical-artifact | qingyan-final-acceptance-canonicalization-20260829 | production-final-v9 | claim-safe-continuity | 9f3534ce93084a4f9b5e6b70b3d60e0599302202f73ef28d92bc762db1e78bd2 | EXACT_MEDIA_ANALYZER_AND_VISUAL | PASS | `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/final-acceptance-canonicalization-20260829/` |
| docs/record_for_agent/2026-08-29-qingyan-caption-final-acceptance.md#qingyan-v9-caption-p6 | qingyan-v9-canonical-artifact | qingyan-final-acceptance-canonicalization-20260829 | production-final-v9 | claim-safe-continuity | 9f3534ce93084a4f9b5e6b70b3d60e0599302202f73ef28d92bc762db1e78bd2 | CAPTION_P6 | PASS | `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/production-final-v9/state/reviews/` |
| docs/record_for_agent/2026-08-29-qingyan-caption-final-acceptance.md#qingyan-v9-final-acceptance | qingyan-v9-canonical-artifact | qingyan-final-acceptance-canonicalization-20260829 | production-final-v9 | claim-safe-continuity | 9f3534ce93084a4f9b5e6b70b3d60e0599302202f73ef28d92bc762db1e78bd2 | FINAL_ACCEPTANCE | PASS | `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/production-final-v9/state/acceptance/final.2ac31c13692c47eeca778def2c0a4d6bad2921da2ed64d88a3275c8f91566e90.json` |

1. Stable session record
   `docs/record_for_agent/2026-08-28-caption-quality-gate-implementation-plan.md` at commit
   `ccb3e4bd6891552ce8f5a0986bdc9b174bda3ff1`, committed bytes SHA-256
   `6916c679f2d9e1cf313d68a1d7e4cd3a570fe3939f9d6718deb2b42b2455dadb`. It reconciles the
   pre-fix FAIL with the post-fix exact Production PASS and preserves proof-layer boundaries.
2. Pre-fix controlled comparison
   `runs/caption-quality-gate-real-validation-20260828-v1/validation-summary.json`, SHA-256
   `f4d09142a8dc636f7e23f9a50c5c93eec6085a2ea5cb59236ffe73f71a09247d`: raw generic
   `sans-serif` PASS versus exact Production `Fixture Sans` lint FAIL
   `font_family_without_font_face`.
3. Post-fix validation summary
   `runs/caption-quality-gate-font-fixture-fix-20260828-v1/validation-summary.json`, SHA-256
   `4174a7bd3debece5781a675583fa5869057aa3fe1bfc7097bc4861efa6cc539e`. The exact
   Production fixture using `Inter` passed materialization, lint, check, render, verification,
   test-fixture activation, audio measurement, and caption frame-boundary checks.
4. Post-fix exact MP4
   `runs/caption-quality-gate-font-fixture-fix-20260828-v1/media/production-caption-inter.mp4`,
   SHA-256 `e3b319bd2ed6d47ce382a34bef97edd724ddb3a49d40f301e878853e21709ab4`.
   It is H.264 `1280x720`, `24fps`, `2.022s`, contains AAC audio, and project-local
   `video-analysis video_review` reported `96/96` unique sampled frames and `issues=[]`.
5. Exact caption boundary evidence
   `runs/caption-quality-gate-font-fixture-fix-20260828-v1/renderer-evidence/caption-frames.json`,
   SHA-256 `a241daac5c5a326de70adfed93270b0b265c4267eb8c98d40db3d804103ac7f1`:
   caption pixels are present on frames `0/11/13/23` and absent on `12/24`, matching `[0,12)`
   and `[13,24)`.
6. Runtime fix commit `0ed672e8dcff68ff8e55e9e736f1361611d7783a`; committed
   `src/ai_video/production/_hyperframes_source.py` SHA-256
   `cceb6cb88219204a8c5bf674e0357a40b2d97d63eeb434d8e11f19c1637fdde7`. The public
   materializer regression verifies typed `RENDERER_SOURCE_INVALID` and no `staging_root` for an
   unsupported family. Mutation removal produced RED before restoration.
7. Fresh exact-range Harness receipt
   `.agent/harness/runs/caption-font-contract-fix-20260828/receipt.json` for
   `ad7ce081..0ed672e`: Architecture Gate PASS, Harness `204 passed`, Production contract
   `2900 passed, 3 skipped, 1225 deselected`, CLI/config `13 passed`; receipt verification reports
   complete, fresh, snapshot-matching proof.
8. Qingyan V9 stable record
   `docs/record_for_agent/2026-08-29-qingyan-caption-final-acceptance.md` at commit
   `18c0f9f8ce3de2c8caba56f5727ee501c54ab9d8`, committed bytes SHA-256
   `b114e9bbad18116ff01d3d77b75b76c873a8373dd9c4d5d6a684d958819ac31a`. It binds the
   exact generic `sans-serif` Chinese caption source to the V9 MP4, all four PASS review receipts,
   CAPTION P6, and Final Acceptance without treating those proof layers as independent attempts.

### Counter Evidence

`counter_evidence`:

| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/record_for_agent/2026-08-29-qingyan-caption-final-acceptance.md#qingyan-v4-production-entry | qingyan-v4-review-only | qingyan-final-acceptance-canonicalization-20260829 | caption-repaired-v4 | review-only-source | 087497ae1b4be12b260899706c19698c8d7d88635708528a6b8cf0d1fd7ac4e1 | PRODUCTION_GATE | NOT_EVALUATED | `docs/record_for_agent/2026-08-28-caption-quality-gate-implementation-plan.md` |

- The raw generic `sans-serif` arm and post-fix canonical `Inter` Production arm both pass. This
  refutes the broader v1 reading that all selected non-generic families require a new local
  `@font-face` asset contract or that the pinned renderer cannot render Production captions.
- The live Production arm exercised only `Inter`; `EB Garamond` is covered by deterministic tests
  but not a separate real-render arm. No cross-host or renderer-upgrade comparison was executed.
- A same-name bundled family can still lack a required language glyph. V9 establishes the exact
  selected Chinese cue set under generic `sans-serif`, not broad Chinese, bilingual, emoji, or
  rare-glyph coverage, and not a reusable perceptual-readability guarantee.
- Custom content-addressed font assets remain outside the implemented contract. The fix rejects
  arbitrary custom family names; it does not add a secure font asset schema or prove that
  `@font-face local()` would preserve authored identity.
- Qingyan V4 review-only captions remain outside the canonical active
  CaptionTrack/ResolvedTimeline/final-media chain. V9 supersedes that NOT_EVALUATED boundary with
  one separate canonical chain; it does not retroactively upgrade V4.
- A focused `experience` RAG follow-up returned the pre-fix claim and record as fresh indexed
  advisory sources; current code, committed record, exact artifacts, and receipt were reopened
  directly because retrieval excerpts do not establish current runtime truth.

### Scope And Exclusions

`scope`: AI-VIDEO's P3/P4 HyperFrames caption source path using `hyperframes@0.7.103`, Chrome
Headless Shell `152.0.7928.2`, the same-name canonical bundled/generic family contract implemented
at commit `0ed672e`, and local isolated exact-source lint/render evidence from 2026-08-28 through
2026-08-29, including Qingyan V9's exact generic `sans-serif` Chinese cue set through CAPTION P6 and
Final Acceptance.

`exclusions`: Do not extrapolate to future HyperFrames versions, other renderers, installed OS font
aliases, custom font assets, cross-host reproducibility, required-language glyph coverage, caption
semantics outside the accepted V9 cues, reusable perceptual readability, other Provider outputs,
other CAPTION P6 or Final Acceptance decisions, release, publication, or Qingyan V4 quality. This
candidate does not authorize Product Runtime changes or reclassify the P4 test Manifest as
Production acceptance.

### Evidence Assessment

`active_evidence_status`: `SUPPORTED`.

Admission is satisfied because new exact evidence materially narrows the existing pending claim:
the original raw/Production comparison identified the boundary, and the fix plus exact Production
PASS, public fail-closed regression, mutation RED, and fresh Harness receipt distinguish a fictional
unsupported family from a canonical bundled family. Qingyan V9 additionally supersedes the earlier
V4 `NOT_EVALUATED` boundary with exact generic `sans-serif` Chinese Production evidence reaching
CAPTION P6 and Final Acceptance. This is a `MATERIAL_EXISTING_CLAIM_UPDATE`, not a second independent
attempt: all V9 proof layers share one artifact identity. Evidence remains bounded to the pinned
runtime and the exact accepted cue/artifact sets. A same-version exact-source failure using `Inter`,
an allowlisted alias that silently substitutes, or a mismatch between the allowlist and renderer
tables would make this claim `CONTESTED`.

### Recommended Action

`recommended_action`: Adopt a maintenance Gate rule: any HyperFrames version change must reopen
the exact renderer bundled/generic font tables, synchronize the AI-VIDEO preflight without admitting
aliases, and rerun both the public unsupported-font/no-staging regression and the exact Production
renderer gate. Readiness evidence must continue to distinguish raw capability from exact
Production-source lint/render evidence. Unknown, alias-substituted, or unverified custom families
must fail closed and must not be hidden by `@font-face local()`, silent fallback, disabled lint, or
an alternate renderer path.

The current runtime fix was directly authorized by the user and independently verified. Adoption
of this Learning Claim authorizes only the bounded durable maintenance rule below; it does not
expand the runtime fix or any Product lifecycle authority.

### Adoption Target

`adoption_target`: `Gate`.

- Canonical owner and exact target path:
  `.agent/context/control-plane-playbook.md`, under the existing empirical final-composition /
  renderer preflight guidance.
- Expected behavior change: document that a pinned HyperFrames version change must synchronize the
  same-name font-family contract and rerun the two existing executable seams before claiming caption
  source readiness.
- Executable seams remain
  `tests/test_production_hyperframes.py::test_p4_source_rejects_caption_font_outside_pinned_renderer_contract`
  and
  `tests/test_production_hyperframes.py::test_p4_production_renderer_gate_renders_resolved_audio_and_captions`.
- Unchanged contracts: `ResolvedTimeline`, HyperFrames selection, `ProductionStateCommitter`,
  caption truth, activation, CAPTION P6, Final Acceptance, Provider authorization, and current
  Product Runtime code remain unchanged.
- Planned verification after confirmation: documentation contract check, policy audit, task-delta
  Architecture Gate, the public unsupported-font regression, and the exact Production renderer
  gate with pinned binary/browser paths.

The adoption target was modified only after the exact candidate confirmation recorded below.

### Confirmation

`pending_approval_status`: `CONFIRMED`.

用户确认了 commit `0d01a97f7c340baf350c6681274c0dde9fce5b96` 中 SHA-256
`f845f5d1aa589527f6987156cd07f79769220a75c16e372aabca7318574ceb17` 的 exact candidate。
本次 adoption 只覆盖预览中声明的 Gate owner、target path、behavior change 与 verification；
evidence、scope、recommendation、target 或 candidate bytes 发生变化时必须重新确认。

### Adoption Evidence

`active_adoption_status`: `ADOPTED`.

- Canonical target：`.agent/context/control-plane-playbook.md` 的
  `HyperFrames Caption Source Readiness`。
- Adoption commit：`9fa65248647bcf5ae07ca15edafeb82b0e69d9bd`。
- Focused verification：unsupported-font/no-staging regression 与
  `test_p4_production_renderer_gate_renders_resolved_audio_and_captions` 均 PASS；后者使用 pinned
  `hyperframes@0.7.103`、Chrome `152.0.7928.2` 与隔离网络 namespace。
- Exact-range Harness receipt：
  `.agent/harness/runs/hyperframes-caption-readiness-adoption-20260829/receipt.json`，验证结果为
  complete、fresh、snapshot-matching；Architecture Gate PASS、Learning Skill `27 passed`、Harness
  `204 passed`。
- Unchanged boundary：没有 Product state、Provider 或 Production media effect，也没有 activation、
  CAPTION P6、Final Acceptance、push 或 release effect。Mandatory exact renderer test 只在 `/tmp`
  生成隔离的 ephemeral fixture/evidence；它不进入 Registry、Manifest 或 delivery truth。V9 的 exact
  Chinese cues 也不外推为 broad glyph coverage。

## Pending Candidate

None. Active v3 已完成 target verification 与 adoption；`pending_claim_version: 0`。后续任何
evidence、scope、recommendation 或 target 变化都必须创建新的 pending revision 并重新确认。

## Supersession And Reopen Conditions

Active v3 supersedes the unconfirmed pending v2 preimage at `692e8b2`; no earlier active adopted
claim required retirement. Reopen or reconfirm if HyperFrames/Chrome changes, the bundled/generic
tables change, a content-addressed custom-font contract is accepted, required-language glyph
coverage becomes part of readiness, or exact same-version evidence contradicts the preflight.
Mark `CONTESTED` for an unresolved exact counterexample, `REFUTED` if the preflight/source
distinction no longer predicts renderer behavior, and `RETIRED` if HyperFrames or the caption
source owner changes.
