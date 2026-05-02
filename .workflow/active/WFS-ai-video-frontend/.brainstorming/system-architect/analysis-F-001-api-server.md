# F-001: API Server - System Architect Analysis

**Framework Reference**: @../guidance-specification.md
**Priority**: High | **Related Roles**: system-architect

## 1. Architecture Overview

API Server 是整个前端系统的核心枢纽，负责将现有 CLI 模块的同步调用包装为异步 REST + SSE 端点。它 MUST 不修改现有 `pipeline.py`、`comfy_client.py`、`config.py` 的内部实现，仅通过 Service Layer 进行编排。

### Component Structure

```
api/
  __init__.py
  app.py              # FastAPI application factory
  deps.py             # Dependency injection (get_comfy, get_pipeline, etc.)
  routers/
    projects.py       # /api/projects
    shots.py          # /api/shots
    runs.py           # /api/runs + SSE
    gallery.py        # /api/gallery
    health.py         # /health
  services/
    project_service.py
    run_service.py
    shot_service.py
  sse/
    manager.py        # SSE connection manager + event bus
    events.py         # Event type definitions
  models/
    requests.py       # API request schemas
    responses.py      # API response schemas
```

## 2. Data Model

### 2.1 Project Entity

```
Project
  +-- project_name: str         [REQUIRED, unique within workspace]
  +-- comfy: ComfyConfig
  |     +-- base_url: str       [DEFAULT: "http://127.0.0.1:8188"]
  |     +-- allow_non_local: bool [DEFAULT: false]
  +-- workflow: WorkflowConfig
  |     +-- template: Path      [REQUIRED, must exist]
  |     +-- binding: Path       [REQUIRED, must exist]
  +-- output: OutputConfig
  |     +-- root: Path          [DEFAULT: "runs"]
  |     +-- min_free_gb: float  [DEFAULT: 1.0]
  +-- defaults: DefaultsConfig
  |     +-- width: int          [DEFAULT: 512]
  |     +-- height: int         [DEFAULT: 512]
  |     +-- fps: int            [DEFAULT: 16]
  |     +-- clip_seconds: int   [DEFAULT: 2]
  |     +-- seed: int           [DEFAULT: 1]
  |     +-- seed_policy: str    [DEFAULT: "derived"]
  |     +-- negative_prompt: str [DEFAULT: ""]
  |     +-- style_prompt: str   [DEFAULT: ""]
  |     +-- max_attempts: int   [DEFAULT: 2]
  |     +-- poll_interval_seconds: float [DEFAULT: 2.0]
  |     +-- job_timeout_seconds: float  [DEFAULT: 1800.0]
  +-- characters: list[CharacterProfile] [DEFAULT: []]
```

**Relationship**: Project 1--* Shot (via shots.yaml), Project 1--* Character, Project 1--* Run

### 2.2 Run Entity (Complex Lifecycle)

```
Run
  +-- run_id: str               [PK, auto-generated: "run-{timestamp}-{uuid8}"]
  +-- status: enum              [pending|running|succeeded|failed]
  +-- created_at: datetime      [auto]
  +-- updated_at: datetime      [auto, on every manifest write]
  +-- project_config_path: str  [REQUIRED for resume]
  +-- shot_list_path: str       [REQUIRED for resume]
  +-- project_config_hash: str  [integrity check]
  +-- workflow_template_hash: str
  +-- workflow_binding_hash: str
  +-- shots: list[ShotRecord]   [ordered, 1:1 with ShotSpec]
  +-- final_output: str|None    [path to final.mp4]
```

### 2.3 ShotRecord Entity

```
ShotRecord
  +-- shot_id: str              [PK within Run, matches ShotSpec.id]
  +-- status: str               [pending|running|succeeded|failed|stale]
  +-- attempts: list[AttemptRecord]
  +-- active_attempt: int       [DEFAULT: 0]
  +-- seed: int|None
  +-- clip_path: str|None
  +-- clip_hash: str|None
  +-- last_frame_path: str|None
  +-- last_frame_hash: str|None
  +-- normalized_clip_path: str|None
  +-- chain_input_hash: str|None
  +-- character_ref_hashes: dict[str, str]
  +-- rendered_workflow_path: str|None
  +-- comfy_prompt_id: str|None
  +-- started_at: datetime|None
  +-- completed_at: datetime|None
  +-- error: dict|None
```

### 2.4 Character Entity

```
CharacterProfile
  +-- id: str                   [PK, unique within project]
  +-- name: str                 [REQUIRED]
  +-- description: str          [DEFAULT: ""]
  +-- reference_images: list[Path] [DEFAULT: []]
  +-- ipadapter: IPAdapterConfig
  |     +-- weight: float       [DEFAULT: 1.0]
  |     +-- start_at: float|None
  |     +-- end_at: float|None
  +-- future_lora: FutureLoraConfig
        +-- path: Path|None
        +-- weight: float|None
```

## 3. Run State Machine (Detailed)

### ASCII Diagram

```
    +---------+     start_run()     +---------+
    | pending |-------------------->| running |
    +---------+                     +----+----+
         ^                               |
         |                               | shot_completed (remaining > 0)
         |                               v
         |                         +---------+  (loop)
         |                         | running |------+
         |                         +----+----+      |
         |                              |           |
         |     all_done + stitch_ok     | shot_failed (exhausted)
         |              v               v
         |        +-----------+   +---------+
         |        | succeeded |   | failed  |
         |        +-----------+   +----+----+
         |                             |
         +------- resume() ------------+
```

### Transition Table

| From | Event | To | Guard | Action |
|------|-------|----|-------|--------|
| pending | start_run | running | disk_space_ok, no_active_run | create_run_dir, write_manifest, start executor |
| running | shot_completed | running | remaining > 0 | append ShotRecord, push SSE shot_completed |
| running | all_done | succeeded | stitch_ok, all clips valid | set final_output, push SSE run_completed |
| running | shot_failed_exhausted | failed | max_attempts reached | record error, push SSE run_failed |
| failed | resume | running | manifest_valid, disk_space_ok | reload, skip succeeded, restart executor |

### SSE Event Types for Run

| Event | Payload | Trigger |
|-------|---------|---------|
| `run:started` | `{run_id, shot_count, status: "running"}` | Run enters running state |
| `shot:started` | `{run_id, shot_id, index, total}` | Shot begins execution |
| `shot:completed` | `{run_id, shot_id, status, clip_path}` | Shot succeeds |
| `shot:failed` | `{run_id, shot_id, error, retryable}` | Shot fails (may retry) |
| `run:completed` | `{run_id, status: "succeeded", final_output}` | All shots done + stitched |
| `run:failed` | `{run_id, status: "failed", error}` | Run fails irrecoverably |
| `run:progress` | `{run_id, completed, total, percentage}` | Any shot status change |

## 4. REST API Endpoints

### Projects

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| GET | `/api/projects` | List projects (scan workspace) | - | `list[ProjectSummary]` |
| POST | `/api/projects` | Create project | `CreateProjectRequest` | `ProjectDetail` (201) |
| GET | `/api/projects/{name}` | Get project detail | - | `ProjectDetail` |
| PUT | `/api/projects/{name}` | Update project config | `UpdateProjectRequest` | `ProjectDetail` |
| DELETE | `/api/projects/{name}` | Delete project | - | 204 |

### Shots

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| GET | `/api/projects/{name}/shots` | List shots | - | `list[ShotSummary]` |
| PUT | `/api/projects/{name}/shots` | Replace full shot list | `list[ShotSpec]` | `list[ShotSummary]` |
| POST | `/api/projects/{name}/shots` | Add a shot | `ShotSpec` | `ShotSummary` (201) |
| PUT | `/api/projects/{name}/shots/{shot_id}` | Update single shot | `ShotSpec` | `ShotSummary` |
| DELETE | `/api/projects/{name}/shots/{shot_id}` | Delete shot | - | 204 |
| PATCH | `/api/projects/{name}/shots/reorder` | Reorder shots | `{ordered_ids: list[str]}` | `list[ShotSummary]` |

### Runs

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| POST | `/api/runs` | Start a new run | `{project_name, run_id?}` | `RunDetail` (202) |
| GET | `/api/runs` | List runs | `?status=running\|succeeded\|failed` | `list[RunSummary]` |
| GET | `/api/runs/{run_id}` | Get run detail | - | `RunDetail` |
| POST | `/api/runs/{run_id}/resume` | Resume failed run | - | `RunDetail` (202) |
| POST | `/api/runs/{run_id}/cancel` | Cancel running run | - | `RunDetail` (200) |
| GET | `/api/runs/{run_id}/events` | SSE stream | - | `text/event-stream` |

### Validation

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| POST | `/api/projects/{name}/validate` | Validate project config | - | `ValidationResult` |
| POST | `/api/projects/{name}/shots/validate` | Validate shot list | - | `ValidationResult` |

## 5. Async Architecture

### Executor Wrapping Pattern

```python
# services/run_service.py
class RunService:
    async def start_run(self, project_name: str) -> RunDetail:
        if self._active_run_id:
            raise ConflictError("A run is already active")
        project, shots, binding, template = self._load_config(project_name)
        runner = PipelineRunner(project, shots, binding, template,
                                progress_callback=self._make_callback())
        run_id = runner._generate_run_id()  # or accept from request
        self._active_run_id = run_id
        self._run_registry[run_id] = RunState(status="running", ...)
        loop = asyncio.get_event_loop()
        loop.run_in_executor(self._executor, self._run_wrapper, runner, run_id)
        return self._to_detail(run_id)

    def _run_wrapper(self, runner: PipelineRunner, run_id: str):
        """Runs in thread pool - MUST bridge events to asyncio loop."""
        loop = asyncio.get_event_loop()
        try:
            manifest = runner.run(run_id=run_id)
            asyncio.run_coroutine_threadsafe(
                self._sse_manager.broadcast(run_id, "run:completed", ...), loop)
        except Exception as exc:
            asyncio.run_coroutine_threadsafe(
                self._sse_manager.broadcast(run_id, "run:failed", ...), loop)
        finally:
            self._active_run_id = None
```

**关键约束**：
- `_run_wrapper` MUST 通过 `asyncio.run_coroutine_threadsafe` 桥接 SSE 推送到事件循环
- `progress_callback` MUST 是线程安全的（使用 queue 桥接）
- MVP MUST 使用 `concurrent.futures.ThreadPoolExecutor(max_workers=1)` 限制并发

## 6. Cancellation Design

MVP 的取消机制 MUST 谨慎设计：

- PipelineRunner 当前不支持取消（同步阻塞循环）
- MVP MUST 通过设置 `self._cancelled = True` 标志位实现软取消
- 软取消 MUST 在下一个 shot 开始前检查，当前执行中的 shot MUST 完成后再停止
- 取消后的 Run 状态 MUST 为 "failed" + error.detail = "cancelled_by_user"
- 后续迭代 SHOULD 支持通过 ComfyUI 的 `/interrupt` 端点硬中断当前 job

## 7. Integration Points

| Integration | Direction | Protocol | Existing Module |
|-------------|-----------|----------|-----------------|
| PipelineRunner | API -> Pipeline | run_in_executor | `pipeline.py` |
| ComfyClient | Pipeline -> ComfyUI | HTTP (sync) | `comfy_client.py` |
| Config Loader | API -> FS | sync call | `config.py` |
| Manifest | Pipeline -> FS | atomic write | `manifest.py` |
| Workflow Renderer | Pipeline -> JSON | sync call | `workflow_renderer.py` |
| Frontend | Browser -> API | REST + SSE | N/A (new) |

## 8. Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| PipelineRunner 同步阻塞导致 SSE 推送延迟 | High | 独立 executor 线程 + queue 桥接 |
| ComfyUI 离线导致 Run 启动后立即失败 | Medium | pre-flight health check (check_available) |
| 线程间状态竞争 | Medium | asyncio.Lock 保护 Run Registry |
| Manifest 写入冲突 | Low | atomic_write_manifest 已实现 |
| 大量 SSE 连接内存泄漏 | Low | 连接超时 + 心跳 + 自动清理 |
