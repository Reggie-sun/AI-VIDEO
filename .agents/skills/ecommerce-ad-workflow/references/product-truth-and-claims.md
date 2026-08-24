# Product Truth and Claims

## Purpose

在 G0 固定商品可被广告使用的事实边界。未知、推测或无法回溯来源的信息不能写成 copy、VO、Hook 或 proof。

## Required Record

为每个 SKU 记录 `sku_id`、正式 `product.name`、每个 `source_asset` 的 exact reference 与 rights status，以及每条 fact 的 `fact_id`、可观察内容、`source_ref`。同时列出 `allowed_claims`、`prohibited_claims`、`required_disclaimers` 与 landing-page snapshot/reference（如用户提供）。

每条准备使用的 claim 必须在 claim ledger 中有 `claim_id`、绑定的 `fact_id`/`source_ref`、`status=allowed`、`used_at`（Hook、beat、copy、VO 或 Shot）和 spoken/visual form。Product Truth 冻结后，strategy 与 variants 只能引用，不能改写事实或 claim status。

## Gates and Stop Conditions

- G0 前缺 SKU、正式名称、source asset、rights、fact source 或 claim lineage 时停止。
- 医疗、治疗、未证实功能、absolute claim、伪造认证、虚构 testimonial、未经支持的 before/after 一律禁止；disclaimer 不能把它们转为允许。
- claim 与事实不一致、rights 不明、required disclaimer 无法容纳时，标为 `BLOCKED_BY_TRUTH_OR_RIGHTS`，不进入 Hook 或 handoff。
- 商品图片是 source/reference asset；V1 delivery intent 仍只能是 video。

## Quick Reference

| Need | Minimum evidence |
| --- | --- |
| Product identity | SKU + formal product name |
| Fact | observable statement + source_ref |
| Claim | allowed status + fact/source linkage + used_at |
| Asset | exact reference + rights status |
| Legal boundary | prohibited claims + required disclaimers |
