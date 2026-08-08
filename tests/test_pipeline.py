from pathlib import Path

import pytest

from ai_video.config import sha256_file
from ai_video.errors import AiVideoError, ErrorCode, retryable_error
from ai_video.manifest import load_manifest
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
