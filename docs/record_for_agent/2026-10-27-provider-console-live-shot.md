---
record_kind: architecture_implementation
topic_id: provider-console-live-shot
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Provider Console Live Shot Record

Date: 2026-10-27

## Failure And Repair

`http://127.0.0.1:5174/` 初始只发现 243 个工作区，最新项目时间停在 10 月 25 日；
真实 `runs/` 已有 608 个 `project.yaml`，包括《失帧》和广告的深层 repair workspace。
原扫描按名称广度遍历，单个素材目录耗尽 16,384 entry 总预算时直接停止，默认深度 6
也遗漏了部分 repair 路径。首页媒体列表另外只接纳已有 exact video 的记录，未产出视频的
attempt 没有直接可见入口。持续文件事件会不断重置 debounce；SSE 重连没有补读缺失状态。

- 原 discovery owner 改为优先近期目录树，每个非根目录最多扫描 256 entries，整体预算仍为
  16,384；深度有限扩至 10，发现候选上限 1,024，返回上限仍为 256。截断继续显式报告，
  catalog 不签发 strict validity，不改变 Production state。
- 初始 detail batch 除最近 6 个 workspace，另纳入最多 6 个近期 video-attempt workspace，
  保留 2 个并发 reader。timestamp hint 只调度 strict detail，不生成 lifecycle truth。
- 首页增加“当前 Shot 动态”，可直接进入 exact attempt；只消费 strict valid detail。
  `running/polling` 显示正在生成，`fetch` 显示获取视频，`validate` 明确显示等待验证。
  未观察到正在生成时只声明“已加载记录中没有”，不把局部扫描当作全局没有任务。
- 文件事件按有限窗口发送，连续写入不能无限延期；每次 SSE `ready` 补读 Runs 与 external
  catalog，覆盖首次订阅及断线重连期间的变动。已有视频选择仍保持固定。

## Verification And Evidence

- 两个新 discovery regression 在修复前失败，修复后 catalog 精准测试 11 项通过。
- exact staged code 的 focused Harness：77 项 Python、112 项 Node tests 通过。
  Receipt：`.agent/harness/runs/20261027-console-shot-live-focused/receipt.json`。
- `npm exec --offline -- vite build` 通过。
- Chrome MCP 在真实本机页面看到此前遗漏的《失帧》S03，点击进入
  `shizhen-S03-qualification-attempt-005`；当时 canonical 状态为 `running/validate`，
  页面正确标记等待验证。desktop 及 390px viewport 检查通过，无页面横向溢出。
- 另一个已关闭的隔离 browser tab 使用临时响应 fixture，经真实 React loader 和 SSE handler
  验证 `polling → fetch → validate` 自动更新及重连补读；这是模拟状态转换，不是新 Provider
  执行。没有写 Manifest、重新生成媒体或调用付费 Provider。
- related/full Harness 均被已有 `AGENTS.md` 的 14,185 bytes 超出 14,000 bytes 上限挡住；
  `git show HEAD:AGENTS.md` 同样为 14,185 bytes，本任务未修改它或放宽 Gate。
  Receipts：`.agent/harness/runs/20261027-console-shot-live-related/receipt.json`、
  `.agent/harness/runs/20261027-console-shot-live-full/receipt.json`。它们是 FAILED，不能宣称
  完整回归或发布验收通过。

## Assessment And Boundaries

`NATIVE_REVIEW_NOT_REQUIRED`：变更为只读 discovery、UI 和刷新调度；原 strict reader、
containment、secret sanitization 与唯一 Production writer 不变，失败路径有针对性测试。
目录容量仍有界，旧工作区可能未发现或按需加载；缺失外部目录仍显示不可用。
CodeGraph 本次返回 source-changed-during-indexing，结构判断使用当前源码和可执行测试。
保留其他窗口的生产代码、policy、制作文件及记录改动，未夹带提交。

`distill-ai-video-learning`：`no_candidate`。这是一次工程故障修复，没有达到独立媒体实验
或受控比较的经验采纳门槛，不创建 Learning Claim，不修改 Skill/Policy/Gate。
