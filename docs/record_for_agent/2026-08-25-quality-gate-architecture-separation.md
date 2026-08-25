# Quality Gate Architecture Separation Record

Date: 2026-08-25

## Purpose

本文记录Quality Gate architecture separation的documentation/contract-test checkpoint。它固定Universal Production QA、Domain-specific Acceptance与market outcome的owner边界，避免把pre-submit readiness、Ecommerce authoring readiness或generic P6 layers误解释为完整跨domain acceptance。

本记录不是新的Runtime、Provider、媒体生成、P6 PASS、Final Acceptance、push或release authorization。代码、tests、canonical docs与本轮exact Git/Harness evidence仍是source of truth。

## Current Runtime Truth

当前选择的architecture是：

```text
Universal Production QA
  + Domain-specific Acceptance Gate
  -> existing P6 Review / Repair / Final Acceptance lifecycle
```

- Existing Registry、media/candidate validators、`ResolvedTimeline`、composition/render、audio/caption owners继续负责universal hard correctness。
- P6 `TECHNICAL`、`LAYOUT`、`STRATEGY`、`SEMANTIC`继续是policy-selected review envelopes；`FINAL_ACCEPTANCE`只由`ProductionStateCommitter.record_final_acceptance()`汇总exact fresh required receipts。
- `STRATEGY`当前只消费reported `evaluated_strategy_ids`与`strategy_mismatch`，不证明advertising或narrative strategy coverage。
- `SEMANTIC`当前仍是policy-authorized evaluator/human + generic `semantic_match`；它尚未type-bind domain、rubric、sealed authoring truth或requirement coverage。
- `AdQCReport.ready`只直接编码Ecommerce authoring readiness；`AdCreativeReviewReport.is_ready`只直接编码deterministic handoff integrity且`production_verdict=None`。当前不存在把这些outputs转换为P6 evidence的canonical bridge，但Runtime也尚未type-enforce禁止错误转换；该gap属于future typed seam。
- Base AI Comic E2E的selected policy只要求`QaLayer.LAYOUT`且`semantic_requirement="optional"`，所以其Final Acceptance只证明该exact selected-policy closure，不是Drama semantic acceptance。
- Production physical/perceptual continuity与future Drama motivation、causality、emotional progression、setup/payoff continuity保持不同owner。
- CTR、CVR、CPA、ROAS、hold rate、retention等market metrics不属于current Production acceptance，也不能由Ad QC、P6或Final Acceptance预测。

## Session Work And Decisions

Implementation commit：

```text
3914044045c7a994215d235b6ddcb25e94363235
docs: separate domain quality gate ownership
```

该commit只包含10个task-owned files：

- canonical architecture/runtime/future routing：`docs/agent-primary-contract-matrix.md`、`docs/v0.2-runtime-baseline.md`、`docs/v0.2-agentic-production-roadmap.md`；
- accepted implementation plan：`docs/superpowers/plans/2026-08-25-ai-video-quality-gate-architecture-separation.md`；
- Ecommerce authoring boundaries：`.agents/skills/ecommerce-ad-workflow/SKILL.md`、`references/ad-qc.md`、`references/runtime-handoff.md`；
- executable boundary evidence：`tests/test_ecommerce_ad_workflow_skill.py`、`tests/test_production_review.py`、`tests/test_production_base_ai_comic_e2e.py`。

没有修改`src/ai_video/**`、Manifest/schema、`QaLayer`、review artifacts、candidate activation、timeline、renderer、Provider或paid/cloud path。`tests/test_production_ad_creative.py`及commercial source preparation的pre-existing/concurrent changes均未stage或commit。

Independent `reviewer_xhigh`首次verdict为`reject`，指出两个真实问题：plan仍写implementation未开始，以及“authoring outputs绝对不能成为P6 evidence”超出current generic `SEMANTIC` contract能证明的范围。修正Status、plan claims、runtime baseline与test命名后，scoped re-review为`accept with concerns`；唯一concern是必须取得exact commit-range Harness proof。

## Verification And Evidence

Parent/shared-checkout focused verification：

- plan指定五文件suite：`159 passed`；
- changed assertions：`4 passed`；
- Documentation Contract Gate：PASS；
- policy audit：无unmapped、unverified、unreferenced或missing check-test path；
- `git diff --check`：PASS。

Exact staged snapshot receipt：

```text
.agent/harness/runs/quality-gate-architecture-separation-20260825-v1/receipt.json
```

该run PASS：Harness tests `184 passed`、Production contracts `2650 passed, 3 skipped, 1003 deselected`、CLI/config `13 passed`、Production review `583 passed`、Ecommerce skill `63 passed`、Architecture Gate PASS。Commit前receipt verifier的integrity、policy、scope、snapshot、freshness与cleanup flags全部为`true`；commit后index清空使该staged-mode receipt按设计不再fresh。

Exact immutable commit-range receipt：

```text
.agent/harness/runs/quality-gate-architecture-separation-commit-3914044-v1/receipt.json
```

该run针对exact range：

```text
2500bbb7254ed5fb2ca936437f636df9e626e44f..
3914044045c7a994215d235b6ddcb25e94363235
```

同样PASS：Harness tests `184 passed`、Production contracts `2650 passed, 3 skipped, 1003 deselected`、CLI/config `13 passed`、Production review `583 passed`、Ecommerce skill `63 passed`、Architecture Gate PASS。Post-run verifier确认`artifact_integrity=true`、`complete_completion_proof=true`、`inspection_matches=true`、`policy_matches=true`、`scope_paths_match=true`与`snapshot_matches=true`。

## Concurrent Workspace Divergence

在`3914044`提交并完成immutable commit-range Harness期间，另一个writer继续修改了：

- `docs/agent-primary-contract-matrix.md`；
- `docs/v0.2-agentic-production-roadmap.md`；
- `docs/v0.2-runtime-baseline.md`。

这些post-commit changes属于独立commercial source preparation slice，不在`3914044`或上述receipt snapshot中。本session未覆盖、stage、commit或采纳它们。由于current shared checkout在相同task-doc paths上已dirty，commit-range receipt的post-run verifier同时报告`scope_worktree_clean=false`、`fresh=false`和`fresh_for_snapshot=false`；这不是receipt artifact、policy、scope或immutable snapshot mismatch，而是当前workspace在proof之后发生了same-file divergence。

## Remaining Risks Or Next Work

- Future Ecommerce post-media acceptance若要进入P6，必须另建active spec/plan，增加preselected content-addressed domain profile、rubric/version、stable requirement IDs、sealed authoring-truth hash binding、exact target/coverage与required `FAIL` / `NOT_EVALUATED` fail-closed aggregation。
- Future Drama adapter必须等formal Drama workflow、authoring artifact与rubric被独立接受；不得复用Ecommerce rubric或physical continuity冒充narrative continuity。
- 当前generic `SEMANTIC` envelope仍可能接受policy-authorized `semantic_match`，所以本slice只证明authoring outputs不直接编码Production acceptance及当前无canonical bridge，不证明typed misuse prevention已实现。
- Current working tree的post-commit same-file divergence需要其owner自行完成、commit或清理；不得为刷新本receipt而覆盖或暂存该work。
- `3914044`仅存在于local `main`，未push、未release、未publish；本session没有live/paid/Provider/media call。
- 本轮`retrieve-ai-video-memory --scope all`返回fresh current-contract hits与stale last-good Superpowers fragments，并只排队local derived-index refresh；retrieval是advisory，不属于Runtime或acceptance evidence。

## Agent Guardrails

- `ShotReadinessGate.READY`不等于post-media quality、P6、activation或Final Acceptance。
- `AdQCReport.ready`不等于whole-ad media acceptance；`AdCreativeReviewReport.is_ready`不等于Production verdict。
- Base AI Comic selected-policy closure不等于Drama QC。
- Domain Skill只能提出authoring artifacts、rubric/requirements或future evidence proposals；不得写Manifest、创建Production receipt或签发Final Acceptance。
- Market outcome不能反推quality PASS，也不能用aggregate score抵消required failure或missing coverage。
- 对`3914044`做后续验收时使用immutable commit/range；不要把current dirty same-file additions误归入该commit或其Harness evidence。
