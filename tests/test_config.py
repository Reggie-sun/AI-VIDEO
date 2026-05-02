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


def test_resolved_paths_are_clean_absolute(tmp_path):
    project_path, _ = write_example_files(tmp_path)
    # Simulate running from a subdirectory: load through a path containing ..
    # so that base_dir (project_path.parent) includes ".." segments.
    sub_dir = tmp_path / "subdir"
    sub_dir.mkdir()
    project = load_project(sub_dir / ".." / "project.yaml")
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


def test_repo_wan22_fast_project_loads_with_local_paths():
    repo_root = Path(__file__).resolve().parents[1]
    project = load_project(repo_root / "configs/wan22_fast.project.yaml")

    assert project.project_name == "wan22-fast-demo"
    assert project.workflow.template == repo_root / "workflows/templates/wan22_i2v_api.json"
    assert project.workflow.binding == repo_root / "workflows/bindings/wan22_i2v_binding.yaml"
    assert project.output.root == repo_root / "runs"
    assert project.defaults.fps == 20
    assert project.defaults.clip_seconds == 3
    assert project.defaults.max_attempts == 1


def test_repo_wan22_quick_shots_override_runtime():
    repo_root = Path(__file__).resolve().parents[1]
    project = load_project(repo_root / "configs/wan22.project.yaml")
    shots = load_shots(repo_root / "configs/wan22_quick.shots.yaml", project)

    assert len(shots) == 1
    assert shots[0].init_image == repo_root / "assets/wan22_quick_init.png"
    assert shots[0].clip_seconds == 3
    assert shots[0].fps == 20
