# Quality Gate Architecture Separation Record

Date: 2026-08-25

## Purpose

本文记录Quality Gate architecture separation的documentation/contract-test checkpoint。它固定Universal Production QA、Domain-specific Acceptance与market outcome的owner边界，避免把pre-submit readiness、Ecommerce authoring readiness或generic P6 layers误解释为完整跨domain acceptance。

本记录不是新的Runtime、Provider、媒体生成、P6 PASS、Final Acceptance、push或release authorization。代码、tests、canonical docs与本轮exact Git/Harness evidence仍是source of truth。

## Current Runtime Truth

当前选择的architecture是：

```text
Gate 1: Universal Production QA
  -> Gate 2: Domain-Specific Acceptance
       -> exactly one selected Domain profile
  -> existing P6 Review / Repair lifecycle
  -> Final Acceptance rollup
```

以上仍不是完整automatic Runtime flow。当前已新增显式、non-persistent、Gate 1-only的
`UniversalQualityGateCoordinator.run_once()`；它不会被background或产品入口自动触发。
Gate 2仍没有accepted typed Domain profile/evidence seam，因此尚不可执行。只有两个top-level
post-media gates；Ecommerce、Drama、AI Comic与future domains是Gate 2 profiles，Final Acceptance
是explicit durable rollup而不是第三个evaluator gate。`ShotReadinessGate`、Ecommerce G0-G7与
`AdCreativeReviewReport`仍是preflight，均不属于这两个post-media gates。

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

### Two-Gate Spec Amendment

后续architecture clarification已提交：

```text
1ab95e4de9e1740cb2fce0ad41344c9fcd5da8f7
docs: define two-stage quality gate contract
```

该commit只包含4个task-owned documentation/control-plane files：

- 新增canonical accepted spec：`docs/superpowers/specs/2026-08-25-ai-video-quality-gate-architecture-separation.md`；
- 更新implementation plan：`docs/superpowers/plans/2026-08-25-ai-video-quality-gate-architecture-separation.md`；
- 在`docs/superpowers/specs/2026-08-21-ai-video-shot-readiness-gate-v3.md`明确Shot Readiness属于pre-submit、位于两个post-media gates之外；
- 在`.agent/harness/docs-contracts.yaml`注册canonical surface及spec-targeted assertions。

Amendment固定只有两个top-level post-media quality gates：Gate 1 `Universal Production QA`与Gate 2 `Domain-Specific Acceptance`。Ecommerce、Drama、AI Comic与future domains是Gate 2 profiles；`Final Acceptance`是explicit durable rollup，不是第三个quality evaluator gate。Current owner APIs中的hard validators只在对应显式action内自动执行，当前没有product-level automatic coordinator。Target coordinator仍须显式调用，按Gate 1再exactly one Gate 2 profile的顺序执行；不得background/watch、自动repair、自动activation、自动`Final Acceptance`或profile fallback。

Future full coordinator还必须在Gate 1 PASS后消费一个preselected、content-addressed Domain
profile；缺失、无效或coverage不完整时必须在任何Gate 2 effect前fail closed。Gate 1的
Universal profile minimum与`QaPolicy.required_layers`coverage现已在下述显式one-shot slice中强制。

本次`reviewer_xhigh`首次re-review为`reject`：plan中的domain headings仍可能被读成额外top-level gates，且future selected `QaPolicy`可以省略universal minimum。修正profile terminology、two-gate assertions与Universal profile coverage约束后，scoped re-review verdict为`accept`，无blocking或non-blocking concerns。

### Gate 1 Runtime Checkpoint

本轮在不触碰其他writer占用的Production integration files前提下，新增：

- `src/ai_video/production/quality_gate_coordinator.py`：content-addressed
  `UniversalQaProfile`、exact `UniversalQaContext`、fail-closed coverage preflight与显式
  `UniversalQualityGateCoordinator.run_once()`；
- `tests/test_production_quality_gate_coordinator.py`：profile minimum、tamper、policy coverage、
  ordering、stale/unknown outcome、STOP与identity binding regressions；
- Spec、plan与`.agent/harness/docs-contracts.yaml`同步current Gate 1-only Runtime边界。

该coordinator只执行preselected Gate 1 hard checks与required P6 review layers。它在任何effect
前strict reopen profile、context与policy；runner只收到reopened profile/context；失败、stale、
unknown outcome或coverage缺失立即STOP且不retry。PASS只产生
`eligible_for_domain_gate=true`的in-memory result，不写Manifest、不自动repair、activation、
Gate 2或Final Acceptance。Result分别绑定profile/context、selected QaPolicy与
context-expected QaPolicy identity；invalid declared hash返回`NOT_EVALUATED`而不是令错误路径失败。

Strict red-green evidence包括：最初module missing的6个失败、profile minimum的7个失败、
unknown-outcome的2个失败、unsealed policy的1个失败、reviewer提出的4个identity/tamper失败、
最后3个fail-closed失败，以及domain eligibility detached-construction的1个失败。最终focused
suite为`60 passed`；最终`reviewer_xhigh` verdict为`accept`，无blocking或non-blocking concern。

原`.agent/harness/policy.yaml`ownership blocker在其writer提交并释放后解除。本session随后把
coordinator source/test映射到`production_review`，同步contract matrix、runtime baseline与roadmap，
并提交exact 9-file implementation：

```text
eba888f80b630cab3a5cd487027e2a9cc4e6d9b4
feat: add universal quality gate one-shot
```

Exact staged Harness `.agent/harness/runs/quality-gate-one-staged-20260825-v4/receipt.json`
状态为PASS：Architecture Gate 0 findings、Harness tests `185 passed`、Production Review tests
`606 passed`。Receipt的scope、policy、artifacts与snapshot均匹配；共享checkout在run期间对
matrix/baseline增加了另一slice的unstaged内容，因此live verifier的freshness为false，但这些内容
未进入`eba888f`且未被覆盖。

随后exact commit-range run
`.agent/harness/runs/quality-gate-one-commit-eba888f-20260825-v1/receipt.json`的全部6个checks也
实际PASS，但另一个session在run期间将`HEAD`推进到`3323a2d`，使Harness meta-check记录
`workspace_stable_confirmed=false`、`snapshot_matches=false`并将receipt status标为failed。
该receipt只证明各check结果，不是completion proof。

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

Two-gate amendment的exact immutable commit-range receipt：

```text
.agent/harness/runs/quality-gate-two-stage-spec-commit-1ab95e4-v1/receipt.json
```

该run针对exact range：

```text
fd163be12db3a0b1ad500d20c9512380952fff5f..
1ab95e4de9e1740cb2fce0ad41344c9fcd5da8f7
```

结果PASS：Documentation Contract Gate与policy audit通过，Harness tests `184 passed`。Receipt verifier确认`artifact_integrity=true`、`complete_completion_proof=true`、`fresh=true`、`fresh_for_snapshot=true`、`scope_paths_match=true`、`snapshot_matches=true`与`cleanup_verified=true`。

Gate 1-only current checkpoint evidence：

- `tests/test_production_quality_gate_coordinator.py`与`tests/test_production_review.py`：
  `60 passed`；
- Documentation Contract Gate：PASS；
- scoped staged `git diff --check`：PASS；
- independent `reviewer_xhigh`：`accept`；
- `.agent/harness/runs/quality-gate-one-staged-20260825-v3/receipt.json`：integrity与exact
  snapshot binding有效，但`passed=false`、`complete_completion_proof=false`，原因是上述
  `policy_audit_check` blocker。该failed receipt不是completion proof。
- `.agent/harness/runs/quality-gate-one-staged-20260825-v4/receipt.json`：全部required checks
  PASS；Harness tests `185 passed`、Production Review tests `606 passed`、Architecture Gate PASS。
- `.agent/harness/runs/quality-gate-one-commit-eba888f-20260825-v1/receipt.json`：全部check
  records PASS，但并发`HEAD`移动导致overall status failed；不得描述为complete completion proof。

## Concurrent Workspace Divergence

在`3914044`提交并完成immutable commit-range Harness期间，另一个writer继续修改了：

- `docs/agent-primary-contract-matrix.md`；
- `docs/v0.2-agentic-production-roadmap.md`；
- `docs/v0.2-runtime-baseline.md`。

这些post-commit changes属于独立commercial source preparation slice，不在`3914044`或上述receipt snapshot中。本session未覆盖、stage、commit或采纳它们。由于current shared checkout在相同task-doc paths上已dirty，commit-range receipt的post-run verifier同时报告`scope_worktree_clean=false`、`fresh=false`和`fresh_for_snapshot=false`；这不是receipt artifact、policy、scope或immutable snapshot mismatch，而是当前workspace在proof之后发生了same-file divergence。

## Remaining Risks Or Next Work

- Future Ecommerce post-media acceptance若要进入P6，必须另建active spec/plan，增加preselected content-addressed domain profile、rubric/version、stable requirement IDs、sealed authoring-truth hash binding、exact target/coverage与required `FAIL` / `NOT_EVALUATED` fail-closed aggregation。
- Gate 1 one-shot coordinator与policy mapping已提交为`eba888f`，但完整two-stage product caller、
  durable Gate profile/evidence binding与Gate 2 typed Domain seam仍需独立accepted slice。
- Product-level automatic caller、durable profile/evidence binding与Gate 2 typed Domain seam仍未实现；
  当前Gate 1必须由caller显式调用，不能声称会自动触发完整two-stage flow。
- Future Drama adapter必须等formal Drama workflow、authoring artifact与rubric被独立接受；不得复用Ecommerce rubric或physical continuity冒充narrative continuity。
- 当前generic `SEMANTIC` envelope仍可能接受policy-authorized `semantic_match`，所以本slice只证明authoring outputs不直接编码Production acceptance及当前无canonical bridge，不证明typed misuse prevention已实现。
- Current working tree的post-commit same-file divergence需要其owner自行完成、commit或清理；不得为刷新本receipt而覆盖或暂存该work。
- 本轮Gate 1 implementation、policy与canonical docs已提交到local `main`；未push、未release。
- `1ab95e4`仅存在于local `main`，未push、未release、未publish；本session没有live/paid/Provider/media call。
- 本轮`retrieve-ai-video-memory --scope all`返回fresh current-contract hits与stale last-good Superpowers fragments，并只排队local derived-index refresh；retrieval是advisory，不属于Runtime或acceptance evidence。

## Agent Guardrails

- `ShotReadinessGate.READY`不等于post-media quality、P6、activation或Final Acceptance。
- Ecommerce、Drama、AI Comic与future domains只能作为Gate 2 profiles，不得升级为额外top-level gates或并行canonical owners。
- `Final Acceptance`是两个Gate之后的explicit durable rollup，不得描述或实现为第三个quality evaluator gate。
- `AdQCReport.ready`不等于whole-ad media acceptance；`AdCreativeReviewReport.is_ready`不等于Production verdict。
- Base AI Comic selected-policy closure不等于Drama QC。
- Domain Skill只能提出authoring artifacts、rubric/requirements或future evidence proposals；不得写Manifest、创建Production receipt或签发Final Acceptance。
- Market outcome不能反推quality PASS，也不能用aggregate score抵消required failure或missing coverage。
- 对`3914044`做后续验收时使用immutable commit/range；不要把current dirty same-file additions误归入该commit或其Harness evidence。
