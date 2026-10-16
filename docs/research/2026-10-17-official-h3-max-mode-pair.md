# Official H3 Max Mode Pair Research

Date: 2026-10-17

## Scope

本说明核对《界蚀》授权内最多两次、零重抽的 MiniMax H3 Max CN 模式比较。官方契约来自 [MiniMax 国内站视频生成 V2 创建接口](https://platform.minimax.cn/docs/api-reference/video-generation-v2-create)；项目能力以当前 [H3 Max adapter](../../src/ai_video/production/minimax_h3_max.py) 和[共享 H3 payload compiler](../../src/ai_video/production/metaso_h3.py) 为准。本轮只做文档 GET 和本地证据核验，没有视频、图片或音频 API POST，也没有准备 permit。

## Official API Contract

官方接口把图生视频端点模式与多模态参考模式分开：`first_frame` / `last_frame` 图片可与 text 同送；只要出现 `reference_image`、`reference_video` 或 `reference_audio` 任一 role，就不能再出现 `first_frame` / `last_frame`，反向也一样。首尾帧模式每种端点最多一张图；多模态模式最多 9 张参考图、3 段视频和 3 段音频，参考视频每段 2–15 秒、合计不超过 15 秒，支持 MP4/MOV、H.264/H.265、23.976–60 fps，单视频不超过 50 MB。每张图不超过 30 MB，图片宽高各 256–5760 px、宽高比 0.4–2.5；请求体总大小不超过 64 MB。

H3 Max 输出支持 480P/768P，不支持 2K；`duration` 必须是 5–15 秒整数。图生视频的比例由输入图决定，接口将其作为 `adaptive`，其他 `ratio` 即使传入也会被忽略。参考模式的 `ratio` 可省略并采用 `adaptive`，也可显式选 `21:9`、`16:9`、`4:3`、`1:1`、`3:4` 或 `9:16`。官方字段说明定义了输入与模式边界，没有宣称参考模式必然遵守身份、动作、人数、空间或反射要求。

## Project Support And Pair Mapping

当前 adapter 已实现两条路线：仅 `aspect_ratio="adaptive"` 时开放 `minimax-h3-max-fl2va-v1` frame capability；该路线要求 `first_frame`，可选 `last_frame`，且 native payload 不发送 `ratio`。`h3-max-reference-v1` reference capability 可绑定参考图/视频并发送 profile 中的显式 `ratio`。两条路线的 H3 Max native options 都带 `extra.prompt_expansion_mode="balanced"`。二者共用同一个 payload compiler，按 binding 的原顺序生成 native `content`；身份 alias 不会在此步骤自动去重。

本对照两臂共同使用 `model="MiniMax-H3-Max"`、必需的非空 `text`、`duration=5`、`resolution="768P"` 与上述 `extra`。A 的素材项是 `type="image_url", role="first_frame"`；B 的素材项是 9 个 `type="image_url", role="reference_image"` 及一个 `type="video_url", role="reference_video"`。旧 CN B 的封存 profile 已明确 `aspect_ratio="9:16"`，而当前 reference compiler 会把 profile 比例发到 native `ratio`。当前 capability 不支持受控 seed，因此新旧输出不能构成同 seed 因果对照。

| Control goal | A: Original PNG as `first_frame` | B: Existing image semantics plus v015 video reference | Evidence boundary |
| --- | --- | --- | --- |
| 开场构图 | 原 PNG 是显式首帧输入；保留图中可见内容。`duration=5`、`resolution=768P`，native 不发 `ratio`，由首帧走 `adaptive`。 | 原 PNG 是 `reference_image` 引导；不是端点约束。旧 B profile 与 native 输入均为 `ratio=9:16`。 | A 的 endpoint role 强于文本引导，但仍须观察 exact 输出；B 的参考绑定不等于首帧必然一致。 |
| 人物身份、人数与道具 | 只有这一张图作为首帧，没有独立 `reference_image` 绑定；保留图中实际可见的身份信息。 | 保留既有 9 个 semantic image bindings，但它们全是同一 PNG SHA，不是 9 份独立人物证据；仍属模型参考引导。 | 两条路线均须在 exact MP4 核验身份、人数及道具。 |
| 动作时序 | v015 不可随 `first_frame` 一同提交；本臂没有白模视频，动作仅保留在原文要求中。 | v015 实际绑定为 `reference_video`，提供动作过程/机位的参考引导。 | 4 秒白模、5 秒生成与 0–3 秒采用窗口分别记录；参考视频不锁定动作到点时刻。 |
| 空间与摄影 | 首帧表达开场空间与机位；后续空间、遮挡、反射和摄影连续性仍未被端点字段保证。 | 白模可以引导布局、动作和摄影，但输出仍需逐项测量和观看。 | 镜面中的其他乘客、人物手部、镜头稳定、画幅与接点都由输出证据裁决。 |

A 因官方互斥约束而省略动态白模，必须在该镜输入记录中保留明确例外及能力依据；这不是项目默认取消逐镜白模。B 保留白模时仍按原职责使用，不把它提升为最终材质或成片验收证据。旧 B 已使用 `ratio=9:16`；若新 B 沿用相同 profile 与 exact inputs，该比例不构成新条件。

## Historical Evidence And Attribution

[既有《界蚀》记录](../record_for_agent/2026-10-13-jieshi-original-s01-s02-candidate.md)显示，前一 H3 Max CN R2V 输入使用了 9 份同 PNG `reference_image` 和 v015 `reference_video`。旧 [profile](../../runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-cn-S01-20261016-001/profile.candidate.json) 明确为 `aspect_ratio=9:16`；它的 SHA 与 [runtime-ready context](../../runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-cn-S01-20261016-001/runtime-ready-context.json) 的 profile SHA 一致，runtime-ready 记录的 native body SHA 又与 [wire POST](../../runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-cn-S01-20261016-001/wire-observations.json) 的 body SHA 一致，且 POST 返回 HTTP 200。[Paid preview](../../runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-cn-S01-20261016-001/paid-preview.final.json) request fingerprint 与同目录 [resolved request](../../runs/canvas-jieshi-original-s01-s02-20261013-001/official-h3-max-cn-S01-20261016-001/resolved-request.candidate.json) 的 resolved hash 匹配。当前 [adapter profile](../../src/ai_video/production/minimax_h3_max.py#L32) 封存比例；[native compiler](../../src/ai_video/production/metaso_h3.py#L290) 在非 frame mode 把 profile `aspect_ratio` 作为 native `ratio` 发送。因此旧 B 的 native 比例已是 `9:16`。`resolved-request` 的 `effective_output.ratio=adaptive` 是 [输出能力投影](../../src/ai_video/production/minimax_h3_max.py#L61)，不能据此推断 native 请求比例。实际 MP4 为 768×1344、4:7，原采用窗口仍是 0–3 秒。15 项 QA 为 **4 PASS / 5 FAIL / 6 NOT_EVALUATED**：缺陈立及道具、出现手部幽影，frame71 仍在抬手，故 S01 继续 STOP。此结果说明该组参考没有保证所有要求通过；它不能证明重复图、参考视频或 `9:16` 比例单独造成失败。

同一记录中的早期 H3 artifact 曾局部保留七人倒影，但整片仍 FAIL，且不是当前输入或接受源。先前白模辅助的另一模型尝试也出现部分局部 PASS 与身份/空间/倒影 FAIL；模型、profile 与输入同时不同，不能作为 H3 Max 的因果对照。以上反例只限制结论，不支持“模型永远做不到”或“白模必然无效”。

若新 B 原样重用旧 reference roles、v015、`ratio=9:16` profile 及其他 exact inputs，它与已经完成的 CN B 是同一条件。再付一次 B 只增加一个随机输出样本，不增加新的模式或比例条件，也不能归因于任何单一控制目标。故本次 paired unit 的“B”已有历史 exact 成片可供对照；重发 unchanged B 对本研究问题不增加可归因信息。A 相对旧 B 改变为 frame mode 并移除视频参考，结果仍只作有界模式观察，不能构成控制变量齐备的因果 A/B。

## Acceptance Boundary

两臂都保留原文全部 15 项 canonical QA 与 0–3 秒采用窗口，不删减允许差异，不用 5 秒尾帧冒充 3 秒切出状态。每个 exact MP4 均须走 project-local `video-analysis`，逐项检查身份、人数、道具、反射、空间/摄影及采用切点；缺证据仍为 `NOT_EVALUATED`。测试通过、API 接受请求或参考素材绑定成功都不代表媒体质量、完整故事或人工 1.0x 验收。既有失败候选继续 STOP；本调研不解除该状态，也不声称跨项目通用质量已证实。
