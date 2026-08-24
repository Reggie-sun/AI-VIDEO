# Audio, Pacing and Coverage

## Purpose

在 G4 为完整广告时长建立 authoring-level audio intent；它不声称完成 P4 mixing、sample timing、loudness 或 P6 质量验证。

## Required Record

每个 beat 声明 dialogue/VO expectation、music presence/energy/transition、SFX 或 reveal hit、ducking、source/generation need，以及与 product/copy event 的同步。`audio_plan.coverage` 必须覆盖 `[0, duration_seconds]`；无 event 的窗口仅在 `intentional_silence=true` 且附 narrative/commercial rationale 时有效。

每条 on-camera line 必须绑定 exact speaker、verbatim line、Shot 和 `lip_sync_required`。每个 native/generated source audio 声明 `keep`、`mute`、`replace` 或 `trim_then_mix` policy；Shot 开头噪声风险要写 trim/fade 意图和 P6 measurement requirement。

## Gates and Stop Conditions

- 中段任何 non-intentional uncovered interval 阻止 `PACKAGE_READY`。
- on-camera speaker、verbatim text、Shot 或 lip-sync requirement 缺失时 fail closed。
- source-audio 或 lead-in noise 无 policy 时停止；Workflow只能请求 trim/fade/P6 measurement，不能声称已经修复实际媒体。

## Quick Reference

| Coverage item | Minimum declaration |
| --- | --- |
| Voice | type, speaker/line when on-camera, Shot |
| Music | presence, energy, transition, ducking |
| SFX | cue + synchronized reveal/product event |
| Silence | exact window + intentional rationale |
| Source audio | keep/mute/replace/trim_then_mix + lead-in plan |
