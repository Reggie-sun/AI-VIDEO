# AI-VIDEO Production Runtime P1 Runtime Truth Fixes Implementation Plan

> **For agentic workers:** 实施本 plan 时，REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans。按 Task 顺序执行，并使用 checkbox (`- [ ]`) 跟踪进度。

**Goal:** 在不改变 Legacy CLI、Manifest v1 schema、flat artifact layout 和纯本地 ComfyUI 路径的前提下，修复 terminal failed Attempt 持久化、真实 last-frame dependency 的 resume stale propagation，并固化 source-generation FPS 与 delivery-normalization FPS 的 Legacy 兼容语义。

**Architecture:** `PipelineRunner` 继续是 Shot/Attempt 转移、resume 判定和 dependency propagation 的 single owner；`manifest.py` 只提供 Manifest v1 model、atomic write、artifact validity 和按精确 Shot ID 标记 stale 的纯 helper。Resume 依次比较当前 Shot 真正消费的直接上游 last-frame hash；只在新上游 artifact hash 改变时将直接 consumer 标 stale，再由后续 Shot 的新输出继续传播。`defaults.fps` 保持同时作为 generation fallback 和固定 delivery normalization FPS，`shot.fps` 只覆盖 source generation；P1 不新增 config 字段。

**Tech Stack:** Python 3.11+、Pydantic v2、pytest、现有 fake ComfyUI/ffmpeg test doubles、Markdown、Git；不新增 runtime dependency，不调用真实 ComfyUI、ffmpeg 生产流程或网络 Provider。

---

## Implementation Authority

本文件只是 P1 implementation plan，**不授权实施**。开始修改 `src/`、`tests/` 或 `README.md` 前，必须获得用户对本 P1 plan 的单独明确批准。

P1 允许的未来实施路径仅限：

- `src/ai_video/manifest.py`
- `src/ai_video/pipeline.py`
- `src/ai_video/workflow_renderer.py`
- `tests/test_manifest.py`
- `tests/test_pipeline.py`
- `tests/test_resume_e2e.py`
- `tests/test_config.py` 仅在现有 config 兼容语义需要额外回归时修改；本 plan 预期只运行它，不修改它
- `README.md`

P1 明确禁止：

- Provider abstraction、`WanComfyProvider`、`MockProvider` 或任何 SDK adapter。
- Manifest v2、公共 schema migration、Take、Human Review 或 Technical Gate。
- 新 CLI command、flag 或 exit-code semantics。
- cloud/remote behavior、Budget Guard、Cloud Egress、Seedance 或付费 submit。
- Audio、Timeline v2、composition fingerprint 或 semantic evaluator。
- `runs/<run_id>/` artifact layout 变化。
- 新 runtime dependency。
- P2-P9 的任何内容。
- 将 `character_ref_hashes`、template/config fingerprint 或 explicit `init_image` content hash 纳入本次 invalidation；P1 只修复当前 last-frame dependency。

## Problem Boundary

P1 仅处理三个已验证的 runtime-truth gap：

1. `_run_shot()` 会把 failed Attempt 追加到内存 list，但 terminal branch 在 `atomic_write_manifest()` 之前直接将异常逃逸。
2. Resume 只检查 Shot 自身 clip/last-frame hash，没有核对它实际消费的 last-frame dependency；现有 `mark_downstream_stale()` 又会将某 Shot 之后所有成功 Shot 一律标 stale。
3. 当前代码已经让 `shot.fps` 只覆盖 workflow generation，而 normalize 始终使用 `defaults.fps`，但此兼容语义没有被端到端测试和用户文档锁定。

P1 的不变 contract：

- `successful_shot_is_valid()` 仍只拥有 Shot 自身 persisted artifact 有效性；它不读当前 `ShotSpec` 或 workflow binding。
- `PipelineRunner.resume()` 是“当前 input/dependency 是否与 Manifest 一致”的唯一 owner。
- `atomic_write_manifest()` 仍是唯一 Manifest 写入路径。
- Local Wan + ComfyUI、Manifest v1、flat paths 和三个公共 CLI command 保持不变。

## Current Behavior Evidence

在开始实施时重新运行：

```bash
git status --short --branch
git rev-parse --short HEAD
rg -n "attempts.append|atomic_write_manifest|raise$|_run_shot\\(" src/ai_video/pipeline.py tests/test_pipeline.py tests/test_resume_e2e.py
rg -n "_prepare_chain_image|previous_frame_hash|chain_input_hash|successful_shot_is_valid|mark_downstream_stale" src/ai_video/manifest.py src/ai_video/pipeline.py tests/test_manifest.py tests/test_pipeline.py tests/test_resume_e2e.py
rg -n "defaults\\.fps|shot\\.fps|frame_rate|frame_count|normalize_clip" src/ai_video/models.py src/ai_video/workflow_renderer.py src/ai_video/pipeline.py tests/test_pipeline.py tests/test_config.py tests/test_workflow_renderer.py
python -m pytest tests/test_manifest.py tests/test_pipeline.py tests/test_resume_e2e.py tests/test_config.py tests/test_workflow_renderer.py -q
```

2026-08-08 的 planning baseline：

- `src/ai_video/pipeline.py:66-78` 和 `136-152` 只在 `_run_shot()` 成功返回后写 Manifest。
- `src/ai_video/pipeline.py:220-228` 对 terminal `AiVideoError` 直接 `raise`；unexpected exception 甚至不会将当前 Attempt 标为 failed。
- `src/ai_video/pipeline.py:254-275` 无条件写入 `chain_input_hash=previous_frame_hash`，即使 `shot.init_image` 覆盖了上游帧，或 binding 没有 `init_image` path。
- `src/ai_video/manifest.py:119-124` 只验证 clip 和 last-frame hash；`127-136` 的 `mark_downstream_stale()` 是未使用的 blanket order-based helper。
- `src/ai_video/workflow_renderer.py:185-212` 以 `shot.fps` 或 `defaults.fps` 驱动 generation `frame_count`/`frame_rate`。
- `src/ai_video/pipeline.py:84-90` 和 `158-163` 对 run/resume normalize 都传入 `project.defaults.fps`。
- 本 plan 编写前的定向基线为 `21 passed in 0.09s`。实施者必须以当时的重跑结果为准。

## File Ownership and Old-Path Decisions

| File | P1 Responsibility | Old-Path Decision |
| --- | --- | --- |
| `src/ai_video/pipeline.py` | terminal failure transition、Attempt numbering/history、actual chain dependency resolution、resume skip/rerun、delivery normalization call | **Single behavioral owner**；保留顺序 Shot 执行和现有 retry policy，用同一 dependency predicate 替换 artifact-only fast/loop 双路判定 |
| `src/ai_video/manifest.py` | Manifest v1 record construction、atomic persistence、artifact hash validity、按精确 ID 标 stale | 保留 `successful_shot_is_valid()`；删除 blanket `mark_downstream_stale()`，替换为只处理 caller 已解析 Shot IDs 的 `mark_shots_stale()` |
| `src/ai_video/workflow_renderer.py` | 明确局部 `generation_fps` 命名 | 保留 `shot.fps` override 和 `defaults.fps` fallback；不改 binding、frame-count 公式或 workflow shape |
| `src/ai_video/models.py` | 只读契约证据 | 不新增 `delivery_fps`、schema version 或其它 config 字段 |
| `tests/test_manifest.py` | 精确 stale helper 和 Manifest v1 round-trip | 保留 own-artifact validity tests，不把 dependency resolution 搬入 manifest tests |
| `tests/test_pipeline.py` | terminal failure atomic persistence、history preservation、run/resume FPS 兼容 | 扩展现有 fakes，不调用真实 ComfyUI/ffmpeg |
| `tests/test_resume_e2e.py` | changed/same upstream artifact 传播、explicit-init cut 与 no-binding guard | 保留生产 loader 路径，不改 artifact layout |
| `tests/test_config.py` | 现有 Legacy config 回归 | 预期不修改；运行以证明没有 schema drift |
| `README.md` | 替换 P0 gap wording，记录实施后的 Attempt/resume/FPS 真实行为 | 保留当前 command/layout 文档；不描述 P2+ 能力为已实现 |

所有 Task 必须按顺序由一个写入 lane 执行。后续 Task 可以继续修改前一 Task 的同一文件，但不得并发安排两个 writer 处理 `pipeline.py` 或其相邻测试。

## Test and Commit Map

| Task | RED Focus | GREEN Owner | Commit Boundary |
| --- | --- | --- | --- |
| Task 1 | typed/unexpected terminal failure、run/resume Attempt history | `pipeline.py` + Manifest v1 record update | `fix: persist terminal shot failures atomically` |
| Task 2 | changed hash propagation、same hash skip、explicit init/no-binding cuts | `PipelineRunner.resume()` + exact-ID manifest helper | `fix: propagate changed chain dependencies on resume` |
| Task 3 | per-shot generation override vs fixed delivery normalization | renderer/pipeline semantic naming + README | `refactor: clarify source and delivery fps roles` |
| Task 4 | full regression and scope leak | verification only | no new commit unless Task 1-3 left a scoped correction |

### Task 1: Persist Terminal Shot Failures Before Exception Escape

**Files:**
- Modify: `src/ai_video/manifest.py:17-71`
- Modify: `src/ai_video/pipeline.py:42-78`
- Modify: `src/ai_video/pipeline.py:104-152`
- Modify: `src/ai_video/pipeline.py:183-233`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write failing tests for typed and unexpected terminal failures**

Add `pytest` and `AiVideoError` imports, then add these tests:

```python
import pytest

from ai_video.errors import AiVideoError, ErrorCode, retryable_error


def test_terminal_failure_persists_all_attempts_before_run_raises(example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    project.defaults.max_attempts = 2

    class AlwaysFailComfy(FakeComfy):
        def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
            raise retryable_error(ErrorCode.COMFY_JOB_FAILED, "temporary failure")

    runner = PipelineRunner(
        project,
        shots[:1],
        binding,
        template,
        comfy=AlwaysFailComfy(),
        ffmpeg=FakeFfmpeg(),
    )
    manifest_path = project.output.root / "run-terminal-failure" / "manifest.json"

    with pytest.raises(AiVideoError):
        runner.run(run_id="run-terminal-failure")

    persisted = load_manifest(manifest_path)
    assert persisted.status == "failed"
    assert len(persisted.shots) == 1
    failed = persisted.shots[0]
    assert failed.status == "failed"
    assert [item.attempt for item in failed.attempts] == [1, 2]
    assert [item.status for item in failed.attempts] == ["failed", "failed"]
    assert failed.active_attempt == 2
    assert failed.completed_at is not None
    assert failed.error == {
        "code": ErrorCode.COMFY_JOB_FAILED.value,
        "message": "temporary failure",
    }


def test_unexpected_terminal_failure_is_sanitized_and_persisted(example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    project.defaults.max_attempts = 1

    class UnexpectedFailComfy(FakeComfy):
        def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
            raise RuntimeError("secret transport detail")

    runner = PipelineRunner(
        project,
        shots[:1],
        binding,
        template,
        comfy=UnexpectedFailComfy(),
        ffmpeg=FakeFfmpeg(),
    )
    manifest_path = project.output.root / "run-unexpected-failure" / "manifest.json"

    with pytest.raises(RuntimeError, match="secret transport detail"):
        runner.run(run_id="run-unexpected-failure")

    persisted = load_manifest(manifest_path)
    failed = persisted.shots[0]
    assert failed.status == "failed"
    assert failed.attempts[0].error == {
        "code": "unexpected_error",
        "message": "Unexpected internal error",
    }
    assert "secret transport detail" not in manifest_path.read_text(encoding="utf-8")
```

Add the resume-path case explicitly:

```python
def test_resume_terminal_failure_appends_history_and_preserves_artifacts(
    example_project_and_shots,
):
    project, shots, binding, template = example_project_and_shots
    project.defaults.max_attempts = 1
    initial = PipelineRunner(
        project,
        shots[:1],
        binding,
        template,
        comfy=FakeComfy(),
        ffmpeg=FakeFfmpeg(),
    )
    initial.run(run_id="run-resume-terminal")
    manifest_path = project.output.root / "run-resume-terminal" / "manifest.json"
    before = load_manifest(manifest_path).shots[0]
    Path(before.clip_path).write_bytes(b"corrupted")

    class ResumeFailComfy(FakeComfy):
        def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
            raise retryable_error(ErrorCode.COMFY_JOB_FAILED, "resume failure")

    resumed = PipelineRunner(
        project,
        shots[:1],
        binding,
        template,
        comfy=ResumeFailComfy(),
        ffmpeg=FakeFfmpeg(),
    )

    with pytest.raises(AiVideoError):
        resumed.resume(manifest_path)

    after = load_manifest(manifest_path)
    failed = after.shots[0]
    assert after.status == "failed"
    assert failed.status == "failed"
    assert [item.attempt for item in failed.attempts] == [1, 2]
    assert [item.status for item in failed.attempts] == ["succeeded", "failed"]
    assert failed.clip_path == before.clip_path
    assert failed.clip_hash == before.clip_hash
    assert failed.last_frame_path == before.last_frame_path
    assert failed.last_frame_hash == before.last_frame_hash
    assert failed.comfy_prompt_id is None
    assert failed.rendered_workflow_path is None
    assert failed.rendered_workflow_hash is None


def test_resume_success_keeps_prior_terminal_failure_history(example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    project.defaults.max_attempts = 2

    class AlwaysFailComfy(FakeComfy):
        def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
            raise retryable_error(ErrorCode.COMFY_JOB_FAILED, "temporary failure")

    manifest_path = project.output.root / "run-terminal-resume-success" / "manifest.json"
    failed_runner = PipelineRunner(
        project,
        shots[:1],
        binding,
        template,
        comfy=AlwaysFailComfy(),
        ffmpeg=FakeFfmpeg(),
    )
    with pytest.raises(AiVideoError):
        failed_runner.run(run_id="run-terminal-resume-success")

    resumed_runner = PipelineRunner(
        project,
        shots[:1],
        binding,
        template,
        comfy=FakeComfy(),
        ffmpeg=FakeFfmpeg(),
    )
    resumed = resumed_runner.resume(manifest_path)

    record = resumed.shots[0]
    assert resumed.status == "succeeded"
    assert [item.attempt for item in record.attempts] == [1, 2, 3]
    assert [item.status for item in record.attempts] == ["failed", "failed", "succeeded"]
    assert record.active_attempt == 3
    assert (manifest_path.parent / "shots" / "shot_001" / "attempt_3" / "workflow.json").exists()
```

- [ ] **Step 2: Run the terminal tests and verify RED**

Run:

```bash
python -m pytest tests/test_pipeline.py -k "terminal_failure or unexpected_terminal" -v
```

Expected: the new tests fail because the current terminal branches escape before a failed `ShotRecord` is atomically written; the resume case also shows the new Attempt is missing.

- [ ] **Step 3: Add one Manifest v1 failed-record constructor without changing schema**

Add this classmethod to `ShotRecord`:

```python
    @classmethod
    def failed(
        cls,
        *,
        shot_id: str,
        attempts: list[AttemptRecord],
        error: dict,
        started_at: str,
        previous: "ShotRecord | None" = None,
    ) -> "ShotRecord":
        updates = {
            "status": "failed",
            "attempts": attempts,
            "active_attempt": attempts[-1].attempt,
            "rendered_workflow_path": None,
            "rendered_workflow_hash": None,
            "comfy_prompt_id": None,
            "started_at": started_at,
            "completed_at": _now(),
            "error": error,
        }
        if previous is None:
            return cls(shot_id=shot_id, **updates)
        return previous.model_copy(update=updates)
```

This method reuses existing Manifest v1 fields. When resume fails after an earlier success, `previous.model_copy()` intentionally retains the earlier clip/last-frame/normalized artifact paths and hashes so a later successful retry can compare the prior dependency artifact instead of losing provenance. It clears top-level `rendered_workflow_*` and `comfy_prompt_id` because those fields would otherwise describe the old successful active Attempt while `active_attempt` points at the new failure; P1 does not invent replacement lifecycle fields.

- [ ] **Step 4: Add the single atomic terminal-persistence seam in PipelineRunner**

Move `AttemptRecord` and `_now` into the existing top-level manifest import, remove the local import inside `_run_shot()`, and add these helpers:

```python
    @staticmethod
    def _find_shot_record(manifest: RunManifest, shot_id: str) -> ShotRecord | None:
        return next((record for record in manifest.shots if record.shot_id == shot_id), None)

    @staticmethod
    def _upsert_shot_record(manifest: RunManifest, record: ShotRecord) -> None:
        existing = PipelineRunner._find_shot_record(manifest, record.shot_id)
        if existing is None:
            manifest.shots.append(record)
            return
        manifest.shots[manifest.shots.index(existing)] = record

    @staticmethod
    def _error_record(exc: BaseException) -> dict[str, str]:
        if isinstance(exc, AiVideoError):
            return {"code": exc.code.value, "message": exc.user_message}
        return {"code": "unexpected_error", "message": "Unexpected internal error"}

    def _persist_terminal_failure(
        self,
        *,
        manifest: RunManifest,
        manifest_path: Path,
        shot: ShotSpec,
        attempts: list[AttemptRecord],
        started_at: str,
        exc: BaseException,
    ) -> None:
        error = self._error_record(exc)
        failed = ShotRecord.failed(
            shot_id=shot.id,
            attempts=attempts,
            error=error,
            started_at=started_at,
            previous=self._find_shot_record(manifest, shot.id),
        )
        self._upsert_shot_record(manifest, failed)
        manifest.status = "failed"
        atomic_write_manifest(manifest_path, manifest)
```

Pass `manifest` and `manifest_path` from both `run()` and `resume()` into `_run_shot()`. Replace the success-path append/replace duplication with `_upsert_shot_record()` so the same record owner is used by both commands.

- [ ] **Step 5: Preserve Attempt history and persist before every terminal escape**

Initialize retry numbering from the existing record and append rather than overwrite prior history:

```python
        previous_record = self._find_shot_record(manifest, shot.id)
        attempts = list(previous_record.attempts) if previous_record else []
        attempt_offset = max((item.attempt for item in attempts), default=0)

        for retry_index in range(1, max_attempts + 1):
            attempt = attempt_offset + retry_index
            attempt_record = AttemptRecord(attempt=attempt, status="running")
            try:
                record, last_frame = self._run_shot_attempt(
                    run_root=run_root,
                    actual_run_id=actual_run_id,
                    shot=shot,
                    shot_index=shot_index,
                    attempt=attempt,
                    characters=characters,
                    character_image_names=character_image_names,
                    previous_frame=previous_frame,
                    previous_frame_hash=previous_frame_hash,
                )
            except AiVideoError as exc:
                attempt_record.status = "failed"
                attempt_record.error = self._error_record(exc)
                attempts.append(attempt_record)
                if isinstance(self.comfy, ComfyClient) and "memory" in (
                    exc.technical_detail or ""
                ).lower():
                    self.comfy.free_memory()
                if exc.retryable and retry_index < max_attempts:
                    continue
                self._persist_terminal_failure(
                    manifest=manifest,
                    manifest_path=manifest_path,
                    shot=shot,
                    attempts=attempts,
                    started_at=started_at,
                    exc=exc,
                )
                raise
            except Exception as exc:
                attempt_record.status = "failed"
                attempt_record.error = self._error_record(exc)
                attempts.append(attempt_record)
                self._persist_terminal_failure(
                    manifest=manifest,
                    manifest_path=manifest_path,
                    shot=shot,
                    attempts=attempts,
                    started_at=started_at,
                    exc=exc,
                )
                raise

            attempt_record.status = "succeeded"
            attempt_record.comfy_prompt_id = record.comfy_prompt_id
            attempts.append(attempt_record)
            record.started_at = started_at
            record.attempts = attempts
            return record, last_frame
```

Required ordering on both terminal branches is: finalize Attempt in memory → construct/update failed Shot → set Run `failed` → `atomic_write_manifest()` returns successfully → re-raise the original exception. Do not catch or suppress an `atomic_write_manifest()` failure; if persistence itself fails, implementation cannot claim the original Attempt was safely recorded.

- [ ] **Step 6: Run focused and affected tests**

Run:

```bash
python -m pytest tests/test_pipeline.py -k "attempt or terminal or retry" -v
python -m pytest tests/test_manifest.py tests/test_pipeline.py tests/test_resume_e2e.py -q
```

Expected: all selected tests pass. Typed errors keep their original `AiVideoError`; unexpected errors keep their original exception type and message outside the Manifest, while the persisted record contains only sanitized text.

- [ ] **Step 7: Commit the terminal-persistence slice**

```bash
git add src/ai_video/manifest.py src/ai_video/pipeline.py tests/test_pipeline.py
git commit -m "fix: persist terminal shot failures atomically"
```

Expected: the commit contains only the three listed files and no schema/layout/CLI changes.

### Task 2: Propagate Only Changed Last-Frame Dependencies During Resume

**Files:**
- Modify: `src/ai_video/manifest.py:119-136`
- Modify: `src/ai_video/pipeline.py:104-174`
- Modify: `src/ai_video/pipeline.py:235-282`
- Modify: `src/ai_video/pipeline.py:310-314`
- Test: `tests/test_manifest.py`
- Test: `tests/test_resume_e2e.py`

- [ ] **Step 1: Write a focused unit test that rejects blanket stale marking**

Import `mark_shots_stale` and add:

```python
def test_mark_shots_stale_updates_only_requested_successful_records():
    manifest = RunManifest(
        run_id="run_1",
        shots=[
            ShotRecord(shot_id="shot_001", status="succeeded"),
            ShotRecord(shot_id="shot_002", status="succeeded"),
            ShotRecord(shot_id="shot_003", status="succeeded"),
        ],
    )

    updated = mark_shots_stale(manifest, {"shot_002"})

    assert [record.status for record in updated.shots] == [
        "succeeded",
        "stale",
        "succeeded",
    ]
```

- [ ] **Step 2: Write exact resume tests around actual artifact identity**

Change the manifest import to:

```python
from ai_video.manifest import atomic_write_manifest, load_manifest
```

Then extend `tests/test_resume_e2e.py` with a content-aware fake ffmpeg:

```python
class ContentHashFfmpeg(FakeFfmpeg):
    def extract_last_frame(self, clip: Path, frame: Path) -> None:
        frame.parent.mkdir(parents=True, exist_ok=True)
        frame.write_bytes(clip.read_bytes())
```

Add the exact content-aware fixture and cases below. This extracts the current inline `test_resume_after_partial_run()` setup into a helper without bypassing the production config/workflow loaders:

```python
class VersionedFakeComfy(FakeComfy):
    def __init__(self, generation: str):
        super().__init__()
        self.generation = generation

    def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
        self.submitted.append(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shot_id = output_path.parent.name
        output_path.write_bytes(f"{self.generation}:{shot_id}".encode())
        return "prompt-id"


def _build_dependency_case(
    tmp_path: Path,
    *,
    second_shot_init: bool = False,
    bind_init_image: bool = True,
):
    refs = tmp_path / "refs"
    refs.mkdir()
    (refs / "hero.png").write_bytes(b"png")
    (tmp_path / "init.png").write_bytes(b"init")
    workflow_dir = tmp_path / "wf"
    workflow_dir.mkdir()
    (workflow_dir / "template.json").write_text(
        '{"3":{"class_type":"KSampler","inputs":{"seed":1}},'
        '"6":{"class_type":"CLIPTextEncode","inputs":{"text":""}},'
        '"7":{"class_type":"CLIPTextEncode","inputs":{"text":""}},'
        '"12":{"class_type":"LoadImage","inputs":{"image":""}},'
        '"42":{"class_type":"VHS_VideoCombine","inputs":{"filename_prefix":""}}}',
        encoding="utf-8",
    )
    init_binding = "init_image:\n  path: ['12', inputs, image]\n" if bind_init_image else ""
    (workflow_dir / "binding.yaml").write_text(
        "positive_prompt:\n  path: ['6', inputs, text]\n"
        "negative_prompt:\n  path: ['7', inputs, text]\n"
        "seed:\n  path: ['3', inputs, seed]\n"
        f"{init_binding}"
        "output_prefix:\n  path: ['42', inputs, filename_prefix]\n"
        "character_refs: []\n"
        "clip_output:\n  node: '42'\n  kind: gifs\n"
        "  extensions: ['.mp4']\n  select: first\n",
        encoding="utf-8",
    )
    project_yaml = tmp_path / "project.yaml"
    project_yaml.write_text(
        "project_name: dependency-test\ncomfy:\n  base_url: http://127.0.0.1:8188\n"
        "workflow:\n  template: wf/template.json\n  binding: wf/binding.yaml\n"
        "output:\n  root: runs\n  min_free_gb: 0\n"
        "defaults:\n  seed: 100\n  fps: 16\n  width: 512\n  height: 512\n",
        encoding="utf-8",
    )
    init_line = "    init_image: init.png\n" if second_shot_init else ""
    shots_yaml = tmp_path / "shots.yaml"
    shots_yaml.write_text(
        "shots:\n  - id: shot_001\n    prompt: first\n"
        "  - id: shot_002\n    prompt: second\n"
        f"{init_line}"
        "  - id: shot_003\n    prompt: third\n",
        encoding="utf-8",
    )
    project = load_project(project_yaml)
    shots = load_shots(shots_yaml, project)
    binding = WorkflowBinding.model_validate(load_yaml(project.workflow.binding))
    template = load_workflow_template(project.workflow.template)
    manifest_path = project.output.root / "run-dependency" / "manifest.json"
    return project, shots, binding, template, manifest_path


def _run_initial_dependency_case(
    tmp_path: Path,
    *,
    second_shot_init: bool = False,
    bind_init_image: bool = True,
):
    project, shots, binding, template, manifest_path = _build_dependency_case(
        tmp_path,
        second_shot_init=second_shot_init,
        bind_init_image=bind_init_image,
    )
    initial = PipelineRunner(
        project,
        shots,
        binding,
        template,
        comfy=VersionedFakeComfy("old"),
        ffmpeg=ContentHashFfmpeg(),
    )
    initial.run(run_id="run-dependency")
    initial_manifest = load_manifest(manifest_path)
    if bind_init_image and not second_shot_init:
        assert (
            initial_manifest.shots[1].chain_input_hash
            == initial_manifest.shots[0].last_frame_hash
        )
    else:
        assert initial_manifest.shots[1].chain_input_hash is None
    shot_001_clip = project.output.root / "run-dependency" / "shots" / "shot_001" / "clip.mp4"
    shot_001_clip.write_bytes(b"corrupted")
    return project, shots, binding, template, manifest_path


def test_resume_propagates_when_each_consumed_last_frame_changes(tmp_path):
    project, shots, binding, template, manifest_path = _run_initial_dependency_case(tmp_path)
    resume_comfy = VersionedFakeComfy("new")
    runner = PipelineRunner(
        project,
        shots,
        binding,
        template,
        comfy=resume_comfy,
        ffmpeg=ContentHashFfmpeg(),
    )
    runner.resume(manifest_path)

    assert [path.parent.name for path in resume_comfy.submitted] == [
        "shot_001",
        "shot_002",
        "shot_003",
    ]


def test_resume_skips_downstream_when_regenerated_last_frame_hash_is_unchanged(tmp_path):
    project, shots, binding, template, manifest_path = _run_initial_dependency_case(tmp_path)
    resume_comfy = VersionedFakeComfy("old")
    runner = PipelineRunner(
        project,
        shots,
        binding,
        template,
        comfy=resume_comfy,
        ffmpeg=ContentHashFfmpeg(),
    )
    runner.resume(manifest_path)

    assert [path.parent.name for path in resume_comfy.submitted] == ["shot_001"]


def test_explicit_init_image_breaks_last_frame_stale_propagation(tmp_path):
    project, shots, binding, template, manifest_path = _run_initial_dependency_case(
        tmp_path,
        second_shot_init=True,
    )
    historical = load_manifest(manifest_path)
    historical.shots[1].chain_input_hash = historical.shots[0].last_frame_hash
    atomic_write_manifest(manifest_path, historical)
    resume_comfy = VersionedFakeComfy("new")
    runner = PipelineRunner(
        project,
        shots,
        binding,
        template,
        comfy=resume_comfy,
        ffmpeg=ContentHashFfmpeg(),
    )
    runner.resume(manifest_path)

    assert [path.parent.name for path in resume_comfy.submitted] == ["shot_001"]


def test_workflow_without_init_binding_has_no_last_frame_dependency(tmp_path):
    project, shots, binding, template, manifest_path = _run_initial_dependency_case(
        tmp_path,
        bind_init_image=False,
    )
    resume_comfy = VersionedFakeComfy("new")
    runner = PipelineRunner(
        project,
        shots,
        binding,
        template,
        comfy=resume_comfy,
        ffmpeg=ContentHashFfmpeg(),
    )
    runner.resume(manifest_path)

    assert [path.parent.name for path in resume_comfy.submitted] == ["shot_001"]
```

The test setup must keep shot IDs, paths and flat layout unchanged. The explicit-init fixture file must be created under `tmp_path`; do not add a repository asset.

- [ ] **Step 3: Run the dependency tests and verify RED plus guard behavior**

Run:

```bash
python -m pytest tests/test_manifest.py tests/test_resume_e2e.py -k "stale or propagates or downstream or explicit_init or binding" -v
```

Expected: the changed-hash propagation case fails under the current code because only the invalid upstream Shot reruns. The same-hash, explicit-init and no-binding cases constrain the implementation against blanket invalidation and may already pass before GREEN.

- [ ] **Step 4: Replace the blanket manifest helper with exact-ID stale marking**

Delete `mark_downstream_stale()`, import `mark_shots_stale` from `ai_video.manifest` in `pipeline.py`, and add:

```python
def mark_shots_stale(manifest: RunManifest, shot_ids: set[str]) -> RunManifest:
    updated = [
        record.model_copy(update={"status": "stale"})
        if record.shot_id in shot_ids and record.status == "succeeded"
        else record
        for record in manifest.shots
    ]
    return manifest.model_copy(update={"shots": updated, "updated_at": _now()})
```

`manifest.py` does not infer graph edges. `PipelineRunner` must pass only Shot IDs already proven to consume a changed artifact.

- [ ] **Step 5: Resolve effective last-frame dependency in one PipelineRunner predicate**

Add these helpers:

```python
    def _uses_previous_frame(self, shot: ShotSpec, previous_frame: Path | None) -> bool:
        return (
            self.binding.init_image is not None
            and shot.init_image is None
            and previous_frame is not None
        )

    def _effective_chain_input_hash(
        self,
        shot: ShotSpec,
        previous_frame: Path | None,
        previous_frame_hash: str | None,
    ) -> str | None:
        if not self._uses_previous_frame(shot, previous_frame):
            return None
        return previous_frame_hash

    def _shot_is_current(
        self,
        record: ShotRecord,
        shot: ShotSpec,
        previous_frame: Path | None,
        previous_frame_hash: str | None,
    ) -> bool:
        if not successful_shot_is_valid(record):
            return False
        if not self._uses_previous_frame(shot, previous_frame):
            return True
        return record.chain_input_hash == previous_frame_hash
```

For a Shot with explicit `shot.init_image`, or a workflow without an `init_image` binding, `_shot_is_current()` intentionally ignores any historical non-null `chain_input_hash` produced by the old unconditional recording path. This avoids a one-time over-invalidation of Legacy manifests that recorded a dependency the workflow never consumed.

- [ ] **Step 6: Make the succeeded fast path use the same dependency predicate**

Add a sequential preflight and replace the current artifact-only `all` expression:

```python
    def _all_resume_shots_current(self, manifest: RunManifest) -> bool:
        previous_frame: Path | None = None
        previous_frame_hash: str | None = None
        for shot in self.shots:
            record = self._find_shot_record(manifest, shot.id)
            if record is None or not self._shot_is_current(
                record,
                shot,
                previous_frame,
                previous_frame_hash,
            ):
                return False
            previous_frame = Path(record.last_frame_path) if record.last_frame_path else None
            previous_frame_hash = record.last_frame_hash
        return True
```

Use:

```python
        if manifest.status == "succeeded" and self._all_resume_shots_current(manifest):
            return manifest
```

This preserves no-op resume while removing the second artifact-only decision path.

- [ ] **Step 7: Record only the dependency actually rendered**

In `_run_shot_attempt()`, replace the unconditional `chain_input_hash=previous_frame_hash` with:

```python
            chain_input_hash=self._effective_chain_input_hash(
                shot,
                previous_frame,
                previous_frame_hash,
            ),
```

Do not add fields to `ShotRecord`. Do not make `successful_shot_is_valid()` aware of `ShotSpec` or binding state.

- [ ] **Step 8: Atomically persist one propagation edge after an upstream rerun**

In the sequential resume loop:

1. Use `_shot_is_current()` for the skip decision.
2. Save `old_last_frame_hash = existing.last_frame_hash if existing else None` before rerun.
3. Upsert the successful new record.
4. If `old_last_frame_hash != record.last_frame_hash`, inspect only `self.shots[index + 1]`.
5. If that direct next Shot actually uses `record`'s last frame and its stored `chain_input_hash` is not already the new hash, call `mark_shots_stale()` for that one ID.
6. Atomically write the new upstream record and the direct downstream stale status together.

The core replacement is:

```python
            if existing and self._shot_is_current(
                existing,
                shot,
                previous_frame,
                previous_frame_hash,
            ):
                previous_frame = Path(existing.last_frame_path) if existing.last_frame_path else None
                previous_frame_hash = existing.last_frame_hash
                continue

            old_last_frame_hash = existing.last_frame_hash if existing else None
            record, previous_frame = self._run_shot(
                manifest=manifest,
                manifest_path=manifest_path,
                run_root=run_root,
                actual_run_id=manifest.run_id,
                shot=shot,
                shot_index=index,
                characters=characters,
                character_image_names=character_image_names,
                previous_frame=previous_frame,
                previous_frame_hash=previous_frame_hash,
            )
            self._upsert_shot_record(manifest, record)
            previous_frame_hash = record.last_frame_hash

            if old_last_frame_hash != record.last_frame_hash and index + 1 < len(self.shots):
                next_shot = self.shots[index + 1]
                next_record = self._find_shot_record(manifest, next_shot.id)
                if (
                    next_record is not None
                    and self._uses_previous_frame(next_shot, previous_frame)
                    and next_record.chain_input_hash != record.last_frame_hash
                ):
                    manifest = mark_shots_stale(manifest, {next_shot.id})

            atomic_write_manifest(manifest_path, manifest)
```

Do not mark all later Shots eagerly. A further Shot becomes stale only if its direct upstream Shot actually reruns, produces a different last-frame hash, and that consumer is not already aligned to the new hash. If an upstream rerun recreates identical last-frame bytes, no downstream generation is invalidated.

- [ ] **Step 9: Run focused, component and e2e verification**

Run:

```bash
python -m pytest tests/test_manifest.py tests/test_resume_e2e.py -k "stale or propagates or downstream or explicit_init or binding" -v
python -m pytest tests/test_manifest.py tests/test_pipeline.py tests/test_resume_e2e.py -v
```

Expected: changed hashes propagate through the real chain; same hashes stop propagation; explicit init and absent binding cut the edge; no-op resume still makes zero Comfy submissions; existing flat paths and final output remain valid.

- [ ] **Step 10: Commit the dependency-aware resume slice**

```bash
git add src/ai_video/manifest.py src/ai_video/pipeline.py tests/test_manifest.py tests/test_resume_e2e.py
git commit -m "fix: propagate changed chain dependencies on resume"
```

Expected: the commit contains only the four listed files. `character_ref_hashes` remains recorded but is not added to validity in P1.

### Task 3: Lock Legacy Generation and Delivery FPS Semantics

**Files:**
- Modify: `src/ai_video/workflow_renderer.py:183-212`
- Modify: `src/ai_video/pipeline.py:80-94`
- Modify: `src/ai_video/pipeline.py:154-167`
- Modify: `tests/test_pipeline.py`
- Modify: `README.md:82-98`
- Verify only: `src/ai_video/models.py`
- Verify only: `tests/test_config.py`
- Verify only: `tests/test_workflow_renderer.py`

- [ ] **Step 1: Write a pipeline test that separates generation FPS from delivery FPS**

Extend `FakeFfmpeg` to retain normalization arguments:

```python
class FakeFfmpeg:
    def __init__(self):
        self.normalize_calls = []

    def normalize_clip(self, source: Path, target: Path, **kwargs) -> None:
        self.normalize_calls.append(kwargs)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
```

Add the import:

```python
from ai_video.models import JsonPathBinding
```

Then add a frame-rate binding to the fixture instance and assert run plus resume behavior:

```python
def test_shot_fps_overrides_generation_but_not_delivery_normalization(
    example_project_and_shots,
):
    project, shots, binding, template = example_project_and_shots
    project.defaults.fps = 16
    shots[0].fps = 20
    template["45"] = {
        "class_type": "VHS_VideoCombine",
        "inputs": {"frame_rate": 0},
    }
    binding.frame_rate = JsonPathBinding(path=["45", "inputs", "frame_rate"])
    comfy = FakeComfy()
    ffmpeg = FakeFfmpeg()

    runner = PipelineRunner(project, shots[:1], binding, template, comfy=comfy, ffmpeg=ffmpeg)
    runner.run(run_id="run-fps-semantics")

    assert comfy.submitted[0]["45"]["inputs"]["frame_rate"] == 20
    assert [call["fps"] for call in ffmpeg.normalize_calls] == [16]

    clip = project.output.root / "run-fps-semantics" / "shots" / "shot_001" / "clip.mp4"
    clip.write_bytes(b"corrupted")
    resume_comfy = FakeComfy()
    resume_ffmpeg = FakeFfmpeg()
    resumed = PipelineRunner(
        project,
        shots[:1],
        binding,
        template,
        comfy=resume_comfy,
        ffmpeg=resume_ffmpeg,
    )
    resumed.resume(project.output.root / "run-fps-semantics" / "manifest.json")

    assert resume_comfy.submitted[0]["45"]["inputs"]["frame_rate"] == 20
    assert [call["fps"] for call in resume_ffmpeg.normalize_calls] == [16]
```

- [ ] **Step 2: Run the FPS tests before semantic cleanup**

Run:

```bash
python -m pytest tests/test_pipeline.py -k "fps or normalization" -v
python -m pytest tests/test_workflow_renderer.py -k "timing or replaces_bound_fields" -v
```

Expected: the behavioral assertions should characterize the already implemented compatibility behavior. If they fail, stop and reconcile the current code instead of adding a new config contract.

- [ ] **Step 3: Clarify local names without changing public config**

In `workflow_renderer.py`, rename the local variable only:

```python
    generation_fps = shot.fps or defaults.fps
    clip_seconds = shot.clip_seconds or defaults.clip_seconds
    resolution = max(width, height)
    frame_count = max(1, generation_fps * clip_seconds + 1)

    if binding.frame_count is not None:
        _set_binding_value(
            workflow,
            binding.frame_count,
            frame_count,
            "frame_count",
        )
    if binding.frame_rate is not None:
        _set_binding_value(
            workflow,
            binding.frame_rate,
            generation_fps,
            "frame_rate",
        )
```

Extract the duplicated run/resume normalization block into this private helper so delivery FPS has one internal owner:

```python
    def _normalize_shots(self, manifest: RunManifest, run_root: Path) -> list[Path]:
        delivery_fps = self.project.defaults.fps
        normalized_paths: list[Path] = []
        for shot_record in manifest.shots:
            source = Path(shot_record.clip_path or "")
            target = run_root / "normalized" / f"{shot_record.shot_id}.mp4"
            self.ffmpeg.normalize_clip(
                source,
                target,
                width=self.project.defaults.width,
                height=self.project.defaults.height,
                fps=delivery_fps,
                encoder="libx264",
            )
            shot_record.normalized_clip_path = str(target)
            shot_record.normalized_clip_hash = sha256_file(target)
            normalized_paths.append(target)
        return normalized_paths
```

Replace each duplicated loop in `run()` and `resume()` with:

```python
        normalized_paths = self._normalize_shots(manifest, run_root)
```

Do not add `delivery_fps` to `DefaultsConfig`, YAML, Manifest v1 or CLI. For Legacy config, `defaults.fps` remains both the generation fallback and the fixed delivery normalization rate; only `shot.fps` is generation-only.

- [ ] **Step 4: Replace README gap wording with implemented truth and FPS semantics**

Update the user-visible paragraphs to state:

```markdown
- Runtime truth fix plan: [`docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md`](docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p1-runtime-truth-fixes.md)

The MVP keeps rendered workflow snapshots and persists each Shot's Attempt history, including a terminally failed Shot, before the original failure leaves the pipeline. Resume appends later Attempts without overwriting the earlier terminal history. Delete old `runs/<run_id>` directories manually when you no longer need them.

## FPS Semantics

For the Legacy config, `defaults.fps` is the fallback source-generation FPS and the fixed delivery-normalization FPS. A Shot-level `fps` overrides only that Shot's source workflow generation rate; all generated clips are still normalized to `defaults.fps` before stitching. P1 does not add a new config field or change the Manifest schema.

## Resume

Resume reloads the existing Manifest and validates each persisted clip and last-frame hash. For a workflow that binds `init_image`, a Shot without its own explicit `init_image` also records and checks the last-frame hash it actually consumed. When an upstream rerun produces a different last-frame artifact, only the direct consumer is marked stale; propagation continues only when that rerun changes the next artifact. An identical regenerated frame or an explicit Shot `init_image` stops propagation. Character-reference hashes remain recorded but are not part of Legacy resume validity in P1.
```

Do not change the documented commands or artifact tree.

- [ ] **Step 5: Run FPS, config and renderer regression tests**

Run:

```bash
python -m pytest tests/test_pipeline.py -k "fps or normalization" -v
python -m pytest tests/test_config.py tests/test_workflow_renderer.py -v
```

Expected: Shot override drives generation `frame_rate`; run and resume normalization both use `defaults.fps`; all existing config and renderer tests pass without schema changes.

- [ ] **Step 6: Commit the FPS semantics and user documentation**

```bash
git add src/ai_video/workflow_renderer.py src/ai_video/pipeline.py tests/test_pipeline.py README.md
git commit -m "refactor: clarify source and delivery fps roles"
```

Expected: the commit contains only the four listed files. `src/ai_video/models.py` and `tests/test_config.py` remain unchanged.

### Task 4: Verify the P1 Slice and Reject Scope Leakage

**Files:**
- Verify: `src/ai_video/manifest.py`
- Verify: `src/ai_video/pipeline.py`
- Verify: `src/ai_video/workflow_renderer.py`
- Verify: `tests/test_manifest.py`
- Verify: `tests/test_pipeline.py`
- Verify: `tests/test_resume_e2e.py`
- Verify: `tests/test_config.py`
- Verify: `README.md`
- Must remain unchanged: public CLI surface、Manifest v1 fields、artifact layout、dependencies、Provider/cloud/audio subsystems

- [ ] **Step 1: Run the P1 acceptance test set**

Run:

```bash
python -m pytest tests/test_manifest.py tests/test_pipeline.py tests/test_resume_e2e.py tests/test_config.py tests/test_workflow_renderer.py -v
```

Expected: command exits `0`; terminal failure, precise dependency propagation and FPS compatibility cases all pass.

- [ ] **Step 2: Run the complete no-network regression suite**

Run:

```bash
python -m pytest -q
```

Expected: command exits `0`; default tests do not contact real ComfyUI or any cloud Provider.

- [ ] **Step 3: Prove terminal persistence ordering and dependency ownership**

Run:

```bash
rg -n "_persist_terminal_failure|atomic_write_manifest|except AiVideoError|except Exception|raise$" src/ai_video/pipeline.py
rg -n "_all_resume_shots_current|_shot_is_current|_uses_previous_frame|mark_shots_stale|chain_input_hash" src/ai_video/manifest.py src/ai_video/pipeline.py
rg -n "mark_downstream_stale" src tests
```

Expected: terminal branches call the atomic persistence seam before `raise`; both succeeded fast path and per-Shot resume use the same dependency predicate; the old blanket helper has no matches.

- [ ] **Step 4: Prove FPS compatibility and absence of schema migration**

Run:

```bash
rg -n "generation_fps|delivery_fps|defaults\\.fps|shot\\.fps|normalize_clip" src/ai_video/models.py src/ai_video/workflow_renderer.py src/ai_video/pipeline.py README.md tests/test_pipeline.py tests/test_config.py
git diff HEAD~3..HEAD -- src/ai_video/models.py src/ai_video/cli.py src/ai_video/config.py pyproject.toml
```

Expected: semantic names and tests show the two roles; the diff for models/CLI/config/dependency declaration is empty.

- [ ] **Step 5: Scan for forbidden P2+ scope**

Run:

```bash
rg -n "VideoProvider|WanComfyProvider|MockProvider|Manifest v2|schema_version|Take|Human Review|Budget Guard|Seedance|Cloud Egress|Audio Timeline|delivery_fps:" src tests README.md
git diff --name-only HEAD~3..HEAD
git diff --check HEAD~3..HEAD
```

Expected: no new P2+ implementation identifier or config field appears. Changed files are limited to P1 ownership, and `git diff --check` exits `0`.

- [ ] **Step 6: Inspect final history and working-tree ownership**

Run:

```bash
git status --short --branch
git log -3 --oneline --decorate
git show --stat --oneline HEAD~3..HEAD
```

Expected: the three planned commits are present; no P1-owned changes remain unstaged; unrelated user work, if any, remains untouched.

## Acceptance Criteria

P1 只有在以下全部成立时才完成：

1. Typed terminal `AiVideoError` 和 unexpected terminal exception 都在原异常离开 pipeline 前将 sanitized failed Attempt、failed Shot 和 Run `failed` 状态通过 `atomic_write_manifest()` 持久化。
2. `run()` 与 `resume()` 都使用同一 terminal-persistence seam；resume 的新 Attempt 追加到原 history，不覆盖旧 Attempt 或 workflow attempt directory。
3. Unexpected exception 在 Manifest 中只持久化 sanitized error，但对 caller 仍保持原 exception/exit semantics。
4. `successful_shot_is_valid()` 仍只校验 Shot 自身 clip/last-frame artifact；dependency-aware 判定只在 `PipelineRunner.resume()`。
5. 只有 `binding.init_image` 存在、Shot 没有 explicit `init_image`、且确实存在 previous frame 时，该 Shot 才记录并校验 `chain_input_hash`。
6. 上游重跑产生不同 last-frame hash 时，只标记直接消费该 artifact 的 Shot stale；传播由各直接边的实际新 artifact 逐步决定。
7. 上游重跑得到相同 last-frame hash、显式 `shot.init_image` 或无 `init_image` binding 时，不产生过度 invalidation。
8. Succeeded Run 在所有 own artifacts 和真实 dependency hashes 都有效时仍是 no-op resume。
9. Legacy `defaults.fps` 仍是 generation fallback 和固定 delivery-normalization FPS；`shot.fps` 仅覆盖 source workflow generation。
10. Manifest v1 fields、flat artifact layout、`validate/run/resume` 公共命令、exit-code semantics、Local ComfyUI default 和当前 dependency set 均未改变。
11. `README.md` 只描述实施后已验证的 Attempt、resume 和 FPS 行为，不将 P2+ 写成 runtime truth。
12. 定向 P1 tests 和全量 `python -m pytest -q` 都退出 `0`。

## Rollback

P1 不包含 schema 或数据迁移，回滚为三个普通 Git revert：

1. 按相反顺序使用 `git revert <commit>` 回退 FPS/docs、dependency propagation 和 terminal persistence commits。
2. 不使用 `git reset --hard`，不删除用户产物，不改写已发布历史。
3. 回滚后运行 `python -m pytest -q`。
4. 回滚会恢复 P0 记录的已知 runtime gaps；既有 Manifest v1 和 flat artifacts 无需转换或移动。

## Scope-Leak Checklist

在实施 handoff 前逐项确认：

- [ ] 没有新建 Provider module、DTO、adapter 或 remote transport。
- [ ] 没有增加 Manifest field、`schema_version` 或 v2 reader/writer。
- [ ] 没有改变 CLI parser、command、flag 或 exit code。
- [ ] 没有改变 `runs/<run_id>/` 目录结构或文件命名。
- [ ] 没有加入 cloud、Budget、Audio、Take、Review、Timeline 或 evaluator 逻辑。
- [ ] 没有新 runtime dependency 或 `pyproject.toml` 变化。
- [ ] 没有将 `character_ref_hashes` 或 P2+ fingerprint 暗中接入 validity。
- [ ] 没有把 `shot.fps` 误用为 delivery FPS，也没有新增未批准的 `delivery_fps` config。

## Execution Handoff

Plan 完成并审查后，停止。不得在本 planning window 执行 Task 1-4。

用户单独批准实施后，可选执行方式：

1. **Subagent-Driven** — 使用 `superpowers:subagent-driven-development`，按 Task 顺序、单 writer lane 执行，并在每个 commit 后 review。
2. **Inline Execution** — 使用 `superpowers:executing-plans`，分 Task 执行并在 commit boundary 进行 review checkpoint。

本 plan 不得被解读为用户已选择任一执行方式。
