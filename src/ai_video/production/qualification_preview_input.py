"""Immutable development capture of a paid qualification trial, never acceptance.

Reuses the existing development preview composition and activation fences.
Source lifecycle remains in its original Manifest; bootstrap owns target writes.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    AssetRecord, AssetRegistrySnapshot, AssetSourceKind, AssetType, ProductionManifest,
)
from ai_video.production.paths import _read_regular_file_nofollow, canonical_video_asset_path
from ai_video.production.repair_input_admission import (
    CapturedSourceDocument, RepairPreviewInputAdmissionReceipt, RepairPreviewUse,
    _preview_input_tool, _preview_video_metadata, _validate_preview_probe,
    repair_input_receipt_path,
)


class QualificationPreviewInputReceipt(RepairPreviewInputAdmissionReceipt):
    contract_version: Literal["development-qualification-preview/1"] = "development-qualification-preview/1"


def _source_state(manifest, attempt_id):
    attempt = next((a for a in manifest.attempts if a.attempt_id == attempt_id), None)
    state = attempt.video_generation_state if attempt else None
    if (state is None or state.phase.value != "validate"
            or attempt.status.value in {"failed", "outcome_unknown", "interrupted"}
            or state.fetch_receipt is None or state.execution_binding is None
            or state.local_fetch_receipt is not None or state.paid_submit_receipt is None
            or state.latest_observation is None or state.quality_rejection is not None
            or state.candidate_video_asset_ids or state.candidate_continuity_asset_ids):
        raise ValueError("Qualification capture needs an exact fetched paid trial before promotion")
    if any(a.status.value in {"outcome_unknown", "interrupted"} for a in manifest.attempts):
        raise ValueError("Qualification source requires explicit recovery")
    return state


def _pointers(state):
    return (state.request, state.fetch_receipt, state.execution_binding,
            state.latest_observation, state.paid_submit_receipt)


def validate_qualification_capture(receipt):
    from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
    from ai_video.production.paid_provider import PaidProviderSubmitReceipt
    from ai_video.production.video import (
        ResolvedVideoGenerationRequest, VideoFetchReceipt, VideoSubmission, VideoTaskObservation,
    )
    if receipt.content_hash != canonical_sha256(receipt.model_dump(mode="json")):
        raise ValueError("Qualification preview capture seal changed")
    if hashlib.sha256(receipt.source_manifest_json.encode()).hexdigest() != receipt.source_manifest_sha256:
        raise ValueError("Captured qualification Manifest bytes changed")
    manifest = ProductionManifest.model_validate_json(receipt.source_manifest_json)
    if receipt.target_project_id == manifest.project_id:
        raise ValueError("Qualification preview requires an independent project identity")
    state = _source_state(manifest, receipt.source_attempt_id)
    docs = {d.path: d for d in receipt.documents}
    pointers = _pointers(state)
    if len(docs) != len(receipt.documents) or set(docs) != {p.path for p in pointers}:
        raise ValueError("Qualification preview source closure is incomplete")

    def reopen(pointer, model):
        document = docs[pointer.path]
        if document.file_sha256 != pointer.file_sha256:
            raise ValueError("Qualification source pointer bytes changed")
        return model.model_validate_json(document.text)

    request = reopen(state.request, ResolvedVideoGenerationRequest)
    fetch = reopen(state.fetch_receipt, VideoFetchReceipt)
    binding = reopen(state.execution_binding, GenerationDecisionExecutionBinding)
    observation = reopen(state.latest_observation, VideoTaskObservation)
    submit = reopen(state.paid_submit_receipt, PaidProviderSubmitReceipt)
    binding.validate_request(request)
    submission = VideoSubmission.from_paid_submit_receipt(resolved=request, receipt=submit)
    if (binding.policy.execution_purpose != "qualification"
            or request.request_input_hash != state.request.request_input_hash
            or request.desired_generation_fingerprint != state.request.request_receipt_fingerprint
            or request.resolved_generation_hash != state.request.resolved_generation_hash
            or request.generation_id != state.request.generation_id
            or request.output_asset_id != state.request.output_asset_id
            or binding.binding_hash != state.execution_binding.binding_hash
            or fetch.artifact_sha256 != receipt.artifact_sha256
            or fetch.size_bytes != receipt.size_bytes or fetch.content_type != "video/mp4"
            or fetch.artifact_sha256 != state.fetch_receipt.artifact_sha256
            or fetch.size_bytes != state.fetch_receipt.artifact_size_bytes
            or fetch.fetch_fingerprint != state.fetch_receipt.fetch_fingerprint
            or fetch.observation_fingerprint != observation.observation_fingerprint
            or fetch.submission_fingerprint != submission.submission_fingerprint
            or fetch.paid_submit_receipt_fingerprint != submit.submit_receipt_fingerprint
            or submit.submit_receipt_fingerprint != state.paid_submit_receipt.submit_receipt_fingerprint
            or submit.attempt_id != receipt.source_attempt_id
            or observation.state.value != "succeeded"
            or observation.submission_fingerprint != submission.submission_fingerprint
            or observation.observation_fingerprint != state.latest_observation.observation_fingerprint
            or observation.provider_file_id != fetch.provider_file_id
            or fetch.provider_file_id != state.provider_file_id):
        raise ValueError("Qualification preview differs from its exact paid source chain")
    _validate_preview_probe(receipt.preview_probe, request=request, fetch=fetch,
        artifact_sha256=receipt.artifact_sha256, size_bytes=receipt.size_bytes)
    use = receipt.preview_use
    if (use.scope != "replacement_audio_preview"
            or use.trim_start_frame + use.trim_duration_frames > receipt.preview_probe.measured.frame_count):
        raise ValueError("Qualification preview needs a contained normal-speed replacement-audio use")


def _prepare_qualification_preview_input(*, target_root, project, registry, source_root,
        source_attempt_id, source_sha256, asset_id, usage_license, preview_use, preview_probe):
    """Read-only preparation for canonical bootstrap_initial_state; no side effects."""
    from ai_video.production.project import load_production_project
    from ai_video.production.registry import registry_semantic_sha256
    from ai_video.production.state_commit import PreparedArtifact, _canonical_json_bytes
    root = Path(source_root).resolve(strict=True)
    target = Path(target_root).resolve(strict=True)
    if root.is_relative_to(target) or target.is_relative_to(root):
        raise ValueError("Qualification source and preview roots must not overlap")
    loaded = load_production_project(root / "project.yaml")
    raw = _read_regular_file_nofollow(root / "state/manifest.json", contained_by=root / "state").data
    manifest = ProductionManifest.model_validate_json(raw)
    if manifest != loaded.manifest:
        raise ValueError("Qualification source changed during capture")
    state = _source_state(manifest, source_attempt_id)
    if state.fetch_receipt.artifact_sha256 != source_sha256:
        raise ValueError("Selected qualification source bytes differ from fetch")
    if any(a.asset_id == asset_id for a in registry.assets):
        raise ValueError("Qualification preview asset must be new and unbound")
    if any(asset_id in role.asset_ids for shot in loaded.shots for role in shot.required_asset_roles):
        raise ValueError("Qualification capture asset must not be a production role binding")
    docs = tuple(CapturedSourceDocument(path=p.path, file_sha256=p.file_sha256,
        text=_read_regular_file_nofollow(root / p.path, contained_by=root / "state").data.decode())
        for p in _pointers(state))
    media = _read_regular_file_nofollow(root / state.fetch_receipt.artifact_path,
        contained_by=root / "state").data
    if hashlib.sha256(media).hexdigest() != source_sha256 or len(media) != state.fetch_receipt.artifact_size_bytes:
        raise ValueError("Qualification media bytes changed")
    values = dict(target_project_id=project.project_id, target_project_hash=project.content_hash,
        asset_id=asset_id, artifact_sha256=source_sha256, size_bytes=len(media), usage_license=usage_license,
        source_attempt_id=source_attempt_id, source_manifest_json=raw.decode(),
        source_manifest_sha256=hashlib.sha256(raw).hexdigest(), documents=docs,
        preview_use=RepairPreviewUse.model_validate(preview_use), preview_probe=preview_probe)
    provisional = QualificationPreviewInputReceipt.model_construct(**values, content_hash="0" * 64)
    receipt = QualificationPreviewInputReceipt.model_validate({**provisional.model_dump(mode="python"),
        "content_hash": canonical_sha256(provisional.model_dump(mode="json"))})
    measured = receipt.preview_probe.measured
    asset = AssetRecord(asset_id=asset_id, asset_type=AssetType.VIDEO,
        artifact_path=canonical_video_asset_path(source_sha256), sha256=source_sha256,
        size_bytes=len(media), mime_type="video/mp4", source_kind=AssetSourceKind.IMPORTED,
        tool=_preview_input_tool(receipt), input_fingerprint=receipt.content_hash,
        creation_receipt_id=receipt.content_hash, usage_license=usage_license,
        width=measured.width, height=measured.height,
        duration_seconds=measured.duration_milliseconds / 1000, video_metadata=_preview_video_metadata(receipt))
    updated = registry.model_copy(update={"assets": (*registry.assets, asset), "schema_version": "2.2"})
    digest = registry_semantic_sha256(updated)
    updated = AssetRegistrySnapshot.model_validate({**updated.model_dump(mode="python"),
        "revision_id": digest, "content_hash": digest})
    payload = _canonical_json_bytes(receipt)
    artifacts = (PreparedArtifact(asset.artifact_path, media, source_sha256),
        PreparedArtifact(repair_input_receipt_path(receipt.content_hash), payload, hashlib.sha256(payload).hexdigest()))
    if _read_regular_file_nofollow(root / "state/manifest.json", contained_by=root / "state").data != raw:
        raise ValueError("Qualification source changed during capture")
    return updated, artifacts


def prepare_qualification_preview_input(**arguments):
    """Typed public boundary; preparation never writes or turns failure into retry."""
    from ai_video.production._state_commit_common import _state_invalid
    try:
        return _prepare_qualification_preview_input(**arguments)
    except (OSError, ValueError, StopIteration) as exc:
        raise _state_invalid("Development qualification preview admission is invalid.", str(exc)) from exc
