# Qingyan Seedance Mini Complete Ad Gate Stop Record

Date: 2026-08-28

## Purpose

本文记录用户要求“生成完整广告，这次用 Seedance Mini”后的 single-submit development experiment。
目标是从 v12/v13 的因果缺口出发，把 `问题 -> 长者推荐 -> 可见交接 -> 姑娘喷用 -> 喷后效果`
压缩进一个 15 秒 Seedance Mini 连续故事单元，再在媒体 Gate 通过后加入有声层和单一动态产品收口。

本轮成功 fetch 真实 Ark MP4，但 required post-media findings 未全部通过，所以没有生成完整广告、
`EcommerceAdProductionPackage`、P4 composition、candidate activation、P6、Final Acceptance 或 publication。

## Current Runtime Truth

- Model: `doubao-seedance-2-0-mini-260615`
- Mode: `REFERENCE_TO_VIDEO`
- Output request: `720p`, `9:16`, `15s`, `24fps`, `generate_audio=false`
- Provider input: exact prompt plus one product-only PNG；没有人物 image/video reference egress
- Product reference classification: `ordinary_non_character_image`
- Submit count: `1` POST；transport counters 为 `14` query GET、`1` download GET
- Retry / permit remint / Provider fallback / activation: `0 / 0 / 0 / 0`
- Finite ceiling: `8 CNY`
- Pricing-derived upper bound and runtime settlement value: `7.452 CNY`；这不是 Provider invoice 或已核实账单扣款

人物参考图被 Ark 判为真人的旧路径没有恢复。新 route 只发送产品图，让 Mini 从文本生成写实人物；
这次没有触发 `PrivacyInformation` rejection，但一次成功不能证明 Ark 服务端以后永不拒绝其他输入。

## Authoring And Paid Preflight

`ecommerce-ad-workflow/input/1` 位于：

```text
runs/qingyan-seedance-mini-complete-ad-20260828-001/ecommerce-input.json
```

input validator 返回 `status=valid`、`diagnostics=[]`。由于新生成媒体在落盘前没有 authoritative
physical-interaction evidence，本轮没有提前伪造 `PACKAGE_READY`；只有 exact media Gate 通过后才允许生成
package。产品表达保持 `抑汗｜净味`、`清爽舒适`，继续禁止医疗、量化、时长和绝对效果承诺。

Seedance prompt 经 linter 从过长 `FAIL` 收敛为：

```text
Seedance Preflight — PASS
words: 169
```

exact prompt、source evidence、Shot contract 与 offline preview：

```text
runs/qingyan-seedance-mini-complete-ad-20260828-001/prompt.txt
runs/qingyan-seedance-mini-complete-ad-20260828-001/source-evidence.json
runs/qingyan-seedance-mini-complete-ad-20260828-001/shot-contract.md
runs/qingyan-seedance-mini-complete-ad-20260828-001/evidence/preflight-report.json
```

offline preflight 确认 `credential_present=true`、`submit_posts=0`、一张 product-only reference、
`estimated_cost_upper_bound_cny=7.452`。credential 只通过 exact Secret Service reference 注入，未写入
artifact、prompt、command argument、stdout、record 或 receipt。

## Exact Live Output

Raw fetched media：

```text
runs/qingyan-seedance-mini-complete-ad-20260828-001/output/seedance-mini-story-15s.mp4
SHA-256 8e9f1c596e131ae2f2399e6f12807ab7aa4cb6d2d5985d02ca64efb477b321da
8,176,148 bytes; H.264 High; 720x1280; 24fps; 361 frames; 15.042s; no audio stream
```

sanitized request/audit 与 exact fetched identity 位于：

```text
runs/qingyan-seedance-mini-complete-ad-20260828-001/evidence/live-report.json
runs/qingyan-seedance-mini-complete-ad-20260828-001/production/state/video-generation/fetch/receipts/1d61ab457a74ec44f2223fa2dead729785d7b507167410cc3eaaea374e29cc3a.json
```

该 MP4 是 local-only development artifact，未 activation、未加入 v12/v13、未发布。

## Post-Media Gate

exact MP4 落盘后立即调用 project-local `video-analysis` 的 `video_analyze` 与 `video_review`：

- probe 与 raw output 一致；
- `20` 个抽取帧；
- `unique_frame_ratio=1.0`；
- no audio；
- scene detector 返回 one scene，但密集帧明确存在 hard cuts，因此不把 scene count 当作 cut truth。

随后使用 `2fps`、`4fps` 全片 contact sheet，以及推荐 `8fps`、交接 `6fps`、喷用/效果 `6fps`
窗口完成 requirement-level inspection。完整 Gate：

```text
runs/qingyan-seedance-mini-complete-ad-20260828-001/evidence/post-media-gate.md
```

关键结果：

| Requirement | Verdict | Evidence |
| --- | --- | --- |
| `PROBLEM_HOOK` | `PASS_VISUAL_ONLY` | 开头拉开腋下湿衣并以紧张表演建立问题；最终首秒声音尚未合成。 |
| `RECOMMENDATION_ORDER` | `PASS_VISUAL_ONLY` | 长者入场、可见口型、先展示产品再递出；最终对白尚未合成。 |
| `HANDOFF_CAUSALITY` | `PASS` | sole holder、伸手、短暂共持、接稳、放手顺序清楚。 |
| `CHARACTER_STYLE` | `FAIL` | 苗家银饰、靛蓝刺绣服饰和银头饰全部丢失，变成普通背心/牛仔裤与灰开衫。 |
| `SPRAY_ORDER` | `FAIL` | 姑娘没有抬臂或露出腋下；喷雾横向越过胸肩，未执行 underarm application。 |
| `RESULT_ORDER` | `PASS_CAUSAL_ORDER` | 放松与微笑出现在可见喷雾之后，但不能修复错误喷用位置。 |
| `CAMERA_AND_TRANSITIONS` | `PASS` | 四种构图切换有动机，无闪白、溶解、数字漂移或异常运镜。 |

overall Gate 为 `FAIL`。`CHARACTER_STYLE` 与 `SPRAY_ORDER` 都是 required findings；任一失败都足以阻止下一步。

## Assessment

本轮关闭了两个问题：

1. Seedance Mini 可以只用 product-only reference 返回写实双人广告画面，不需要动漫 fallback，也不需要把
   synthetic photorealistic person image 送到 Ark。
2. 同一个 15 秒生成单元可以实现“推荐在前、可见交接在中、喷雾与效果在后”的宏观因果顺序。

但它没有完成用户要的广告：Miao visual identity 丢失，且核心喷用动作在身体位置上错误。把这条视频配音、
加文案和 packshot 只会掩盖失败，不会修复它，因此 composition 被正确阻断。

## Remaining Risk And Next Decision

本次 one-use permit 已消费，finite ceiling 已结算；任何新 Seedance submit 都需要新的 exact preview、预算、
durable intent 与 one-use permit，不得 blind retry。下一次若继续 Seedance Mini，应只修改两个已归因变量：

1. 提升 Miao wardrobe / silver-accessory adherence，同时继续不发送 person reference；
2. 把喷用拆成更短、更明确的 dedicated underarm Shot，减少 15 秒多动作竞争。

这会增加调用数与预算，必须由用户重新授权。当前 raw MP4 可供用户检查因果和风格失败，但不能标为完整广告。

## Agent Guardrails

- `Ark task succeeded` 不等于 `post-media Gate PASS`。
- `HANDOFF_CAUSALITY=PASS` 不得覆盖 `CHARACTER_STYLE=FAIL` 或 `SPRAY_ORDER=FAIL`。
- product-only route 没有恢复或绕过被退役的 photorealistic person-reference egress path。
- 不得自动重提、扩预算、改用动漫、fallback 到其他 Provider，或把 raw MP4 拼进 v12/v13。
- 没有完整有声 composition，因此不得声称用户要求的完整广告已生成。
- Human normal-speed verdict、P6、Final Acceptance、publication 和广告效果均为 `NOT_EVALUATED`。
