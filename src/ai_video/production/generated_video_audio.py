"""Derive one registered WAV asset from a settled generated-video fetch."""

from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from pydantic import Field, ValidationError, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._paid_provider_project_reader import (
    load_paid_provider_budget,
    load_paid_provider_gate_receipt,
    load_paid_provider_submit_receipt,
)
from ai_video.production._state_commit_common import (
    _canonical_json_bytes,
    _state_invalid,
    prepare_audio_registry_commit,
)
from ai_video.production._state_commit_contracts import PreparedArtifact, StateCommitRequest
from ai_video.production._generated_video_audio_contracts import (
    GeneratedVideoAudioReceipt,
    canonical_generated_video_audio_receipt_path,
    generated_video_audio_derivation_identity,
)
from ai_video.production._video_project_reader import (
    load_video_fetch_receipt,
    load_video_request_receipt,
    load_video_status_receipt,
)
from ai_video.production.audio import AudioProbeToolchain, probe_audio_candidate
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AUDIO_KIND_TO_ASSET_TYPE,
    AudioAssetMetadata,
    AudioKind,
    AudioSource,
    EgressMetadata,
    PaidProviderAttemptPhase,
    StrictModel,
    ToolIdentity,
    VideoAttemptPhase,
)
from ai_video.production.paid_provider import BudgetReservationStatus, PaidProviderSubmitOutcome
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_audio_asset_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.video import (
    BillingKind,
    VideoExecutionKind,
    VideoSubmission,
    VideoTaskState,
)


_Runner = Callable[..., subprocess.CompletedProcess]


def _audio_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_STATE_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class GeneratedVideoAudioRequest(StrictModel):
    """The target audio identity and the exact settled source video attempt."""

    attempt_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    source_project_root: Path
    source_attempt_id: str = Field(min_length=1)
    audio_kind: AudioKind
    speaker_id: str | None = None
    voice_id: str | None = None
    language: str | None = None
    script_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    usage_license: str = Field(min_length=1)

    @model_validator(mode="after")
    def _require_generated_speech_identity(self) -> "GeneratedVideoAudioRequest":
        if self.audio_kind not in {AudioKind.DIALOGUE, AudioKind.NARRATION}:
            raise ValueError("generated video audio extraction supports dialogue or narration only")
        if (
            not self.speaker_id
            or not self.voice_id
            or not self.language
            or self.script_hash is None
        ):
            raise ValueError("generated speech extraction requires speaker, voice, language, and script")
        try:
            resolved = self.source_project_root.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ValueError("source project root must resolve") from exc
        if not self.source_project_root.is_absolute() or resolved != self.source_project_root:
            raise ValueError("source project root must be canonical and absolute")
        return self


def _read_source_binding(
    request: GeneratedVideoAudioRequest,
    *,
    settled_budget_pointer=None,
) -> tuple[dict[str, object], bytes]:
    source = load_production_project(request.source_project_root / "project.yaml")
    attempt = next((item for item in source.manifest.attempts if item.attempt_id == request.source_attempt_id), None)
    if (
        attempt is None
        or attempt.operation != "video_generation"
        or attempt.status.value != "running"
        or attempt.video_generation_state is None
        or attempt.video_generation_state.phase is not VideoAttemptPhase.VALIDATE
        or attempt.video_generation_state.fetch_receipt is None
        or attempt.video_generation_state.latest_observation is None
        or attempt.paid_provider_state is None
        or attempt.paid_provider_state.phase is not PaidProviderAttemptPhase.SETTLED
        or attempt.paid_provider_state.submit_receipt is None
        or source.manifest.active_paid_provider_budget is None
    ):
        raise _audio_invalid("Generated video audio requires exact settled fetched source evidence.")
    state = attempt.video_generation_state
    paid = attempt.paid_provider_state
    resolved = load_video_request_receipt(request.source_project_root, state.request)
    observation = load_video_status_receipt(request.source_project_root, state.latest_observation)
    fetched = load_video_fetch_receipt(request.source_project_root, state.fetch_receipt)
    gate = load_paid_provider_gate_receipt(request.source_project_root, paid.gate_receipt)
    submit = load_paid_provider_submit_receipt(request.source_project_root, paid.submit_receipt)
    budget_pointer = settled_budget_pointer or source.manifest.active_paid_provider_budget
    budget = load_paid_provider_budget(request.source_project_root, budget_pointer)
    reservation = next((item for item in budget.reservations if item.reservation_id == paid.reservation_id), None)
    try:
        submission = VideoSubmission.from_paid_submit_receipt(resolved=resolved, receipt=submit)
    except AiVideoError as exc:
        raise _audio_invalid("Generated video audio source submission is invalid.", exc.user_message) from exc
    if (
        resolved.execution_kind is not VideoExecutionKind.REMOTE
        or resolved.billing_kind is not BillingKind.METERED
        or observation.state is not VideoTaskState.SUCCEEDED
        or observation.paid_submit_receipt_fingerprint != submit.submit_receipt_fingerprint
        or observation.submission_fingerprint != submission.submission_fingerprint
        or fetched.paid_submit_receipt_fingerprint != submit.submit_receipt_fingerprint
        or fetched.submission_fingerprint != submission.submission_fingerprint
        or fetched.observation_fingerprint != observation.observation_fingerprint
        or fetched.provider_file_id != observation.provider_file_id
        or submit.outcome is not PaidProviderSubmitOutcome.ACCEPTED
        or submit.attempt_id != request.source_attempt_id
        or submit.request_fingerprint != resolved.resolved_generation_hash
        or gate.preview.attempt_id != request.source_attempt_id
        or gate.preview.request_fingerprint != resolved.resolved_generation_hash
        or submit.preview_fingerprint != gate.preview.preview_fingerprint
        or submit.gate_receipt_fingerprint != gate.gate_receipt_fingerprint
        or submit.reservation_id != gate.reservation_id
        or reservation is None
        or reservation.status is not BudgetReservationStatus.SETTLED
        or reservation.actual_cost_microunits is None
        or reservation.attempt_id != request.source_attempt_id
        or reservation.request_fingerprint != resolved.resolved_generation_hash
        or reservation.preview_fingerprint != gate.preview.preview_fingerprint
        or reservation.submit_receipt_fingerprint != submit.submit_receipt_fingerprint
    ):
        raise _audio_invalid("Generated video audio requires exact settled source reservation evidence.")
    try:
        artifact = _read_regular_file_nofollow(
            request.source_project_root / state.fetch_receipt.artifact_path,
            contained_by=request.source_project_root / "state" / "video-generation" / "fetch",
        )
    except (OSError, ValueError) as exc:
        raise _audio_invalid("Could not reopen exact fetched video bytes.", str(exc)) from exc
    if artifact.file_sha256 != fetched.artifact_sha256 or len(artifact.data) != fetched.size_bytes:
        raise _audio_invalid("Fetched video bytes no longer match sealed source evidence.")
    return (
        {
            "source_project_id": source.manifest.project_id,
            "source_attempt_id": request.source_attempt_id,
            "source_request": resolved,
            "source_observation": observation,
            "source_fetch": fetched,
            "source_gate": gate,
            "source_submit": submit,
            "source_budget_pointer": budget_pointer,
            "source_budget": budget,
            "source_reservation": reservation,
        },
        artifact.data,
    )


def _extract_wav(source_video: bytes, toolchain: AudioProbeToolchain, runner: _Runner) -> bytes:
    try:
        with tempfile.TemporaryFile() as source_file, tempfile.TemporaryFile() as wav_file:
            source_file.write(source_video)
            source_file.flush()
            source_fd = os.dup(source_file.fileno())
            wav_fd = os.dup(wav_file.fileno())
            try:
                result = runner(
                    [
                        str(toolchain.ffmpeg_path),
                        "-nostdin",
                        "-y",
                        "-v",
                        "error",
                        "-i",
                        f"/proc/self/fd/{source_fd}",
                        "-map",
                        "0:a:0",
                        "-vn",
                        "-c:a",
                        "pcm_s16le",
                        "-f",
                        "wav",
                        f"/proc/self/fd/{wav_fd}",
                    ],
                    shell=False,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    close_fds=True,
                    pass_fds=(source_fd, wav_fd),
                    check=False,
                    text=False,
                    timeout=120,
                )
            finally:
                os.close(source_fd)
                os.close(wav_fd)
            wav_file.seek(0)
            output = wav_file.read()
    except (OSError, subprocess.SubprocessError) as exc:
        raise _audio_invalid("Generated video audio extraction tool could not run.", type(exc).__name__) from exc
    if result.returncode != 0 or not output:
        raise _audio_invalid("Fetched generated video has no extractable audio stream.")
    return output


def _probe_wav(payload: bytes, toolchain: AudioProbeToolchain, runner: _Runner):
    with tempfile.TemporaryFile() as audio_file:
        audio_file.write(payload)
        audio_file.flush()
        return probe_audio_candidate(
            audio_file.fileno(), mime_type="audio/wav", toolchain=toolchain, runner=runner
        )


def _active_registry(committer):
    loaded = load_production_project(committer._project_root / "project.yaml")
    return loaded.manifest, loaded


def _require_supported_target(manifest, loaded) -> None:
    if manifest.schema_version not in {"2.0", "2.1", "2.2"}:
        raise _audio_invalid("Generated video audio supports Manifest versions through 2.2 only.")
    if loaded.registry.schema_version != "2.1":
        raise _audio_invalid("Generated video audio requires Asset Registry 2.1.")


def _replay_if_exact(
    committer,
    request: GeneratedVideoAudioRequest,
    binding: dict[str, object],
    toolchain: AudioProbeToolchain,
):
    manifest, loaded = _active_registry(committer)
    existing = next((item for item in manifest.attempts if item.attempt_id == request.attempt_id), None)
    if existing is None:
        return None
    if existing.status.value != "succeeded" or existing.operation != "audio_import":
        raise _audio_invalid("Generated video audio attempt requires explicit recovery before replay.")
    record = next((item for item in loaded.registry.assets if item.asset_id == request.asset_id), None)
    if record is None or record.audio_metadata is None:
        raise _audio_invalid("Generated video audio replay asset is missing.")
    receipt_id = record.audio_metadata.provenance_receipt_id
    try:
        raw_receipt = _read_regular_file_nofollow(
            committer._project_root / canonical_generated_video_audio_receipt_path(receipt_id),
            contained_by=committer._project_root / "state" / "generated-video-audio",
        )
        receipt = GeneratedVideoAudioReceipt.model_validate_json(raw_receipt.data)
        audio = _read_regular_file_nofollow(
            committer._project_root / record.artifact_path,
            contained_by=committer._project_root / "assets" / "audio",
        )
    except (OSError, ValueError, ValidationError, AiVideoError) as exc:
        raise _audio_invalid("Generated video audio replay evidence could not be reopened.", str(exc)) from exc
    expected_identity = generated_video_audio_derivation_identity(
        target_project_id=manifest.project_id,
        target_attempt_id=request.attempt_id,
        target_asset_id=request.asset_id,
        target_base_project=receipt.target_base_project,
        target_base_registry=receipt.target_base_registry,
        target_audio_metadata=receipt.target_audio_metadata,
        target_usage_license=request.usage_license,
        **binding,
        extraction_ffmpeg=toolchain.ffmpeg,
        probe_ffprobe=toolchain.ffprobe,
    )
    if (
        raw_receipt.file_sha256 != receipt_id
        or receipt.derivation_identity != expected_identity
        or receipt.target_project_id != manifest.project_id
        or receipt.target_attempt_id != request.attempt_id
        or receipt.target_asset_id != request.asset_id
        or receipt.target_usage_license != request.usage_license
        or receipt.target_audio_metadata.audio_kind is not request.audio_kind
        or receipt.target_audio_metadata.speaker_id != request.speaker_id
        or receipt.target_audio_metadata.voice_id != request.voice_id
        or receipt.target_audio_metadata.language != request.language
        or receipt.target_audio_metadata.script_hash != request.script_hash
        or receipt.target_audio_metadata
        != record.audio_metadata.model_copy(
            update={"provenance_receipt_id": "pending-generated-video-audio-receipt"}
        )
        or receipt.source_project_id != binding["source_project_id"]
        or receipt.source_attempt_id != binding["source_attempt_id"]
        or receipt.source_request != binding["source_request"]
        or receipt.source_observation != binding["source_observation"]
        or receipt.source_fetch != binding["source_fetch"]
        or receipt.source_gate != binding["source_gate"]
        or receipt.source_submit != binding["source_submit"]
        or receipt.source_budget_pointer != binding["source_budget_pointer"]
        or receipt.source_budget != binding["source_budget"]
        or receipt.source_reservation != binding["source_reservation"]
        or receipt.extraction_ffmpeg != toolchain.ffmpeg
        or receipt.probe_ffprobe != toolchain.ffprobe
        or audio.file_sha256 != receipt.probe.file_sha256
        or len(audio.data) != receipt.probe.size_bytes
        or record.sha256 != receipt.probe.file_sha256
        or record.size_bytes != receipt.probe.size_bytes
        or record.source_kind is not AssetSourceKind.GENERATED
    ):
        raise _audio_invalid("Generated video audio replay identity changed.")
    return manifest


def _existing_receipt(committer, request: GeneratedVideoAudioRequest):
    manifest, loaded = _active_registry(committer)
    existing = next((item for item in manifest.attempts if item.attempt_id == request.attempt_id), None)
    if existing is None:
        return None
    record = next((item for item in loaded.registry.assets if item.asset_id == request.asset_id), None)
    if record is None or record.audio_metadata is None:
        raise _audio_invalid("Generated video audio replay asset is missing.")
    try:
        raw = _read_regular_file_nofollow(
            committer._project_root
            / canonical_generated_video_audio_receipt_path(
                record.audio_metadata.provenance_receipt_id
            ),
            contained_by=committer._project_root / "state" / "generated-video-audio",
        )
        return GeneratedVideoAudioReceipt.model_validate_json(raw.data)
    except (OSError, ValueError) as exc:
        raise _audio_invalid("Generated video audio replay receipt could not be reopened.", str(exc)) from exc


def register_generated_video_audio(
    committer,
    request: GeneratedVideoAudioRequest,
    *,
    toolchain: AudioProbeToolchain,
    runner: _Runner = subprocess.run,
):
    """Register a derived WAV through the sole target ``ProductionStateCommitter``."""

    target_manifest, target_loaded = _active_registry(committer)
    _require_supported_target(target_manifest, target_loaded)
    existing_receipt = _existing_receipt(committer, request)
    binding, source_bytes = _read_source_binding(
        request,
        settled_budget_pointer=(
            None if existing_receipt is None else existing_receipt.source_budget_pointer
        ),
    )
    replay = _replay_if_exact(committer, request, binding, toolchain)
    if replay is not None:
        return replay
    manifest, loaded = _active_registry(committer)
    if (
        any(item.attempt_id == request.attempt_id for item in manifest.attempts)
        or any(item.asset_id == request.asset_id for item in loaded.registry.assets)
    ):
        raise _audio_invalid("Generated video audio target attempt or asset ID already exists.")
    wav = _extract_wav(source_bytes, toolchain, runner)
    probe = _probe_wav(wav, toolchain, runner)
    source_request = binding["source_request"]
    source_gate = binding["source_gate"]
    source_provider = ToolIdentity(
        name=source_request.provider_kind,
        version=source_request.model_id,
    )
    provisional_metadata = AudioAssetMetadata(
        audio_kind=request.audio_kind,
        source=AudioSource(
            kind=AssetSourceKind.GENERATED,
            provider_or_tool=source_provider,
            input_artifact_ids=(),
            input_fingerprint=binding["source_fetch"].artifact_sha256,
            original_reference=f"video-fetch:{source_request.resolved_generation_hash}",
        ),
        speaker_id=request.speaker_id,
        voice_id=request.voice_id,
        language=request.language,
        script_hash=request.script_hash,
        duration_samples=probe.duration_samples,
        sample_rate_hz=probe.sample_rate_hz,
        channels=probe.channels,
        channel_layout=probe.channel_layout,
        codec_name=probe.codec_name,
        loudness=probe.loudness,
        provenance_receipt_id="pending-generated-video-audio-receipt",
    )
    identity = generated_video_audio_derivation_identity(
        target_project_id=manifest.project_id,
        target_attempt_id=request.attempt_id,
        target_asset_id=request.asset_id,
        target_base_project=manifest.active_project,
        target_base_registry=manifest.active_registry,
        target_audio_metadata=provisional_metadata,
        target_usage_license=request.usage_license,
        **binding,
        extraction_ffmpeg=toolchain.ffmpeg,
        probe_ffprobe=toolchain.ffprobe,
    )
    receipt = GeneratedVideoAudioReceipt.create(
        derivation_identity=identity,
        target_project_id=manifest.project_id,
        target_attempt_id=request.attempt_id,
        target_asset_id=request.asset_id,
        target_base_project=manifest.active_project,
        target_base_registry=manifest.active_registry,
        target_audio_metadata=provisional_metadata,
        target_usage_license=request.usage_license,
        **binding,
        extraction_ffmpeg=toolchain.ffmpeg,
        probe_ffprobe=toolchain.ffprobe,
        probe=probe,
    )
    receipt_payload = _canonical_json_bytes(receipt)
    receipt_file_sha256 = hashlib.sha256(receipt_payload).hexdigest()
    metadata = provisional_metadata.model_copy(update={"provenance_receipt_id": receipt_file_sha256})
    record = AssetRecord(
        asset_id=request.asset_id,
        asset_type=AUDIO_KIND_TO_ASSET_TYPE[request.audio_kind],
        artifact_path=canonical_audio_asset_path(probe.file_sha256),
        sha256=probe.file_sha256,
        size_bytes=probe.size_bytes,
        mime_type="audio/wav",
        source_kind=AssetSourceKind.GENERATED,
        tool=source_provider,
        input_artifact_ids=(),
        input_fingerprint=binding["source_fetch"].artifact_sha256,
        creation_receipt_id=f"generated-video-audio-{receipt_file_sha256}",
        usage_license=request.usage_license,
        egress=EgressMetadata(
            remote=True,
            destination=source_gate.preview.destination,
            authorization_receipt_id=source_gate.authorization.egress_policy_receipt_id,
            request_fingerprint=source_request.resolved_generation_hash,
            payload_fingerprint=source_gate.preview.preview_fingerprint,
            retention_mode=source_gate.preview.retention_mode,
            provider_policy_snapshot_id=source_gate.preview.provider_policy_snapshot_id,
        ),
        cost_receipt_id=binding["source_budget"].content_hash,
        audio_metadata=metadata,
    )
    registry = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id="0" * 64,
        content_hash="0" * 64,
        assets=loaded.registry.assets + (record,),
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": registry_hash, "content_hash": registry_hash})
    project_snapshot = _read_regular_file_nofollow(
        committer._project_root / manifest.active_project.path,
        contained_by=committer._project_root,
    )
    base = prepare_audio_registry_commit(
        manifest=manifest,
        project=loaded.project,
        base_registry=loaded.registry,
        registry=registry,
        attempt_id=request.attempt_id,
        artifacts=(
            PreparedArtifact(record.artifact_path, wav, probe.file_sha256),
        ),
        active_project_artifact=PreparedArtifact(
            manifest.active_project.path, project_snapshot.data, project_snapshot.file_sha256
        ),
    )
    artifacts = {
        item.relative_path: item
        for item in (
            *base.artifacts,
            PreparedArtifact(
                canonical_generated_video_audio_receipt_path(receipt_file_sha256),
                receipt_payload,
                receipt_file_sha256,
            ),
        )
    }
    rechecked_binding, rechecked_source = _read_source_binding(
        request,
        settled_budget_pointer=binding["source_budget_pointer"],
    )
    if rechecked_binding != binding or rechecked_source != source_bytes:
        raise _audio_invalid("Generated video audio source changed before registration.")
    return committer.commit(
        StateCommitRequest(
            attempt_id=request.attempt_id,
            operation="audio_import",
            expected_manifest_revision=manifest.manifest_revision,
            artifacts=tuple(sorted(artifacts.values(), key=lambda item: item.relative_path.as_posix())),
            next_project=base.next_project,
            next_registry=base.next_registry,
        )
    )
