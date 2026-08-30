# Ecommerce Ad Authoring Contract

## Goal

制作一条 `28s`、`1080×1920`、`24fps` 的抖音竖屏候选广告。主人物固定为同一位现代年轻苗家女孩；商品以用户提供的真实 packshot 作为唯一可读视觉真值。

## Product Truth And Claim Boundary

- SKU：`qingyan-aluminum-chlorohydrate-refreshing-spray-60ml`
- 正式商品名：`青颜 氯化羟铝抑汗净味喷雾`
- 可观察包装：黄色盒装、黄色瓶身标签、白色瓶盖、`青颜` 与 `60ml`。
- 允许表达：`抑汗净味，清爽舒适`、`帮助减少汗湿困扰`。
- 禁止表达：`14天`、`96.67%`、`15%`、`止痒`、`治疗`、`收缩汗腺`、绝对/永久效果及其他未经本轮独立证据支持的宣称。

## Shot Contract

| Time | Role | Visual | Copy |
| --- | --- | --- | --- |
| 0–3s | Hook | 苗家女孩窗边整理衣服，轻微顾虑 | 汗湿黏腻？异味尴尬？ |
| 3–6s | Product intro | 同一女孩自然拿出黄色喷雾 | 出门前，先喷青颜 |
| 6–9s | Product truth | 用户原图 packshot 英雄特写 | 青颜抑汗净味喷雾 |
| 9–13s | Benefit | 金黄色清透流体与轻雾 | 抑汗净味 / 清爽舒适 / 帮助减少汗湿困扰 |
| 13–18s | Payoff | 女孩在明亮山野街巷轻盈行走 | 清爽自在，自信靠近 |
| 18–22s | Social | 女孩与朋友自然互动、回眸 | 近距离社交，更从容 |
| 22–26s | Hero | 真实产品 packshot，浅色留白 | 通勤·出游·运动·约会都自在 |
| 26–28s | Brand close | 女孩背景 + 真实产品卡 | 清爽自在，自信不用藏 |

## Runtime And Quality Boundary

- 人物图、产品手持过桥图和抽象流体图由 built-in `imagegen` 生成；人物身份、现代苗绣、银饰与服装连续。
- 商品可读镜头只使用 `assets/product-packshot.jpg` 的真实像素。手持过桥图不作为 label fidelity 证据，也不宣称喷头/文字细节通过。
- 成片使用确定性 FFmpeg 图层、竖屏轻推拉、商业图文、BGM 与可追溯 SFX；不伪造复杂 UI、医学机制或人物口型。
- `ecommerce-input.json` 通过 input validator 后只证明 Product Truth 输入闭合。由于真实人物持物/喷涂仍需独立 temporal product-fidelity acceptance，本轮不创建 `PACKAGE_READY` 或 Production verdict。
- 本成片是供用户视觉审阅的 media candidate；不自动等于 P6、Final Acceptance、投放效果或平台审核通过。
