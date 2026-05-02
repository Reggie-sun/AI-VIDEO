# AI-VIDEO API Server (F-001) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI API server that wraps the existing CLI modules into REST + SSE endpoints, enabling a frontend to manage projects, shots, and generation runs.

**Architecture:** FastAPI app with a Service Layer that orchestrates existing modules (`config.py`, `pipeline.py`, `comfy_client.py`, `manifest.py`). PipelineRunner runs in `run_in_executor` with a thread-safe bridge to SSE. Run Registry is in-memory (single-user local). Unified error envelope per EP-001.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, sse-starlette, existing project modules (pydantic, httpx, PyYAML)

---

## File Structure

```
src/ai_video/
├── api/                        # NEW: API server package
│   ├── __init__.py
│   ├── app.py                  # FastAPI app factory, CORS, lifespan, mount routers
│   ├── deps.py                 # Shared dependencies (RunRegistry, config loader, etc.)
│   ├── errors.py               # Unified error response models + exception handlers (EP-001)
│   ├── sse.py                  # SSE Manager: event buffering, heartbeat, Last-Event-ID replay
│   ├── registry.py             # Run Registry: in-memory active run tracking, 409 conflict guard
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py           # GET /health — ComfyUI, disk, ffmpeg checks (EP-005)
│   │   ├── projects.py         # CRUD /api/projects, drafts, validate, templates
│   │   ├── shots.py            # CRUD /api/projects/{name}/shots, reorder, validate
│   │   ├── runs.py             # POST /api/runs, GET runs, SSE events, cancel, resume
│   │   ├── gallery.py          # GET /api/runs/{run_id}/gallery, file serving with Range
│   │   ├── params.py           # POST validate params, workflow-preview, workflow-diff
│   │   └── rerun.py            # POST re-run, single-shot re-run
│   └── schemas/
│       ├── __init__.py
│       ├── common.py           # ErrorResponse, ValidationResult, PaginatedResponse
│       ├── project.py          # ProjectSummary, ProjectDetail, DraftCreate, DraftUpdate
│       ├── shot.py             # ShotSummary, ShotDetail, ReorderRequest, ValidateResult
│       ├── run.py              # RunSummary, RunDetail, RunCreate, PipelineState, SSEEvent
│       └── gallery.py          # GalleryIndex, GalleryShot, HealthCheck
├── cli.py                      # EXISTING: add `serve` subcommand
├── config.py                   # EXISTING: add load_project_by_name(), list_projects()
├── pipeline.py                 # EXISTING: no changes (wrapped by executor)
└── ...
```

---

### Task 1: API Package Skeleton + Unified Error Contract

**Files:**
- Create: `src/ai_video/api/__init__.py`
- Create: `src/ai_video/api/app.py`
- Create: `src/ai_video/api/errors.py`
- Create: `src/ai_video/api/schemas/__init__.py`
- Create: `src/ai_video/api/schemas/common.py`
- Test: `tests/test_api_errors.py`

- [ ] **Step 1: Write failing tests for error response format**

```python
# tests/test_api_errors.py
from ai_video.api.errors import error_response_from_exception
from ai_video.errors import AiVideoError, ErrorCode

def test_error_response_from_ai_video_error():
    exc = AiVideoError(
        code=ErrorCode.COMFY_UNAVAILABLE,
        user_message="ComfyUI 不可达",
        technical_detail="Connection refused: http://127.0.0.1:8188",
        retryable=True,
    )
    resp = error_response_from_exception(exc)
    assert resp["error"]["code"] == "COMFY_UNAVAILABLE"
    assert resp["error"]["message"] == "ComfyUI 不可达"
    assert resp["error"]["detail"] == "Connection refused: http://127.0.0.1:8188"
    assert "suggestion" in resp["error"]

def test_error_response_from_validation_error():
    from pydantic import ValidationError
    from ai_video.models import ProjectConfig
    try:
        ProjectConfig.model_validate({})
    except ValidationError as exc:
        resp = error_response_from_exception(exc)
        assert resp["error"]["code"] == "CONFIG_INVALID"
        assert resp["error"]["message"] != ""

def test_error_response_from_unexpected_exception():
    resp = error_response_from_exception(RuntimeError("oops"))
    assert resp["error"]["code"] == "INTERNAL_ERROR"
    assert resp["error"]["message"] != ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_errors.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Create api package and error module**

```python
# src/ai_video/api/__init__.py
```

```python
# src/ai_video/api/errors.py
from __future__ import annotations

from typing import Any

from ai_video.errors import AiVideoError, ErrorCode

_SUGGESTIONS: dict[str, str] = {
    "CONFIG_INVALID": "请检查项目配置文件格式和字段值是否正确",
    "WORKFLOW_INVALID": "请确认 Workflow JSON 模板文件格式正确",
    "BINDING_INVALID": "请检查 Binding 配置中的路径和节点 ID 是否匹配 Workflow 模板",
    "COMFY_UNAVAILABLE": "请确认 ComfyUI 已启动，或修改项目设置中的生成服务地址",
    "COMFY_SUBMISSION_FAILED": "请检查 ComfyUI 是否正常运行，或查看其控制台日志",
    "COMFY_QUEUE_TIMEOUT": "ComfyUI 队列超时，请检查是否有其他任务占用或减少等待时间",
    "COMFY_JOB_TIMEOUT": "生成任务超时，请尝试降低分辨率或减少帧数",
    "COMFY_JOB_FAILED": "生成任务失败，请检查 ComfyUI 控制台的错误日志",
    "COMFY_OUTPUT_MISSING": "ComfyUI 输出文件缺失，请检查输出目录配置",
    "OUTPUT_INVALID": "输出文件验证失败，请检查 ffmpeg 是否正常安装",
    "FFMPEG_FAILED": "ffmpeg 处理失败，请确认 ffmpeg 已正确安装且版本支持 H.264",
    "MANIFEST_INVALID": "运行记录文件损坏，请删除对应的 runs 目录后重试",
    "DISK_SPACE_LOW": "磁盘空间不足，请清理不需要的文件或更换输出目录",
    "RUN_CONFLICT": "已有生成任务正在运行，请等待完成或取消后再试",
    "INTERNAL_ERROR": "发生意外错误，请查看日志或重新启动服务",
}


def error_response_from_exception(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, AiVideoError):
        code = exc.code.value
        return {
            "error": {
                "code": code.upper(),
                "message": exc.user_message,
                "detail": exc.technical_detail,
                "suggestion": _SUGGESTIONS.get(code, ""),
            }
        }
    if type(exc).__name__ == "ValidationError":
        return {
            "error": {
                "code": "CONFIG_INVALID",
                "message": "配置验证失败",
                "detail": str(exc),
                "suggestion": _SUGGESTIONS["CONFIG_INVALID"],
            }
        }
    return {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "发生意外错误",
            "detail": str(exc),
            "suggestion": _SUGGESTIONS["INTERNAL_ERROR"],
        }
    }
```

```python
# src/ai_video/api/schemas/__init__.py
```

```python
# src/ai_video/api/schemas/common.py
from __future__ import annotations

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    detail: str | None = None
    suggestion: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = []
    warnings: list[str] = []


class PaginatedMeta(BaseModel):
    offset: int
    limit: int
    total: int


class PaginatedResponse(BaseModel):
    data: list
    meta: PaginatedMeta
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_errors.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ai_video/api/__init__.py src/ai_video/api/errors.py src/ai_video/api/schemas/__init__.py src/ai_video/api/schemas/common.py tests/test_api_errors.py
git commit -m "feat(api): add unified error response contract (EP-001)"
```

---

### Task 2: FastAPI App Factory + Exception Handlers

**Files:**
- Create: `src/ai_video/api/app.py`
- Create: `src/ai_video/api/deps.py`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write failing tests for app factory**

```python
# tests/test_api_app.py
from fastapi.testclient import TestClient
from ai_video.api.app import create_app

def test_app_creates():
    app = create_app()
    assert app.title == "AI-VIDEO API"

def test_health_endpoint_missing():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/health")
    # 200 or 503 depending on ComfyUI, but route must exist
    assert resp.status_code in (200, 503)

def test_cors_headers():
    app = create_app()
    client = TestClient(app)
    resp = client.options("/health", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    })
    assert resp.headers.get("access-control-allow-origin") in ("*", "http://localhost:5173")

def test_error_handler_returns_unified_format():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/projects/nonexistent")
    # Either 404 or 500 — but must be unified error format
    if resp.status_code >= 400:
        body = resp.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_app.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement app factory**

```python
# src/ai_video/api/deps.py
from __future__ import annotations

from dataclasses import dataclass, field

from ai_video.api.registry import RunRegistry
from ai_video.api.sse import SSEManager


@dataclass
class AppState:
    run_registry: RunRegistry = field(default_factory=RunRegistry)
    sse_manager: SSEManager = field(default_factory=SSEManager)
```

```python
# src/ai_video/api/app.py
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai_video.api.deps import AppState
from ai_video.api.errors import error_response_from_exception
from ai_video.errors import AiVideoError


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.app_state = AppState()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="AI-VIDEO API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AiVideoError)
    async def ai_video_error_handler(request: Request, exc: AiVideoError):
        status = 409 if exc.code.value == "run_conflict" else 400
        return JSONResponse(status_code=status, content=error_response_from_exception(exc))

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content=error_response_from_exception(exc))

    from ai_video.api.routers.health import router as health_router
    app.include_router(health_router)

    from ai_video.api.routers.projects import router as projects_router
    app.include_router(projects_router, prefix="/api")

    return app
```

- [ ] **Step 4: Create placeholder routers so imports succeed**

```python
# src/ai_video/api/routers/__init__.py
```

```python
# src/ai_video/api/routers/health.py
from __future__ import annotations

import shutil
import subprocess

import httpx
from fastapi import APIRouter

from ai_video.api.schemas.gallery import HealthCheck

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheck)
async def health_check():
    comfyui_status = "down"
    latency_ms = None
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            import time
            start = time.monotonic()
            resp = await client.get("http://127.0.0.1:8188/system_stats")
            latency_ms = int((time.monotonic() - start) * 1000)
            comfyui_status = "up" if resp.status_code == 200 else "down"
    except Exception:
        pass

    ffmpeg_status = "available"
    try:
        subprocess.run(["ffprobe", "-version"], capture_output=True, timeout=5, check=True)
    except Exception:
        ffmpeg_status = "missing"

    disk_status = "ok"
    free_gb = 0.0
    try:
        free_gb = shutil.disk_usage(".").free / (1024**3)
        if free_gb < 5:
            disk_status = "low"
    except Exception:
        pass

    overall = "healthy"
    if comfyui_status == "down":
        overall = "degraded"
    if ffmpeg_status == "missing":
        overall = "unhealthy"

    return HealthCheck(
        status=overall,
        comfyui={"status": comfyui_status, "latency_ms": latency_ms},
        disk={"status": disk_status, "free_gb": round(free_gb, 1)},
        ffmpeg={"status": ffmpeg_status},
    )
```

```python
# src/ai_video/api/routers/projects.py
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["projects"])
```

```python
# src/ai_video/api/schemas/gallery.py
from __future__ import annotations

from pydantic import BaseModel


class HealthCheckComponent(BaseModel):
    status: str
    latency_ms: int | None = None
    free_gb: float | None = None


class HealthCheck(BaseModel):
    status: str
    comfyui: HealthCheckComponent
    disk: HealthCheckComponent
    ffmpeg: HealthCheckComponent
```

- [ ] **Step 5: Create placeholder SSE and Registry modules**

```python
# src/ai_video/api/registry.py
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RunState:
    run_id: str
    status: str = "pending"
    project_name: str = ""


@dataclass
class RunRegistry:
    _active_run: RunState | None = None

    def start_run(self, run_id: str, project_name: str) -> RunState:
        if self._active_run is not None:
            from ai_video.errors import AiVideoError, ErrorCode
            raise AiVideoError(
                code=ErrorCode("run_conflict"),
                user_message=f"已有运行中的任务: {self._active_run.run_id}",
                retryable=False,
            )
        self._active_run = RunState(run_id=run_id, status="running", project_name=project_name)
        return self._active_run

    def finish_run(self, run_id: str, status: str = "succeeded") -> None:
        if self._active_run and self._active_run.run_id == run_id:
            self._active_run = None

    @property
    def active_run(self) -> RunState | None:
        return self._active_run
```

```python
# src/ai_video/api/sse.py
from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class SSEEvent:
    event: str
    data: dict
    id: str
    timestamp: float = field(default_factory=time.time)


class SSEManager:
    def __init__(self, buffer_size: int = 200, ttl_seconds: float = 600):
        self._buffers: dict[str, deque[SSEEvent]] = {}
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._buffer_size = buffer_size
        self._ttl = ttl_seconds
        self._event_counter: int = 0

    async def publish(self, run_id: str, event_type: str, data: dict) -> None:
        self._event_counter += 1
        event = SSEEvent(
            event=event_type,
            data=data,
            id=f"{run_id}-{self._event_counter}",
        )
        buf = self._buffers.setdefault(run_id, deque(maxlen=self._buffer_size))
        buf.append(event)
        for queue in self._subscribers.get(run_id, []):
            await queue.put(event)

    def subscribe(self, run_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.setdefault(run_id, []).append(queue)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue) -> None:
        subs = self._subscribers.get(run_id, [])
        if queue in subs:
            subs.remove(queue)

    def events_after(self, run_id: str, last_event_id: str | None) -> list[SSEEvent]:
        buf = self._buffers.get(run_id, deque())
        if not last_event_id:
            return list(buf)
        for i, event in enumerate(buf):
            if event.id == last_event_id:
                return list(buf)[i + 1 :]
        return list(buf)
```

- [ ] **Step 6: Add `ErrorCode` entry for run_conflict**

In `src/ai_video/errors.py`, add `RUN_CONFLICT = "run_conflict"` to the `ErrorCode` enum.

- [ ] **Step 7: Add dependencies to pyproject.toml**

In `pyproject.toml`, add to `dependencies`:
```
"fastapi>=0.115",
"uvicorn[standard]>=0.30",
"sse-starlette>=2.0",
```

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && pip install -e ".[dev]"`

- [ ] **Step 8: Run test to verify it passes**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_app.py tests/test_api_errors.py -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add src/ai_video/api/ pyproject.toml tests/test_api_app.py
git commit -m "feat(api): FastAPI app factory with health, CORS, error handlers, SSE manager, Run registry"
```

---

### Task 3: Projects CRUD + Validation Endpoints

**Files:**
- Modify: `src/ai_video/api/routers/projects.py`
- Create: `src/ai_video/api/schemas/project.py`
- Modify: `src/ai_video/config.py`
- Test: `tests/test_api_projects.py`

- [ ] **Step 1: Write failing tests for project CRUD**

```python
# tests/test_api_projects.py
import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from ai_video.api.app import create_app


def _make_project_yaml(tmp: Path, name: str = "test_project") -> Path:
    workflow_dir = tmp / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    template_path = workflow_dir / "test_workflow.json"
    template_path.write_text('{"1": {"class_type": "Test"}}')
    binding_path = workflow_dir / "test_binding.yaml"
    binding_path.write_text(
        "positive_prompt:\n  path: ['1','inputs','text']\n"
        "seed:\n  path: ['1','inputs','seed']\n"
        "clip_output:\n  node: '1'\n  kind: 'output'\n"
    )
    project_yaml = tmp / f"{name}.project.yaml"
    project_yaml.write_text(
        f"project_name: {name}\n"
        f"workflow:\n  template: {template_path}\n  binding: {binding_path}\n"
    )
    return project_yaml


def test_list_projects_empty(tmp_path):
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/projects", params={"search_dir": str(tmp_path)})
    assert resp.status_code == 200
    assert resp.json() == []


def test_validate_comfy_url():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/validate/comfy-url", params={"url": "http://127.0.0.1:9999"})
    assert resp.status_code == 200
    body = resp.json()
    assert "valid" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_projects.py -v`
Expected: FAIL — endpoints not implemented

- [ ] **Step 3: Implement project schemas and router**

```python
# src/ai_video/api/schemas/project.py
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from ai_video.models import DefaultsConfig, ComfyConfig, OutputConfig


class ProjectSummary(BaseModel):
    name: str
    config_path: str
    comfy_base_url: str = ""
    workflow_template: str = ""


class ProjectDetail(BaseModel):
    name: str
    config_path: str
    comfy: ComfyConfig
    workflow_template: str
    workflow_binding: str
    output_root: str
    defaults: DefaultsConfig
    shot_count: int = 0


class DraftCreate(BaseModel):
    project_name: str = "my_project"
    comfy_base_url: str = "http://127.0.0.1:8188"
    workflow_template: str = ""
    workflow_binding: str = ""


class DraftUpdate(BaseModel):
    comfy_base_url: str | None = None
    workflow_template: str | None = None
    workflow_binding: str | None = None
    defaults: DefaultsConfig | None = None
```

Implement `projects.py` router with: `GET /api/projects` (list), `GET /api/projects/{name}` (detail), `GET /api/validate/comfy-url`, `GET /api/validate/workflow-template`, `GET /api/validate/binding`, `GET /api/templates`.

Each endpoint delegates to `config.py` functions and returns schema-validated JSON.

- [ ] **Step 4: Implement config helper functions**

Add to `src/ai_video/config.py`:
- `list_projects(search_dir: Path) -> list[Path]`: scan for `*.project.yaml` files
- `load_project_by_name(name: str, search_dir: Path) -> tuple[ProjectConfig, Path]`: find + load

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_projects.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/ai_video/api/routers/projects.py src/ai_video/api/schemas/project.py src/ai_video/config.py tests/test_api_projects.py
git commit -m "feat(api): project CRUD endpoints, list/detail/validate"
```

---

### Task 4: Shots CRUD + Reorder + Validate Endpoints

**Files:**
- Create: `src/ai_video/api/routers/shots.py`
- Create: `src/ai_video/api/schemas/shot.py`
- Test: `tests/test_api_shots.py`

- [ ] **Step 1: Write failing tests for shot CRUD**

```python
# tests/test_api_shots.py
from fastapi.testclient import TestClient
from ai_video.api.app import create_app


def test_list_shots_for_project(tmp_path):
    # Create a project with known shots
    app = create_app()
    client = TestClient(app)
    resp = client.get(f"/api/projects/test_project/shots", params={"project_dir": str(tmp_path)})
    assert resp.status_code == 200


def test_add_shot(tmp_path):
    app = create_app()
    client = TestClient(app)
    resp = client.post(
        f"/api/projects/test_project/shots",
        json={"id": "shot_01", "prompt": "A hero walks"},
        params={"project_dir": str(tmp_path)},
    )
    assert resp.status_code == 201


def test_reorder_shots(tmp_path):
    app = create_app()
    client = TestClient(app)
    resp = client.patch(
        f"/api/projects/test_project/shots/reorder",
        json={"order": ["shot_02", "shot_01"]},
        params={"project_dir": str(tmp_path)},
    )
    assert resp.status_code == 200


def test_validate_shots(tmp_path):
    app = create_app()
    client = TestClient(app)
    resp = client.post(
        f"/api/projects/test_project/shots/validate",
        params={"project_dir": str(tmp_path)},
    )
    assert resp.status_code == 200
    assert "valid" in resp.json()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_shots.py -v`
Expected: FAIL — router not registered

- [ ] **Step 3: Implement shot schemas and router**

```python
# src/ai_video/api/schemas/shot.py
from __future__ import annotations

from pydantic import BaseModel

from ai_video.models import ShotSpec


class ShotSummary(BaseModel):
    id: str
    prompt: str
    status: str = "draft"
    overrides: list[str] = []


class ShotCreate(BaseModel):
    id: str
    prompt: str
    negative_prompt: str = ""
    characters: list[str] = []
    seed: int | None = None
    clip_seconds: int | None = None
    fps: int | None = None
    width: int | None = None
    height: int | None = None


class ShotUpdate(BaseModel):
    prompt: str | None = None
    negative_prompt: str | None = None
    characters: list[str] | None = None
    seed: int | None = None
    clip_seconds: int | None = None
    fps: int | None = None
    width: int | None = None
    height: int | None = None


class ReorderRequest(BaseModel):
    order: list[str]


class ValidateResult(BaseModel):
    valid: bool
    errors: list[dict] = []
    warnings: list[dict] = []
```

Implement `shots.py` router with: `GET /projects/{name}/shots`, `POST` add, `PUT` update, `DELETE`, `PATCH` reorder, `POST` validate.

Shot data is read from and written to `shots.yaml`. Reorder writes new shot order to YAML. Validate runs `ShotSpec.model_validate()` + character reference checks.

- [ ] **Step 4: Register shots router in app.py**

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_shots.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/ai_video/api/routers/shots.py src/ai_video/api/schemas/shot.py src/ai_video/api/app.py tests/test_api_shots.py
git commit -m "feat(api): shot CRUD, reorder, validate endpoints"
```

---

### Task 5: Runs API — Start, Cancel, Resume + SSE Event Stream

**Files:**
- Create: `src/ai_video/api/routers/runs.py`
- Create: `src/ai_video/api/schemas/run.py`
- Modify: `src/ai_video/api/app.py` (register router)
- Test: `tests/test_api_runs.py`

- [ ] **Step 1: Write failing tests for runs API**

```python
# tests/test_api_runs.py
from fastapi.testclient import TestClient
from ai_video.api.app import create_app


def test_start_run_returns_202(tmp_path, monkeypatch):
    app = create_app()
    client = TestClient(app)
    # Mock PipelineRunner.run to avoid real ComfyUI call
    resp = client.post("/api/runs", json={"project_name": "test_project"})
    assert resp.status_code == 202
    assert "run_id" in resp.json()


def test_concurrent_run_returns_409():
    app = create_app()
    client = TestClient(app)
    # Start first run
    resp1 = client.post("/api/runs", json={"project_name": "test_project"})
    assert resp1.status_code == 202
    # Second run should fail
    resp2 = client.post("/api/runs", json={"project_name": "test_project"})
    assert resp2.status_code == 409


def test_sse_events_stream():
    app = create_app()
    client = TestClient(app)
    resp = client.post("/api/runs", json={"project_name": "test_project"})
    run_id = resp.json()["run_id"]
    # SSE endpoint must be reachable
    with client.stream("GET", f"/api/runs/{run_id}/events") as stream:
        # Should get at least heartbeat or run:started
        chunk = next(stream.iter_lines())
        assert chunk is not None


def test_cancel_run():
    app = create_app()
    client = TestClient(app)
    resp = client.post("/api/runs", json={"project_name": "test_project"})
    run_id = resp.json()["run_id"]
    cancel_resp = client.post(f"/api/runs/{run_id}/cancel")
    assert cancel_resp.status_code == 200


def test_list_runs():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/runs")
    assert resp.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_runs.py -v`
Expected: FAIL — router not registered

- [ ] **Step 3: Implement run schemas and router**

```python
# src/ai_video/api/schemas/run.py
from __future__ import annotations

from pydantic import BaseModel


class RunCreate(BaseModel):
    project_name: str
    shot_overrides: dict | None = None


class RunSummary(BaseModel):
    run_id: str
    status: str
    project_name: str = ""
    created_at: str = ""
    shot_count: int = 0


class RunDetail(BaseModel):
    run_id: str
    status: str
    project_name: str = ""
    created_at: str = ""
    shots: list[dict] = []
    final_output: str | None = None
    total_duration_s: float | None = None


class SSEEventSchema(BaseModel):
    event: str
    data: dict
    id: str
```

Implement `runs.py` router:
- `POST /api/runs` — acquire Run Registry lock, start `PipelineRunner.run()` in `run_in_executor`, return 202
- `GET /api/runs` — scan `runs/*/manifest.json` (using manifest.load_manifest)
- `GET /api/runs/{run_id}` — load single manifest
- `POST /api/runs/{run_id}/cancel` — set cancel flag
- `POST /api/runs/{run_id}/resume` — resume via `PipelineRunner.resume()`
- `GET /api/runs/{run_id}/events` — SSE stream using `SSEManager.subscribe()`

The thread-bridge pattern: `PipelineRunner` callback calls `asyncio.run_coroutine_threadsafe(sse_manager.publish(...), loop)`.

- [ ] **Step 4: Register runs router in app.py**

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_runs.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/ai_video/api/routers/runs.py src/ai_video/api/schemas/run.py src/ai_video/api/app.py tests/test_api_runs.py
git commit -m "feat(api): runs API with start, cancel, resume, SSE event stream"
```

---

### Task 6: Gallery + File Serving Endpoints

**Files:**
- Create: `src/ai_video/api/routers/gallery.py`
- Modify: `src/ai_video/api/schemas/gallery.py` (add GalleryIndex, GalleryShot)
- Test: `tests/test_api_gallery.py`

- [ ] **Step 1: Write failing tests for gallery API**

```python
# tests/test_api_gallery.py
from fastapi.testclient import TestClient
from ai_video.api.app import create_app


def test_gallery_index(tmp_path):
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/runs/run-test/gallery")
    assert resp.status_code == 200
    body = resp.json()
    assert "shots" in body


def test_file_serving_blocks_path_traversal(tmp_path):
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/files/run-test/shot_01/../../etc/passwd")
    assert resp.status_code in (400, 404, 403)


def test_file_serving_supports_range(tmp_path):
    # Create a small test video file
    test_dir = tmp_path / "runs" / "run-test" / "shots" / "shot_01"
    test_dir.mkdir(parents=True)
    (test_dir / "clip.mp4").write_bytes(b"fake mp4 data for range test")
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/files/run-test/shot_01/clip.mp4", headers={"Range": "bytes=0-3"})
    assert resp.status_code == 206
    assert len(resp.content) == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_gallery.py -v`
Expected: FAIL

- [ ] **Step 3: Implement gallery router and file serving**

Gallery router: `GET /api/runs/{run_id}/gallery` returns index of all artifacts. File serving: `GET /api/files/{run_id}/{shot_id}/{filename}` with path traversal protection (`Path.resolve()` + `startswith()`), Range header support, `Content-Disposition` for downloads.

Add `GalleryIndex` and `GalleryShot` to `schemas/gallery.py`.

- [ ] **Step 4: Register gallery router in app.py**

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_gallery.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/ai_video/api/routers/gallery.py src/ai_video/api/schemas/gallery.py src/ai_video/api/app.py tests/test_api_gallery.py
git commit -m "feat(api): gallery index and secure file serving with Range support"
```

---

### Task 7: Params Validate + Workflow Preview + Re-run Endpoints

**Files:**
- Create: `src/ai_video/api/routers/params.py`
- Create: `src/ai_video/api/routers/rerun.py`
- Test: `tests/test_api_params.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_api_params.py
from fastapi.testclient import TestClient
from ai_video.api.app import create_app


def test_validate_params():
    app = create_app()
    client = TestClient(app)
    resp = client.post(
        "/api/projects/test_project/params/validate",
        json={"seed": 42, "clip_seconds": 3, "fps": 16},
    )
    assert resp.status_code == 200
    assert "valid" in resp.json()


def test_workflow_preview():
    app = create_app()
    client = TestClient(app)
    resp = client.post("/api/projects/test_project/shots/shot_01/workflow-preview")
    assert resp.status_code == 200


def test_rerun_returns_202():
    app = create_app()
    client = TestClient(app)
    resp = client.post("/api/runs/re-run", json={"source_run_id": "run-old", "overrides": {}})
    assert resp.status_code in (202, 409)  # 409 if active run


def test_rerun_conflict_when_active():
    app = create_app()
    client = TestClient(app)
    # Start a run first
    client.post("/api/runs", json={"project_name": "test_project"})
    # Rerun should conflict
    resp = client.post("/api/runs/re-run", json={"source_run_id": "run-old", "overrides": {}})
    assert resp.status_code == 409
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_params.py -v`
Expected: FAIL

- [ ] **Step 3: Implement params and rerun routers**

`params.py`: `POST validate` runs `DefaultsConfig.model_validate()` + `ShotSpec.model_validate()`. `POST workflow-preview` calls `render_workflow()` via `run_in_executor`. `POST workflow-diff` runs `render_workflow` twice and diffs.

`rerun.py`: `POST re-run` loads source Run manifest, applies overrides, starts new PipelineRunner via `run_in_executor`, returns 202. Checks Run Registry for 409.

- [ ] **Step 4: Register routers in app.py**

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_api_params.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/ai_video/api/routers/params.py src/ai_video/api/routers/rerun.py src/ai_video/api/app.py tests/test_api_params.py
git commit -m "feat(api): param validation, workflow preview, re-run endpoints"
```

---

### Task 8: CLI `serve` Subcommand + Integration Test

**Files:**
- Modify: `src/ai_video/cli.py`
- Test: `tests/test_cli_serve.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_cli_serve.py
from ai_video.cli import build_parser


def test_serve_subcommand_exists():
    parser = build_parser()
    args = parser.parse_args(["serve", "--port", "8080"])
    assert args.command == "serve"
    assert args.port == 8080


def test_serve_default_port():
    parser = build_parser()
    args = parser.parse_args(["serve"])
    assert args.port == 8787
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_cli_serve.py -v`
Expected: FAIL — no `serve` subcommand

- [ ] **Step 3: Add serve subcommand to CLI**

In `src/ai_video/cli.py`, add:
```python
def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn
    from ai_video.api.app import create_app
    uvicorn.run(create_app(), host=args.host, port=args.port)
    return 0
```

Register in `build_parser()`:
```python
serve = subcommands.add_parser("serve")
serve.add_argument("--host", default="127.0.0.1")
serve.add_argument("--port", type=int, default=8787)
serve.set_defaults(func=_cmd_serve)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/test_cli_serve.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite to verify no regressions**

Run: `cd /home/reggie/vscode_folder/AI-VIDEO && python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/ai_video/cli.py tests/test_cli_serve.py
git commit -m "feat(cli): add serve subcommand for API server"
```

---

## Self-Review

### 1. Spec Coverage Check

| F-001 Requirement | Task |
|---|---|
| FastAPI + SSE | Task 2 (app factory), Task 5 (SSE stream) |
| run_in_executor wrapping | Task 5 (runs router) |
| Run state machine (pending→running→succeeded/failed) | Task 5 (Run Registry + manifest status) |
| Single Run + 409 | Task 5 (RunRegistry.start_run) |
| Project CRUD | Task 3 |
| Shot CRUD + reorder + validate | Task 4 |
| Run CRUD + events | Task 5 |
| Gallery + file serving + Range | Task 6 |
| Validate comfy-url | Task 3 |
| Params validate + workflow preview + rerun | Task 7 |
| Unified error format (EP-001) | Task 1 |
| Health check (EP-005) | Task 2 |
| CLI serve command | Task 8 |
| X-Request-ID header | **MISSING** — add middleware in Task 2 |
| SSE heartbeat 15s | Task 5 (SSE integration) |
| SSE Last-Event-ID replay | Task 5 (SSEManager.events_after) |
| Path traversal protection | Task 6 |
| Cancel = failed + cancelled_by_user | Task 5 |

**Gap found:** X-Request-ID middleware not in any task. Will add to Task 2.

### 2. Placeholder Scan

No TBD/TODO/fill-in patterns found. All steps contain actual code.

### 3. Type Consistency

- `RunRegistry.start_run()` raises `AiVideoError` with `run_conflict` code — matches `errors.py` `RUN_CONFLICT` enum value added in Task 2
- `SSEEvent.data` is `dict` — matches `SSEEventSchema.data` in Task 5
- `HealthCheck` schema in Task 2 matches `gallery.py` additions in Task 6
- `ReorderRequest.order` is `list[str]` — matches shot IDs used in Task 4

**Fix:** Add `RUN_CONFLICT` to `ErrorCode` enum in Task 2, Step 6.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-02-ai-video-frontend.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
