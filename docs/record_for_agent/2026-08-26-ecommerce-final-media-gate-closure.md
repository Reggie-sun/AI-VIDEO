# Ecommerce Final-Media Gate Closure Record

Date: 2026-08-26

## Purpose

本文记录 Ecommerce final-media Runtime 闭环的实现 checkpoint。它修复的不是某个模型或 FFmpeg operation，而是 exact final candidate 的 ownership、evidence freshness 与 acceptance ordering。

本记录不把既有青颜 V3 MP4 追认成 Production candidate，也不产生新的 Provider、媒体、人类视觉质量、push、release 或 repository 外 publication evidence。代码、tests、Manifest state 与 exact Harness receipt 仍是 source of truth。

## Current Runtime Truth

`run_ecommerce_ad_generation()` 继续只表示 Provider Shot-stage execution；其 `complete=True` 不表示 composition、Gate、P6、Final Acceptance 或 deliverable。

新的唯一 public Ecommerce Production application entry 是 `run_ecommerce_ad_production()`：

1. 在任何 Shot / Provider 或 render effect 前，验证 exact Provider Shot set、concrete `EcommerceVideoGenerationFacade`、facade `project_root` 与 sealed handoff identity。
2. 复用 `run_ecommerce_ad_generation()` 的 sequential Shot barrier；前一 Shot 未通过 current commercial PASS/activation 时，不执行后一 Shot。
3. 调用 caller 预选的 canonical render activator；该 callback 不取得任意 final MP4 acceptance authority。
4. private final-media closure 从同一个 `ProductionStateCommitter` root 重新打开 exact active render、output bytes 与 content-addressed `ResolvedTimeline`，并从 real `VideoGenerationService` 重新打开 ordered activated Shot checkpoints。
5. closure 内部运行 `UniversalQualityGateCoordinator.run_once()`；caller不能注入 `project_root`、timeline、Gate 1 context 或 Gate 1 PASS result。
6. `EcommerceQualityGateCoordinator` 将 Gate 1 identity、sealed handoff、Shot lineage、`CompositionSpec`、exact active timeline/output SHA-256、selected Ecommerce profile/policy与durable `ReviewRequest` 封装成 content-addressed whole-ad acceptance target。
7. private P6 adapter只通过existing `begin_review()`、one-use `run_review_analysis()` 与 `record_review_receipt()`提交 `SEMANTIC` evidence。Ecommerce semantic payload缺少exact target envelope时，P6 adjudication固定为`NOT_EVALUATED`。
8. 只有Gate 2 PASS且selected policy的全部current required receipts均为PASS时，才调用existing `ProductionStateCommitter.record_final_acceptance()`；只有该 durable Final Acceptance 成功后，`EcommerceAdProductionResult.complete`才为`True`。

`ProductionStateCommitter`仍是唯一 Manifest/P6/Final Acceptance writer；没有新增 schema、第二 timeline、第二 renderer、第二 lifecycle 或自动 background acceptance。

## Evidence Freshness Invariant

任何 post-gate media mutation 都产生新的 acceptance target。Canonical rerender会清空旧active review receipts与Final Acceptance；直接篡改active render bytes会在current target reopen时fail closed。Gate 2同时检查active render持有的timeline content hash与重新计算的timeline fingerprint，不能用声明相同technical windows但bytes/完整timeline不同的对象继承旧结论。

因此 FFmpeg、slow motion、interpolation、freeze、transition、audio remix或custom timing本身不是禁止项；它们若改变最终bytes或timeline，就必须作为新的exact canonical candidate重新走Gate 1、Ecommerce Gate 2、P6与Final Acceptance。

## Verification And Independent Review

本轮使用deterministic local fixtures与fake HyperFrames runner验证canonical `CompositionSpec -> ResolvedTimeline -> active render -> Gate 1 -> Ecommerce Gate 2 -> P6 -> Final Acceptance`。没有调用Provider或生成新的真实媒体。

已验证的focused evidence包括：

- Gate 2 exact target、stale Gate 1、active timeline mismatch、permit replay、invalid evaluator durable `NOT_EVALUATED`与P6 request/output binding。
- Canonical no-Provider Ecommerce Production path自动调用Gate 1/Gate 2/P6/Final Acceptance。
- Active render bytes mutation在任何Gate evaluator effect前fail closed。
- Protocol-compatible custom facade在任何Shot/Provider或render effect前被public Production entry拒绝。
- Final focused runs：`99 passed`与后续scoped `22 passed`。

同一`reviewer_xhigh`经过多轮root/timeline/Shot/Gate injection、caller ownership与pre-effect safety review，最终verdict为`accept with concerns`，blocking issues为None。

## Superseded Current-Facing Claims

本记录 supersede 以下旧记录中“Ecommerce whole-ad Gate 2 / product caller仍未实现”的 current-facing 状态；旧记录的历史实现、测试、媒体与authorization边界保持有效：

- `docs/record_for_agent/2026-08-25-quality-gate-architecture-separation.md`
- `docs/record_for_agent/2026-08-26-qingyan-ecommerce-post-media-gate-m1-m3.md`

Milestone 4 live pilot仍未在本轮执行，但它不再是deterministic Gate 2/P6 Runtime implementation的前置条件。它仍是青颜或其他具体广告的empirical/model-quality acceptance前置证据。

## Remaining Risks And Boundaries

- `activate_final_render`仍是caller-supplied `Callable`；acceptance correctness由后续exact active render/timeline/output reopen保护，但callback自身的side effects不由本slice证明。后续如出现真实ownership defect，可再收紧为typed canonical activator contract。
- 当前zero-effect regression覆盖custom protocol facade；真实`EcommerceVideoGenerationFacade` wrong-root case由同一preflight branch拒绝，但尚无单独fixture test。
- Runtime只能控制canonical Production/P6/Final Acceptance truth，不能阻止human或repository外tool直接分发任意development MP4。
- 既有`artifacts/qingyan-miao-ad-20260826-v3/`没有被迁移、重渲染或重新验收，仍无Gate 2/P6/Final Acceptance evidence。
- 本轮没有live/paid/local Provider call、真实媒体生成、`video-analysis`或human visual verdict；RAG derived index也没有刷新。

## Agent Guardrails

- 不得把`EcommerceAdGenerationResult.complete`称为deliverable completion。
- 不得公开private final-media closure或P6 adapter形成alternate path。
- 不得让caller注入timeline、Gate 1 PASS或arbitrary MP4进入canonical acceptance。
- 不得把Gate/Harness PASS外推为青颜V3主观质量、market outcome、push、release或publication。
