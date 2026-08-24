# Hooks

## Purpose

在 G2 定义第一秒可观察的商业进入点。Hook 是可同步的视觉、语言、copy 和声音合同，不是一句脱离证据的标题。

## Required Components

`hook_contract` 必须包含 `visual_hook`、`dialogue_or_vo_hook`、`copy_hook`、`audio_hook`、`product_presence`（`none`、`tease` 或 `explicit`）、`promise_boundary`、`first_payoff_deadline_seconds` 与 `platform_constraints`。至少一个 component 在第一秒出现，并绑定 beat、Shot 或 audio/copy cue。

visual Hook 可用场景变化、product tease 或可观察问题；dialogue/VO 与 copy 必须逐字或可复核地表达；audio Hook 必须指定 reveal hit、voice entry、music change 或 intentional silence。所有 promise 回指 claim ledger。

## Gates and Stop Conditions

- 没有 first-second observable component，或只写抽象情绪/效果词时，G2 fail closed。
- `promise_boundary` 超出 allowed claim、暗示医疗/治疗或 before/after 时停止。
- 不为了 Hook 伪造物理产品互动、客户证明或 Runtime capability。

## Quick Reference

| Component | Must bind |
| --- | --- |
| Visual | first-second beat/Shot + product state when present |
| Dialogue/VO | claim_id where promise is made |
| Copy | typed commercial role + cue |
| Audio | event/time intent + coverage interval |
