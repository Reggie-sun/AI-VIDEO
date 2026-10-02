# METASO H3 Provider

## Public Contract

2026-10-02 核对 [METASO 官方插件源码](https://github.com/meta-sota/ComfyUI-MiniMaxH3-API) 与 [METASO H3 页面](https://metaso.cn/minimax-h3) 的公开 API 示例：

- Base URL `https://metaso.cn/api/minimax`，`Authorization: Bearer <METASO_API_KEY>`，model `MiniMax-H3`。
- `POST /v2/video_generation` 接收 `model`、`content`、`duration`、`resolution`、`ratio`、`context_ir_enabled`；返回 `task_id`。
- `GET /v2/query/video_generation/{task_id}` 返回 `task.id`、`task.status`、成功时 `task.content.url`。URL 在内存重查后以无 credential 的 HTTPS GET 下载，不写入 receipt。
- `content` 使用官方 `text` / `image_url` / `audio_url` / `video_url` schema；后三种的 `role` 分别为 `reference_image` / `reference_audio` / `reference_video`。adapter 直接发送 exact Registry bytes 的 data URI，不新增上传接口。
- 图片最多 9 张、单张 30 MiB；视频最多 3 段、单段 50 MiB；音频最多 3 段、单段 15 MiB。音视频每段 2–15 秒，同种类总计不超过 15 秒；audio 必须伴随 image 或 video。图像/视频尺寸 256–5760、宽高比 0.4–2.5。当前通用 binding 只表达整数 FPS，adapter 接受视频 reference 24–60 FPS，公开 API 下界为 23.976。
- 输出 duration 整数 4–15 秒；`768P` / `2K`；ratio `adaptive` / `21:9` / `16:9` / `4:3` / `1:1` / `3:4` / `9:16`。不提交 seed、fps 或臆测的负面 prompt 字段。插件 README 的 5 秒下界落后于当前节点与官方页面的 4 秒下界。
- Context IR 默认开启；每请求 `context_ir_enabled: true/false` 优先于控制台全局设置，可关闭。插件旧 client 没有此字段，METASO 自己的公开示例明确支持。只有实际 response 提供 IR 文本才保存，未返回不伪造。
- 完整 JSON body 上限 64 MiB。reference video 路径已实现；本次 COCO/Nosha 不发送视频。

## Ownership And Safety

`metaso_h3.py` 显式实现 Ref2VA payload/query mapping；复用现有 video request/receipt、remote prose compiler、paid budget/egress/one-use permit、`VideoGenerationService` 与唯一 `ProductionStateCommitter`。下载复用 public-IP pinned HTTPS，禁 redirect。raw key 唯一默认来源是进程环境 `METASO_API_KEY`，不回退其他 secret；request repr 与错误不包含 credential。不注册 default、不 retry POST、不激活 candidate。

Profile 封存 requested ratio 和 Context IR。输出 pixel geometry 与物理 FPS 由 Provider 决定；现有 flexible requirement 使用 adaptive geometry / 24 FPS nominal 声明，实际 MP4 必须独立 probe。内部 `cost_upper_bound_microunits` 是 operator 上限，真实 credits/cost 只从可确认的 Provider response 取证。

## Multiple Reference Views

Planner 允许同一个 Character 的多个 exact reference views，但仍要求覆盖 Shot 的全部重要角色；同一角色的两张图不能补足缺失角色。Scene 可提供多个 reference views。`ShotRoutingContext.additional_scene_references` 只能补充已有 `canonical_scene_reference`，每张都校验同一个 target Scene 的 ID/content hash、selected Registry、role 与唯一 asset ID，并经原有 requirement binding 和 compiler 进入请求。默认空值不进入旧 context 的序列化，保持旧 snapshot/hash 兼容。

《反相之地》的原文复现实验使用显式注册的 task-local native compiler，保持画布全文，仅将 reference 名称改成 H3 的 `Image N` 语法。它仍经过 typed intent、完整输入 identity、Generation Decision、paid preview、one-use permit 和原生 payload 校验；不是默认 compiler 或任意 raw request 旁路。五图一视频的 exact inputs 与视频最低时长适配见 [实验记录](record_for_agent/2026-10-02-fanxiang-transom-metaso-h3-test.md)。

## Verification

`PYTHONPATH=src:tests python -m pytest -p no:cacheprovider tests/test_production_metaso_h3.py tests/test_production_minimax_h3.py tests/test_production_vidu_download.py -q`。新增 adapter / tests 路由既有 `production_video_provider`；离线 PASS 不证明 live、声线复刻或 production qualification。
