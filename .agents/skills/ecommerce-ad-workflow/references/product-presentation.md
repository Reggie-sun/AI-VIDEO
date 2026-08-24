# Product Presentation

## Purpose

在 G3 为每次商品出现指定真实的商业用途与可行呈现模式；商品不是任意位置的 PNG overlay。

## Required Record

每项 `product_presentation` 必须有 beat、Shot、start intent、duration intent、role、mode、product source identity、talent interaction、occlusion need、lighting/shadow need、copy cue、audio cue 与 fallback policy。role 只使用 `INTRO`、`DEMONSTRATION`、`BENEFIT_PROOF`、`HERO_SHOT` 或 `CTA_SUPPORT`；mode 使用 `IN_SCENE_GENERATED`、`GRAPHIC_REVEAL`、`DEDICATED_HERO_SHOT` 或 `PHYSICAL_INTERACTION_REQUIRED`。

`GRAPHIC_REVEAL` 必须明确承认 graphic layer；`DEDICATED_HERO_SHOT` 是独立、受控的产品画面。`IN_SCENE_GENERATED` 必须说明场景/人物如何自然承接 source media。

## Gates and Stop Conditions

- 首次出现、demo/payoff、hero/CTA 任一无 typed role/mode 时阻止 G3。
- `PHYSICAL_INTERACTION_REQUIRED` 若缺 source-generation strategy 或 verified Runtime capability，validator 返回 blocker code `blocked_capability_gap`；handoff requirement仍分别使用合法 classification `REQUIRES_SOURCE_GENERATION_STRATEGY` 或 `REQUIRES_RUNTIME_CAPABILITY`。V1 没有可独立重开的 authoritative evidence seam，且 current Runtime 未实现 verified physical interaction，因此即使 package 自称 `SUPPORTED_CURRENTLY` 也必须 fail closed；未来放行需要独立 contract/evidence slice。不得把 blocker code写成 classification，也不得降级为假装手持、遮挡、透视、shadow 或 tracking 的 flat overlay。
- fallback 仅可切换成明确 graphic treatment 或 dedicated hero shot，并须重新批准 creative intent；不能静默改变。

## Quick Reference

| Need | Valid mode |
| --- | --- |
| Natural in-scene use | IN_SCENE_GENERATED |
| Honest graphic entrance | GRAPHIC_REVEAL |
| Controlled product focus | DEDICATED_HERO_SHOT |
| Hand/contact/occlusion | PHYSICAL_INTERACTION_REQUIRED + capability gate |
