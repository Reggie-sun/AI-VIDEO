# Official MiniMax H3 Max Provider

## Scope And Authority

显式选择 `minimax_h3_max` / `MiniMax-H3-Max`，通过既有 Canvas、Planner/Router、
`VideoGenerationService`、Paid Provider Gate 与唯一 `ProductionStateCommitter` 执行。
它不自动替换 METASO、旧 MiniMax H3 或其他模型，不注册默认路由，不产生新的状态库。
开发执行成功、Provider 返回和离线测试均不代替逐镜媒体 Gate 或人工成片验收。

## Native Contract

依据 [MiniMax 官方创建接口](https://platform.minimax.io/docs/api-reference/video-generation-v2-create)
与 [查询接口](https://platform.minimax.io/docs/api-reference/video-generation-v2-query)：
国际站直连 `https://api.minimax.io`；国内站按
[国内官方文档](https://platform.minimax.cn/docs/api-reference/video-generation-v2-create)
显式选择 sealed profile 的 `api_region="cn"`，只访问 `https://api.minimax.cn`。
未指定 region 的旧 profile 保持国际站及原 hash，不因 401 自动切换站点。
两站均创建 `POST /v2/video_generation`，查询
`GET /v2/query/video_generation/{task_id}`。模型字段必须为 `MiniMax-H3-Max`。
支持 5–15 秒、480P/768P；不发送 4 秒或 2K。参考模式允许图片、视频及音频，
首尾帧模式与参考模式互斥；白模必须实际作为视频参考绑定，不能只写在 prompt 中。
`extra.prompt_expansion_mode` 属于所选 immutable profile；不发送 METASO 专用的
`context_ir_enabled`。生成时长与原镜头采用时窗分开；trim/frame/sample/timing
继续由 `ResolvedTimeline` 独占，不延长剧情窗口来容纳模型输出。

从 4 秒模型切换时，提交前必须逐项比较 selected QA 的原文、技术 observable 和
final-output goal：用新版本将“请求4秒”适配为 H3 Max 的5秒标称生成，保留原采用时窗、
对白窗口、全部剧情要求、proof/tolerance 和旧 source quotes；不能只改请求然后把旧4秒规则
判成 PASS。尚无 paid intent/permit/transport 的旧准备只能由 committer 显式封存为
unsubmitted，保留其历史与计数，不能重分类已提交或未知的任务。

## Credentials And Paid Effects

适配器必须由 operator 注入 exact credential supplier；公共封存引用为
`MINIMAX_H3_API_KEY`，它是引用标识，不要求用户私有存储使用同名变量。
国内站引用为 `MINIMAX_H3_CN_API_KEY`；operator 先核对用户实际创建 Key 的站点，
再明确绑定对应 supplier/profile/origin，禁止自动跨站尝试同一凭据。
供应器只读取用户明确指定的私有来源，不自行搜索 `.env`、其他变量、Secret Service 或旧 key，
不把 key 内容、hash、header、签名结果 URL 写入输出、argv、日志或 receipt。
项目级 `.env` 读取只在用户明确指定该文件时由 task operator 完成，不是适配器默认能力。

每次提交绑定 exact native preview、完整图片/视频/音频 bytes identity、origin、model、
profile、预算 reservation、egress、durable intent 与 one-use permit。
付费 preview 的 `request_fingerprint` 使用 resolved request 的
`resolved_generation_hash`；先以 `build_video_paid_permit_binding` 核验一致性，不能填入
原始 `request_input_hash` 后才靠真实提交入口发现错误。
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
