from pathlib import Path

from ai_video.errors import ErrorCode, retryable_error
from ai_video.manifest import load_manifest
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
