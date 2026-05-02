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
    """Simulate: run 3 shots, corrupt shot_003's clip, resume should only re-run shot_003."""
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
    runner = PipelineRunner(project, shots, binding, template, comfy=fake_comfy, ffmpeg=FakeFfmpeg())
    manifest = runner.run(
        run_id="run-partial",
        project_config_path=project_yaml,
        shot_list_path=shots_yaml,
    )
    assert manifest.status == "succeeded"
    assert len(fake_comfy.submitted) == 3

    # Corrupt shot_003's clip
    shot_003_clip = tmp_path / "runs" / "run-partial" / "shots" / "shot_003" / "clip.mp4"
    if shot_003_clip.exists():
        shot_003_clip.write_bytes(b"corrupted")

    # Resume: only shot_003 should be re-run
    resume_comfy = FakeComfy()
    runner2 = PipelineRunner(project, shots, binding, template, comfy=resume_comfy, ffmpeg=FakeFfmpeg())
    resumed = runner2.resume(tmp_path / "runs" / "run-partial" / "manifest.json")
    assert resumed.status == "succeeded"
    assert len(resume_comfy.submitted) == 1
