# F-004: Generation Monitor - System Architect Analysis

**Framework Reference**: @../guidance-specification.md
**Priority**: High | **Related Roles**: system-architect, ux-expert

## 1. Architecture Overview

Generation Monitor 是前端最核心的实时交互组件，架构挑战在于：将同步阻塞的 PipelineRunner 执行过程转化为可观测的 SSE 事件流，实现 shot 级状态上报和管道节点视图的实时更新。

## 2. SSE Architecture

### 2.1 Connection Manager

```
                    +-------------------+
                    |  SSE Manager      |
                    |  - connections:   |
                    |    dict[run_id,   |
                    |     set[client]]  |
                    |  - event_queue:   |
                    |    asyncio.Queue  |
                    +--------+----------+
                             |
              +--------------+--------------+
              |              |              |
         +----v---+    +----v---+    +----v---+
         | Client1|    | Client2|    | Client3|
         | (SSE)  |    | (SSE)  |    | (SSE)  |
         +--------+    +--------+    +--------+
```

**SSE Manager 设计约束**：
- MUST 为每个 run_id 维护独立的订阅者集合
- MUST 使用 `asyncio.Queue` 作为事件缓冲区（容量 100）
- MUST 在队列满时丢弃最老事件（非阻塞写入）
- MUST 在客户端断连时自动清理
- MUST 支持心跳机制（每 30s 发送 `:heartbeat\n\n`），防止代理超时
- MUST 在 Run 完成后保持连接 60s 再关闭（确保客户端收到最终事件）

### 2.2 Event Bridge (Thread -> Asyncio)

PipelineRunner 在 executor 线程中执行，SSE 推送在事件循环线程中执行。桥接设计：

```
[Executor Thread]                    [Event Loop Thread]
PipelineRunner                       FastAPI
  |                                    |
  progress_callback(msg)               |
  |                                    |
  v                                    |
  thread-safe Queue ----bridge----> asyncio.Queue
                                       |
                                       v
                                 SSE Manager.broadcast()
                                       |
                                       v
                                 EventSourceResponse
```

**桥接约束**：
- MUST 使用 `asyncio.run_coroutine_threadsafe()` 从线程推送到事件循环
- progress_callback MUST 在线程安全的环境中解析消息并构造事件
- MUST 定义结构化的事件格式，MUST NOT 传递原始 progress 文本

### 2.3 Event Schema

SSE 事件 MUST 使用以下格式：

```
event: {event_type}
id: {event_id}
data: {json_payload}

```

**event_id** MUST 单调递增，用于客户端断线重连时的 `Last-Event-ID` 处理。

### 2.4 Event Types

| Event Type | Data Schema | Trigger |
|------------|-------------|---------|
| `run:started` | `{run_id, shot_count, project_name}` | Run 进入 running |
| `shot:started` | `{run_id, shot_id, index, total, attempt}` | Shot 开始执行 |
| `shot:progress` | `{run_id, shot_id, percentage}` | Shot 执行中（MVP: 估算） |
| `shot:completed` | `{run_id, shot_id, clip_path, last_frame_path, duration_s}` | Shot 成功 |
| `shot:failed` | `{run_id, shot_id, error_code, message, retryable, next_attempt}` | Shot 失败（可能重试） |
| `run:stitching` | `{run_id, current_shot, total_shots}` | 开始拼接 |
| `run:completed` | `{run_id, final_output, total_duration_s}` | Run 成功 |
| `run:failed` | `{run_id, error_code, message}` | Run 失败 |
| `run:cancelled` | `{run_id}` | Run 被取消 |

## 3. Shot Status State Machine

```
     +---------+   start_shot   +---------+   submit_prompt   +---------+
     | pending |--------------->| queued  |------------------>| running |
     +---------+                +---------+                   +----+----+
                                                              |  |
                                                    succeed   |  | fail (retryable)
                                                              |  v
                                                    +---------+  +--------+
                                                    |succeeded|  |retrying|--> queued
                                                    +---------+  +--------+
                                                              |
                                                    fail (exhausted)
                                                              v
                                                        +---------+
                                                        | failed  |
                                                        +---------+
```

**状态转换表**：

| From | Event | To | Condition |
|------|-------|----|-----------|
| pending | shot_started | queued | Run is active |
| queued | prompt_submitted | running | ComfyUI accepted |
| running | job_completed | succeeded | Output valid |
| running | job_failed | retrying | retryable && attempts < max |
| retrying | auto | queued | Immediate re-queue |
| running | job_failed | failed | !retryable OR attempts >= max |

**前端渲染约束**：
- pending/queued MUST 渲染为灰色节点
- running MUST 渲染为蓝色脉冲动画节点
- succeeded MUST 渲染为绿色节点 + clip 缩略图预览
- failed MUST 渲染为红色节点 + 错误信息 tooltip
- retrying MUST 渲染为黄色节点 + 重试次数标注

## 4. Pipeline Node View Data Model

### 4.1 Pipeline State Response

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/runs/{run_id}/pipeline-state` | 获取当前管道状态快照 |

Response:
```json
{
  "run_id": "run-20260502-143000-abcd1234",
  "status": "running",
  "shots": [
    {
      "shot_id": "shot_01",
      "status": "succeeded",
      "index": 0,
      "total": 4,
      "clip_thumbnail": "/api/gallery/runs/run-.../shots/shot_01/clip.mp4/thumb",
      "duration_s": 45.2
    },
    {
      "shot_id": "shot_02",
      "status": "running",
      "index": 1,
      "total": 4,
      "attempt": 1,
      "started_at": "2026-05-02T14:31:00Z"
    }
  ],
  "final_output": null
}
```

- 此端点 MUST 同时通过 SSE 推送变更（客户端无需轮询）
- 首次连接 MUST 发送完整状态快照，后续只推送增量

## 5. Reconnection Strategy

### 5.1 Client-Side

- SSE 客户端 MUST 在断线后自动重连（`EventSource` 内置行为）
- 重连时 MUST 发送 `Last-Event-ID` header
- 服务端 MUST 支持从指定 event_id 之后重放事件

### 5.2 Server-Side Event Buffer

- SSE Manager MUST 维护最近 N 条事件（N=200）用于重连重放
- 事件 MUST 带 TTL（默认 10 分钟），超时后清理
- 重放时 MUST 从 `Last-Event-ID` 之后开始发送
- 如果请求的 event_id 已被清理，MUST 发送完整状态快照 + 后续事件

## 6. Cancellation Flow

```
[User clicks Cancel]
       |
       v
PATCH /api/runs/{run_id}/cancel
       |
       v
[RunService] sets _cancelled = True
       |
       v
[Executor Thread] checks _cancelled before next shot
       |
       v
[PipelineRunner] completes current shot, skips remaining
       |
       v
[SSE] broadcasts run:cancelled
       |
       v
[Manifest] status = "failed", error = "cancelled_by_user"
```

- 当前 shot MUST 完成后再取消（PipelineRunner 不支持中途中断单 shot）
- 已完成的 shot 产物 MUST 保留（manifest 记录）
- 取消的 Run MUST 可通过 resume 端点继续执行

## 7. Progress Estimation (MVP)

MVP 阶段无法获取 ComfyUI 节点级进度，SHOULD 使用以下估算策略：

- shot 级 `percentage` = (已用时间 / 预估总时间) * 100
- 预估总时间 = `defaults.clip_seconds * baseline_seconds_per_second`
- `baseline_seconds_per_second` SHOULD 基于历史 Run 统计得出，MVP 可固定为 30s/clip-second
- 前端 MUST 将估算进度标记为"estimated"，避免误导用户

## 8. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| SSE 连接泄漏导致内存增长 | Medium | 心跳超时 + 最大连接数限制（10） |
| 线程-事件循环桥接死锁 | High | 使用 `run_coroutine_threadsafe` + 非阻塞 queue |
| 断线重连丢失事件 | Medium | 事件缓冲 + Last-Event-ID 重放 |
| 进度估算不准确 | Low | 明确标注"estimated"，后续接入 ComfyUI WS 获取精确进度 |
| 长时间无事件导致代理超时 | Medium | 30s 心跳保活 |
