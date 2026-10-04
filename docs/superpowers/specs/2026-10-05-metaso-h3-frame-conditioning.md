# METASO H3 Frame Conditioning Spec

## Goal And Scope

基于 `bf2c81d` 补齐 existing METASO adapter 的 input coverage；仅 offline 验证合法 pre-submit。
用户已授权本 slice，Parent self-review 后执行；不改变 continuity architecture。

## Capability Variants

保留 `metaso-h3-ref2va-v1` 的全部字段、顺序和含义。adaptive profile 增加
`metaso-h3-fl2va-v1`：`IMAGE_TO_VIDEO`、allowed roles `("first_frame", "last_frame")`、
`required_first_frame=True`、`max_reference_count=0`、无 media references。
existing grammar 保证恰好一张 first、至多一张 last；first-only 与 first+last 使用同一 variant。
model、output、execution/billing/recovery 延用 sealed profile；不声明 continuity/identity/state guarantee。

## Native Mapping

同一个 `MetasoH3VideoProvider` 将 text、first、optional last 稳定映射为
`text`、`image_url(role=first_frame)`、`image_url(role=last_frame)`。
endpoint/model 复用 `POST /v2/video_generation` / `MiniMax-H3`。
frame 模式省略 ratio，必须 adaptive profile；Ref2VA ratio/Context IR/payload bytes 保持。
frame Context IR 延用 profile；不新增 seed/watermark/negative-prompt settings。

## Exact Input Validation

复用 request/compiler/Resolved contracts 验证 mode、角色、数量、MIME、大小和几何。
frame 必须有 size，png/jpeg/webp、单张最多 30 MiB、宽高 256–5760、ratio 0.4–2.5。
native compilation 经 injected Registry resolver 验证 exact bytes/hash/size；frame encoded
MIME/dimensions 必须匹配 binding，并验证可读图像。不得改 bytes 或接受 unbound URL。
last 独立满足同样要求；upstream 没有 pair equality 证据，不新增等尺寸/等比例要求。

## Compatibility And Fail Closed

`MetasoH3Profile` serialization/pointer 与旧 Ref2VA variant/compiler identity 不变；
adaptive profile 的 provider-wide capability fingerprint 因新增 variant 合法变化，旧 Ref2VA
variant fingerprint 不变。非 adaptive profile 只暴露 Ref2VA，不能静默忽略封存 ratio。
missing first、last-only、reference-as-first、media-in-I2V、unsupported output/settings、
missing size、invalid geometry/MIME/bytes 均在 effect 前拒绝，不自动降级或切换模式。

## Integration And Test Matrix

offline tests 覆盖 deterministic capabilities、first-only、first+last、ordering、missing/last-only、
wrong role、hash/size tamper、missing size、invalid/encoded geometry/MIME、mixed media、profile ratio、
Ref2VA regression、EXACT_TERMINAL terminal → first、HARD_CUT/FULL/C2 derived → first、
explicit soft Ref2VA FULL 仍返回 `CONTINUITY_FRAME_CONDITIONING_REQUIRED`。
复用 Router fixture 与标准 compiler/resolve/preview；effect/credential spies 必须零调用。
运行 METASO、provider-neutral Router、sequence/transition、local H3 family 和 changed-path Harness。

## Non Goals

不读 H3 credential、不 POST/poll/fetch/generate/消费真实 permit；不修历史 source，不改上游
continuity/Planner/Router/QA owners，不新增 mode/transport/fallback。不证明 live API acceptance
或 model quality；真实 B arm 仍须 fresh accepted source。

## Self Review

上述范围满足 upstream 可追溯 input grammar；optional last 已由现有 abstraction 表达。
固定 ratio profile 的拒绝避免 silent input loss；pair equality 保持未证实边界。
风险限定为 adapter input coverage；verification 后按现有 Review Risk Gate 裁决。

## Discovered Boundary

现有 remote prose compiler 不支持 typed-hash state，属于正确 fail-closed。
本 slice 的 native integration 使用完整 v4 text intent；另测 canonical typed-hash intent
仍返回 `PROMPT_EXPRESSION_UNSUPPORTED`。不为获得 B-ready 结论放宽或旁路该 owner；
此 limitation 与历史 source admission 缺证分别保留，后续需要单独的最小 owner 修复设计。
