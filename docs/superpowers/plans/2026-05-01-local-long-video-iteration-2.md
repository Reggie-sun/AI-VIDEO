# Local Long-Video Iteration 2: Resume, Reliability, and Production Readiness

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the resume pipeline, add real manifest-driven resume with stale detection, fix path resolution bugs exposed by the first real run, add CLI progress output, and harden the end-to-end chain so interrupted runs recover cleanly and repeated runs are reliable.

**Architecture:** Build on the existing manifest-driven pipeline. The first real run (`first-real-run`) proved the happy path but exposed several gaps: manifest `final_output` stays `null` even after stitching, resume is a no-op stub, shot paths contain `configs/../` relative artifacts, and there is no CLI progress feedback during long local ComfyUI generations. Each fix is small and testable; we do not add new subsystems.

**Tech Stack:** Python 3.11+, Pydantic v2, PyYAML, httpx, pytest, ffmpeg/ffprobe subprocess calls. No new dependencies.

---

## What Iteration 1 Proved

The first real run (`first-real-run`) generated 3 clips with Wan2.2 I2V on a local ComfyUI, extracted last frames, chained them, normalized, and stitched `final.mp4`. Key observations:

1. **Happy path works end-to-end.** 3 shots, ~5 minutes per shot, final.mp4 is 2.9 MB and playable.
2. **Manifest `final_output` is `null`.** The pipeline writes `manifest.status = "succeeded"` and `final_output` string, but the manifest on disk shows `null` — the atomic write after stitching is either not reaching the right path or the manifest is being overwritten.
3. **Shot artifact paths contain `configs/../`.** The working directory when running from `configs/` produces paths like `configs/../runs/first-real-run/...` — path resolution should produce clean absolute paths.
4. **`resume` is a stub.** `PipelineRunner.resume()` calls `self.run()` which creates a brand new run instead of loading the existing manifest, skipping completed shots, and re-running only failed/stale ones.
5. **No progress output.** During 5-minute ComfyUI generations, the CLI is silent. Users have no idea what is happening.
6. **`started_at` is always `null`.** Shot records never set `started_at`.
7. **`attempt` records are empty.** `ShotRecord.attempts` is always `[]` — the per-attempt tracking is not populated.
8. **No `project_config_hash`, `workflow_template_hash`, or `workflow_binding_hash`.** These are always `null` in the manifest, so stale detection on resume cannot work.
9. **`normalize_clip` and `stitch_clips` use stream copy.** When clips have different encoding parameters (e.g., different resolutions from non-deterministic generation), stream copy can produce broken output. The spec says "If not, do a final re-encode pass."
10. **`wan22_quick.shots.yaml` has only 1 shot.** A quick-test config exists but is not integrated with the CLI.

## File Structure

- Modify: `src/ai_video/pipeline.py` — fix manifest final_output write, add real resume, populate started_at/attempts, compute config hashes
- Modify: `src/ai_video/manifest.py` — add `mark_downstream_stale` usage in resume, add `re_extract_missing_last_frame`
- Modify: `src/ai_video/ffmpeg_tools.py` — add re-encode fallback when stream copy fails
- Modify: `src/ai_video/cli.py` — add progress output during run/resume
- Modify: `src/ai_video/config.py` — fix path resolution to produce clean absolute paths
- Modify: `tests/test_pipeline.py` — add resume integration tests, stale detection tests
- Modify: `tests/test_manifest.py` — add re-extract and stale chain tests
- Modify: `tests/test_ffmpeg_tools.py` — add re-encode fallback test
- Modify: `tests/test_cli.py` — add progress output tests
- Modify: `tests/test_config.py` — add path cleanliness test

---

## Task 1: Fix Path Resolution — Clean Absolute Paths

**Files:**
- Modify: `src/ai_video/config.py:36-39`
- Modify: `tests/test_config.py`

**Problem:** When the CLI is run from a subdirectory like `configs/`, `_resolve_path` resolves relative paths against the project file's parent, but the resulting path can be `configs/../runs/...` because `Path.resolve()` is never called. The manifest stores these ugly paths.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py — add to existing file
def test_resolved_paths_are_clean_absolute(tmp_path):
    project_path, _ = write_example_files(tmp_path)
    project = load_project(project_path)
    # All resolved paths should be absolute and contain no ../
    for char in project.characters:
        for img in char.reference_images:
            assert img.is_absolute(), f"Character image path is not absolute: {img}"
            assert ".." not in str(img), f"Character image path contains ..: {img}"
    assert project.workflow.template.is_absolute()
    assert ".." not in str(project.workflow.template)
    assert project.workflow.binding.is_absolute()
    assert ".." not in str(project.workflow.binding)
    assert project.output.root.is_absolute()
    assert ".." not in str(project.output.root)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_resolved_paths_are_clean_absolute -v`
Expected: FAIL — paths are not resolved to absolute (or contain `..`)

- [ ] **Step 3: Fix `_resolve_path` to return clean absolute paths**

```python
# src/ai_video/config.py — replace _resolve_path
def _resolve_path(base_dir: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    if path.is_absolute():
        return path.resolve()
    return (base_dir / path).resolve()
```

The `.resolve()` call eliminates `..` segments and makes paths absolute.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: All tests pass, including the new one.

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: 24+ tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/ai_video/config.py tests/test_config.py
git commit -m "fix: resolve config paths to clean absolute form without .. segments"
```

---

## Task 2: Fix Manifest — Populate final_output And Config Hashes

**Files:**
- Modify: `src/ai_video/pipeline.py:41-89`
- Modify: `tests/test_pipeline.py`

**Problem:** The manifest after `first-real-run` shows `final_output: null` and all config hashes are `null`. The pipeline sets these fields but the manifest on disk doesn't reflect the update. Additionally, config/template/binding hashes are never computed, making stale detection impossible.

- [ ] **Step 1: Write the failing test**

The existing `example_project_and_shots` fixture in `tests/conftest.py` creates a project with 3 shots. The output root is `tmp_path / "runs"` (resolved by `load_project`). Use this fixture.

```python
# tests/test_pipeline.py — add to existing file
from ai_video.manifest import load_manifest

def test_run_populates_manifest_final_output_and_hashes(example_project_and_shots, tmp_path):
    project, shots, binding, template = example_project_and_shots
    runner = PipelineRunner(project, shots, binding, template, comfy=FakeComfy(), ffmpeg=FakeFfmpeg())
    manifest = runner.run(
        run_id="run-hashes",
        project_config_path=tmp_path / "project.yaml",
        shot_list_path=tmp_path / "shots.yaml",
    )
    assert manifest.final_output is not None
    assert manifest.final_output.endswith("final.mp4")
    assert manifest.project_config_hash is not None
    assert manifest.workflow_template_hash is not None
    assert manifest.workflow_binding_hash is not None
    # Verify manifest on disk matches
    run_dir = tmp_path / "runs" / "run-hashes"
    disk_manifest = load_manifest(run_dir / "manifest.json")
    assert disk_manifest.final_output is not None
    assert disk_manifest.final_output == manifest.final_output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline.py::test_run_populates_manifest_final_output_and_hashes -v`
Expected: FAIL — `final_output` is None, config hashes are None

- [ ] **Step 3: Fix pipeline to compute and store config hashes, and ensure manifest write after stitching**

In `PipelineRunner.run()`, compute hashes before the shot loop and ensure the final manifest write persists:

```python
# src/ai_video/pipeline.py — in run() method, after creating manifest:
import json

manifest.project_config_hash = sha256_file(self.project._config_path) if hasattr(self.project, '_config_path') else None
manifest.workflow_template_hash = sha256_file(self.project.workflow.template) if self.project.workflow.template.exists() else None
manifest.workflow_binding_hash = sha256_file(self.project.workflow.binding) if self.project.workflow.binding.exists() else None
atomic_write_manifest(manifest_path, manifest)
```

Also, the pipeline needs to accept `project_config_path` and `shot_list_path` to compute hashes. Add optional parameters:

```python
def run(self, run_id: str | None = None, *, project_config_path: Path | None = None, shot_list_path: Path | None = None) -> RunManifest:
```

And store them in the manifest:

```python
manifest.project_config_path = str(project_config_path) if project_config_path else None
manifest.shot_list_path = str(shot_list_path) if shot_list_path else None
if project_config_path and project_config_path.exists():
    manifest.project_config_hash = sha256_file(project_config_path)
if self.project.workflow.template.exists():
    manifest.workflow_template_hash = sha256_file(self.project.workflow.template)
if self.project.workflow.binding.exists():
    manifest.workflow_binding_hash = sha256_file(self.project.workflow.binding)
```

The CLI should pass these paths when calling `run()`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline.py -v`
Expected: All pipeline tests pass.

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`
Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/ai_video/pipeline.py tests/test_pipeline.py
git commit -m "fix: populate manifest final_output, config/template/binding hashes"
```

---

## Task 3: Fix Shot Records — Populate started_at And Attempts

**Files:**
- Modify: `src/ai_video/pipeline.py:104-190`
- Modify: `tests/test_pipeline.py`

**Problem:** `ShotRecord.started_at` is always `null` and `ShotRecord.attempts` is always `[]`. The pipeline runs shots but doesn't record when they started or track each attempt.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline.py — add
def test_run_populates_shot_started_at_and_attempts(tmp_path, example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    runner = PipelineRunner(project, shots, binding, template, comfy=FakeComfy(), ffmpeg=FakeFfmpeg())
    manifest = runner.run(run_id="run-attempts")
    for shot_record in manifest.shots:
        assert shot_record.started_at is not None
        assert len(shot_record.attempts) >= 1
        assert shot_record.attempts[0].status == "succeeded"
        assert shot_record.attempts[0].attempt == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline.py::test_run_populates_shot_started_at_and_attempts -v`
Expected: FAIL — `started_at` is None, `attempts` is `[]`

- [ ] **Step 3: Fix pipeline to record started_at and attempt records**

In `_run_shot()`, set `started_at` before the attempt loop. After each attempt, add an `AttemptRecord`:

```python
# In _run_shot, before the attempt loop:
from datetime import datetime, timezone
record_started_at = datetime.now(timezone.utc).isoformat()

# Inside the attempt loop, after success:
attempt_record = AttemptRecord(attempt=attempt, status="succeeded", comfy_prompt_id=prompt_id)
```

In `_run_shot_attempt()`, return the `attempt_record` along with the `ShotRecord` and `last_frame_path`. Then in `_run_shot()`, accumulate attempt records and set them on the final `ShotRecord`.

Also set `shot_record.started_at = record_started_at` after the shot succeeds.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline.py -v`
Expected: All pipeline tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/ai_video/pipeline.py tests/test_pipeline.py
git commit -m "fix: populate shot started_at and attempt records in manifest"
```

---

## Task 4: Implement Real Resume — Skip Completed, Re-Run Failed/Stale

**Files:**
- Modify: `src/ai_video/pipeline.py:91-95`
- Modify: `src/ai_video/manifest.py`
- Modify: `tests/test_pipeline.py`
- Modify: `tests/test_manifest.py`

**Problem:** `PipelineRunner.resume()` is a stub that just calls `self.run()` with the same run_id, creating a fresh run. It should: (1) load the existing manifest, (2) validate completed shots' artifacts, (3) skip shots that are still valid, (4) re-extract missing last frames, (5) re-run failed/stale shots, (6) mark downstream shots stale if an upstream shot is re-run.

- [ ] **Step 1: Write failing resume tests**

```python
# tests/test_pipeline.py — add
def test_resume_skips_completed_shots(tmp_path, example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    runner = PipelineRunner(project, shots, binding, template, comfy=FakeComfy(), ffmpeg=FakeFfmpeg())
    manifest = runner.run(run_id="run-resume")
    assert manifest.status == "succeeded"

    # Resume should not re-submit any shots
    fake_comfy = FakeComfy()
    runner2 = PipelineRunner(project, shots, binding, template, comfy=fake_comfy, ffmpeg=FakeFfmpeg())
    resumed = runner2.resume(tmp_path / "runs" / "run-resume" / "manifest.json")
    assert resumed.status == "succeeded"
    assert len(fake_comfy.submitted) == 0  # no shots re-submitted


def test_resume_reruns_failed_shot(tmp_path, example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    runner = PipelineRunner(project, shots, binding, template, comfy=FakeComfy(), ffmpeg=FakeFfmpeg())
    manifest = runner.run(run_id="run-fail-resume")
    # Simulate the second shot failing by corrupting its clip
    shot_002_clip = tmp_path / "runs" / "run-fail-resume" / "shots" / "shot_002" / "clip.mp4"
    if shot_002_clip.exists():
        shot_002_clip.write_bytes(b"corrupted")

    fake_comfy = FakeComfy()
    runner2 = PipelineRunner(project, shots, binding, template, comfy=fake_comfy, ffmpeg=FakeFfmpeg())
    resumed = runner2.resume(tmp_path / "runs" / "run-fail-resume" / "manifest.json")
    # Only shot_002 (and possibly shot_003) should be re-run
    assert len(fake_comfy.submitted) >= 1
```

- [ ] **Step 2: Write failing re-extract test**

```python
# tests/test_manifest.py — add
def test_re_extract_missing_last_frame(tmp_path):
    from ai_video.manifest import RunManifest, ShotRecord, successful_shot_is_valid

    clip = tmp_path / "clip.mp4"
    frame = tmp_path / "last.png"
    clip.write_bytes(b"clip")
    frame.write_bytes(b"frame")
    record = ShotRecord.succeeded(
        shot_id="shot_001", seed=100, clip_path=clip,
        last_frame_path=frame, chain_input_hash=None,
        character_ref_hashes={},
    )
    assert successful_shot_is_valid(record) is True
    # Delete the last frame
    frame.unlink()
    assert successful_shot_is_valid(record) is False
    # The record should be flagged as needing re-extraction
    # This is tested through the pipeline resume path
```

- [ ] **Step 3: Run failing tests**

Run: `pytest tests/test_pipeline.py::test_resume_skips_completed_shots tests/test_pipeline.py::test_resume_reruns_failed_shot -v`
Expected: FAIL — resume is a stub

- [ ] **Step 4: Implement real resume in PipelineRunner**

Replace `PipelineRunner.resume()` with:

```python
def resume(self, manifest_path: Path) -> RunManifest:
    manifest = load_manifest(manifest_path)
    if manifest.status == "succeeded":
        # Validate all artifacts
        all_valid = all(successful_shot_is_valid(r) for r in manifest.shots)
        if all_valid:
            return manifest

    run_root = manifest_path.parent
    # Determine which shots need re-running
    characters = {character.id: character for character in self.project.characters}
    character_image_names = self._prepare_character_images()
    previous_frame: Path | None = None
    previous_frame_hash: str | None = None

    for index, shot in enumerate(self.shots):
        existing = None
        for record in manifest.shots:
            if record.shot_id == shot.id:
                existing = record
                break

        if existing and existing.status == "succeeded" and successful_shot_is_valid(existing):
            # Check last frame, re-extract if missing
            last_frame_path = Path(existing.last_frame_path) if existing.last_frame_path else None
            if last_frame_path and not last_frame_path.exists():
                clip_path = Path(existing.clip_path)
                if clip_path.exists():
                    self.ffmpeg.extract_last_frame(clip_path, last_frame_path)
                    existing.last_frame_hash = sha256_file(last_frame_path)
                    atomic_write_manifest(manifest_path, manifest)
            previous_frame = last_frame_path
            previous_frame_hash = existing.last_frame_hash
            continue

        # Need to re-run this shot
        record, previous_frame = self._run_shot(
            run_root=run_root,
            actual_run_id=manifest.run_id,
            shot=shot,
            shot_index=index,
            characters=characters,
            character_image_names=character_image_names,
            previous_frame=previous_frame,
            previous_frame_hash=previous_frame_hash,
        )
        # Update or append the record
        if existing:
            idx = manifest.shots.index(existing)
            manifest.shots[idx] = record
        else:
            manifest.shots.append(record)
        previous_frame_hash = record.last_frame_hash
        atomic_write_manifest(manifest_path, manifest)

    # Re-normalize and stitch
    normalized_paths = []
    for shot_record in manifest.shots:
        source = Path(shot_record.clip_path or "")
        target = run_root / "normalized" / f"{shot_record.shot_id}.mp4"
        self.ffmpeg.normalize_clip(
            source, target,
            width=self.project.defaults.width,
            height=self.project.defaults.height,
            fps=self.project.defaults.fps,
            encoder="libx264",
        )
        shot_record.normalized_clip_path = str(target)
        shot_record.normalized_clip_hash = sha256_file(target)
        normalized_paths.append(target)

    final_output = run_root / "final" / "final.mp4"
    self.ffmpeg.stitch_clips(normalized_paths, final_output)
    manifest.final_output = str(final_output)
    manifest.status = "succeeded"
    atomic_write_manifest(manifest_path, manifest)
    return manifest
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_pipeline.py -v`
Expected: All pipeline tests pass, including new resume tests.

- [ ] **Step 6: Run full test suite**

Run: `pytest -v`
Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/ai_video/pipeline.py src/ai_video/manifest.py tests/test_pipeline.py tests/test_manifest.py
git commit -m "feat: implement real manifest-driven resume with stale detection and re-extraction"
```

---

## Task 5: Add CLI Progress Output During ComfyUI Generations

**Files:**
- Modify: `src/ai_video/pipeline.py`
- Modify: `src/ai_video/cli.py`
- Modify: `tests/test_cli.py`

**Problem:** During 5-minute ComfyUI generations, the CLI prints nothing. Users don't know which shot is running or how many remain.

- [ ] **Step 1: Write failing test**

```python
# tests/test_cli.py — add
def test_run_prints_shot_progress(capsys, example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    # Simulate by checking that PipelineRunner calls a progress callback
    # We'll test via the CLI's capture of stdout
    from ai_video.pipeline import PipelineRunner

    class TrackingFakeComfy(FakeComfy):
        def submit_and_collect_clip(self, workflow, output_path):
            return super().submit_and_collect_clip(workflow, output_path)

    runner = PipelineRunner(
        project, shots, binding, template,
        comfy=TrackingFakeComfy(), ffmpeg=FakeFfmpeg(),
    )
    manifest = runner.run(run_id="run-progress")
    # The progress output is tested via pipeline's callback mechanism
```

- [ ] **Step 2: Add progress callback to PipelineRunner**

Add an optional `progress_callback` parameter to `PipelineRunner.__init__`:

```python
def __init__(
    self,
    project: ProjectConfig,
    shots: Sequence[ShotSpec],
    binding: WorkflowBinding,
    template: dict[str, Any],
    *,
    comfy: Any | None = None,
    ffmpeg: Any | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> None:
    # ... existing code ...
    self.progress = progress_callback or (lambda msg: None)
```

Then in `_run_shot()`, call `self.progress()`:

```python
self.progress(f"Shot {shot.id} ({shot_index + 1}/{len(self.shots)}): starting attempt {attempt}")
```

And in `_submit_and_collect_clip()`:

```python
self.progress(f"Shot {shot.id}: submitting to ComfyUI...")
# ... after poll ...
self.progress(f"Shot {shot.id}: generation complete, collecting output")
```

And in the main `run()` method:

```python
self.progress(f"Starting run {actual_run_id} with {len(self.shots)} shots")
# ... after stitch ...
self.progress(f"Final video: {final_output}")
```

- [ ] **Step 3: Wire progress callback in CLI**

In `cli.py`, create a simple print-based callback:

```python
def _cmd_run(args: argparse.Namespace) -> int:
    project, shots, binding, template = _load_binding_and_template(args.project, args.shots)
    runner = PipelineRunner(project, shots, binding, template, progress_callback=print)
    manifest = runner.run(run_id=args.run_id, project_config_path=Path(args.project), shot_list_path=Path(args.shots))
    print(f"Run succeeded: {manifest.final_output}")
    return 0
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_pipeline.py tests/test_cli.py -v`
Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/ai_video/pipeline.py src/ai_video/cli.py tests/test_pipeline.py tests/test_cli.py
git commit -m "feat: add progress callback for shot-by-shot CLI feedback"
```

---

## Task 6: Add Stitching Re-Encode Fallback

**Files:**
- Modify: `src/ai_video/ffmpeg_tools.py:142-165`
- Modify: `tests/test_ffmpeg_tools.py`

**Problem:** `stitch_clips()` always uses `-c copy` (stream copy). If normalized clips have mismatched encoding parameters (different codec profiles, extradata, etc.), the output is broken. The spec says: "If all normalized clips share identical parameters, final concat can use stream copy. If not, do a final re-encode pass."

- [ ] **Step 1: Write failing test**

```python
# tests/test_ffmpeg_tools.py — add
@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not available")
def test_stitch_clips_re_encodes_on_copy_failure(tmp_path):
    # Create two clips with different parameters
    clip_a = tmp_path / "a.mp4"
    clip_b = tmp_path / "b.mp4"
    output = tmp_path / "final.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=1:size=64x64:rate=4",
         "-pix_fmt", "yuv420p", "-c:v", "libx264", str(clip_a)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=1:size=128x128:rate=8",
         "-pix_fmt", "yuv420p", "-c:v", "libx264", str(clip_b)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    # This should succeed even with mismatched clips, by falling back to re-encode
    stitch_clips([clip_a, clip_b], output)
    assert output.exists()
    assert output.stat().st_size > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ffmpeg_tools.py::test_stitch_clips_re_encodes_on_copy_failure -v`
Expected: FAIL — stream copy on mismatched clips produces a broken file or ffmpeg error

- [ ] **Step 3: Implement re-encode fallback in stitch_clips**

```python
# src/ai_video/ffmpeg_tools.py — replace stitch_clips
def stitch_clips(normalized_clips: Sequence[str | Path], output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
        handle.write(concat_list_text(normalized_clips))
        list_path = Path(handle.name)
    try:
        # Try stream copy first (fast)
        run_command(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", str(list_path), "-c", "copy", str(output)],
        )
    except AiVideoError:
        # Fallback: re-encode
        if output.exists():
            output.unlink()
        run_command(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", str(list_path), "-c:v", "libx264",
             "-pix_fmt", "yuv420p", "-an", str(output)],
        )
    finally:
        list_path.unlink(missing_ok=True)
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_ffmpeg_tools.py -v`
Expected: All ffmpeg tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/ai_video/ffmpeg_tools.py tests/test_ffmpeg_tools.py
git commit -m "fix: add re-encode fallback when stream copy fails in stitch_clips"
```

---

## Task 7: Wire Resume CLI Command

**Files:**
- Modify: `src/ai_video/cli.py:53-56`
- Modify: `tests/test_cli.py`

**Problem:** `_cmd_resume` is a stub that just prints a message. It should load the manifest, re-construct the PipelineRunner from the manifest's config paths, and call `resume()`.

- [ ] **Step 1: Write failing test**

```python
# tests/test_cli.py — add
def test_resume_command_reconstructs_and_resumes(example_project_files, tmp_path, capsys):
    project_path, shots_path = example_project_files
    from ai_video.config import load_project, load_shots, load_yaml
    from ai_video.models import WorkflowBinding
    from ai_video.pipeline import PipelineRunner
    from ai_video.workflow_loader import load_workflow_template

    project = load_project(project_path)
    shots = load_shots(shots_path, project)
    binding = WorkflowBinding.model_validate(load_yaml(project.workflow.binding))
    template = load_workflow_template(project.workflow.template)

    runner = PipelineRunner(project, shots, binding, template, comfy=FakeComfy(), ffmpeg=FakeFfmpeg())
    manifest = runner.run(
        run_id="run-resume-cli",
        project_config_path=project_path,
        shot_list_path=shots_path,
    )
    manifest_path = tmp_path / "runs" / "run-resume-cli" / "manifest.json"
    assert manifest_path.exists()

    # Now test the resume CLI command
    code = main(["resume", "--manifest", str(manifest_path)])
    assert code == 0
```

- [ ] **Step 2: Implement resume CLI command**

```python
# src/ai_video/cli.py — replace _cmd_resume
def _cmd_resume(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    from ai_video.manifest import load_manifest
    manifest = load_manifest(manifest_path)

    # Reconstruct project and shots from manifest paths
    if not manifest.project_config_path or not manifest.shot_list_path:
        print("Cannot resume: manifest does not contain project config path.", file=sys.stderr)
        return 1

    project, shots, binding, template = _load_binding_and_template(
        manifest.project_config_path, manifest.shot_list_path
    )
    runner = PipelineRunner(
        project, shots, binding, template,
        progress_callback=print,
    )
    result = runner.resume(manifest_path)
    print(f"Resume completed: {result.final_output}")
    return 0
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_cli.py -v`
Expected: All CLI tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/ai_video/cli.py tests/test_cli.py
git commit -m "feat: wire resume CLI to load manifest and reconstruct pipeline"
```

---

## Task 8: End-to-End Validation With Real Run Manifest

**Files:**
- Modify: `src/ai_video/pipeline.py` — ensure manifest_path is stored on PipelineRunner for resume
- Add: `tests/test_resume_e2e.py` — full mocked resume flow

**Problem:** Need a full integration test that proves: create a run, simulate a crash after 2 shots, resume, and verify shot_003 is re-run while shot_001 and shot_002 are skipped.

- [ ] **Step 1: Write the end-to-end resume test**

```python
# tests/test_resume_e2e.py
from pathlib import Path
from ai_video.config import load_project, load_shots, load_yaml
from ai_video.manifest import load_manifest
from ai_video.models import WorkflowBinding
from ai_video.pipeline import PipelineRunner
from ai_video.workflow_loader import load_workflow_template


class FakeComfy:
    def __init__(self):
        self.submitted = []

    def prepare_image(self, path: Path) -> str:
        return Path(path).name if path else "none"

    def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
        self.submitted.append(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"clip")
        return "prompt-id"


class FakeFfmpeg:
    def validate_clip(self, path: Path) -> None:
        pass

    def extract_last_frame(self, clip: Path, frame: Path) -> None:
        frame.parent.mkdir(parents=True, exist_ok=True)
        frame.write_bytes(b"frame")

    def normalize_clip(self, source: Path, target: Path, **kwargs) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())

    def stitch_clips(self, clips, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"final")


def test_resume_after_partial_run(tmp_path):
    """Simulate: run 3 shots, crash after 2, resume should only run shot_003."""
    # Set up project
    refs = tmp_path / "refs"
    refs.mkdir()
    (refs / "hero.png").write_bytes(b"png")
    wf = tmp_path / "wf"
    wf.mkdir()
    (wf / "template.json").write_text(
        '{"3":{"class_type":"KSampler","inputs":{"seed":1}},'
        '"6":{"class_type":"CLIPTextEncode","inputs":{"text":""}},'
        '"7":{"class_type":"CLIPTextEncode","inputs":{"text":""}},'
        '"12":{"class_type":"LoadImage","inputs":{"image":""}},'
        '"42":{"class_type":"VHS_VideoCombine","inputs":{"filename_prefix":""}}}',
        encoding="utf-8",
    )
    (wf / "binding.yaml").write_text(
        "positive_prompt:\n  path: ['6', inputs, text]\n"
        "negative_prompt:\n  path: ['7', inputs, text]\n"
        "seed:\n  path: ['3', inputs, seed]\n"
        "init_image:\n  path: ['12', inputs, image]\n"
        "output_prefix:\n  path: ['42', inputs, filename_prefix]\n"
        "character_refs: []\n"
        "clip_output:\n  node: '42'\n  kind: gifs\n  extensions: ['.mp4']\n  select: first\n",
        encoding="utf-8",
    )
    project_yaml = tmp_path / "project.yaml"
    project_yaml.write_text(
        "project_name: resume-test\ncomfy:\n  base_url: http://127.0.0.1:8188\n"
        "workflow:\n  template: wf/template.json\n  binding: wf/binding.yaml\n"
        "output:\n  root: runs\n  min_free_gb: 0\n"
        "defaults:\n  seed: 100\n  fps: 16\n  width: 512\n  height: 512\n",
        encoding="utf-8",
    )
    shots_yaml = tmp_path / "shots.yaml"
    shots_yaml.write_text(
        "shots:\n  - id: shot_001\n    prompt: first\n"
        "  - id: shot_002\n    prompt: second\n"
        "  - id: shot_003\n    prompt: third\n",
        encoding="utf-8",
    )

    project = load_project(project_yaml)
    shots = load_shots(shots_yaml, project)
    binding = WorkflowBinding.model_validate(load_yaml(project.workflow.binding))
    template = load_workflow_template(project.workflow.template)

    # Run all 3 shots
    fake_comfy = FakeComfy()
    runner = PipelineRunner(
        project, shots, binding, template,
        comfy=fake_comfy, ffmpeg=FakeFfmpeg(),
    )
    manifest = runner.run(
        run_id="run-partial",
        project_config_path=project_yaml,
        shot_list_path=shots_yaml,
    )
    assert manifest.status == "succeeded"
    assert len(fake_comfy.submitted) == 3

    # Simulate crash: corrupt shot_003's clip
    shot_003_clip = tmp_path / "runs" / "run-partial" / "shots" / "shot_003" / "clip.mp4"
    if shot_003_clip.exists():
        shot_003_clip.write_bytes(b"corrupted")

    # Resume: only shot_003 should be re-run
    resume_comfy = FakeComfy()
    runner2 = PipelineRunner(
        project, shots, binding, template,
        comfy=resume_comfy, ffmpeg=FakeFfmpeg(),
    )
    resumed = runner2.resume(tmp_path / "runs" / "run-partial" / "manifest.json")
    assert resumed.status == "succeeded"
    # shot_001 and shot_002 skipped, only shot_003 re-run
    assert len(resume_comfy.submitted) == 1
```

- [ ] **Step 2: Run the test**

Run: `pytest tests/test_resume_e2e.py -v`
Expected: PASS (if resume is correctly implemented from Task 4) or FAIL (if resume needs more wiring)

- [ ] **Step 3: Fix any issues found**

- [ ] **Step 4: Run full test suite**

Run: `pytest -v`
Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_resume_e2e.py
git commit -m "test: add end-to-end resume integration test"
```

---

## Task 9: Fix conftest.py Template Loading Consistency

**Files:**
- Modify: `tests/conftest.py:71`

**Problem:** The `example_project_and_shots` fixture uses `yaml.safe_load(project.workflow.template.read_text(...))` to load the workflow template. This bypasses `load_workflow_template()` which handles UI-to-API conversion and validation. Tests should use the same code path as production.

- [ ] **Step 1: Fix the fixture**

```python
# tests/conftest.py — replace line 71
from ai_video.workflow_loader import load_workflow_template

@pytest.fixture
def example_project_and_shots(example_project_files):
    project_path, shots_path = example_project_files
    project = load_project(project_path)
    shots = load_shots(shots_path, project)
    binding = WorkflowBinding.model_validate(load_yaml(project.workflow.binding))
    template = load_workflow_template(project.workflow.template)
    return project, shots, binding, template
```

- [ ] **Step 2: Run full test suite**

Run: `pytest -v`
Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "fix: use load_workflow_template in conftest fixture for consistency"
```

---

## Task 10: Run A Real End-to-End Test And Verify Artifacts

**Files:**
- No code changes; manual verification

**Problem:** After all the fixes, we need to verify the real pipeline works with an actual local ComfyUI.

- [ ] **Step 1: Run a quick 1-shot test with the real pipeline**

```bash
cd /home/reggie/vscode_folder/AI-VIDEO
ai-video validate --project configs/wan22.project.yaml --shots configs/wan22_quick.shots.yaml
```

Expected: "Project is valid."

- [ ] **Step 2: Run a 1-shot generation**

```bash
ai-video run --project configs/wan22.project.yaml --shots configs/wan22_quick.shots.yaml --run-id quick-verify
```

Expected: Progress output during generation, final video at `runs/quick-verify/final/final.mp4`.

- [ ] **Step 3: Verify manifest is complete**

```bash
cat runs/quick-verify/manifest.json | python -m json.tool
```

Expected: `final_output` is populated, `project_config_hash`, `workflow_template_hash`, `workflow_binding_hash` are all non-null, `started_at` is set, `attempts` has records.

- [ ] **Step 4: Verify path cleanliness**

Check that artifact paths in the manifest are absolute and contain no `../` segments.

- [ ] **Step 5: Test resume by re-running the same manifest**

```bash
ai-video resume --manifest runs/quick-verify/manifest.json
```

Expected: "Resume completed", no new shots generated (since all are valid).

---

## Completion Criteria

- [x] All `pytest` tests pass
- [ ] Manifest `final_output` is populated after stitching
- [ ] Config/template/binding hashes are populated in manifest
- [ ] Shot `started_at` and `attempts` are populated
- [ ] All artifact paths are clean absolute paths with no `../`
- [ ] `resume` skips completed shots, re-runs failed/stale ones
- [ ] `resume` re-extracts missing last frames
- [ ] CLI prints progress during ComfyUI generations
- [ ] `stitch_clips` falls back to re-encode when stream copy fails
- [ ] `resume` CLI command works end-to-end
- [ ] A real ComfyUI run produces a complete manifest and valid final.mp4
