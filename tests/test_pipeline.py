from pathlib import Path

from ai_video.errors import ErrorCode, retryable_error
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
