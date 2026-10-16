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


def test_preflight_reports_reference_bytes_measurements_and_unresolved_control_evidence(
    tmp_path, monkeypatch
):
    from ai_video.canvas_preflight import canvas_reference_preflight
    from ai_video.production.registry import registry_semantic_sha256
    from test_canvas_source_expression import local_video_source_fixture, subject_source

    packet, data, image_registry, _ = subject_source(
        tmp_path, duplicate_room_png=True,
        scenario=("Courier", "sets a parcel down", "a station platform"),
    )
    _, _, _, video_registry, _ = local_video_source_fixture(tmp_path, monkeypatch)
    combined = image_registry.model_copy(update={
        "assets": (*image_registry.assets, *video_registry.assets)
    })
    registry_hash = registry_semantic_sha256(combined)
    combined = combined.model_copy(update={"revision_id": registry_hash, "content_hash": registry_hash})

    row = data["shots"][0]
    for reference in row["generation"]["references"]:
        reference["owner_id"] = "robot" if reference["role"] == "character_reference" else "road"
    row["generation"]["references"].append({
        "role": "existing_video", "asset_id": "guide-video", "owner_id": "road"
    })
    row["composition"] = {"trim_start_frame": 4, "trim_end_frame": 60}
    row["generation"]["output_need"] = {
        "duration_seconds": 7, "width": 1280, "height": 720, "fps": 24
    }

    report = canvas_reference_preflight(packet=packet, direction=data, registry=combined)
    shot = report["shots"][0]
    inventory = shot.get("reference_inventory", {})
    assert inventory.get("semantic_binding_count") == 4
    assert inventory["unique_exact_byte_count"] == 3
    duplicate = inventory["duplicate_byte_groups"]
    assert len(duplicate) == 1
    assert {(item["asset_id"], item["role"], item["owner_id"])
            for item in duplicate[0]["bindings"]} == {
                ("robot-main", "character_reference", "robot"),
                ("room", "scene_reference", "road"),
            }
    image_references = [item for item in shot["references"]
                        if item.get("identity", {}).get("mime_type") == "image/png"]
    assert len({(item["identity"]["sha256"], item["identity"]["size_bytes"])
                for item in image_references}) == 2
    assert "character_count" not in duplicate[0]
    assert duplicate[0]["mime_type"] == "image/png"

    image = next(item for item in shot["references"] if item["asset_id"] == "robot-main")
    video = next(item for item in shot["references"] if item["asset_id"] == "guide-video")
    assert image["owner_id"] == "robot"
    assert image["measurements"]["width"] == 320
    assert image["measurements"]["height"] == 320
    assert video["measurements"]["width"] == 960
    assert video["measurements"]["height"] == 540
    assert video["measurements"]["duration_seconds"] == 4
    assert video["measurements"]["duration_milliseconds"] == 4000
    assert video["measurements"]["fps"] == {"numerator": 24, "denominator": 1}
    assert video["measurements"]["frame_count"] == 96
    assert shot["composition"] == {"trim_start_frame": 4, "trim_end_frame": 60}
    assert shot["requested_duration_seconds"] == 7
    assert shot["selected_route"] == "NOT_EVALUATED"
    assert shot["independent_character_evidence"] == "NOT_EVALUATED"
    assert shot["whitebox_reference"]["purpose_validation"] == "NOT_EVALUATED"
    assert shot["whitebox_reference"]["timing_validation"] == "NOT_EVALUATED"
    assert shot["whitebox_reference"]["candidate_video_asset_ids"] == ["guide-video"]


def test_preflight_does_not_instantiate_runtime_factory_or_write_state(tmp_path, monkeypatch):
    from scripts.canvas_production import run

    source, definition = text_data()
    (tmp_path / "source.json").write_text(json.dumps(source))
    path = tmp_path / "data.json"
    path.write_text(json.dumps(definition))
    project_root = tmp_path / "production"
    project_root.mkdir()
    import scripts.canvas_production as canvas_cli
    monkeypatch.setattr(canvas_cli.importlib, "import_module",
        lambda *_: pytest.fail("preflight must not instantiate a runtime factory"))

    result = run(data_path=path, project_root=project_root, action="preflight",
        runtime_factory="forbidden:factory")

    assert result["production_acceptance"] == "NOT_EVALUATED"
    assert list(project_root.iterdir()) == []


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


def _video_project_data(tmp_path, *, video_asset_id="motion-guide", video_role="existing_video"):
    from test_canvas_assets import local_video_selection

    source = document()
    source["nodes"] = [node for node in source["nodes"] if node["id"] != "voice"]
    source["edges"] = [edge for edge in source["edges"] if edge["source"] != "voice"]
    source["nodes"].append({"id": "guide", "type": "video", "data": {
        "resourceId": "guide-resource",
        "resourceBatches": [{"id": "guide-import", "resourceIds": ["guide-resource"]}]}})
    for node in source["nodes"]:
        if node["id"] == "room":
            node["data"]["resourceBatches"] = [{"id": "room-import", "resourceIds": ["room-resource"]}]
        if node["id"] not in {"a", "b"}:
            continue
        draft = node["data"]["generationDraft"]
        node["data"]["resourceBatches"] = [{"id": node["id"] + "-import",
            "resourceIds": [node["data"]["resourceId"]]}]
        draft["references"] = [ref for ref in draft["references"] if ref["nodeId"] != "voice"]
        draft["parts"].append({"type": "extension", "extension_type": "node",
            "object_id": "guide-slot"})
        draft["references"].append({"slotId": "guide-slot", "nodeId": "guide", "role": "reference"})
        source["edges"].append({"id": "guide-" + node["id"], "source": "guide",
            "target": node["id"], "type": "reference"})

    data = direction()
    for row in data["shots"]:
        row["shot"].pop("intent")
        row["generation"] = {"references": [
            {"asset_id": "room", "role": "scene_reference"},
            {"asset_id": video_asset_id, "role": video_role},
        ]}
    png = tmp_path / "room.png"
    from tests.production_project_factory import _p7_png
    png.write_bytes(_p7_png(width=320, height=320, rgba=bytes((1, 2, 3, 255))))
    image_selection = [{"asset_id": "room", "node_id": "room", "resource_id": "room-resource",
        "path": png, "usage_license": "fixture-only"}]
    video = local_video_selection(tmp_path)
    video["asset_id"] = video_asset_id
    video["input_artifact_ids"] = []
    definition = {"schema_version": "canvas-project-data/1", "source": "source.json",
        "selection": {"node_ids": ["a", "b"]}, "direction": data,
        "images": [{**image_selection[0], "path": "room.png"}],
        "videos": [{**video, "path": video["path"].name}]}
    return source, definition, video["path"]


def test_local_video_reference_is_imported_authored_and_immutably_reopened(tmp_path, monkeypatch):
    from ai_video.production.project import load_production_project
    from ai_video.production.models import AssetType
    from test_canvas_assets import fake_local_video_probe

    fake_local_video_probe(monkeypatch)
    source, definition, video_path = _video_project_data(tmp_path)
    (tmp_path / "source.json").write_text(json.dumps(source))
    inspection = inspect_canvas_source(source, definition["selection"])
    original_source = deepcopy(source)
    project_root = tmp_path / "project"
    project_root.mkdir()
    committer = ProductionStateCommitter(project_root)

    service, registry, artifacts = open_canvas_project(inspection=inspection, definition=definition,
        data_root=tmp_path, committer=committer, resume=False, ffprobe_executable="/usr/bin/ffprobe")
    bundle = service.author(registry=registry, asset_artifacts=artifacts)
    bundle.bootstrap(committer=committer, attempt_id="video-reference-author")
    loaded = load_production_project(project_root / "project.yaml")

    assert source == original_source
    assert loaded.registry.schema_version == "2.2"
    assert {asset.asset_type for asset in loaded.registry.assets} == {AssetType.IMAGE, AssetType.VIDEO}
    expression = service.direction["shots"][0]["shot"]["preserved_source_expression"]
    video_materials = [material for part in expression["parts"] if part["type"] == "reference"
        for material in part["materials"] if material["role"] == "video_reference"]
    assert [(item["asset_id"], item["asset_sha256"]) for item in video_materials] == [
        ("motion-guide", next(asset.sha256 for asset in loaded.registry.assets
                               if asset.asset_id == "motion-guide"))]
    assert service.direction["shots"][0]["shot"]["intent"].endswith("图片1视频1")
    assert service.packet["source_snapshot_sha256"] == inspection["source_snapshot_sha256"]
    assert [reference["slot_id"] for reference in service.packet["units"][0]["references"]] == [
        "room-slot", "guide-slot"]
    assert [part["text"] for part in expression["parts"] if part["type"] == "text"] == [
        "前段：生物遮满镜头。"]
    assert video_path.exists()

    video_path.unlink()
    import ai_video.canvas_video_assets as video_assets
    monkeypatch.setattr(video_assets, "_probe_canvas_mp4",
        lambda *_: pytest.fail("immutable reopen must not probe the original source file"))
    reopened, reopened_registry, reopened_artifacts = open_canvas_project(inspection=inspection,
        definition=definition, data_root=tmp_path, committer=committer)
    assert reopened.direction == service.direction
    assert reopened_registry == loaded.registry
    assert reopened_artifacts == ()


@pytest.mark.parametrize("damage", ["wrong_role", "ambiguous_role"])
def test_video_import_requires_explicit_probe_and_rejects_generation_role_mismatch(
    tmp_path, monkeypatch, damage
):
    from test_canvas_assets import fake_local_video_probe

    fake_local_video_probe(monkeypatch)
    source, definition, _ = _video_project_data(tmp_path)
    inspection = inspect_canvas_source(source, definition["selection"])
    project_root = tmp_path / "project"
    project_root.mkdir()
    committer = ProductionStateCommitter(project_root)
    with pytest.raises(ValueError, match="explicit absolute ffprobe"):
        open_canvas_project(inspection=inspection, definition=definition, data_root=tmp_path,
            committer=committer, resume=False)
    assert list(project_root.iterdir()) == []

    references = definition["direction"]["shots"][0]["generation"]["references"]
    if damage == "wrong_role":
        references[1]["role"] = "scene_reference"
    else:
        references.append(dict(references[1]))
    with pytest.raises(AiVideoError, match="existing_video role"):
        open_canvas_project(inspection=inspection, definition=definition,
            data_root=tmp_path, committer=committer, resume=False, ffprobe_executable="/usr/bin/ffprobe")
    assert list(project_root.iterdir()) == []


def test_video_and_image_registry_asset_id_collision_is_rejected(tmp_path, monkeypatch):
    from test_canvas_assets import fake_local_video_probe

    fake_local_video_probe(monkeypatch)
    source, definition, _ = _video_project_data(tmp_path, video_asset_id="room")
    project_root = tmp_path / "project"
    project_root.mkdir()
    with pytest.raises(ValueError, match="asset label collision"):
        open_canvas_project(inspection=inspect_canvas_source(source, definition["selection"]),
            definition=definition, data_root=tmp_path,
            committer=ProductionStateCommitter(project_root), resume=False,
            ffprobe_executable="/usr/bin/ffprobe")


def test_video_preflight_cli_passes_explicit_probe_without_loading_runtime(tmp_path, monkeypatch, capsys):
    from scripts.canvas_production import main
    from test_canvas_assets import fake_local_video_probe

    fake_local_video_probe(monkeypatch)
    source, definition, _ = _video_project_data(tmp_path)
    (tmp_path / "source.json").write_text(json.dumps(source))
    data_path = tmp_path / "project.json"
    data_path.write_text(json.dumps(definition))
    project_root = tmp_path / "production"
    project_root.mkdir()
    import scripts.canvas_production as canvas_cli
    monkeypatch.setattr(canvas_cli.importlib, "import_module",
        lambda *_: pytest.fail("video preflight must not instantiate a runtime factory"))

    result = main(["preflight", "--data", str(data_path), "--project-root", str(project_root),
        "--runtime", "forbidden:factory", "--ffprobe", "/usr/bin/ffprobe"])
    report = json.loads(capsys.readouterr().out)
    assert result == 0
    assert report["production_acceptance"] == "NOT_EVALUATED"
    assert any(reference["asset_id"] == "motion-guide" and
        reference["identity"]["mime_type"] == "video/mp4"
        for shot in report["shots"] for reference in shot["references"])
    assert list(project_root.iterdir()) == []


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
