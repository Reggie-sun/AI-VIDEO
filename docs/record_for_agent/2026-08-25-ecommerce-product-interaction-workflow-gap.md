# Ecommerce Product Interaction Source Preparation Record

Date: 2026-08-25

## Purpose

本文记录 AI-VIDEO 在“人物使用指定真实商品”的电商广告场景中已经落地的 first structural slice，以及仍需真实媒体验证的边界。详细执行合同由 `docs/superpowers/plans/2026-08-25-ai-video-ecommerce-product-interaction-source-preparation.md` 独占；本记录只保存 stable implementation truth、verification 和 guardrails。

## Current Runtime Truth

当前 Runtime 已实现 product-interaction source preparation 的 offline structural closure：

- `AdCreativePlan /2` 将 `PRODUCT_INTERACTION` Shot 纯投影为 `CommercialExecutionProjection`，不创建第二套 creative truth。
- `ProductReferenceSet` 独立绑定 exact Product/Registry bytes；Character、Scene、Wardrobe 和 Accessory identity 保持分离。
- V1 materialization 仅支持 registered local/human-observed PNG import。`P7_GENERATION` 固定 typed BLOCKED，没有 caller callback、Provider submit 或 fallback。
- Manifest `2.12` 保存 request、candidate、review intent/evidence/receipt 和 active approval；`ProductionStateCommitter` 仍是唯一 writer、activation 和 explicit recovery owner。
- Commercial attempt lifecycle invariants 位于 cohesive `_commercial_source_state.py`；`models.py` 保留既有 public enum/model identity 和 Manifest schema composition，避免继续扩张 oversized shared model owner。
- Commercial source review 复用 active P6 `QaPolicy`。Injected authorizer 选择 exact actor，committer 先持久化 content-addressed intent，再 durable consume 并签发 process-local one-use permit；analyzer 不能自行选择 durable PASS 或写 Manifest。
- Exact semantic PASS 才可选择 `ApprovedCommercialSourceBinding`。Approval 与 commercial dependency graph/states 在同一个 final Manifest replace 中 co-activate；Project/Registry/QA policy 变化会清理 active approval 并把 attempt 标为 `STALE`。
- Preparation、candidate、review-intent、analysis 和 approval 的 exact replay 都绑定 caller-supplied request/candidate/approval identity，经 standard loader 重验 full current chain，并保持零 revision/effect。
- Planner strict reopen active approval 和 current `LoadedProductionProject`，生成 provider-neutral requirement `/3`；Router 仅对 exact approved-first-frame product-fidelity I2V requirement 开放 structural selection，T2V、generic reference、wrong/stale approval 均 fail closed。
- Commercial failure classifier 只提出 typed root/boundary；P5 resolver、repair authorization 和 closure ownership 没有迁移。

该 closure 表示“exact registered interaction keyframe 可被授权审查、批准并交给 current Planner/Router”，不表示 generated Shot、整支广告或真实商品质量已经通过。

## Architecture Decision

已实现的 vertical slice 为：

```text
AdCreativePlan product-interaction intent
  -> Commercial execution projection
  -> ProductReferenceSet + Character / Scene constraints
  -> registered interaction-keyframe candidate
  -> authorized product / character / interaction semantic review
  -> ApprovedCommercialSourceBinding
  -> VideoPlanner first-frame I2V requirement
```

保持的 owner/invariant：

- Product identity 独立于 Character、Scene、Wardrobe、Accessory 和 continuity state；
- approved first frame 承载 Product pixels，Product references 不降级成 generic Provider `reference`；
- concrete product-aware Image Provider 仍需后续独立 qualification；
- P6 扩展 source-image target，不创建第二 QA lifecycle；
- source/keyframe/product failures 先分类，再交给 existing Dependency Graph/P5 Repair；
- 没有新建 Registry、第二 writer、timeline、renderer、router 或 repair engine。

## Verification And Evidence

Implementation checkpoint 为 local commit `7cc4ee6`；后续 review-authority/recovery/replay closure 与 canonical docs 由 final task commit 补齐。Fresh executable evidence：

- Commercial/ad/image/P0/paid/structure focused matrix：`190 passed in 30.88s`。
- Review/recovery/Shot 03/04 core：`31 passed in 16.20s`。
- Plan implementation matrix（不含被 unrelated concurrent uncommitted files 污染的 repository-wide policy audit）：`831 passed in 346.02s`。
- Replay/cardinality focused group：`152 passed`；唯一失败是 unrelated staged quality-gate files 导致 current-tree repository-wide policy audit 报告两个 unmapped paths，不属于本 slice。Final exact detached commit snapshot 必须重新通过该 audit。
- Final closure 由 exact immutable commit-range Harness receipt `.agent/harness/runs/ecommerce-product-interaction-source-preparation-final-20260825/receipt.json` 独占；receipt 必须验证 scope、policy、artifact hashes 和 freshness。

AI-VIDEO RAG query `ecommerce product interaction source materialization approved keyframe commercial visual QA` 只作为 discovery/advisory evidence；关键结论均重新核对 current files 和 tests。

本轮没有运行 Provider、ComfyUI、媒体生成、renderer、paid API、credential lookup 或 network research。Tests/Harness 只证明 structural and deterministic behavior，不证明视觉质量、喷雾动作、P6 generated-video PASS 或 Final Acceptance。

## Remaining Work

- Concrete product-aware Image Provider materializer 尚未实现；当前只支持 registered import。
- 仍需独立的 temporal interaction/video product-fidelity QA。
- Concrete Image/Video Provider 对青颜 packaging、苗家女孩 identity、手部遮挡和喷雾动作的表现仍属于 empirical/model-quality uncertainty。
- 任何真实 Shot 04 experiment 都需要新的 explicit authorization 和全部 Provider/egress/budget/permit gates；本轮没有授权或执行该实验。

## Agent Guardrails

- 不得把 `AdCreativeReviewReport.is_ready` 解释为 commercial visual ready。
- 不得把 registered image candidate 解释为 approved interaction source。
- 不得用 prompt 文字、generic reference 或 flat overlay 替代 exact `ProductReferenceSet` 和 approved keyframe。
- 不得因 Provider 支持 reference image 就假定 Product semantic binding 已经存在。
- 不得让 source materializer、reviewer、Router 或 Provider adapter 直接写 activation state。
- 不得在没有 generated-video commercial evidence 时声明“拿起并喷”已闭环。
