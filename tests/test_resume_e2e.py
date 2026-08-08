from pathlib import Path

import pytest

from ai_video.config import load_project, load_shots, load_yaml
from ai_video.manifest import atomic_write_manifest, load_manifest
from ai_video.models import WorkflowBinding
from ai_video.pipeline import PipelineRunner
from ai_video.workflow_loader import load_workflow_template


class VersionedFakeComfy:
    def __init__(self, generation: str | dict[str, str]):
        self.generation = generation
        self.submitted: list[str] = []

    def prepare_image(self, path: Path) -> str:
        return Path(path).name if path else "none"

    def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
        shot_id = output_path.parent.name
        self.submitted.append(shot_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        generation = (
            self.generation.get(shot_id, "old")
            if isinstance(self.generation, dict)
            else self.generation
        )
        output_path.write_bytes(f"{generation}:{shot_id}".encode())
        return "prompt-id"


class ContentHashFfmpeg:
    def validate_clip(self, path: Path) -> None:
        pass

    def extract_last_frame(self, clip: Path, frame: Path) -> None:
        frame.parent.mkdir(parents=True, exist_ok=True)
        frame.write_bytes(clip.read_bytes())

    def normalize_clip(self, source: Path, target: Path, **kwargs) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())

    def stitch_clips(self, clips, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"final")


def _write_resume_project(
    tmp_path: Path,
    *,
    second_shot_init: bool = False,
    bind_init_image: bool = True,
) -> tuple[Path, Path]:
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
    binding = (
        "positive_prompt:\n  path: ['6', inputs, text]\n"
        "negative_prompt:\n  path: ['7', inputs, text]\n"
        "seed:\n  path: ['3', inputs, seed]\n"
        "output_prefix:\n  path: ['42', inputs, filename_prefix]\n"
        "character_refs: []\n"
        "clip_output:\n  node: '42'\n  kind: gifs\n  extensions: ['.mp4']\n  select: first\n"
    )
    if bind_init_image:
        binding = (
            "positive_prompt:\n  path: ['6', inputs, text]\n"
            "negative_prompt:\n  path: ['7', inputs, text]\n"
            "seed:\n  path: ['3', inputs, seed]\n"
            "init_image:\n  path: ['12', inputs, image]\n"
            "output_prefix:\n  path: ['42', inputs, filename_prefix]\n"
            "character_refs: []\n"
            "clip_output:\n  node: '42'\n  kind: gifs\n  extensions: ['.mp4']\n  select: first\n"
        )
    (wf / "binding.yaml").write_text(binding, encoding="utf-8")
    project_yaml = tmp_path / "project.yaml"
    project_yaml.write_text(
        "project_name: resume-test\ncomfy:\n  base_url: http://127.0.0.1:8188\n"
        "workflow:\n  template: wf/template.json\n  binding: wf/binding.yaml\n"
        "output:\n  root: runs\n  min_free_gb: 0\n"
        "defaults:\n  seed: 100\n  fps: 16\n  width: 512\n  height: 512\n",
        encoding="utf-8",
    )
    shots_yaml = tmp_path / "shots.yaml"
    init_line = "    init_image: second.png\n" if second_shot_init else ""
    shots_yaml.write_text(
        "shots:\n  - id: shot_001\n    prompt: first\n"
        f"  - id: shot_002\n    prompt: second\n{init_line}"
        "  - id: shot_003\n    prompt: third\n",
        encoding="utf-8",
    )
    if second_shot_init:
        (tmp_path / "second.png").write_bytes(b"explicit-init")
    return project_yaml, shots_yaml


def _initial_resume_case(
    tmp_path: Path,
    *,
    second_shot_init: bool = False,
    bind_init_image: bool = True,
    corrupt_shot_001: bool = True,
):
    project_yaml, shots_yaml = _write_resume_project(
        tmp_path,
        second_shot_init=second_shot_init,
        bind_init_image=bind_init_image,
    )

    project = load_project(project_yaml)
    shots = load_shots(shots_yaml, project)
    binding = WorkflowBinding.model_validate(load_yaml(project.workflow.binding))
    template = load_workflow_template(project.workflow.template)

    initial_comfy = VersionedFakeComfy("old")
    runner = PipelineRunner(
        project, shots, binding, template, comfy=initial_comfy, ffmpeg=ContentHashFfmpeg()
    )
    manifest = runner.run(
        run_id="run-resume",
        project_config_path=project_yaml,
        shot_list_path=shots_yaml,
    )
    assert manifest.status == "succeeded"
    assert initial_comfy.submitted == ["shot_001", "shot_002", "shot_003"]

    second = manifest.shots[1]
    if bind_init_image and not second_shot_init:
        assert second.chain_input_hash == manifest.shots[0].last_frame_hash
    else:
        assert second.chain_input_hash is None

    if corrupt_shot_001:
        shot_001_clip = tmp_path / "runs" / "run-resume" / "shots" / "shot_001" / "clip.mp4"
        shot_001_clip.write_bytes(b"corrupted")
    return project, shots, binding, template, manifest, project.output.root / "run-resume" / "manifest.json"


def test_resume_propagates_changed_upstream_last_frame_to_direct_dependents(tmp_path):
    project, shots, binding, template, _, manifest_path = _initial_resume_case(tmp_path)

    resume_comfy = VersionedFakeComfy("new")
    resumed = PipelineRunner(
        project, shots, binding, template, comfy=resume_comfy, ffmpeg=ContentHashFfmpeg()
    ).resume(manifest_path)

    assert resumed.status == "succeeded"
    assert resume_comfy.submitted == ["shot_001", "shot_002", "shot_003"]


def test_resume_stops_downstream_propagation_when_last_frame_is_identical(tmp_path):
    project, shots, binding, template, _, manifest_path = _initial_resume_case(tmp_path)

    resume_comfy = VersionedFakeComfy("old")
    resumed = PipelineRunner(
        project, shots, binding, template, comfy=resume_comfy, ffmpeg=ContentHashFfmpeg()
    ).resume(manifest_path)

    assert resumed.status == "succeeded"
    assert resume_comfy.submitted == ["shot_001"]


def test_resume_explicit_init_cuts_downstream_propagation_for_legacy_chain_hash(tmp_path):
    project, shots, binding, template, manifest, manifest_path = _initial_resume_case(
        tmp_path, second_shot_init=True
    )
    manifest.shots[1].chain_input_hash = manifest.shots[0].last_frame_hash
    atomic_write_manifest(manifest_path, manifest)

    resume_comfy = VersionedFakeComfy("new")
    resumed = PipelineRunner(
        project, shots, binding, template, comfy=resume_comfy, ffmpeg=ContentHashFfmpeg()
    ).resume(manifest_path)

    assert resumed.status == "succeeded"
    assert resume_comfy.submitted == ["shot_001"]


def test_resume_without_init_image_binding_has_no_downstream_dependency(tmp_path):
    project, shots, binding, template, _, manifest_path = _initial_resume_case(
        tmp_path, bind_init_image=False
    )

    resume_comfy = VersionedFakeComfy("new")
    resumed = PipelineRunner(
        project, shots, binding, template, comfy=resume_comfy, ffmpeg=ContentHashFfmpeg()
    ).resume(manifest_path)

    assert resumed.status == "succeeded"
    assert resume_comfy.submitted == ["shot_001"]


def test_resume_persists_running_status_before_interrupted_stale_downstream(tmp_path):
    project, shots, binding, template, _, manifest_path = _initial_resume_case(tmp_path)

    class InterruptingComfy(VersionedFakeComfy):
        def submit_and_collect_clip(self, workflow, output_path: Path) -> str:
            if output_path.parent.name == "shot_002":
                raise KeyboardInterrupt
            return super().submit_and_collect_clip(workflow, output_path)

    with pytest.raises(KeyboardInterrupt):
        PipelineRunner(
            project,
            shots,
            binding,
            template,
            comfy=InterruptingComfy("new"),
            ffmpeg=ContentHashFfmpeg(),
        ).resume(manifest_path)

    interrupted = load_manifest(manifest_path)
    assert interrupted.status == "running"
    assert [record.status for record in interrupted.shots] == ["succeeded", "stale", "succeeded"]


def test_resume_fast_path_bypasses_valid_artifacts_with_downstream_chain_hash_mismatch(tmp_path):
    project, shots, binding, template, manifest, manifest_path = _initial_resume_case(
        tmp_path, corrupt_shot_001=False
    )
    manifest.shots[1].chain_input_hash = "mismatched-chain-input"
    atomic_write_manifest(manifest_path, manifest)

    resume_comfy = VersionedFakeComfy("old")
    resumed = PipelineRunner(
        project, shots, binding, template, comfy=resume_comfy, ffmpeg=ContentHashFfmpeg()
    ).resume(manifest_path)

    assert resumed.status == "succeeded"
    assert resume_comfy.submitted == ["shot_002"]


def test_resume_stops_downstream_at_middle_edge_when_regenerated_last_frame_is_identical(tmp_path):
    project, shots, binding, template, _, manifest_path = _initial_resume_case(tmp_path)

    resume_comfy = VersionedFakeComfy({"shot_001": "new", "shot_002": "old"})
    resumed = PipelineRunner(
        project, shots, binding, template, comfy=resume_comfy, ffmpeg=ContentHashFfmpeg()
    ).resume(manifest_path)

    assert resumed.status == "succeeded"
    assert resume_comfy.submitted == ["shot_001", "shot_002"]
