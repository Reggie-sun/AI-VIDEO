"""Measured ordinary frame references from the canonical accepted-source owner.

This module prepares immutable artifacts. Only ProductionStateCommitter writes
them; the frame is a reference, never a fabricated terminal or semantic PASS.
"""
from dataclasses import dataclass
from io import BytesIO
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image

from ai_video.production._sequence_source import accepted_sequence_source
from ai_video.production.hashing import canonical_sha256
from ai_video.production.image import measure_png_bytes
from ai_video.production.image_import_video_frame import (
    VideoFrameImageImportReferenceBinding, _decode_selected_frame_rgb,
    validate_video_frame_reference_bytes,
)
from ai_video.production.models import AssetRecord, AssetSourceKind, AssetType, ToolIdentity
from ai_video.production.paths import _read_regular_file_nofollow, canonical_image_asset_path
from ai_video.production.state_commit import PreparedArtifact


@dataclass(frozen=True)
class CanvasStateReference:
    asset: AssetRecord
    artifacts: tuple[PreparedArtifact, ...]
    source_shot_id: str
    source_request_hash: str
    reference: VideoFrameImageImportReferenceBinding


def assess_canvas_state_reference(*, loaded, selected, checks, session, adjudicate, tool_identity):
    """Explicit MCP observation of the source at the selected state, before binding."""
    import asyncio
    from dataclasses import replace
    from ai_video.production.generation_evaluation import GenerationAnalysisEvidence
    from ai_video.production.review import ContinuityCheckMeasurement
    from ai_video.canvas_review import DIMENSIONS
    if not isinstance(checks, dict) or not checks or set(checks) - DIMENSIONS:
        raise ValueError("state reference needs selected continuity dimensions and observable requirements")
    if loaded.qa_policy is None or tool_identity not in loaded.qa_policy.semantic_authorities:
        raise ValueError("state reference evaluator must be selected by the current QA policy")
    video = next(a for a in loaded.registry.assets if a.asset_id in selected.asset.input_artifact_ids)
    context = {"source_shot_id": selected.source_shot_id, "source_request_hash": selected.source_request_hash,
        "source_video_sha256": video.sha256, "frame_sha256": selected.asset.sha256,
        "frame_index": selected.reference.frame_index, "checks": checks}
    result = asyncio.run(session.call_tool("video_analyze", arguments={
        "video_path": str(loaded.asset_paths[video.asset_id]), "extract_frames": True,
        "transcribe_audio": False, "detect_scenes": True}))
    response = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    analysis = GenerationAnalysisEvidence(artifact_sha256=video.sha256, size_bytes=video.size_bytes,
        response_json=json.dumps(response, sort_keys=True, separators=(",", ":")))
    if analysis.payload["video_path"] != str(loaded.asset_paths[video.asset_id]):
        raise ValueError("state analysis identifies different source media")
    findings = adjudicate(context, analysis, selected)
    if not isinstance(findings, dict) or set(findings) != set(checks):
        raise ValueError("state reference Gate is NOT_EVALUATED: missing required findings")
    measured = {name: ContinuityCheckMeasurement.model_validate(value) for name, value in findings.items()}
    if any(value.expected != checks[name] or value.status != "match" for name, value in measured.items()):
        raise ValueError("state reference Gate is FAIL or NOT_EVALUATED")
    assessment = {"context": context, "findings": {k: v.model_dump(mode="json") for k, v in measured.items()},
        "evaluator": tool_identity.model_dump(mode="json"), "qa_policy_content_hash": loaded.qa_policy.content_hash,
        "analysis": analysis.model_dump(mode="json")}
    artifacts = [a for a in selected.artifacts if a.relative_path.suffix != ".json"]
    evidence = json.loads(next(a.payload for a in selected.artifacts if a.relative_path.suffix == ".json"))
    evidence["assessment"] = assessment
    identity = canonical_sha256(evidence)
    data = (json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    artifacts.append(PreparedArtifact(Path(f"evidence/video-frame-import/{identity}.json"), data,
                                      hashlib.sha256(data).hexdigest()))
    asset = selected.asset.model_copy(update={"asset_id": f"canvas-state-{identity}", "input_fingerprint": identity,
        "creation_receipt_id": f"canvas-state-reference:{identity}"})
    return replace(selected, asset=asset, artifacts=tuple(artifacts))


def prepare_canvas_state_reference(*, loaded, source_shot_id, frame_index, usage_license):
    if type(frame_index) is not int or frame_index < 0:
        raise ValueError("state reference frame_index must be a nonnegative integer")
    source = next(s for s in loaded.shots if s.shot_id == source_shot_id)
    _, request, _, _, _ = accepted_sequence_source(loaded, source)
    video = next(a for a in loaded.registry.assets if a.asset_id == request.output_asset_id)
    if video.video_metadata is None or frame_index >= video.video_metadata.frame_count:
        raise ValueError("state reference frame_index is outside the accepted source")
    raw = _read_regular_file_nofollow(loaded.asset_paths[video.asset_id], contained_by=loaded.root)
    if raw.file_sha256 != video.sha256 or len(raw.data) != video.size_bytes:
        raise ValueError("state reference accepted source bytes changed")
    width, height, rgb = _decode_selected_frame_rgb(raw.data, frame_index)
    output = BytesIO()
    Image.frombytes("RGB", (width, height), rgb).save(output, format="PNG")
    png = output.getvalue()
    measured = measure_png_bytes(png)
    version = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True,
        check=True, timeout=3).stdout.splitlines()[0].split()[2]
    reference = VideoFrameImageImportReferenceBinding(
        role="video_frame", source_video_path=Path(f"evidence/video-frame-import/{video.sha256}.mp4"),
        source_video_sha256=video.sha256, source_video_size_bytes=video.size_bytes,
        extracted_frame_path=Path(f"evidence/video-frame-import/{measured.sha256}.png"),
        extracted_frame_sha256=measured.sha256, extracted_frame_size_bytes=measured.size_bytes,
        extracted_frame_width=width, extracted_frame_height=height, frame_index=frame_index,
        extraction_contract_version="video-frame-import-v1", extractor_name="ffmpeg", extractor_version=version)
    validate_video_frame_reference_bytes(reference, source_video_bytes=raw.data,
        extracted_frame_bytes=png, verify_derivation=True)
    evidence = {"source_shot_id": source_shot_id, "source_request_hash": request.request_input_hash,
                "reference": reference.model_dump(mode="json")}
    identity = canonical_sha256(evidence)
    path = canonical_image_asset_path(measured.sha256)
    asset = AssetRecord(asset_id=f"canvas-state-{identity}", asset_type=AssetType.IMAGE,
        artifact_path=path, sha256=measured.sha256, size_bytes=measured.size_bytes, mime_type="image/png",
        width=width, height=height, source_kind=AssetSourceKind.GENERATED,
        tool=ToolIdentity(name="canvas-accepted-state-frame", version="1"),
        input_artifact_ids=(video.asset_id,), input_fingerprint=identity,
        creation_receipt_id=f"canvas-state-reference:{identity}", usage_license=usage_license)
    evidence_bytes = (json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    payloads = {path: png, reference.source_video_path: raw.data, reference.extracted_frame_path: png,
                Path(f"evidence/video-frame-import/{identity}.json"): evidence_bytes}
    artifacts = tuple(PreparedArtifact(p, data, hashlib.sha256(data).hexdigest())
                      for p, data in sorted(payloads.items()))
    return CanvasStateReference(asset, artifacts, source_shot_id, request.request_input_hash, reference)


def require_canvas_video_reference(*, loaded, asset, source_shot_id):
    """Require the exact Registry MP4 produced by an accepted predecessor Shot."""
    source = next((shot for shot in loaded.shots if shot.shot_id == source_shot_id), None)
    if source is None:
        raise ValueError("source video reference requires an exact accepted predecessor Shot")
    _, request, _, _, _ = accepted_sequence_source(loaded, source)
    video = next((item for item in loaded.registry.assets if item.asset_id == request.output_asset_id), None)
    if (video is None or video.asset_type is not AssetType.VIDEO or asset != video
            or video.mime_type != "video/mp4" or video.video_metadata is None):
        raise ValueError("source video reference must be the predecessor's exact accepted original MP4")
    raw = _read_regular_file_nofollow(loaded.asset_paths[video.asset_id], contained_by=loaded.root)
    if raw.file_sha256 != video.sha256 or len(raw.data) != video.size_bytes:
        raise ValueError("accepted source video bytes changed before successor binding")
    return {"source_shot_id": source_shot_id, "request_input_hash": request.request_input_hash,
            "asset_id": video.asset_id, "sha256": video.sha256, "size_bytes": video.size_bytes}


def require_canvas_state_reference(*, loaded, asset):
    if asset.tool != ToolIdentity(name="canvas-accepted-state-frame", version="1"):
        raise ValueError("state reference requires its measured extraction owner")
    identity = asset.input_fingerprint
    raw = _read_regular_file_nofollow(loaded.root / f"evidence/video-frame-import/{identity}.json",
                                    contained_by=loaded.root)
    evidence = json.loads(raw.data)
    if canonical_sha256(evidence) != identity or asset.creation_receipt_id != f"canvas-state-reference:{identity}":
        raise ValueError("state reference extraction identity changed")
    reference = VideoFrameImageImportReferenceBinding.model_validate(evidence["reference"])
    from ai_video.production.generation_evaluation import GenerationAnalysisEvidence
    from ai_video.production.review import ContinuityCheckMeasurement
    assessment = evidence.get("assessment")
    if not isinstance(assessment, dict):
        raise ValueError("state reference lacks the explicit selected-state Gate")
    context = assessment["context"]
    if (loaded.qa_policy is None or assessment["qa_policy_content_hash"] != loaded.qa_policy.content_hash
            or ToolIdentity.model_validate(assessment["evaluator"]) not in loaded.qa_policy.semantic_authorities
            or context["source_shot_id"] != evidence["source_shot_id"]
            or context["source_request_hash"] != evidence["source_request_hash"]
            or context["frame_index"] != reference.frame_index
            or context["frame_sha256"] != asset.sha256
            or context["source_video_sha256"] != reference.source_video_sha256
            or not context["checks"] or set(assessment["findings"]) != set(context["checks"])):
        raise ValueError("state reference Gate is missing, stale or bound to another state")
    analysis = GenerationAnalysisEvidence.model_validate(assessment["analysis"])
    if analysis.artifact_sha256 != reference.source_video_sha256:
        raise ValueError("state reference analysis identifies different accepted source bytes")
    for dimension, data in assessment["findings"].items():
        finding = ContinuityCheckMeasurement.model_validate(data)
        if finding.expected != context["checks"][dimension] or finding.status != "match":
            raise ValueError("state reference Gate is FAIL or NOT_EVALUATED")
    source = next(s for s in loaded.shots if s.shot_id == evidence["source_shot_id"])
    _, request, _, _, _ = accepted_sequence_source(loaded, source)
    video = next(a for a in loaded.registry.assets if a.asset_id == request.output_asset_id)
    if (request.request_input_hash != evidence["source_request_hash"]
            or video.sha256 != reference.source_video_sha256 or asset.sha256 != reference.extracted_frame_sha256
            or asset.input_artifact_ids != (video.asset_id,)
            or (asset.width, asset.height, asset.size_bytes) != (reference.extracted_frame_width,
                reference.extracted_frame_height, reference.extracted_frame_size_bytes)):
        raise ValueError("state reference is not from the current accepted predecessor")
    source_bytes = _read_regular_file_nofollow(loaded.asset_paths[video.asset_id], contained_by=loaded.root).data
    frame = _read_regular_file_nofollow(loaded.asset_paths[asset.asset_id], contained_by=loaded.root).data
    validate_video_frame_reference_bytes(reference, source_video_bytes=source_bytes,
        extracted_frame_bytes=frame, verify_derivation=True)
    return evidence


def replace_state_reference(*, direction, loaded, target_occurrence_id, replace_asset_id,
                            asset, source_shot_id, frame_index):
    from copy import deepcopy
    from ai_video.production.seedance_source_expression import source_parts_sha256
    data = deepcopy(direction)
    row = next(r for r in data["shots"] if r["occurrence_id"] == target_occurrence_id)
    source = next(s for s in loaded.shots if s.shot_id == source_shot_id)
    target_id = row["shot"]["shot_id"]
    order = [r["shot"]["shot_id"] for r in data["shots"]]
    if order.index(source_shot_id) >= order.index(target_id):
        raise ValueError("state reference must consume an earlier accepted source")
    if source.scene_id == row["shot"]["scene_id"]:
        raise ValueError("state replacement needs a target Scene reference owner separate from the source")
    refs = row["generation"]["references"]
    state_plan = row.get("state_reference") or {}
    conditioning = state_plan.get("conditioning", "extracted_frame")
    if conditioning not in {"extracted_frame", "source_video"}:
        raise ValueError("state reference has an unsupported conditioning mode")
    accepted_video = None
    if conditioning == "source_video":
        _, request, _, _, _ = accepted_sequence_source(loaded, source)
        accepted_video = next((a for a in loaded.registry.assets if a.asset_id == request.output_asset_id), None)
        if accepted_video is None or accepted_video.asset_type is not AssetType.VIDEO:
            raise ValueError("source video conditioning requires the accepted predecessor's Registry MP4")
        require_canvas_video_reference(loaded=loaded, asset=accepted_video, source_shot_id=source_shot_id)
    matches = [r for r in refs if r["asset_id"] == replace_asset_id]
    if len(matches) != 1 or matches[0]["role"] != "scene_reference":
        raise ValueError("ordinary state replacement requires one selected scene reference")
    scene = next(s for s in data["scenes"] if s["scene_id"] == row["shot"]["scene_id"])
    if replace_asset_id not in scene.get("visual_reference_asset_ids", ()):
        raise ValueError("state replacement differs from the target Scene selection")
    replacement_asset = asset if conditioning == "extracted_frame" else accepted_video
    replacement_role = "scene_reference" if conditioning == "extracted_frame" else "existing_video"
    matches[0]["asset_id"] = replacement_asset.asset_id
    matches[0]["role"] = replacement_role
    if conditioning == "extracted_frame":
        scene["visual_reference_asset_ids"] = [asset.asset_id if a == replace_asset_id else a
                                              for a in scene["visual_reference_asset_ids"]]
        for role in row["shot"]["required_asset_roles"]:
            role["asset_ids"] = [asset.asset_id if a == replace_asset_id else a
                                  for a in role["asset_ids"]]
    expression = row["shot"].get("preserved_source_expression")
    if expression is not None:
        materials = [m for p in expression["parts"] if p["type"] == "reference" for m in p["materials"]]
        materials.extend(expression.get("implicit_references", ()))
        selected = [m for m in materials if m["asset_id"] == replace_asset_id]
        if not selected or any(m["role"] != "scene" for m in selected):
            raise ValueError("ordinary state replacement must retain its original scene chip")
        for material in selected:
            material.update(asset_id=replacement_asset.asset_id, asset_sha256=replacement_asset.sha256,
                            role="scene" if conditioning == "extracted_frame" else "video_reference")
        for alias in expression.get("image_aliases", ()):
            alias["asset_ids"] = [replacement_asset.asset_id if aid == replace_asset_id else aid
                                   for aid in alias["asset_ids"]]
        expression["source_sha256"] = source_parts_sha256(expression["parts"], expression.get("implicit_references", ()))
        from ai_video.canvas_source_expression import adapted_canvas_prompt
        prompt = adapted_canvas_prompt(expression)
        row["shot"]["intent"] = prompt
        row["generation"]["generation_intent"]["subject_action"]["progression"] = prompt
    replacement = {"original_asset_id": replace_asset_id, "source_shot_id": source_shot_id,
                   "frame_index": frame_index}
    if conditioning == "source_video":
        replacement.update(conditioning="source_video", video_asset_id=accepted_video.asset_id,
                           video_asset_sha256=accepted_video.sha256)
    row.setdefault("reference_replacements", {})[asset.asset_id] = replacement
    return data
