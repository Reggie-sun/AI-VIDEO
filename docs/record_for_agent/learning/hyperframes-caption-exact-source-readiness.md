---
document_kind: learning_claim
claim_id: hyperframes-caption-exact-source-readiness
evidence_index_version: "1"
admission_basis: MATERIAL_EXISTING_CLAIM_UPDATE
material_update_target_claim: hyperframes-caption-exact-source-readiness
material_update_previous_evidence: docs/record_for_agent/2026-08-29-qingyan-caption-final-acceptance.md#caption-readiness-v2-previous
material_update_delta: V9 exact generic-sans Chinese Production evidence 取代 V4 NOT_EVALUATED，并新增 CAPTION_P6 与 FINAL_ACCEPTANCE proof
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

Active v3 已在用户确认 exact candidate、target owner 完成验证后被 Gate 采用。此前未确认的 v1/v2
preimage 继续由各自 checkpoint commit 保存；它们从未进入 active 或 adopted 状态。

### Failure Pattern

`failure_pattern`：raw pinned-HyperFrames caption capability 可以 PASS，但 exact AI-VIDEO
Production source 仍可能在 render 前失败。将虚构 fixture family 替换为 renderer bundled canonical
family 后，exact Production source 可以 PASS；但如果缺少前置 runtime font contract，任意 family 或
alias-substituted family 仍可能进入 source lint，并在 materialization 开始后才失败。

因此，不能根据 raw generic-font arm、source-string unit assertion 或 browser availability 推断
renderer readiness。必须同时具备 fail-closed pinned font-family preflight，并证明 exact materialized
Production source 通过 selected renderer 的 lint/render Gate。

### Hypothesis

`hypothesis`：已观察到的 failure 来自虚构的 `Fixture Sans` family；它不在
`hyperframes@0.7.103` 接受的 same-name canonical bundled/generic tables 中，同时 AI-VIDEO 缺少相应
preflight。这不是 renderer binary、Chrome、local audio、caption timing 或 network isolation 的普遍失败。

FAIL/PASS evidence 之间保持不变的条件包括 AI-VIDEO P3/P4 source path、pinned
HyperFrames/Chrome runtime、local isolated execution、deterministic audio/timeline inputs，以及同一
Production renderer Gate。实际变量是 font identity（`Fixture Sans` 改为 canonical `Inter`）和新增
pre-staging validation。public seam mutation experiment 隔离了 validation behavior：删除 allowlist
check 后，unsupported-font regression 以 `DID NOT RAISE` 失败；恢复检查后 test PASS。

这些证据不能证明 HyperFrames 升级后 hard-coded set 仍然正确，也不能证明全部 bundled family
包含所有 required glyph，或已经支持 content-addressed custom font asset。

### Supporting Evidence

`supporting_evidence`:

| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/record_for_agent/2026-08-29-qingyan-caption-final-acceptance.md#qingyan-v9-exact-media | qingyan-v9-canonical-artifact | qingyan-final-acceptance-canonicalization-20260829 | production-final-v9 | claim-safe-continuity | 9f3534ce93084a4f9b5e6b70b3d60e0599302202f73ef28d92bc762db1e78bd2 | EXACT_MEDIA_ANALYZER_AND_VISUAL | PASS | `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/evidence/final-acceptance-canonicalization-20260829/` |
| docs/record_for_agent/2026-08-29-qingyan-caption-final-acceptance.md#qingyan-v9-caption-p6 | qingyan-v9-canonical-artifact | qingyan-final-acceptance-canonicalization-20260829 | production-final-v9 | claim-safe-continuity | 9f3534ce93084a4f9b5e6b70b3d60e0599302202f73ef28d92bc762db1e78bd2 | CAPTION_P6 | PASS | `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/production-final-v9/state/reviews/` |
| docs/record_for_agent/2026-08-29-qingyan-caption-final-acceptance.md#qingyan-v9-final-acceptance | qingyan-v9-canonical-artifact | qingyan-final-acceptance-canonicalization-20260829 | production-final-v9 | claim-safe-continuity | 9f3534ce93084a4f9b5e6b70b3d60e0599302202f73ef28d92bc762db1e78bd2 | FINAL_ACCEPTANCE | PASS | `runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/production-final-v9/state/acceptance/final.2ac31c13692c47eeca778def2c0a4d6bad2921da2ed64d88a3275c8f91566e90.json` |

1. 稳定 session record
   `docs/record_for_agent/2026-08-28-caption-quality-gate-implementation-plan.md`，commit
   `ccb3e4bd6891552ce8f5a0986bdc9b174bda3ff1` 中的 bytes SHA-256 为
   `6916c679f2d9e1cf313d68a1d7e4cd3a570fe3939f9d6718deb2b42b2455dadb`。它对齐了 pre-fix
   FAIL 与 post-fix exact Production PASS，并保留 proof-layer boundary。
2. 修复前 controlled comparison
   `runs/caption-quality-gate-real-validation-20260828-v1/validation-summary.json`, SHA-256
   `f4d09142a8dc636f7e23f9a50c5c93eec6085a2ea5cb59236ffe73f71a09247d`：raw generic
   `sans-serif` PASS，而 exact Production `Fixture Sans` 在 lint 阶段以
   `font_family_without_font_face` FAIL。
3. 修复后 validation summary
   `runs/caption-quality-gate-font-fixture-fix-20260828-v1/validation-summary.json`, SHA-256
   `4174a7bd3debece5781a675583fa5869057aa3fe1bfc7097bc4861efa6cc539e`。使用 `Inter` 的 exact
   Production fixture 通过 materialization、lint、check、render、verification、test-fixture
   activation、audio measurement 与 caption frame-boundary checks。
4. 修复后 exact MP4
   `runs/caption-quality-gate-font-fixture-fix-20260828-v1/media/production-caption-inter.mp4`,
   SHA-256 `e3b319bd2ed6d47ce382a34bef97edd724ddb3a49d40f301e878853e21709ab4`.
   该文件为 H.264 `1280x720`、`24fps`、`2.022s`，包含 AAC audio；project-local
   `video-analysis video_review` 报告 `96/96` unique sampled frames 与 `issues=[]`。
5. Exact caption boundary evidence
   `runs/caption-quality-gate-font-fixture-fix-20260828-v1/renderer-evidence/caption-frames.json`,
   SHA-256 `a241daac5c5a326de70adfed93270b0b265c4267eb8c98d40db3d804103ac7f1`：caption pixels
   在 frames `0/11/13/23` 存在，在 `12/24` 不存在，符合 `[0,12)` 与 `[13,24)`。
6. Runtime fix commit `0ed672e8dcff68ff8e55e9e736f1361611d7783a`；committed
   `src/ai_video/production/_hyperframes_source.py` SHA-256
   `cceb6cb88219204a8c5bf674e0357a40b2d97d63eeb434d8e11f19c1637fdde7`。public materializer
   regression 验证 unsupported family 返回 typed `RENDERER_SOURCE_INVALID`，且不创建
   `staging_root`；移除 validation 的 mutation 在恢复前产生 RED。
7. Fresh exact-range Harness receipt
   `.agent/harness/runs/caption-font-contract-fix-20260828/receipt.json` for
   `ad7ce081..0ed672e`：Architecture Gate PASS、Harness `204 passed`、Production contract
   `2900 passed, 3 skipped, 1225 deselected`、CLI/config `13 passed`；receipt verification 为
   complete、fresh、snapshot-matching。
8. Qingyan V9 稳定 record
   `docs/record_for_agent/2026-08-29-qingyan-caption-final-acceptance.md`，commit
   `18c0f9f8ce3de2c8caba56f5727ee501c54ab9d8` 中的 bytes SHA-256 为
   `b114e9bbad18116ff01d3d77b75b76c873a8373dd9c4d5d6a684d958819ac31a`。它把 exact generic
   `sans-serif` Chinese caption source 绑定到 V9 MP4、四层 PASS review receipts、CAPTION P6 与
   Final Acceptance，同时没有把这些 proof layers 误算为独立 attempts。

### Counter Evidence

`counter_evidence`:

| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/record_for_agent/2026-08-29-qingyan-caption-final-acceptance.md#qingyan-v4-production-entry | qingyan-v4-review-only | qingyan-final-acceptance-canonicalization-20260829 | caption-repaired-v4 | review-only-source | 087497ae1b4be12b260899706c19698c8d7d88635708528a6b8cf0d1fd7ac4e1 | PRODUCTION_GATE | NOT_EVALUATED | `docs/record_for_agent/2026-08-28-caption-quality-gate-implementation-plan.md` |

- Raw generic `sans-serif` arm 与 post-fix canonical `Inter` Production arm 都 PASS。这否定了 v1
  的过宽解释：不是所有 selected non-generic family 都需要新的 local `@font-face` asset contract，
  pinned renderer 也不是无法渲染 Production captions。
- Live Production arm 只实际覆盖 `Inter`；`EB Garamond` 仅有 deterministic tests，没有独立
  real-render arm。本轮没有执行 cross-host 或 renderer-upgrade comparison。
- Same-name bundled family 仍可能缺少 required language glyph。V9 只证明 generic `sans-serif`
  下 exact selected Chinese cue set，不证明 broad Chinese、bilingual、emoji 或 rare-glyph coverage，
  也不提供可复用的 perceptual-readability guarantee。
- Custom content-addressed font asset 仍在 implemented contract 之外。当前修复会拒绝任意 custom
  family name，但没有增加 secure font asset schema，也没有证明 `@font-face local()` 能保留
  authored identity。
- Qingyan V4 review-only captions 仍不在 canonical active
  `CaptionTrack -> ResolvedTimeline -> final media` chain 中。V9 以单独的 canonical chain 取代该
  `NOT_EVALUATED` boundary，但不会反向升级 V4。
- Focused `experience` RAG follow-up 返回 pre-fix claim 与 record；由于 retrieval excerpt 不能证明
  current runtime truth，本轮仍直接重新打开 current code、committed record、exact artifacts 与 receipt。

### Scope And Exclusions

`scope`：AI-VIDEO P3/P4 HyperFrames caption source path，固定 `hyperframes@0.7.103`、Chrome
Headless Shell `152.0.7928.2`、commit `0ed672e` 实现的 same-name canonical bundled/generic family
contract，以及 2026-08-28 至 2026-08-29 的 local isolated exact-source lint/render evidence；其中
包含 Qingyan V9 exact generic `sans-serif` Chinese cue set 到 CAPTION P6 与 Final Acceptance 的证据。

`exclusions`：不得外推到未来 HyperFrames version、其他 renderer、installed OS font alias、custom
font asset、cross-host reproducibility、required-language glyph coverage、accepted V9 cues 之外的
caption semantics、可复用 perceptual readability、其他 Provider output、其他 CAPTION P6 或 Final
Acceptance 决策、release、publication 或 Qingyan V4 quality。本 claim 不授权 Product Runtime 变更，
也不把 P4 test Manifest 重新分类为 Production acceptance。

### Evidence Assessment

`active_evidence_status`: `SUPPORTED`.

Admission 成立，因为新的 exact evidence 对既有 pending claim 形成了实质收窄：原始 raw/Production
comparison 定位了 boundary；修复、exact Production PASS、public fail-closed regression、mutation
RED 与 fresh Harness receipt 区分了虚构 unsupported family 和 canonical bundled family。Qingyan V9
进一步以到达 CAPTION P6 与 Final Acceptance 的 exact generic `sans-serif` Chinese Production
evidence，取代早期 V4 `NOT_EVALUATED` boundary。这属于
`MATERIAL_EXISTING_CLAIM_UPDATE`，不是第二个 independent attempt；全部 V9 proof layers 共享同一
artifact identity。Evidence 仍限定于 pinned runtime 与 exact accepted cue/artifact set。如果同一
version 的 `Inter` exact source 失败、allowlisted alias 发生 silent substitution，或 allowlist 与
renderer tables 不一致，本 claim 应改为 `CONTESTED`。

### Recommended Action

`recommended_action`：采用一条 maintenance Gate rule。任何 HyperFrames version change 都必须重新
打开 exact renderer bundled/generic font tables，同步 AI-VIDEO preflight 且不得接纳 alias，并重跑
public unsupported-font/no-staging regression 与 exact Production renderer Gate。Readiness evidence
必须继续区分 raw capability 和 exact Production-source lint/render evidence。Unknown、
alias-substituted 或 unverified custom family 必须 fail closed，不得用 `@font-face local()`、silent
fallback、disabled lint 或 alternate renderer path 隐藏问题。

当前 runtime fix 已由用户直接授权并独立验证。采用本 Learning Claim 只授权下方 bounded durable
maintenance rule，不扩大 runtime fix 或任何 Product lifecycle authority。

### Adoption Target

`adoption_target`: `Gate`.

- Canonical owner 与 exact target path：`.agent/context/control-plane-playbook.md`，位于现有
  empirical final-composition / renderer preflight guidance 下。
- 预期 behavior change：明确 pinned HyperFrames version change 必须同步 same-name font-family
  contract，并在声明 caption source readiness 前重跑两条现有 executable seams。
- Executable seams 保持为
  `tests/test_production_hyperframes.py::test_p4_source_rejects_caption_font_outside_pinned_renderer_contract`
  以及
  `tests/test_production_hyperframes.py::test_p4_production_renderer_gate_renders_resolved_audio_and_captions`.
- Unchanged contracts：`ResolvedTimeline`、HyperFrames selection、`ProductionStateCommitter`、
  caption truth、activation、CAPTION P6、Final Acceptance、Provider authorization 与 current Product
  Runtime code 保持不变。
- 确认后的 planned verification：documentation contract check、policy audit、task-delta Architecture
  Gate、public unsupported-font regression，以及使用 pinned binary/browser paths 的 exact Production
  renderer Gate。

Adoption target 仅在下方记录的 exact candidate confirmation 之后修改。

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

无。Active v3 已完成 target verification 与 adoption；`pending_claim_version: 0`。后续任何
evidence、scope、recommendation 或 target 变化都必须创建新的 pending revision 并重新确认。

## Supersession And Reopen Conditions

Active v3 取代 commit `692e8b2` 中未确认的 pending v2 preimage；此前没有 active adopted claim 需要
retire。HyperFrames/Chrome、bundled/generic tables 发生变化，content-addressed custom-font contract
获准，required-language glyph coverage 被纳入 readiness，或 exact same-version evidence 与
preflight 矛盾时，必须 reopen 或 reconfirm。存在未解决的 exact counterexample 时标记
`CONTESTED`；preflight/source distinction 不再能预测 renderer behavior 时标记 `REFUTED`；
HyperFrames 或 caption source owner 变更时标记 `RETIRED`。
