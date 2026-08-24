# Creative Variants

## Purpose

在 master Product Truth 和 strategy 不变时，构建可比较的 creative hypotheses；variant 不是 Provider retry、seed 更换、repair attempt 或任意不同媒体。

## Required Record

每个 variant 必须只声明一个 `changed_variable`，可选值为 Hook、opening visual、advertising angle、proof order、CTA、presenter profile、pacing 或 duration cut。另需 `baseline_value`、`variant_value`、complete `held_constants`、`hypothesis` 与 `required_new_assets`。

held constants 至少覆盖 product truth、allowed claims、rights/disclaimers、objective、platform constraints、delivery intent、核心 CTA destination，以及没有被声明变化的 master strategy 部分。

## Gates and Stop Conditions

- changed variable 数量不等于一、held constants 不完整或新 asset 无 rights/source plan 时，不产生 variant package。
- 不把 Provider retry、random seed、repair、selected media difference、performance result或 campaign optimization当作 variant。
- variant 不得改写 Product Truth、claim status 或禁止边界；若需要新 promise，先回到 G0/G1。

## Quick Reference

| Allowed experiment | Hold constant |
| --- | --- |
| Opening visual | truth, angle, proof, CTA |
| CTA wording | truth, Hook, proof order |
| Proof order | facts, claims, platform rules |
| Pacing/duration cut | core message and delivery=video |
