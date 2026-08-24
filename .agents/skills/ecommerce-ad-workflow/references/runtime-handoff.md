# Runtime Handoff

## Purpose

在 G6 将广告 package 投影为 existing AI-VIDEO authoring proposals、requirements 和 capability gaps。此文件不创建 Runtime、Provider、timeline、renderer 或 lifecycle。

## Projection

`product_truth`/constraints -> `ProductionBrief` proposal + upstream truth attachment；talent -> `Character` proposal；set -> `Scene` proposal；beats/storyboard -> `Storyboard`/`StoryboardBeat` proposal；shot intents -> `Shot` proposal。product source assets 只提出 Registry import/image-generation request；dialogue/VO 只提出 `AudioTrackSpec` request；`DIALOGUE_SUBTITLE` 只提出 `CaptionTrack`/binding request；audio cues 提出 P4 authoring request。

每个 handoff item 必须声明 `classification`：`SUPPORTED_CURRENTLY`、`REQUIRES_SOURCE_GENERATION_STRATEGY`、`REQUIRES_RUNTIME_CAPABILITY`、`REQUIRES_HUMAN_DECISION` 或 `BLOCKED_BY_TRUTH_OR_RIGHTS`，并写明 source package field、requirement/gap、owner 与 unresolved item。

每个 `requirement_id` 必须恰好出现在一个 `classified_gap.requirement_ids` 中，且 gap 与所有 bound requirements 的 `classification` 完全一致。`SUPPORTED_CURRENTLY` 只是 handoff classification，不是可伪造的 Runtime evidence；对 physical interaction，V1 validator 不接受该自我声明。

`blocked_capability_gap` 是 validator diagnostic code，不是第六个 classification。出现该 blocker时保持 package not-ready，并用上述 source-generation / Runtime-capability classification描述缺口。

## Forbidden Fields and Stop Conditions

- handoff 不得包含 Provider name/profile、credential、permit、task ID、Manifest revision、timeline frames/samples、render path、P6 PASS、Final Acceptance、activation 或 execution instruction。
- `PHYSICAL_INTERACTION_REQUIRED`、advertising copy graphics 或其他未实现能力必须如实分类；不得写 unsupported `CompositionSpec` 字段、建立第二 timeline/renderer，或以 prose 隐藏 gap。
- capability/truth/rights owner 或 resolution path 不明确时，不通过 G6。

## Quick Reference

| Package intent | Runtime-facing form |
| --- | --- |
| Product constraints | ProductionBrief proposal, preserve lineage |
| Talent / set | Character / Scene proposal |
| Shot intent | Storyboard / Shot proposal |
| Commercial graphics | explicit capability requirement |
| Exact timing / acceptance | excluded; retained by Runtime owners |
