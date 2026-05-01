from pathlib import Path

from ai_video.cli import main


def test_validate_returns_zero_for_example_project(example_project_files, capsys):
    project_path, shots_path = example_project_files
    code = main(["validate", "--project", str(project_path), "--shots", str(shots_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "valid" in captured.out.lower()


def test_validate_returns_one_for_bad_config(tmp_path, capsys):
    project = tmp_path / "bad.yaml"
    shots = tmp_path / "shots.yaml"
    project.write_text("project_name: bad\n", encoding="utf-8")
    shots.write_text("shots: []\n", encoding="utf-8")
    code = main(["validate", "--project", str(project), "--shots", str(shots)])
    captured = capsys.readouterr()
    assert code == 1
    assert "config" in captured.err.lower() or "validation" in captured.err.lower()


def test_validate_accepts_ui_workflow_template(tmp_path, capsys):
    fixture = Path(__file__).parent / "fixtures" / "wan22_i2v_ui.json"
    refs = tmp_path / "refs"
    refs.mkdir()
    (refs / "hero.png").write_bytes(b"fake-png")

    workflows = tmp_path / "workflows"
    workflows.mkdir()
    template = workflows / "wan22_i2v_ui.json"
    template.write_bytes(fixture.read_bytes())
    binding = workflows / "binding.yaml"
    binding.write_text(
        "positive_prompt:\n  path: ['549', inputs, text]\n"
        "negative_prompt:\n  path: ['548', inputs, negative_prompt]\n"
        "seed:\n  path: ['561', inputs, value]\n"
        "init_image:\n  path: ['521', inputs, image]\n"
        "output_prefix:\n  path: ['30', inputs, filename_prefix]\n"
        "character_refs: []\n"
        "clip_output:\n  node: '30'\n  kind: gifs\n  extensions: ['.mp4']\n  select: first\n",
        encoding="utf-8",
    )

    project = tmp_path / "project.yaml"
    project.write_text(
        "project_name: demo\n"
        "comfy:\n  base_url: http://127.0.0.1:8188\n"
        "workflow:\n"
        "  template: workflows/wan22_i2v_ui.json\n"
        "  binding: workflows/binding.yaml\n"
        "output:\n  root: runs\n  min_free_gb: 0\n"
        "defaults:\n  seed: 100\n"
        "characters:\n"
        "  - id: hero\n"
        "    name: Hero\n"
        "    reference_images: [refs/hero.png]\n",
        encoding="utf-8",
    )
    shots = tmp_path / "shots.yaml"
    shots.write_text(
        "shots:\n"
        "  - id: shot_001\n"
        "    prompt: hero enters room\n"
        "    characters: [hero]\n",
        encoding="utf-8",
    )

    code = main(["validate", "--project", str(project), "--shots", str(shots)])
    captured = capsys.readouterr()

    assert code == 0
    assert "valid" in captured.out.lower()
