# Cross-Cutting Architecture Decisions

**Framework Reference**: @../guidance-specification.md

## 1. Layered Architecture

系统采用三层架构，明确各层职责边界：

```
+--------------------------------------------------+
|  Frontend (React + shadcn/ui)                     |
|  - REST calls -> API Layer                        |
|  - SSE subscription -> Event Stream               |
+--------------------------------------------------+
|  API Layer (FastAPI)                              |
|  - Routers: /projects, /shots, /runs, /gallery   |
|  - Services: ProjectService, RunService, etc.     |
|  - SSE Manager: event bus + connection lifecycle  |
+--------------------------------------------------+
|  Existing Modules (ai_video.*)                    |
|  - config, pipeline, comfy_client, manifest      |
|  - models, errors, workflow_renderer             |
+--------------------------------------------------+
```

**关键约束**：
- API Layer MUST NOT 直接操作文件系统路径，MUST 通过 Service Layer 间接调用
- Service Layer MUST 通过 `run_in_executor` 包装所有同步调用
- Frontend MUST NOT 直接访问 ComfyUI API，MUST 通过 API Layer 代理

## 2. State Management

### 2.1 Run State Machine (Core Lifecycle)

Run 是最复杂的状态实体，其生命周期定义如下：

```
                    +-----------+
                    |  pending  |
                    +-----+-----+
                          |
                     start_run()
                          |
                    +-----v-----+
              +---->|  running   |<----+
              |     +-----+-----+     |
              |           |            |
              |    shot_failed()      resume()
              |           |            |
              |     +-----v-----+     |
              |     |  failed    |-----+
              |     +-----------+
              |           |
              |   all_shots_succeeded() + stitch_completed()
              |           |
              |     +-----v-----+
              +---->| succeeded  |
                    +-----------+
```

**Transition Table**:

| Current | Event | Next | Guard | Side Effect |
|---------|-------|------|-------|-------------|
| pending | start_run | running | disk_space_ok | create run directory, write initial manifest |
| running | shot_completed | running | remaining_shots > 0 | append ShotRecord, atomic_write_manifest |
| running | all_shots_done + stitch_ok | succeeded | all clips valid | set final_output, write manifest |
| running | shot_failed + no_retry | failed | last_attempt_exhausted | record error, write manifest |
| failed | resume | running | manifest exists | reload shots, skip succeeded |

### 2.2 Shot State (Within Run)

```
pending -> queued -> running -> succeeded
                              -> failed -> (retry) -> running
                              -> failed (exhausted)
```

MVP MUST 只上报 shot 级状态（pending/queued/running/succeeded/failed），MAY 在后续迭代中上报 ComfyUI 节点级进度。

### 2.3 In-Memory Run Registry

API Server MUST 维护一个内存中的 Run Registry，用于追踪活跃 Run 的状态并支持 SSE 推送：

- 类型: `dict[str, RunState]`，key 为 run_id
- RunState MUST 包含: status, current_shot_index, shot_statuses[], started_at
- RunState MUST 在 `run_in_executor` 的 progress_callback 中更新
- RunState MUST NOT 持有 PipelineRunner 引用（避免 GC 阻塞）
- Run 完成/失败后 SHOULD 从 Registry 中清理（保留最近 N 条用于查询）

## 3. Error Handling Strategy

### 3.1 Error Classification

复用现有 `ErrorCode` 枚举，API 层 MUST 将其映射为 HTTP 状态码：

| ErrorCode Category | HTTP Status | Retryable | Example |
|--------------------|-------------|-----------|---------|
| CONFIG_INVALID | 400 | No | YAML parse error |
| WORKFLOW_INVALID | 400 | No | Template validation failed |
| BINDING_INVALID | 400 | No | JSONPath binding error |
| COMFY_UNAVAILABLE | 503 | Yes | ComfyUI offline |
| COMFY_SUBMISSION_FAILED | 502 | Varies | Prompt rejected |
| COMFY_JOB_TIMEOUT | 504 | Yes | Job exceeded timeout |
| COMFY_JOB_FAILED | 500 | Yes | ComfyUI runtime error |
| COMFY_OUTPUT_MISSING | 502 | Yes | Artifact not found |
| OUTPUT_INVALID | 500 | No | ffmpeg validation failed |
| FFMPEG_FAILED | 500 | No | ffmpeg process error |
| MANIFEST_INVALID | 500 | No | Corrupt manifest |
| DISK_SPACE_LOW | 507 | No | Insufficient disk |

### 3.2 Unified Error Response Format

API 层 MUST 返回统一错误响应：

```json
{
  "error": {
    "code": "comfy_unavailable",
    "message": "ComfyUI is unavailable.",
    "detail": "Connection refused: 127.0.0.1:8188",
    "retryable": true
  }
}
```

### 3.3 Recovery Mechanisms

- **ComfyUI 不可用**: API MUST 返回 503 + Retry-After header，Frontend SHOULD 展示重试提示
- **Job 超时**: PipelineRunner 内置重试（max_attempts），API 层 MUST 透传重试状态
- **磁盘空间不足**: API MUST 在 Run 启动前检查（`ensure_min_free_space`），返回 507
- **Manifest 损坏**: API MUST 返回 500，Frontend SHOULD 提示用户检查文件

## 4. Observability Requirements

### 4.1 Metrics (Minimum 5)

| Metric | Type | Description |
|--------|------|-------------|
| `run_duration_seconds` | Histogram | Run 从开始到完成/失败的总时长 |
| `shot_duration_seconds` | Histogram | 单个 Shot 从开始到完成/失败的时长 |
| `active_runs_gauge` | Gauge | 当前活跃 Run 数量 |
| `comfyui_request_duration_seconds` | Histogram | ComfyUI HTTP 请求耗时 |
| `error_count_total` | Counter | 按 error_code 分类的错误计数 |
| `sse_connections_gauge` | Gauge | 当前 SSE 连接数 |
| `api_request_duration_seconds` | Histogram | API 请求耗时（按路由分组） |

### 4.2 Log Events

API Layer MUST 输出以下结构化日志事件（JSON 格式）：

- `run.started`: run_id, shot_count, project_name
- `run.completed`: run_id, status, duration_seconds
- `shot.started`: run_id, shot_id, attempt
- `shot.completed`: run_id, shot_id, status, duration_seconds
- `comfyui.request`: method, path, status_code, duration_ms
- `sse.connected`: client_id, run_id
- `sse.disconnected`: client_id, run_id, reason
- `api.request`: method, path, status_code, duration_ms

### 4.3 Health Checks

API Server MUST 提供 `/health` 端点，返回：

```json
{
  "status": "healthy" | "degraded" | "unhealthy",
  "checks": {
    "comfyui": {"status": "up" | "down", "latency_ms": 42},
    "disk": {"status": "ok" | "low", "free_gb": 15.3},
    "ffmpeg": {"status": "available" | "missing"}
  }
}
```

- ComfyUI 检查: MUST 调用 `comfy.check_available()`，MUST 设置 5s 超时
- 磁盘检查: MUST 报告 output.root 可用空间
- FFmpeg 检查: SHOULD 验证 ffmpeg 二进制可用性

## 5. Deployment Strategy

### 5.1 MVP: Local Single-Process

```
[Browser] --HTTP/SSE--> [FastAPI Server] --sync--> [PipelineRunner] --HTTP--> [ComfyUI]
                                         --sync--> [ComfyClient]
                                         --sync--> [ffmpeg]
```

- FastAPI + Frontend 静态文件 MUST 运行在同一进程
- 默认端口: 8000 (API) + ComfyUI 8188
- 启动方式: `ai-video serve` 命令或 `uvicorn ai_video.api:app`

### 5.2 Future: Remote-Split

```
[Browser] --HTTPS/WSS--> [Nginx] --HTTP--> [FastAPI Server] --HTTP--> [ComfyUI (remote)]
```

- Frontend MUST 构建为静态资源，SHOULD 支持独立部署
- API Server MUST 支持 CORS 配置
- WebSocket 预留 MUST 支持通过 Nginx 代理升级

## 6. API Versioning

- MVP MUST NOT 引入 URL 版本前缀（单版本足够）
- API 路由 MUST 组织为: `/api/projects/`, `/api/shots/`, `/api/runs/`, `/api/gallery/`
- 未来版本升级 SHOULD 使用 Header-based versioning (`Accept: application/vnd.ai-video.v2+json`)

## 7. Concurrency Model

- MVP MUST 限制同时运行 1 个 Run（本地单用户场景）
- API Server MUST 拒绝第二个 Run 请求（返回 409 Conflict）
- `run_in_executor` MUST 使用独立线程（非默认 asyncio executor），避免阻塞事件循环
- SSE 推送 MUST 在事件循环线程中执行，MUST NOT 从 executor 线程直接推送
- 线程间通信 MUST 通过 `asyncio.Queue` 或 `asyncio.Event` 桥接
