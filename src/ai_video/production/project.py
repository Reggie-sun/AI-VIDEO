from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
from typing import TypeVar
import wave

from pydantic import BaseModel, ValidationError

from ai_video.config import load_yaml, sha256_file
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._image_project_reader import verify_active_image_evidence
from ai_video.production._paid_provider_project_reader import (
    verify_paid_provider_evidence,
)
import ai_video.production._project_dependency_evidence as _project_evidence
from ai_video.production._video_project_reader import verify_manifest_video_evidence
from ai_video.production._voice_project_reader import verify_voice_candidate_history
from ai_video.production.audio import (
    VoiceCallAuthorization,
    VoiceCostReceipt,
    VoiceGenerationPreview,
    VoiceGenerationRequest,
    VoicePricingSnapshot,
    VoiceProvenanceReceipt,
    VoiceProviderResult,
)
from ai_video.production.captions import (
    _canonical_track_bytes,
    caption_style_fingerprint,
    validate_caption_track_timeline_binding,
)
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.dependency import (
    _asset_role,
    _fp,
    dependency_graph_semantic_sha256,
    desired_fingerprints,
    resolve_dependency_state,
    voice_semantic_projection_fingerprint,
)
from ai_video.production.models import (
    ArtifactReference,
    AssetSourceKind,
    AssetType,
    CaptionTrack,
    CaptionStyleReference,
    Character,
    DependencyGraphSnapshot,
    DependencyGraphSnapshotPointer,
    DependencyLifecycle,
    DependencyNode,
    DependencyNodeKind,
    DependencyNodeState,
    FinalAcceptanceReceipt,
    FinalAcceptanceReceiptPointer,
    LoadedProductionProject,
    ProductionBrief,
    ProductionManifest,
    ProductionProject,
    QaPolicy,
    QaPolicyPointer,
    ProjectDependencyEvidence,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    RegistryDependencyEvidence,
    RendererSourceReceipt,
    RendererAudioBinding,
    RendererCaptionBinding,
    RenderReceipt,
    RenderStateSnapshot,
    RenderStateSnapshotPointer,
    ReviewReceipt,
    ReviewReceiptPointer,
    ReviewEvidence,
    ReviewEvidencePointer,
    ReviewRequest,
    ReviewRequestPointer,
    RenderDependencyEvidence,
    ResolvedTimeline,
    Scene,
    Shot,
    SourceReference,
    Story,
    Storyboard,
    StateCommitStatus,
    VoiceRequestReceipt,
    VersionedArtifact,
)
from ai_video.production.visual_media import visual_payload_matches
from ai_video.production.video_dependency import generated_video_semantic_fingerprint
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_audio_asset_path,
    canonical_dependency_graph_snapshot_path,
    canonical_render_output_path,
    canonical_render_receipt_path,
    canonical_render_source_asset_path,
    canonical_render_source_index_path,
    canonical_render_source_root,
    canonical_render_state_path,
    canonical_render_timeline_path,
    canonical_renderer_source_receipt_path,
    canonical_voice_attempt_artifact_path,
    resolve_contained_path,
)
from ai_video.production.registry import load_asset_registry
from ai_video.production.validation import validate_project_references

ModelT = TypeVar("ModelT", bound=BaseModel)
ArtifactT = TypeVar("ArtifactT", bound=VersionedArtifact)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _resolve_input(
    root: Path,
    stored: Path,
    *,
    allowed_root: Path | None = None,
) -> Path:
    try:
        return resolve_contained_path(root, stored, allowed_root=allowed_root)
    except ValueError as exc:
        raise _invalid(
            f"Production artifact path must be clean and contained: {stored}",
            str(exc),
        ) from exc


def _load_yaml_artifact(path: Path, model_type: type[ArtifactT]) -> ArtifactT:
    try:
        model = model_type.model_validate(load_yaml(path))
    except (ValidationError, AiVideoError) as exc:
        raise _invalid(f"Could not load production artifact: {path}", str(exc)) from exc
    if not verify_artifact_hash(model):
        raise _invalid(f"Production artifact content hash mismatch: {path}")
    return model


def _load_json_model(path: Path, model_type: type[ModelT]) -> ModelT:
    try:
        return model_type.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError) as exc:
        raise _invalid(f"Could not load production state: {path}", str(exc)) from exc


def _load_content_addressed_json(
    root: Path,
    path: Path,
    *,
    file_sha256: str,
    model_type: type[ModelT],
    content_hash: str,
    label: str,
) -> ModelT:
    resolved = _resolve_input(root, path, allowed_root=root / "state")
    try:
        snapshot = _read_regular_file_nofollow(resolved, contained_by=root / "state")
        model = model_type.model_validate_json(snapshot.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid(f"Could not reopen {label}.", str(exc)) from exc
    if (
        snapshot.file_sha256 != file_sha256
        or getattr(model, "content_hash", None) != content_hash
        or not verify_artifact_hash(model)
    ):
        raise _invalid(f"{label} identity is invalid.")
    return model


def load_qa_policy(root: str | Path, pointer: QaPolicyPointer) -> QaPolicy:
    resolved_root = Path(root).resolve(strict=True)
    policy = _load_content_addressed_json(
        resolved_root,
        pointer.path,
        file_sha256=pointer.file_sha256,
        model_type=QaPolicy,
        content_hash=pointer.content_hash,
        label="QA policy",
    )
    if policy.policy_id != pointer.policy_id or policy.policy_version != pointer.policy_version:
        raise _invalid("QA policy pointer identity is invalid.")
    return policy


def load_review_receipt(
    root: str | Path, pointer: ReviewReceiptPointer
) -> ReviewReceipt:
    resolved_root = Path(root).resolve(strict=True)
    receipt = _load_content_addressed_json(
        resolved_root,
        pointer.path,
        file_sha256=pointer.file_sha256,
        model_type=ReviewReceipt,
        content_hash=pointer.content_hash,
        label="Review Receipt",
    )
    if receipt.review_id != pointer.review_id or receipt.layer != pointer.layer:
        raise _invalid("Review Receipt pointer identity is invalid.")
    for evidence_pointer in receipt.evidence:
        evidence = load_review_evidence(resolved_root, evidence_pointer)
        if (
            evidence.layer is not receipt.layer
            or evidence.evidence_id not in receipt.evidence_ids
            or evidence.render_output_sha256 != receipt.render_output_sha256
            or evidence.timeline_fingerprint != receipt.timeline_fingerprint
            or evidence.dependency_graph_revision_id
            != receipt.dependency_graph_revision_id
        ):
            raise _invalid("Review evidence does not match its Receipt.")
    return receipt


def load_review_evidence(
    root: str | Path, pointer: ReviewEvidencePointer
) -> ReviewEvidence:
    resolved_root = Path(root).resolve(strict=True)
    evidence = _load_content_addressed_json(
        resolved_root,
        pointer.path,
        file_sha256=pointer.file_sha256,
        model_type=ReviewEvidence,
        content_hash=pointer.content_hash,
        label="Review evidence",
    )
    if (
        evidence.evidence_id != pointer.evidence_id
        or evidence.layer is not pointer.layer
        or evidence.strength is not pointer.strength
    ):
        raise _invalid("Review evidence pointer identity is invalid.")
    return evidence


def load_final_acceptance_receipt(
    root: str | Path, pointer: FinalAcceptanceReceiptPointer
) -> FinalAcceptanceReceipt:
    resolved_root = Path(root).resolve(strict=True)
    receipt = _load_content_addressed_json(
        resolved_root,
        pointer.path,
        file_sha256=pointer.file_sha256,
        model_type=FinalAcceptanceReceipt,
        content_hash=pointer.content_hash,
        label="Final Acceptance Receipt",
    )
    if receipt.acceptance_id != pointer.acceptance_id:
        raise _invalid("Final Acceptance Receipt pointer identity is invalid.")
    return receipt


def load_review_request(
    root: str | Path, pointer: ReviewRequestPointer
) -> ReviewRequest:
    resolved_root = Path(root).resolve(strict=True)
    request = _load_content_addressed_json(
        resolved_root,
        pointer.path,
        file_sha256=pointer.file_sha256,
        model_type=ReviewRequest,
        content_hash=pointer.content_hash,
        label="ReviewRequest",
    )
    if request.request_id != pointer.request_id:
        raise _invalid("ReviewRequest pointer identity is invalid.")
    return request


def _load_referenced_artifact(
    root: Path,
    reference: ArtifactReference,
    model_type: type[ArtifactT],
) -> ArtifactT:
    model = _load_yaml_artifact(
        _resolve_input(root, reference.path, allowed_root=root / "creative"),
        model_type,
    )
    actual = (model.artifact_id, model.revision, model.content_hash)
    expected = (reference.artifact_id, reference.revision, reference.content_hash)
    if actual != expected:
        raise _invalid(
            f"Production artifact does not match its project reference: {reference.path}"
        )
    return model


def _resolve_candidate_project_path(root: Path, project_path: Path) -> Path:
    if project_path == Path("project.yaml"):
        return _resolve_input(root, project_path)
    if not (
        len(project_path.parts) > 2 and project_path.parts[:2] == ("state", "projects")
    ):
        raise _invalid("Candidate project snapshot path is not allowed.")
    return _resolve_input(
        root,
        project_path,
        allowed_root=root / "state/projects",
    )


def _resolve_candidate_registry_path(root: Path, registry_path: Path) -> Path:
    return _resolve_input(root, registry_path, allowed_root=root / "assets")


def _verify_snapshot_file_hash(path: Path, expected: str, label: str) -> None:
    try:
        actual = sha256_file(path)
    except OSError as exc:
        raise _invalid(
            f"Could not verify {label} snapshot file hash: {path}", str(exc)
        ) from exc
    if actual != expected:
        raise _invalid(
            f"{label.capitalize()} snapshot file hash does not match Manifest."
        )


def _verify_manifest_snapshot_identity(
    bundle: LoadedProductionProject,
    project_pointer: ProjectSnapshotPointer,
    registry_pointer: RegistrySnapshotPointer,
) -> None:
    if bundle.project.revision != project_pointer.revision:
        raise _invalid(
            "Manifest project revision does not match selected project snapshot."
        )
    if bundle.project.content_hash != project_pointer.content_hash:
        raise _invalid(
            "Manifest project content hash does not match selected project snapshot."
        )
    if bundle.registry.revision_id != registry_pointer.revision_id:
        raise _invalid(
            "Manifest registry revision does not match selected registry snapshot."
        )
    if bundle.registry.content_hash != registry_pointer.content_hash:
        raise _invalid(
            "Manifest registry content hash does not match selected registry snapshot."
        )


def _canonical_model_bytes(model: BaseModel) -> bytes:
    payload = json.dumps(
        model.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (payload + "\n").encode("utf-8")


def _read_voice_model(
    root: Path,
    attempt_id: str,
    name: str,
    model_type: type[ModelT],
) -> tuple[ModelT, bytes]:
    snapshot = _read_regular_file_nofollow(
        canonical_voice_attempt_artifact_path(root, attempt_id, name),
        contained_by=root,
    )
    model = model_type.model_validate_json(snapshot.data)
    if snapshot.data != _canonical_model_bytes(model):
        raise ValueError(f"{name} is not canonical")
    return model, snapshot.data


def _read_voice_json(
    root: Path, attempt_id: str, name: str
) -> tuple[dict[str, object], bytes]:
    snapshot = _read_regular_file_nofollow(
        canonical_voice_attempt_artifact_path(root, attempt_id, name),
        contained_by=root,
    )
    value = json.loads(snapshot.data)
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain an object")
    canonical = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    if snapshot.data != canonical:
        raise ValueError(f"{name} is not canonical")
    return value, snapshot.data


def _verify_active_voice_evidence(bundle: LoadedProductionProject) -> None:
    attempts = tuple(
        attempt
        for attempt in bundle.manifest.attempts
        if attempt.operation == "voice_generation"
        and attempt.status is StateCommitStatus.SUCCEEDED
        and attempt.voice_phase == "activate"
    )
    try:
        attempts_by_asset = verify_voice_candidate_history(
            bundle,
            attempts,
            load_dependency_graph=_load_active_dependency_graph,
        )
    except (AiVideoError, OSError, ValidationError, ValueError) as exc:
        detail = exc.technical_detail if isinstance(exc, AiVideoError) else str(exc)
        raise _invalid(
            "Active P4 voice candidate history is invalid.", detail
        ) from exc
    assets_by_id = {asset.asset_id: asset for asset in bundle.registry.assets}
    generated_voice_ids = {
        asset.asset_id
        for asset in bundle.registry.assets
        if asset.asset_type is AssetType.VOICE
        and asset.source_kind is AssetSourceKind.GENERATED
    }
    claimed_audio_ids = {
        asset_id
        for attempt in attempts
        for asset_id in attempt.candidate_audio_asset_ids
    }
    if generated_voice_ids != claimed_audio_ids:
        raise _invalid("Active generated voice assets do not match succeeded attempts.")
    for attempt in attempts:
        if len(attempt.candidate_audio_asset_ids) != 1:
            raise _invalid(
                "Each succeeded voice attempt must select exactly one audio asset."
            )
        audio_id = attempt.candidate_audio_asset_ids[0]
        asset = assets_by_id[audio_id]
        if attempts_by_asset.get(audio_id) != attempt:
            raise _invalid("Active generated voice asset claim is invalid.")
        if not asset.egress.remote:
            raise _invalid(
                "Active generated voice asset requires remote egress evidence."
            )
        try:
            request, _ = _read_voice_model(
                bundle.root, attempt.attempt_id, "request.json", VoiceGenerationRequest
            )
            preview, _ = _read_voice_model(
                bundle.root, attempt.attempt_id, "preview.json", VoiceGenerationPreview
            )
            authorization, _ = _read_voice_model(
                bundle.root,
                attempt.attempt_id,
                "authorization.json",
                VoiceCallAuthorization,
            )
            cost, cost_bytes = _read_voice_model(
                bundle.root, attempt.attempt_id, "cost.json", VoiceCostReceipt
            )
            provenance, provenance_bytes = _read_voice_model(
                bundle.root,
                attempt.attempt_id,
                "provenance.json",
                VoiceProvenanceReceipt,
            )
            intent, _ = _read_voice_json(
                bundle.root, attempt.attempt_id, "submit-intent.json"
            )
            outcome, _ = _read_voice_json(
                bundle.root, attempt.attempt_id, "outcome.json"
            )
            alignment = _read_regular_file_nofollow(
                canonical_voice_attempt_artifact_path(
                    bundle.root, attempt.attempt_id, "alignment.json"
                ),
                contained_by=bundle.root,
            )
            pricing = VoicePricingSnapshot(
                snapshot_id=preview.pricing_snapshot_id,
                effective_date=preview.pricing_effective_date,
                currency=preview.currency,
                pricing_unit=preview.pricing_unit,
                unit_price_microunits=preview.unit_price_microunits,
                minimum_billable_units=preview.minimum_billable_units,
            )
            audio_snapshot = _read_regular_file_nofollow(
                bundle.root / asset.artifact_path, contained_by=bundle.root
            )
            if (
                audio_snapshot.file_sha256 != asset.sha256
                or audio_snapshot.size_bytes != asset.size_bytes
            ):
                raise ValueError(
                    "voice audio identity changed after registry verification"
                )
            result = VoiceProviderResult(
                request_id=request.request_id,
                request_fingerprint=request.voice_request_fingerprint,
                audio_bytes=audio_snapshot.data,
                audio_sha256=asset.sha256,
                content_type=asset.mime_type,
                provider_request_id=outcome.get("provider_request_id"),
                provider_trace_id=outcome.get("provider_trace_id"),
                alignment_receipt_bytes=alignment.data,
                alignment_receipt_sha256=alignment.file_sha256,
                cost_receipt=cost,
                provenance_receipt=provenance,
                terminal_status=outcome.get("terminal_status"),
                preview_fingerprint=preview.preview_fingerprint,
                authorization_fingerprint=authorization.authorization_fingerprint,
                result_fingerprint=outcome.get("result_fingerprint"),
            )
            expected_result = VoiceProviderResult.create(
                request=request,
                preview=preview,
                authorization=authorization,
                pricing=pricing,
                audio_bytes=audio_snapshot.data,
                content_type=result.content_type,
                provider_request_id=result.provider_request_id,
                provider_trace_id=result.provider_trace_id,
                alignment_receipt_bytes=alignment.data,
                cost_receipt=cost,
                provenance_receipt=provenance,
                terminal_status=result.terminal_status,
            )
            if result != expected_result:
                raise ValueError(
                    "durable voice result is not the canonical expected result"
                )
            metadata = asset.audio_metadata
            if metadata is None or attempt.voice_request is None:
                raise ValueError("voice metadata is missing")
            expected_request_receipt = VoiceRequestReceipt(
                request_id=request.request_id,
                attempt_id=request.attempt_id,
                request_fingerprint=request.voice_request_fingerprint,
                script_hash=request.script_hash,
                provider_kind=request.provider_kind,
                model_id=request.model_id,
                voice_id=request.voice_id,
                language=request.language,
                pricing_snapshot_id=request.pricing_snapshot_id,
                budget_reservation_receipt_id=request.budget_reservation_receipt_id,
                egress_authorization_receipt_id=request.egress_authorization_receipt_id,
                destination=authorization.destination,
            )
            expected_intent = {
                "attempt_id": request.attempt_id,
                "request_fingerprint": request.voice_request_fingerprint,
                "authorization_fingerprint": authorization.authorization_fingerprint,
                "destination": authorization.destination,
                "budget_reservation_receipt_id": authorization.budget_reservation_receipt_id,
                "egress_authorization_receipt_id": authorization.egress_authorization_receipt_id,
            }
            expected_outcome = {
                "request_id": result.request_id,
                "request_fingerprint": result.request_fingerprint,
                "preview_fingerprint": result.preview_fingerprint,
                "authorization_fingerprint": result.authorization_fingerprint,
                "result_fingerprint": result.result_fingerprint,
                "provider_request_id": result.provider_request_id,
                "provider_trace_id": result.provider_trace_id,
                "audio_sha256": result.audio_sha256,
                "alignment_receipt_sha256": result.alignment_receipt_sha256,
                "content_type": result.content_type,
                "policy_receipt_id": provenance.policy_receipt_id,
                "retention_mode": provenance.retention_mode,
                "terminal_status": result.terminal_status,
            }
            caption_assets = tuple(
                assets_by_id[item]
                for item in attempt.candidate_caption_asset_ids
                if item in assets_by_id
            )
            caption_tracks: dict[str, CaptionTrack] = {}
            for caption in caption_assets:
                caption_snapshot = _read_regular_file_nofollow(
                    bundle.root / caption.artifact_path, contained_by=bundle.root
                )
                caption_tracks[caption.asset_id] = CaptionTrack.model_validate_json(
                    caption_snapshot.data
                )
            if (
                request.attempt_id != attempt.attempt_id
                or request.base_project != attempt.base_project
                or request.base_registry != attempt.base_registry
                or attempt.voice_request != expected_request_receipt
                or intent != expected_intent
                or outcome != expected_outcome
                or asset.asset_id not in attempt.candidate_audio_asset_ids
                or asset.artifact_path != canonical_audio_asset_path(asset.sha256)
                or asset.creation_receipt_id
                != f"voice-result-{result.result_fingerprint}"
                or asset.source_kind is not AssetSourceKind.GENERATED
                or asset.tool != provenance.adapter
                or asset.usage_license != provenance.license_policy_decision
                or asset.input_artifact_ids != request.input_artifact_ids
                or asset.input_fingerprint != request.input_fingerprint
                or asset.cost_receipt_id
                != f"cost-{hashlib.sha256(cost_bytes).hexdigest()}"
                or metadata.provenance_receipt_id
                != f"provenance-{hashlib.sha256(provenance_bytes).hexdigest()}"
                or metadata.alignment_receipt_id != f"alignment-{alignment.file_sha256}"
                or metadata.audio_kind != request.audio_kind
                or metadata.speaker_id != request.speaker_id
                or metadata.voice_id != request.voice_id
                or metadata.language != request.language
                or metadata.script_hash != request.script_hash
                or metadata.sample_rate_hz != request.output_sample_rate_hz
                or metadata.channels != request.output_channels
                or metadata.source.kind is not AssetSourceKind.GENERATED
                or metadata.source.provider_or_tool != asset.tool
                or metadata.source.provider_or_tool != provenance.adapter
                or metadata.source.input_artifact_ids != request.input_artifact_ids
                or metadata.source.input_fingerprint != request.input_fingerprint
                or asset.egress.destination != authorization.destination
                or asset.egress.authorization_receipt_id
                != request.egress_authorization_receipt_id
                or asset.egress.request_fingerprint != request.voice_request_fingerprint
                or asset.egress.payload_fingerprint != request.script_hash
                or asset.egress.retention_mode != provenance.retention_mode
                or asset.egress.provider_policy_snapshot_id
                != provenance.policy_receipt_id
                or len(caption_assets) != len(attempt.candidate_caption_asset_ids)
                or any(
                    caption.caption_metadata is None
                    or caption.source_kind is not AssetSourceKind.DERIVED
                    or caption.tool != provenance.adapter
                    or caption.usage_license != provenance.license_policy_decision
                    or caption.creation_receipt_id
                    != f"caption-result-{result.result_fingerprint}"
                    or caption.input_artifact_ids != (asset.asset_id,)
                    or caption.input_fingerprint != asset.sha256
                    or caption.caption_metadata.source_audio_asset_id != asset.asset_id
                    or caption.caption_metadata.source_audio_sha256 != asset.sha256
                    or caption.artifact_path
                    != Path(f"assets/captions/{caption.sha256}.json")
                    or caption.caption_metadata.script_hash != request.script_hash
                    or caption.caption_metadata.transcript_hash != request.script_hash
                    or caption.caption_metadata.alignment_receipt_id
                    != metadata.alignment_receipt_id
                    or caption_tracks[caption.asset_id].script_hash
                    != request.script_hash
                    or caption_tracks[caption.asset_id].creation_receipt_id
                    != caption.creation_receipt_id
                    or caption_tracks[caption.asset_id].source_provenance
                    != (
                        SourceReference(
                            kind="derived",
                            reference=(f"alignment-{result.alignment_receipt_sha256}"),
                        ),
                    )
                    or caption_tracks[caption.asset_id].transcript_hash
                    != request.script_hash
                    or caption_tracks[caption.asset_id].source_audio_asset_id
                    != asset.asset_id
                    or caption_tracks[caption.asset_id].source_audio_sha256
                    != asset.sha256
                    or caption_tracks[caption.asset_id].source_sample_rate_hz
                    != metadata.sample_rate_hz
                    or caption_tracks[caption.asset_id].alignment_provider
                    != request.provider_kind
                    or caption_tracks[caption.asset_id].alignment_model
                    != request.model_id
                    or caption_tracks[caption.asset_id].alignment_receipt_id
                    != metadata.alignment_receipt_id
                    for caption in caption_assets
                )
            ):
                raise ValueError("voice evidence identity mismatch")
        except (
            AiVideoError,
            OSError,
            ValidationError,
            ValueError,
            KeyError,
            TypeError,
        ) as exc:
            detail = exc.technical_detail if isinstance(exc, AiVideoError) else str(exc)
            raise _invalid(
                "Active P4 voice evidence graph is invalid.", detail
            ) from exc


def _bundle_hash(state: RenderStateSnapshot) -> str:
    bundle = state.source_bundle
    entries = [
        (
            bundle.index.path.relative_to(bundle.root_path).as_posix(),
            bundle.index.file_sha256,
        ),
        *(
            (item.path.relative_to(bundle.root_path).as_posix(), item.file_sha256)
            for item in bundle.assets
        ),
    ]
    payload = json.dumps(
        sorted(entries), ensure_ascii=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _render_source_binding_map(
    source: RendererSourceReceipt,
) -> dict[Path, tuple[str, str, object]]:
    """Map every declared source exactly once to its role and expected digest."""

    bindings: dict[Path, tuple[str, str, object]] = {}

    def add(path: Path, role: str, digest: str, binding: object) -> None:
        previous = bindings.get(path)
        if previous is not None:
            if (
                role == "caption_style"
                and previous[0] == role
                and previous[1] == digest
            ):
                return
            raise ValueError("render source bindings contain a duplicate path")
        bindings[path] = (role, digest, binding)

    for binding in source.asset_bindings:
        add(binding.materialized_path, "visual", binding.asset_sha256, binding)
    for binding in source.audio_bindings:
        add(binding.materialized_path, "audio", binding.asset_sha256, binding)
    for binding in source.caption_bindings:
        add(
            binding.materialized_path,
            "caption",
            binding.caption_asset_sha256,
            binding,
        )
        if binding.style_materialized_path is not None:
            assert binding.style_content_hash is not None
            add(
                binding.style_materialized_path,
                "caption_style",
                binding.style_content_hash,
                binding,
            )
    return bindings


def _validate_source_timeline_bindings(
    source: RendererSourceReceipt, timeline: ResolvedTimeline
) -> None:
    expected_track_ids = tuple(item.track_id for item in timeline.audio_spans)
    if expected_track_ids:
        if len(source.audio_bindings) != 1:
            raise ValueError(
                "P4 render source requires exactly one mixed audio binding"
            )
        audio = source.audio_bindings[0]
        if (
            audio.asset_mime_type != "audio/wav"
            or audio.sample_rate_hz != timeline.sample_rate
            or audio.channels != 2
            or audio.duration_samples != timeline.total_samples
            or audio.resolved_track_ids != expected_track_ids
        ):
            raise ValueError(
                "P4 mixed audio binding does not match the resolved timeline"
            )
    elif source.audio_bindings:
        raise ValueError("silent timeline cannot declare a renderer audio binding")

    expected_caption_tracks = {item.caption_track_id for item in timeline.caption_cues}
    actual_caption_tracks = tuple(
        item.caption_track_id for item in source.caption_bindings
    )
    if len(actual_caption_tracks) != len(set(actual_caption_tracks)):
        raise ValueError("renderer caption track bindings must be unique")
    if set(actual_caption_tracks) != expected_caption_tracks:
        raise ValueError("renderer caption bindings do not match the resolved timeline")
    for binding in source.caption_bindings:
        cues = tuple(
            item
            for item in timeline.caption_cues
            if item.caption_track_id == binding.caption_track_id
        )
        style_identities = {
            (item.style_reference_id, item.style_content_hash) for item in cues
        }
        if (
            not cues
            or {item.caption_asset_sha256 for item in cues}
            != {binding.caption_asset_sha256}
            or binding.resolved_cue_ids != tuple(item.segment_id for item in cues)
            or style_identities
            != {(binding.style_reference_id, binding.style_content_hash)}
        ):
            raise ValueError("renderer caption binding does not match resolved cues")
    if (
        timeline.audio_spans or timeline.caption_cues
    ) and source.schema_version != "2.1":
        raise ValueError("P4 timeline requires RendererSourceReceipt 2.1")


def _render_source_payload_matches(
    payload: bytes,
    *,
    suffix: str,
    role: str,
    binding: object,
    timeline: ResolvedTimeline,
) -> bool:
    if role == "visual":
        mime_type = getattr(binding, "asset_mime_type", "")
        return visual_payload_matches(
            payload, suffix=suffix, mime_type=mime_type
        )
    if role == "audio":
        if not isinstance(binding, RendererAudioBinding):
            return False
        if suffix != ".wav" or binding.asset_mime_type != "audio/wav":
            return False
        try:
            with wave.open(BytesIO(payload), "rb") as source:
                return (
                    source.getsampwidth() == 2
                    and source.getcomptype() == "NONE"
                    and source.getframerate() == binding.sample_rate_hz
                    and source.getnchannels() == binding.channels
                    and source.getnframes() == binding.duration_samples
                )
        except (EOFError, wave.Error):
            return False
    if role == "caption":
        if not isinstance(binding, RendererCaptionBinding) or suffix != ".json":
            return False
        try:
            track = CaptionTrack.model_validate_json(payload)
        except (ValidationError, ValueError):
            return False
        if payload != _canonical_track_bytes(track):
            return False
        cues = tuple(
            cue
            for cue in timeline.caption_cues
            if cue.caption_track_id == binding.caption_track_id
        )
        try:
            validate_caption_track_timeline_binding(
                track,
                caption_asset_sha256=binding.caption_asset_sha256,
                cues=cues,
                audio_spans=timeline.audio_spans,
                sample_rate_hz=timeline.sample_rate,
                fps=timeline.delivery_profile.fps,
                style_reference_id=binding.style_reference_id,
                style_content_hash=binding.style_content_hash,
            )
        except ValueError:
            return False
        return binding.resolved_cue_ids == tuple(cue.segment_id for cue in cues)
    if role == "caption_style":
        if not isinstance(binding, RendererCaptionBinding) or suffix != ".json":
            return False
        try:
            value = json.loads(payload)
        except (UnicodeError, json.JSONDecodeError):
            return False
        return isinstance(value, dict)
    return False


def _read_render_model(
    root: Path,
    relative: Path,
    model_type: type[ModelT],
    *,
    expected_file_hash: str,
    label: str,
) -> tuple[ModelT, bytes]:
    try:
        snapshot = _read_regular_file_nofollow(root / relative, contained_by=root)
        if snapshot.file_sha256 != expected_file_hash:
            raise ValueError("file hash mismatch")
        model = model_type.model_validate_json(snapshot.data)
    except (OSError, ValidationError, ValueError) as exc:
        raise _invalid(
            f"Could not verify active {label}: {relative}", str(exc)
        ) from exc
    return model, snapshot.data


def load_verified_render_state(
    root: Path,
    pointer: RenderStateSnapshotPointer,
    *,
    project: ProjectSnapshotPointer,
    registry: RegistrySnapshotPointer,
) -> RenderStateSnapshot:
    """Read one Manifest-selected render graph without following links or scanning."""
    if pointer.path != canonical_render_state_path(pointer.content_hash):
        raise _invalid("Active render state path is noncanonical.")
    state, _ = _read_render_model(
        root,
        pointer.path,
        RenderStateSnapshot,
        expected_file_hash=pointer.file_sha256,
        label="render state",
    )
    if (
        not verify_artifact_hash(state)
        or state.revision != pointer.revision
        or state.content_hash != pointer.content_hash
        or state.project != project
        or state.registry != registry
    ):
        raise _invalid("Active render state identity does not match Manifest.")
    timeline, _ = _read_render_model(
        root,
        state.timeline.path,
        ResolvedTimeline,
        expected_file_hash=state.timeline.file_sha256,
        label="render timeline",
    )
    source, _ = _read_render_model(
        root,
        state.source_receipt.path,
        RendererSourceReceipt,
        expected_file_hash=state.source_receipt.file_sha256,
        label="renderer source receipt",
    )
    render, _ = _read_render_model(
        root,
        state.render_receipt.path,
        RenderReceipt,
        expected_file_hash=state.render_receipt.file_sha256,
        label="render receipt",
    )
    if not all(verify_artifact_hash(item) for item in (timeline, source, render)):
        raise _invalid("Active render artifact semantic hash is invalid.")
    if (
        state.timeline.path != canonical_render_timeline_path(timeline.content_hash)
        or (timeline.revision, timeline.content_hash)
        != (state.timeline.revision, state.timeline.content_hash)
        or state.source_receipt.path
        != canonical_renderer_source_receipt_path(source.content_hash)
        or (source.revision, source.content_hash)
        != (state.source_receipt.revision, state.source_receipt.content_hash)
        or state.render_receipt.path
        != canonical_render_receipt_path(render.content_hash)
        or (render.revision, render.content_hash)
        != (state.render_receipt.revision, state.render_receipt.content_hash)
    ):
        raise _invalid("Active render artifact pointer identity is invalid.")
    bundle = state.source_bundle
    if (
        bundle.root_path != canonical_render_source_root(bundle.bundle_sha256)
        or bundle.index.path != canonical_render_source_index_path(bundle.bundle_sha256)
        or source.source_bundle != bundle
        or _bundle_hash(state) != bundle.bundle_sha256
    ):
        raise _invalid("Active render source bundle identity is invalid.")
    try:
        index_snapshot = _read_regular_file_nofollow(
            root / bundle.index.path, contained_by=root
        )
    except (OSError, ValueError) as exc:
        raise _invalid(
            "Could not verify active render source index.", str(exc)
        ) from exc
    if (
        index_snapshot.file_sha256 != bundle.index.file_sha256
        or index_snapshot.size_bytes != bundle.index.size_bytes
    ):
        raise _invalid("Active render source index identity is invalid.")
    try:
        binding_map = _render_source_binding_map(source)
        _validate_source_timeline_bindings(source, timeline)
    except ValueError as exc:
        raise _invalid("Active render source bindings are invalid.", str(exc)) from exc
    pointer_by_path = {item.path: item for item in bundle.assets}
    if len(pointer_by_path) != len(bundle.assets):
        raise _invalid("Active render source bundle contains duplicate assets.")
    for path, (_, digest, _) in binding_map.items():
        pointer = pointer_by_path.get(path)
        if pointer is None or digest != pointer.file_sha256:
            raise _invalid(
                "Active render source binding hash does not match its bundle pointer."
            )
    asset_paths = tuple(item.path for item in bundle.assets)
    if len(asset_paths) != len(set(asset_paths)):
        raise _invalid("Active render source bundle contains duplicate assets.")
    if set(binding_map) != set(asset_paths):
        raise _invalid("Active render source bindings are incomplete.")
    for asset in bundle.assets:
        try:
            if asset.path != canonical_render_source_asset_path(
                bundle.bundle_sha256, asset.file_sha256, asset.path.suffix
            ):
                raise ValueError("noncanonical asset path")
            snapshot = _read_regular_file_nofollow(root / asset.path, contained_by=root)
        except (OSError, ValueError) as exc:
            raise _invalid(
                "Could not verify active render source asset.", str(exc)
            ) from exc
        if (
            snapshot.file_sha256 != asset.file_sha256
            or snapshot.size_bytes != asset.size_bytes
            or not _render_source_payload_matches(
                snapshot.data,
                suffix=asset.path.suffix,
                role=binding_map[asset.path][0],
                binding=binding_map[asset.path][2],
                timeline=timeline,
            )
        ):
            raise _invalid("Active render source asset identity is invalid.")
    try:
        from ai_video.production.hyperframes import audit_hyperframes_source

        relative_bindings = tuple(
            item.model_copy(
                update={
                    "materialized_path": item.materialized_path.relative_to(
                        bundle.root_path
                    )
                }
            )
            for item in source.asset_bindings
        )
        relative_audio_bindings = tuple(
            item.model_copy(
                update={
                    "materialized_path": item.materialized_path.relative_to(
                        bundle.root_path
                    )
                }
            )
            for item in source.audio_bindings
        )
        relative_caption_bindings = tuple(
            item.model_copy(
                update={
                    "materialized_path": item.materialized_path.relative_to(
                        bundle.root_path
                    ),
                    "style_materialized_path": (
                        item.style_materialized_path.relative_to(bundle.root_path)
                        if item.style_materialized_path is not None
                        else None
                    ),
                }
            )
            for item in source.caption_bindings
        )
        audit_hyperframes_source(
            root / bundle.index.path,
            expected_assets=relative_bindings,
            expected_timeline=timeline,
            expected_audio=relative_audio_bindings,
            expected_captions=relative_caption_bindings,
        )
    except (AiVideoError, OSError, ValueError) as exc:
        detail = exc.technical_detail if isinstance(exc, AiVideoError) else str(exc)
        raise _invalid("Active render source audit failed.", detail) from exc
    try:
        output = _read_regular_file_nofollow(
            root / state.output.path, contained_by=root
        )
    except (OSError, ValueError) as exc:
        raise _invalid("Could not verify active render output.", str(exc)) from exc
    if (
        state.output.path != canonical_render_output_path(state.output.file_sha256)
        or output.file_sha256 != state.output.file_sha256
        or output.size_bytes != state.output.size_bytes
        or render.output_path != state.output.path
        or render.output_sha256 != state.output.file_sha256
        or render.output_size_bytes != state.output.size_bytes
        or (render.measured.width, render.measured.height)
        != (timeline.delivery_profile.width, timeline.delivery_profile.height)
        or render.measured.fps_num
        != timeline.delivery_profile.fps * render.measured.fps_den
        or render.measured.duration_frames != timeline.total_frames
    ):
        raise _invalid("Active render output identity is invalid.")
    if (
        timeline.composition_fingerprint != state.timeline_fingerprint
        or timeline.renderer != state.renderer
        or source.attempt_id != state.attempt_id
        or render.attempt_id != state.attempt_id
        or source.renderer != state.renderer
        or render.renderer != state.renderer
        or source.timeline_fingerprint != state.timeline_fingerprint
        or render.timeline_fingerprint != state.timeline_fingerprint
        or source.source_sha256 != state.source_sha256
        or render.source_sha256 != state.source_sha256
        or source.source_bundle.bundle_sha256 != state.source_bundle_sha256
        or render.source_bundle_sha256 != state.source_bundle_sha256
        or render.asset_hashes != state.asset_hashes
    ):
        raise _invalid("Active render graph contains mixed provenance.")
    return state


def _validate_canonical_entrypoint(root: Path, supplied_path: Path) -> None:
    if supplied_path.is_symlink():
        raise _invalid("Production project entry point must not be a symlink.")
    if not supplied_path.exists():
        raise _invalid("Production project entry point must exist.")
    if not supplied_path.is_file():
        raise _invalid("Production project entry point must be a regular file.")
    try:
        resolved_entrypoint = supplied_path.resolve(strict=True)
        resolved_entrypoint.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise _invalid(
            "Production project entry point must be contained by its root.", str(exc)
        ) from exc
    if resolved_entrypoint != root / "project.yaml":
        raise _invalid(
            "Production project entry point must resolve to root project.yaml."
        )


def _build_loaded_project(
    root: Path,
    manifest: ProductionManifest,
    project: ProductionProject,
    registry_path: Path,
) -> LoadedProductionProject:
    asset_root = _resolve_input(root, project.asset_root, allowed_root=root / "assets")
    registry, asset_paths = load_asset_registry(registry_path, root, asset_root)
    refs = project.artifacts
    bundle = LoadedProductionProject(
        root=root,
        project=project,
        manifest=manifest,
        brief=_load_referenced_artifact(root, refs.brief, ProductionBrief),
        story=_load_referenced_artifact(root, refs.story, Story),
        characters=tuple(
            _load_referenced_artifact(root, item, Character) for item in refs.characters
        ),
        scenes=tuple(
            _load_referenced_artifact(root, item, Scene) for item in refs.scenes
        ),
        storyboard=_load_referenced_artifact(root, refs.storyboard, Storyboard),
        shots=tuple(_load_referenced_artifact(root, item, Shot) for item in refs.shots),
        registry=registry,
        asset_paths=asset_paths,
    )
    validate_project_references(bundle)
    return bundle


def _load_active_dependency_graph(
    root: Path,
    pointer: DependencyGraphSnapshotPointer,
) -> DependencyGraphSnapshot:
    if pointer.path != canonical_dependency_graph_snapshot_path(pointer.revision_id):
        raise _invalid("Active dependency graph path is noncanonical.")
    try:
        snapshot = _read_regular_file_nofollow(
            root / pointer.path,
            contained_by=root / "state",
        )
        if snapshot.file_sha256 != pointer.file_sha256:
            raise ValueError("file hash mismatch")
        graph = DependencyGraphSnapshot.model_validate_json(snapshot.data)
        if (
            graph.revision_id != pointer.revision_id
            or graph.content_hash != pointer.content_hash
            or dependency_graph_semantic_sha256(graph) != pointer.content_hash
        ):
            raise ValueError("semantic identity mismatch")
    except (AiVideoError, OSError, ValidationError, ValueError) as exc:
        detail = exc.technical_detail if isinstance(exc, AiVideoError) else str(exc)
        raise _invalid("Could not verify active dependency graph.", detail) from exc
    return graph


def _verify_dependency_project_evidence(
    bundle: LoadedProductionProject,
    evidence: ProjectDependencyEvidence,
    node: DependencyNode | None = None,
    context: tuple[DependencyGraphSnapshot, DependencyNodeState] | None = None,
) -> None:
    root = bundle.root
    path = _resolve_candidate_project_path(root, evidence.pointer.path)
    _verify_snapshot_file_hash(path, evidence.pointer.file_sha256, "project evidence")
    project = _load_yaml_artifact(path, ProductionProject)
    if (
        project.project_id != bundle.manifest.project_id
        or project.revision != evidence.pointer.revision
        or project.content_hash != evidence.pointer.content_hash
    ):
        raise _invalid("Project dependency evidence identity is invalid.")
    refs = project.artifacts
    artifacts = (
        _load_referenced_artifact(root, refs.brief, ProductionBrief),
        _load_referenced_artifact(root, refs.story, Story),
        *(
            _load_referenced_artifact(root, item, Character)
            for item in refs.characters
        ),
        *(_load_referenced_artifact(root, item, Scene) for item in refs.scenes),
        _load_referenced_artifact(root, refs.storyboard, Storyboard),
        *(_load_referenced_artifact(root, item, Shot) for item in refs.shots),
    )
    matches = _project_evidence.matching_evidence_artifacts(
        artifacts, evidence.artifact_id
    )
    if len(matches) != 1:
        raise _invalid("Project dependency evidence artifact is not in its snapshot.")
    if node is None:
        return
    artifact = matches[0]
    contributions = {item.key: item.fingerprint for item in node.contributions}
    if isinstance(artifact, Shot):
        graph, state = context or (None, None)
        origin_graph = graph
        origin_pointer = _project_evidence.historical_origin_graph_pointer(
            bundle, evidence
        )
        if origin_pointer is not None:
            origin_graph = _load_active_dependency_graph(root, origin_pointer)
        _project_evidence.verify_active_shot_projection_evidence(
            bundle, evidence, node, graph, state, artifact, origin_graph
        )
        return
    elif isinstance(artifact, (Character, Scene)):
        graph, state = context or (None, None)
        origin_graph = graph
        origin_pointer = _project_evidence.historical_origin_graph_pointer(
            bundle, evidence
        )
        if origin_pointer is not None:
            origin_graph = _load_active_dependency_graph(root, origin_pointer)
        current_matches = tuple(
            item
            for item in (*bundle.characters, *bundle.scenes)
            if item.artifact_id == evidence.artifact_id
        )
        if len(current_matches) != 1:
            raise _invalid("Current project dependency artifact is ambiguous.")
        _project_evidence.verify_active_versioned_artifact_evidence(
            bundle,
            evidence,
            node,
            graph,
            state,
            artifact,
            current_matches[0],
            origin_graph,
        )
    else:
        if node.artifact_revision != artifact.revision:
            raise _invalid("Project dependency evidence revision is invalid.")
        kind = node.node_id.split(":", 2)[1] if ":" in node.node_id else ""
        expected = {f"{kind}.semantic": artifact.content_hash}
        if contributions != expected:
            raise _invalid("Project dependency evidence projection is invalid.")


def _verify_dependency_registry_evidence(
    bundle: LoadedProductionProject,
    evidence: RegistryDependencyEvidence,
    node: DependencyNode | None = None,
) -> None:
    root = bundle.root
    path = _resolve_candidate_registry_path(root, evidence.pointer.path)
    _verify_snapshot_file_hash(path, evidence.pointer.file_sha256, "registry evidence")
    registry, _ = load_asset_registry(
        evidence.pointer.path,
        root,
        _resolve_input(root, bundle.project.asset_root, allowed_root=root / "assets"),
    )
    assets = tuple(
        item for item in registry.assets if item.asset_id == evidence.artifact_id
    )
    if (
        registry.revision_id != evidence.pointer.revision_id
        or registry.content_hash != evidence.pointer.content_hash
        or len(assets) != 1
    ):
        raise _invalid("Registry dependency evidence identity is invalid.")
    if node is None:
        return
    asset = assets[0]
    if node.artifact_revision is not None or node.semantic_role is not _asset_role(asset):
        raise _invalid("Registry dependency evidence node identity is invalid.")
    contributions = {item.key: item.fingerprint for item in node.contributions}
    voice_attempts = tuple(
        attempt
        for attempt in bundle.manifest.attempts
        if attempt.operation == "voice_generation"
        and attempt.status is StateCommitStatus.SUCCEEDED
        and asset.asset_id in attempt.candidate_audio_asset_ids
        and attempt.candidate_registry == evidence.pointer
    )
    if len(voice_attempts) > 1:
        raise _invalid("Registry dependency voice evidence is ambiguous.")
    request = None
    if voice_attempts:
        try:
            request, _ = _read_voice_model(
                root,
                voice_attempts[0].attempt_id,
                "request.json",
                VoiceGenerationRequest,
            )
        except (AiVideoError, OSError, ValidationError, ValueError) as exc:
            detail = exc.technical_detail if isinstance(exc, AiVideoError) else str(exc)
            raise _invalid("Registry dependency voice evidence is invalid.", detail) from exc
    input_artifact_ids = (
        request.input_artifact_ids if request is not None else asset.input_artifact_ids
    )
    input_fingerprint = request.input_fingerprint if request else asset.input_fingerprint
    expected = {
        "asset.inputs": _fp(
            "ai-video-asset-inputs/1",
            {
                "input_artifact_ids": input_artifact_ids,
                "input_fingerprint": input_fingerprint,
            },
        )
    }
    if request is not None:
        expected["voice.semantic"] = voice_semantic_projection_fingerprint(request)
    elif (video_fingerprint := generated_video_semantic_fingerprint(asset)) is not None:
        expected["video.generation"] = video_fingerprint
    elif (metadata := asset.caption_metadata) is not None:
        expected["caption.timing"] = metadata.timing_fingerprint
        if metadata.style_reference_id is None:
            expected["caption.style"] = _fp("ai-video-caption-style-none/1", None)
        else:
            if (
                metadata.style_reference_revision is None
                or metadata.style_content_hash is None
            ):
                raise _invalid("Caption dependency style revision is missing.")
            style_path = root / "assets/styles" / f"{metadata.style_content_hash}.json"
            try:
                style = _read_regular_file_nofollow(style_path, contained_by=root / "assets")
            except (OSError, ValueError) as exc:
                raise _invalid("Caption dependency style evidence is invalid.", str(exc)) from exc
            if style.file_sha256 != metadata.style_content_hash:
                raise _invalid("Caption dependency style bytes are invalid.")
            style_reference = CaptionStyleReference(
                artifact_id=metadata.style_reference_id,
                revision=metadata.style_reference_revision,
                content_hash=metadata.style_content_hash,
                path=style_path.relative_to(root),
            )
            expected["caption.style"] = caption_style_fingerprint(
                style_reference, style.data
            )
    else:
        expected["asset.bytes"] = asset.sha256
    audio = asset.audio_metadata
    if audio is not None:
        contract = (
            {
                "audio_kind": request.audio_kind.value,
                "script_hash": request.script_hash,
                "voice_id": request.voice_id,
                "language": request.language,
                "sample_rate_hz": request.output_sample_rate_hz,
                "channels": request.output_channels,
                "input_artifact_ids": request.input_artifact_ids,
                "input_fingerprint": request.input_fingerprint,
            }
            if request is not None
            else {
                "audio_kind": audio.audio_kind.value,
                "script_hash": audio.script_hash,
                "voice_id": audio.voice_id,
                "language": audio.language,
                "duration_samples": audio.duration_samples,
                "sample_rate_hz": audio.sample_rate_hz,
                "channels": audio.channels,
                "input_artifact_ids": audio.source.input_artifact_ids,
                "input_fingerprint": audio.source.input_fingerprint,
            }
        )
        expected["audio.contract"] = _fp("ai-video-audio-contract/1", contract)
    if contributions != expected:
        raise _invalid("Registry dependency evidence projection is invalid.")


def _load_exact_render_state(
    bundle: LoadedProductionProject,
    pointer: RenderStateSnapshotPointer,
) -> RenderStateSnapshot:
    root = bundle.root
    state, _ = _read_render_model(
        root,
        pointer.path,
        RenderStateSnapshot,
        expected_file_hash=pointer.file_sha256,
        label="dependency render state",
    )
    if (
        not verify_artifact_hash(state)
        or state.revision != pointer.revision
        or state.content_hash != pointer.content_hash
    ):
        raise _invalid("Render dependency evidence identity is invalid.")
    project_path = _resolve_candidate_project_path(root, state.project.path)
    registry_path = _resolve_candidate_registry_path(root, state.registry.path)
    _verify_snapshot_file_hash(
        project_path, state.project.file_sha256, "render evidence project"
    )
    _verify_snapshot_file_hash(
        registry_path, state.registry.file_sha256, "render evidence registry"
    )
    historical = load_production_project_candidate(
        root,
        bundle.manifest,
        state.project.path,
        state.registry.path,
    )
    _verify_manifest_snapshot_identity(historical, state.project, state.registry)
    return load_verified_render_state(
        root,
        pointer,
        project=state.project,
        registry=state.registry,
    )


def _verify_dependency_render_evidence(
    bundle: LoadedProductionProject,
    evidence: RenderDependencyEvidence,
    *,
    node: DependencyNode | None = None,
    graph: DependencyGraphSnapshot | None = None,
    require_current: bool = False,
) -> None:
    state = _load_exact_render_state(bundle, evidence.pointer)
    if not require_current:
        return
    if node is None or graph is None:
        raise _invalid("Current render dependency evidence requires its graph node.")
    if (
        state.project != bundle.manifest.active_project
        or state.registry != bundle.manifest.active_registry
    ):
        raise _invalid("Fresh render evidence must use the active project/registry pair.")

    render_domain = {
        kind: tuple(item for item in graph.nodes if item.kind is kind)
        for kind in (
            DependencyNodeKind.COMPOSITION_SPEC,
            DependencyNodeKind.RESOLVED_TIMELINE,
            DependencyNodeKind.RENDERER_SOURCE,
            DependencyNodeKind.RENDER,
        )
    }
    if any(len(items) != 1 for items in render_domain.values()):
        raise _invalid("Fresh render evidence requires one complete render-domain unit.")
    unit = {items[0].node_id for items in render_domain.values()}
    if node.node_id not in unit:
        raise _invalid("Render evidence node is outside the active render-domain unit.")
    composition = render_domain[DependencyNodeKind.COMPOSITION_SPEC][0]
    timeline_node = render_domain[DependencyNodeKind.RESOLVED_TIMELINE][0]
    source_node = render_domain[DependencyNodeKind.RENDERER_SOURCE][0]
    render_node = render_domain[DependencyNodeKind.RENDER][0]
    edge_pairs = {(edge.source_node_id, edge.target_node_id) for edge in graph.edges}
    if not {
        (composition.node_id, timeline_node.node_id),
        (timeline_node.node_id, source_node.node_id),
        (timeline_node.node_id, render_node.node_id),
        (source_node.node_id, render_node.node_id),
    }.issubset(edge_pairs):
        raise _invalid("Fresh render evidence unit has an invalid dependency shape.")

    timeline, _ = _read_render_model(
        bundle.root,
        state.timeline.path,
        ResolvedTimeline,
        expected_file_hash=state.timeline.file_sha256,
        label="dependency render timeline",
    )
    composition_content = {
        item.key: item.fingerprint for item in composition.contributions
    }.get("composition.content")
    if (
        not verify_artifact_hash(timeline)
        or timeline.composition_spec_id != composition.artifact_id
        or timeline.composition_spec_revision != composition.artifact_revision
        or timeline.composition_spec_hash != composition_content
        or timeline.composition_fingerprint != state.timeline_fingerprint
    ):
        raise _invalid("Fresh render evidence does not match its CompositionSpec timeline.")
    renderer_fingerprint = _fp(
        "ai-video-renderer-identity/1",
        state.renderer.model_dump(mode="json"),
    )
    for item in (timeline_node, source_node, render_node):
        contributions = {
            contribution.key: contribution.fingerprint
            for contribution in item.contributions
        }
        if contributions.get("renderer.identity") != renderer_fingerprint:
            raise _invalid("Fresh render evidence renderer identity is stale.")


def _verify_manifest_dependency_states(
    bundle: LoadedProductionProject,
    graph: DependencyGraphSnapshot,
) -> None:
    states = bundle.manifest.dependency_states
    state_by_id = {state.node_id: state for state in states}
    node_by_id = {node.node_id: node for node in graph.nodes}
    active_ids = set(node_by_id)
    if set(state_by_id).intersection(active_ids) != active_ids:
        raise _invalid("Manifest dependency states do not cover the active graph.")
    for node_id, state in state_by_id.items():
        if node_id in active_ids:
            if state.lifecycle is DependencyLifecycle.SUPERSEDED:
                raise _invalid("Active dependency node cannot be superseded.")
        elif state.lifecycle is not DependencyLifecycle.SUPERSEDED:
            raise _invalid("Only absent dependency nodes may be retained as superseded.")
        elif state.graph_revision_id == graph.revision_id:
            raise _invalid("Superseded dependency state must preserve its origin revision.")

    desired = desired_fingerprints(graph)
    for node_id in sorted(active_ids):
        state = state_by_id[node_id]
        node = node_by_id[node_id]
        if state.desired_fingerprint != desired[node_id]:
            raise _invalid("Manifest dependency desired fingerprint is invalid.")
        evidence = state.applied_evidence
        if evidence is None:
            continue
        if evidence.artifact_id != node.artifact_id:
            raise _invalid("Dependency evidence artifact does not match its node.")
        if isinstance(evidence, ProjectDependencyEvidence):
            if node.kind is not DependencyNodeKind.CREATIVE_ARTIFACT:
                raise _invalid("Project evidence has an invalid dependency owner.")
            _verify_dependency_project_evidence(bundle, evidence, node, (graph, state))
        elif isinstance(evidence, RegistryDependencyEvidence):
            if node.kind is not DependencyNodeKind.ASSET:
                raise _invalid("Registry evidence has an invalid dependency owner.")
            _verify_dependency_registry_evidence(bundle, evidence, node)
        elif isinstance(evidence, RenderDependencyEvidence):
            if node.kind in {
                DependencyNodeKind.CREATIVE_ARTIFACT,
                DependencyNodeKind.ASSET,
            }:
                raise _invalid("Render evidence has an invalid dependency owner.")
            _verify_dependency_render_evidence(
                bundle,
                evidence,
                node=node,
                graph=graph,
                require_current=state.lifecycle is DependencyLifecycle.FRESH,
            )

    render_domain_ids = {
        node.node_id
        for node in graph.nodes
        if node.kind
        in {
            DependencyNodeKind.COMPOSITION_SPEC,
            DependencyNodeKind.RESOLVED_TIMELINE,
            DependencyNodeKind.RENDERER_SOURCE,
            DependencyNodeKind.RENDER,
        }
    }
    fresh_render_ids = {
        node_id
        for node_id in render_domain_ids
        if state_by_id[node_id].lifecycle is DependencyLifecycle.FRESH
    }
    if fresh_render_ids and fresh_render_ids != render_domain_ids:
        raise _invalid("Render-domain dependency nodes must become fresh atomically.")

    active_render_pointers = {
        state.applied_evidence.pointer
        for node_id, state in state_by_id.items()
        if node_id in active_ids
        and isinstance(state.applied_evidence, RenderDependencyEvidence)
    }
    if bundle.manifest.active_render_state is None:
        if active_render_pointers:
            raise _invalid("Active render evidence requires active_render_state.")
    elif active_render_pointers != {bundle.manifest.active_render_state}:
        raise _invalid(
            "Active render evidence must match the Manifest-selected render state."
        )

    for node_id in sorted(set(state_by_id) - active_ids):
        evidence = state_by_id[node_id].applied_evidence
        if isinstance(evidence, ProjectDependencyEvidence):
            _verify_dependency_project_evidence(bundle, evidence)
        elif isinstance(evidence, RegistryDependencyEvidence):
            _verify_dependency_registry_evidence(bundle, evidence)
        elif isinstance(evidence, RenderDependencyEvidence):
            _verify_dependency_render_evidence(bundle, evidence)

    try:
        resolved = resolve_dependency_state(graph, states)
    except AiVideoError as exc:
        raise _invalid(
            "Manifest dependency lifecycle is invalid.", exc.technical_detail
        ) from exc
    if resolved.states != tuple(sorted(states, key=lambda state: state.node_id)):
        raise _invalid("Manifest dependency lifecycle is inconsistent with the graph.")


def load_production_project_candidate(
    root: str | Path,
    manifest: ProductionManifest,
    project_path: Path,
    registry_path: Path,
) -> LoadedProductionProject:
    """Read and validate explicit P2A candidate snapshots without activating them."""
    try:
        resolved_root = Path(root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise _invalid(
            "Production project root could not be resolved safely.", str(exc)
        ) from exc
    if not resolved_root.is_dir():
        raise _invalid("Production project root must be a directory.")
    project_path = Path(project_path)
    registry_path = Path(registry_path)
    resolved_project_path = _resolve_candidate_project_path(resolved_root, project_path)
    resolved_registry_path = _resolve_candidate_registry_path(
        resolved_root, registry_path
    )
    project = _load_yaml_artifact(resolved_project_path, ProductionProject)
    if manifest.project_id != project.project_id:
        raise _invalid("Production manifest project_id does not match project.")
    return _build_loaded_project(
        resolved_root,
        manifest,
        project,
        resolved_registry_path.relative_to(resolved_root),
    )


def load_production_project(path: str | Path) -> LoadedProductionProject:
    supplied_path = Path(path)
    if supplied_path.name != "project.yaml":
        raise _invalid("Production project entry point must be named project.yaml.")
    try:
        root = supplied_path.parent.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise _invalid(
            "Production project root could not be resolved safely.", str(exc)
        ) from exc
    _validate_canonical_entrypoint(root, supplied_path)
    manifest = _load_json_model(
        _resolve_input(
            root,
            Path("state/manifest.json"),
            allowed_root=root / "state",
        ),
        ProductionManifest,
    )
    project_path = _resolve_candidate_project_path(root, manifest.active_project.path)
    registry_path = _resolve_candidate_registry_path(
        root, manifest.active_registry.path
    )
    _verify_snapshot_file_hash(project_path, manifest.active_project.file_sha256, "project")
    _verify_snapshot_file_hash(
        registry_path, manifest.active_registry.file_sha256, "registry"
    )
    bundle = load_production_project_candidate(
        root,
        manifest,
        manifest.active_project.path,
        manifest.active_registry.path,
    )
    _verify_manifest_snapshot_identity(bundle, manifest.active_project, manifest.active_registry)
    _verify_active_voice_evidence(bundle)
    verify_active_image_evidence(bundle)
    verify_paid_provider_evidence(root, manifest)
    verify_manifest_video_evidence(bundle, manifest)
    if manifest.active_dependency_graph is not None:
        dependency_graph = _load_active_dependency_graph(
            root, manifest.active_dependency_graph
        )
        _verify_manifest_dependency_states(bundle, dependency_graph)
        bundle = bundle.model_copy(update={"dependency_graph": dependency_graph})
    if manifest.schema_version == "2.4" or (
        manifest.schema_version in {"2.5", "2.6", "2.7", "2.8"}
        and manifest.active_qa_policy is not None
    ):
        if manifest.active_qa_policy is None:
            raise _invalid(f"Manifest {manifest.schema_version} requires an active QA policy.")
        qa_policy = load_qa_policy(root, manifest.active_qa_policy)
        current_render = (
            _load_exact_render_state(bundle, manifest.active_render_state)
            if manifest.active_render_state is not None
            else None
        )
        for receipt_pointer in manifest.active_review_receipts:
            receipt = load_review_receipt(root, receipt_pointer)
            if (
                current_render is None
                or receipt.qa_policy != manifest.active_qa_policy
                or receipt.dependency_graph_revision_id
                != manifest.active_dependency_graph.revision_id
                or receipt.render_state != manifest.active_render_state
                or receipt.render_output_sha256
                != current_render.output.file_sha256
                or receipt.timeline_fingerprint
                != current_render.timeline_fingerprint
            ):
                raise _invalid("Active Review Receipt is stale.")
        if (
            manifest.final_acceptance_state is not None
            and manifest.final_acceptance_state.active_receipt is not None
        ):
            final_receipt = load_final_acceptance_receipt(
                root, manifest.final_acceptance_state.active_receipt
            )
            required_layers = {
                item
                for item in qa_policy.required_layers
                if item.value != "final_acceptance"
            }
            selected_layers = {
                item.layer for item in final_receipt.required_review_receipts
            }
            dependency_states_hash = canonical_sha256(
                {
                    "dependency_states": [
                        item.model_dump(mode="json")
                        for item in manifest.dependency_states
                    ]
                }
            )
            if (
                current_render is None
                or
                final_receipt.dependency_graph != manifest.active_dependency_graph
                or final_receipt.render_state != manifest.active_render_state
                or final_receipt.qa_policy != manifest.active_qa_policy
                or final_receipt.dependency_states_hash != dependency_states_hash
                or final_receipt.render_output_sha256
                != current_render.output.file_sha256
                or final_receipt.timeline_fingerprint
                != current_render.timeline_fingerprint
                or selected_layers != required_layers
                or set(final_receipt.required_review_receipts)
                != {
                    item
                    for item in manifest.active_review_receipts
                    if item.layer in required_layers
                }
            ):
                raise _invalid("Final Acceptance Receipt is stale.")
        bundle = bundle.model_copy(update={"qa_policy": qa_policy})
    if manifest.active_render_state is not None:
        render_state = (
            _load_exact_render_state(bundle, manifest.active_render_state)
            if manifest.schema_version in {"2.3", "2.4", "2.5", "2.6", "2.7", "2.8"}
            else load_verified_render_state(
                root,
                manifest.active_render_state,
                project=manifest.active_project,
                registry=manifest.active_registry,
            )
        )
        bundle = bundle.model_copy(update={"render_state": render_state})
    return bundle
