# Ad QC

## Purpose

G7 是 authoring preflight：检查 package 的真相、广告逻辑和 handoff honesty。它不评价真实 compositing、lip-sync、audio stream、watchability、P6、Final Acceptance 或投放效果。

## Blocking Checklist

1. 每个 used claim 是否回溯 Product Truth source？
2. 正式 product name 是否至少 visible 或 audible？
3. Hook、benefit、proof、CTA 是否一致且各自有 cue？
4. intro、demo/payoff、hero shot、CTA 与 brand closure 是否各有 beat/Shot？
5. presentation mode 是否诚实，未把 graphic overlay 冒充 physical interaction？
6. presenter action、source framing、lighting/occlusion 是否有可执行空间或明确 gap？
7. `DIALOGUE_SUBTITLE` 是否与 commercial roles 分离，并具 hierarchy/safe-area/avoidance？
8. audio coverage、on-camera binding、source-audio policy、lead-in P6 requirement 是否完整？
9. Shot duration 是否由 beat rationale 驱动，而非机械等长？
10. Runtime capability gap 是否已分类，未被 fallback 或 prose 隐藏？
11. Package `ad_format`是否与source input一致，且对应Gate Profile已经闭合？

## Decision

任一缺证据、缺 trace、未覆盖 audio window、缺 CTA/end card、缺 product presentation，或未分类 capability gap 即为 blocking finding，回到对应 G0-G6。只有无 blocking finding 才能让`AdQCReport.ready=true`并标记`PACKAGE_READY`；该verdict只关闭Ecommerce authoring preflight。

`AdQCReport.ready`不得创建或冒充`ReviewReceipt`、`FinalAcceptanceReceipt`、Production verdict、Manifest mutation、candidate activation或whole-ad post-media acceptance。它也不预测CTR、CVR、CPA、ROAS、hold rate、retention或其他market outcome；future media acceptance必须由另行批准的typed Runtime seam把exact domain/rubric/requirement/media evidence重新绑定到existing P6 lifecycle。

## Quick Reference

| Finding type | Route back to |
| --- | --- |
| Truth/rights/claim | G0 |
| Audience/promise/proof | G1 |
| Hook/beat causality | G2 |
| Presentation feasibility | G3 |
| Copy/audio/closure | G4 |
| Traceability | G5 |
| Ownership/capability | G6 |
