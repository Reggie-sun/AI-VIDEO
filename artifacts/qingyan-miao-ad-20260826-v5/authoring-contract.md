# Authoring Contract

## Repair Boundary

- 修复 v4 的三个 human blockers：无推广口播、clone-frame seam/stutter、跨段视觉不连贯。
- 保持 30 秒、`1080x1920`、`24fps`；T8/H3 人物素材为原生 `768x1344` portrait canvas。
- 新增一条本地 T8 native-audio 商品推广 Shot；exact MP4 落盘后必须先完成逐 Shot Gate，PASS 前不得进入整片合成。
- 复用素材保持历史 exact bytes；所有可读包装继续由 source packshot 所有。

## Spoken Promotion

- Speaker: `(S1)`，22 岁中国女性，画面内本人，普通话，温和自然、非夸张播音腔。
- Exact line: `出门前用青颜，抑汗净味，清爽舒适。`
- 口播只使用已允许的商品名和 claim；不得扩写量化、医疗、全天或绝对效果。
- Gate requirement：能检测到清晰人声；ASR 必须覆盖 `青颜`、`抑汗净味`、`清爽舒适` 三个语义锚点；人物嘴部应有连续发声动作。

## No-Freeze Timeline

所有 live-action segment 直接使用真实源 frames，不使用 `tpad`、clone、reverse loop 或 duplicated-frame extension。
30 秒由 10 个 segment 和 9 个 6-frame crossfade 组成：源总长 `774` frames，transition overlap
总计 `54` frames，最终精确 `720` frames。

| Segment | Source frames | Role | Continuity rule |
| --- | ---: | --- | --- |
| 01 concern | 48 | problem hook | 跳过原素材开头 8 个静止帧，保留连续真实动作 |
| 02 product lift | 56 | recommendation setup | 与 01 用 6-frame dissolve，不假定同一动作 |
| 03 spoken recommendation | 124 | audible promotion | 新 T8 Shot；独立 close/medium presentation beat |
| 04 benefit canvas | 96 | benefit explanation | animated fluid canvas，承接口播，不冻结人物 |
| 05 walk forward | 56 | payoff | 单一原镜头 |
| 06 scenario canvas | 72 | explicit scene reset | 将两个户外动作分隔为不同场景，不直接硬拼 |
| 07 walk smile | 56 | commute/travel state | 单一原镜头 |
| 08 social turn | 56 | social payoff | 新场景 dissolve，不宣称延续上一脚步 |
| 09 product hero | 120 | readable product truth | source packshot + continuous motion graphics |
| 10 end card | 90 | CTA closure | source packshot + continuous motion graphics |

## Final Gate Requirements

- `ad.audio.product_recommendation`: spoken promotion present and intelligible.
- `ad.audio.voice_continuity`: one stable `(S1)` voice during the dialogue window.
- `ad.motion.required_windows`: no unapproved freeze interval in live-action windows.
- `ad.edit.pacing`: no live-action clone padding; each boundary visually intentional.
- `ad.continuity.character`: face、wardrobe、product coarse identity remain stable.
- `ad.continuity.spatial_temporal`: no direct pose/scale/foot-state jump presented as one continuous Shot.
- `ad.product.packaging_consistency`: readable hero/end-card pixels use exact source packshot.
- `ad.copy.claim_compliance`: only allowed claim text and exact spoken line.
- `ad.delivery.duration_aspect`: 30 seconds、9:16、24fps、720 frames。

## Publication Boundary

本轮只交付 local development candidate 和 requirement-level evidence；不自动成为 Production
Manifest candidate、P6、Final Acceptance、`PACKAGE_READY` 或平台发布证明。
