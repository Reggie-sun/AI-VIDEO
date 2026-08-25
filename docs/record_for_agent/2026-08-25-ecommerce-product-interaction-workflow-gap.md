# Ecommerce Product Interaction Workflow Gap Record

Date: 2026-08-25

## Purpose

本文记录 AI-VIDEO 在“人物使用指定真实商品”的电商广告场景中的 current architecture boundary，以及本轮形成的第一个 P0 implementation direction。详细执行合同由 `docs/superpowers/plans/2026-08-25-ai-video-ecommerce-product-interaction-source-preparation.md` 独占；本记录不复制 plan，也不把 proposed behavior描述成 implemented Runtime。

## Current Runtime Truth

当前系统已经具备两端能力，但没有形成 product-interaction production closure：

- Ecommerce authoring和 `AdCreativePlan` 能表达 Product Truth、ad beats、product presentation、commercial graphics、audio和 CTA。
- P7/P8、Asset Registry、`ProductionStateCommitter`、Dependency Graph、VideoPlanner、Shot Router、Providers、P6 Review、P5 Repair、`ResolvedTimeline` 和 HyperFrames都有真实实现。
- `ProductPresentationMode.IN_SCENE_PROVIDER` 当前要求 caller预先提供 `SourceGenerationEvidencePointer`；`compile_ad_creative_plan()` 只验证 source layer已经存在，不创建或审查它。
- `CompiledAdCreativeHandoff` 没有 commercial execution class、reference pack、source materialization request、approved source binding或 canonical `VideoPlanningRequest` connector。
- `AssetRole`、`SemanticReferenceRole` 和 Router context没有独立 Product identity；商品 reference不能与 Character/Scene/generic reference可靠区分。
- P6 current semantic/continuity evidence没有 product packaging、Logo/label、wardrobe/accessory或 hand-object interaction measurement contract。
- P5 Repair能执行 exact approved closure，但 failure type和 root owner仍由 caller提供。

因此“existing source evidence can be consumed”不能解释为“Runtime can materialize and approve exact character + product interaction source”。当前 flat overlay也不能满足 physical interaction requirement；这一点已经 fail closed，不是缺口。

## Architecture Decision

第一优先事项固定为 product-aware approved interaction-keyframe vertical slice：

```text
AdCreativePlan product-interaction intent
  -> Commercial execution projection
  -> ProductReferenceSet + Character / Scene constraints
  -> interaction-keyframe candidate
  -> product / character / interaction semantic review
  -> ApprovedCommercialSourceBinding
  -> VideoPlanner first-frame I2V
```

最小演进原则：

- Product identity独立于 Character、Scene、Wardrobe、Accessory和 continuity state；
- first slice以 approved first frame承载 Product pixels，不把 Product reference降级成 generic Provider `reference`；
- imported keyframe是 first supported materialization lane；concrete product-aware Image Provider需要后续独立 qualification；
- P6扩展 source-image target，不创建第二 QA lifecycle；
- source/keyframe/product failures先分类，再交给 existing Dependency Graph/P5 Repair；
- 不新建 Registry、writer、timeline、renderer、router或 repair engine。

## Verification And Evidence

本轮结论来自 current checkout `3c9dc852969ac0bc3ae3cb6427d31fc1ba4d580b` 的源码、tests和 canonical docs：

- `src/ai_video/production/ad_creative_types.py`、`ad_creative.py`、`ad_creative_review.py`；
- `src/ai_video/planning/_planner_models.py`、`_asset_readiness.py`、`video_planner.py`；
- `src/ai_video/production/video_requirement.py`、`_video_requirement_routing.py`、`shot_router.py`、`video_compiler.py`；
- `src/ai_video/production/image.py`、`image_import.py`、state-commit modules；
- `src/ai_video/production/review.py`、`models.py`、`_state_commit_repair.py`；
- current Provider capability/adapter implementations和相关 tests。

AI-VIDEO RAG query `ecommerce product interaction source materialization approved keyframe commercial visual QA` 返回 fresh current-contract、roadmap和 prior-plan命中；它只作为 discovery/advisory evidence，重要结论均重新核对 current files。Existing codegraph index能确认 `VideoPlanner`、`ProductionStateCommitter` 的 broad caller/relationship surface，但未包含较新的 `ad_creative.py`；该部分使用 current filesystem和 exact symbol search核对，未因本记录重建 index。

本轮没有运行 Provider、ComfyUI、媒体生成、renderer、paid API、credential lookup或 network research。Plan/documentation verification不证明视觉质量、喷雾动作、P6 generated-video PASS或 Final Acceptance。

## Remaining Work

- Implementation尚未开始；new contracts、Manifest migration、P6 source review、Planner/Router bridge和 repair classification均仍是 proposed。
- First slice完成后仍需独立的 temporal interaction/video product-fidelity QA。
- Concrete Image/Video Provider对青颜 packaging、苗家女孩 identity、手部遮挡和喷雾动作的表现仍属于 empirical/model-quality uncertainty。
- 任何真实 Shot 04 experiment都需要新的 explicit authorization和全部 Provider/egress/budget/permit gates。

## Agent Guardrails

- 不得把 `AdCreativeReviewReport.is_ready` 解释为 commercial visual ready。
- 不得把 registered image candidate解释为 approved interaction source。
- 不得用 prompt文字、generic reference或 flat overlay替代 exact ProductReferenceSet和 approved keyframe。
- 不得因 Provider支持 reference image就假定 Product semantic binding已经存在。
- 不得让 source materializer、reviewer、Router或 Provider adapter直接写 activation state。
- 不得在没有 generated-video commercial evidence时声明“拿起并喷”已闭环。
