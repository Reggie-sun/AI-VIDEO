"""Current authored parts replace historical instructions without rewriting by a compiler."""
from copy import deepcopy

import pytest

from ai_video.canvas_authoring import author_canvas_project
from ai_video.canvas_project_data import prepare_canvas_project_data
from ai_video.production.hashing import canonical_sha256
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from scripts.canvas_production_source import inspect_canvas_source
from test_canvas_project_data import text_data


def revision_fixture(tmp_path):
    source, definition = text_data()
    draft = next(n for n in source["nodes"] if n["id"] == "a")["data"]["generationDraft"]
    draft["parts"] = [
        {"type": "text", "text": "A passenger raises an empty left hand."},
        {"type": "text", "text": "Old photographic style; reference video lasts four seconds."},
    ]
    inspection = inspect_canvas_source(source, definition["selection"])
    packet, direction, registry, artifacts = prepare_canvas_project_data(
        inspection=inspection, definition=definition, data_root=tmp_path)
    bundle = author_canvas_project(packet=packet, direction=direction, registry=registry,
        asset_artifacts=artifacts)
    root = tmp_path / "production"
    root.mkdir()
    bundle.bootstrap(committer=ProductionStateCommitter(root), attempt_id="original-input")
    from ai_video.canvas_dependencies import initialize_canvas_graph
    initialize_canvas_graph(ProductionStateCommitter(root), "original-input-graph")
    previous = load_production_project(root / "project.yaml")
    original_parts = deepcopy(draft["parts"])
    current = {"type": "text", "text": "Current sculpted CG style; reference video lasts five seconds."}
    draft["parts"] = [original_parts[0], current]
    definition["direction"]["shots"][0]["source_revision"] = {
        "contract_version": "canvas-source-revision/1",
        "baseline_source_snapshot_sha256": packet["source_snapshot_sha256"],
        "baseline_prompt_parts_sha256": canonical_sha256({"parts": original_parts}),
        "baseline_effective_prompt_sha256": canonical_sha256({"intent": direction["shots"][0]["shot"]["intent"],
            "preserved_source_expression": direction["shots"][0]["shot"].get("preserved_source_expression")}),
        "reason": "The user replaced the visual style and the motion guide.",
        "sections": [
            {"section_id": "story-action", "parts": [original_parts[0]]},
            {"section_id": "visual-and-reference-direction", "parts": [current]},
        ],
        "dispositions": [
            {"part_index": 0, "part_sha256": canonical_sha256(original_parts[0]),
             "disposition": "retained", "reason": "Keep the original action."},
            {"part_index": 1, "part_sha256": canonical_sha256(original_parts[1]),
             "disposition": "superseded", "reason": "Replace the old style and guide description."},
        ],
    }
    return source, definition, previous, original_parts


def prepare_revision(source, definition, previous, tmp_path):
    packet, direction, registry, artifacts = prepare_canvas_project_data(
        inspection=inspect_canvas_source(source, definition["selection"]),
        definition=definition, data_root=tmp_path)
    return author_canvas_project(packet=packet, direction=direction, registry=registry,
        asset_artifacts=artifacts, previous=previous)


def test_complete_current_sections_replace_old_input_and_preserve_canonical_history(tmp_path):
    source, definition, previous, original = revision_fixture(tmp_path)
    before = (previous.root / "state/manifest.json").read_bytes()

    bundle = prepare_revision(source, definition, previous, tmp_path)

    shot = next(s for s in bundle.creative_artifacts if getattr(s, "shot_id", None) == "one")
    assert shot.intent == ("A passenger raises an empty left hand."
        "Current sculpted CG style; reference video lasts five seconds.")
    assert "four seconds" not in shot.intent and "Old photographic" not in shot.intent
    assert [p.text for p in shot.preserved_source_expression.parts] == [original[0]["text"],
        "Current sculpted CG style; reference video lasts five seconds."]
    assert previous.shots[0].intent.endswith("reference video lasts four seconds.")
    assert (previous.root / "state/manifest.json").read_bytes() == before


def test_revision_reopens_and_reauthors_exactly_after_canonical_commit(tmp_path):
    from ai_video.canvas_production import CanvasProductionService

    source, definition, previous, _ = revision_fixture(tmp_path)
    packet, direction, registry, artifacts = prepare_canvas_project_data(
        inspection=inspect_canvas_source(source, definition["selection"]),
        definition=definition, data_root=tmp_path)
    service = CanvasProductionService(committer=ProductionStateCommitter(previous.root),
        packet=packet, direction=direction)
    service.revise_authoring(attempt_id="current-input", registry=registry, asset_artifacts=artifacts)
    loaded = service._load()
    before = (previous.root / "state/manifest.json").read_bytes()
    reauthored = service.author(registry=registry)
    assert reauthored.project.artifacts.shots == loaded.project.artifacts.shots
    assert loaded.shots[0].intent.endswith("reference video lasts five seconds.")
    assert service.revise_authoring(attempt_id="exact-replay", registry=registry) == loaded.manifest
    assert (previous.root / "state/manifest.json").read_bytes() == before
    changed = deepcopy(service.direction)
    changed["shots"][0]["shot"]["intent"] += " Reused revision with a different effective prompt."
    changed["shots"][0]["shot"].pop("preserved_source_expression")
    with pytest.raises(ValueError, match="source revision baseline"):
        author_canvas_project(packet=packet, direction=changed, registry=registry, previous=loaded)
    assert (previous.root / "state/manifest.json").read_bytes() == before
    service.direction["shots"][0].pop("source_revision")
    with pytest.raises(ValueError, match="source revision declaration cannot be discarded"):
        author_canvas_project(packet=packet, direction=service.direction,
            registry=registry, previous=loaded)


def test_changed_style_input_requires_revision_inventory(tmp_path):
    source, definition, previous, _ = revision_fixture(tmp_path)
    row = definition["direction"]["shots"][0]
    row.pop("source_revision")
    row["visual_style"] = {}  # Revision must be checked before style/schema approval.
    with pytest.raises(ValueError, match="source revision required"):
        prepare_revision(source, definition, previous, tmp_path)


def test_changed_legacy_canvas_prompt_requires_explicit_revision(tmp_path):
    source, definition, previous, _ = revision_fixture(tmp_path)
    definition["direction"]["shots"][0].pop("source_revision")
    with pytest.raises(ValueError, match="source revision required"):
        prepare_revision(source, definition, previous, tmp_path)


def test_revision_baseline_follows_shot_identity_when_canvas_node_is_renamed(tmp_path):
    source, definition, previous, _ = revision_fixture(tmp_path)
    next(n for n in source["nodes"] if n["id"] == "a")["id"] = "renamed-a"
    definition["selection"]["node_ids"][0] = "renamed-a"
    definition["direction"]["shots"][0]["occurrence_id"] = "renamed-a"
    bundle = prepare_revision(source, definition, previous, tmp_path)
    shot = next(s for s in bundle.creative_artifacts if getattr(s, "shot_id", None) == "one")
    assert "five seconds" in shot.intent and "four seconds" not in shot.intent


@pytest.mark.parametrize("change", ["intent", "expression", "both"])
def test_effective_prompt_cannot_change_without_revision(tmp_path, change):
    from ai_video.canvas_source_revision import _previous_director

    _, _, previous, _ = revision_fixture(tmp_path)
    baseline = _previous_director(previous)
    row = baseline["direction"]["shots"][0]
    if change in {"intent", "both"}:
        row["shot"]["intent"] += " Appended camera and old style instructions."
    if change in {"expression", "both"}:
        row["shot"].pop("preserved_source_expression")
    before = (previous.root / "state/manifest.json").read_bytes()
    with pytest.raises(ValueError, match="source revision required"):
        author_canvas_project(packet=baseline["packet"], direction=baseline["direction"],
            registry=previous.registry, previous=previous)
    if change == "both":
        from ai_video.canvas_production import CanvasProductionService
        from ai_video.errors import AiVideoError
        service = CanvasProductionService(committer=ProductionStateCommitter(previous.root),
            packet=baseline["packet"], direction=baseline["direction"])
        with pytest.raises(AiVideoError, match="source revision required"):
            service.revise_authoring(attempt_id="undeclared-effective-prompt", registry=previous.registry)
    assert (previous.root / "state/manifest.json").read_bytes() == before


def test_observed_prompt_without_parts_requires_revision(tmp_path):
    from scripts.canvas_reference_packet import build_packet
    from scripts.canvas_sequence_packet import build_sequence_packet
    from test_canvas_reference_packet import fixture
    from test_canvas_authoring import direction as director

    graph, composers = fixture()
    composers["results"][0]["parameters"] = {"durationSeconds": 15, "aspectRatio": "16:9"}
    packet = build_sequence_packet(build_packet(graph, composers), {"node_ids": ["shot"]})
    direction = director()
    direction["shots"] = [direction["shots"][0]]
    direction["shots"][0]["occurrence_id"] = "shot"
    direction["storyboard"]["beats"][0]["shot_ids"] = ["one"]
    bundle = author_canvas_project(packet=packet, direction=direction)
    root = tmp_path / "production"
    root.mkdir()
    bundle.bootstrap(committer=ProductionStateCommitter(root), attempt_id="observed-original")
    previous = load_production_project(root / "project.yaml")
    composers["results"][0]["prompt"] += " New current style."
    changed = build_sequence_packet(build_packet(graph, composers), {"node_ids": ["shot"]})
    assert "parts" not in changed["units"][0]["prompt_source"]
    before = (root / "state/manifest.json").read_bytes()
    with pytest.raises(ValueError, match="source revision required"):
        author_canvas_project(packet=changed, direction=direction,
            registry=previous.registry, previous=previous)
    assert (root / "state/manifest.json").read_bytes() == before

    old_part = {"type": "text", "text": packet["units"][0]["source_text"]}
    old_shot = deepcopy(direction["shots"][0]["shot"])
    composers["results"][0]["prompt"] = "Current sculpted CG style; preserve the action."
    changed = build_sequence_packet(build_packet(graph, composers), {"node_ids": ["shot"]})
    current_part = {"type": "text", "text": changed["units"][0]["source_text"]}
    direction["shots"][0]["shot"]["intent"] = current_part["text"]
    direction["shots"][0]["source_revision"] = {
        "contract_version": "canvas-source-revision/1",
        "baseline_source_snapshot_sha256": packet["source_snapshot_sha256"],
        "baseline_prompt_parts_sha256": canonical_sha256({"parts": [old_part]}),
        "baseline_effective_prompt_sha256": canonical_sha256({"intent": old_shot["intent"],
            "preserved_source_expression": old_shot.get("preserved_source_expression")}),
        "reason": "Explicitly replace the observed prose and director prompt.",
        "sections": [{"section_id": "current-observed-prose", "parts": [current_part]}],
        "dispositions": [{"part_index": 0, "part_sha256": canonical_sha256(old_part),
            "disposition": "superseded", "reason": "Replace the old prose completely."}],
    }
    revised = author_canvas_project(packet=changed, direction=direction,
        registry=previous.registry, previous=previous)
    shot = next(s for s in revised.creative_artifacts if getattr(s, "shot_id", None) == "one")
    assert shot.intent == current_part["text"]
    assert (root / "state/manifest.json").read_bytes() == before


@pytest.mark.parametrize("path", ["intent", "structured_intent"])
def test_superseded_raw_history_cannot_return_through_effective_intent(tmp_path, path):
    source, definition, previous, original = revision_fixture(tmp_path)
    packet, direction, registry, artifacts = prepare_canvas_project_data(
        inspection=inspect_canvas_source(source, definition["selection"]),
        definition=definition, data_root=tmp_path)
    row = direction["shots"][0]
    row["shot"].pop("preserved_source_expression")
    if path == "intent":
        row["shot"]["intent"] += original[1]["text"]
    else:
        row.setdefault("generation", {})["generation_intent"] = {
            "subject_action": {"progression": original[1]["text"]}}
    before = (previous.root / "state/manifest.json").read_bytes()
    with pytest.raises(ValueError, match="superseded history"):
        author_canvas_project(packet=packet, direction=direction, registry=registry,
            asset_artifacts=artifacts, previous=previous)
    assert (previous.root / "state/manifest.json").read_bytes() == before


@pytest.mark.parametrize("field", ["progression", "performance"])
def test_structured_native_prompt_change_requires_revision(tmp_path, field):
    from ai_video.canvas_production import CanvasProductionService
    from ai_video.errors import AiVideoError
    from ai_video.production.video_requirement import GenerationIntent
    from test_canvas_production import runtime

    service, provider, _, _ = runtime(tmp_path)
    previous = service._load()
    changed = deepcopy(service.direction)
    intent = changed["shots"][0]["generation"]["generation_intent"]
    if field == "progression":
        intent["subject_action"]["progression"] = "Keep old style and add a second action."
    else:
        intent["performance_intent"] = {"trigger": "A light flickers", "visible_response": "Turn slowly",
            "gaze_target": "The far door", "body_behavior": "Stand still", "hand_behavior": "Empty hands",
            "terminal_performance_state": "Facing the far door"}
    GenerationIntent.model_validate(intent)
    before = (previous.root / "state/manifest.json").read_bytes()
    with pytest.raises(ValueError, match="source revision required"):
        author_canvas_project(packet=service.packet, direction=changed,
            registry=previous.registry, previous=previous)
    revised = CanvasProductionService(committer=service.committer, packet=service.packet, direction=changed)
    with pytest.raises(AiVideoError, match="source revision required"):
        revised.revise_authoring(attempt_id="undeclared-structured-prompt", registry=previous.registry)
    assert (previous.root / "state/manifest.json").read_bytes() == before
    assert provider.call_counts.submit == 0
    from ai_video.canvas_source_revision import retained_source_revision
    changed["shots"][0]["source_revision"] = retained_source_revision(previous=previous,
        packet=service.packet, row=changed["shots"][0], reason="Explicit structured performance/action revision.")
    revised.direction = deepcopy(changed)
    revised.revise_authoring(attempt_id="declared-structured-prompt", registry=previous.registry)
    approved = revised._load()
    before = (previous.root / "state/manifest.json").read_bytes()
    assert revised.revise_authoring(attempt_id="declared-structured-replay") == approved.manifest
    revised.direction["shots"][0]["generation"]["generation_intent"]["subject_action"]["progression"] += " Another edit."
    with pytest.raises(AiVideoError, match="source revision baseline effective prompt"):
        revised.revise_authoring(attempt_id="reused-structured-revision")
    assert (previous.root / "state/manifest.json").read_bytes() == before
    assert provider.call_counts.submit == 0


@pytest.mark.parametrize("damage", ["baseline", "effective_hash", "part_hash", "missing_decision", "duplicate_section",
    "stale_history", "section_drift", "retained_removed", "unknown_field"])
def test_revision_rejects_stale_or_incomplete_current_input_before_writes(tmp_path, damage):
    source, definition, previous, original = revision_fixture(tmp_path)
    revision = definition["direction"]["shots"][0]["source_revision"]
    draft = next(n for n in source["nodes"] if n["id"] == "a")["data"]["generationDraft"]
    if damage == "baseline":
        revision["baseline_source_snapshot_sha256"] = "f" * 64
    elif damage == "effective_hash":
        revision["baseline_effective_prompt_sha256"] = "f" * 64
    elif damage == "part_hash":
        revision["dispositions"][1]["part_sha256"] = "f" * 64
    elif damage == "missing_decision":
        revision["dispositions"].pop()
    elif damage == "duplicate_section":
        revision["sections"][1]["section_id"] = "story-action"
    elif damage == "stale_history":
        draft["parts"].append(original[1])
        revision["sections"].append({"section_id": "old-instructions", "parts": [original[1]]})
    elif damage == "section_drift":
        draft["parts"].append({"type": "text", "text": "Undeclared appended history."})
    elif damage == "retained_removed":
        draft["parts"].pop(0)
        revision["sections"].pop(0)
    else:
        revision["implicitly_approved"] = True
    before = (previous.root / "state/manifest.json").read_bytes()
    with pytest.raises(ValueError, match="source revision"):
        prepare_revision(source, definition, previous, tmp_path)
    assert (previous.root / "state/manifest.json").read_bytes() == before
