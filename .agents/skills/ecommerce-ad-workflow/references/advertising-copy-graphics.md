# Advertising Copy Graphics

## Purpose

在 G4 保持商业图文的广告语义与 dialogue captions 分离，并让每条文字与商品、镜头和声音事件同步。

## Typed Roles and Required Fields

只将 audio-aligned dialogue/VO 使用 `DIALOGUE_SUBTITLE`。商业图文使用 `HEADLINE`、`BENEFIT_CALLOUT`、`PRODUCT_LABEL`、`PROOF_LABEL`、`CTA` 或 `BRAND_END_CARD`。每个 item 必须有 role、text、priority、beat/Shot binding、safe-area intent、subject/product avoidance、entrance/exit intent、keyword emphasis、brand token reference，以及 synchronized audio/product event。

正式 product name 必须至少一次出现在 `PRODUCT_LABEL` 或 `BRAND_END_CARD`，或由有绑定的 dialogue/VO 可听说出。headline、benefit、proof、CTA 和 end card 必须表现信息层级，不能把同一 caption style 机械复制到全部 Shots。

## Gates and Stop Conditions

- 只有 `DIALOGUE_SUBTITLE`、缺 product name、缺 CTA/end-card，或 cue 无绑定时 G4 fail closed。
- commercial role 目前没有完整 Runtime surface 时，handoff 记录 `required_capability=advertising_copy_graphics`；不得伪装成完成的 ordinary CaptionTrack。
- safe area、主体/商品避让无法声明时停止，避免文案遮挡商业证据。

## Quick Reference

| Role | Function |
| --- | --- |
| DIALOGUE_SUBTITLE | audio-aligned speech only |
| PRODUCT_LABEL / PROOF_LABEL | identity and supported fact/disclaimer |
| HEADLINE / BENEFIT_CALLOUT | Hook and value hierarchy |
| CTA / BRAND_END_CARD | action and closure |
