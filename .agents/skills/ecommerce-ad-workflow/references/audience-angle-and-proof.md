# Audience, Angle and Proof

## Purpose

在 G1 把已冻结的 Product Truth 转成单一、可证明的商业主张，而不是以泛化人设或未证实卖点填补信息空白。

## Required Fields

`audience` 至少包含 target consumer、use context、pain point 与 desired outcome；`platform` 包含 placement 与 content constraints；`objective` 明确为 awareness、consideration 或 conversion 等目标。`ad_strategy` 必须记录 audience、pain point、angle、promise、proof boundary、objection handling 和 objective。

promise 必须引用 claim ledger；proof 只能使用对应 Product Truth fact、可授权 source asset 或明确的 disclaimer。选择 `comparison` 格式前，先确认 Product Truth 和 platform rule 都允许比较对象、措辞与证据。

## Gates and Stop Conditions

- audience、pain point、angle、promise、proof、objective 任一互相矛盾时，不得通过 G1。
- 如果 objection 只能靠夸大、医疗/治疗暗示或未验证 testimonial 回答，停止并回到 Product Truth。
- 不把 UGC testimonial 作为默认证据路线；不得发明消费者经历、认证或效果数据。

## Quick Reference

| Strategy link | Required trace |
| --- | --- |
| Pain point -> outcome | target consumer + use context |
| Promise -> proof | claim_id -> fact/source_ref |
| Proof -> copy/shot | beat and cue binding |
| Objection | supported response or explicit unresolved item |
