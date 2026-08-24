# Ad Beat Sequences

## Purpose

用因果驱动的 beats 组织 30 秒竖屏广告：Hook -> value -> proof -> payoff/hero -> CTA，而不是固定时长的素材拼盘或 fiction episode。

## Required Structure

每个 `ad_beat` 记录 ordered role、message、duration budget、进入/离开因果、product expectation、copy expectation、audio expectation，以及至少一个 Shot binding。总 duration budget 必须与 `duration_seconds` 在 schema 定义的容差内相等；每个 Shot 也必须反向绑定一个 beat。

格式可以采用 `product_demo`、`presenter_spokesperson`、`lifestyle_use_case`、`comparison`、`problem_solution` 或 `motion_graphics_product`。人物与场景仍以 `talent_plan` 和 `set_plan` 服务广告目的，不产生 episode、serial 或 narrative cliffhanger。

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
