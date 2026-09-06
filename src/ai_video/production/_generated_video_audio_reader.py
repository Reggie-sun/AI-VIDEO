"""Strict reader for the independently derived generated-video-audio lane."""

from __future__ import annotations

import hashlib
import json

import yaml
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import audio_content_fingerprint
from ai_video.production._generated_video_audio_contracts import (
    GeneratedVideoAudioReceipt,
    canonical_generated_video_audio_receipt_path,
    generated_video_audio_derivation_identity,
)
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    LoadedProductionProject,
    PaidProviderAttemptPhase,
    ProductionProject,
    StateCommitStatus,
    ToolIdentity,
    VideoAttemptPhase,
)
from ai_video.production.paid_provider import BudgetReservationStatus, PaidProviderSubmitOutcome
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.video import (
    BillingKind,
    VideoExecutionKind,
    VideoSubmission,
    VideoTaskState,
)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _registry(bundle: LoadedProductionProject, pointer: object) -> AssetRegistrySnapshot:
    try:
        raw = _read_regular_file_nofollow(bundle.root / pointer.path, contained_by=bundle.root)
        registry = AssetRegistrySnapshot.model_validate_json(raw.data)
    except (OSError, ValueError, ValidationError, AiVideoError) as exc:
        raise _invalid("Generated video audio registry evidence could not be reopened.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or registry.revision_id != pointer.revision_id
        or registry.content_hash != pointer.content_hash
        or registry_semantic_sha256(registry) != registry.content_hash
    ):
        raise _invalid("Generated video audio registry evidence identity is invalid.")
    return registry


def _artifact_hash(entries: tuple[tuple[str, str], ...]) -> str:
    return hashlib.sha256(
        json.dumps(sorted(entries), separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _canonical_model_file_sha256(model) -> str:
    payload = json.dumps(
        model.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    return hashlib.sha256(payload).hexdigest()


def _validate_source_closure(receipt: GeneratedVideoAudioReceipt) -> None:
    request = receipt.source_request
    observation = receipt.source_observation
    fetched = receipt.source_fetch
    gate = receipt.source_gate
    submit = receipt.source_submit
    reservation = receipt.source_reservation
    budget = receipt.source_budget
    try:
        submission = VideoSubmission.from_paid_submit_receipt(resolved=request, receipt=submit)
    except AiVideoError as exc:
        raise _invalid("Generated video audio source submission is invalid.", exc.user_message) from exc
    if (
        request.execution_kind is not VideoExecutionKind.REMOTE
        or request.billing_kind is not BillingKind.METERED
        or observation.state is not VideoTaskState.SUCCEEDED
        or observation.paid_submit_receipt_fingerprint != submit.submit_receipt_fingerprint
        or observation.submission_fingerprint != submission.submission_fingerprint
        or fetched.paid_submit_receipt_fingerprint != submit.submit_receipt_fingerprint
        or fetched.submission_fingerprint != submission.submission_fingerprint
        or fetched.observation_fingerprint != observation.observation_fingerprint
        or fetched.provider_file_id != observation.provider_file_id
        or submit.outcome is not PaidProviderSubmitOutcome.ACCEPTED
        or submit.attempt_id != receipt.source_attempt_id
        or submit.request_fingerprint != request.resolved_generation_hash
        or gate.preview.attempt_id != receipt.source_attempt_id
        or gate.preview.request_fingerprint != request.resolved_generation_hash
        or gate.gate_receipt_fingerprint != submit.gate_receipt_fingerprint
        or gate.preview.preview_fingerprint != submit.preview_fingerprint
        or gate.reservation_id != submit.reservation_id
        or receipt.source_budget_pointer.content_hash != budget.content_hash
        or receipt.source_budget_pointer.revision != budget.revision
        or receipt.source_budget_pointer.file_sha256 != _canonical_model_file_sha256(budget)
        or reservation not in budget.reservations
        or reservation.status is not BudgetReservationStatus.SETTLED
        or reservation.actual_cost_microunits is None
        or reservation.attempt_id != receipt.source_attempt_id
        or reservation.request_fingerprint != request.resolved_generation_hash
        or reservation.preview_fingerprint != gate.preview.preview_fingerprint
        or reservation.submit_receipt_fingerprint != submit.submit_receipt_fingerprint
        or reservation.reservation_id != submit.reservation_id
    ):
        raise _invalid("Generated video audio source closure is invalid.")


def _verify_derived_asset(bundle: LoadedProductionProject, asset) -> str:
    if asset.audio_metadata is None:
        raise _invalid("Generated video audio asset has no audio metadata.")
    receipt_id = asset.audio_metadata.provenance_receipt_id
    try:
        raw_receipt = _read_regular_file_nofollow(
            bundle.root / canonical_generated_video_audio_receipt_path(receipt_id),
            contained_by=bundle.root / "state" / "generated-video-audio",
        )
        receipt = GeneratedVideoAudioReceipt.model_validate_json(raw_receipt.data)
        audio = _read_regular_file_nofollow(
            bundle.root / asset.artifact_path,
            contained_by=bundle.root / "assets" / "audio",
        )
    except (OSError, ValueError, ValidationError, AiVideoError) as exc:
        raise _invalid("Generated video audio receipt or WAV could not be reopened.", str(exc)) from exc
    if raw_receipt.file_sha256 != receipt_id:
        raise _invalid("Generated video audio receipt file identity is invalid.")
    try:
        base_project_raw = _read_regular_file_nofollow(
            bundle.root / receipt.target_base_project.path,
            contained_by=bundle.root,
        )
        base_project = ProductionProject.model_validate(yaml.safe_load(base_project_raw.data))
    except (OSError, ValueError, ValidationError, yaml.YAMLError) as exc:
        raise _invalid("Generated video audio base project could not be reopened.", str(exc)) from exc
    if (
        base_project_raw.file_sha256 != receipt.target_base_project.file_sha256
        or base_project.revision != receipt.target_base_project.revision
        or base_project.content_hash != receipt.target_base_project.content_hash
        or not verify_artifact_hash(base_project)
        or base_project.project_id != receipt.target_project_id
    ):
        raise _invalid("Generated video audio base project identity is invalid.")
    identity = generated_video_audio_derivation_identity(
        target_project_id=receipt.target_project_id,
        target_attempt_id=receipt.target_attempt_id,
        target_asset_id=receipt.target_asset_id,
        target_base_project=receipt.target_base_project,
        target_base_registry=receipt.target_base_registry,
        target_audio_metadata=receipt.target_audio_metadata,
        target_usage_license=receipt.target_usage_license,
        source_project_id=receipt.source_project_id,
        source_attempt_id=receipt.source_attempt_id,
        source_request=receipt.source_request,
        source_observation=receipt.source_observation,
        source_fetch=receipt.source_fetch,
        source_gate=receipt.source_gate,
        source_submit=receipt.source_submit,
        source_budget_pointer=receipt.source_budget_pointer,
        source_budget=receipt.source_budget,
        source_reservation=receipt.source_reservation,
        extraction_ffmpeg=receipt.extraction_ffmpeg,
        probe_ffprobe=receipt.probe_ffprobe,
    )
    if (
        receipt.derivation_identity != identity
        or receipt.target_project_id != bundle.manifest.project_id
        or receipt.target_asset_id != asset.asset_id
        or receipt.target_audio_metadata != asset.audio_metadata.model_copy(
            update={"provenance_receipt_id": "pending-generated-video-audio-receipt"}
        )
        or asset.source_kind is not AssetSourceKind.GENERATED
        or asset.asset_type is not AssetType.VOICE
        or receipt.target_audio_metadata.source.kind is not AssetSourceKind.GENERATED
        or receipt.target_audio_metadata.source.provider_or_tool
        != ToolIdentity(
            name=receipt.source_request.provider_kind,
            version=receipt.source_request.model_id,
        )
        or asset.tool != receipt.target_audio_metadata.source.provider_or_tool
        or asset.tool
        != ToolIdentity(
            name=receipt.source_request.provider_kind,
            version=receipt.source_request.model_id,
        )
        or receipt.target_audio_metadata.source.input_artifact_ids
        or receipt.target_audio_metadata.source.input_fingerprint
        != receipt.source_fetch.artifact_sha256
        or asset.input_artifact_ids
        or asset.input_fingerprint != receipt.source_fetch.artifact_sha256
        or asset.usage_license != receipt.target_usage_license
        or asset.sha256 != receipt.probe.file_sha256
        or asset.size_bytes != receipt.probe.size_bytes
        or audio.file_sha256 != receipt.probe.file_sha256
        or len(audio.data) != receipt.probe.size_bytes
        or receipt.probe.content_fingerprint != audio_content_fingerprint(receipt.probe)
        or receipt.probe.ffmpeg != receipt.extraction_ffmpeg
        or receipt.probe.ffprobe != receipt.probe_ffprobe
        or receipt.target_audio_metadata.duration_samples != receipt.probe.duration_samples
        or receipt.target_audio_metadata.sample_rate_hz != receipt.probe.sample_rate_hz
        or receipt.target_audio_metadata.channels != receipt.probe.channels
        or receipt.target_audio_metadata.channel_layout != receipt.probe.channel_layout
        or receipt.target_audio_metadata.codec_name != receipt.probe.codec_name
        or receipt.target_audio_metadata.loudness != receipt.probe.loudness
        or asset.egress.destination != receipt.source_gate.preview.destination
        or asset.egress.authorization_receipt_id
        != receipt.source_gate.authorization.egress_policy_receipt_id
        or asset.egress.request_fingerprint != receipt.source_request.resolved_generation_hash
        or asset.egress.payload_fingerprint != receipt.source_gate.preview.preview_fingerprint
        or asset.egress.retention_mode != receipt.source_gate.preview.retention_mode
        or asset.egress.provider_policy_snapshot_id
        != receipt.source_gate.preview.provider_policy_snapshot_id
        or asset.cost_receipt_id != receipt.source_budget.content_hash
    ):
        raise _invalid("Generated video audio asset does not match its exact receipt.")
    _validate_source_closure(receipt)
    attempt = next(
        (item for item in bundle.manifest.attempts if item.attempt_id == receipt.target_attempt_id),
        None,
    )
    if (
        attempt is None
        or attempt.operation != "audio_import"
        or attempt.status is not StateCommitStatus.SUCCEEDED
        or attempt.base_project != receipt.target_base_project
        or attempt.base_registry != receipt.target_base_registry
        or attempt.candidate_project is not None
        or attempt.candidate_registry is None
    ):
        raise _invalid("Generated video audio target transaction is invalid.")
    base = _registry(bundle, attempt.base_registry)
    candidate = _registry(bundle, attempt.candidate_registry)
    if (
        bundle.registry.assets[: len(candidate.assets)] != candidate.assets
        or candidate.assets[: len(base.assets)] != base.assets
        or candidate.assets[len(base.assets) :] != (asset,)
    ):
        raise _invalid("Generated video audio target registry suffix is invalid.")
    expected_artifacts = (
        (attempt.base_project.path.as_posix(), attempt.base_project.file_sha256),
        (attempt.candidate_registry.path.as_posix(), attempt.candidate_registry.file_sha256),
        (asset.artifact_path.as_posix(), asset.sha256),
        (canonical_generated_video_audio_receipt_path(receipt_id).as_posix(), receipt_id),
    )
    if attempt.candidate_artifacts_hash != _artifact_hash(expected_artifacts):
        raise _invalid("Generated video audio target artifact closure is invalid.")
    return asset.asset_id


def verify_derived_generated_video_audio(bundle: LoadedProductionProject) -> set[str]:
    """Return only generated voice IDs proven by the derived-audio closure."""

    claims: set[str] = set()
    for asset in bundle.registry.assets:
        if asset.asset_type is AssetType.VOICE and asset.source_kind is AssetSourceKind.GENERATED:
            try:
                claim = _verify_derived_asset(bundle, asset)
            except AiVideoError:
                continue
            if claim in claims:
                raise _invalid("Generated video audio claim is ambiguous.")
            claims.add(claim)
    return claims


def verify_active_generated_voice_claims(
    bundle: LoadedProductionProject, claimed_audio_ids: set[str]
) -> None:
    """Require every generated voice to have exactly one verified ownership lane."""

    generated_voice_ids = {
        asset.asset_id
        for asset in bundle.registry.assets
        if asset.asset_type is AssetType.VOICE and asset.source_kind is AssetSourceKind.GENERATED
    }
    derived_audio_ids = verify_derived_generated_video_audio(bundle)
    if (
        derived_audio_ids & claimed_audio_ids
        or generated_voice_ids != claimed_audio_ids | derived_audio_ids
    ):
        raise _invalid("Active generated voice assets do not match succeeded attempts.")
