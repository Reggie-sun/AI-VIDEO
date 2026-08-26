# Video Analysis MCP Multi-Agent Serialization Record

Date: 2026-08-27

## Purpose

本文记录 project-local `video-analysis` MCP 在多个 Agent 各自持有独立 stdio server
process 时的 repository-wide 串行执行契约，以及本轮实现、验证和未覆盖边界。

该记录只描述当前已提交 runtime truth，不授予新的 Provider、媒体生成、Manifest、P6、
activation、Final Acceptance 或 release 权限。源码、测试与 fresh Harness receipt 仍是最终
source of truth。

## Current Runtime Truth

- `.codex/config.toml` 和 `.mcp.json` 继续把 `python -m ai_video_mcp` 注册为
  project-local stdio server；本轮没有改变 transport、tool schema 或 public tool names。
- Native child Agent 的实际 tool catalog 已确认包含全部 8 个 `video-analysis` tools；每个
  Agent 仍可建立自己的 stdio server process。
- 所有 8 个显式 MCP tool calls 与 asynchronous post-media hook 现在共享 repository-local
  `.git/ai-video-analysis-hook/worker.lock`，并通过 POSIX `flock` 持有一个 exclusive lock。
  因此，同一 repository 中来自不同 Agent/process 的分析 execution 不再重叠。
- 等待 lock 时取消 request，不会启动底层 operation；operation 已在线程中启动后，即使
  request 被重复取消，也会继续持有 lock，直到实际 worker 完成，再向 caller 传播取消。
- lock 只序列化 execution。Whisper/model cache 仍是每个 stdio process 的 process-local
  state，operation 结束后也可能继续占用各自资源；本实现不是 shared daemon，也不声明
  single GPU owner。

## Session Work And Decisions

本轮建立了一个明确的 serialization owner：

- 新增 `src/ai_video_mcp/serialization.py`，统一提供 synchronous hook 和 asynchronous
  MCP tool 的 shared lock boundary。
- `src/ai_video_mcp/server.py` 的 8 个 public tool wrappers 全部通过统一
  `run_serialized()` path 执行。
- `src/ai_video_mcp/analysis_hook.py` 删除重复的 worker-lock ownership，改为复用同一
  helper，保证 background hook 与 direct Agent calls 互斥。
- cancellation regression coverage 固定了 pre-lock 与 post-start 两种语义；cross-process
  test 固定了不同 Python process 的峰值并发数为 1。
- README、contract matrix 与 runtime baseline 已同步当前行为和边界。

本轮刻意没有修改 existing dirty `.codex/config.toml`。尤其没有把整个 MCP server 设为
自动批准，因为 `video_apply_optimization` 可以写 Legacy YAML；执行串行化不应放宽 tool
approval 或 mutation contract。

## Verification And Evidence

Implementation commit：

```text
cbfb36e6062d8c9c670f2cc020f8edc601b4f0c4 fix: serialize video analysis MCP calls
```

Fresh exact commit-range Harness receipt：

```text
.agent/harness/runs/mcp-serial-agents-commit/receipt.json
11829dae16840b678b6ba9c6014fd62e874f3bb9..cbfb36e6062d8c9c670f2cc020f8edc601b4f0c4
```

Receipt verification 结果：

- Harness tests：`185 passed`。
- MCP tests：`58 passed, 1 skipped`。
- Architecture Gate：`PASS`，`0 errors`、`0 warnings`、`0 info`。
- policy audit：无 unmapped、unverified 或 unreferenced owned paths。
- freshness、artifact hashes、completion proof、snapshot match 与 workspace stability 均已验证。

Real two-client stdio proof 使用 MCP 自身的隔离 Python runtime 启动两个独立
`ClientSession`：

- 两个 client 均列出 8 个 public tools。
- parent process 持有 shared lock 时，两边均保持 blocked：
  `blocked_while_parent_held_lock: [true, true]`。
- release 后两个 `video_probe` 均成功返回，且 `is_error: false`。
- proof 只读取 existing local video，没有 Provider submit、媒体生成或 lifecycle write。

Native `reviewer_xhigh` 在两轮 cancellation blocker 修复后完成 scoped re-review，最终
`Verdict: accept`，无 blocking issues 或 non-blocking concerns。

## Remaining Risks

- 多个长期存活的 MCP process 仍可能各自保留 Whisper/model cache；如果目标扩大为单一
  GPU-resident model owner，需要单独设计 shared daemon、CPU routing 或 deterministic
  unload policy。
- 只有加载本 repository project config 且 MCP startup 成功的 Agent 才能使用该 server；
  repository 外 session 或启动失败不能由 file lock 补救。
- 已经运行且加载旧 Python module 的 MCP process 需要重启或重新连接，才能获得本次
  committed behavior；本轮没有主动终止任何 existing process。
- 本轮没有执行 live Provider、ComfyUI、媒体质量、P6、activation、Final Acceptance、
  push 或 release 验证。

## Agent Guardrails

- 不得把 client-side parallel scheduling hint 当成跨 Agent/process lock。
- 不得把 execution serialization 描述成 shared cache、single GPU owner 或 resource quota。
- 不得为了“每个 Agent 都能用”而 server-wide 自动批准
  `video_apply_optimization` 等 write-capable tool。
- 不得把 successful MCP analysis 当成 Manifest write、candidate activation、P6 或 Final
  Acceptance。
- 修改 lock path、serialization owner、tool wrappers 或 hook execution path 时，必须同时
  覆盖 cross-process overlap、pre-lock cancellation 和 post-start repeated cancellation。
