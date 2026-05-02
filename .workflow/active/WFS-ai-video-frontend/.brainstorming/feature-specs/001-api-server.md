# Feature Spec: F-001 - api-server

**Priority**: High
**Contributing Roles**: system-architect, ux-expert, ui-designer
**Status**: Draft (from synthesis)

## 1. Requirements Summary

### 功能需求

- API Server MUST 将现有 CLI 模块（`pipeline.py`, `comfy_client.py`, `config.py`, `workflow_renderer.py`）包装为 REST + SSE 端点，MUST NOT 修改现有模块的内部实现
- API Server MUST 使用 FastAPI (Python) 作为框架，MUST NOT 引入次级运行时（如 Node.js）
- API Server MUST 实现 SSE 作为 MVP 实时通信方案，SHOULD 预留 WebSocket 升级能力
- PipelineRunner.run() MUST 通过 `run_in_executor` 包装实现非阻塞调用
- Run 生命周期 MUST 实现 pending → running → succeeded/failed 状态机，且支持 resume
- 系统 MUST 限制同时运行 1 个 Run（本地单用户场景），第二个请求 MUST 返回 409 Conflict
- API Server MUST 提供项目、镜头、运行、画廊、验证等完整 CRUD 端点
- API Server MUST 提供统一错误响应格式（EP-001），包含 `code`, `message`, `detail`, `suggestion` 字段
- API Server MUST 提供 `/health` 端点（EP-005），检测 ComfyUI 可达性、磁盘空间、ffmpeg 可用性

### 用户体验需求

- 所有 API 错误 MUST 映射为用户可读的中文描述，MUST 包含可操作的下一步建议
- SSE 事件 MUST 包含 `message` 字段，前端可直接显示为状态文案
- SSE 连接 MUST 每 15s 发送心跳事件，MUST 支持断线重连（`Last-Event-ID`）
- CRUD 端点 MUST 支持分页（`offset`/`limit`），文件服务端点 MUST 支持 Range 请求
- 每个 API 请求 MUST 返回 `X-Request-ID` header

### 技术需求

- API 层 MUST 通过 Service Layer 编排，MUST NOT 在 Router 中直接调用现有模块
- 线程间通信 MUST 通过 `asyncio.Queue` 或 `asyncio.run_coroutine_threadsafe` 桥接
- SSE Manager MUST 维护最近 200 条事件用于重连重放，事件带 TTL（10 分钟）
- 文件服务 MUST 防止路径遍历攻击，MUST 使用 `Path.resolve()` + `startswith()` 校验
- 视口范围限定为 1280px+ 桌面端（EP-007），API 响应无需做移动端适配

## 2. Design Decisions

### Decision 1: FastAPI + SSE 先行 + WebSocket 预留

- **Context**: 前端需要实时获取生成进度，需选择通信协议
- **Options Considered**:
  - (A) 纯 REST 轮询 — 实现简单但延迟高、资源浪费
  - (B) WebSocket 全双工 — 功能最强但 MVP 复杂度高，需处理连接管理和协议设计
  - (C) SSE 先行 + WebSocket 预留 — MVP 快速上线，单向推送足够，后续按需升级
- **Chosen Approach**: 方案 C。MVP 用 SSE 实现单向进度推送，WebSocket 能力在架构中预留但不实现
- **Trade-offs**: 优势：MVP 开发速度快，SSE 原生支持断线重连；劣势：无法实现双向交互控制（如暂停/恢复需等 WebSocket），SSE 仅支持文本推送
- **Source**: system-architect (D-007), ux-expert (SSE 事件 schema), ui-designer (连接状态 UI)

### Decision 2: run_in_executor 包装同步代码

- **Context**: PipelineRunner 是同步阻塞调用，直接在 FastAPI 事件循环中执行会阻塞所有请求
- **Options Considered**:
  - (A) 全量重写 PipelineRunner 为 async — 改动大，风险高，影响现有 CLI
  - (B) run_in_executor 低侵入包装 — MVP 最小改动，通过线程池隔离
  - (C) 独立子进程运行 pipeline — 隔离好但通信复杂
- **Chosen Approach**: 方案 B。MVP 用 `concurrent.futures.ThreadPoolExecutor(max_workers=1)` 包装 `PipelineRunner.run()`，通过 `asyncio.run_coroutine_threadsafe` 桥接 SSE 推送
- **Trade-offs**: 优势：零侵入现有代码，快速上线；劣势：线程间桥接增加复杂度，后续仍需逐步异步化热点方法
- **Source**: system-architect (D-008), cross-cutting Section 7

### Decision 3: 统一错误响应契约 (EP-001)

- **Context**: 现有 `errors.py` 定义了结构化错误（`AiVideoError` with `code`, `user_message`, `technical_detail`），但前端需要统一的错误处理模式
- **Options Considered**:
  - (A) 直接透传 Python 异常信息 — 前端难以解析，用户不可读
  - (B) 统一信封格式 `{ data, error, meta }` + 结构化错误 — 前端可统一处理，错误可操作
- **Chosen Approach**: 方案 B。所有 API 响应 MUST 使用统一信封格式，错误字段包含 `code`, `message`, `detail`, `suggestion`，前端可分三层展示（字段级/功能级/系统级）
- **Trade-offs**: 优势：前端错误处理一致，用户可理解可操作；劣势：增加 API 层包装代码量
- **Source**: ux-expert (Error Response Format), ui-designer (Error Hierarchy), EP-001

### Decision 4: Run 状态机与并发控制

- **Context**: 本地单用户场景下，同时只能运行一个 Run，需明确状态转换规则
- **Options Considered**:
  - (A) 允许多 Run 并发 — 需要资源管理，MVP 过于复杂
  - (B) 单 Run + 内存注册表 — 简单可靠，符合本地场景
- **Chosen Approach**: 方案 B。API Server 维护内存 Run Registry（`dict[str, RunState]`），活跃 Run 存在时拒绝新请求（409），支持 resume 恢复失败 Run
- **Trade-offs**: 优势：实现简单，状态一致性好；劣势：重启后丢失活跃 Run 信息（依赖 manifest 恢复）
- **Source**: system-architect (Run State Machine), conflict_map (RESOLVED)

### Decision 5: ComfyUI 连接健康状态 (EP-005)

- **Context**: 用户启动生成前需确认 ComfyUI 可用，避免运行后立即失败
- **Options Considered**:
  - (A) 仅在 Run 启动时检查 — 太晚，浪费用户等待时间
  - (B) 持久健康指示器 + 启动前预检查 — 用户随时可知状态，减少无效操作
- **Chosen Approach**: 方案 B。API Server MUST 提供 `/health` 端点（检测 ComfyUI/磁盘/ffmpeg），前端 MUST 在页面头部持久显示连接状态指示器，Run 启动前 MUST 执行 pre-flight health check
- **Trade-offs**: 优势：主动预防，用户信心提升；劣势：健康检查增加 API 调用开销（MUST 缓存结果）
- **Source**: EP-005, ux-expert (Connection Test), ui-designer (SSE Connection State)

### Decision 6: 优先级对齐 — 架构 High vs UX Medium

- **Context**: conflict_map 标记 F-001 存在优先级对齐冲突：system-architect 视为 High，ux-expert 视为 Medium（API 不直接面向用户）
- **Resolution**: 架构优先级保持 High（API 是所有前端功能的基座），UX 影响通过 API 契约（错误格式、SSE schema、延迟预算）间接实现。UX 角色关注点转化为 API 契约约束，写入 API 设计而非独立 UX 功能
- **Source**: conflict_map (RESOLVED: arch High, UX impact Medium via API contract)

## 3. Interface Contract

### REST API 端点

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/health` | 健康检查 | `HealthCheck` |
| GET | `/api/projects` | 列出项目 | `list[ProjectSummary]` |
| POST | `/api/projects` | 创建项目 | `ProjectDetail` (201) |
| GET | `/api/projects/{name}` | 项目详情 | `ProjectDetail` |
| PUT | `/api/projects/{name}` | 更新项目 | `ProjectDetail` |
| DELETE | `/api/projects/{name}` | 删除项目 | 204 |
| GET | `/api/projects/{name}/shots` | 列出镜头 | `list[ShotSummary]` |
| PUT | `/api/projects/{name}/shots` | 替换镜头列表 | `list[ShotSummary]` |
| POST | `/api/projects/{name}/shots` | 添加镜头 | `ShotSummary` (201) |
| PUT | `/api/projects/{name}/shots/{shot_id}` | 更新镜头 | `ShotSummary` |
| DELETE | `/api/projects/{name}/shots/{shot_id}` | 删除镜头 | 204 |
| PATCH | `/api/projects/{name}/shots/reorder` | 重排镜头 | `list[ShotSummary]` |
| POST | `/api/projects/{name}/validate` | 校验项目 | `ValidationResult` |
| POST | `/api/projects/{name}/shots/validate` | 校验镜头 | `ValidationResult` |
| POST | `/api/runs` | 启动运行 | `RunDetail` (202) |
| GET | `/api/runs` | 列出运行 | `list[RunSummary]` |
| GET | `/api/runs/{run_id}` | 运行详情 | `RunDetail` |
| POST | `/api/runs/{run_id}/resume` | 恢复运行 | `RunDetail` (202) |
| POST | `/api/runs/{run_id}/cancel` | 取消运行 | `RunDetail` (200) |
| GET | `/api/runs/{run_id}/events` | SSE 事件流 | `text/event-stream` |
| GET | `/api/runs/{run_id}/gallery` | 画廊索引 | `GalleryIndex` |
| GET | `/api/validate/comfy-url` | 校验 ComfyUI | `ValidationResult` |
| GET | `/api/validate/workflow-template` | 校验模板 | `ValidationResult` |
| POST | `/api/projects/{name}/params/validate` | 校验参数修改 | `ValidationResult` |
| POST | `/api/projects/{name}/shots/{shot_id}/workflow-preview` | 预览渲染后的 Workflow JSON | `WorkflowJSON` |
| POST | `/api/projects/{name}/shots/{shot_id}/workflow-diff` | 对比两个 Workflow JSON | `WorkflowDiff` |
| POST | `/api/runs/re-run` | 基于历史 Run 重跑 | `RunDetail` (202) |
| POST | `/api/runs/{run_id}/shots/{shot_id}/re-run` | 重跑单个 shot | `RunDetail` (202) |
| GET | `/api/runs/{run_id}/pipeline-state` | 获取管道状态快照 | `PipelineState` |
| GET | `/api/runs/{run_id}/config-drift` | 配置漂移检测 | `ConfigDriftResult` |

### 统一错误响应格式 (EP-001)

```json
{
  "error": {
    "code": "CONFIG_INVALID",
    "message": "项目配置验证失败：ComfyUI 地址不可达",
    "detail": "Connection refused: http://127.0.0.1:8188",
    "suggestion": "请确认 ComfyUI 已启动，或修改项目设置中的生成服务地址"
  }
}
```

### SSE 事件类型

| Event Type | Payload 摘要 | 触发时机 |
|------------|-------------|---------|
| `run:started` | `{run_id, shot_count, project_name}` | Run 进入 running |
| `shot:started` | `{run_id, shot_id, index, total, attempt}` | Shot 开始执行 |
| `shot:completed` | `{run_id, shot_id, clip_path, last_frame_path, duration_s}` | Shot 成功 |
| `shot:progress` | `{run_id, shot_id, percentage}` | Shot 执行中（MVP 估算） |
| `shot:failed` | `{run_id, shot_id, error_code, message, retryable, next_attempt}` | Shot 失败 |
| `run:stitching` | `{run_id, current_shot, total_shots}` | 开始拼接 |
| `run:completed` | `{run_id, final_output, total_duration_s}` | Run 成功 |
| `run:failed` | `{run_id, error_code, message}` | Run 失败 |
| `run:cancelled` | `{run_id}` | Run 被取消 |

### 健康检查响应 (EP-005)

```json
{
  "status": "healthy|degraded|unhealthy",
  "checks": {
    "comfyui": {"status": "up|down", "latency_ms": 42},
    "disk": {"status": "ok|low", "free_gb": 15.3},
    "ffmpeg": {"status": "available|missing"}
  }
}
```

## 4. Constraints & Risks

| 约束/风险 | 严重度 | 缓解策略 |
|-----------|--------|---------|
| PipelineRunner 同步阻塞导致 SSE 推送延迟 | High | 独立 executor 线程 + queue 桥接 |
| 线程间状态竞争 | Medium | asyncio.Lock 保护 Run Registry |
| ComfyUI 离线导致 Run 启动后立即失败 | Medium | pre-flight health check (EP-005) |
| SSE 连接泄漏导致内存增长 | Medium | 心跳超时 + 最大连接数限制（10） |
| 断线重连丢失事件 | Medium | 事件缓冲（200 条）+ Last-Event-ID 重放 |
| 路径遍历攻击 | High | Path.resolve() + startswith() 校验 |
| 重启后丢失 Run Registry | Low | 依赖 manifest.json 恢复状态 |

## 5. Acceptance Criteria

1. API Server 启动后 `/health` 端点 MUST 在 1s 内返回 ComfyUI、磁盘、ffmpeg 检查结果
2. 创建项目 MUST 生成与 `load_project()` 兼容的 `project.yaml`，写入后回读验证一致
3. 启动 Run MUST 返回 202，SSE 流 MUST 在 5s 内推送 `run:started` 事件
4. 正在执行 Run 时第二个 Run 请求 MUST 返回 409 Conflict
5. SSE 断线重连 MUST 支持 `Last-Event-ID`，服务端 MUST 从指定 ID 后重放事件
6. 所有错误响应 MUST 符合 EP-001 统一格式，MUST 包含中文 `message` 和 `suggestion`
7. Gallery 文件服务 MUST 支持 HTTP Range Requests，MUST 阻止 `../` 路径遍历
8. Run 取消 MUST 在当前 Shot 完成后停止，状态 MUST 记录为 failed + "cancelled_by_user"。SSE 事件 `run:cancelled` 仅为通知事件，不影响 Run 最终状态分类（cancelled 是 failed 的子类型）
9. 失败 Run 的 resume MUST 跳过已完成的 Shot，重新执行失败项
10. API 延迟：项目 CRUD < 500ms，Shot 列表 < 300ms，启动生成 < 1s

## 6. Detailed Analysis References

- @../system-architect/analysis-F-001-api-server.md — 架构设计、数据模型、Run 状态机、异步架构、取消机制
- @../ux-expert/analysis-F-001-api-server.md — 错误格式 UX 约束、SSE 事件 schema、延迟预算、错误码映射
- @../ui-designer/analysis-F-001-api-server.md — API 消费模式、加载状态架构、错误视觉规范、Toast 系统
- @../system-architect/analysis-cross-cutting.md — 三层架构、Run Registry、并发模型
- @../guidance-specification.md#feature-decomposition — 功能定义与优先级

## 7. Cross-Feature Dependencies

- **Depends on**: 无（F-001 是基座功能，所有其他功能依赖它）
- **Required by**: F-002 (项目 CRUD), F-003 (Shot CRUD + 排序), F-004 (Run 启动 + SSE), F-005 (Gallery 文件服务), F-006 (Run 列表 + 详情), F-007 (参数验证 + 预览 + 重跑)
- **Shared patterns**:
  - 统一错误响应格式 (EP-001) — 所有功能的前端错误处理基础
  - SSE Manager — F-004 和 F-007 的 re-run 共用
  - `/health` 端点 — F-002 连接测试、F-004 启动前检查共用
  - API 延迟预算 — 所有功能的前端加载状态策略基础
- **Integration points**:
  - F-004: `POST /api/runs` + `GET /api/runs/{run_id}/events` SSE 流
  - F-007: `POST /api/projects/{name}/params/validate` + `POST /api/runs/re-run`
  - F-005: `GET /api/runs/{run_id}/gallery` + Range-based 文件服务
