# Audio, Pacing and Coverage

## Purpose

在 G4 为完整广告时长建立 authoring-level audio intent；它不声称完成 P4 mixing、sample timing、loudness 或 P6 质量验证。

## Required Record

每个 beat 声明 dialogue/VO expectation、music presence/energy/transition、SFX 或 reveal hit、ducking、source/generation need，以及与 product/copy event 的同步。`audio_plan.coverage` 必须覆盖 `[0, duration_seconds]`；无 event 的窗口仅在 `intentional_silence=true` 且附 narrative/commercial rationale 时有效。

每条 on-camera line 必须绑定 exact speaker、verbatim line、Shot 和 `lip_sync_required`。每个 native/generated source audio 声明 `keep`、`mute`、`replace` 或 `trim_then_mix` policy；Shot 开头噪声风险要写 trim/fade 意图和 P6 measurement requirement。

## Provider capability branch

`SourceAudioPolicy`先声明逐Shot意图，Runtime后续才把它绑定到已选Provider capability；本Skill
不选择Provider。`GENERATED + KEEP/TRIM_THEN_MIX`表示该Shot需要Provider生成并保留同步原声，
因此Runtime request必须要求native audio，不能静默改成静音视频再假设P4会补齐。`MUTE`与
`REPLACE`表示Provider source audio不计入最终coverage，仍需的voice/music/SFX必须由显式
audio events和P4 requirements覆盖。`NONE`只允许无source的`MUTE` route。

`p6_measurement_required`与`measurement_requirement`必须同时存在或同时缺失；lead-in risk仍必须
要求measurement。`TRIM_THEN_MIX`必须给出finite non-negative trim start；其他policy不得夹带trim。
Provider返回音轨只证明stream存在，不能替代对audibility、同步、speaker/line、重复文案、
lead-in noise和最终route的逐项Gate。

## Gates and Stop Conditions

- 中段任何 non-intentional uncovered interval 阻止 `PACKAGE_READY`。
- on-camera speaker、verbatim text、Shot 或 lip-sync requirement 缺失时 fail closed。
- source-audio 或 lead-in noise 无 policy 时停止；Workflow只能请求 trim/fade/P6 measurement，不能声称已经修复实际媒体。
- source type、KEEP/MUTE/REPLACE/TRIM_THEN_MIX、trim或measurement互相矛盾时停止。Package
  validity只证明authoring intent自洽；执行时仍必须由Agent Per-Shot Gate把policy绑定到exact
  request与Provider capability，不得以Provider不支持native audio为由自动降级到P4替换路线。

## Quick Reference

| Coverage item | Minimum declaration |
| --- | --- |
| Voice | type, speaker/line when on-camera, Shot |
| Music | presence, energy, transition, ducking |
| SFX | cue + synchronized reveal/product event |
| Silence | exact window + intentional rationale |
| Source audio | keep/mute/replace/trim_then_mix + lead-in plan |
