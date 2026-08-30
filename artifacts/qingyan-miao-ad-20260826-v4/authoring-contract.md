# Authoring Contract

## Delivery Boundary

- 交付为 30 秒、`1080x1920`、`24fps` 的 9:16 开发候选片。
- 本轮不新增 T8 Provider submit；复用已经按 exact bytes 完成逐镜 Gate 的人物素材，并对补充步行素材重新做项目级视频复核。
- T8/H3 人物素材使用节点原生支持的 `768x1344` portrait canvas；输入适配、模型 canvas 与最终交付尺寸是三层独立契约。
- 最终 Composition 将 `768x1344` portrait canvas 规范化到 `1080x1920`，不把底层 tensor 或生成能力误述为仅支持 16:9。
- 所有可读产品包装与产品英雄镜头使用用户源产品图；T8 生成手持产品只表达拿取或出门准备动作，不作为包装文字、喷头或实际喷雾的证据。

## Product Truth And Claims

- 产品视觉锚点：黄色盒装、黄色瓶身标签、白色瓶盖、青颜字样、`60ml`。
- 允许文案：`抑汗净味 清爽舒适`、`帮助减少汗湿困扰`。
- 禁止文案：医疗或治疗表达、汗腺机理、量化功效、`清爽一整天`、永久或绝对保证。
- 近距离社交只表达人物状态转变，不暗示他人对体味作出可验证反应。

## Revised Shot Plan

| Shot | Time | Frames | Visual | On-screen Copy | Proof Role |
| --- | --- | ---: | --- | --- | --- |
| 01 | 0-3s | 72 | 苗家女孩出门前轻触腋下附近衣物，神情克制 | `汗湿黏腻？` `靠近不自在？` | 痛点钩子，不羞辱体味 |
| 02 | 3-6s | 72 | 女孩拿起产品；右下叠加源产品图卡片 | `出门前，带上青颜` | 动作提示 + 可读产品真值 |
| 03 | 6-9s | 72 | 干净的使用前动作，叠加源产品图 | `抑汗净味 清爽舒适` | 允许 claim；不伪造喷雾微距 |
| 04 | 9-13s | 96 | 金黄色清透流体与留白画布 | `帮助减少汗湿困扰` `保持清爽自在` | 抽象利益表达，不画汗腺机理 |
| 05 | 13-18s | 120 | 两段稳定户外步行与微笑状态 | `清爽自在 步步从容` | 状态转变 |
| 06 | 18-22s | 96 | 民族元素穿搭、银饰、自然回眸 | `通勤 · 出游 · 约会` `自在切换` | 场景扩展 |
| 07 | 22-26s | 96 | 源产品图英雄镜头、浅色画布、少量金色纹样 | `青颜 氯化羟铝抑汗净味喷雾` | 可读 SKU 真值 |
| 08 | 26-30s | 96 | 人物背景柔化，前景源产品卡片 | `清爽自在 自信不用藏` `出门前，带上青颜` | 品牌记忆与 CTA |

## Runtime Handoff

- Composition owner: `compose_t8_canvas_v4.sh`
- Reused T8 clips: `runtime/t8_portrait_ad/*.mp4`
- Deterministic assets: `assets/product-packshot.jpg`、`assets/04-golden-fluid.png`
- Output: `final/青颜_苗家女孩T8动态广告_30s_9x16_v4.mp4`
- Publication state: local development candidate only; not `PACKAGE_READY`、P6 或 Final Acceptance。

## Remaining Risk

- 未生成可信的真实喷雾微距；Shot 03 只使用前动作与源产品图表达。
- BGM 与 SFX 沿用现有本地资产，本轮没有取得发布级 license provenance。
- 人物素材原生为 T8 支持的 `768x1344` portrait canvas，最终由 deterministic compositor 规范化到 `1080x1920`；放大仍可能带来细节损失，但不代表 T8 只能生成横屏。
