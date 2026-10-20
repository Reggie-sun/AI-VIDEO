"""Actual accepted MP4 references and edited-cut P6 identity, with scripted media."""
import asyncio
from copy import deepcopy

import pytest

from ai_video.canvas_production import CanvasProductionService
from ai_video.canvas_handoff import require_canvas_state_reference
from ai_video.canvas_planning import canvas_feedback_context
from ai_video.canvas_review import canvas_cut_contract
from ai_video.canvas_target_gate import target_state_requirements
from ai_video.production.hashing import seal_artifact
from test_canvas_production import runtime, submit_and_fetch, pass_evaluation
from test_generation_feedback_review import Session


def accept_current(service, provider, limits, auth):
    submit_and_fetch(service, provider, limits, auth)
    def all_fixture_findings(review):
        from ai_video.production.generation_evaluation import GenerationObservation, GenerationEvaluationSource
        if review.evaluation_items:
            items = review.evaluation_items
            return (GenerationEvaluationSource(schema_version="generation-evaluation/2",
                request_hash=items[0].request_hash, artifact_sha256=review.analysis.artifact_sha256,
                size_bytes=review.analysis.size_bytes, rubric_hash=items[0].rubric_hash,
                qa_policy_content_hash=review.qa_policy.content_hash, qa_policy_snapshot=review.qa_policy,
                analysis_evidence=review.analysis, evaluator=review.qa_policy.semantic_authorities[0], proof="technical",
                observations=tuple(GenerationObservation(requirement_id=item.requirement_id, verdict="PASS",
                    observation="Controlled offline state fixture answer", evaluation_item_hash=item.evaluation_item_hash,
                    question_text=item.question_text, presentation_ref=review.presentation_ref, answer_ref=review.answer_ref)
                    for item in items)),)
        source = pass_evaluation(review)[0]
        return (source.model_copy(update={"observations": tuple(GenerationObservation(
            requirement_id=rule.requirement_id, verdict="PASS",
            observation="Explicit offline fixture finding; no actual continuity acceptance")
            for rule in review.recipe.expressions)}),)
    if service._load().qa_policy.selected_generation_acceptance().profile_payload.get("requirement_semantics_version"):
        from ai_video_mcp.generation_feedback import ControlledPresentationVerifier
        verifier = ControlledPresentationVerifier(evaluator=service._load().qa_policy.semantic_authorities[0],
            proof="technical", adjudicate=all_fixture_findings)
        asyncio.run(service.evaluate(session=Session(), presentation_verifier=verifier))
    else:
        asyncio.run(service.evaluate(session=Session(), adjudicate=all_fixture_findings))
    service.execute(action="validate")
    service.execute(action="activate")


def state_target(tmp_path):
    service, provider, limits, auth = runtime(tmp_path)
    data = deepcopy(service.direction)
    aid = data["shots"][1]["generation"]["references"][0]["asset_id"]
    data["scenes"].append({"scene_id": "after", "location": "road", "time": "day", "mood": "quiet",
                           "visual_reference_asset_ids": [aid]})
    data["storyboard"]["beats"].append({"beat_id": "after", "scene_id": "after", "shot_ids": ["two"],
                                      "narrative_intent": "Original successor"})
    data["storyboard"]["beats"][0]["shot_ids"] = ["one"]
    target = data["shots"][1]
    target["shot"].update(scene_id="after", storyboard_beat_id="after")
    target["shot"]["required_asset_roles"].pop()
    target["generation"]["references"][0]["role"] = "scene_reference"
    target["state_reference"] = {"source_shot_id": "one", "frame_index": 7,
        "replace_asset_id": aid, "usage_license": "fixture-only",
        "checks": {"action": "Required intermediate action state", "space": "Required intermediate space state"}}
    service.direction = data
    service.revise_authoring(attempt_id="separate-reference-owner")
    # Selected QA owns successor observations; source-frame approval is separate.
    from ai_video.production.domain_acceptance import DomainAcceptancePolicy
    from ai_video.production.hashing import canonical_sha256
    loaded = service._load()
    acceptance = loaded.qa_policy.selected_generation_acceptance()
    payload = acceptance.model_dump(mode="json")["profile_payload"]
    payload.pop("content_hash")
    from test_requirement_semantics import semantic_rule
    payload["requirement_semantics_version"] = "requirement-semantics/1"
    for identity, (dimension, expected) in target_state_requirements(target).items():
        payload["required_requirement_ids"].append(identity)
        payload["generation_requirements"].append({"requirement_id": identity, "level": "acceptance",
            "stage": "raw_generation", "dimension": dimension, "observable": expected,
            "tolerance": "Selected required state is retained", "measurement": "Compare to bound accepted-state reference",
            "proof": "technical", "intent_paths": ["generation_intent.subject_action.progression"], "production_owner": "generation"})
    for rule in payload["generation_requirements"]:
        rule["semantics"] = semantic_rule(rule["requirement_id"])["semantics"]
    payload["generation_requirements"].sort(key=lambda item: item["requirement_id"])
    digest = canonical_sha256(payload)
    payload["content_hash"] = digest
    acceptance = DomainAcceptancePolicy.model_validate({**acceptance.model_dump(mode="json"),
        "profile_content_hash": digest, "profile_payload": payload,
        "required_requirement_ids": payload["required_requirement_ids"]})
    policy = seal_artifact(loaded.qa_policy.model_copy(update={"generation_acceptance": acceptance,
        "revision": loaded.qa_policy.revision + 1}))
    service.committer.activate_qa_policy(policy, expected_manifest_revision=loaded.manifest.manifest_revision,
                                         attempt_id="selected-successor-state-criteria")
    provider.prompt_text = data["shots"][0]["generation"]["generation_intent"]["subject_action"]["progression"]
    return service, provider, limits, auth, aid


def reference_gate(service):
    def adjudicate(context, analysis, selected):
        assert selected.reference.frame_index == context["frame_index"]
        return {name: {"status": "match", "expected": expected, "observed": "Explicit scripted state at frame 7",
            "confidence_milli": 1000, "rationale": "Offline evaluator fixture; no real continuity acceptance"}
            for name, expected in context["checks"].items()}
    return {"checks": {"action": "Required intermediate action state", "space": "Required intermediate space state"},
        "session": Session(), "adjudicate": adjudicate, "tool_identity": service._load().qa_policy.semantic_authorities[0]}


def test_intermediate_reference_consumes_accepted_bytes_and_replays_without_effect(tmp_path):
    service, provider, limits, auth, aid = state_target(tmp_path)
    with pytest.raises(Exception, match="unsubmitted target"):
        service.handoff_reference(source_shot_id="one", target_occurrence_id="b", frame_index=7,
                                  replace_asset_id=aid, usage_license="fixture-only", **reference_gate(service))
    accept_current(service, provider, limits, auth)
    source = service._load()
    source_shot = source.shots[0]
    args = dict(source_shot_id="one", target_occurrence_id="b", frame_index=7,
                replace_asset_id=aid, usage_license="fixture-only", **reference_gate(service))
    asset = service.handoff_reference(**args)
    loaded = service._load()
    evidence = require_canvas_state_reference(loaded=loaded, asset=asset)
    assert evidence["reference"]["frame_index"] == 7
    assert asset.input_artifact_ids[0] in {a.asset_id for a in loaded.registry.assets if a.asset_type.value == "video"}
    assert loaded.shots[0] == source_shot
    context = canvas_feedback_context(loaded=loaded, row=service.direction["shots"][1], policy=service.routing_policy)
    assert any(e.asset_id == asset.asset_id and e.asset_sha256 == asset.sha256
               for e in context["projection"].requirement.asset_evidence)
    revision = loaded.manifest.manifest_revision
    assert service.handoff_reference(**args) == asset
    assert service._load().manifest.manifest_revision == revision
    assert args["session"].calls == 1
    assert provider.call_counts.submit == 1
    assert service.author(registry=loaded.registry).registry == loaded.registry
    path = loaded.asset_paths[asset.asset_id]
    path.write_bytes(b"forged frame")
    with pytest.raises(Exception):
        service.prepare(limits=limits)
    assert provider.call_counts.submit == 1


def test_rich_source_state_handoff_revisions_canonical_source_and_replays_exactly(tmp_path):
    from ai_video.canvas_assets import prepare_canvas_png_assets
    from ai_video.canvas_source_expression import adapted_canvas_prompt
    from ai_video.canvas_source_revision import (
        _previous_director, effective_prompt_sha256, retained_source_revision,
    )
    from ai_video.production.hashing import canonical_sha256
    from ai_video.production.registry import registry_semantic_sha256
    from ai_video.production.seedance_source_expression import (
        PreservedSourceExpression, SourceReferenceMaterial, SourceReferencePart,
        SourceTextPart, source_parts_sha256,
    )
    from scripts.canvas_sequence_packet import build_sequence_packet
    from test_canvas_sequence_packet import document
    from production_project_factory import _p7_png

    service, provider, limits, auth, _placeholder_id = state_target(tmp_path)
    previous = service._load()

    raw_document = document()
    target_node = next(node for node in raw_document["nodes"] if node["id"] == "b")
    target_draft = target_node["data"]["generationDraft"]
    target_draft["references"] = [ref for ref in target_draft["references"]
        if ref["slotId"] != "voice-slot"]
    raw_document["edges"] = [edge for edge in raw_document["edges"]
        if not (edge["source"] == "voice" and edge["target"] == "b")]
    packet = build_sequence_packet(raw_document, {"node_ids": ["a", "b"]})
    target_unit = next(unit for unit in packet["units"] if unit["occurrence_id"] == "b")
    baseline = _previous_director(previous)
    baseline_unit = next(unit for unit in baseline["packet"]["units"]
        if unit["occurrence_id"] == "b")
    assert target_unit["prompt_source"]["parts"] == baseline_unit["prompt_source"]["parts"]

    local_path = tmp_path / "retained-room.png"
    local_path.write_bytes(_p7_png(rgba=b"\x11\x22\x33\xff"))
    scene_id = "canvas-local-room-for-state-handoff"
    local_registry, local_artifacts = prepare_canvas_png_assets(packet=packet,
        selections=[{"asset_id": scene_id, "node_id": "room", "resource_id": "room-resource",
            "path": local_path, "usage_license": "fixture-only"}], allowed_asset_root=tmp_path)
    local_scene_asset = local_registry.assets[0]
    registry = previous.registry.model_copy(update={"assets": tuple(sorted(
        (*previous.registry.assets, local_scene_asset), key=lambda asset: asset.asset_id))})
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": registry_hash, "content_hash": registry_hash})

    direction = deepcopy(service.direction)
    target = next(row for row in direction["shots"] if row["occurrence_id"] == "b")
    next(scene for scene in direction["scenes"] if scene["scene_id"] == "after")[
        "visual_reference_asset_ids"] = [scene_id]
    target["generation"]["references"] = [{"role": "scene_reference", "asset_id": scene_id}]
    target["state_reference"]["replace_asset_id"] = scene_id
    raw_parts = target_unit["prompt_source"]["parts"]
    text_part = next(part for part in raw_parts if part["type"] == "text")
    room_part = next(part for part in raw_parts if part["type"] == "extension")
    expression_parts = (
        SourceTextPart(text=text_part["text"]),
        SourceReferencePart(slot_id=room_part["object_id"], materials=(
            SourceReferenceMaterial(asset_id=scene_id, asset_sha256=local_scene_asset.sha256, role="scene"),
        )),
    )
    expression = PreservedSourceExpression(contract_version="seedance-preserved-source/2",
        source_sha256=source_parts_sha256(expression_parts), parts=expression_parts)
    target["shot"]["preserved_source_expression"] = expression.model_dump(mode="json")
    prompt = adapted_canvas_prompt(target["shot"]["preserved_source_expression"])
    target["shot"]["intent"] = prompt
    target["generation"]["generation_intent"]["subject_action"]["progression"] = prompt
    target["source_revision"] = retained_source_revision(previous=previous,
        packet=packet, row=target,
        reason="Retain the inspected source parts while binding the selected accepted-state reference.")

    baseline_row = next(row for row in baseline["direction"]["shots"]
        if row["occurrence_id"] == "b")
    setup_revision = target["source_revision"]
    assert setup_revision["baseline_source_snapshot_sha256"] == baseline["packet"]["source_snapshot_sha256"]
    assert setup_revision["baseline_prompt_parts_sha256"] == canonical_sha256({
        "parts": baseline_unit["prompt_source"]["parts"]})
    assert setup_revision["baseline_effective_prompt_sha256"] == effective_prompt_sha256(baseline_row)

    service.packet = packet
    service.direction = direction
    service.revise_authoring(attempt_id="rich-source-state-reference",
        registry=registry, asset_artifacts=local_artifacts)
    assert service.direction["shots"][0]["shot"].get("preserved_source_expression") is None
    assert service.direction["shots"][1]["shot"]["preserved_source_expression"]["parts"][0][
        "text"] == text_part["text"]

    accept_current(service, provider, limits, auth)
    pre_handoff = service._load()
    pre_handoff_baseline = _previous_director(pre_handoff)
    pre_handoff_baseline_row = next(row for row in pre_handoff_baseline["direction"]["shots"]
        if row["occurrence_id"] == "b")
    pre_handoff_baseline_unit = next(unit for unit in pre_handoff_baseline["packet"]["units"]
        if unit["occurrence_id"] == "b")
    gate = reference_gate(service)
    evaluations = 0
    original_adjudicate = gate["adjudicate"]

    def count_evaluation(*args):
        nonlocal evaluations
        evaluations += 1
        return original_adjudicate(*args)

    gate["adjudicate"] = count_evaluation
    args = {"source_shot_id": "one", "target_occurrence_id": "b", "frame_index": 7,
        "replace_asset_id": scene_id, "usage_license": "fixture-only", **gate}
    accepted_frame = service.handoff_reference(**args)
    loaded = service._load()
    revised_target = next(row for row in service.direction["shots"] if row["occurrence_id"] == "b")
    revised_expression = revised_target["shot"]["preserved_source_expression"]
    revised_parts = revised_expression["parts"]
    validated_expression = PreservedSourceExpression.model_validate(revised_expression)
    assert revised_parts[0]["text"] == text_part["text"]
    assert revised_parts[1]["materials"] == [{
        "asset_id": accepted_frame.asset_id, "asset_sha256": accepted_frame.sha256, "role": "scene",
    }]
    assert validated_expression.source_sha256 == source_parts_sha256(validated_expression.parts)
    assert revised_target["reference_replacements"][accepted_frame.asset_id] == {
        "original_asset_id": scene_id, "source_shot_id": "one", "frame_index": 7,
    }
    handoff_revision = revised_target["source_revision"]
    assert handoff_revision["baseline_source_snapshot_sha256"] == packet["source_snapshot_sha256"]
    assert handoff_revision["baseline_prompt_parts_sha256"] == canonical_sha256({
        "parts": pre_handoff_baseline_unit["prompt_source"]["parts"]})
    assert handoff_revision["baseline_effective_prompt_sha256"] == effective_prompt_sha256(
        pre_handoff_baseline_row)
    assert require_canvas_state_reference(loaded=loaded, asset=accepted_frame)[
        "reference"]["frame_index"] == 7

    manifest_revision = loaded.manifest.manifest_revision
    assert service.handoff_reference(**args) == accepted_frame
    assert service._load().manifest.manifest_revision == manifest_revision
    assert evaluations == 1
    assert args["session"].calls == 1
    assert provider.call_counts.submit == 1


def test_source_video_handoff_binds_accepted_mp4_and_replays_before_successor_prepare(tmp_path):
    service, provider, limits, auth, aid = state_target(tmp_path)
    service.direction["shots"][1]["state_reference"]["conditioning"] = "source_video"
    service.revise_authoring(attempt_id="source-video-conditioning")
    accept_current(service, provider, limits, auth)

    gate = reference_gate(service)
    args = dict(source_shot_id="one", target_occurrence_id="b", frame_index=7,
        replace_asset_id=aid, usage_license="fixture-only", **gate)
    state = service.handoff_reference(**args)
    loaded = service._load()
    source_video_id = state.input_artifact_ids[0]
    source_video = next(asset for asset in loaded.registry.assets if asset.asset_id == source_video_id)
    successor = next(row for row in service.direction["shots"] if row["occurrence_id"] == "b")

    assert service.position().next_action == "prepare"
    assert successor["generation"]["references"] == [{"asset_id": source_video_id, "role": "existing_video"}]
    assert source_video.asset_type.value == "video"
    assert source_video.sha256 == require_canvas_state_reference(loaded=loaded, asset=state)[
        "reference"]["source_video_sha256"]
    revision = loaded.manifest.manifest_revision
    assert service.handoff_reference(**args) == state
    assert service._load().manifest.manifest_revision == revision
    assert args["session"].calls == 1
    assert provider.call_counts.submit == 1


def test_invalid_reference_decision_has_no_registry_or_manifest_effect(tmp_path):
    service, provider, limits, auth, aid = state_target(tmp_path)
    accept_current(service, provider, limits, auth)
    before = service._load()
    with pytest.raises(Exception, match="scene reference"):
        service.handoff_reference(source_shot_id="one", target_occurrence_id="b", frame_index=7,
                                  replace_asset_id="wrong-version", usage_license="fixture-only", **reference_gate(service))
    assert service._load().manifest == before.manifest
    assert service._load().registry == before.registry
    assert provider.call_counts.submit == 1


def test_state_reference_gate_missing_or_failed_observations_do_not_bind_target(tmp_path):
    service, provider, limits, auth, aid = state_target(tmp_path)
    accept_current(service, provider, limits, auth)
    before = service._load()
    gate = reference_gate(service)
    gate["adjudicate"] = lambda *_: {}
    with pytest.raises(Exception, match="NOT_EVALUATED"):
        service.handoff_reference(source_shot_id="one", target_occurrence_id="b", frame_index=7,
                                  replace_asset_id=aid, usage_license="fixture-only", **gate)
    assert service._load().manifest == before.manifest
    assert service.position().next_action == "handoff_reference"
    assert service.start(limits=limits).next_action == "handoff_reference"
    assert provider.call_counts.submit == 1


def test_source_video_conditioning_keeps_approved_frame_as_separate_proof(monkeypatch):
    from types import SimpleNamespace
    from ai_video.canvas_handoff import replace_state_reference
    from ai_video.production.models import AssetType
    from ai_video.production.seedance_source_expression import (
        PreservedSourceExpression, SourceImageAlias, SourceReferenceMaterial,
        SourceReferencePart, SourceTextPart, source_parts_sha256,
    )

    original = SimpleNamespace(asset_id="selected-still", sha256="a" * 64,
        asset_type=AssetType.IMAGE)
    video = SimpleNamespace(asset_id="accepted-video", sha256="b" * 64,
        asset_type=AssetType.VIDEO)
    source = SimpleNamespace(shot_id="one", scene_id="before")
    monkeypatch.setattr("ai_video.canvas_handoff.accepted_sequence_source",
        lambda loaded, shot: (None, SimpleNamespace(output_asset_id=video.asset_id,
            request_input_hash="accepted-request"), None, None, None))
    monkeypatch.setattr("ai_video.canvas_handoff.require_canvas_video_reference",
        lambda **_kwargs: None)
    loaded = SimpleNamespace(shots=(source,), registry=SimpleNamespace(assets=(original, video)))
    materials = (SourceReferenceMaterial(asset_id=original.asset_id, asset_sha256=original.sha256, role="scene"),)
    parts = (SourceTextPart(text="图片1接续动作。"), SourceReferencePart(slot_id="scene", materials=materials))
    expression = PreservedSourceExpression(contract_version="seedance-preserved-source/2",
        source_sha256=source_parts_sha256(parts), parts=parts,
        image_aliases=(SourceImageAlias(label="图片1", asset_ids=(original.asset_id,)),))
    direction = {"shots": [
        {"occurrence_id": "a", "shot": {"shot_id": "one"}},
        {"occurrence_id": "b", "shot": {"shot_id": "two", "scene_id": "after",
            "intent": "图片1接续动作。图片1", "preserved_source_expression": expression.model_dump(mode="json"),
            "required_asset_roles": [{"role": "scene_reference", "asset_ids": [original.asset_id],
                "allowed_asset_types": ["image"]}]},
         "generation": {"references": [{"asset_id": original.asset_id, "role": "scene_reference"}],
            "generation_intent": {"subject_action": {"progression": "图片1接续动作。图片1"}}},
         "state_reference": {"conditioning": "source_video"}}],
        "scenes": [{"scene_id": "after", "visual_reference_asset_ids": [original.asset_id]}]}

    revised = replace_state_reference(direction=direction, loaded=loaded, target_occurrence_id="b",
        replace_asset_id=original.asset_id, asset=SimpleNamespace(asset_id="approved-frame", sha256="c" * 64),
        source_shot_id="one", frame_index=7)

    invalid = deepcopy(direction)
    invalid["shots"][1]["state_reference"]["conditioning"] = "unknown"
    with pytest.raises(ValueError, match="unsupported conditioning"):
        replace_state_reference(direction=invalid, loaded=loaded, target_occurrence_id="b",
            replace_asset_id=original.asset_id,
            asset=SimpleNamespace(asset_id="approved-frame", sha256="c" * 64),
            source_shot_id="one", frame_index=7)

    row = revised["shots"][1]
    assert row["generation"]["references"] == [{"asset_id": video.asset_id, "role": "existing_video"}]
    assert row["shot"]["required_asset_roles"] == [{"role": "scene_reference",
        "asset_ids": [original.asset_id], "allowed_asset_types": ["image"]}]
    preserved = row["shot"]["preserved_source_expression"]
    assert preserved["parts"][1]["materials"] == [{"asset_id": video.asset_id,
        "asset_sha256": video.sha256, "role": "video_reference"}]
    assert row["shot"]["intent"] == "视频1接续动作。视频1"
    assert row["generation"]["generation_intent"]["subject_action"]["progression"] == row["shot"]["intent"]
    assert revised["scenes"][0]["visual_reference_asset_ids"] == [original.asset_id]
    assert row["reference_replacements"] == {"approved-frame": {
        "original_asset_id": original.asset_id, "source_shot_id": "one", "frame_index": 7,
        "conditioning": "source_video", "video_asset_id": video.asset_id,
        "video_asset_sha256": video.sha256}}


def test_preserved_source_reopens_same_accepted_video_and_state_frame(monkeypatch):
    from types import SimpleNamespace
    from ai_video.canvas_source_expression import require_canvas_source_expression
    from ai_video.production.seedance_source_expression import (
        PreservedSourceExpression, SourceReferenceMaterial, SourceReferencePart,
        SourceTextPart, source_parts_sha256,
    )

    snapshot = "e" * 64
    original = SimpleNamespace(asset_id="selected-still", sha256="a" * 64,
        creation_receipt_id=f"canvas-local-selection:{snapshot}:node:resource")
    video = SimpleNamespace(asset_id="accepted-video", sha256="b" * 64)
    frame = SimpleNamespace(asset_id="approved-frame", sha256="c" * 64)
    material = SourceReferenceMaterial(asset_id=video.asset_id, asset_sha256=video.sha256,
        role="video_reference")
    parts = (SourceTextPart(text="保留动作文字。"), SourceReferencePart(slot_id="scene", materials=(material,)))
    expression = PreservedSourceExpression(contract_version="seedance-preserved-source/2",
        source_sha256=source_parts_sha256(parts), parts=parts)
    replacement = {"original_asset_id": original.asset_id, "source_shot_id": "one", "frame_index": 7,
        "conditioning": "source_video", "video_asset_id": video.asset_id,
        "video_asset_sha256": video.sha256}
    row = {"shot": {"preserved_source_expression": expression.model_dump(mode="json")},
        "generation": {"references": [{"asset_id": video.asset_id, "role": "existing_video"}]},
        "reference_replacements": {frame.asset_id: replacement}}
    packet = {"source_snapshot_sha256": snapshot,
        "assets": [{"id": "node", "type": "image", "data": {"resourceId": "resource"}}]}
    unit = {"prompt_source": {"parts": [{"type": "text", "text": "保留动作文字。"},
        {"type": "extension", "object_id": "scene"}]},
        "references": [{"slot_id": "scene", "node_id": "node"}]}
    registry = SimpleNamespace(assets=(original, video, frame))
    loaded = object()
    monkeypatch.setattr("ai_video.canvas_handoff.require_canvas_state_reference",
        lambda *, loaded, asset: {"source_shot_id": "one", "source_request_hash": "accepted-request",
            "reference": {"frame_index": 7, "source_video_sha256": video.sha256}}
        if asset.asset_id == frame.asset_id else pytest.fail("wrong state frame"))
    monkeypatch.setattr("ai_video.canvas_handoff.require_canvas_video_reference",
        lambda *, loaded, asset, source_shot_id: {"source_shot_id": source_shot_id,
            "request_input_hash": "accepted-request", "asset_id": asset.asset_id, "sha256": asset.sha256})

    require_canvas_source_expression(packet=packet, unit=unit, row=row, registry=registry, previous=loaded)

    changed = {**row, "reference_replacements": {frame.asset_id: {**replacement,
        "video_asset_sha256": "f" * 64}}}
    with pytest.raises(ValueError, match="exact original reference"):
        require_canvas_source_expression(packet=packet, unit=unit, row=changed, registry=registry, previous=loaded)


def test_source_video_reference_checks_exact_accepted_mp4_bytes(tmp_path, monkeypatch):
    import hashlib
    from types import SimpleNamespace
    from ai_video.canvas_handoff import require_canvas_video_reference
    from ai_video.production.models import AssetType

    path = tmp_path / "accepted.mp4"
    path.write_bytes(b"exact accepted video")
    video = SimpleNamespace(asset_id="accepted-video", asset_type=AssetType.VIDEO,
        mime_type="video/mp4", video_metadata=object(), sha256=hashlib.sha256(
            b"exact accepted video").hexdigest(), size_bytes=len(b"exact accepted video"))
    source = SimpleNamespace(shot_id="one")
    request = SimpleNamespace(output_asset_id=video.asset_id, request_input_hash="accepted-request")
    monkeypatch.setattr("ai_video.canvas_handoff.accepted_sequence_source",
        lambda loaded, shot: (None, request, None, None, None))
    loaded = SimpleNamespace(shots=(source,), registry=SimpleNamespace(assets=(video,)),
        asset_paths={video.asset_id: path}, root=tmp_path)

    assert require_canvas_video_reference(loaded=loaded, asset=video,
        source_shot_id="one")["request_input_hash"] == request.request_input_hash
    path.write_bytes(b"changed video")
    with pytest.raises(ValueError, match="bytes changed"):
        require_canvas_video_reference(loaded=loaded, asset=video, source_shot_id="one")


def test_source_video_preflight_keeps_state_gate_separate_from_input_admission():
    from types import SimpleNamespace
    from ai_video.canvas_preflight import canvas_reference_preflight

    plan = {"source_shot_id": "one", "frame_index": 7, "replace_asset_id": "scene-placeholder",
        "checks": {"action": "Hand remains on the phone"}, "usage_license": "fixture-only",
        "conditioning": "source_video"}
    replacement = {"original_asset_id": "scene-placeholder", "source_shot_id": "one", "frame_index": 7,
        "conditioning": "source_video", "video_asset_id": "accepted-a", "video_asset_sha256": "a" * 64}
    packet = {"source_snapshot_sha256": "b" * 64, "units": [{"occurrence_id": "b",
        "source_text": "视频1继续动作。", "prompt_source": {"parts": []}}]}
    direction = {"project_id": "continuity-test", "shots": [{"occurrence_id": "b",
        "shot": {"shot_id": "two", "intent": "视频1继续动作。"}, "generation": {
            "references": [{"asset_id": "accepted-a", "role": "existing_video"}]},
        "state_reference": plan, "reference_replacements": {"state-frame": replacement}}],
        "cut_requirements": []}

    report = canvas_reference_preflight(packet=packet, direction=direction, registry=SimpleNamespace(assets=()))

    state = report["shots"][0]["state_reference"]
    assert state["input_kind"] == "source_video"
    assert state["binding_status"] == "DECLARED_BINDING_REQUIRES_GATE"
    assert state["bound_asset_ids"] == ["state-frame"]
    assert state["accepted_video_asset_ids"] == ["accepted-a"]
    assert "same_accepted_original_video_reference_binding" in state["required_evidence"]
    assert state["provider_admission"] == state["state_acceptance"] == "NOT_EVALUATED"


def test_unplanned_intermediate_handoff_cannot_skip_successor_requirements(tmp_path):
    service, provider, limits, auth, aid = state_target(tmp_path)
    accept_current(service, provider, limits, auth)
    service.direction = deepcopy(service.direction)
    service.direction["shots"][1].pop("state_reference")
    service.revise_authoring(attempt_id="remove-state-plan")
    before = service._load()
    gate = reference_gate(service)
    with pytest.raises(Exception, match="approved state reference plan"):
        service.handoff_reference(source_shot_id="one", target_occurrence_id="b", frame_index=7,
                                  replace_asset_id=aid, usage_license="fixture-only", **gate)
    assert gate["session"].calls == 0
    assert service._load().manifest == before.manifest
    assert service._load().registry == before.registry
    assert provider.call_counts.submit == 1


@pytest.mark.parametrize("verdict", ["PASS", "FAIL", "missing"])
def test_successor_requires_its_own_exact_state_findings_before_adoption(tmp_path, verdict):
    from dataclasses import replace
    from ai_video.production.video import VideoProviderCapabilities, VideoGenerationMode
    from ai_video.production.generation_evaluation import GenerationEvaluationSource, GenerationObservation
    from ai_video_mcp.generation_feedback import ControlledPresentationVerifier
    service, provider, limits, auth, aid = state_target(tmp_path)
    accept_current(service, provider, limits, auth)
    service.handoff_reference(source_shot_id="one", target_occurrence_id="b", frame_index=7,
        replace_asset_id=aid, usage_license="fixture-only", **reference_gate(service))
    original = provider.capabilities().variants[0]
    successor = original.model_copy(update={"capability_id": "fixture-state-r2v",
        "mode": VideoGenerationMode.REFERENCE_TO_VIDEO, "required_first_frame": False,
        "allowed_image_roles": ("reference",), "max_reference_count": 1, "max_image_bytes": 1_000_000})
    provider._capabilities = VideoProviderCapabilities.create(provider_name="fake-video", variants=(original, successor))
    provider._scenario = replace(provider._scenario, external_effect_id="successor-state-effect")
    limits = limits.model_copy(update={"allowed_remote_candidates": (*limits.allowed_remote_candidates,
        "fake-video/fixture-state-r2v")})
    submit_and_fetch(service, provider, limits, auth)
    def observations(review):
        items = review.evaluation_items
        return (GenerationEvaluationSource(schema_version="generation-evaluation/2",
            request_hash=items[0].request_hash, artifact_sha256=review.analysis.artifact_sha256,
            size_bytes=review.analysis.size_bytes, rubric_hash=items[0].rubric_hash,
            qa_policy_content_hash=review.qa_policy.content_hash, qa_policy_snapshot=review.qa_policy,
            analysis_evidence=review.analysis, evaluator=review.qa_policy.semantic_authorities[0], proof="technical",
            observations=tuple(GenerationObservation(requirement_id=item.requirement_id,
                verdict=verdict if item.requirement_id.startswith("canvas-state-") else "PASS",
                observation="Explicit controlled successor fixture observation", evaluation_item_hash=item.evaluation_item_hash,
                question_text=item.question_text, presentation_ref=review.presentation_ref, answer_ref=review.answer_ref)
                for item in items if not (verdict == "missing" and item.requirement_id.startswith("canvas-state-")))),)
    verifier = ControlledPresentationVerifier(evaluator=service._load().qa_policy.semantic_authorities[0],
        proof="technical", adjudicate=observations)
    result = asyncio.run(service.evaluate(session=Session(), presentation_verifier=verifier))
    assert result.all_required_observed_pass is (verdict == "PASS")
    if verdict == "PASS":
        service.execute(action="validate")
        service.execute(action="activate")
        assert service.position().next_action == "compose"
    else:
        with pytest.raises(Exception, match="media Gate"):
            service.execute(action="validate")
        assert service.position().shot_id == "two"
    assert provider.call_counts.submit == 2


def test_successor_state_qa_projection_is_typed_and_missing_inventory_blocks_before_submit(tmp_path):
    from ai_video.canvas_target_gate import target_state_qa_rules, require_target_state_inventory
    from ai_video.production.generation_recipe import RequirementExpression
    service, provider, _, _, _ = state_target(tmp_path)
    row = service.direction["shots"][1]
    rules = target_state_qa_rules(direction=service.direction, row=row, proof="technical")
    assert {RequirementExpression.model_validate(rule).requirement_id for rule in rules} == set(target_state_requirements(row))
    changed = deepcopy(row)
    changed["state_reference"]["checks"]["identity"] = "Required unchanged identity"
    with pytest.raises(ValueError, match="canvas-state-b-identity"):
        require_target_state_inventory(loaded=service._load(), row=changed)
    assert provider.call_counts.submit == 0


def cut_data(service):
    data = deepcopy(service.direction)
    data["cut_requirements"] = [{"from_occurrence_id": "a", "to_occurrence_id": "b", "kind": "scene_reset",
        "checks": {"identity": "Selected traveller remains identifiable", "camera": "Intentional viewpoint change",
                   "audio": "Required audible transition is checked"}}]
    return data


@pytest.mark.parametrize("damage", ["missing", "dimension", "order", "kind"])
def test_cut_contract_rejects_missing_ambiguous_or_inapplicable_checks(tmp_path, damage):
    service, _, _, _ = runtime(tmp_path)
    data = cut_data(service)
    if damage == "missing": data["cut_requirements"] = []
    if damage == "dimension": data["cut_requirements"][0]["checks"]["shared_picture"] = "Same picture"
    if damage == "order": data["composition_order"] = ["b", "a"]
    if damage == "kind": data["cut_requirements"][0]["kind"] = "automatic_tail_frame"
    with pytest.raises(ValueError):
        canvas_cut_contract(data)


def render_final(tmp_path, monkeypatch, *, insert=False):
    from dataclasses import replace
    import subprocess
    from production_e2e_support import DeterministicHyperFramesRunner, require_audio_toolchain
    from ai_video.production.hyperframes import RendererCommandResult
    from test_canvas_render import _executable
    service, provider, limits, auth = runtime(tmp_path)
    data = cut_data(service)
    if insert:
        from test_canvas_sequence_packet import document
        from scripts.canvas_sequence_packet import build_sequence_packet
        raw = document()
        node = deepcopy(next(n for n in raw["nodes"] if n["id"] == "a"))
        node["id"] = "c"
        raw["nodes"].append(node)
        raw["edges"].extend([{**e, "id": e["id"] + "-c", "target": "c"}
                              for e in deepcopy(raw["edges"]) if e["target"] == "a"])
        service.packet = build_sequence_packet(raw, {"node_ids": ["a", "b", "c"]})
        aid = service.direction["shots"][0]["generation"]["references"][0]["asset_id"]
        data["shots"].append({"occurrence_id": "c", "adaptation_reason": "Scripted static insert fixture",
            "boundary": {"independent": True, "reason": "Explicit insert"}, "shot": {"shot_id": "insert",
            "scene_id": "road", "storyboard_beat_id": "arrival", "intent": "Scripted reaction insert",
            "duration_policy": {"mode": "fixed", "seconds": 1}, "visual_strategy": "static_image",
            "required_asset_roles": [{"role": "primary_visual", "asset_ids": [aid], "allowed_asset_types": ["image"]}]}})
        data["storyboard"]["beats"][0]["shot_ids"].append("insert")
        data["composition_order"] = ["a", "c", "b"]
        data["cut_requirements"] = [{"from_occurrence_id": a, "to_occurrence_id": b, "kind": "insert",
            "checks": {"action": "Reaction insert preserves the resumed action", "camera": "Declared viewpoint relation"}}
            for a, b in (("a", "c"), ("c", "b"))]
    service.direction = data
    service.revise_authoring(attempt_id="cut-goal")
    loaded = service._load()
    policy = seal_artifact(loaded.qa_policy.model_copy(update={"final_output": canvas_cut_contract(service.direction),
        "revision": loaded.qa_policy.revision + 1}))
    service.committer.activate_qa_policy(policy, expected_manifest_revision=loaded.manifest.manifest_revision,
                                         attempt_id="cut-policy")
    tools = require_audio_toolchain()
    second = tmp_path / "successor.mp4"
    subprocess.run([str(tools.ffmpeg_path), "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i",
        "color=c=green:s=64x64:r=24:d=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-threads", "1",
        str(second)], capture_output=True, check=True)
    for index in range(2):
        if index:
            provider._artifact_bytes = second.read_bytes()
        provider._scenario = replace(provider._scenario, external_effect_id=f"cut-effect-{index}")
        accept_current(service, provider, limits, auth)
    class Renderer(DeterministicHyperFramesRunner):
        def run(self, command, args, **kwargs):
            if command != "render":
                return super().run(command, args, **kwargs)
            result = subprocess.run([str(tools.ffmpeg_path), "-nostdin", "-v", "error", "-y", "-f", "lavfi",
                "-i", f"color=c=blue:s=64x64:r=24:d={3 if insert else 2}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-threads", "1", args[args.index("-o") + 1]], capture_output=True)
            return RendererCommandResult(returncode=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode())
    runner = Renderer(tools.ffmpeg_path)
    # Same deterministic renderer seam used by Production E2E; no quality claim.
    monkeypatch.setattr("ai_video.production.hyperframes._NetworkIsolatedHyperFramesRunner", lambda **_: runner)
    fake = tmp_path / "tools"
    toolchain = {"binary_path": fake / "node_modules/.bin/hyperframes",
        **{name + "_path": _executable(fake / name) for name in ("browser", "unshare", "ip", "bash")},
        "ffmpeg_path": tools.ffmpeg_path, "ffprobe_path": tools.ffprobe_path}
    service.render(attempt_id="cut-render", toolchain=toolchain)
    return service


def test_insert_is_composed_between_generated_dependents_from_canonical_spans(tmp_path, monkeypatch):
    service = render_final(tmp_path, monkeypatch, insert=True)
    loaded, timeline = service.deliver()
    assert [s for b in loaded.storyboard.beats for s in b.shot_ids] == ["one", "two", "insert"]
    assert [s.shot_id for s in timeline.visual_spans] == ["one", "insert", "two"]
    packet = service.cut_packet()
    assert [(c["evidence"]["from"]["start_frame"], c["evidence"]["to"]["start_frame"]) for c in packet["cuts"]] == [(0, 24), (24, 48)]
    assert len([a for a in loaded.manifest.attempts if a.operation == "video_generation"]) == 2
    assert packet["production_acceptance"] == "NOT_EVALUATED"


def test_final_cut_review_missing_human_proof_is_not_evaluated_and_replay_is_zero_effect(tmp_path, monkeypatch):
    from ai_video.production.models import QaVerdict
    service = render_final(tmp_path, monkeypatch)
    session = Session()
    def adjudicate(packet, request, raw):
        return {"contract_hash": service._load().qa_policy.final_output.contract_hash,
                "review_request_content_hash": request.content_hash,
                "findings": [{"requirement_id": r["requirement_id"], "verdict": "pass",
                              "observation": "Scripted explicit cut observation"}
                             for r in packet["contract"]["requirements"] if r["proof"] == "evaluator"]}
    args = dict(attempt_id="edited-cut-review", session=session, adjudicate=adjudicate,
                tool_identity=service._load().qa_policy.semantic_authorities[0])
    receipt = service.review_delivery(**args)
    assert receipt.verdict is QaVerdict.NOT_EVALUATED
    before = service._load().manifest.manifest_revision
    assert service.review_delivery(**args) == receipt
    assert service._load().manifest.manifest_revision == before
    assert session.calls == 1
    assert service._load().manifest.final_acceptance_state is None


@pytest.mark.parametrize("duration_mode", ["fixed", "content_driven"])
def test_native_audio_follows_resolved_trim_and_edit_order_with_identical_source_bytes(tmp_path, duration_mode):
    from dataclasses import replace
    import subprocess
    from production_e2e_support import require_audio_toolchain
    tools = require_audio_toolchain()
    media = tmp_path / "native.mp4"
    subprocess.run([str(tools.ffmpeg_path), "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i",
        "color=c=blue:s=64x64:r=24:d=1", "-f", "lavfi", "-i", "sine=frequency=600:sample_rate=48000:duration=1",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-threads", "1", "-c:a", "aac", "-ar", "48000", "-ac", "2",
        str(media)], capture_output=True, check=True)
    service, provider, limits, auth = runtime(tmp_path, native_media=media.read_bytes())
    data = deepcopy(service.direction)
    data["composition_order"] = ["b", "a"]
    for row in data["shots"]:
        row["shot"]["duration_policy"]["mode"] = duration_mode
        row["shot"]["duration_policy"]["seconds"] = 0.5
        row["generation"]["output_need"] = {"duration_seconds": 1, "width": 64, "height": 64,
            "fps": 24, "container_mime": "video/mp4"}
        row["composition"]["trim_start_frame"] = 6
    service.direction = data
    service.revise_authoring(attempt_id="audio-trim-order")
    for index, shot_id in enumerate(("one", "two")):
        provider._scenario = replace(provider._scenario, external_effect_id=f"audio-effect-{index}")
        accept_current(service, provider, limits, auth)
        service.register_native_audio(shot_id=shot_id, audio_kind="ambience", usage_license="fixture-only", toolchain=tools)
    spec, timeline = service.compose()
    assert spec.shot_ids == ("two", "one")
    assert [s.trim_start_frame for s in timeline.visual_spans] == [6, 6]
    frames = 12 if duration_mode == "fixed" else 18
    samples = frames * 2000
    assert [s.duration_frames for s in timeline.visual_spans] == [frames, frames]
    assert [(s.track_id, s.start_sample, s.source_start_sample, s.duration_samples)
            for s in sorted(timeline.audio_spans, key=lambda s: s.start_sample)] == [
        ("canvas-native-two", 0, 12000, samples), ("canvas-native-one", samples, 12000, samples)]
    assert provider.call_counts.submit == 2
