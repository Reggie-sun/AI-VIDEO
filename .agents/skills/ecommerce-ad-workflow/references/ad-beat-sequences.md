# Ad Beat Sequences

## Purpose

用因果驱动的 beats 组织 30 秒竖屏广告：Hook -> value -> proof -> payoff/hero -> CTA，而不是固定时长的素材拼盘或 fiction episode。

## Required Structure

每个 `ad_beat` 记录 ordered role、message、duration budget、进入/离开因果、product expectation、copy expectation、audio expectation，以及至少一个 Shot binding。总 duration budget 必须与 `duration_seconds` 在 schema 定义的容差内相等；每个 Shot 也必须反向绑定一个 beat。

格式可以采用 `product_demo`、`presenter_spokesperson`、`lifestyle_use_case`、`comparison`、`problem_solution` 或 `motion_graphics_product`。Package必须保留exact `ad_format`并应用shared Gate加format profile：`product_demo`需要demonstration；`presenter_spokesperson`需要talent、spoken audio与demo/proof；`comparison`需要used comparison claim与proof；`problem_solution`需要problem beat与demo/proof；`lifestyle_use_case`需要set与demo/proof；`motion_graphics_product`需要graphic reveal与demo/proof，但允许无talent、无dialogue Hook。人物与场景只在格式确实需要时服务广告目的，不产生 episode、serial 或 narrative cliffhanger。

G5为每个`ShotIntent`声明purpose、beat、time window、duration basis、product state、可空talent action、camera intent、presentation/copy/audio bindings与visual strategy need；storyboard必须覆盖每个beat，且beat、Shot与cue双向一致。不要用这些字段重复Runtime timeline或execution state。

## Gates and Stop Conditions

- beat 缺 role/message/duration/causality，或所有 Shot 机械等长却没有广告理由时，不通过 G2/G5。
- intro、demo/payoff、hero shot、CTA/brand closure 缺任一必要商业职责时，返回 blocking QC finding。
- comparison 不满足 truth/platform 条件时停止；motion graphics 仅是 creative intent，必须在 handoff 标注 capability。

## Quick Reference

| Beat question | Required answer |
| --- | --- |
| Why now? | Hook and first payoff deadline |
| Why believe? | claim-linked proof |
| Why this product? | typed presentation state |
| What next? | CTA + end-card binding |
