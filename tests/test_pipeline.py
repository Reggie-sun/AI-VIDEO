from pathlib import Path

import pytest

import ai_video.pipeline as pipeline_module
from ai_video.config import sha256_file
from ai_video.errors import AiVideoError, ErrorCode, retryable_error
from ai_video.manifest import atomic_write_manifest, load_manifest
from ai_video.models import JsonPathBinding
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
    def __init__(self):
        self.normalize_calls = []

    def extract_last_frame(self, clip: Path, frame: Path) -> None:
        frame.parent.mkdir(parents=True, exist_ok=True)
        frame.write_bytes(frame.name.encode())

    def normalize_clip(self, source: Path, target: Path, **kwargs) -> None:
        self.normalize_calls.append((source, target, kwargs))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())

    def stitch_clips(self, clips, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"final")


def _promotion_case(tmp_path: Path, *, existing: bool = True) -> dict[str, Path]:
    shot_dir = tmp_path / "shot_001"
    shot_dir.mkdir()
    paths = {
        "staged_clip": shot_dir / ".attempt_2.clip.mp4",
        "staged_frame": shot_dir / ".attempt_2.last_frame.png",
        "clip": shot_dir / "clip.mp4",
        "frame": shot_dir / "last_frame.png",
        "clip_backup": shot_dir / ".attempt_2.clip.mp4.backup",
        "frame_backup": shot_dir / ".attempt_2.last_frame.png.backup",
    }
    paths["staged_clip"].write_bytes(b"new-clip")
    paths["staged_frame"].write_bytes(b"new-frame")
    if existing:
        paths["clip"].write_bytes(b"old-clip")
        paths["frame"].write_bytes(b"old-frame")
    return paths


def _promotion_runner(progress: list[str] | None = None) -> PipelineRunner:
    runner = object.__new__(PipelineRunner)
    runner.progress = (progress if progress is not None else []).append
    return runner


def test_three_shot_chain_passes_last_frames(example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    runner = PipelineRunner(project, shots, binding, template, comfy=FakeComfy(), ffmpeg=FakeFfmpeg())
    manifest = runner.run(run_id="run-test")
    assert manifest.status == "succeeded"
    assert len(manifest.shots) == 3
    assert manifest.final_output is not None


def test_manifest_populates_final_output_and_config_hashes(example_project_and_shots, example_project_files):
    project, shots, binding, template = example_project_and_shots
    project_path, shots_path = example_project_files
    runner = PipelineRunner(project, shots, binding, template, comfy=FakeComfy(), ffmpeg=FakeFfmpeg())
    manifest = runner.run(
        run_id="run-hash-test",
        project_config_path=project_path,
        shot_list_path=shots_path,
    )
    # Verify in-memory manifest
    assert manifest.status == "succeeded"
    assert manifest.final_output is not None
    assert manifest.final_output.endswith("final.mp4")
    assert manifest.project_config_hash is not None
    assert manifest.workflow_template_hash is not None
    assert manifest.workflow_binding_hash is not None
    assert manifest.project_config_path == str(project_path)
    assert manifest.shot_list_path == str(shots_path)
    # Verify manifest persisted on disk
    manifest_path = project.output.root / "run-hash-test" / "manifest.json"
    disk_manifest = load_manifest(manifest_path)
    assert disk_manifest.final_output is not None
    assert disk_manifest.final_output.endswith("final.mp4")
    assert disk_manifest.project_config_hash == manifest.project_config_hash
    assert disk_manifest.workflow_template_hash == manifest.workflow_template_hash
    assert disk_manifest.workflow_binding_hash == manifest.workflow_binding_hash
    assert disk_manifest.project_config_path == str(project_path)
    assert disk_manifest.shot_list_path == str(shots_path)


def test_shot_fps_overrides_generation_but_not_delivery_normalization(
    example_project_and_shots,
):
    project, shots, binding, template = example_project_and_shots
    project.defaults.fps = 16
    shots[0].fps = 20
    template["45"] = {"class_type": "VHS_VideoCombine", "inputs": {"frame_rate": 0}}
    binding.frame_rate = JsonPathBinding(path=["45", "inputs", "frame_rate"])

    initial_comfy = FakeComfy()
    initial_ffmpeg = FakeFfmpeg()
    runner = PipelineRunner(
        project,
        shots[:1],
        binding,
        template,
        comfy=initial_comfy,
        ffmpeg=initial_ffmpeg,
    )
    manifest = runner.run(run_id="run-shot-fps")
    manifest_path = project.output.root / "run-shot-fps" / "manifest.json"
    expected_clip = project.output.root / "run-shot-fps" / "shots" / "shot_001" / "clip.mp4"
    expected_normalized = project.output.root / "run-shot-fps" / "normalized" / "shot_001.mp4"
    persisted_after_run = load_manifest(manifest_path)

    assert initial_comfy.submitted[0]["45"]["inputs"]["frame_rate"] == 20
    assert [
        (source, target, kwargs["fps"])
        for source, target, kwargs in initial_ffmpeg.normalize_calls
    ] == [(expected_clip, expected_normalized, 16)]
    assert persisted_after_run.shots[0].normalized_clip_path == str(expected_normalized)
    assert persisted_after_run.shots[0].normalized_clip_hash == sha256_file(expected_normalized)

    Path(manifest.shots[0].clip_path).write_bytes(b"corrupted")
    resumed_comfy = FakeComfy()
    resumed_ffmpeg = FakeFfmpeg()
    resumed = PipelineRunner(
        project,
        shots[:1],
        binding,
        template,
        comfy=resumed_comfy,
        ffmpeg=resumed_ffmpeg,
    )
    resumed.resume(manifest_path)
    persisted_after_resume = load_manifest(manifest_path)

    assert resumed_comfy.submitted[0]["45"]["inputs"]["frame_rate"] == 20
    assert [
        (source, target, kwargs["fps"])
        for source, target, kwargs in resumed_ffmpeg.normalize_calls
    ] == [(expected_clip, expected_normalized, 16)]
    assert persisted_after_resume.shots[0].normalized_clip_path == str(expected_normalized)
    assert persisted_after_resume.shots[0].normalized_clip_hash == sha256_file(expected_normalized)


def test_retry_reuses_shot_after_retryable_failure(example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    project.defaults.max_attempts = 2

    class FlakyComfy(FakeComfy):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
            self.calls += 1
            if self.calls == 1:
                raise retryable_error(ErrorCode.COMFY_JOB_FAILED, "temporary failure")
            return super().submit_and_collect_clip(workflow, output_path)

    comfy = FlakyComfy()
    runner = PipelineRunner(project, shots[:1], binding, template, comfy=comfy, ffmpeg=FakeFfmpeg())
    manifest = runner.run(run_id="run-retry")
    assert manifest.status == "succeeded"
    assert comfy.calls == 2
    assert manifest.shots[0].active_attempt == 2


def test_shot_records_populate_started_at_and_attempts(example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    runner = PipelineRunner(project, shots, binding, template, comfy=FakeComfy(), ffmpeg=FakeFfmpeg())
    manifest = runner.run(run_id="run-attempts")
    for shot_record in manifest.shots:
        assert shot_record.started_at is not None
        assert len(shot_record.attempts) == 1
        assert shot_record.attempts[0].attempt == 1
        assert shot_record.attempts[0].status == "succeeded"
        assert shot_record.attempts[0].comfy_prompt_id == "prompt-id"


def test_shot_records_track_failed_attempts(example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    project.defaults.max_attempts = 3

    class TwoFailComfy(FakeComfy):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
            self.calls += 1
            if self.calls <= 2:
                raise retryable_error(ErrorCode.COMFY_JOB_FAILED, "temporary failure")
            return super().submit_and_collect_clip(workflow, output_path)

    comfy = TwoFailComfy()
    runner = PipelineRunner(project, shots[:1], binding, template, comfy=comfy, ffmpeg=FakeFfmpeg())
    manifest = runner.run(run_id="run-failed-attempts")
    assert manifest.status == "succeeded"
    record = manifest.shots[0]
    assert record.started_at is not None
    assert len(record.attempts) == 3
    assert record.attempts[0].status == "failed"
    assert record.attempts[1].status == "failed"
    assert record.attempts[2].status == "succeeded"


def test_terminal_failure_persists_all_attempts_before_run_raises(example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    project.defaults.max_attempts = 2

    class AlwaysFailComfy(FakeComfy):
        def __init__(self):
            super().__init__()
            self.errors = []

        def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
            error = retryable_error(ErrorCode.COMFY_JOB_FAILED, "temporary failure")
            self.errors.append(error)
            raise error

    comfy = AlwaysFailComfy()
    runner = PipelineRunner(
        project,
        shots[:1],
        binding,
        template,
        comfy=comfy,
        ffmpeg=FakeFfmpeg(),
    )
    manifest_path = project.output.root / "run-terminal-failure" / "manifest.json"

    with pytest.raises(AiVideoError) as exc_info:
        runner.run(run_id="run-terminal-failure")

    assert exc_info.value is comfy.errors[-1]
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


def test_resume_extract_failure_preserves_canonical_artifact_bytes(
    example_project_and_shots,
):
    project, shots, binding, template = example_project_and_shots
    initial = PipelineRunner(
        project,
        shots[:2],
        binding,
        template,
        comfy=FakeComfy(),
        ffmpeg=FakeFfmpeg(),
    )
    initial.run(run_id="run-resume-artifact-preservation")
    manifest_path = project.output.root / "run-resume-artifact-preservation" / "manifest.json"
    before_manifest = load_manifest(manifest_path)
    before = before_manifest.shots[1].model_copy(deep=True)
    clip_path = Path(before.clip_path)
    frame_path = Path(before.last_frame_path)
    old_clip_bytes = clip_path.read_bytes()
    old_frame_bytes = frame_path.read_bytes()
    before_manifest.shots[1].chain_input_hash = "force-dependency-rerun"
    atomic_write_manifest(manifest_path, before_manifest)

    class ReplacementComfy(FakeComfy):
        def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"replacement-clip")
            return "replacement-prompt-id"

    extract_error = RuntimeError("replacement frame extraction failed")

    class FailingExtractFfmpeg(FakeFfmpeg):
        def extract_last_frame(self, clip: Path, frame: Path) -> None:
            frame.parent.mkdir(parents=True, exist_ok=True)
            frame.write_bytes(b"replacement-frame")
            raise extract_error

    runner = PipelineRunner(
        project,
        shots[:2],
        binding,
        template,
        comfy=ReplacementComfy(),
        ffmpeg=FailingExtractFfmpeg(),
    )

    with pytest.raises(RuntimeError) as exc_info:
        runner.resume(manifest_path)

    assert exc_info.value is extract_error
    persisted = load_manifest(manifest_path)
    failed = persisted.shots[1]
    assert persisted.status == "failed"
    assert failed.status == "failed"
    assert [item.status for item in failed.attempts] == ["succeeded", "failed"]
    assert failed.active_attempt == 2
    assert failed.clip_path == before.clip_path
    assert failed.clip_hash == before.clip_hash
    assert failed.last_frame_path == before.last_frame_path
    assert failed.last_frame_hash == before.last_frame_hash
    assert clip_path.read_bytes() == old_clip_bytes
    assert frame_path.read_bytes() == old_frame_bytes
    assert sha256_file(clip_path) == failed.clip_hash
    assert sha256_file(frame_path) == failed.last_frame_hash
    attempt_dir = manifest_path.parent / "shots" / "shot_002" / "attempt_2"
    shot_dir = attempt_dir.parent
    assert (attempt_dir / "workflow.json").exists()
    assert not (shot_dir / ".attempt_2.clip.mp4").exists()
    assert not (shot_dir / ".attempt_2.last_frame.png").exists()


def test_resume_promotion_failure_restores_both_canonical_artifacts(
    example_project_and_shots,
    monkeypatch,
):
    project, shots, binding, template = example_project_and_shots
    initial = PipelineRunner(
        project,
        shots[:2],
        binding,
        template,
        comfy=FakeComfy(),
        ffmpeg=FakeFfmpeg(),
    )
    initial.run(run_id="run-resume-promotion-rollback")
    manifest_path = project.output.root / "run-resume-promotion-rollback" / "manifest.json"
    before_manifest = load_manifest(manifest_path)
    before = before_manifest.shots[1].model_copy(deep=True)
    clip_path = Path(before.clip_path)
    frame_path = Path(before.last_frame_path)
    old_clip_bytes = clip_path.read_bytes()
    old_frame_bytes = frame_path.read_bytes()
    before_manifest.shots[1].chain_input_hash = "force-dependency-rerun"
    atomic_write_manifest(manifest_path, before_manifest)

    class ReplacementComfy(FakeComfy):
        def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"replacement-clip")
            return "replacement-prompt-id"

    shot_dir = manifest_path.parent / "shots" / "shot_002"
    staged_clip = shot_dir / ".attempt_2.clip.mp4"
    staged_frame = shot_dir / ".attempt_2.last_frame.png"
    promotion_error = OSError("frame promotion failed")
    original_replace = Path.replace

    def fail_staged_frame_promotion(source: Path, target: Path) -> Path:
        if source == staged_frame and Path(target) == frame_path:
            raise promotion_error
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_staged_frame_promotion)
    runner = PipelineRunner(
        project,
        shots[:2],
        binding,
        template,
        comfy=ReplacementComfy(),
        ffmpeg=FakeFfmpeg(),
    )

    with pytest.raises(OSError) as exc_info:
        runner.resume(manifest_path)

    assert exc_info.value is promotion_error
    persisted = load_manifest(manifest_path)
    failed = persisted.shots[1]
    assert persisted.status == "failed"
    assert failed.status == "failed"
    assert [item.status for item in failed.attempts] == ["succeeded", "failed"]
    assert failed.active_attempt == 2
    assert clip_path.read_bytes() == old_clip_bytes
    assert frame_path.read_bytes() == old_frame_bytes
    assert sha256_file(clip_path) == failed.clip_hash == before.clip_hash
    assert sha256_file(frame_path) == failed.last_frame_hash == before.last_frame_hash
    assert not staged_clip.exists()
    assert not staged_frame.exists()
    assert not (shot_dir / ".attempt_2.clip.mp4.backup").exists()
    assert not (shot_dir / ".attempt_2.last_frame.png.backup").exists()


@pytest.mark.parametrize(
    ("failed_artifact", "exception_type"),
    [
        pytest.param("clip", OSError, id="first-promotion"),
        pytest.param("frame", OSError, id="second-promotion"),
        pytest.param("frame", KeyboardInterrupt, id="keyboard-interrupt"),
    ],
)
def test_promotion_failure_rolls_back_existing_canonical_artifacts(
    tmp_path,
    monkeypatch,
    failed_artifact,
    exception_type,
):
    paths = _promotion_case(tmp_path)
    promotion_error = exception_type(f"{failed_artifact} promotion failed")
    failed_source = paths["staged_clip" if failed_artifact == "clip" else "staged_frame"]
    original_replace = Path.replace

    def fail_selected_promotion(source: Path, target: Path) -> Path:
        if source == failed_source:
            raise promotion_error
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_selected_promotion)

    with pytest.raises(exception_type) as exc_info:
        _promotion_runner()._promote_shot_artifacts(
            staged_clip_path=paths["staged_clip"],
            staged_last_frame_path=paths["staged_frame"],
            clip_path=paths["clip"],
            last_frame_path=paths["frame"],
        )

    assert exc_info.value is promotion_error
    assert paths["clip"].read_bytes() == b"old-clip"
    assert paths["frame"].read_bytes() == b"old-frame"
    assert not paths["staged_clip"].exists()
    assert not paths["staged_frame"].exists()
    assert not paths["clip_backup"].exists()
    assert not paths["frame_backup"].exists()


def test_second_promotion_failure_removes_partial_canonical_without_prior_files(
    tmp_path,
    monkeypatch,
):
    paths = _promotion_case(tmp_path, existing=False)
    promotion_error = OSError("frame promotion failed")
    original_replace = Path.replace

    def fail_frame_promotion(source: Path, target: Path) -> Path:
        if source == paths["staged_frame"]:
            raise promotion_error
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_frame_promotion)

    with pytest.raises(OSError) as exc_info:
        _promotion_runner()._promote_shot_artifacts(
            staged_clip_path=paths["staged_clip"],
            staged_last_frame_path=paths["staged_frame"],
            clip_path=paths["clip"],
            last_frame_path=paths["frame"],
        )

    assert exc_info.value is promotion_error
    assert not paths["clip"].exists()
    assert not paths["frame"].exists()
    assert not paths["staged_clip"].exists()
    assert not paths["staged_frame"].exists()


@pytest.mark.parametrize("recovery_backup", ["clip_backup", "frame_backup"])
def test_preexisting_recovery_backup_is_never_owned_or_deleted(
    tmp_path,
    recovery_backup,
):
    paths = _promotion_case(tmp_path)
    paths[recovery_backup].write_bytes(b"recovery-evidence")
    other_backup = "frame_backup" if recovery_backup == "clip_backup" else "clip_backup"

    with pytest.raises(FileExistsError):
        _promotion_runner()._promote_shot_artifacts(
            staged_clip_path=paths["staged_clip"],
            staged_last_frame_path=paths["staged_frame"],
            clip_path=paths["clip"],
            last_frame_path=paths["frame"],
        )

    assert paths[recovery_backup].read_bytes() == b"recovery-evidence"
    assert not paths[other_backup].exists()
    assert paths["clip"].read_bytes() == b"old-clip"
    assert paths["frame"].read_bytes() == b"old-frame"


def test_hardlink_file_exists_race_preserves_recovery_backup(tmp_path, monkeypatch):
    paths = _promotion_case(tmp_path)
    race_error = FileExistsError("concurrent recovery backup")

    def race_creates_backup(source, target):
        Path(target).write_bytes(b"concurrent-recovery")
        raise race_error

    def forbid_copy(source, target):
        raise AssertionError("copy fallback must not overwrite a raced backup")

    monkeypatch.setattr(pipeline_module.os, "link", race_creates_backup)
    monkeypatch.setattr(pipeline_module.shutil, "copy2", forbid_copy)

    with pytest.raises(FileExistsError) as exc_info:
        _promotion_runner()._promote_shot_artifacts(
            staged_clip_path=paths["staged_clip"],
            staged_last_frame_path=paths["staged_frame"],
            clip_path=paths["clip"],
            last_frame_path=paths["frame"],
        )

    assert exc_info.value is race_error
    assert paths["clip_backup"].read_bytes() == b"concurrent-recovery"
    assert not paths["frame_backup"].exists()
    assert paths["clip"].read_bytes() == b"old-clip"
    assert paths["frame"].read_bytes() == b"old-frame"


def test_promotion_uses_copy_fallback_when_hardlink_backup_fails(tmp_path, monkeypatch):
    paths = _promotion_case(tmp_path)
    copy_calls = []
    original_copyfileobj = pipeline_module.shutil.copyfileobj

    def fail_hardlink(source, target):
        raise OSError("hardlink unavailable")

    def record_copy(source, target, *args, **kwargs):
        copy_calls.append((Path(source.name), Path(target.name)))
        return original_copyfileobj(source, target, *args, **kwargs)

    def forbid_copy2(source, target):
        raise AssertionError("backup fallback must use exclusive streamed copy")

    monkeypatch.setattr(pipeline_module.os, "link", fail_hardlink)
    monkeypatch.setattr(pipeline_module.shutil, "copyfileobj", record_copy)
    monkeypatch.setattr(pipeline_module.shutil, "copy2", forbid_copy2)
    transaction = _promotion_runner()._promote_shot_artifacts(
        staged_clip_path=paths["staged_clip"],
        staged_last_frame_path=paths["staged_frame"],
        clip_path=paths["clip"],
        last_frame_path=paths["frame"],
    )

    transaction.commit()
    assert copy_calls == [
        (paths["clip"], paths["clip_backup"]),
        (paths["frame"], paths["frame_backup"]),
    ]
    assert paths["clip"].read_bytes() == b"new-clip"
    assert paths["frame"].read_bytes() == b"new-frame"
    assert not paths["clip_backup"].exists()
    assert not paths["frame_backup"].exists()


def test_backup_creation_failure_leaves_canonical_untouched(tmp_path, monkeypatch):
    paths = _promotion_case(tmp_path)
    backup_error = OSError("backup creation failed")

    def fail_hardlink(source, target):
        raise OSError("hardlink unavailable")

    def fail_copy(source, target, *args, **kwargs):
        target.write(b"partial-backup")
        raise backup_error

    def forbid_copy2(source, target):
        raise AssertionError("backup fallback must use exclusive streamed copy")

    monkeypatch.setattr(pipeline_module.os, "link", fail_hardlink)
    monkeypatch.setattr(pipeline_module.shutil, "copyfileobj", fail_copy)
    monkeypatch.setattr(pipeline_module.shutil, "copy2", forbid_copy2)

    with pytest.raises(OSError) as exc_info:
        _promotion_runner()._promote_shot_artifacts(
            staged_clip_path=paths["staged_clip"],
            staged_last_frame_path=paths["staged_frame"],
            clip_path=paths["clip"],
            last_frame_path=paths["frame"],
        )

    assert exc_info.value is backup_error
    assert paths["clip"].read_bytes() == b"old-clip"
    assert paths["frame"].read_bytes() == b"old-frame"
    assert not paths["staged_clip"].exists()
    assert not paths["staged_frame"].exists()
    assert not paths["clip_backup"].exists()


def test_rollback_replace_failure_uses_copy_fallback(tmp_path, monkeypatch):
    paths = _promotion_case(tmp_path)
    promotion_error = OSError("frame promotion failed")
    original_replace = Path.replace
    original_copy2 = pipeline_module.shutil.copy2
    rollback_copies = []

    def fail_promotion_and_backup_replace(source: Path, target: Path) -> Path:
        if source == paths["staged_frame"]:
            raise promotion_error
        if source == paths["clip_backup"]:
            raise OSError("backup replace failed")
        return original_replace(source, target)

    def record_rollback_copy(source, target):
        rollback_copies.append((Path(source), Path(target)))
        return original_copy2(source, target)

    monkeypatch.setattr(Path, "replace", fail_promotion_and_backup_replace)
    monkeypatch.setattr(pipeline_module.shutil, "copy2", record_rollback_copy)

    with pytest.raises(OSError) as exc_info:
        _promotion_runner()._promote_shot_artifacts(
            staged_clip_path=paths["staged_clip"],
            staged_last_frame_path=paths["staged_frame"],
            clip_path=paths["clip"],
            last_frame_path=paths["frame"],
        )

    assert exc_info.value is promotion_error
    assert rollback_copies == [(paths["clip_backup"], paths["clip"])]
    assert paths["clip"].read_bytes() == b"old-clip"
    assert paths["frame"].read_bytes() == b"old-frame"
    assert not paths["clip_backup"].exists()


def test_failed_rollback_preserves_backup_and_adds_exception_note(tmp_path, monkeypatch):
    paths = _promotion_case(tmp_path)
    promotion_error = OSError("frame promotion failed")
    original_replace = Path.replace

    def fail_promotion_and_backup_replace(source: Path, target: Path) -> Path:
        if source == paths["staged_frame"]:
            raise promotion_error
        if source == paths["clip_backup"]:
            raise OSError("backup replace failed")
        return original_replace(source, target)

    def fail_restore_copy(source, target):
        raise OSError("backup copy failed")

    monkeypatch.setattr(Path, "replace", fail_promotion_and_backup_replace)
    monkeypatch.setattr(pipeline_module.shutil, "copy2", fail_restore_copy)

    with pytest.raises(OSError) as exc_info:
        _promotion_runner()._promote_shot_artifacts(
            staged_clip_path=paths["staged_clip"],
            staged_last_frame_path=paths["staged_frame"],
            clip_path=paths["clip"],
            last_frame_path=paths["frame"],
        )

    assert exc_info.value is promotion_error
    assert paths["clip_backup"].read_bytes() == b"old-clip"
    assert any("rollback" in note.lower() for note in promotion_error.__notes__)
    assert any("backup copy failed" in note for note in promotion_error.__notes__)

    canonical_clip_before_retry = paths["clip"].read_bytes()
    canonical_frame_before_retry = paths["frame"].read_bytes()
    paths["staged_clip"].write_bytes(b"second-new-clip")
    paths["staged_frame"].write_bytes(b"second-new-frame")
    with pytest.raises(FileExistsError):
        _promotion_runner()._promote_shot_artifacts(
            staged_clip_path=paths["staged_clip"],
            staged_last_frame_path=paths["staged_frame"],
            clip_path=paths["clip"],
            last_frame_path=paths["frame"],
        )

    assert paths["clip_backup"].read_bytes() == b"old-clip"
    assert not paths["frame_backup"].exists()
    assert paths["clip"].read_bytes() == canonical_clip_before_retry
    assert paths["frame"].read_bytes() == canonical_frame_before_retry
    assert not paths["staged_clip"].exists()
    assert not paths["staged_frame"].exists()


def test_failure_path_cleanup_error_is_attached_to_original_exception(tmp_path, monkeypatch):
    paths = _promotion_case(tmp_path)
    promotion_error = OSError("clip promotion failed")
    cleanup_error = OSError("staged frame cleanup failed")
    original_replace = Path.replace
    original_unlink = Path.unlink

    def fail_clip_promotion(source: Path, target: Path) -> Path:
        if source == paths["staged_clip"]:
            raise promotion_error
        return original_replace(source, target)

    def fail_staged_frame_cleanup(path: Path, *args, **kwargs):
        if path == paths["staged_frame"]:
            raise cleanup_error
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "replace", fail_clip_promotion)
    monkeypatch.setattr(Path, "unlink", fail_staged_frame_cleanup)

    with pytest.raises(OSError) as exc_info:
        _promotion_runner()._promote_shot_artifacts(
            staged_clip_path=paths["staged_clip"],
            staged_last_frame_path=paths["staged_frame"],
            clip_path=paths["clip"],
            last_frame_path=paths["frame"],
        )

    assert exc_info.value is promotion_error
    assert paths["staged_frame"].exists()
    assert any("cleanup" in note.lower() for note in promotion_error.__notes__)
    assert any("staged frame cleanup failed" in note for note in promotion_error.__notes__)


def test_commit_cleanup_failure_reports_progress_and_keeps_recovery_file(tmp_path, monkeypatch):
    paths = _promotion_case(tmp_path)
    signals = []
    transaction = _promotion_runner(signals)._promote_shot_artifacts(
        staged_clip_path=paths["staged_clip"],
        staged_last_frame_path=paths["staged_frame"],
        clip_path=paths["clip"],
        last_frame_path=paths["frame"],
    )
    cleanup_error = OSError("backup cleanup failed")
    original_unlink = Path.unlink

    def fail_clip_backup_cleanup(path: Path, *args, **kwargs):
        if path == paths["clip_backup"]:
            raise cleanup_error
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_clip_backup_cleanup)

    transaction.commit()
    assert paths["clip_backup"].exists()
    assert any("cleanup" in signal.lower() for signal in signals)
    assert any(str(paths["clip_backup"]) in signal for signal in signals)


def test_resume_manifest_write_failure_rolls_back_promoted_artifacts(
    example_project_and_shots,
    monkeypatch,
):
    project, shots, binding, template = example_project_and_shots
    initial = PipelineRunner(
        project,
        shots[:2],
        binding,
        template,
        comfy=FakeComfy(),
        ffmpeg=FakeFfmpeg(),
    )
    initial.run(run_id="run-resume-manifest-rollback")
    manifest_path = project.output.root / "run-resume-manifest-rollback" / "manifest.json"
    before_manifest = load_manifest(manifest_path)
    before = before_manifest.shots[1].model_copy(deep=True)
    clip_path = Path(before.clip_path)
    frame_path = Path(before.last_frame_path)
    old_clip_bytes = clip_path.read_bytes()
    old_frame_bytes = frame_path.read_bytes()
    before_manifest.shots[1].chain_input_hash = "force-dependency-rerun"
    atomic_write_manifest(manifest_path, before_manifest)

    class ReplacementComfy(FakeComfy):
        def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"replacement-clip")
            return "replacement-prompt-id"

    persistence_error = OSError("manifest persistence failed")
    real_atomic_write = pipeline_module.atomic_write_manifest

    def fail_post_promotion_write(path, manifest):
        target = next(record for record in manifest.shots if record.shot_id == "shot_002")
        if manifest.status == "running" and target.active_attempt == 2:
            raise persistence_error
        return real_atomic_write(path, manifest)

    monkeypatch.setattr(pipeline_module, "atomic_write_manifest", fail_post_promotion_write)
    runner = PipelineRunner(
        project,
        shots[:2],
        binding,
        template,
        comfy=ReplacementComfy(),
        ffmpeg=FakeFfmpeg(),
    )

    with pytest.raises(OSError) as exc_info:
        runner.resume(manifest_path)

    assert exc_info.value is persistence_error
    persisted = load_manifest(manifest_path)
    persisted_target = persisted.shots[1]
    assert persisted.status == "running"
    assert persisted_target.active_attempt == 1
    assert persisted_target.clip_hash == before.clip_hash
    assert persisted_target.last_frame_hash == before.last_frame_hash
    assert clip_path.read_bytes() == old_clip_bytes
    assert frame_path.read_bytes() == old_frame_bytes
    assert sha256_file(clip_path) == persisted_target.clip_hash
    assert sha256_file(frame_path) == persisted_target.last_frame_hash
    shot_dir = manifest_path.parent / "shots" / "shot_002"
    assert not (shot_dir / ".attempt_2.clip.mp4").exists()
    assert not (shot_dir / ".attempt_2.last_frame.png").exists()
    assert not (shot_dir / ".attempt_2.clip.mp4.backup").exists()
    assert not (shot_dir / ".attempt_2.last_frame.png.backup").exists()


def test_update_manifest_failure_rolls_back_before_atomic_write(
    example_project_and_shots,
):
    project, shots, binding, template = example_project_and_shots
    initial = PipelineRunner(
        project,
        shots[:1],
        binding,
        template,
        comfy=FakeComfy(),
        ffmpeg=FakeFfmpeg(),
    )
    initial.run(run_id="run-update-callback-rollback")
    manifest_path = project.output.root / "run-update-callback-rollback" / "manifest.json"
    manifest = load_manifest(manifest_path)
    before = manifest.shots[0].model_copy(deep=True)
    clip_path = Path(before.clip_path)
    frame_path = Path(before.last_frame_path)
    old_clip_bytes = clip_path.read_bytes()
    old_frame_bytes = frame_path.read_bytes()

    class ReplacementComfy(FakeComfy):
        def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"replacement-clip")
            return "replacement-prompt-id"

    runner = PipelineRunner(
        project,
        shots[:1],
        binding,
        template,
        comfy=ReplacementComfy(),
        ffmpeg=FakeFfmpeg(),
    )
    characters = {character.id: character for character in project.characters}
    record, _, promotion = runner._run_shot(
        manifest=manifest,
        manifest_path=manifest_path,
        run_root=manifest_path.parent,
        actual_run_id=manifest.run_id,
        shot=shots[0],
        shot_index=0,
        characters=characters,
        character_image_names=runner._prepare_character_images(),
        previous_frame=None,
        previous_frame_hash=None,
    )
    update_error = RuntimeError("dependency update failed")

    def fail_update() -> None:
        raise update_error

    with pytest.raises(RuntimeError) as exc_info:
        runner._persist_successful_shot(
            manifest=manifest,
            manifest_path=manifest_path,
            record=record,
            promotion=promotion,
            update_manifest=fail_update,
        )

    assert exc_info.value is update_error
    persisted = load_manifest(manifest_path)
    persisted_record = persisted.shots[0]
    assert persisted_record.active_attempt == 1
    assert persisted_record.clip_hash == before.clip_hash
    assert persisted_record.last_frame_hash == before.last_frame_hash
    assert clip_path.read_bytes() == old_clip_bytes
    assert frame_path.read_bytes() == old_frame_bytes
    assert sha256_file(clip_path) == persisted_record.clip_hash
    assert sha256_file(frame_path) == persisted_record.last_frame_hash
    shot_dir = manifest_path.parent / "shots" / "shot_001"
    assert not (shot_dir / ".attempt_2.clip.mp4").exists()
    assert not (shot_dir / ".attempt_2.last_frame.png").exists()
    assert not (shot_dir / ".attempt_2.clip.mp4.backup").exists()
    assert not (shot_dir / ".attempt_2.last_frame.png.backup").exists()


def test_resume_cleanup_progress_failure_is_best_effort_after_manifest_commit(
    example_project_and_shots,
    monkeypatch,
):
    project, shots, binding, template = example_project_and_shots
    initial = PipelineRunner(
        project,
        shots,
        binding,
        template,
        comfy=FakeComfy(),
        ffmpeg=FakeFfmpeg(),
    )
    initial.run(run_id="run-cleanup-progress-failure")
    manifest_path = project.output.root / "run-cleanup-progress-failure" / "manifest.json"
    manifest = load_manifest(manifest_path)
    manifest.shots[1].chain_input_hash = "force-dependency-rerun"
    atomic_write_manifest(manifest_path, manifest)

    class ReplacementComfy(FakeComfy):
        def __init__(self):
            super().__init__()
            self.shot_ids = []

        def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
            shot_id = output_path.parent.name
            self.shot_ids.append(shot_id)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(f"replacement:{shot_id}".encode())
            return "replacement-prompt-id"

    shot_dir = manifest_path.parent / "shots" / "shot_002"
    retained_backup = shot_dir / ".attempt_2.clip.mp4.backup"
    original_unlink = Path.unlink

    def fail_backup_cleanup(path: Path, *args, **kwargs):
        if path == retained_backup:
            raise OSError("backup cleanup failed")
        return original_unlink(path, *args, **kwargs)

    callback_error = RuntimeError("progress consumer failed")
    signals = []

    def failing_progress(message: str) -> None:
        signals.append(message)
        if str(retained_backup) in message:
            raise callback_error

    monkeypatch.setattr(Path, "unlink", fail_backup_cleanup)
    comfy = ReplacementComfy()
    runner = PipelineRunner(
        project,
        shots,
        binding,
        template,
        comfy=comfy,
        ffmpeg=FakeFfmpeg(),
        progress_callback=failing_progress,
    )

    resumed = runner.resume(manifest_path)

    assert resumed.status == "succeeded"
    assert comfy.shot_ids == ["shot_002", "shot_003"]
    assert retained_backup.exists()
    assert any(str(retained_backup) in signal for signal in signals)
    persisted = load_manifest(manifest_path)
    assert persisted.status == "succeeded"
    assert persisted.shots[1].active_attempt == 2
    assert persisted.shots[2].active_attempt == 2
    for record in persisted.shots:
        assert sha256_file(record.clip_path) == record.clip_hash
        assert sha256_file(record.last_frame_path) == record.last_frame_hash


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
    resumed_runner.resume(manifest_path)

    persisted = load_manifest(manifest_path)
    record = persisted.shots[0]
    assert persisted.status == "succeeded"
    assert [item.attempt for item in record.attempts] == [1, 2, 3]
    assert [item.status for item in record.attempts] == ["failed", "failed", "succeeded"]
    assert record.active_attempt == 3
    assert (manifest_path.parent / "shots" / "shot_001" / "attempt_3" / "workflow.json").exists()


def test_resume_skips_completed_shots(example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    runner = PipelineRunner(project, shots, binding, template, comfy=FakeComfy(), ffmpeg=FakeFfmpeg())
    manifest = runner.run(run_id="run-resume-skip")
    assert manifest.status == "succeeded"

    fake_comfy = FakeComfy()
    runner2 = PipelineRunner(project, shots, binding, template, comfy=fake_comfy, ffmpeg=FakeFfmpeg())
    resumed = runner2.resume(project.output.root / "run-resume-skip" / "manifest.json")
    assert resumed.status == "succeeded"
    assert len(fake_comfy.submitted) == 0


def test_resume_reruns_failed_shot(example_project_and_shots):
    project, shots, binding, template = example_project_and_shots
    runner = PipelineRunner(project, shots, binding, template, comfy=FakeComfy(), ffmpeg=FakeFfmpeg())
    manifest = runner.run(run_id="run-fail-resume")
    # Corrupt shot_002's clip to invalidate it
    shot_002_clip = project.output.root / "run-fail-resume" / "shots" / "shot_002" / "clip.mp4"
    if shot_002_clip.exists():
        shot_002_clip.write_bytes(b"corrupted")

    fake_comfy = FakeComfy()
    runner2 = PipelineRunner(project, shots, binding, template, comfy=fake_comfy, ffmpeg=FakeFfmpeg())
    resumed = runner2.resume(project.output.root / "run-fail-resume" / "manifest.json")
    assert resumed.status == "succeeded"
    assert len(fake_comfy.submitted) >= 1
