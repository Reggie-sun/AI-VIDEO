# Local Long-Video MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI that validates ComfyUI workflow projects, renders workflow JSON per shot, runs/resumes local ComfyUI jobs, chains last frames, and stitches clips with ffmpeg.

**Architecture:** Use the reviewed manifest-driven pipeline from `docs/superpowers/specs/2026-04-30-local-long-video-system-design.md`. Keep the MVP to eight source modules: CLI, config/models, workflow renderer, Comfy client, manifest store, ffmpeg tools, pipeline orchestrator, and typed errors. The first working path must run entirely locally and be testable without real ComfyUI through mocks.

**Tech Stack:** Python 3.11+, Pydantic v2, PyYAML, httpx, pytest, ffmpeg/ffprobe subprocess calls, local editable install with `ai-video` console script.

---

## File Structure

- Create `pyproject.toml`: package metadata, console script, runtime/dev dependencies, pytest config.
- Create `.gitignore`: ignore caches, virtualenvs, generated run artifacts, and media outputs.
- Create `README.md`: local setup, config format, workflow export note, validation/run/resume commands, artifact retention.
- Create `configs/example.project.yaml`: example project config.
- Create `configs/example.shots.yaml`: example three-shot list.
- Create `workflows/templates/example_i2v_api.json`: minimal API-format test template.
- Create `workflows/bindings/example_i2v_binding.yaml`: binding for the example workflow.
- Create `src/ai_video/__init__.py`: package version.
- Create `src/ai_video/errors.py`: typed application errors and retryability.
- Create `src/ai_video/models.py`: Pydantic data models and validation.
- Create `src/ai_video/config.py`: YAML loading, path resolution, project validation, hash/free-space helpers.
- Create `src/ai_video/workflow_renderer.py`: API-format validation, binding path get/set, prompt composition, workflow rendering, output selection.
- Create `src/ai_video/manifest.py`: atomic manifest persistence, artifact hash verification, resume/stale decisions.
- Create `src/ai_video/ffmpeg_tools.py`: ffprobe, clip validation, last-frame extraction, normalization, concat list generation, final stitching.
- Create `src/ai_video/comfy_client.py`: ComfyUI availability, upload, prompt submission, lifecycle polling, output collection, cleanup.
- Create `src/ai_video/pipeline.py`: run/resume orchestration, per-shot retries, chaining, final stitch.
- Create `src/ai_video/cli.py`: `validate`, `run`, and `resume` commands.
- Create `tests/conftest.py`: shared fixtures and tiny workflow/config helpers.
- Create `tests/test_config.py`: config/model validation.
- Create `tests/test_workflow_renderer.py`: workflow API-format, path helper, prompt/render/output behavior.
- Create `tests/test_manifest.py`: atomic writes, hash verification, resume decisions.
- Create `tests/test_ffmpeg_tools.py`: command construction and optional tiny media integration.
- Create `tests/test_comfy_client.py`: mocked ComfyUI lifecycle/error matrix.
- Create `tests/test_pipeline.py`: mocked 3-shot chain, retry, resume, stale downstream behavior.
- Create `tests/test_cli.py`: public command behavior.

## Task 1: Project Skeleton And Error Model

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/ai_video/__init__.py`
- Create: `src/ai_video/errors.py`
- Create: `tests/test_errors.py`

- [ ] **Step 1: Write failing error-model tests**

```python
# tests/test_errors.py
from ai_video.errors import (
    AiVideoError,
    ErrorCode,
    config_error,
    retryable_error,
)


def test_config_error_is_not_retryable():
    error = config_error(ErrorCode.CONFIG_INVALID, "Bad config", "missing project_name")
    assert error.code is ErrorCode.CONFIG_INVALID
    assert error.user_message == "Bad config"
    assert error.technical_detail == "missing project_name"
    assert error.retryable is False
    assert str(error) == "Bad config"


def test_retryable_error_preserves_cause():
    cause = RuntimeError("connection reset")
    error = retryable_error(ErrorCode.COMFY_UNAVAILABLE, "ComfyUI unavailable", cause=cause)
    assert error.retryable is True
    assert error.cause is cause
    assert isinstance(error, AiVideoError)
```

- [ ] **Step 2: Run the failing tests**

Run: `pytest tests/test_errors.py -v`

Expected: fails because `ai_video.errors` does not exist.

- [ ] **Step 3: Create package metadata and error implementation**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ai-video"
version = "0.1.0"
description = "Pure-local ComfyUI long-video orchestration CLI"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.27",
  "pydantic>=2.7",
  "PyYAML>=6.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
]

[project.scripts]
ai-video = "ai_video.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

```gitignore
# .gitignore
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.venv/
venv/
*.egg-info/
runs/*
!runs/.gitkeep
*.mp4
*.webm
*.mov
*.png
```

```python
# src/ai_video/__init__.py
__version__ = "0.1.0"
```

```python
# src/ai_video/errors.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    CONFIG_INVALID = "config_invalid"
    WORKFLOW_INVALID = "workflow_invalid"
    BINDING_INVALID = "binding_invalid"
    COMFY_UNAVAILABLE = "comfy_unavailable"
    COMFY_SUBMISSION_FAILED = "comfy_submission_failed"
    COMFY_QUEUE_TIMEOUT = "comfy_queue_timeout"
    COMFY_JOB_TIMEOUT = "comfy_job_timeout"
    COMFY_JOB_FAILED = "comfy_job_failed"
    COMFY_OUTPUT_MISSING = "comfy_output_missing"
    OUTPUT_INVALID = "output_invalid"
    FFMPEG_FAILED = "ffmpeg_failed"
    MANIFEST_INVALID = "manifest_invalid"
    DISK_SPACE_LOW = "disk_space_low"


@dataclass
class AiVideoError(Exception):
    code: ErrorCode
    user_message: str
    technical_detail: Optional[str] = None
    retryable: bool = False
    cause: Optional[BaseException] = None

    def __str__(self) -> str:
        return self.user_message


def config_error(code: ErrorCode, message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, technical_detail=detail, retryable=False)


def retryable_error(
    code: ErrorCode,
    message: str,
    detail: str | None = None,
    cause: BaseException | None = None,
) -> AiVideoError:
    return AiVideoError(
        code=code,
        user_message=message,
        technical_detail=detail,
        retryable=True,
        cause=cause,
    )
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_errors.py -v`

Expected: 2 passed.

## Task 2: Pydantic Models And Config Loading

**Files:**
- Create: `src/ai_video/models.py`
- Create: `src/ai_video/config.py`
- Create: `tests/test_config.py`
- Create: `configs/example.project.yaml`
- Create: `configs/example.shots.yaml`
- Create: `workflows/templates/example_i2v_api.json`
- Create: `workflows/bindings/example_i2v_binding.yaml`

- [ ] **Step 1: Write failing model/config tests**

```python
# tests/test_config.py
from pathlib import Path

import pytest

from ai_video.config import load_project, load_shots
from ai_video.errors import AiVideoError, ErrorCode


def write_example_files(tmp_path: Path) -> tuple[Path, Path]:
    refs = tmp_path / "refs"
    refs.mkdir()
    (refs / "hero.png").write_bytes(b"fake-png")
    workflow_dir = tmp_path / "workflows"
    workflow_dir.mkdir()
    (workflow_dir / "template.json").write_text(
        '{"3":{"class_type":"KSampler","inputs":{"seed":1}},'
        '"6":{"class_type":"CLIPTextEncode","inputs":{"text":""}},'
        '"7":{"class_type":"CLIPTextEncode","inputs":{"text":""}},'
        '"12":{"class_type":"LoadImage","inputs":{"image":""}},'
        '"20":{"class_type":"LoadImage","inputs":{"image":""}},'
        '"25":{"class_type":"IPAdapter","inputs":{"weight":0.8}},'
        '"42":{"class_type":"VHS_VideoCombine","inputs":{"filename_prefix":""}}}',
        encoding="utf-8",
    )
    (workflow_dir / "binding.yaml").write_text(
        "positive_prompt:\n  path: ['6', inputs, text]\n"
        "negative_prompt:\n  path: ['7', inputs, text]\n"
        "seed:\n  path: ['3', inputs, seed]\n"
        "init_image:\n  path: ['12', inputs, image]\n"
        "output_prefix:\n  path: ['42', inputs, filename_prefix]\n"
        "character_refs:\n"
        "  - character: hero\n"
        "    image_path: ['20', inputs, image]\n"
        "    weight_path: ['25', inputs, weight]\n"
        "clip_output:\n  node: '42'\n  kind: gifs\n  extensions: ['.mp4']\n  select: first\n",
        encoding="utf-8",
    )
    project = tmp_path / "project.yaml"
    project.write_text(
        "project_name: demo\n"
        "comfy:\n  base_url: http://127.0.0.1:8188\n"
        "workflow:\n  template: workflows/template.json\n  binding: workflows/binding.yaml\n"
        "output:\n  root: runs\n  min_free_gb: 0\n"
        "defaults:\n  width: 512\n  height: 512\n  fps: 16\n  clip_seconds: 2\n  seed: 100\n"
        "characters:\n"
        "  - id: hero\n"
        "    name: Hero\n"
        "    description: same person, same outfit\n"
        "    reference_images: [refs/hero.png]\n"
        "    ipadapter:\n      weight: 0.8\n",
        encoding="utf-8",
    )
    shots = tmp_path / "shots.yaml"
    shots.write_text(
        "shots:\n"
        "  - id: shot_001\n    prompt: hero enters room\n    characters: [hero]\n"
        "  - id: shot_002\n    prompt: hero looks at camera\n    characters: [hero]\n",
        encoding="utf-8",
    )
    return project, shots


def test_load_project_resolves_paths_and_local_url(tmp_path):
    project_path, _ = write_example_files(tmp_path)
    project = load_project(project_path)
    assert project.project_name == "demo"
    assert project.workflow.template == tmp_path / "workflows/template.json"
    assert project.workflow.binding == tmp_path / "workflows/binding.yaml"
    assert project.output.root == tmp_path / "runs"
    assert project.characters[0].reference_images == [tmp_path / "refs/hero.png"]


def test_non_local_comfy_url_requires_opt_in(tmp_path):
    project_path, _ = write_example_files(tmp_path)
    text = project_path.read_text(encoding="utf-8").replace(
        "http://127.0.0.1:8188", "https://example.com"
    )
    project_path.write_text(text, encoding="utf-8")
    with pytest.raises(AiVideoError) as exc:
        load_project(project_path)
    assert exc.value.code is ErrorCode.CONFIG_INVALID
    assert "non-local" in exc.value.user_message


def test_load_shots_rejects_unknown_character(tmp_path):
    project_path, shots_path = write_example_files(tmp_path)
    project = load_project(project_path)
    shots_path.write_text(
        "shots:\n  - id: shot_001\n    prompt: missing\n    characters: [villain]\n",
        encoding="utf-8",
    )
    with pytest.raises(AiVideoError) as exc:
        load_shots(shots_path, project)
    assert exc.value.code is ErrorCode.CONFIG_INVALID
    assert "villain" in exc.value.user_message
```

- [ ] **Step 2: Run failing tests**

Run: `pytest tests/test_config.py -v`

Expected: fails because `models.py` and `config.py` do not exist.

- [ ] **Step 3: Implement models and config loader**

Implement Pydantic models for `ComfyConfig`, `WorkflowConfig`, `OutputConfig`, `DefaultsConfig`, `IPAdapterConfig`, `CharacterProfile`, `ProjectConfig`, `ShotSpec`, `ShotList`, `JsonPathBinding`, `CharacterRefBinding`, `ClipOutputBinding`, and `WorkflowBinding`.

Implement in `config.py`:

- `load_yaml(path: Path) -> dict`
- `is_local_url(url: str) -> bool`
- `resolve_project_paths(project: ProjectConfig, base_dir: Path) -> ProjectConfig`
- `load_project(path: str | Path) -> ProjectConfig`
- `load_shots(path: str | Path, project: ProjectConfig) -> list[ShotSpec]`
- `sha256_file(path: Path) -> str`
- `ensure_min_free_space(path: Path, min_free_gb: float) -> None`

Required behavior:

- Resolve relative paths against the project file directory.
- Allow `localhost`, `127.0.0.1`, and `::1`.
- Reject remote URLs unless `allow_non_local: true`.
- Reject shot character IDs not present in project config.
- Raise `AiVideoError` with `ErrorCode.CONFIG_INVALID` for user config failures.
- Raise `ErrorCode.DISK_SPACE_LOW` when free space is below threshold.

- [ ] **Step 4: Add example config and workflow files**

Create example files mirroring the test fixtures, with three shots and a minimal API-format workflow. The template does not need to generate real video; it is a validation/rendering example.

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_config.py -v`

Expected: all tests pass.

## Task 3: Workflow Renderer

**Files:**
- Create: `src/ai_video/workflow_renderer.py`
- Create: `tests/test_workflow_renderer.py`

- [ ] **Step 1: Write failing workflow renderer tests**

```python
# tests/test_workflow_renderer.py
import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.models import (
    CharacterProfile,
    CharacterRefBinding,
    ClipOutputBinding,
    DefaultsConfig,
    JsonPathBinding,
    ShotSpec,
    WorkflowBinding,
)
from ai_video.workflow_renderer import (
    collect_clip_artifact,
    compose_prompt,
    render_workflow,
    validate_api_workflow,
)


def binding() -> WorkflowBinding:
    return WorkflowBinding(
        positive_prompt=JsonPathBinding(path=["6", "inputs", "text"]),
        negative_prompt=JsonPathBinding(path=["7", "inputs", "text"]),
        seed=JsonPathBinding(path=["3", "inputs", "seed"]),
        init_image=JsonPathBinding(path=["12", "inputs", "image"]),
        output_prefix=JsonPathBinding(path=["42", "inputs", "filename_prefix"]),
        character_refs=[
            CharacterRefBinding(
                character="hero",
                image_path=["20", "inputs", "image"],
                weight_path=["25", "inputs", "weight"],
            )
        ],
        clip_output=ClipOutputBinding(
            node="42", kind="gifs", extensions=[".mp4"], select="first"
        ),
    )


def workflow() -> dict:
    return {
        "3": {"class_type": "KSampler", "inputs": {"seed": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}},
        "12": {"class_type": "LoadImage", "inputs": {"image": ""}},
        "20": {"class_type": "LoadImage", "inputs": {"image": ""}},
        "25": {"class_type": "IPAdapter", "inputs": {"weight": 0.0}},
        "42": {"class_type": "VHS_VideoCombine", "inputs": {"filename_prefix": ""}},
    }


def test_rejects_ui_workflow_json():
    with pytest.raises(AiVideoError) as exc:
        validate_api_workflow({"nodes": [], "links": []})
    assert exc.value.code is ErrorCode.WORKFLOW_INVALID
    assert "API-format" in exc.value.user_message


def test_render_workflow_replaces_bound_fields(tmp_path):
    shot = ShotSpec(id="shot_001", prompt="walks in", characters=["hero"])
    character = CharacterProfile(
        id="hero",
        name="Hero",
        description="same face",
        reference_images=[tmp_path / "hero.png"],
    )
    rendered = render_workflow(
        template=workflow(),
        binding=binding(),
        shot=shot,
        defaults=DefaultsConfig(seed=100, style_prompt="cinematic", negative_prompt="blur"),
        characters={"hero": character},
        shot_index=0,
        chain_image_name="prev.png",
        character_image_names={"hero": "hero_uploaded.png"},
        output_prefix="demo/run/shot_001/attempt_1",
    )
    assert rendered.workflow["6"]["inputs"]["text"] == "cinematic, same face, walks in"
    assert rendered.workflow["7"]["inputs"]["text"] == "blur"
    assert rendered.workflow["3"]["inputs"]["seed"] == 100
    assert rendered.workflow["12"]["inputs"]["image"] == "prev.png"
    assert rendered.workflow["20"]["inputs"]["image"] == "hero_uploaded.png"
    assert rendered.workflow["25"]["inputs"]["weight"] == 1.0
    assert rendered.workflow["42"]["inputs"]["filename_prefix"] == "demo/run/shot_001/attempt_1"


def test_collect_clip_artifact_filters_extensions():
    history = {
        "outputs": {
            "42": {
                "gifs": [
                    {"filename": "preview.gif", "subfolder": "", "type": "output"},
                    {"filename": "clip.mp4", "subfolder": "demo", "type": "output"},
                ]
            }
        }
    }
    artifact = collect_clip_artifact(history, binding().clip_output)
    assert artifact.filename == "clip.mp4"
    assert artifact.subfolder == "demo"
    assert artifact.extension == ".mp4"
```

- [ ] **Step 2: Run failing tests**

Run: `pytest tests/test_workflow_renderer.py -v`

Expected: fails because renderer functions do not exist.

- [ ] **Step 3: Implement renderer**

Implement:

- `validate_api_workflow(workflow: Mapping[str, Any]) -> None`
- internal `_get_path()` / `_set_path()` helpers with useful `AiVideoError`.
- `derive_seed(default_seed: int, shot_seed: int | None, shot_index: int) -> int`
- `compose_prompt(defaults, shot, characters) -> tuple[str, str]`
- `render_workflow(...) -> RenderedWorkflow`
- `collect_clip_artifact(history: dict, clip_output: ClipOutputBinding) -> ClipArtifact`

Required behavior:

- Reject UI workflow JSON with top-level `nodes`.
- Require each workflow node to have `class_type` and `inputs`.
- Validate all required binding paths before mutation.
- Deep-copy templates before rendering.
- Prompt order: style prompt, character descriptions, shot prompt, continuity note.
- Negative prompt order: global negative, shot negative.
- Seed default: `defaults.seed + shot_index` when shot seed is absent.
- Output selection: filter by extension, then first/last according to binding.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_workflow_renderer.py -v`

Expected: all renderer tests pass.

## Task 4: Manifest Store

**Files:**
- Create: `src/ai_video/manifest.py`
- Create: `tests/test_manifest.py`

- [ ] **Step 1: Write failing manifest tests**

```python
# tests/test_manifest.py
from pathlib import Path

from ai_video.manifest import (
    RunManifest,
    ShotRecord,
    atomic_write_manifest,
    load_manifest,
    successful_shot_is_valid,
)


def test_atomic_write_and_load_manifest(tmp_path):
    manifest = RunManifest(run_id="run_1", status="running")
    path = tmp_path / "manifest.json"
    atomic_write_manifest(path, manifest)
    loaded = load_manifest(path)
    assert loaded.run_id == "run_1"
    assert loaded.status == "running"


def test_successful_shot_validates_hashes(tmp_path):
    clip = tmp_path / "clip.mp4"
    frame = tmp_path / "last.png"
    clip.write_bytes(b"clip")
    frame.write_bytes(b"frame")
    record = ShotRecord.succeeded(
        shot_id="shot_001",
        seed=100,
        clip_path=clip,
        last_frame_path=frame,
        chain_input_hash=None,
        character_ref_hashes={"hero": "abc"},
    )
    assert successful_shot_is_valid(record) is True
    clip.write_bytes(b"changed")
    assert successful_shot_is_valid(record) is False
```

- [ ] **Step 2: Run failing tests**

Run: `pytest tests/test_manifest.py -v`

Expected: fails because manifest module does not exist.

- [ ] **Step 3: Implement manifest store**

Implement Pydantic models:

- `AttemptRecord`
- `ShotRecord`
- `RunManifest`

Implement functions:

- `atomic_write_manifest(path: Path, manifest: RunManifest) -> None`
- `load_manifest(path: Path) -> RunManifest`
- `hash_file(path: Path) -> str`
- `successful_shot_is_valid(record: ShotRecord) -> bool`
- `mark_downstream_stale(manifest: RunManifest, starting_after_shot_id: str) -> RunManifest`

Required behavior:

- Write `manifest.json.tmp`, then `replace()` to final path.
- Store path strings as absolute or run-root-relative consistently; tests may use absolute paths for simplicity.
- `ShotRecord.succeeded()` computes clip and last-frame hashes.
- If a successful artifact is missing or hash differs, return invalid.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_manifest.py -v`

Expected: manifest tests pass.

## Task 5: ffmpeg Tools

**Files:**
- Create: `src/ai_video/ffmpeg_tools.py`
- Create: `tests/test_ffmpeg_tools.py`

- [ ] **Step 1: Write failing ffmpeg tests**

```python
# tests/test_ffmpeg_tools.py
import shutil
import subprocess

import pytest

from ai_video.ffmpeg_tools import (
    concat_list_text,
    extract_last_frame,
    ffmpeg_available,
    normalize_clip,
)


def test_concat_list_escapes_single_quotes():
    text = concat_list_text(["/tmp/a clip.mp4", "/tmp/b'clip.mp4"])
    assert "file '/tmp/a clip.mp4'" in text
    assert "file '/tmp/b'\\''clip.mp4'" in text


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not available")
def test_extract_last_frame_from_tiny_video(tmp_path):
    source = tmp_path / "source.mp4"
    frame = tmp_path / "last frame.png"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=64x64:rate=4",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    extract_last_frame(source, frame)
    assert frame.exists()
    assert frame.stat().st_size > 0


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not available")
def test_normalize_clip_writes_output(tmp_path):
    source = tmp_path / "source.mp4"
    target = tmp_path / "normalized.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=64x64:rate=4",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    normalize_clip(source, target, width=64, height=64, fps=4, encoder="libx264")
    assert target.exists()
    assert target.stat().st_size > 0
```

- [ ] **Step 2: Run failing tests**

Run: `pytest tests/test_ffmpeg_tools.py -v`

Expected: first test fails because module does not exist; media tests skip if ffmpeg is unavailable.

- [ ] **Step 3: Implement ffmpeg helpers**

Implement:

- `ffmpeg_available() -> bool`
- `run_command(args: list[str]) -> subprocess.CompletedProcess`
- `probe_clip(path: Path) -> dict`
- `validate_clip(path: Path) -> None`
- `extract_last_frame(source: Path, target: Path) -> None`
- `normalize_clip(source: Path, target: Path, width: int, height: int, fps: int, encoder: str) -> None`
- `concat_list_text(paths: Sequence[str | Path]) -> str`
- `stitch_clips(normalized_clips: Sequence[Path], output_path: Path) -> None`

Required behavior:

- Use list-style subprocess args, not shell strings.
- Create target directories.
- Raise `AiVideoError(ErrorCode.FFMPEG_FAILED, ...)` with stderr detail.
- Last-frame extraction should use `-sseof -0.1` and fallback to a regular frame extraction if needed.
- Normalize to `scale=<width>:<height>,fps=<fps>`, `yuv420p`, no audio.
- Concat via concat demuxer list file.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_ffmpeg_tools.py -v`

Expected: command test passes; media tests pass or skip with reason.

## Task 6: ComfyUI Client

**Files:**
- Create: `src/ai_video/comfy_client.py`
- Create: `tests/test_comfy_client.py`

- [ ] **Step 1: Write failing Comfy client tests**

```python
# tests/test_comfy_client.py
import httpx
import pytest

from ai_video.comfy_client import ComfyClient, JobStatus
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.models import ClipOutputBinding


def test_submit_rejects_node_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": "bad prompt", "node_errors": {"6": "bad"}})

    client = ComfyClient("http://127.0.0.1:8188", http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(AiVideoError) as exc:
        client.submit_prompt({"6": {"inputs": {}, "class_type": "Test"}})
    assert exc.value.code is ErrorCode.COMFY_SUBMISSION_FAILED
    assert exc.value.retryable is False


def test_poll_completed_history_collects_status():
    responses = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/queue":
            return httpx.Response(200, json={"queue_running": [], "queue_pending": []})
        if request.url.path == "/history/prompt-1":
            return httpx.Response(200, json={"prompt-1": {"outputs": {"42": {"gifs": [{"filename": "clip.mp4", "subfolder": "", "type": "output"}]}}}})
        responses.append(request.url.path)
        return httpx.Response(404)

    client = ComfyClient("http://127.0.0.1:8188", http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    result = client.poll_job("prompt-1", poll_interval_seconds=0, timeout_seconds=1)
    assert result.status is JobStatus.COMPLETED
    assert result.history["outputs"]["42"]["gifs"][0]["filename"] == "clip.mp4"


def test_collect_output_downloads_view(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/view":
            return httpx.Response(200, content=b"video")
        return httpx.Response(404)

    client = ComfyClient("http://127.0.0.1:8188", http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    target = tmp_path / "clip.mp4"
    client.download_artifact(filename="clip.mp4", subfolder="", type_="output", target=target)
    assert target.read_bytes() == b"video"
```

- [ ] **Step 2: Run failing tests**

Run: `pytest tests/test_comfy_client.py -v`

Expected: fails because client module does not exist.

- [ ] **Step 3: Implement Comfy client**

Implement:

- `JobStatus` enum: `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `MISSING`, `TIMEOUT`.
- `JobResult` dataclass with `status`, `prompt_id`, `history`, `error`.
- `ComfyClient.__init__(base_url, http_client=None)`
- `check_available()`
- `upload_image(path: Path) -> str`
- `submit_prompt(workflow: dict) -> str`
- `poll_job(prompt_id, poll_interval_seconds, timeout_seconds) -> JobResult`
- `download_artifact(filename, subfolder, type_, target)`
- `free_memory()`

Required behavior:

- Use `/prompt`, `/queue`, `/history/{prompt_id}`, `/upload/image`, `/view`, and `/free`.
- Treat `error` or `node_errors` in `/prompt` response as non-retryable submission failure.
- Poll queue/history until completion or timeout.
- Return normalized completed history payload under `JobResult.history`.
- Use typed errors for unavailable server and failed downloads.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_comfy_client.py -v`

Expected: Comfy client tests pass.

## Task 7: Pipeline Orchestrator And CLI

**Files:**
- Create: `src/ai_video/pipeline.py`
- Create: `src/ai_video/cli.py`
- Create: `tests/test_pipeline.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing pipeline tests**

```python
# tests/test_pipeline.py
from pathlib import Path

from ai_video.pipeline import PipelineRunner


class FakeComfy:
    def __init__(self):
        self.submitted = []

    def prepare_image(self, path: Path) -> str:
        return path.name

    def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
        self.submitted.append(workflow)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"clip")
        return "prompt-id"


class FakeFfmpeg:
    def extract_last_frame(self, clip: Path, frame: Path) -> None:
        frame.parent.mkdir(parents=True, exist_ok=True)
        frame.write_bytes(frame.name.encode())

    def normalize_clip(self, source: Path, target: Path, **kwargs) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())

    def stitch_clips(self, clips, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"final")


def test_three_shot_chain_passes_last_frames(example_project_and_shots, tmp_path):
    project, shots, binding, template = example_project_and_shots
    runner = PipelineRunner(project, shots, binding, template, comfy=FakeComfy(), ffmpeg=FakeFfmpeg())
    manifest = runner.run(run_id="run-test")
    assert manifest.status == "succeeded"
    assert len(manifest.shots) == 3
    assert manifest.final_output is not None
```

- [ ] **Step 2: Write failing CLI tests**

```python
# tests/test_cli.py
from ai_video.cli import main


def test_validate_returns_zero_for_example_project(example_project_files, capsys):
    project_path, shots_path = example_project_files
    code = main(["validate", "--project", str(project_path), "--shots", str(shots_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "valid" in captured.out.lower()


def test_validate_returns_one_for_bad_config(tmp_path, capsys):
    project = tmp_path / "bad.yaml"
    shots = tmp_path / "shots.yaml"
    project.write_text("project_name: bad\n", encoding="utf-8")
    shots.write_text("shots: []\n", encoding="utf-8")
    code = main(["validate", "--project", str(project), "--shots", str(shots)])
    captured = capsys.readouterr()
    assert code == 1
    assert "config" in captured.err.lower() or "validation" in captured.err.lower()
```

- [ ] **Step 3: Run failing tests**

Run: `pytest tests/test_pipeline.py tests/test_cli.py -v`

Expected: fails because pipeline and CLI do not exist.

- [ ] **Step 4: Implement pipeline**

Implement `PipelineRunner` with:

- constructor accepting project, shots, binding, template, optional `comfy`, optional `ffmpeg`.
- `run(run_id: str | None = None) -> RunManifest`
- `resume(manifest_path: Path) -> RunManifest`
- per-shot attempt loop using same seed first.
- render workflow snapshot per attempt.
- pass previous `last_frame_path` as chain image.
- extract last frame after clip success.
- normalize and stitch after all shots succeed.

For MVP tests, keep dependency injection simple: fakes only need methods used in tests. The real CLI wires real `ComfyClient` and `ffmpeg_tools`.

- [ ] **Step 5: Implement CLI**

Implement argparse commands:

- `validate --project PATH --shots PATH`
- `run --project PATH --shots PATH [--run-id ID]`
- `resume --manifest PATH`

Required behavior:

- `main(argv=None) -> int` for tests.
- Print concise success messages to stdout.
- Print `AiVideoError.user_message` to stderr and return 1.
- Let unexpected exceptions print a concise message and return 2.

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_pipeline.py tests/test_cli.py -v`

Expected: pipeline and CLI tests pass.

## Task 8: Fixtures, README, And Full Validation

**Files:**
- Create: `tests/conftest.py`
- Modify: `README.md`
- Modify: `configs/example.project.yaml`
- Modify: `configs/example.shots.yaml`
- Modify: `workflows/templates/example_i2v_api.json`
- Modify: `workflows/bindings/example_i2v_binding.yaml`

- [ ] **Step 1: Add shared pytest fixtures**

Implement `example_project_files` and `example_project_and_shots` fixtures that create:

- local project YAML.
- three-shot YAML.
- fake reference image.
- minimal API-format workflow template.
- matching binding YAML.

Tests should import these fixtures instead of duplicating setup after Task 8.

- [ ] **Step 2: Write README**

Include:

- local-only promise.
- prerequisite: running ComfyUI, ffmpeg/ffprobe installed.
- setup: `python -m venv .venv`, activate, `pip install -e .[dev]`.
- validation: `ai-video validate --project configs/example.project.yaml --shots configs/example.shots.yaml`.
- dry run / real run notes.
- API-format workflow export warning.
- generated artifact layout under `runs/<run_id>/`.
- manual cleanup note.
- smoke-test checklist for real ComfyUI.

- [ ] **Step 3: Run the full test suite**

Run: `pytest -v`

Expected: all tests pass; ffmpeg media tests pass or skip with clear reason.

- [ ] **Step 4: Run CLI validation against examples**

Run: `python -m ai_video.cli validate --project configs/example.project.yaml --shots configs/example.shots.yaml`

Expected: exit 0 and prints that the project is valid.

- [ ] **Step 5: Final validation**

Run:

```bash
pytest -v
```

Expected: tests pass.

## Completion Criteria

- `ai-video validate` works on example files.
- `ai-video run` and `ai-video resume` have tested command wiring.
- Workflow templates are rejected early when they are UI JSON instead of API-format JSON.
- Binding replacement is deterministic and tested.
- ComfyUI HTTP behavior is covered by mocked tests.
- Pipeline chaining is covered by a mocked 3-shot integration test.
- ffmpeg commands are tested, with tiny media integration when binaries are installed.
- README explains how to adapt a real ComfyUI workflow and where artifacts land.
