"""Edited-cut evidence adapter; P6 owns every receipt and acceptance transition."""
import asyncio
import hashlib

from ai_video.production.final_output_contracts import FinalOutputContract, FinalOutputRequirement
from ai_video.production.final_output_review import FinalOutputObservation
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    EvidenceStrength, QaLayer, ReviewEvidence, ReviewEvidencePointer, ReviewReceipt,
    ReviewRequest, SourceReference, StateCommitStatus,
)
from ai_video.production.paths import canonical_review_evidence_path
from ai_video.production.review import adjudicate_review_evidence, build_technical_review_context
from ai_video.production.state_commit import _canonical_json_bytes


DIMENSIONS = {"identity", "props", "action", "space", "motion_direction", "camera", "audio"}


def canvas_cut_contract(direction):
    rows = {r["occurrence_id"]: r for r in direction["shots"]}
    order = direction.get("composition_order", list(rows))
    pairs = list(zip(order, order[1:]))
    cuts = direction.get("cut_requirements", [])
    if [(c["from_occurrence_id"], c["to_occurrence_id"]) for c in cuts] != pairs:
        raise ValueError("cut_requirements must cover every actual edited junction in composition order")
    requirements = []
    for index, cut in enumerate(cuts):
        if set(cut) != {"from_occurrence_id", "to_occurrence_id", "kind", "checks"}:
            raise ValueError("cut requirement needs exact occurrences, kind and selected checks")
        if cut["kind"] not in {"continuous", "insert", "scene_reset"}:
            raise ValueError("cut kind must describe continuous action, an insert, or an intentional scene reset")
        checks = cut["checks"]
        if not isinstance(checks, dict) or not checks or set(checks) - DIMENSIONS:
            raise ValueError("cut checks must select actual identity/prop/action/space/motion/camera/audio obligations")
        for dimension, observable in sorted(checks.items()):
            if not isinstance(observable, str) or not observable.strip():
                raise ValueError("each selected cut dimension needs an observable requirement")
            requirements.append(FinalOutputRequirement(requirement_id=f"cut-{index}-{dimension}",
                observable=f"{cut['from_occurrence_id']} → {cut['to_occurrence_id']} ({cut['kind']}): {observable}",
                proof="evaluator"))
    requirements.append(FinalOutputRequirement(requirement_id="whole-playback",
        observable="User watches and hears the exact complete final film at 1.0x and accepts it", proof="human"))
    return FinalOutputContract(goal_id=f"canvas-{direction['project_id']}", goal_version=canonical_sha256({"cuts": cuts}),
        user_goal="Preserve the canvas story and verify every edited junction and complete audiovisual delivery",
        requirements=tuple(requirements))


def canvas_cut_packet(*, loaded, timeline, direction):
    """Read cut positions solely from the canonical resolved visual/audio spans."""
    contract = canvas_cut_contract(direction)
    rows = {r["occurrence_id"]: r for r in direction["shots"]}
    assets = {a.asset_id: a for a in loaded.registry.assets}
    spans = {}
    for span in timeline.visual_spans:
        spans.setdefault((span.shot_id, span.asset_role), []).append(span)
    cuts = []
    for authored in direction.get("cut_requirements", []):
        evidence = {}
        for side, key in (("from", "from_occurrence_id"), ("to", "to_occurrence_id")):
            row = rows[authored[key]]
            role = row.get("composition", {}).get("asset_role", "primary_visual")
            pieces = sorted(spans[(row["shot"]["shot_id"], role)], key=lambda s: s.start_frame)
            first, last = pieces[0], pieces[-1]
            if (len({s.asset_id for s in pieces}) != 1 or any(
                    a.start_frame + a.duration_frames != b.start_frame for a, b in zip(pieces, pieces[1:]))):
                raise ValueError("cut evidence needs one contiguous resolved primary visual")
            asset = assets[first.asset_id]
            source_duration = last.trim_duration_frames or last.duration_frames
            evidence[side] = {"shot_id": first.shot_id, "asset_id": asset.asset_id, "asset_sha256": asset.sha256,
                "start_frame": first.start_frame, "duration_frames": last.start_frame + last.duration_frames - first.start_frame,
                "source_start_frame": first.trim_start_frame,
                "source_last_frame": last.trim_start_frame + (last.duration_frames - 1) * source_duration // last.duration_frames,
                "resolved_segments": [{"start_frame": s.start_frame, "duration_frames": s.duration_frames,
                    "source_start_frame": s.trim_start_frame,
                    "source_duration_frames": s.trim_duration_frames or s.duration_frames} for s in pieces],
                "references": row.get("reference_replacements", {}),
                "audio_spans": [s.model_dump(mode="json") for s in timeline.audio_spans
                    if s.start_sample < last.start_sample + last.duration_samples
                    and s.start_sample + s.duration_samples > first.start_sample]}
        if evidence["from"]["start_frame"] + evidence["from"]["duration_frames"] != evidence["to"]["start_frame"]:
            raise ValueError("cut requirements differ from actual adjacent resolved spans")
        cuts.append({**authored, "evidence": evidence})
    return {"contract": contract.model_dump(mode="json"), "cuts": cuts,
        "render_output_sha256": loaded.render_state.output.file_sha256,
        "timeline_fingerprint": timeline.composition_fingerprint,
        "production_acceptance": "NOT_EVALUATED"}


def review_canvas_delivery(*, service, attempt_id, session, adjudicate, tool_identity,
                           strength=EvidenceStrength.EXPLICIT_EVALUATOR):
    """One exact final-MP4 MCP observation under the canonical durable P6 permit.

    The caller supplies explicit findings; neither raw analysis nor reference
    extraction manufactures a match. Unknown analysis cannot be rerun blindly.
    """
    loaded, timeline = service.deliver()
    packet = canvas_cut_packet(loaded=loaded, timeline=timeline, direction=service.direction)
    policy, manifest = loaded.qa_policy, loaded.manifest
    contract = canvas_cut_contract(service.direction)
    if policy.final_output != contract or tool_identity not in policy.semantic_authorities:
        raise ValueError("delivery review requires the selected exact canvas contract and evaluator authority")
    identity = canonical_sha256({"attempt": attempt_id, "packet": packet, "policy": policy.content_hash})
    existing = next((a for a in manifest.attempts if a.attempt_id == attempt_id), None)
    if existing is not None:
        if existing.operation != "review" or existing.status is not StateCommitStatus.SUCCEEDED:
            raise ValueError("delivery review has an unknown/unfinished outcome; use canonical recovery")
        from ai_video.production.project import load_review_request, load_review_receipt
        request = load_review_request(loaded.root, existing.review_request)
        if (request.render_output_sha256 != packet["render_output_sha256"]
                or request.timeline_fingerprint != packet["timeline_fingerprint"]
                or request.qa_policy != manifest.active_qa_policy
                or request.dependency_graph != manifest.active_dependency_graph):
            raise ValueError("delivery review replay is stale")
        return load_review_receipt(loaded.root, next(p for p in manifest.active_review_receipts
                if p.review_id == identity))
    context = build_technical_review_context(loaded, timeline,
        render_output_sha256=packet["render_output_sha256"], measurement_contract_version="canvas-edited-cuts/1")
    request = seal_artifact(ReviewRequest(artifact_id=f"canvas-review-{identity}", request_id=identity,
        revision=1, content_hash="0" * 64, creation_receipt_id=attempt_id,
        source_provenance=(SourceReference(kind="derived", reference="canvas-edited-cuts", content_hash=canonical_sha256(packet)),),
        base_manifest_revision=manifest.manifest_revision, dependency_graph=manifest.active_dependency_graph,
        dependency_states_hash=canonical_sha256({"dependency_states": [s.model_dump(mode="json") for s in manifest.dependency_states]}),
        render_state=manifest.active_render_state, render_output_sha256=packet["render_output_sha256"],
        timeline_fingerprint=packet["timeline_fingerprint"], qa_policy=manifest.active_qa_policy,
        requested_layers=(QaLayer.SEMANTIC,), evidence_tool_identities=(tool_identity,), technical_context=context))
    begun = service.committer.begin_review(request, attempt_id=attempt_id)
    pointer = next(a.review_request for a in begun.attempts if a.attempt_id == attempt_id)
    def analyzer(durable, permit):
        if not permit._consume_review_analysis_permit(request_content_hash=durable.content_hash,
                render_output_sha256=durable.render_output_sha256,
                technical_context_hash=canonical_sha256(durable.technical_context.model_dump(mode="json"))):
            raise ValueError("delivery analysis permit was already consumed")
        result = asyncio.run(session.call_tool("video_analyze", arguments={"video_path": str(
            loaded.root / loaded.render_state.output.path)}))
        result = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        if not isinstance(result, dict) or result.get("isError", False):
            raise ValueError("exact final video-analysis MCP observation is unavailable")
        import json
        from ai_video.production.generation_evaluation import GenerationAnalysisEvidence
        analysis = GenerationAnalysisEvidence(artifact_sha256=durable.render_output_sha256,
            size_bytes=loaded.render_state.output.size_bytes,
            response_json=json.dumps(result, sort_keys=True, separators=(",", ":")))
        if analysis.payload["video_path"] != str(loaded.root / loaded.render_state.output.path):
            raise ValueError("final analysis identifies different media")
        current, _ = service.deliver()
        if current.render_state != loaded.render_state:
            raise ValueError("final render changed during cut analysis")
        observation = FinalOutputObservation.model_validate(adjudicate(packet, durable, result))
        if strength is EvidenceStrength.HUMAN and (observation.viewing_mode != "full_playback"
                or observation.viewing_speed_milli != 1000):
            raise ValueError("human final evidence requires complete 1.0x viewing and listening")
        return seal_artifact(ReviewEvidence(artifact_id=f"canvas-evidence-{identity}", evidence_id=identity,
            revision=1, content_hash="0" * 64, creation_receipt_id=attempt_id,
            source_provenance=(SourceReference(kind="derived", reference=durable.content_hash),),
            layer=QaLayer.SEMANTIC, strength=strength, render_output_sha256=durable.render_output_sha256,
            timeline_fingerprint=durable.timeline_fingerprint, dependency_graph_revision_id=durable.dependency_graph.revision_id,
            tool_identity=tool_identity, measurement_contract_version=context.measurement_contract_version,
            subject_ids=tuple(s.shot_id for s in loaded.shots), measured_payload={"cuts": packet,
                "raw_analysis": result, "coverage_complete": True,
                "evaluator_identity": f"{tool_identity.name}@{tool_identity.version}",
                "final_output": observation.model_dump(mode="json")}))
    evidence = service.committer.run_review_analysis(review_request=pointer,
        expected_manifest_revision=begun.manifest_revision, analyzer=analyzer)
    evidence_pointer = ReviewEvidencePointer(path=canonical_review_evidence_path(evidence.content_hash),
        evidence_id=evidence.evidence_id, layer=evidence.layer, strength=evidence.strength,
        content_hash=evidence.content_hash, file_sha256=hashlib.sha256(_canonical_json_bytes(evidence)).hexdigest())
    verdict = adjudicate_review_evidence(policy, QaLayer.SEMANTIC, (evidence,),
        review_request_content_hash=request.content_hash)
    receipt = seal_artifact(ReviewReceipt(artifact_id=f"canvas-receipt-{identity}", review_id=identity,
        revision=1, content_hash="0" * 64, creation_receipt_id=attempt_id,
        source_provenance=evidence.source_provenance, layer=QaLayer.SEMANTIC, review_request=pointer,
        render_state=request.render_state, render_output_sha256=request.render_output_sha256,
        timeline_fingerprint=request.timeline_fingerprint, dependency_graph_revision_id=request.dependency_graph.revision_id,
        qa_policy=request.qa_policy, evidence=(evidence_pointer,), evidence_ids=(evidence.evidence_id,),
        tool_identities=(tool_identity,), verdict=verdict))
    service.committer.record_review_receipt(receipt, (evidence,),
        expected_manifest_revision=service._load().manifest.manifest_revision, attempt_id=attempt_id)
    return receipt
