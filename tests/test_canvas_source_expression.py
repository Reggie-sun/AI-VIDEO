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


def subject_source(tmp_path, *, scene_auxiliary=False, generated=False):
    """Inspect/import real fixture bytes before canonical authoring and planning."""
    from ai_video.canvas_assets import prepare_canvas_png_assets
    from tests.production_project_factory import _p7_png

    raw = document()
    raw["edges"] = []
    raw["nodes"].append({"id": "robot", "type": "subject", "data": {
        "main": {"refType": "resource_snapshot", "resourceId": "robot-main"},
        "auxiliaries": [{"refType": "resource_snapshot", "resourceId": "robot-aux"}]}})
    for node in raw["nodes"]:
        draft = node["data"].get("generationDraft")
        if draft is None:
            continue
        draft["parts"] = [{"type": "text", "text": "Robot "},
            {"type": "extension", "extension_type": "subject", "object_id": "robot-slot"},
            {"type": "text", "text": " lifts its hands in "},
            {"type": "extension", "extension_type": "node", "object_id": "room-slot"},
            {"type": "text", "text": "."}]
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
    parts = [{"type": "text", "text": "Robot "},
        {"type": "reference", "slot_id": "robot-slot", "materials": materials},
        {"type": "text", "text": " lifts its hands in "},
        {"type": "reference", "slot_id": "room-slot", "materials": [
            {"asset_id": "room", "asset_sha256": next(a.sha256 for a in registry.assets if a.asset_id == "room"),
             "role": "scene"}]}, {"type": "text", "text": "."}]
    data = direction()
    data["delivery_profile"] = {"width": 1280, "height": 720, "fps": 24}
    data["characters"] = [{"character_id": "robot", "name": "Robot", "identity": "Robot",
        "appearance_bible": "Metal body", "reference_asset_ids": [m["asset_id"] for m in materials
                                                                  if m["role"] == "identity"]}]
    data["scenes"][0]["visual_reference_asset_ids"] = ["room", *[m["asset_id"] for m in materials
                                                      if m["role"] == "scene"]]
    for row in data["shots"]:
        row["shot"].update(intent="Robot 图片2、图片1 lifts its hands in 图片3.", character_ids=["robot"],
            duration_policy={"mode": "fixed", "seconds": 5}, preserved_source_expression={
                "source_sha256": canonical_sha256({"parts": parts, "implicit_references": []}),
                "parts": parts})
        row["generation"] = {"references": [{"role": "scene_reference" if m["role"] == "scene"
            else "character_reference", "asset_id": m["asset_id"]} for m in materials] + [
                {"role": "scene_reference", "asset_id": "room"}],
            "intent_evidence": {"character_action_required": True},
            "generation_intent": {"subject_action": {"progression": row["shot"]["intent"]},
                                  "pacing": {"shot_duration_seconds": 5}},
            "audio_need": "required", "quality_need": {}}
    return source, data, registry, artifacts


@dataclass(frozen=True)
class LoadedFixture:
    project: object


def subject_service(tmp_path, *, generated=False):
    from ai_video.canvas_dependencies import initialize_canvas_graph
    from ai_video.canvas_production import CanvasProductionService
    from ai_video.production.generation_decision import DecisionPolicy, ExecutionLimits
    from ai_video.production.generation_feedback import RegisteredGenerationTarget
    from ai_video.production.project import load_production_project
    from ai_video.production.seedance import SeedanceVideoProvider
    from ai_video.production.shot_router import AdapterCompilerContract
    from ai_video.production.state_commit import ProductionStateCommitter
    from tests.production_generation_execution_factory import activate_fixture_generation_qa_policy
    from test_production_seedance import _profile, _profile_pointer, _request
    from test_production_shot_router import _policy

    source, data, registry, artifacts = subject_source(tmp_path, generated=generated)
    root = tmp_path / "project"
    root.mkdir()
    profile = _profile()
    model = "doubao-seedance-2-0-fast-260128"
    output = _request(profile, model_id=model).output_requirement.model_copy(update={"timing_mode": "nominal_seconds"})
    def forbidden(*args, **kwargs):
        pytest.fail("source-boundary tests must not use Provider effects or credentials")
    provider = SeedanceVideoProvider(profile=profile, transport=forbidden,
                                    credential=forbidden, input_reference=forbidden)
    service = CanvasProductionService(committer=ProductionStateCommitter(root), packet=source,
        direction=data, targets=(RegisteredGenerationTarget(provider, _profile_pointer(profile),
            AdapterCompilerContract.create(compiler_id="seedance-video-compiler", compiler_version="3"),
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
        allowed_remote_candidates=tuple(f"seedance/{v.capability_id}" for v in provider.capabilities().variants
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
