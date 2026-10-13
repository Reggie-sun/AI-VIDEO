"""Check actual changed Canvas inputs through the canonical read-only seam."""
import json
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from scripts import agent_harness_canvas_data as data_check
from test_canvas_project_data import text_data


def project(tmp_path):
    root = tmp_path / "docs/canvas-projects/story"
    root.mkdir(parents=True)
    source, definition = text_data()
    (root / "project.json").write_text(json.dumps(definition))
    (root / "source.json").write_text(json.dumps(source))
    return root


def test_valid_inputs_deduplicate_project_without_production_effects(tmp_path, monkeypatch):
    root = project(tmp_path)
    before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
    original = data_check.canvas_run
    calls = []

    def author(**kwargs):
        assert kwargs["action"] == "author"
        assert kwargs.get("runtime_factory") is None
        calls.append(kwargs["data_path"])
        result = original(**kwargs)
        assert list(Path(kwargs["project_root"]).iterdir()) == []
        return result

    monkeypatch.setattr(data_check, "canvas_run", author)
    result = data_check.check_paths(tmp_path, [
        "docs/canvas-projects/story/project.json", "docs/canvas-projects/story/source.json",
    ])
    assert calls == [root / "project.json"]
    assert result["checked_projects"] == ["docs/canvas-projects/story/project.json"]
    assert result["production_acceptance"] == "NOT_EVALUATED"
    assert before == sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))


@pytest.mark.parametrize("damage", ["missing_source", "expanded_intent", "missing_definition"])
def test_invalid_real_inputs_fail_closed(tmp_path, damage):
    root = project(tmp_path)
    if damage == "missing_source":
        (root / "source.json").unlink()
    elif damage == "missing_definition":
        (root / "project.json").unlink()
    else:
        definition = json.loads((root / "project.json").read_text())
        definition["direction"]["shots"][0]["shot"]["intent"] = "invented action"
        (root / "project.json").write_text(json.dumps(definition))
    with pytest.raises((AiVideoError, ValueError, OSError)):
        data_check.check_paths(tmp_path, ["docs/canvas-projects/story/project.json"])


def test_deleted_reference_still_reopens_project(tmp_path):
    project(tmp_path)
    result = data_check.check_paths(tmp_path, ["docs/canvas-projects/story/deleted.png"])
    assert len(result["checked_projects"]) == 1


def test_removed_project_and_markdown_do_not_invoke_author(tmp_path, monkeypatch):
    def unexpected(**kwargs):
        pytest.fail("no surviving project data changed")
    monkeypatch.setattr(data_check, "canvas_run", unexpected)
    result = data_check.check_paths(tmp_path, [
        "docs/canvas-projects/removed/project.json", "docs/canvas-projects/story/README.md",
        "docs/unrelated.json",
    ])
    assert result["checked_projects"] == []


@pytest.mark.parametrize("escape", ["../private.json", "docs/canvas-projects/story/../../../../private.json"])
def test_scope_path_traversal_is_rejected(tmp_path, escape):
    with pytest.raises(ValueError):
        data_check.check_paths(tmp_path, [escape])


def test_symlinked_input_path_is_rejected_even_if_not_referenced(tmp_path):
    root = project(tmp_path)
    (tmp_path / "outside.json").write_text("{}")
    (root / "alias.json").symlink_to(tmp_path / "outside.json")
    with pytest.raises(ValueError):
        data_check.check_paths(tmp_path, ["docs/canvas-projects/story/alias.json"])


@pytest.mark.parametrize("damage", ["missing", "bad_png"])
def test_referenced_image_bytes_are_checked_by_canonical_author(tmp_path, damage):
    from shutil import copytree
    source = Path(__file__).resolve().parents[1] / "docs/canvas-projects/subject-reference"
    root = tmp_path / "docs/canvas-projects/story"
    copytree(source, root)
    assert data_check.check_paths(tmp_path, ["docs/canvas-projects/story/room.png"])["checked_projects"]
    if damage == "missing":
        (root / "room.png").unlink()
    else:
        (root / "room.png").write_bytes(b"not a PNG")
    with pytest.raises((AiVideoError, ValueError, OSError)):
        data_check.check_paths(tmp_path, ["docs/canvas-projects/story/room.png"])


def test_cli_reports_failure_without_echoing_source(tmp_path, monkeypatch, capsys):
    root = project(tmp_path)
    (root / "source.json").write_text("PRIVATE_INVALID_SOURCE")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(data_check, "install_network_guard", lambda: None)
    assert data_check.main(["--paths", "docs/canvas-projects/story/source.json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "failed"
    assert report["production_acceptance"] == "NOT_EVALUATED"
    assert "PRIVATE_INVALID_SOURCE" not in json.dumps(report)


def test_flag_named_changed_file_is_passed_as_literal_path(tmp_path, monkeypatch, capsys):
    root = project(tmp_path)
    (root / "source.json").write_text("invalid source")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(data_check, "install_network_guard", lambda: None)
    from scripts.agent_harness import _check_argv
    argv = _check_argv({"argv": ["check"], "scope_paths": True},
        {"changed_paths": ["--help", "docs/canvas-projects/story/source.json"]}, None)
    assert data_check.main(list(argv[1:])) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "failed"
