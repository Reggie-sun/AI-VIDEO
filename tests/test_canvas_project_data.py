from copy import deepcopy
import json

import pytest

from ai_video.canvas_project_data import open_canvas_project, prepare_canvas_project_data
from ai_video.errors import AiVideoError
from ai_video.production.state_commit import ProductionStateCommitter
from scripts.canvas_production_source import inspect_canvas_source
from test_canvas_authoring import direction
from test_canvas_sequence_packet import document


def text_data():
    source = document()
    source["edges"] = []
    for node in source["nodes"]:
        draft = node["data"].get("generationDraft")
        if draft:
            node["data"]["resourceBatches"] = [{"id": "adopted-" + node["id"],
                "resourceIds": [node["data"]["resourceId"]]}]
            draft["references"] = []
            draft["parts"] = [p for p in draft["parts"] if p["type"] == "text"]
    data = direction()
    for row in data["shots"]:
        row["shot"].pop("intent")
    definition = {"schema_version": "canvas-project-data/1", "source": "source.json",
                  "selection": {"node_ids": ["a", "b"]}, "direction": data, "images": []}
    return source, definition


def test_data_entry_preserves_original_text_and_resumes_immutable_director_inputs(tmp_path):
    source, definition = text_data()
    inspection = inspect_canvas_source(source, definition["selection"])
    (tmp_path / "project").mkdir()
    service, registry, artifacts = open_canvas_project(inspection=inspection, definition=definition,
        data_root=tmp_path, committer=ProductionStateCommitter(tmp_path / "project"))
    bundle = service.author(registry=registry, asset_artifacts=artifacts)
    bundle.bootstrap(committer=service.committer, attempt_id="data-author")
    reopened, _, _ = open_canvas_project(inspection=inspection, definition=definition,
        data_root=tmp_path, committer=service.committer)
    assert reopened.direction == service.direction
    assert service.direction["shots"][0]["shot"]["intent"] == "前段：生物遮满镜头。"
    assert definition["direction"]["shots"][0]["shot"].get("intent") is None
    assert all(a["reason"] for a in bundle.adaptations)


def test_reproduction_rejects_director_expansion_before_any_state(tmp_path):
    source, definition = text_data()
    definition["direction"]["shots"][0]["shot"]["intent"] = "invented dialogue and camera"
    with pytest.raises(AiVideoError, match="differs"):
        prepare_canvas_project_data(inspection=inspect_canvas_source(source, definition["selection"]),
            definition=definition, data_root=tmp_path)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("index", [0, 1])
@pytest.mark.parametrize("field", ["shot.intent", "shot.dialogue", "shot.narration",
                                  "generation.generation_intent.subject_action.progression"])
def test_source_rejection_locates_occurrence_and_field_without_raw_input(tmp_path, capsys, index, field):
    from scripts.canvas_production import main
    source, definition = text_data()
    row = definition["direction"]["shots"][index]
    cursor = row
    parts = field.split(".")
    for part in parts[:-1]:
        cursor = cursor.setdefault(part, {})
    cursor[parts[-1]] = "PRIVATE_CALLER_TEXT"
    inspection = inspect_canvas_source(source, definition["selection"])
    occurrence = inspection["selection"]["sequence_packet"]["units"][index]["occurrence_id"]
    (tmp_path / "source.json").write_text(json.dumps(source))
    (tmp_path / "project.json").write_text(json.dumps(definition))
    production = tmp_path / "production"
    production.mkdir()
    result = main(["author", "--data", str(tmp_path / "project.json"), "--project-root", str(production)])
    report = json.loads(capsys.readouterr().out)
    assert result == 2
    assert occurrence in report["error"] and field in report["error"]
    assert "PRIVATE_CALLER_TEXT" not in report["error"]
    assert report["production_acceptance"] == "NOT_EVALUATED"
    assert list(production.iterdir()) == []


def test_generic_cli_requires_only_data_for_authoring(tmp_path):
    from scripts.canvas_production import main
    source, definition = text_data()
    (tmp_path / "source.json").write_text(json.dumps(source))
    path = tmp_path / "data.json"
    path.write_text(json.dumps(definition))
    (tmp_path / "project").mkdir()
    assert main(["author", "--data", str(path), "--project-root", str(tmp_path / "project")]) == 0
    assert list((tmp_path / "project").iterdir()) == []


def test_sequence_preflight_exposes_future_state_before_first_generation(tmp_path):
    from scripts.canvas_production import run
    source, definition = text_data()
    rows = definition["direction"]["shots"]
    rows[1]["state_reference"] = {"source_shot_id": "one", "frame_index": 12,
        "replace_asset_id": "future-state", "checks": {"action": "Right hand holds phone"},
        "usage_license": "provider-output"}
    definition["direction"]["composition_order"] = ["b", "a"]
    (tmp_path / "source.json").write_text(json.dumps(source))
    path = tmp_path / "data.json"
    path.write_text(json.dumps(definition))
    production = tmp_path / "production"
    production.mkdir()
    result = run(data_path=path, project_root=production, action="preflight",
        runtime_factory="does_not_exist:must_not_be_loaded")
    assert result["generation_order"] == ["one", "two"]
    assert result["composition_order"] == ["two", "one"]
    assert result["shots"][0]["source_text"] == "前段：生物遮满镜头。"
    state = result["shots"][1]["state_reference"]
    assert state["input_kind"] == "extracted_frame"
    assert state["source_shot_id"] == "one" and state["frame_index"] == 12
    assert state["binding_status"] == "PENDING_ACCEPTED_SOURCE"
    assert state["provider_admission"] == "NOT_EVALUATED"
    assert result["production_acceptance"] == "NOT_EVALUATED"
    assert list(production.iterdir()) == []


def test_preflight_resumes_sealed_direction_not_mutable_project_data(tmp_path):
    from scripts.canvas_production import run
    source, definition = text_data()
    production = tmp_path / "production"
    production.mkdir()
    service, registry, artifacts = open_canvas_project(
        inspection=inspect_canvas_source(source, definition["selection"]),
        definition=definition, data_root=tmp_path, committer=ProductionStateCommitter(production))
    service.author(registry=registry, asset_artifacts=artifacts).bootstrap(
        committer=service.committer, attempt_id="preflight-input")
    definition["direction"]["shots"][0]["shot"]["intent"] = "UNAPPROVED EDIT"
    (tmp_path / "source.json").write_text(json.dumps(source))
    path = tmp_path / "data.json"
    path.write_text(json.dumps(definition))
    before = {p.relative_to(production): p.read_bytes() for p in production.rglob("*") if p.is_file()}
    result = run(data_path=path, project_root=production, action="preflight")
    assert result["shots"][0]["authored_text"] == "前段：生物遮满镜头。"
    assert before == {p.relative_to(production): p.read_bytes() for p in production.rglob("*") if p.is_file()}


def test_author_preflight_separates_asset_provenance_from_provider_admission(tmp_path):
    from pathlib import Path
    from scripts.canvas_production import run
    root = Path(__file__).resolve().parents[1] / "docs/canvas-projects/subject-reference"
    tmp_path.mkdir(exist_ok=True)
    result = run(data_path=root / "project.json", project_root=tmp_path, action="author")
    report = result["preflight"]
    refs = report["shots"][0]["references"]
    assert len(refs) == 3
    assert {r["role"] for r in refs} == {"character_reference", "scene_reference"}
    assert all(len(r["identity"]["sha256"]) == 64 for r in refs)
    assert all(r["provider_admission"] == "NOT_EVALUATED" for r in refs)
    definition = json.loads((root / "project.json").read_text())
    assert report["shots"][0]["generation_requirements"]["audio_need"] == (
        definition["direction"]["shots"][0]["generation"]["audio_need"])
    successor = report["shots"][1]
    placeholder = successor["state_reference"]["replace_asset_id"]
    assert next(r for r in successor["references"] if r["asset_id"] == placeholder)[
        "source_status"] == "AUTHORING_PLACEHOLDER_NOT_ACCEPTED_STATE"
    assert list(tmp_path.iterdir()) == []


def test_preflight_rejects_invalid_authoring_instead_of_projecting_it(tmp_path):
    from scripts.canvas_production import main
    source, definition = text_data()
    definition["direction"]["shots"][1]["state_reference"] = {"source_shot_id": "one"}
    (tmp_path / "source.json").write_text(json.dumps(source))
    (tmp_path / "data.json").write_text(json.dumps(definition))
    production = tmp_path / "production"
    production.mkdir()
    assert main(["preflight", "--data", str(tmp_path / "data.json"),
        "--project-root", str(production)]) == 2
    assert list(production.iterdir()) == []


def test_data_entry_rejects_forged_inspection_identity(tmp_path):
    from test_canvas_source_expression import subject_source
    source, data, registry, _ = subject_source(tmp_path)
    # Feed the preserved original graph and ordinary imported PNG selections.
    raw = deepcopy(document())
    # The helper's packet is also accepted by the inspection-free data API only
    # after a correctly hash-bound inspection projection.
    from ai_video.canvas_authoring import input_hash
    inspection = {"source_snapshot": raw, "source_snapshot_sha256": input_hash(raw), "selection": {}}
    # Use the packet's exact source identity by reopening its actual source in
    # the dedicated source-expression tests; reject a fabricated wrapper here.
    inspection["selection"] = {"status": "CANONICAL_PACKET_AVAILABLE", "sequence_packet": source,
                               "sequence_packet_sha256": input_hash(source)}
    definition = {"schema_version": "canvas-project-data/1", "direction": data, "images": []}
    with pytest.raises(Exception, match="identity changed"):
        prepare_canvas_project_data(inspection=inspection, definition=definition, data_root=tmp_path)


def test_subject_example_is_measured_and_grouped_without_internal_hash_input(tmp_path):
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "docs/canvas-projects/subject-reference"
    definition = json.loads((root / "project.json").read_text())
    source = json.loads((root / "source.json").read_text())
    packet, data, registry, artifacts = prepare_canvas_project_data(
        inspection=inspect_canvas_source(source, definition["selection"]), definition=definition, data_root=root)
    materials = data["shots"][0]["shot"]["preserved_source_expression"]["parts"][1]["materials"]
    assert [m["asset_id"] for m in materials] == ["robot-main", "robot-aux"]
    assert {m["role"] for m in materials} == {"identity"}
    assert data["shots"][0]["shot"]["intent"] == "Robot 图片2、图片1 lifts its hands in 图片3."
    assert len(registry.assets) == 3 and len(artifacts) == 3
    assert "preserved_source_expression" not in definition["direction"]["shots"][0]["shot"]


def test_standard_reader_rejects_changed_sealed_project_input(tmp_path):
    from ai_video.production.project import load_production_project
    source, definition = text_data()
    service, registry, artifacts = open_canvas_project(inspection=inspect_canvas_source(source, definition["selection"]),
        definition=definition, data_root=tmp_path, committer=ProductionStateCommitter(tmp_path))
    bundle = service.author(registry=registry, asset_artifacts=artifacts)
    bundle.bootstrap(committer=service.committer, attempt_id="sealed-input")
    input_file = next((tmp_path / "evidence/authoring-input").glob("*.json"))
    input_file.write_text("{}\n")
    with pytest.raises(Exception, match="authoring input"):
        load_production_project(tmp_path / "project.yaml")


@pytest.mark.parametrize("source_shape", ["original", "repeated_and_tray_only"])
def test_nominal_15_second_example_uses_real_seedance_compiler_without_effects(tmp_path, source_shape):
    from pathlib import Path
    from test_canvas_source_expression import subject_service
    from ai_video.production.generation_feedback import RegisteredGenerationTarget
    from tests.production_generation_execution_factory import activate_fixture_generation_qa_policy
    from test_canvas_source_expression import LoadedFixture
    service, limits = subject_service(tmp_path)
    root = Path(__file__).resolve().parents[1] / "docs/canvas-projects/subject-reference"
    definition = json.loads((root / "project.json").read_text())
    original = json.loads((root / "source.json").read_text())
    if source_shape == "repeated_and_tray_only":
        draft = next(n for n in original["nodes"] if n["id"] == "a")["data"]["generationDraft"]
        draft["parts"].insert(2, deepcopy(draft["parts"][1]))
        draft["parts"] = [p for p in draft["parts"]
            if p.get("object_id") != draft["references"][1]["slotId"]]
    packet, data, registry, artifacts = prepare_canvas_project_data(
        inspection=inspect_canvas_source(original, definition["selection"]), definition=definition, data_root=root)
    # Existing fixture's original raw source is identical except observed batch
    # history: approve the exact new source through the canonical revision seam.
    service.packet, service.direction = packet, data
    service.revise_authoring(attempt_id="example-revision", registry=registry, asset_artifacts=artifacts)
    target = service.targets[0]
    output = target.output_requirement.model_copy(update={"duration_seconds": 15, "width": 864, "height": 496,
        "timing_mode": "nominal_seconds", "resolution_label": "480p"})
    service.targets = (RegisteredGenerationTarget(target.provider, target.profile, target.compiler_contract, output),)
    activate_fixture_generation_qa_policy(root=service.committer.project_root,
        inputs=LoadedFixture(service._load()), output=output)
    prepared = service.prepare(limits=limits)
    assert prepared.execution_binding is not None, prepared.decision
    assert prepared.compilation.request.output_requirement.timing_mode == "nominal_seconds"
    assert prepared.compilation.request.output_requirement.duration_seconds == 15
    assert prepared.compilation.request.prompt_text == data["shots"][0]["shot"]["intent"]
    assert len(prepared.compilation.request.image_bindings) == 3
