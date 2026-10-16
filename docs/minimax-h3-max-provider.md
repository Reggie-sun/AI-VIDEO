# Official MiniMax H3 Max Provider

## Scope And Authority

显式选择 `minimax_h3_max` / `MiniMax-H3-Max`，通过既有 Canvas、Planner/Router、
`VideoGenerationService`、Paid Provider Gate 与唯一 `ProductionStateCommitter` 执行。
它不自动替换 METASO、旧 MiniMax H3 或其他模型，不注册默认路由，不产生新的状态库。
开发执行成功、Provider 返回和离线测试均不代替逐镜媒体 Gate 或人工成片验收。

## Native Contract

依据 [MiniMax 官方创建接口](https://platform.minimax.io/docs/api-reference/video-generation-v2-create)
与 [查询接口](https://platform.minimax.io/docs/api-reference/video-generation-v2-query)：
直连 `https://api.minimax.io`，创建 `POST /v2/video_generation`，查询
`GET /v2/query/video_generation/{task_id}`。模型字段必须为 `MiniMax-H3-Max`。
支持 5–15 秒、480P/768P；不发送 4 秒或 2K。参考模式允许图片、视频及音频，
首尾帧模式与参考模式互斥；白模必须实际作为视频参考绑定，不能只写在 prompt 中。
`extra.prompt_expansion_mode` 属于所选 immutable profile；不发送 METASO 专用的
`context_ir_enabled`。生成时长与原镜头采用时窗分开；trim/frame/sample/timing
继续由 `ResolvedTimeline` 独占，不延长剧情窗口来容纳模型输出。

## Credentials And Paid Effects

适配器必须由 operator 注入 exact credential supplier；公共封存引用为
`MINIMAX_H3_API_KEY`，它是引用标识，不要求用户私有存储使用同名变量。
供应器只读取用户明确指定的私有来源，不自行搜索 `.env`、其他变量、Secret Service 或旧 key，
不把 key 内容、hash、header、签名结果 URL 写入输出、argv、日志或 receipt。
项目级 `.env` 读取只在用户明确指定该文件时由 task operator 完成，不是适配器默认能力。

每次提交绑定 exact native preview、完整图片/视频/音频 bytes identity、origin、model、
profile、预算 reservation、egress、durable intent 与 one-use permit。
currency 与 monetary fields 只表示 operator 预配置的内部 upper bound，不是官方价格、
汇率换算、真实消费或账户余额。沿既有 ledger 保留历史消费，不新建账本避开计数。
无自动重抽、fallback 或 redirect；unknown 停止。查询与下载必须继续绑定原 task；
下载通过既有 public-IP pinning、TLS/SNI、无凭据 GET，签名 URL 仅暂存内存。

## Verification

Focused checks 使用 `tests/test_production_minimax_h3_max.py`、
`tests/test_production_metaso_h3.py` 和原 MiniMax H3 测试；同时覆盖原文保留编译、
错误模型/endpoint/profile/reference/permit 与 known-no-effect/unknown 的边界。
正式源码变更完成后执行 exact snapshot Harness 及适用 native Risk Gate。
真实 MP4 落盘后显式调用 project-local `video-analysis` MCP，全部 required findings
为 PASS 才允许提取 accepted 状态和提交下一镜；工具成功不代签质量或听音语义。
