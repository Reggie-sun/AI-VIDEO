"""Deterministic local preparation for generated voice candidates.

The factory materializes and probes exact provider bytes before the canonical
state committer reconstructs the authoritative registry record and activates it.
It has no Provider, Manifest, or activation authority.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import (
    AudioProbeToolchain,
    PreparedAudioImport,
    VoiceCallAuthorization,
    VoiceGenerationPreview,
    VoiceGenerationRequest,
    VoiceProviderResult,
    materialize_audio_candidate,
    probe_audio_candidate,
)
from ai_video.production.models import (
    AssetRecord,
    AssetSourceKind,
    AssetType,
    AudioAssetMetadata,
    AudioSource,
    EgressMetadata,
)
from ai_video.production.paths import canonical_audio_asset_path
from ai_video.production.state_commit import (
    PreparedVoiceCandidate,
    VoiceAttemptPaths,
)


def _candidate_invalid(message: str) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.AUDIO_ASSET_INVALID,
        user_message=message,
        retryable=False,
    )


def _receipt_hash(receipt: object) -> str:
    model_dump = getattr(receipt, "model_dump")
    payload = json.dumps(
        model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    payload = (payload + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


VoiceCandidatePreparer = Callable[
    [
        VoiceGenerationRequest,
        VoiceGenerationPreview,
        VoiceCallAuthorization,
        VoiceProviderResult,
        VoiceAttemptPaths,
    ],
    PreparedVoiceCandidate,
]


def make_voice_candidate_preparer(
    root: Path, toolchain: AudioProbeToolchain
) -> VoiceCandidatePreparer:
    """Return the injected voice preparer for exact generated WAV results."""

    def prepare(
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
        result: VoiceProviderResult,
        paths: VoiceAttemptPaths,
    ) -> PreparedVoiceCandidate:
        del preview
        snapshot = materialize_audio_candidate(
            result.audio_bytes,
            candidate_path=paths.audio_candidate_path,
            project_root=root,
            attempt_id=request.attempt_id,
        )
        if snapshot.data != result.audio_bytes:
            raise _candidate_invalid("Voice candidate bytes changed during materialization.")
        with paths.audio_candidate_path.open("rb") as source:
            probe = probe_audio_candidate(
                source.fileno(),
                mime_type=result.content_type,
                toolchain=toolchain,
                measure_loudness=False,
            )
        if (
            probe.file_sha256 != result.audio_sha256
            or probe.size_bytes != len(result.audio_bytes)
        ):
            raise _candidate_invalid("Voice candidate bytes do not match the provider result.")
        if (
            probe.codec_name != request.output_codec
            or probe.sample_rate_hz != request.output_sample_rate_hz
            or probe.channels != request.output_channels
        ):
            raise _candidate_invalid("Voice candidate output does not match the exact request.")

        audio_id = f"voice-{request.attempt_id}"
        record = AssetRecord(
            asset_id=audio_id,
            asset_type=AssetType.VOICE,
            artifact_path=canonical_audio_asset_path(result.audio_sha256),
            sha256=result.audio_sha256,
            size_bytes=len(result.audio_bytes),
            mime_type=result.content_type,
            source_kind=AssetSourceKind.GENERATED,
            tool=result.provenance_receipt.adapter,
            input_artifact_ids=request.input_artifact_ids,
            input_fingerprint=request.input_fingerprint,
            creation_receipt_id=f"voice-result-{result.result_fingerprint}",
            usage_license=result.provenance_receipt.license_policy_decision,
            egress=EgressMetadata(
                remote=True,
                destination=authorization.destination,
                authorization_receipt_id=request.egress_authorization_receipt_id,
                request_fingerprint=request.voice_request_fingerprint,
                payload_fingerprint=request.script_hash,
                retention_mode=result.provenance_receipt.retention_mode,
                provider_policy_snapshot_id=result.provenance_receipt.policy_receipt_id,
            ),
            cost_receipt_id=f"cost-{_receipt_hash(result.cost_receipt)}",
            audio_metadata=AudioAssetMetadata(
                audio_kind=request.audio_kind,
                source=AudioSource(
                    kind=AssetSourceKind.GENERATED,
                    provider_or_tool=result.provenance_receipt.adapter,
                    input_artifact_ids=request.input_artifact_ids,
                    input_fingerprint=request.input_fingerprint,
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
                provenance_receipt_id=(
                    f"provenance-{_receipt_hash(result.provenance_receipt)}"
                ),
                alignment_receipt_id=(
                    f"alignment-{result.alignment_receipt_sha256}"
                ),
            ),
        )
        return PreparedVoiceCandidate(
            audio=PreparedAudioImport(
                payload=result.audio_bytes,
                probe=probe,
                asset_record=record,
            )
        )

    return prepare


__all__ = ["make_voice_candidate_preparer"]
