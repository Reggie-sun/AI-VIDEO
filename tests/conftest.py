from pathlib import Path

import pytest
import yaml

from ai_video.config import load_project, load_shots, load_yaml
from ai_video.models import WorkflowBinding
from ai_video.workflow_loader import load_workflow_template


@pytest.fixture
def example_project_files(tmp_path: Path) -> tuple[Path, Path]:
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
        "defaults:\n  width: 64\n  height: 64\n  fps: 4\n  clip_seconds: 1\n  seed: 100\n"
        "characters:\n"
        "  - id: hero\n"
        "    name: Hero\n"
        "    description: same person\n"
        "    reference_images: [refs/hero.png]\n",
        encoding="utf-8",
    )
    shots = tmp_path / "shots.yaml"
    shots.write_text(
        "shots:\n"
        "  - id: shot_001\n    prompt: hero enters room\n    characters: [hero]\n"
        "  - id: shot_002\n    prompt: hero looks at camera\n    characters: [hero]\n"
        "  - id: shot_003\n    prompt: hero walks away\n    characters: [hero]\n",
        encoding="utf-8",
    )
    return project, shots


@pytest.fixture
def example_project_and_shots(example_project_files):
    project_path, shots_path = example_project_files
    project = load_project(project_path)
    shots = load_shots(shots_path, project)
    binding = WorkflowBinding.model_validate(load_yaml(project.workflow.binding))
    template = load_workflow_template(project.workflow.template)
    return project, shots, binding, template
