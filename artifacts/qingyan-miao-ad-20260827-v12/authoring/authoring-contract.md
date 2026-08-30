# Authoring Contract

## Goal

在 v10 已接受素材基础上修复叙事因果、声音、运镜、切点和结尾重复：老人先向苗家少女推荐产品，少女随后开盖喷用，之后才表现清爽与社交结果。

## Product Truth

- Product: `青颜 氯化羟铝抑汗净味喷雾`
- Allowed claims: `抑汗｜净味`、`清爽舒适`
- Forbidden: 医疗、治疗、治愈、量化时效、绝对保证与未经证实的比较级。

## Timeline

| Frames | Time | Beat | Source / motion contract |
| --- | --- | --- | --- |
| `0-107` | `0.000-4.500s` | Problem | 少女察觉腋下不适并回避；衣物摩擦声与问题文案必须同时建立冲突。 |
| `108-173` | `4.500-7.250s` | Elder recommendation | 老人开口、少女倾听；产品推荐只说一次，喷用尚未发生。 |
| `174-317` | `7.250-13.250s` | Treatment | 单一连续镜头完成开盖、放下盖子、抬臂、喷用；`11s` 位于本镜头内部，冻结尾帧不进入成片。 |
| `318-408` | `13.250-17.042s` | Immediate result | 少女以轻微慢动作放松微笑、收好产品；只出现一次 `清爽舒适`。 |
| `409-583` | `17.042-24.333s` | Social result | 两人连续同行；`22s` 位于本镜头内部，不设置切镜或转场。 |
| `584-719` | `24.333-30.000s` | Product close | 单一动态 packshot 缓慢推进；无第二张静态 CTA 卡，无重复口播。 |

## Audio Contract

- 开头必须有可听见的衣物摩擦 / 问题提示，不得保持无信息的静默。
- 老人推荐对白由既有、已接受的原生对白素材重构；全片产品口播只出现一次。
- 开盖与喷雾 SFX 必须绑定真实动作帧。
- 结尾只保留轻微提示音与 BGM，不再重复广告词。
- 同时交付 BGM 版与 no-BGM 审片版。

## Editing Contract

- `11s` 和 `22s` 不得成为切点。
- 只使用有因果动机的 hard cut，不使用无动机的 xfade、闪白或方向突变。
- 每个 Shot 只有一个主要动作；不新增数字手持抖动、轨道漂移或突然推拉。
- 结尾必须是一个连续运动画面，不得回到两张静图轮播。

## Source Identity

- Problem: `00_problem_discovery_sniff_recoil_v2.mp4`, SHA-256 `8e1db59cb565f8e348ac79eec75f0531b027d2a3e8ebea78f1253845d711b846`
- Elder dialogue: `02_elder_dialogue_repair.mp4`, SHA-256 `4d28cd1f9ea588802d8028e5581fa421e33f3cd5154159971b7179e1226ba2aa`
- Treatment: `01_problem_open_cap_spray.mp4`, SHA-256 `d33a0a8fd1c1dd3a56183886dc554cacdd8452b5cb6e2fdb3ac4522f387e536e`
- Result bridge: `01_recap_elder_enters_v2.mp4`, SHA-256 `e6e54b1c504737d6453056f5f7bbe68ef742d0f186bb3ff02be5c6ec6540a943`
- Walk: `03_leave_together.mp4`, SHA-256 `5edda6a828c1fbbf392ccf5c49aec6e68dce4092ad6b64fbc4f9144257502eb8`
- Packshot: `product-packshot.jpg`, SHA-256 `03d27bd46be48082b6d5ac737fbbb1f6cdca68b891d6c7d7c58eaa2c1c14f078`

## Acceptance

- Exact output: `1080x1920`, `24 fps`, `720 frames`, `30.000s`, H.264 + AAC stereo.
- Transcript contains one product recommendation and no repeated closing slogan.
- Requirement-level media review must verify narrative order, problem readability, treatment/result separation, `11s` / `22s` continuity and single moving close.
- Human visual acceptance remains required; analysis receipts do not replace it.
