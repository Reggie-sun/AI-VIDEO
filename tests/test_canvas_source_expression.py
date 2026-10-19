"""Authoring cannot relabel invented prose as preserved canvas source."""
from copy import deepcopy
from dataclasses import dataclass

import pytest

from ai_video.canvas_authoring import author_canvas_project
from ai_video.production.hashing import canonical_sha256
from test_canvas_authoring import direction
from test_canvas_sequence_packet import document
from scripts.canvas_sequence_packet import build_sequence_packet


@pytest.mark.parametrize("damage", [None, "text", "parts", "slot"])
def test_original_canvas_parts_are_reopened_at_authoring(damage):
    raw = document()
    raw["edges"] = []
    for node in raw["nodes"]:
        draft = node["data"].get("generationDraft")
        if draft is not None:
            draft["parts"] = [p for p in draft["parts"] if p["type"] == "text"]
            draft["references"] = []
    source, data = build_sequence_packet(raw, {"node_ids": ["a", "b"]}), direction()
    parts = source["units"][0]["prompt_source"]["parts"]
    expression_parts = deepcopy(parts)
    if damage == "text":
        expression_parts[0]["text"] += " invented action"
    elif damage == "parts":
        expression_parts.append({"type": "text", "text": " extra"})
    elif damage == "slot":
        expression_parts[0] = {"type": "reference", "slot_id": "invented", "materials": [
            {"asset_id": "invented", "asset_sha256": "b" * 64, "role": "identity"}]}
    data["shots"][0]["shot"]["preserved_source_expression"] = {
        "source_sha256": canonical_sha256({"parts": expression_parts, "implicit_references": []}),
        "parts": expression_parts}
    if damage is None:
        assert author_canvas_project(packet=source, direction=data).creative_artifacts
    else:
        with pytest.raises(ValueError):
            author_canvas_project(packet=source, direction=data)


def subject_source(tmp_path, *, scene_auxiliary=False, generated=False,
                   duplicate_room_png=False, scenario=None, authored_deadline_text=None,
                   adopted_duration_seconds=5, generation_output_duration_seconds=None,
                   generation_output_geometry_policy="exact", adopted_composition=None, author_performance=False):
    """Inspect/import real fixture bytes before canonical authoring and planning."""
    from ai_video.canvas_assets import prepare_canvas_png_assets
    from tests.production_project_factory import _p7_png

    character, action, space = scenario or ("Robot", "lifts its hands", "")
    performance = None
    performance_text = ""
    if author_performance:
        from types import SimpleNamespace
        from performance_fixture import fixture_performance_intent
        from ai_video.production.performance_direction import render_performance_direction

        performance = fixture_performance_intent((SimpleNamespace(character_id="robot", name=character),),
            trigger="the authored action begins", emotion="quiet attention",
            facial_expression=("rigid face remains unchanged; eye lights stay steady" if character == "Robot"
                               else "eyes remain attentive with an unforced neutral mouth"),
            gaze_target="the authored action target", breathing=("no biological breathing on the metal body"
                if character == "Robot" else "gentle breathing consistent with the posture"),
            body_behavior="natural balance during the authored action")
        performance_text = " " + " ".join(dict.fromkeys(getattr(performance, name) for name in (
            "trigger", "visible_response", "gaze_target", "body_behavior", "hand_behavior",
            "terminal_performance_state"))) + ". " + render_performance_direction(performance)
    raw = document()
    raw["edges"] = []
    raw["nodes"].append({"id": "robot", "type": "subject", "data": {
        "main": {"refType": "resource_snapshot", "resourceId": "robot-main"},
        "auxiliaries": [{"refType": "resource_snapshot", "resourceId": "robot-aux"}]}})
    for node in raw["nodes"]:
        draft = node["data"].get("generationDraft")
        if draft is None:
            continue
        draft["parts"] = [{"type": "text", "text": character + " "},
            {"type": "extension", "extension_type": "subject", "object_id": "robot-slot"},
            {"type": "text", "text": f" {action} in {space + ' ' if scenario else ''}"},
            {"type": "extension", "extension_type": "node", "object_id": "room-slot"},
            {"type": "text", "text": "."}]
        if performance_text:
            draft["parts"].append({"type": "text", "text": performance_text})
        if authored_deadline_text is not None:
            draft["parts"].append({"type": "text", "text": " " + authored_deadline_text})
        draft["references"] = [{"slotId": "robot-slot", "nodeId": "robot", "role": "reference",
            "type": "extension", "extensionType": "subject", "sourceInstanceId": "robot"},
            {"slotId": "room-slot", "nodeId": "room", "role": "reference"}]
        raw["edges"].append({"id": "robot-" + node["id"], "source": "robot",
                             "target": node["id"], "type": "reference"})
        raw["edges"].append({"id": "room-" + node["id"], "source": "room",
                             "target": node["id"], "type": "reference"})
    source = build_sequence_packet(raw, {"node_ids": ["a", "b"]})
    selections = []
    for index, asset_id in enumerate(("robot-main", "robot-aux", "room")):
        path = tmp_path / f"{asset_id}.png"
        if duplicate_room_png and asset_id == "room":
            path.write_bytes((tmp_path / "robot-main.png").read_bytes())
        else:
            path.write_bytes(_p7_png(width=320, height=320, rgba=bytes((index, 32, 48, 255))))
        selections.append({"asset_id": asset_id, "node_id": "room" if asset_id == "room" else "robot",
                           "resource_id": "room-resource" if asset_id == "room" else asset_id,
                           "path": path, "usage_license": "fixture-only"})
        if generated and asset_id == "robot-main":
            import hashlib
            import json
            raw_image = path.read_bytes()
            record = tmp_path / "generated-source.json"
            record.write_text(json.dumps({"sha256": hashlib.sha256(raw_image).hexdigest(),
                "size_bytes": len(raw_image), "width": 320, "height": 320}))
            selections[-1]["generated_source"] = {"record_path": record.name,
                "record_sha256": hashlib.sha256(record.read_bytes()).hexdigest(),
                "tool": {"name": "external-image-tool", "version": "not-recorded"}}
    registry, artifacts = prepare_canvas_png_assets(packet=source, selections=selections,
                                                   allowed_asset_root=tmp_path)
    materials = [{"asset_id": a.asset_id, "asset_sha256": a.sha256,
                  "role": "scene" if scene_auxiliary and a.asset_id == "robot-aux" else "identity"}
                 for asset_id in ("robot-main", "robot-aux")
                 for a in registry.assets if a.asset_id == asset_id]
    parts = [{"type": "text", "text": character + " "},
        {"type": "reference", "slot_id": "robot-slot", "materials": materials},
        {"type": "text", "text": f" {action} in {space + ' ' if scenario else ''}"},
        {"type": "reference", "slot_id": "room-slot", "materials": [
            {"asset_id": "room", "asset_sha256": next(a.sha256 for a in registry.assets if a.asset_id == "room"),
             "role": "scene"}]}, {"type": "text", "text": "."}]
    if performance_text:
        parts.append({"type": "text", "text": performance_text})
    if authored_deadline_text is not None:
        parts.append({"type": "text", "text": " " + authored_deadline_text})
    data = direction()
    data["delivery_profile"] = {"width": 1280, "height": 720, "fps": 24}
    if scenario:
        data["scenes"][0]["location"] = space
    data["characters"] = [{"character_id": "robot", "name": character, "identity": character,
        "appearance_bible": "Metal body", "reference_asset_ids": [m["asset_id"] for m in materials
                                                                  if m["role"] == "identity"]}]
    data["scenes"][0]["visual_reference_asset_ids"] = ["room", *[m["asset_id"] for m in materials
                                                      if m["role"] == "scene"]]
    for row in data["shots"]:
        authored_prompt = f"{character} 图片2、图片1 {action} in 图片3."
        if scenario:
            authored_prompt = f"{character} 图片2、图片1 {action} in {space} 图片3."
        authored_prompt += performance_text
        if authored_deadline_text is not None:
            authored_prompt += " " + authored_deadline_text
        row["shot"].update(intent=authored_prompt, character_ids=["robot"],
            duration_policy={"mode": "fixed", "seconds": adopted_duration_seconds}, preserved_source_expression={
                "source_sha256": canonical_sha256({"parts": parts, "implicit_references": []}),
                "parts": parts})
        if adopted_composition is not None:
            row["composition"] = dict(adopted_composition)
        row["generation"] = {"references": [{"role": "scene_reference" if m["role"] == "scene"
            else "character_reference", "asset_id": m["asset_id"]} for m in materials] + [
                {"role": "scene_reference", "asset_id": "room"}],
            "intent_evidence": {"character_action_required": True},
            "generation_intent": {"subject_action": {"progression": row["shot"]["intent"]},
                                  "pacing": {"shot_duration_seconds": (
                                      5 if generation_output_duration_seconds is None
                                      else generation_output_duration_seconds)}},
            "audio_need": "required", "quality_need": {}}
        if performance is not None:
            row["generation"]["generation_intent"]["performance_intent"] = performance.model_dump(mode="json")
        if generation_output_duration_seconds is not None:
            output_need = {"duration_seconds": generation_output_duration_seconds,
                "geometry_policy": generation_output_geometry_policy, "fps": 24,
                "container_mime": "video/mp4"}
            if generation_output_geometry_policy == "exact":
                output_need.update(width=1280, height=720)
            row["generation"]["output_need"] = output_need
    return source, data, registry, artifacts


@pytest.mark.parametrize("scenario", [
    ("Robot", "raises both arms", "an atrium"),
    ("Courier", "sets a parcel down", "a station platform"),
    ("Scientist", "turns toward the window", "a narrow cabin"),
])
def test_canvas_prompt_keeps_character_action_space_and_distinct_duplicate_byte_roles(
    tmp_path, scenario
):
    from ai_video.canvas_source_expression import adapted_canvas_prompt

    source, data, registry, _ = subject_source(
        tmp_path, duplicate_room_png=True, scenario=scenario
    )
    source_text_parts = [part["text"] for part in source["units"][0]["prompt_source"]["parts"]
                         if part["type"] == "text"]
    assert source_text_parts == [scenario[0] + " ",
        f" {scenario[1]} in {scenario[2]} ", "."]
    expression = data["shots"][0]["shot"]["preserved_source_expression"]
    prompt = adapted_canvas_prompt(expression)
    robot = next(asset for asset in registry.assets if asset.asset_id == "robot-main")
    room = next(asset for asset in registry.assets if asset.asset_id == "room")
    assert (robot.sha256, robot.size_bytes) == (room.sha256, room.size_bytes)
    assert prompt == f"{scenario[0]} 图片2、图片1 {scenario[1]} in {scenario[2]} 图片3."
    referenced = [material for part in expression["parts"] if part["type"] == "reference"
                  for material in part["materials"]]
    assert [(item["asset_id"], item["role"]) for item in referenced] == [
        ("robot-main", "identity"), ("robot-aux", "identity"), ("room", "scene")]


@dataclass(frozen=True)
class LoadedFixture:
    project: object


def subject_service(tmp_path, *, generated=False, scenario=None, authored_deadline_text=None,
                    adopted_duration_seconds=5, generation_output_duration_seconds=None,
                    adopted_composition=None, provider_family="seedance"):
    from ai_video.canvas_dependencies import initialize_canvas_graph
    from ai_video.canvas_production import CanvasProductionService
    from ai_video.production.generation_decision import DecisionPolicy, ExecutionLimits
    from ai_video.production.generation_feedback import RegisteredGenerationTarget
    from ai_video.production.project import load_production_project
    from ai_video.production.shot_router import AdapterCompilerContract
    from ai_video.production.state_commit import ProductionStateCommitter
    from tests.production_generation_execution_factory import activate_fixture_generation_qa_policy
    from test_production_seedance import _profile, _profile_pointer, _request
    from test_production_shot_router import _policy

    source, data, registry, artifacts = subject_source(tmp_path, generated=generated,
        scenario=scenario, authored_deadline_text=authored_deadline_text,
        adopted_duration_seconds=adopted_duration_seconds,
        generation_output_duration_seconds=generation_output_duration_seconds,
        generation_output_geometry_policy=("adaptive" if provider_family == "h3-max" else "exact"),
        adopted_composition=adopted_composition, author_performance=True)
    root = tmp_path / "project"
    root.mkdir()
    def forbidden(*args, **kwargs):
        pytest.fail("source-boundary tests must not use Provider effects or credentials")
    if provider_family == "seedance":
        from ai_video.production.seedance import SeedanceVideoProvider

        profile = _profile()
        model = "doubao-seedance-2-0-fast-260128"
        output = _request(profile, model_id=model).output_requirement.model_copy(
            update={"timing_mode": "nominal_seconds"})
        provider = SeedanceVideoProvider(profile=profile, transport=forbidden,
            credential=forbidden, input_reference=forbidden)
        provider_name = "seedance"
        profile_pointer = _profile_pointer(profile)
        compiler_id, compiler_version = "seedance-video-compiler", "3"
    elif provider_family == "h3-max":
        from ai_video.production.minimax_h3_max import (
            MINIMAX_H3_MAX_MODEL_ID, MiniMaxH3MaxProfile, MiniMaxH3MaxVideoProvider,
        )

        profile = MiniMaxH3MaxProfile(duration=5, resolution="768P", aspect_ratio="adaptive",
            currency="CNY", cost_upper_bound_microunits=1)
        model = MINIMAX_H3_MAX_MODEL_ID
        output = profile.output()
        provider = MiniMaxH3MaxVideoProvider(profile=profile, transport=forbidden,
            credential=forbidden, reference_resolver=forbidden)
        provider_name = "minimax_h3_max"
        profile_pointer = profile.pointer()
        compiler_id, compiler_version = "minimax-h3-max-video-compiler", "1"
    else:
        raise ValueError(f"unsupported source fixture provider family: {provider_family}")
    service = CanvasProductionService(committer=ProductionStateCommitter(root), packet=source,
        direction=data, targets=(RegisteredGenerationTarget(provider, profile_pointer,
            AdapterCompilerContract.create(compiler_id=compiler_id, compiler_version=compiler_version),
            output),), routing_policy=_policy(remote_authorized=True, budget_authorized=True),
        decision_policy=DecisionPolicy(allow_bounded_exploration=True))
    service.author(registry=registry, asset_artifacts=artifacts).bootstrap(
        committer=service.committer, attempt_id="source-bootstrap")
    initialize_canvas_graph(service.committer, "source-graph")
    loaded = load_production_project(root / "project.yaml")
    service.committer.upgrade_manifest_schema("2.14",
        expected_manifest_revision=loaded.manifest.manifest_revision)
    activate_fixture_generation_qa_policy(root=root,
        inputs=LoadedFixture(load_production_project(root / "project.yaml")), output=output)
    limits = ExecutionLimits(task_id="preserved-source-test", generation_forbidden=False,
        allowed_remote_candidates=tuple(f"{provider_name}/{v.capability_id}"
                                        for v in provider.capabilities().variants
                                        if v.model_id == model), paid_submit_ceiling=1, paid_submits_used=0,
        local_batch_limit=1, local_batch_used=0, local_total_used=0, local_resource_available=True)
    return service, limits


def test_generated_copy_retains_original_subject_binding_and_revision(tmp_path):
    service, limits = subject_service(tmp_path, generated=True)
    before = service._load()
    assert service.prepare(limits=limits).execution_binding is not None
    service.direction["title"] = "Generated source retained"
    service.revise_authoring(attempt_id="generated-source-title")
    after = service._load()
    assert after.registry == before.registry and after.shots == before.shots
    assert all(r in after.project.source_provenance for r in before.project.source_provenance
               if r.reference.startswith("evidence/authoring-input/"))
    assert service.prepare(limits=limits).execution_binding is not None


@pytest.mark.parametrize("damage", ["missing", "bytes", "node_id", "resource_id", "sha256", "record"])
def test_generated_copy_cannot_replace_original_binding_with_resealed_evidence(tmp_path, damage):
    import hashlib
    import json
    from pathlib import Path
    from ai_video.production.authoring_input import authoring_input_reference, authoring_input_payload
    from ai_video.production.registry import registry_semantic_sha256
    from ai_video.production.state_commit import PreparedArtifact
    source, data, registry, artifacts = subject_source(tmp_path, generated=True)
    asset = next(a for a in registry.assets if a.asset_id == "robot-main")
    path = Path(f"evidence/authoring-input/{asset.input_fingerprint}.json")
    artifact = next(a for a in artifacts if a.relative_path == path)
    changed = [a for a in artifacts if a != artifact]
    if damage == "bytes":
        changed.append(PreparedArtifact(path, artifact.payload + b" ", artifact.file_sha256))
    elif damage != "missing":
        value = json.loads(artifact.payload)
        if damage == "record":
            record_artifact = next(a for a in artifacts
                if str(a.relative_path) == value["generated_source"]["record_path"])
            wrapper = json.loads(record_artifact.payload)
            record = json.loads(wrapper["record_utf8"])
            record["width"] += 1
            wrapper["record_utf8"] = json.dumps(record)
            wrapper["record_sha256"] = hashlib.sha256(wrapper["record_utf8"].encode()).hexdigest()
            ref = authoring_input_reference(wrapper)
            payload = authoring_input_payload(wrapper)
            changed = [a for a in changed if a != record_artifact]
            changed.append(PreparedArtifact(Path(ref.reference), payload, hashlib.sha256(payload).hexdigest()))
            value["generated_source"].update(record_path=ref.reference, record_sha256=wrapper["record_sha256"])
        else:
            value[damage] = "wrong-resource" if damage != "sha256" else "b" * 64
        ref = authoring_input_reference(value)
        payload = authoring_input_payload(value)
        changed.append(PreparedArtifact(Path(ref.reference), payload, hashlib.sha256(payload).hexdigest()))
        replacement = asset.model_copy(update={"input_fingerprint": ref.content_hash,
            "creation_receipt_id": f"canvas-generated-image-source:{ref.content_hash}"})
        registry = registry.model_copy(update={"assets": tuple(replacement if a == asset else a
                                                               for a in registry.assets)})
        digest = registry_semantic_sha256(registry)
        registry = registry.model_copy(update={"revision_id": digest, "content_hash": digest})
    with pytest.raises(ValueError):
        author_canvas_project(packet=source, direction=data, registry=registry, asset_artifacts=tuple(changed))


def test_subject_materials_have_character_owners_through_real_common_compiler(tmp_path):
    service, limits = subject_service(tmp_path)
    prepared = service.prepare(limits=limits)
    assert prepared.execution_binding is not None
    assert prepared.resolved_request.prompt_text == service.direction["shots"][0]["shot"]["intent"]
    requirement = prepared.execution_binding.projection.requirement
    assert {e.role.value for e in requirement.asset_evidence if e.asset_id.startswith("robot-")} == {"identity"}
    bound = prepared.execution_binding.decision.routing.provider_bound_request
    assert {a.canonical_owner_kind for a in bound.input_assets if a.asset_id.startswith("robot-")} == {"character"}
    assert {a.canonical_owner_id for a in bound.input_assets if a.asset_id.startswith("robot-")} == {"robot"}
    assert {b.asset_id for b in prepared.resolved_request.image_bindings} == {"robot-main", "robot-aux", "room"}
    prepared.execution_binding.validate_current_project(service._load())
    from ai_video.production.video_generation import VideoGenerationService
    VideoGenerationService(committer=service.committer, provider=prepared.provider).start(
        attempt_id="unchanged-source", request=prepared.resolved_request,
        execution_binding=prepared.execution_binding)
    assert service._load().manifest.attempts[-1].video_generation_state.execution_binding.binding_hash == (
        prepared.execution_binding.binding_hash)


@pytest.mark.parametrize("scenario", [
    ("Robot", "raises both arms", "an atrium"),
    ("Courier", "sets a parcel down", "a station platform"),
    ("Scientist", "turns toward the window", "a narrow cabin"),
])
@pytest.mark.parametrize(("provider_family", "expected_provider", "expected_compiler", "expected_version"), [
    ("seedance", "seedance", "seedance-video-compiler", "3"),
    ("h3-max", "minimax_h3_max", "minimax-h3-max-video-compiler", "1"),
])
def test_authored_deadline_reaches_compiler_without_changing_generation_or_adopted_trim(
    tmp_path, scenario, provider_family, expected_provider, expected_compiler, expected_version
):
    deadline = "Technical action deadline: finish by 2.5 seconds and hold the completed pose through the cut."
    composition = {"trim_start_frame": 0, "trim_duration_frames": 72}
    service, limits = subject_service(tmp_path, generated=True, scenario=scenario,
        authored_deadline_text=deadline, adopted_duration_seconds=3,
        generation_output_duration_seconds=5, adopted_composition=composition,
        provider_family=provider_family)
    baseline_root = tmp_path / "baseline"
    baseline_root.mkdir()
    baseline_packet, baseline_data, _, _ = subject_source(baseline_root, generated=True,
        scenario=scenario, adopted_duration_seconds=3, generation_output_duration_seconds=5,
        generation_output_geometry_policy=("adaptive" if provider_family == "h3-max" else "exact"),
        adopted_composition=composition, author_performance=True)
    source_parts = service.packet["units"][0]["prompt_source"]["parts"]
    baseline_parts = baseline_packet["units"][0]["prompt_source"]["parts"]
    assert source_parts[:-1] == baseline_parts
    assert service.packet["units"][0]["references"] == baseline_packet["units"][0]["references"]
    assert [part["type"] for part in source_parts] == [
        "text", "extension", "text", "extension", "text", "text", "text"]
    assert [part["text"] for part in source_parts if part["type"] == "text"][-1] == " " + deadline
    preserved_parts = service.direction["shots"][0]["shot"]["preserved_source_expression"]["parts"]
    baseline_preserved_parts = baseline_data["shots"][0]["shot"]["preserved_source_expression"]["parts"]
    assert preserved_parts[:-1] == baseline_preserved_parts
    assert [part["slot_id"] for part in preserved_parts if part["type"] == "reference"] == [
        "robot-slot", "room-slot"]
    assert [material["asset_id"] for material in preserved_parts[1]["materials"]] == [
        "robot-main", "robot-aux"]
    assert [material["asset_id"] for material in preserved_parts[3]["materials"]] == ["room"]

    prepared = service.prepare(limits=limits)

    expected_prompt = baseline_data["shots"][0]["shot"]["intent"] + " " + deadline
    assert expected_prompt.startswith(f"{scenario[0]} 图片2、图片1 {scenario[1]} in {scenario[2]} 图片3.")
    assert prepared.execution_binding is not None
    assert prepared.resolved_request.provider_name == expected_provider
    assert prepared.resolved_request.prompt_text == expected_prompt
    assert prepared.resolved_request.adapter_compiler_id == expected_compiler
    assert prepared.resolved_request.adapter_compiler_version == expected_version
    assert [binding.asset_id for binding in prepared.resolved_request.image_bindings] == [
        "robot-aux", "robot-main", "room"]
    assert prepared.resolved_request.effective_output.duration_seconds == 5
    requirement = prepared.execution_binding.projection.requirement
    assert requirement.output_need.duration_seconds == 5
    assert requirement.output_need.fps == 24
    assert composition["trim_duration_frames"] / requirement.output_need.fps == 3
    assert requirement.generation_intent.pacing.shot_duration_seconds == 5
    loaded_shot = next(shot for shot in service._load().shots if shot.shot_id == "one")
    assert loaded_shot.duration_policy.seconds == 3
    assert service.direction["shots"][0]["composition"] == composition

    recipe = prepared.execution_binding.decision.routing.provider_bound_request.generation_recipe
    inventory = recipe.acceptance_policy.profile_payload["generation_requirements"]
    assert {item["requirement_id"] for item in inventory} == {"duration", "performance"}
    assert inventory[0]["requirement_id"] == "duration"
    assert inventory[0]["observable"] == "5 seconds"
    assert inventory[0]["intent_paths"] == ("output_need.duration_seconds",)


def test_generated_selection_receipt_cannot_be_reused_after_raw_deadline_edit(tmp_path):
    from ai_video.canvas_authoring import author_canvas_project

    old_packet, _, old_registry, old_artifacts = subject_source(tmp_path, generated=True)
    new_packet, new_direction, _, _ = subject_source(tmp_path,
        authored_deadline_text="Technical action deadline: finish by 2.5 seconds.")
    assert old_packet["source_snapshot_sha256"] != new_packet["source_snapshot_sha256"]

    with pytest.raises(ValueError, match="generated copy differs from the original canvas resource"):
        author_canvas_project(packet=new_packet, direction=new_direction,
            registry=old_registry, asset_artifacts=old_artifacts)


def test_subject_auxiliary_cannot_be_reclassified_as_scene(tmp_path):
    source, data, registry, artifacts = subject_source(tmp_path, scene_auxiliary=True)
    with pytest.raises(ValueError, match="subject.*identity"):
        author_canvas_project(packet=source, direction=data, registry=registry, asset_artifacts=artifacts)


def test_preserved_image_project_can_revise_title_through_canonical_owner(tmp_path):
    service, _ = subject_service(tmp_path)
    before = service._load()
    service.direction["title"] = "Revised title"
    service.revise_authoring(attempt_id="source-title-revision")
    after = service._load()
    assert after.project.title == "Revised title"
    assert after.project.revision == before.project.revision + 1
    assert after.registry == before.registry
    assert after.asset_paths == before.asset_paths
    assert [s.preserved_source_expression for s in after.shots] == [
        s.preserved_source_expression for s in before.shots]


@pytest.mark.parametrize("damage", ["prompt", "omit_auxiliary", "image_metadata"])
def test_execution_binding_and_start_reject_resealed_source_changes(tmp_path, damage):
    from ai_video.errors import AiVideoError
    from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
    from ai_video.production.video import ResolvedVideoGenerationRequest, VideoGenerationRequest
    from ai_video.production.video_generation import VideoGenerationService

    service, limits = subject_service(tmp_path)
    prepared = service.prepare(limits=limits)
    binding = prepared.execution_binding
    assert binding is not None
    original = prepared.resolved_request
    changes = {"prompt_text": original.prompt_text + " Invent a new camera move."} if damage == "prompt" else {
        "image_bindings": tuple(b for b in original.image_bindings if b.asset_id != "robot-aux")}
    if damage == "image_metadata":
        changes = {"image_bindings": tuple(b.model_copy(update={"width": b.width + 1})
                                          if b.asset_id == "robot-aux" else b for b in original.image_bindings)}
    sealed = VideoGenerationRequest.create(**{
        **original.activation_scope.request.model_dump(mode="python", exclude={"request_input_hash"}), **changes})
    capability = next(v for v in prepared.provider.capabilities().variants if v.capability_id == original.capability_id)
    changed = ResolvedVideoGenerationRequest.create(request=sealed, capability=capability,
        effective_output=original.effective_output, effective_seed=original.effective_seed,
        effective_negative_prompt_text=original.effective_negative_prompt_text)
    values = {**{name: getattr(binding, name) for name in GenerationDecisionExecutionBinding.model_fields
                 if name not in {"schema_version", "binding_hash"}}, "compiled_request": changed}
    with pytest.raises(ValueError, match="preserved source"):
        GenerationDecisionExecutionBinding.create(**values)
    # A caller bypassing the constructor still cannot cross the canonical start seam.
    payload = {**binding.model_dump(mode="json", exclude={"binding_hash"}),
               "compiled_request": changed.model_dump(mode="json")}
    forged = binding.model_copy(update={"compiled_request": changed,
        "binding_hash": canonical_sha256(GenerationDecisionExecutionBinding._payload(payload))})
    manifest_path = service.committer.project_root / "state" / "manifest.json"
    before = manifest_path.read_bytes()
    with pytest.raises(AiVideoError):
        VideoGenerationService(committer=service.committer, provider=prepared.provider).start(
            attempt_id="changed-source", request=changed, execution_binding=forged)
    assert manifest_path.read_bytes() == before


@pytest.mark.parametrize("damage", ["opening_without_facts", "closing_without_facts", "subject_endpoint", "camera"])
def test_execution_rejects_source_semantics_with_unchanged_prose_and_images(tmp_path, monkeypatch, damage):
    from ai_video.errors import AiVideoError
    from ai_video.production.generation_decision import resolve_generation_decision, extract_generation_features
    from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
    from ai_video.production.shot_router import VideoGenerationResolver
    from ai_video.production.video import ResolvedVideoGenerationRequest, VideoGenerationRequest
    from ai_video.production.video_generation import VideoGenerationService
    from ai_video.production.video_requirement import (
        GenerationIntent, ProviderNeutralVideoRequirement, VerifiedGenerationRequirementProjection,
    )

    service, limits = subject_service(tmp_path)
    prepared = service.prepare(limits=limits)
    binding = prepared.execution_binding
    original = prepared.resolved_request
    intent_data = binding.projection.requirement.generation_intent.model_dump(mode="python")
    if damage == "opening_without_facts":
        intent_data["open_state"] = {"kind": "typed_hash", "state_hash": "a" * 64}
    elif damage == "closing_without_facts":
        intent_data["close_state"] = {"kind": "typed_hash", "state_hash": "b" * 64}
    elif damage == "subject_endpoint":
        intent_data["subject_action"]["endpoint"] = {"state_hash": "c" * 64}
    else:
        intent_data["camera_intent"] = {"movement": "pan_left"}
    requirement = ProviderNeutralVideoRequirement.create(**{
        **binding.projection.requirement.model_dump(mode="python", exclude={"requirement_id", "requirement_hash"}),
        "generation_intent": GenerationIntent.model_validate(intent_data)})
    projection = VerifiedGenerationRequirementProjection.create(**{
        **binding.projection.model_dump(mode="python", exclude={"projection_hash", "requirement"}),
        "requirement": requirement})
    inputs = binding.inputs.model_copy(update={"projection_hash": projection.projection_hash,
        "facts_hash": canonical_sha256(requirement.model_dump(mode="json", exclude={"requirement_id", "requirement_hash"})),
        "feature_scope": extract_generation_features(projection),
        "candidates": tuple(c.model_copy(update={"recipe": c.recipe.model_copy(
            update={"requirement_hash": requirement.requirement_hash})}) for c in binding.inputs.candidates)})
    decision = resolve_generation_decision(VideoGenerationResolver(), projection=projection,
        context=binding.context, policy=binding.policy, lifecycle=binding.lifecycle, inputs=inputs)
    assert decision.disposition == "GENERATE_ONCE"
    bound = decision.routing.provider_bound_request
    sealed = VideoGenerationRequest.create(**{
        **original.activation_scope.request.model_dump(mode="python", exclude={"request_input_hash"}),
        "requirement_hash": requirement.requirement_hash,
        "provider_bound_request_hash": bound.provider_bound_request_hash})
    capability = next(v for v in prepared.provider.capabilities().variants if v.capability_id == original.capability_id)
    changed = ResolvedVideoGenerationRequest.create(request=sealed, capability=capability,
        effective_output=original.effective_output, effective_seed=original.effective_seed,
        effective_negative_prompt_text=original.effective_negative_prompt_text)
    values = {**{name: getattr(binding, name) for name in GenerationDecisionExecutionBinding.model_fields
                 if name not in {"schema_version", "binding_hash"}},
              "projection": projection, "inputs": inputs, "decision": decision, "compiled_request": changed}
    assert changed.prompt_text == original.prompt_text and changed.image_bindings == original.image_bindings
    with pytest.raises(ValueError):
        GenerationDecisionExecutionBinding.create(**values)
    payload = {"schema_version": "1", **{name: value.model_dump(mode="json") if hasattr(value, "model_dump")
        else value for name, value in values.items()}}
    forged = GenerationDecisionExecutionBinding.model_construct(**values, schema_version="1",
        binding_hash=canonical_sha256(GenerationDecisionExecutionBinding._payload(payload)))
    manifest_path = service.committer.project_root / "state" / "manifest.json"
    before = manifest_path.read_bytes()
    with pytest.raises(AiVideoError):
        VideoGenerationService(committer=service.committer, provider=prepared.provider).start(
            attempt_id="changed-source-semantics", request=changed, execution_binding=forged)
    assert manifest_path.read_bytes() == before
    # Reopen a constructor-bypassed historical binding at the actual pre-submit
    # guard, after a normal start. No intent, permit or Provider call may advance.
    VideoGenerationService(committer=service.committer, provider=prepared.provider).start(
        attempt_id="unchanged-before-submit", request=original, execution_binding=binding)
    loaded = service._load()
    state = next(a.video_generation_state for a in loaded.manifest.attempts
                 if a.attempt_id == "unchanged-before-submit")
    before = {p.relative_to(loaded.root): p.read_bytes() for p in (loaded.root / "state").rglob("*.json")}
    monkeypatch.setattr(service.committer, "_reopen_generation_execution_binding", lambda _: forged)
    with pytest.raises((AiVideoError, ValueError)):
        service.committer._require_submit_execution_binding(loaded.manifest, state, changed)
    assert {p.relative_to(loaded.root): p.read_bytes() for p in (loaded.root / "state").rglob("*.json")} == before


def local_video_source_fixture(tmp_path, monkeypatch):
    from test_canvas_assets import local_video_packet, local_video_selection, fake_local_video_probe
    from ai_video.production.seedance_source_expression import source_parts_sha256

    packet = local_video_packet()
    selection = local_video_selection(tmp_path)
    registry, artifacts = fake_local_video_probe(monkeypatch)(packet=packet,
        selections=[selection], allowed_asset_root=tmp_path, ffprobe_executable="/usr/bin/ffprobe")
    asset = registry.assets[0]
    unit = packet["units"][0]
    parts = []
    for raw in unit["prompt_source"]["parts"]:
        if raw["type"] == "text":
            parts.append({"type": "text", "text": raw["text"]})
        else:
            parts.append({"type": "reference", "slot_id": raw["object_id"], "materials": [
                {"asset_id": asset.asset_id, "asset_sha256": asset.sha256, "role": "video_reference"}]})
    expression = {"source_sha256": source_parts_sha256(parts), "parts": parts}
    row = {"shot": {"preserved_source_expression": expression}}
    return packet, unit, row, registry, artifacts


def test_preserved_source_accepts_only_exact_local_video_reference(tmp_path, monkeypatch):
    from ai_video.canvas_source_expression import require_canvas_source_expression

    packet, unit, row, registry, artifacts = local_video_source_fixture(tmp_path, monkeypatch)
    require_canvas_source_expression(packet=packet, unit=unit, row=row, registry=registry,
        asset_artifacts=artifacts)


@pytest.mark.parametrize("damage", ["missing_receipt", "forged_receipt", "stale_snapshot",
    "wrong_role", "wrong_slot", "wrong_type", "wrong_mime", "wrong_metadata"])
def test_preserved_source_rejects_unproven_or_mismatched_local_video(tmp_path, monkeypatch, damage):
    from ai_video.canvas_source_expression import require_canvas_source_expression
    from ai_video.production.registry import registry_semantic_sha256
    from ai_video.production.seedance_source_expression import source_parts_sha256
    from ai_video.production.state_commit import PreparedArtifact

    packet, unit, row, registry, artifacts = local_video_source_fixture(tmp_path, monkeypatch)
    expression = row["shot"]["preserved_source_expression"]
    if damage == "missing_receipt":
        artifacts = tuple(a for a in artifacts if a.relative_path.suffix != ".json")
    elif damage == "forged_receipt":
        receipt = next(a for a in artifacts if a.relative_path.suffix == ".json")
        artifacts = tuple(a for a in artifacts if a != receipt) + (PreparedArtifact(
            receipt.relative_path, receipt.payload + b" ", receipt.file_sha256),)
    elif damage == "stale_snapshot":
        packet["source_snapshot_sha256"] = "d" * 64
    elif damage in {"wrong_role", "wrong_slot"}:
        part = expression["parts"][1]
        if damage == "wrong_role":
            part["materials"][0]["role"] = "scene"
        else:
            part["slot_id"] = "other-slot"
        expression["source_sha256"] = source_parts_sha256(expression["parts"])
    else:
        asset = registry.assets[0]
        if damage == "wrong_type":
            changed_asset = asset.model_copy(update={"asset_type": type(asset.asset_type).IMAGE})
        elif damage == "wrong_mime":
            changed_asset = asset.model_copy(update={"mime_type": "video/quicktime"})
        else:
            changed_asset = asset.model_copy(update={"width": asset.width + 1,
                "video_metadata": asset.video_metadata.model_copy(update={"width": asset.width + 1})})
        assets = (changed_asset,)
        identity = registry_semantic_sha256(registry.model_copy(update={"assets": assets}))
        registry = registry.model_copy(update={"assets": assets, "revision_id": identity, "content_hash": identity})
    with pytest.raises((ValueError, KeyError)):
        require_canvas_source_expression(packet=packet, unit=unit, row=row, registry=registry,
            asset_artifacts=artifacts)
