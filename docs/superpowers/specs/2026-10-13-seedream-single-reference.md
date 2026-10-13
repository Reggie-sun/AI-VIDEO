# Seedream Single PNG Reference

## Goal And Scope

原 S01 要用几何一致的窗内 clean plate，只删除林砚倒影；原文没有强制最终视频 overlay。选择首帧准备路线，先补同一 Seedream adapter 的单张 exact PNG 参考输入，复用现有 image/paid/Registry/P5 owners。工程修改属于当前任务必要共享适配；本 spec 不授权任何图片/视频 POST。

## Current And Target Contract

当前 Seedream request 和 profile 均只支持纯文字。新增显式 opt-in `allow_single_png_reference=true` profile，最多一张 `scene` ImageReferenceBinding。图片仅由 injected `image_resolver(binding)` 返回原 bytes，经 PNG measurement、exact SHA、尺寸/bytes ceiling 重验。不得把路径、URL、未注册图片或任意 mask 参数送给 Provider。

纯文字 request 使用原 `ai-video-image-request/4`，profile 序列化/hash 与 `seedream-original-png/1` result identity 不变。单参考 request 用 `/5`，新 opt-in profile 使用 `seedream-single-reference-png/1` identity；result 也明确区分。旧 profile 不自动获得图生图。

Preview 的 egress items 单独绑定 reference SHA/bytes/MIME；reference_total_bytes 必须与 items 一致。Native payload 只新增 `image=data:image/png;base64,...`。重开图片不得改变 bytes，preflight 和 permit 前重验同一 preview；异图、损坏图、缺 resolver、过期 profile、错误 role/count 或无 exact authority 必须在 credential/permit/POST 前停止。现有 durable intent、reservation、one-use permit、no retry/unknown fail-closed 保留。

## Evidence And Limits

接口依据：[官方 Seedream 5.0 Pro 教程](https://docs.volcengine.com/docs/ark/seedream-5-0-pro?lang=zh)，同一 model `doubao-seedream-5-0-pro-260628` 支持 image + prompt、`<bbox>` 坐标定位。只实现单 PNG，未扩多图、图层拆分、HTTP image fetch、mask/VFX、renderer 或故事 executor。坐标须从实际待编辑图审查，不在此编造；模型输出不保证逐像素保护或七倒影，仍须实际 QA。

原首帧、plate 与保护区域的 actual identities 尚缺；单参考支持只是准备能力。新原 S01 raw MP4 的全部 required findings 必须 PASS，才可进入 handoff/S02。合成不能代签 raw reflection PASS。声音仍为 EVIDENCE_REPAIR_FIRST；当前会话不能实际听音，且 controlled verifier 未接 human host。

## Acceptance And Verification

通过 public remote image committer 测试单参考 wire/egress、激活、strict reopen、replay 与来源 hash；覆盖旧 profile/旧 T2I bytes、role/count、reference drift/invalid PNG、错误 preview bytes、失效时间及 unknown no retry。测试是工程证据，不证明《界蚀》媒体。运行相关 image/remote lifecycle suites、Architecture Gate 和 exact staged Harness。

## Self Review

不新增 Provider/model、timeline、状态 owner 或可重放 permit；保留旧纯文字契约和付费历史。新能力明确 opt-in，没有参考时仍走旧 result identity。复用已存在 Grok image-resolver/egress pattern，但不调用 Grok。首帧准备满足原文机制的可能性与实际视频保留分别验收；缺几何或听音证据时停止，不能用工程 PASS 推进。
