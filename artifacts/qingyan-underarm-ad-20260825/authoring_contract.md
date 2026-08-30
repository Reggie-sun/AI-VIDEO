# Ecommerce Ad Authoring Contract

## Product Truth

- SKU: `qingyan-aluminum-chlorohydrate-refreshing-spray-60ml`
- Formal product name: `青颜 氯化羟铝抑汗净味喷雾`
- Authorized source: 用户本轮指定的 `/home/reggie/电商图片/青颜` 商品图片及历史青颜视频素材。
- Observable facts: 包装正面可见商品名、`60ml`、外用喷雾形态。
- Allowed copy: `抑汗净味`（包装正式名称的一部分）、`清爽随身`、`日常外用`、`按说明使用`，以及非量化创意转述 `尴尬气味？` / `尴尬退场`。后二者只回指正式名称中的 `净味`，不得解释为即时、彻底、全天或永久效果。
- Prohibited copy: `14天`、`96.67%`、`止痒`、`治疗`、`收敛汗腺`、`直接调节汗液分泌`、全天或永久效果，以及任何未经独立证据支持的数据或 before/after。

## Strategy

- Audience: 成年通勤、运动和社交人群。
- Pain point: 腋下汗湿或气味带来的日常尴尬。
- Angle: 以夸张但非羞辱性的“腋下小剧场”主观视角引出商品。
- Promise boundary: 只表达商品身份、`净味` 的非量化创意隐喻和轻量日常使用场景，不承诺即时/彻底效果、治疗、持续时长或量化效果。
- Objective: conversion-oriented product awareness。

## Hook And Beats

1. `0.0–4.6s`：成年人物腋下 POV；漫画“尴尬气味”云退场，并以 `清爽随身` 作商品定位，不表达即时生效。
2. `4.6–7.8s`：真实商品 hero card，正式名称可见。
3. `7.8–12.4s`：运动场景，人物反应略夸张。
4. `12.4–17.0s`：通勤场景，黄色飘带承接“清爽随身”。
5. `17.0–22.0s`：群像 CTA + 真实商品 graphic reveal + 使用提示。

## Presentation And Runtime Classification

- 腋下 POV：source-image motion treatment，`SUPPORTED_CURRENTLY`。
- 商品 hero/CTA：真实商品图 `GRAPHIC_REVEAL`，`SUPPORTED_CURRENTLY`。
- 商业图文：deterministic FFmpeg graphics，candidate composition only。
- 人物喷涂、手持、皮肤接触：不执行；`REQUIRES_RUNTIME_CAPABILITY`，本片无此需求。
- P6、Final Acceptance、投放效果：未声明、未执行。

## Audio And CTA

- 全时段由同一可听节奏床覆盖；旧 T8 source audio 统一静音，避免拼接噪声和不一致对白。候选交付前必须用 `volumedetect` 复核整体可听电平。
- CTA: `看看青颜`。
- Disclaimer: `日常外用 · 按说明使用`。
