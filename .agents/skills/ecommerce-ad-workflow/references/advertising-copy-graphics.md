# Advertising Copy Graphics

## Purpose

在 G4 保持商业图文的广告语义与 dialogue captions 分离，并让每条文字与商品、镜头和声音事件同步。

## Typed Roles and Required Fields

只将 audio-aligned dialogue/VO 使用 `DIALOGUE_SUBTITLE`。商业图文使用 `HEADLINE`、`BENEFIT_CALLOUT`、`PRODUCT_LABEL`、`PROOF_LABEL`、`CTA` 或 `BRAND_END_CARD`。每个 item 必须有 role、text、priority、beat/Shot binding、safe-area intent、subject/product avoidance、entrance/exit intent、keyword emphasis、brand token reference，以及 synchronized audio/product event。

正式 product name 必须至少一次出现在 `PRODUCT_LABEL` 或 `BRAND_END_CARD`，或由有绑定的 dialogue/VO 可听说出。headline、benefit、proof、CTA 和 end card 必须表现信息层级，不能把同一 caption style 机械复制到全部 Shots。

## Authoring And Media Review

先结合实际素材决定文字的必要性、表达、信息层级和出现时机，再编排样式；在现有 copy/visual/layout 或修复方案中说明各条文字承担什么、与哪个动作或声音事件关联，以及哪里应留白。没有对白不意味着需要用连续广告句填满画面；不得先套默认字幕模板再补文案，也不要求固定句数、字号或动效。

将上述决定落实到实际 `GraphicTreatment` 或对应 composition 输入：按角色选择字号、字重、颜色、位置、底衬与动效，并核对脸、手、商品和平台安全区。角色枚举不同、字段齐全或改变字号本身不证明层级成立；使用底衬应有可读性或表达理由，不能把所有文字默认排成同样的长条。已有正式 handoff 继续绑定 reviewed visual system 与 per-ad layout；本地审片或手工编排也不得跳过设计与实际媒体复核，不得冒称正式 handoff ready。

出片后先以 exact 成片核对文案、字形、遮挡、层级、动作时点和连续阅读节奏；抽帧只证明实际观察到的局部布局，技术检查不证明观感。用户否定字幕效果时，重新审视表达与编排并输出新候选，保留旧片和反馈，不能仅以 schema、lint 或对比度 PASS 关闭问题。未完成的原速观看、聆听或人工认可须明确保留；完整审片与验收沿 `open-video` Creative Completion Practice 和既有 QA owner，不新增审美分数或自动批准。

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
